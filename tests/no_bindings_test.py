# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""The package with btclib_secp256k1 not installed, which is a subprocess.

`btclib_ecc._libsecp256k1` asks for the bindings once, at import, and
`curves.curve._libsecp256k1_available` is that answer; so the question
this file asks -- does the package import and answer without them --
can only be asked of an interpreter that has not imported it yet. A
monkeypatch cannot: by the time a test runs, the import has happened and
its answer is bound.

Uninstalling them is not an option either, the suite being one
environment. So the bindings are put out of reach by a meta path finder
that refuses the name, in a child interpreter, and the package is
imported after that -- which is what `import btclib_ecc` does on a
machine that never had them.

This is not `test.yml`'s `no-bindings` job and does not replace it: a finder
that refuses one name leaves the wheel installed and the environment
resolved, where the job installs neither. What it does is make the
absent-bindings configuration answerable in the ordinary suite, on every
platform the matrix runs, rather than only where a second install exists.

What the child returns is compared with what this process computes with
the bindings in reach: agreement between the two implementations is the
property, and a child that merely fails to crash proves nothing about it.

`test_the_two_arms_refuse_the_same_inputs` asks the same question of a
refusal: the test above compares only what both arms compute
successfully, so it would not catch the shape of issue
btclib-org/btclib#1227 -- one input answered on one arm and raised on the
other, two answers decided by `pip install`. A second child, built the
same way, runs a table of inputs and compares what each arm refuses
them with.

`test_an_installed_but_too_old_package_is_not_read_as_absent` asks a
different question: not "is the package findable at all", but "is a name
this module asks of a *found* package missing". issue
btclib-org/ellipticcurves#25 is that the two used to answer the same way.
The meta path finder above cannot build that case -- it refuses to find
`btclib_secp256k1` in the first place -- so that child stubs the package
directly into `sys.modules`, present and one name short.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Callable
from typing import Any

import pytest

from btclib_ecc._libsecp256k1 import ENABLED, INSTALLED, NO_LIBSECP256K1
from btclib_ecc.curves import (
    bytes_from_point,
    curve,
    is_libsecp256k1_serving,
    mult,
    point_from_octets,
    secp256k1,
    set_libsecp256k1_serving,
)
from btclib_ecc.curves.curve import CURVES
from btclib_ecc.ecc import dsa, ssa
from btclib_ecc.exceptions import BTClibEccException, BTClibEccValueError
from tests import needs_bindings

# the key and message the child works from: constants, because the two
# processes have to be asked the same question
_PRV_KEY = 0x1234567890ABCDEF1234567890ABCDEF1234567890ABCDEF1234567890ABCDEF
_MSG_HASH = bytes(range(32))
# BIP340 signing is randomized where the caller names no aux -- `sign_`
# draws `secrets.token_bytes` for it, which is BIP340's own *Default
# Signing* -- so the two processes are given the same aux and compared
# octet for octet. ECDSA needs no such argument, RFC6979 making the
# nonce a function of the message and the key
_AUX = bytes(32)

# what the child runs: the finder first, the package after it, and the answers
# as json on stdout. `-c` and not a file, so that nothing has to be
# written to disk and cleaned up
_CHILD = """
import json, sys


class RefuseTheBindings:
    def find_spec(self, name, path=None, target=None):
        if name == "btclib_secp256k1" or name.startswith("btclib_secp256k1."):
            # `ModuleNotFoundError` with `name` set to the module the
            # import system was looking for: what a genuinely-uninstalled
            # `btclib_secp256k1` raises with no finder in the way at all,
            # and what `_libsecp256k1`'s own except clause reads to tell
            # this apart from an installed package too old for a name it
            # asks for (btclib-org/ellipticcurves#25)
            raise ModuleNotFoundError(f"{{name}} is out of reach", name=name)
        return None


sys.meta_path.insert(0, RefuseTheBindings())

import btclib_ecc
from btclib_ecc._libsecp256k1 import ENABLED, INSTALLED, NO_LIBSECP256K1
from btclib_ecc.curves import curve, mult
from btclib_ecc.ecc import dh, dsa, ellswift, ssa
from btclib_ecc.exceptions import BTClibEccValueError

assert "btclib_secp256k1" not in sys.modules, "the finder let the bindings in"

print(json.dumps({{
    "installed": INSTALLED,
    "dispatch": curve._libsecp256k1_available,
    "point": mult({prv_key}),
    "dsa": dsa.sign_({msg_hash!r}, {prv_key}).serialize().hex(),
    "ssa": ssa.sign_({msg_hash!r}, {prv_key}, {aux!r}).serialize().hex(),
    "verify": dsa.verify_(
        {msg_hash!r},
        bytes.fromhex({sec!r}),
        bytes.fromhex({sig!r}),
    ),
}}))
"""


