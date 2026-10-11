# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""ECDSA key recovery against vectors of somebody else's making.

Each source is pinned in `tests/_data/README.md`, whose entry for the Core
file says what recovering from its signatures does and does not establish:

- Bitcoin Core's `key_tests.cpp`: the compact signature, with its recovery
  flag, that `CKey::SignCompact` writes for each of its keys over one
  message. Recovering from it must give the key of the WIF.
- libsecp256k1's `secp256k1_recovery` tests: which of the four recovery ids
  recover a key from a fixed signature, and which refuse.

Each test runs on both arithmetics, so that the Python arm is held to these
answers and not only to the bindings'.
"""

import hashlib
from typing import Any

import pytest

from btclib_ecc.curves import mult
from btclib_ecc.ecc import dsa
from btclib_ecc.exceptions import BTClibEccRuntimeError, BTClibEccValueError
from tests import b58decode, both_arms, load, vector_id

_CORE: dict[str, Any] = load("ecc", "_data", "bitcoin_core_compact_vectors.json")
_LIBSECP256K1: dict[str, Any] = load("ecc", "_data", "secp256k1_recovery_vectors.json")

# `Hash` of Core's hash.h, which `key_tests.cpp` hashes its message with
CORE_HASH = hashlib.sha256(
    hashlib.sha256(_CORE["message"].encode("ascii")).digest()
).digest()


def core_vector(vector: dict[str, str]) -> tuple[int, bool, int, dsa.Sig]:
    """Return a Core vector's key, compression, recovery id and signature.

    The flag byte of a compact signature is 27 + recid, plus 4 for a
    compressed key.
    """
    # 0x80, the key, and 0x01 where the key is compressed
    payload = b58decode(vector["wif"])
    prv_key = int.from_bytes(payload[1:33], "big")
    compact = bytes.fromhex(vector["compact"])
    flag = compact[0] - 27
    sig = dsa.Sig(
        int.from_bytes(compact[1:33], "big"), int.from_bytes(compact[33:], "big")
    )
    return prv_key, bool(flag & 4), flag & 3, sig


CORE_PARAMS = [
    pytest.param(vector, id=vector_id(i, vector["id"]))
    for i, vector in enumerate(_CORE["keys"])
]


@pytest.mark.parametrize("vector", CORE_PARAMS)
@both_arms
def test_core_recovers_the_signers_key(vector: dict[str, str]) -> None:
    """Every spelling of the recovery gives the key of the WIF."""
    prv_key, compressed, key_id, sig = core_vector(vector)
    Q = mult(prv_key)

    assert dsa.recover_pub_key_(key_id, CORE_HASH, sig) == Q
    assert Q in dsa.recover_pub_keys_(CORE_HASH, sig)

    sec = dsa.recover_sec_(key_id, CORE_HASH, sig, compressed=compressed)
    assert len(sec) == (33 if compressed else 65)
    assert sec == dsa.recover_sec_(
        key_id, CORE_HASH, sig.serialize(), compressed=compressed
    )
    assert dsa.verify_(CORE_HASH, Q, sig)


_LIBSECP256K1_CASES = [
    pytest.param(case, id=vector_id(i, case["id"]))
    for i, case in enumerate(_LIBSECP256K1["cases"])
]


@pytest.mark.parametrize("case", _LIBSECP256K1_CASES)
@both_arms
def test_libsecp256k1_recovers_what_it_says_it_does(case: dict[str, Any]) -> None:
    """Each recovery id recovers a key or refuses, as upstream asserts.

    A key that is recovered verifies the signature it was recovered from.
    A zero r or s is refused: libsecp256k1 parses it and then declines to
    recover, and `recover_pub_key_` raises.
    """
    msg_hash = bytes.fromhex(_LIBSECP256K1["msg32"])
    r = int(case["r"], 16)
    s = int(case["s"], 16)
    for recid, recovers in case["recovers"].items():
        key_id = int(recid)
        if not recovers:
            with pytest.raises((BTClibEccValueError, BTClibEccRuntimeError)):
                sig = dsa.Sig(r, s, check_validity=False)
                dsa.recover_pub_key_(key_id, msg_hash, sig)
            continue
        sig = dsa.Sig(r, s)
        Q = dsa.recover_pub_key_(key_id, msg_hash, sig)
        assert dsa.verify_(msg_hash, Q, sig)
        assert Q in dsa.recover_pub_keys_(msg_hash, sig)
