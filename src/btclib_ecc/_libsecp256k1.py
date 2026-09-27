# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Everything this package asks of libsecp256k1, imported in one place.

The modules that delegate to the bindings import none of them directly:
they import from here, so the question "are the bindings installed" is
asked once, at one import, and answered by `INSTALLED` rather than by a
`try` block in each of them, which could drift apart. `ENABLED` is that
answer with `BTCLIB_ECC_NO_LIBSECP256K1` applied -- installed, and not
refused -- and `curves.curve` reads it into `_libsecp256k1_available`,
which is the seam every dispatch in the package consults, so an absent
binding is a dispatch that declines rather than an `ImportError` raised
before any dispatch is reached.

Two names because the seam moves and this import does not. `ENABLED` is
only the state `curves.curve` starts in, and `set_libsecp256k1_serving`
may have moved it since; `INSTALLED` is settled here and stays, so it is
what that function reads to refuse `serving=True` where there is nothing
to serve, and what the suite skips its `bindings` marker on. The
difference is this module's and the seam's, not a caller's:
`curves.is_libsecp256k1_serving` publishes one answer -- whether the next
call goes to libsecp256k1 or to the Python arithmetic -- which is the
only difference a caller can act on.

A module that imports nothing else of this package, and is therefore
below every module that reads it. What it does import is the whole of
the surface this package uses, so this file is also the answer to "what
does this package need these bindings for", which no reader has to
assemble from the delegating modules' own imports.

The names are re-exported under the bindings' own spelling and the caller
aliases them as it always did: a caller holding `keys` and reaching
through it, and a caller naming `pubkey_sum` directly, both keep the call
they had. Neither shape costs an attribute lookup it did not cost before,
which matters where `curves.curve` counts tenths of a microsecond.

With the bindings absent every name here is None. Nothing may call one:
`_libsecp256k1_serves` is False in that configuration, and it is the
predicate in front of every delegation -- which is a rule about the
package rather than about this file, and is what `tests/no_bindings_test.py`
checks by importing this package with the bindings out of reach.

Absent and installed-but-too-old are different failures, and only the
first one is this fallback (btclib-org/ellipticcurves#25). `btclib_secp256k1`
itself failing to import is `ModuleNotFoundError` with its `name` naming
the top-level package -- nothing else is. A name this module asks for that
an installed, too-old package does not have raises a plain `ImportError`
instead (the package is found; the attribute inside it is not), or a
`ModuleNotFoundError` naming a submodule rather than the top-level package
(an old package missing a whole submodule this floor needs). Catching
either of those as "absent" is the defect: it is what let
`btclib-secp256k1` 0.8.0.6, which has no `btclib_secp256k1.ecdh.shared_point`,
answer `INSTALLED = False` instead of raising. So only the first shape is
caught here; the other two propagate, which is a loud failure at import
time rather than a silent, slower fallback nobody is told about.
"""

from __future__ import annotations

import os

# the environment variable that refuses the bindings without uninstalling
# them, read once and here, when this module is first imported. `import
# btclib_ecc` alone does not import it, the root importing lazily; the
# first import of `curves`, of `ecc` or of a module under them does, so a
# caller settling the variable after that has settled it after this module
# answered. The package's name as its prefix, and "set to ask for it": an
# empty value is not set, so `BTCLIB_ECC_NO_LIBSECP256K1=` leaves them
# serving
NO_LIBSECP256K1 = "BTCLIB_ECC_NO_LIBSECP256K1"

__all__ = [
    "ENABLED",
    "INSTALLED",
    "NO_LIBSECP256K1",
    "PubkeyTweakChain",
    "dsa",
    "ellswift",
    "ffi",
    "keys",
    "musig",
    "pubkey_from_prvkey",
    "pubkey_sum",
    "pubkey_tweak_add",
    "pubkey_tweak_mul_sum",
    "recovery",
    "shared_point",
    "ssa",
    "xonly_pubkey_verify",
    "xonly_to_pubkey",
]

try:
    # `ffi` is the one object here that is not a wrapped call: issue
    # btclib-org/btclib#1009 is why it is needed at all -- `ecc.dsa.Signer`
    # builds its own `unsigned char[32]` with it, to hold a private key in
    # memory this package can overwrite, the way `ssa.Signer` already can
    # through the keypair `ssa` itself builds. Nothing else here needs it,
    # `dsa.sign` and every other wrapped call taking that buffer as the `prvkey`
    # a caller may already hold (btclib-org/btclib-secp256k1#253)
    from btclib_secp256k1 import (
        dsa,
        ellswift,
        ffi,
        keys,
        musig,
        recovery,
        ssa,
    )
    from btclib_secp256k1.ecdh import shared_point
    from btclib_secp256k1.keys import (
        PubkeyTweakChain,
        pubkey_from_prvkey,
        pubkey_sum,
        pubkey_tweak_add,
        pubkey_tweak_mul_sum,
    )
    from btclib_secp256k1.xonly import pubkey_verify as xonly_pubkey_verify
    from btclib_secp256k1.xonly import to_pubkey as xonly_to_pubkey

    INSTALLED = True
# issue btclib-org/btclib#1002 measured this branch rather than assuming it
# stays transitional: `test.yml`'s `no-bindings` job executes it every run, and
# `coverage-union` combines that run's data with the `coverage` job's. The
# combined report is 100% with this pragma removed -- so the branch is reached
# and is not dead code -- and the pragma still belongs here regardless, because
# `coverage-union` is a second gate beside the `coverage` job's, not instead of
# it: that job's own report, `pytest --cov` on this configuration alone, has
# bindings installed by construction, a `ModuleNotFoundError` only reachable by
# actually removing them, and a subprocess that does
# (`tests/no_bindings_test.py`) whose coverage that job does not collect. So
# this branch is a structural miss in that report regardless of the union, and
# removing the pragma would fail the one gate this issue chose to leave
# unchanged
except ModuleNotFoundError as exc:  # pragma: no cover -- only no-bindings reaches this
    # `exc.name` is the top-level package's own name only when the
    # import system never found it at all -- a submodule of an
    # installed package failing to import names that submodule instead
    # (`btclib_secp256k1.ecdh`, say), and a name missing from a module
    # that *was* found raises plain `ImportError`, which this clause
    # does not catch to begin with. Either of those is an installed
    # package too old for what this module asks of it
    # (btclib-org/ellipticcurves#25), and the caller is told rather than
    # silently handed the slower Python arithmetic
    if exc.name != "btclib_secp256k1":
        raise
    # None and not a callable that raises: what would raise is never
    # called, so the object would be a second thing to keep true. The
    # ignore is on the assignment and not on the module: every other
    # name here keeps the type the try branch gave it
    dsa = ellswift = ffi = keys = musig = recovery = ssa = None  # type: ignore[assignment]
    shared_point = None  # type: ignore[assignment]
    # a class rather than a function, so mypy calls it an assignment to
    # a type and wants the second code as well
    PubkeyTweakChain = None  # type: ignore[misc, assignment]
    pubkey_from_prvkey = pubkey_sum = None  # type: ignore[assignment]
    pubkey_tweak_add = pubkey_tweak_mul_sum = None  # type: ignore[assignment]
    xonly_pubkey_verify = xonly_to_pubkey = None  # type: ignore[assignment]

    INSTALLED = False

# installed and not refused, which is one state and not two: a caller
# asking whether the bindings serve has no use for the difference, and
# `curves.curve` starts its seam from this
ENABLED = INSTALLED and not os.environ.get(NO_LIBSECP256K1)