def _child_answers(sec: str, sig: str) -> dict[str, Any]:
    """Run the child and return what it printed, failing on its stderr."""
    source = _CHILD.format(
        prv_key=_PRV_KEY,
        msg_hash=_MSG_HASH,
        aux=_AUX,
        sec=sec,
        sig=sig,
    )
    completed = subprocess.run(  # noqa: S603
        [sys.executable, "-c", source],
        capture_output=True,
        encoding="utf-8",
        check=False,
        # large enough to be uninteresting, and there so that a child
        # that hangs fails as this test rather than as a slow suite: it
        # would otherwise hold an xdist worker until the job's own
        # timeout-minutes, and the report would name neither
        timeout=120,
    )
    assert completed.returncode == 0, completed.stderr
    answers: dict[str, Any] = json.loads(completed.stdout)
    return answers


@needs_bindings
def test_the_package_answers_with_the_bindings_out_of_reach() -> None:
    """Import and answer, and answer what the bindings answer.

    Every layer at once, deliberately: the arithmetic (`mult`) and the
    two signature schemes, signing and verifying. One child process for
    them, a python interpreter costing more to start than any of them
    costs to run.

    The child imports guarded modules beyond the ones it then calls:
    `src/btclib_ecc/__init__.py` imports nothing eagerly, so `import
    btclib_ecc` is the metadata lookup and no module at all, and a
    guard nothing imports is a guard nothing checks. `ecc.dh` and
    `ecc.ellswift` are the two the calls below would not reach on their
    own.
    """
    # the same question this process answers with the bindings serving
    assert INSTALLED
    assert ENABLED
    assert curve._libsecp256k1_available

    sec = bytes_from_point(mult(_PRV_KEY)).hex()
    sig = dsa.sign_(_MSG_HASH, _PRV_KEY).serialize().hex()

    answers = _child_answers(sec, sig)

    assert answers["installed"] is False
    assert answers["dispatch"] is False
    assert tuple(answers["point"]) == mult(_PRV_KEY)
    assert answers["dsa"] == sig
    assert answers["ssa"] == ssa.sign_(_MSG_HASH, _PRV_KEY, _AUX).serialize().hex()
    assert answers["verify"] is True


@needs_bindings
def test_the_environment_variable_refuses_the_installed_bindings() -> None:
    """`BTCLIB_ECC_NO_LIBSECP256K1` settles the question before import.

    A public function cannot do this job on its own:
    `btclib_ecc._libsecp256k1` answers at import, so a caller that wants the
    Python arithmetic from the first call has to say so before the interpreter
    reaches `import btclib_ecc`. A test runner is exactly that caller, which
    is why the variable exists beside `set_libsecp256k1_serving` rather than
    instead of it.

    Installed and refused answers what absent answers -- one state, not
    two -- so the assertion is the same as the child above makes.
    """
    probe = (
        "from btclib_ecc._libsecp256k1 import ENABLED, INSTALLED;"
        "from btclib_ecc.curves import is_libsecp256k1_serving;"
        "print(INSTALLED, ENABLED, is_libsecp256k1_serving())"
    )
    answered = subprocess.run(  # noqa: S603
        [sys.executable, "-c", probe],
        capture_output=True,
        encoding="utf-8",
        check=True,
        env={**os.environ, NO_LIBSECP256K1: "1"},
    ).stdout.split()
    assert answered == ["True", "False", "False"]

    # and an empty value is not set: the bindings serve
    answered = subprocess.run(  # noqa: S603
        [sys.executable, "-c", probe],
        capture_output=True,
        encoding="utf-8",
        check=True,
        env={**os.environ, NO_LIBSECP256K1: ""},
    ).stdout.split()
    assert answered == ["True", "True", "True"]


