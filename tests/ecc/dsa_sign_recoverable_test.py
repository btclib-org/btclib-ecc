# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`dsa.sign_recoverable_` against the compact signatures of Bitcoin Core.

Core's expected bytes are libsecp256k1's output (`CKey::SignCompact` calls
`secp256k1_ecdsa_sign_recoverable`), so agreeing with them is not an
authority other than the bindings. This is why the test is not in
`dsa_recovery_test.py`, which `py_arm_authority_test.py` lists in
`_THIRD_PARTY_VECTORS`, and why `dsa.sign_recoverable_` stays in that
file's `_WITHOUT_AN_AUTHORITY`.
"""

import pytest

from btclib_ecc.ecc import dsa
from tests import both_arms
from tests.ecc.dsa_recovery_test import CORE_HASH, CORE_PARAMS, core_vector


@pytest.mark.parametrize("vector", CORE_PARAMS)
@both_arms
def test_core_signs_the_same_compact_signature(vector: dict[str, str]) -> None:
    """`sign_recoverable_` gives Core's r, s and recovery id."""
    prv_key, _, key_id, expected = core_vector(vector)
    sig, signed_key_id = dsa.sign_recoverable_(CORE_HASH, prv_key)
    assert sig == expected
    assert signed_key_id == key_id
