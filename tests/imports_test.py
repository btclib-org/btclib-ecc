# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Tests for the import graph of the `btclib_ecc` package.

Every module must be importable *first*, with no other module of this
package in sys.modules yet. Nothing else in the suite establishes that: a
test module reaches its subject through whatever the modules imported
before it have already pulled in, so a cycle that only bites the caller
who happens to arrive from the other side stays invisible.

What a module may import is the standard library, `typing_extensions`,
the bindings, gmpy2 and this package: each module is asked in an interpreter of
its own at run time, and each file's import statements are read
statically, which is what a module the suite never imports is checked
by.
"""

from __future__ import annotations

import ast
import importlib
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, cast

import pytest

import btclib_ecc
from tests import module_names

if TYPE_CHECKING:
    from collections.abc import Iterator

_ROOT = Path(__file__).resolve().parents[1]


def _is_ours(name: str) -> bool:
    """Answer whether a dotted name is this package or one of its modules.

    `btclib_ecc` and not a bare `startswith`, which would also take in
    a sibling distribution whose name merely begins the same way.
    """
    return name == "btclib_ecc" or name.startswith("btclib_ecc.")


def loaded_modules() -> list[str]:
    """Return the modules of this package in sys.modules."""
    return [name for name in sys.modules if _is_ours(name)]


@pytest.fixture
def unimported() -> Iterator[None]:
    """Hide every module of this package, then put it back.

    A subprocess per module would be the obvious way to get a virgin
    interpreter, and it costs an interpreter start-up per module for
    nothing: the import machinery decides what to execute by consulting
    sys.modules and nothing else.

    What the modules imported inside the fixture must not do is outlive
    it. They are fresh objects, so a class reimported here is not the
    class the rest of the suite already holds a reference to, and an
    isinstance check across the two would fail.
    """
    saved = {name: sys.modules[name] for name in loaded_modules()}
    for name in saved:
        del sys.modules[name]
    try:
        yield
    finally:
        for name in loaded_modules():
            del sys.modules[name]
        sys.modules.update(saved)


@pytest.mark.parametrize("module_name", module_names())
def test_import_first(module_name: str, unimported: None) -> None:
    """Import each module first, with nothing of this package loaded."""
    assert importlib.import_module(module_name).__name__ == module_name


def _loaded_after_importing(module_name: str) -> list[str]:
    """Import one module in a fresh interpreter and return sorted(sys.modules).

    A fresh subprocess rather than `unimported`: that fixture only hides
    this package's own modules from `sys.modules`, so a third-party
    package an earlier test already imported would still answer present,
    and the absence this module exists to prove would mean nothing.
    """
    probe = f"import {module_name}, sys; print(sorted(sys.modules))"
    stdout = subprocess.run(  # noqa: S603
        [sys.executable, "-c", probe],
        check=True,
        capture_output=True,
        encoding="utf-8",
        cwd=_ROOT,
    ).stdout
    return cast("list[str]", ast.literal_eval(stdout))


def test_the_tests_package_imports_no_submodule() -> None:
    """Importing the `tests` package alone reaches the root and no further.

    `tests/__init__.py` is imported by every test module before that
    module's own body runs -- before any fixture, `unimported` included,
    so this probe is a subprocess rather than that fixture. The coverage
    floor reads what the import itself reaches, so a helper built at the
    module scope of `tests/__init__.py` would be measured as reached by
    every module that asks it nothing.
    """
    loaded = _loaded_after_importing("tests")
    assert [m for m in loaded if _is_ours(m)] == ["btclib_ecc"]


# what is heavier than the stdlib basics, and `btclib`, which builds on this
# package and so cannot be below it. Not `socket`: the root reads `__version__`
# through `importlib.metadata`, which pulls in `email.utils` and, through it,
# `socket`, on every interpreter before 3.13, so asserting its absence would be
# a fact about the interpreter rather than about the package
_ABOVE_OR_HEAVY = ("btclib", "urllib.request", "ssl", "http.client")


@pytest.mark.parametrize("module_name", module_names())
def test_no_module_reaches_above_the_package(module_name: str) -> None:
    """Each module, imported alone, loads neither `btclib` nor a heavy module.

    A heavy module-level import here would be paid by every importer of
    this package, whatever it imported it for.
    """
    loaded = _loaded_after_importing(module_name)
    assert not set(loaded) & set(_ABOVE_OR_HEAVY)


def _loaded_within(entry_point: str) -> set[str]:
    """Return the modules of this package one import loads, the root aside."""
    return {m for m in _loaded_after_importing(entry_point) if _is_ours(m)} - {
        "btclib_ecc"
    }


def test_curves_stays_stdlib_light() -> None:
    """`btclib_ecc.curves` loads the arithmetic and the substrate alone.

    Subset rather than equal: a new edge into the package is the defect
    this exists to catch, and a removed one is not. Narrower than the
    package: it is the curve's own arithmetic, and its docstring states
    "Nothing here knows what a signature is", so `ecc` is out of it.
    """
    assert _loaded_within("btclib_ecc.curves") <= {
        "btclib_ecc._libsecp256k1",
        "btclib_ecc._utils",
        "btclib_ecc.alias",
        "btclib_ecc.curves",
        "btclib_ecc.curves.curve",
        "btclib_ecc.curves.curve_group",
        "btclib_ecc.curves.curve_group_2",
        "btclib_ecc.curves.curve_group_f",
        "btclib_ecc.curves.sec_point",
        "btclib_ecc.exceptions",
        "btclib_ecc.number_theory",
    }


def test_ecc_loads_every_scheme() -> None:
    """`btclib_ecc.ecc` binds each scheme it publishes, eagerly.

    Its `__init__` imports every module `__all__` names, which is what
    lets `btclib_ecc.ecc.dsa` answer after `import btclib_ecc.ecc`
    alone; the heavy modules are asked of it by the test above.
    """
    loaded = _loaded_within("btclib_ecc.ecc")
    schemes = {
        f"btclib_ecc.ecc.{name}"
        for name in importlib.import_module("btclib_ecc.ecc").__all__
        if isinstance(
            getattr(importlib.import_module("btclib_ecc.ecc"), name), ModuleType
        )
    }
    assert schemes
    assert schemes <= loaded


# the distributions a module of the package may import at the top level,
# beside the standard library: the typing backport, the bindings, whose
# absence `_libsecp256k1` answers for, gmpy2, whose absence
# `number_theory` answers for, and the package itself
_ALLOWED_THIRD_PARTY = frozenset(
    {"typing_extensions", "btclib_secp256k1", "gmpy2", "btclib_ecc"}
)


def _top_level_imports(source: str) -> set[str]:
    """Return the first component of every name one module's imports name.

    Relative imports name this package, so they are recorded as it.
    """
    names: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.add("btclib_ecc" if node.level else (node.module or "").split(".")[0])
    return names


def _outside(names: set[str]) -> list[str]:
    """Return what is neither the standard library nor allowed."""
    return sorted(names - set(sys.stdlib_module_names) - _ALLOWED_THIRD_PARTY)


def test_the_import_scan_finds_a_planted_import() -> None:
    """The scan names each form, and the check refuses what is outside."""
    source = (
        "import hashlib\nimport btclib.b58\nfrom btclib_wallet import bip32\n"
        "from . import kdf\nfrom typing_extensions import override\n"
    )
    names = _top_level_imports(source)
    assert names == {
        "hashlib",
        "btclib",
        "btclib_wallet",
        "btclib_ecc",
        "typing_extensions",
    }
    assert _outside(names) == ["btclib", "btclib_wallet"]


def test_no_module_imports_outside_the_stdlib_and_the_extras() -> None:
    """Every file of the package, read rather than imported.

    The static half of `test_no_module_reaches_above_the_package`: an
    import inside a function or behind `TYPE_CHECKING` is one no
    interpreter runs at import, and it would still fail the day it ran.
    """
    root = Path(btclib_ecc.__path__[0])
    found = {
        path.relative_to(root).as_posix(): _outside(
            _top_level_imports(path.read_text(encoding="utf-8"))
        )
        for path in sorted(root.rglob("*.py"))
    }
    assert "ecc/dsa.py" in found
    assert {file: names for file, names in found.items() if names} == {}
