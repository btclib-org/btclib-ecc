# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Tests for BIP341's x-only tweaks in `btclib_ecc.ecc.ssa`.

The vectors are inputs of BIP341's `keyPathSpending`, copied from
bip-0341/wallet-test-vectors.json of bitcoin/bips at 927b6de: each gives an
internal private key, its x-only public key, the TapTweak and the tweaked
private key.
"""

from collections.abc import Callable
from typing import Any

import pytest

from btclib_ecc.curves import CURVES, mult, secp256k1
from btclib_ecc.ecc import ssa
from btclib_ecc.exceptions import (
    BTClibEccException,
    BTClibEccTypeError,
    BTClibEccValueError,
)
from tests import REFUSED_SCALARS, both_arms, refused_secret
from tests.secret_free import assert_secret_free

# internalPrivkey, internalPubkey, tweak, tweakedPrivkey
BIP341_KEY_PATH = [
    (
        "6b973d88838f27366ed61c9ad6367663045cb456e28335c109e30717ae0c6baa",
        "d6889cb081036e0faefa3a35157ad71086b123b2b144b649798b494c300a961d",
        "b86e7be8f39bab32a6f2c0443abbc210f0edac0e2c53d501b36b64437d9c6c70",
        "2405b971772ad26915c8dcdf10f238753a9b837e5f8e6a86fd7c0cce5b7296d9",
    ),
    (
        "1e4da49f6aaf4e5cd175fe08a32bb5cb4863d963921255f33d3bc31e1343907f",
        "187791b6f712a8ea41c8ecdd0ee77fab3e85263b37e1ec18a3651926b3a6cf27",
        "cbd8679ba636c1110ea247542cfbd964131a6be84f873f7f3b62a777528ed001",
        "ea260c3b10e60f6de018455cd0278f2f5b7e454be1999572789e6a9565d26080",
    ),
    (
        "d3c7af07da2d54f7a7735d3d0fc4f0a73164db638b2f2f7c43f711f6d4aa7e64",
        "93478e9488f956df2396be2ce6c5cced75f900dfa18e7dabd2428aae78451820",
        "6af9e28dbf9d6aaf027696e2598a5b3d056f5fd2355a7fd5a37a0e5008132d30",
        "97323385e57015b75b0339a549c56a948eb961555973f0951f555ae6039ef00d",
    ),
]


@pytest.mark.parametrize("vector", BIP341_KEY_PATH)
@both_arms
def test_bip341_key_path(vector: tuple[str, str, str, str]) -> None:
    """The tweaked private key, and the output key and parity it is the key of."""
    prv_key, pub_key, tweak, tweaked = vector
    assert ssa.prv_key_tweak_add(prv_key, tweak) == int(tweaked, 16)

    x, parity = ssa.pub_key_tweak_add_var(pub_key, tweak)
    Q = mult(int(tweaked, 16))
    assert (Q[0], Q[1] & 1) == (x, parity)

    # the internal key as its SEC octets and as its point name one x-only key
    P = ssa.point_from_bip340pub_key_var(pub_key)
    assert ssa.pub_key_tweak_add_var(P, tweak) == (x, parity)
    assert ssa.pub_key_tweak_add_var(mult(int(prv_key, 16)), tweak) == (x, parity)


@both_arms
def test_the_tweaked_key_is_the_key_of_the_tweaked_point() -> None:
    """On secp256k1 and, on the Python arm alone, on secp256r1."""
    for ec in (secp256k1, CURVES["secp256r1"]):
        for q, t in ((1, 0), (2, 3), (ec.n - 1, ec.n - 2), (0xC0FFEE, 0xBEEF)):
            _, x_Q = ssa.gen_keys(q, ec)
            x, parity = ssa.pub_key_tweak_add_var(x_Q, t, ec)
            tweaked = ssa.prv_key_tweak_add(q, t, ec)
            Q = mult(tweaked, ec=ec)
            assert (Q[0], Q[1] & 1) == (x, parity)


@both_arms
def test_the_sum_at_infinity_is_refused() -> None:
    """A tweak that is the negated key of the even point has no output key."""
    q, x_Q = ssa.gen_keys(0xC0FFEE)
    with pytest.raises(BTClibEccValueError, match="public key at infinity"):
        ssa.pub_key_tweak_add_var(x_Q, secp256k1.n - q)
    with pytest.raises(BTClibEccValueError, match="private key is zero") as e:
        ssa.prv_key_tweak_add(q, secp256k1.n - q)
    assert_secret_free(e.value, [hex(q)[2:], q.to_bytes(32, "big")])


@both_arms
def test_refusals() -> None:
    """An internal key that is no x-coordinate, and a tweak out of range."""
    # 5 is the x of no point of secp256k1, as is p, which is no field element
    for x in (5, secp256k1.p, -1):
        with pytest.raises(BTClibEccValueError):
            ssa.pub_key_tweak_add_var(x, 1)
    for t in (-1, secp256k1.n):
        with pytest.raises(BTClibEccValueError, match="tweak not in 0..n-1"):
            ssa.pub_key_tweak_add_var(1, t)
        with pytest.raises(BTClibEccValueError, match="tweak not in 0..n-1"):
            ssa.prv_key_tweak_add(1, t)
    with pytest.raises(BTClibEccTypeError):
        ssa.pub_key_tweak_add_var(1.0, 1)  # type: ignore[arg-type]
    with pytest.raises(BTClibEccTypeError):
        ssa.pub_key_tweak_add_var(1, 1, "secp256k1")  # type: ignore[arg-type]


# --------------------------------------------------------------------
# a refusal carries no secret
# --------------------------------------------------------------------
# Section 7 of the organization's standard: what a secret is refused for
# is said without it. The secret is fed in each spelling of
# `tests.REFUSED_SECRETS` that the call refuses, on both arms.

_SECRET_CALLS: dict[str, tuple[Callable[[Any], object], list[str]]] = {
    "prv_key_tweak_add": (lambda q: ssa.prv_key_tweak_add(q, 1), REFUSED_SCALARS),
}


_SECRET_CASES = [
    (name, kind) for name, (_, kinds) in _SECRET_CALLS.items() for kind in kinds
]


@pytest.mark.parametrize("name, kind", _SECRET_CASES)
@both_arms
def test_a_refusal_carries_no_secret(name: str, kind: str) -> None:
    """No piece of the secret is in the exception or in anything it chains."""
    call, _ = _SECRET_CALLS[name]
    secret, spellings = refused_secret(kind)
    with pytest.raises(BTClibEccException) as refused:
        call(secret)
    assert_secret_free(refused.value, spellings)
