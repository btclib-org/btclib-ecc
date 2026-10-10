# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Tests for the `btclib_ecc.ecc.bip340_nonce` module.

The BIP340 vectors pin secp256k1 with sha256, in `tests/ecc/ssa_test.py`.
These cover the other curves and hash functions.
"""

from hashlib import sha256, sha512
from typing import Any

import pytest

from btclib_ecc.alias import HashF, Point
from btclib_ecc.curves import mult, secp256k1
from btclib_ecc.curves.curve import CURVES
from btclib_ecc.ecc import bip340_nonce, ssa
from btclib_ecc.ecc.bip340_nonce import _nonce_with_pub_key_, bip340_nonce_
from btclib_ecc.exceptions import BTClibEccValueError
from btclib_ecc.hashes import tagged_hash
from tests import Sha256FirstByte
from tests.curves.curve_test import byte_boundary_curves

# a hash shorter than the curve order
SHORT_HASH = [
    ("secp384r1", sha256),
    ("secp521r1", sha256),
    ("secp521r1", sha512),
]


@pytest.mark.parametrize("curve, hf", SHORT_HASH)
def test_a_nonce_is_as_long_as_the_curve_order(curve: str, hf: HashF) -> None:
    """A nonce is as long as n, not as the hash."""
    ec = CURVES[curve]
    aux = bytes(hf().digest_size)
    longest = 0
    for i in range(200):
        k, _, _, _ = bip340_nonce_(i.to_bytes(4, "big"), i + 1, aux, ec, hf)
        assert 0 < k < ec.n
        longest = max(longest, min(k, ec.n - k).bit_length())
    # each uniform nonce falls 9 bits short with probability 2^-8,
    # so all 200 of them with probability 2^-1600
    assert longest >= ec.nlen - 8


@pytest.mark.parametrize("curve, hf", SHORT_HASH)
def test_a_signature_with_a_short_hash_verifies(curve: str, hf: HashF) -> None:
    """The longer nonce is still a nonce `ssa` signs and verifies with."""
    ec = CURVES[curve]
    q, x_Q = ssa.gen_keys(0x1234567890ABCDEF, ec)
    sig = ssa.sign(b"a message", q, None, ec, hf)
    assert ssa.verify(b"a message", x_Q, sig, hf)


@pytest.mark.parametrize("curve, hf", SHORT_HASH)
def test_the_aux_mask_covers_the_whole_key(
    curve: str, hf: HashF, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Another aux changes the top bytes of the masked key too."""
    ec = CURVES[curve]
    hashed: list[bytes] = []

    def record(tag: bytes, m: bytes, hf: HashF) -> bytes:
        if tag == b"BIP0340/nonce":
            hashed.append(m)
        return tagged_hash(tag, m, hf)

    monkeypatch.setattr(bip340_nonce, "tagged_hash", record)
    for aux in (b"\x01", b"\x02"):
        bip340_nonce_(b"a message", ec.n - 1, aux * hf().digest_size, ec, hf)
    # every input of the nonce hash begins with the masked key, n_size bytes
    first, second = hashed[0][: ec.n_size], hashed[-1][: ec.n_size]
    top = ec.n_size - hf().digest_size
    assert first[:top] != second[:top]


@pytest.mark.parametrize("curve, hf", SHORT_HASH)
def test_the_nonce_is_deterministic(curve: str, hf: HashF) -> None:
    """One key, aux and message give one nonce, and another aux another."""
    ec = CURVES[curve]
    aux = bytes(hf().digest_size)
    k = bip340_nonce_(b"a message", 1, aux, ec, hf)
    assert k == bip340_nonce_(b"a message", 1, aux, ec, hf)
    assert k != bip340_nonce_(b"a message", 1, b"\x01" * len(aux), ec, hf)


@pytest.mark.parametrize(
    "curve, hf, expected",
    [
        (
            "secp256r1",
            sha256,
            0x89549C27A9B9458D87C955F625B3D0F35B57270B26BA6271DC376940CF0624F9,
        ),
        (
            "secp384r1",
            sha512,
            0x73A948B13BD720FDCD10579370A3568550F8F70E8152B500EA2DE6EA9213A90D03D87B74C68EB42E6F675FF438688820,
        ),
        ("secp112r1", sha256, 0x3F963EC5CD21AD81E568B1F0C616),
    ],
    ids=["secp256r1-sha256", "secp384r1-sha512", "secp112r1-sha256"],
)
def test_a_hash_as_long_as_the_curve_order_keeps_its_nonce(
    curve: str, hf: HashF, expected: int
) -> None:
    """Where one digest covers nlen bits, the nonce is the one it always was."""
    ec = CURVES[curve]
    k, _, _, _ = bip340_nonce_(
        b"unchanged", 0x1234567890ABCDEF, bytes(hf().digest_size), ec, hf
    )
    assert k == expected


@pytest.mark.parametrize("name, stretched", [("ec251_257", True), ("ec257_251", False)])
def test_a_one_byte_hash_is_stretched_when_n_has_more_bits(
    name: str, stretched: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The counter-mode branch runs when nlen exceeds the 8 bits of the hash.

    ec251_257 has nlen 9; ec257_251 has nlen 8, which one digest covers.
    """
    ec = byte_boundary_curves[name]
    assert (ec.nlen > 8) == stretched

    calls: list[int] = []
    stretch = bip340_nonce._stretch

    def spy(tag: bytes, m: bytes, size: int, hf: HashF) -> bytes:
        calls.append(size)
        return stretch(tag, m, size, hf)

    monkeypatch.setattr(bip340_nonce, "_stretch", spy)
    for q in range(1, ec.n):
        calls.clear()
        k, _, _, _ = bip340_nonce_(b"a message", q, bytes(1), ec, Sha256FirstByte)
        assert 0 < k < ec.n
        assert bool(calls) == stretched


def test_a_given_pub_key_spares_the_multiplication_and_changes_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A given point of the key gives the answer of the derived one."""
    calls: list[int] = []

    def spy(k: int, *args: Any, **kwargs: Any) -> Point:
        calls.append(k)
        return mult(k, *args, **kwargs)

    for q in (1, 0x1234567890ABCDEF, secp256k1.n - 1):
        expected = bip340_nonce_(b"a message", q, bytes(32))
        Q = mult(q)
        calls.clear()
        with monkeypatch.context() as patch:
            patch.setattr("btclib_ecc.ecc.bip340_nonce.mult", spy)
            assert (
                _nonce_with_pub_key_(b"a message", q, bytes(32), secp256k1, sha256, Q)
                == expected
            )
        assert len(calls) == 1

        # the control: without the point the derivation multiplies twice
        calls.clear()
        with monkeypatch.context() as patch:
            patch.setattr("btclib_ecc.ecc.bip340_nonce.mult", spy)
            _nonce_with_pub_key_(b"a message", q, bytes(32), secp256k1, sha256, None)
        assert len(calls) == 2


def test_the_key_is_refused_before_the_aux() -> None:
    """With a bad key and a bad aux, the key is the one named."""
    with pytest.raises(BTClibEccValueError, match="private key not in"):
        bip340_nonce_(b"m", 0, b"\x01")