# `btclib-secp256k1` 0.8.0.6's own shape, from the issue: every name this
# module takes from the package is there except
# `btclib_secp256k1.ecdh.shared_point` -- the package is found, and one name
# inside it is not. Built with `sys.modules` and not the meta path finder
# above, because that finder answers a different question -- it refuses to
# find the package at all, where this case needs the package found and one
# attribute of it missing
_STALE_BINDINGS_CHILD = """
import sys, types

parent = types.ModuleType("btclib_secp256k1")
for name in ("dsa", "ellswift", "ffi", "musig", "recovery", "ssa"):
    setattr(parent, name, types.ModuleType(f"btclib_secp256k1.{name}"))

keys_module = types.ModuleType("btclib_secp256k1.keys")
for name in (
    "PubkeyTweakChain",
    "pubkey_from_prvkey",
    "pubkey_sum",
    "pubkey_tweak_add",
    "pubkey_tweak_mul_sum",
):
    setattr(keys_module, name, object())
parent.keys = keys_module

xonly_module = types.ModuleType("btclib_secp256k1.xonly")
xonly_module.pubkey_verify = object()
xonly_module.to_pubkey = object()

# the module is there; the name this floor needs from it is not
ecdh_module = types.ModuleType("btclib_secp256k1.ecdh")

sys.modules["btclib_secp256k1"] = parent
sys.modules["btclib_secp256k1.keys"] = keys_module
sys.modules["btclib_secp256k1.xonly"] = xonly_module
sys.modules["btclib_secp256k1.ecdh"] = ecdh_module

try:
    import btclib_ecc._libsecp256k1
except ImportError as exc:
    print("raised", type(exc).__name__)
else:
    print("swallowed")
"""


