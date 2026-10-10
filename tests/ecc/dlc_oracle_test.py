# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Tests for the `btclib_ecc.ecc.dlc_oracle` module.

The vectors are the DLC specification's own, `test/dlc_schnorr_test.json`
of discreetlogcontracts/dlcspecs, vendored under `tests/ecc/_data/`;
`tests/_data/README.md` pins the revision.
"""

import random
from typing import Any

import pytest

from btclib_ecc.curves import bytes_from_point, mult, secp256k1
from btclib_ecc.ecc import dlc_oracle, ssa
from btclib_ecc.exceptions import BTClibEccValueError
from tests import both_arms, load, vector_id

random.seed(42)

_VECTORS: list[dict[str, Any]] = load("ecc", "_data", "dlc_schnorr_test.json")


@pytest.mark.parametrize(
    "vector", _VECTORS, ids=[vector_id(i) for i in range(len(_VECTORS))]
)
@both_arms
def test_vectors(vector: dict[str, Any]) -> None:
    """Each case: the keys, the signature and its point."""
    inputs = vector["inputs"]
    msg = inputs["msgHash"]
    _, x_Q = ssa.gen_keys(inputs["privKey"])
    _, x_K = ssa.gen_keys(inputs["privNonce"])
    assert x_Q.to_bytes(32, "big").hex() == vector["pubKey"]
    assert x_K.to_bytes(32, "big").hex() == vector["pubNonce"]

    sig = dlc_oracle.sign_(msg, inputs["privKey"], inputs["privNonce"])
    assert sig.serialize().hex() == vector["signature"]
    assert ssa.verify_(msg, vector["pubKey"], sig)

    S = dlc_oracle.sig_point_(msg, vector["pubKey"], vector["pubNonce"])
    assert bytes_from_point(S).hex() == vector["sigPoint"]


def test_sig_point_is_s_times_g() -> None:
    """The signature point is s*G of the signature made with its nonce."""
    for _ in range(32):
        prv_key = 1 + random.randrange(secp256k1.n - 1)
        nonce = 1 + random.randrange(secp256k1.n - 1)
        msg = random.randbytes(random.randrange(64))
        sig = dlc_oracle.sign_(msg, prv_key, nonce)
        _, x_Q = ssa.gen_keys(prv_key)
        _, x_K = ssa.gen_keys(nonce)
        assert sig.r == x_K
        assert dlc_oracle.sig_point_(msg, x_Q, x_K) == mult(sig.s)


def test_invalid_nonce() -> None:
    """A nonce outside 1..n-1 is refused."""
    for nonce in (0, secp256k1.n):
        with pytest.raises(BTClibEccValueError):
            dlc_oracle.sign_(b"", 1, nonce)
