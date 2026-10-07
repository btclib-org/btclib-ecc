# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""The known-answer check of the bindings `btclib_ecc._libsecp256k1` selects."""

import runpy
from collections.abc import Callable
from typing import Any

import pytest

from btclib_ecc import _libsecp256k1
from btclib_ecc._libsecp256k1 import NO_LIBSECP256K1
from btclib_ecc.curves import (
    curve,
    is_libsecp256k1_serving,
    set_libsecp256k1_serving,
)
from btclib_ecc.exceptions import BTClibEccRuntimeError
from tests import needs_bindings

pytestmark = needs_bindings


class _DerOnly:
    """A bindings submodule that parses DER and not compact signatures."""

    def verify(self, *_: Any, compact: bool = False, **__: Any) -> bool:
        return not compact


class _Wrong:
    """A bindings submodule whose `verify` answers the same to everything."""

    def __init__(self, answer: bool) -> None:
        self.answer = answer

    def verify(self, *_: Any, **__: Any) -> bool:
        return self.answer


def test_the_real_bindings_pass() -> None:
    """The check is silent on the bindings the suite runs against."""
    _libsecp256k1._check_bindings(setter=False)


@pytest.mark.parametrize(
    "name, wrong, message",
    [
        ("pubkey_from_prvkey", lambda *_: bytes(33), "wrong public key"),
        ("dsa", _Wrong(False), "known ECDSA signature"),
        ("dsa", _DerOnly(), "known ECDSA signature"),
        ("dsa", _Wrong(True), "over another message"),
        ("ssa", _Wrong(False), "known BIP340 signature"),
    ],
)
def test_each_wrong_answer_raises(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    wrong: Callable[..., Any],
    message: str,
) -> None:
    """A backend that answers one of the checks wrongly raises."""
    monkeypatch.setattr(_libsecp256k1, name, wrong)
    with pytest.raises(BTClibEccRuntimeError, match=message):
        _libsecp256k1._check_bindings(setter=False)


def _execute_afresh() -> dict[str, Any]:
    """Execute the module's file in a new namespace, as an import does.

    The run name is inside the package: coverage matches `btclib_ecc` by
    module name and caches the answer per file, so a name outside it
    would stop the file being measured for the rest of the worker.
    """
    path = _libsecp256k1.__file__
    assert path is not None
    return runpy.run_path(path, run_name="btclib_ecc._libsecp256k1_fresh")


def test_import_refuses_a_wrong_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    """Executing the module with a wrong public key raises, once enabled.

    The first execution shows that it is silent on the real bindings; the
    wrong one is then refused when the bindings are enabled and let through
    when `BTCLIB_ECC_NO_LIBSECP256K1` refuses them: they are checked when
    first selected, which `test_the_setter_checks_the_bindings` covers.
    """
    monkeypatch.delenv(_libsecp256k1.NO_LIBSECP256K1, raising=False)
    _execute_afresh()

    monkeypatch.setattr(_libsecp256k1.keys, "pubkey_from_prvkey", lambda *_: bytes(33))
    with pytest.raises(
        BTClibEccRuntimeError, match=f"wrong public key.*set {NO_LIBSECP256K1} to"
    ):
        _execute_afresh()

    monkeypatch.setenv(_libsecp256k1.NO_LIBSECP256K1, "1")
    assert not _execute_afresh()["ENABLED"]


def test_the_setter_checks_the_bindings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Selecting bindings not yet checked checks them, once, before serving.

    The seam starts off, the state `BTCLIB_ECC_NO_LIBSECP256K1` leaves.
    """
    monkeypatch.setattr(curve, "_libsecp256k1_available", False)
    monkeypatch.setattr(_libsecp256k1, "_checked", False)
    with monkeypatch.context() as wrong:
        wrong.setattr(_libsecp256k1, "pubkey_from_prvkey", lambda *_: bytes(33))
        with pytest.raises(
            BTClibEccRuntimeError, match="wrong public key.*keep `serving=False`"
        ):
            set_libsecp256k1_serving(serving=True)
    assert not is_libsecp256k1_serving()
    assert not _libsecp256k1._checked

    set_libsecp256k1_serving(serving=True)
    assert is_libsecp256k1_serving()
    assert _libsecp256k1._checked