def test_an_installed_but_too_old_package_is_not_read_as_absent() -> None:
    """A name missing from a *found* package raises, rather than reading absent.

    issue btclib-org/ellipticcurves#25: catching every `ImportError` the
    bindings' own import could raise, absent or merely too old, answered
    `INSTALLED = False` for both -- `btclib-secp256k1` 0.8.0.6 lacking
    `ecdh.shared_point` fell back to the Python arithmetic exactly as an
    uninstalled package does, with nothing said about it.

    A subprocess, for the same reason as the child above: `_libsecp256k1`
    answers at import, so the question can only be put to an interpreter
    that has not imported it yet.
    """
    completed = subprocess.run(  # noqa: S603
        [sys.executable, "-c", _STALE_BINDINGS_CHILD],
        capture_output=True,
        encoding="utf-8",
        check=False,
        timeout=120,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.split() == ["raised", "ImportError"]


def test_the_switch_refuses_to_promise_bindings_that_are_not_there(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Asking for C where there is none is refused, not ignored.

    A caller that asked for the bindings and was quietly left on the
    Python arithmetic would be timing Python and calling it C, which is
    the mistake `curves/curve.py` says the seam exists to make
    impossible.
    """
    monkeypatch.setattr(curve, "_bindings_installed", False)
    with pytest.raises(BTClibEccValueError, match="btclib_secp256k1 is not installed"):
        set_libsecp256k1_serving(serving=True)

    # try/finally and not a monkeypatch for the restore: monkeypatch puts
    # back the value it found, and it would find the False this test has
    # just set -- which is a process-wide switch left off for whatever
    # runs next in this worker
    try:
        # switching them off is allowed whatever is installed: it is the
        # direction that always has an implementation to fall back to
        set_libsecp256k1_serving(serving=False)
        assert not is_libsecp256k1_serving()
    finally:
        monkeypatch.undo()
        set_libsecp256k1_serving(serving=ENABLED)


@needs_bindings
def test_the_switch_is_read_back_by_the_reader() -> None:
    """The pair is one state: what is set is what is read."""
    assert is_libsecp256k1_serving() is curve._libsecp256k1_available
    delegated = mult(_PRV_KEY)

    try:
        set_libsecp256k1_serving(serving=False)
        assert is_libsecp256k1_serving() is False
        # every dispatch reads it, which is what makes the pair worth
        # having: the arithmetic answers the same either way
        assert mult(_PRV_KEY) == delegated
        set_libsecp256k1_serving(serving=True)
        assert is_libsecp256k1_serving() is True
    finally:
        set_libsecp256k1_serving(serving=ENABLED)


@needs_bindings
def test_the_reader_is_the_dispatch_for_secp256k1() -> None:
    """What a caller asks the public reader is what the dispatch decides.

    A caller outside this package that picks between `btclib_secp256k1`
    and this package's Python arithmetic for secp256k1, with no hash
    function of its own in the choice, asks `is_libsecp256k1_serving`:
    the private predicate every module here asks gives the same answer
    there, in either state of the switch, and on any other curve its
    answer is no.
    """
    try:
        for serving in (True, False):
            set_libsecp256k1_serving(serving=serving)
            assert curve._libsecp256k1_serves(secp256k1, None) is serving
            assert is_libsecp256k1_serving() is serving
            assert curve._libsecp256k1_serves(CURVES["secp256r1"], None) is False
    finally:
        set_libsecp256k1_serving(serving=ENABLED)


_Q = mult(_PRV_KEY)
_X = _Q[0].to_bytes(32, "big")
_Y = _Q[1].to_bytes(32, "big")

# name -> the call. Each is held to the message as well as the class: each
# refusal runs in a shared precondition above the arm split --
# `int_from_integer` for the bool (issue btclib-org/btclib#1206),
# `point_from_octets`'s own hybrid check for the key -- so neither arm sees the
# input before the one sentence of this package has fired
_REFUSALS: dict[str, Callable[[], object]] = {
    "bool private key": lambda: dsa.sign(_MSG_HASH, True),
    "hybrid public key": lambda: point_from_octets(bytes([0x06]) + _X + _Y),
}

# a second child, built the same way as `_CHILD` above: the finder
# first, then a table of the same inputs `_REFUSALS` names, run against
# whatever each raises rather than what each returns. `installed` and
# `dispatch` are asked again here rather than trusted from the first
# child's own answer, a separate `-c` invocation being a separate
# process this test has not otherwise looked at
_REFUSAL_CHILD = """
import json, sys


class RefuseTheBindings:
    def find_spec(self, name, path=None, target=None):
        if name == "btclib_secp256k1" or name.startswith("btclib_secp256k1."):
            # `ModuleNotFoundError` with `name` set to the module the
            # import system was looking for: what a genuinely-uninstalled
            # `btclib_secp256k1` raises with no finder in the way at all,
            # and what `_libsecp256k1`'s own except clause reads to tell
            # this apart from an installed package too old for a name it
            # asks for (btclib-org/ellipticcurves#25)
            raise ModuleNotFoundError(f"{{name}} is out of reach", name=name)
        return None


sys.meta_path.insert(0, RefuseTheBindings())

from btclib_ecc._libsecp256k1 import INSTALLED
from btclib_ecc.curves import curve, point_from_octets
from btclib_ecc.ecc import dsa
from btclib_ecc.exceptions import BTClibEccException

assert "btclib_secp256k1" not in sys.modules, "the finder let the bindings in"


def refused(call):
    try:
        call()
    except BTClibEccException as e:
        return [type(e).__name__, str(e)]
    return None  # a call this table names but does not refuse is the finding


print(json.dumps({{
    "installed": INSTALLED,
    "dispatch": curve._libsecp256k1_available,
    "bool private key": refused(lambda: dsa.sign({msg_hash!r}, True)),
    "hybrid public key": refused(
        lambda: point_from_octets(bytes.fromhex({hybrid_sec!r}))
    ),
}}))
"""


def _refusal_child_answers() -> dict[str, Any]:
    """Run the refusal child and return what it printed, or fail on stderr."""
    source = _REFUSAL_CHILD.format(
        msg_hash=_MSG_HASH,
        hybrid_sec=(bytes([0x06]) + _X + _Y).hex(),
    )
    completed = subprocess.run(  # noqa: S603
        [sys.executable, "-c", source],
        capture_output=True,
        encoding="utf-8",
        check=False,
        # the same ceiling as `_child_answers`, and the same reason: a
        # hung child fails as this test rather than as a slow suite
        timeout=120,
    )
    assert completed.returncode == 0, completed.stderr
    answers: dict[str, Any] = json.loads(completed.stdout)
    return answers


def _locally_refused(call: Callable[[], object]) -> tuple[str, str]:
    """Run call with the bindings in reach and return what it raised."""
    with pytest.raises(BTClibEccException) as excinfo:
        call()
    return type(excinfo.value).__name__, str(excinfo.value)


@needs_bindings
def test_the_two_arms_refuse_the_same_inputs() -> None:
    """A refusal is held to one class and one wording on either arm.

    `test_the_package_answers_with_the_bindings_out_of_reach` above
    compares only what both arms compute successfully, so it would not
    catch the shape of issue btclib-org/btclib#1227: one input answered on
    one arm and raised on the other. This asks the question it does not:
    given an input, do the two arms refuse it the same way.

    `_REFUSALS` names the inputs, and the comment above the table says why each
    is held to its wording as well as its class. Every entry is refused here,
    with the bindings in reach, before the child runs, so a table entry that
    stopped refusing would fail this half rather than silently comparing two
    successes.
    """
    local = {name: _locally_refused(call) for name, call in _REFUSALS.items()}

    answers = _refusal_child_answers()
    assert answers["installed"] is False
    assert answers["dispatch"] is False

    for name in _REFUSALS:
        got = answers[name]
        assert got is not None, f"{name}: the no-bindings arm did not refuse"
        assert tuple(got) == local[name], name
