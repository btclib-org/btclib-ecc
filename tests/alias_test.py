# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Tests for the type aliases of ecc.alias.

HashF is the constructor that every hf in the package is, and it returns
a Protocol rather than Any.

What a checker rejects cannot be asserted from inside the suite, so what is
asserted here is the run-time incompatibility the types describe: a
one-shot digest where a HashF goes does not merely type-check badly, it
does not work.
"""

from __future__ import annotations

import hashlib
import inspect
from typing import Any, get_args, get_type_hints

import pytest

from ecc.alias import HashF, HashObject
from ecc.hashes import reduce_to_hlen, tagged_hash


def _one_shot(data: bytes) -> bytes:
    """Return a digest in one call, which is what a HashF is not."""
    return hashlib.sha256(data).digest()


def test_a_one_shot_digest_is_not_a_hash_f() -> None:
    """A HashF is called with no argument, and a one-shot digest cannot be.

    hashlib.sha256 is a constructor: called with no data it returns an
    object to update. A one-shot digest needs its argument.
    """
    assert len(reduce_to_hlen(b"m", hashlib.sha256)) == 32
    # the one-shot is a working digest, so what is refused below is the
    # shape of the call and not a broken function
    assert _one_shot(b"m") == hashlib.sha256(b"m").digest()

    with pytest.raises(TypeError):
        reduce_to_hlen(b"m", _one_shot)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        tagged_hash(b"t", b"m", _one_shot)  # type: ignore[arg-type]


def test_hash_f_returns_a_protocol_not_any() -> None:
    """Returning Any would leave everything downstream of it unchecked.

    The package reads digest_size and builds digests through update().
    With HashF returning Any, a typo in either is a run-time
    AttributeError in a mypy-strict code base -- and mypy reports even a
    *correct* hf().digest() as "Returning Any".
    """
    hints = get_type_hints(HashObject.digest)
    assert hints["return"] is bytes
    assert get_type_hints(HashObject.hexdigest)["return"] is str

    # digest_size and block_size are properties, so read them off the class
    assert get_type_hints(HashObject.digest_size.fget)["return"] is int  # type: ignore[attr-defined]
    assert get_type_hints(HashObject.block_size.fget)["return"] is int  # type: ignore[attr-defined]
    assert get_type_hints(HashObject.name.fget)["return"] is str  # type: ignore[attr-defined]

    # update alone is Any, and only because hmac.new's digestmod wants a
    # parameter type this package cannot spell before 3.12
    assert get_type_hints(HashObject.update)["data"] is Any


def test_a_real_hashlib_object_satisfies_the_protocol() -> None:
    """Structural typing has to describe something that exists."""
    hash_object = hashlib.sha256()
    for name, member in inspect.getmembers(HashObject):
        if name.startswith("_"):
            continue
        assert hasattr(hash_object, name), f"hashlib.sha256() has no {name}"
        assert member is not None

    assert isinstance(hash_object.digest_size, int)
    assert isinstance(hash_object.block_size, int)
    assert isinstance(hash_object.name, str)
    hash_object.update(b"m")
    assert isinstance(hash_object.digest(), bytes)
    assert isinstance(hash_object.hexdigest(), str)
    assert isinstance(hash_object.copy().digest(), bytes)


def test_hash_f_is_a_constructor() -> None:
    """No argument in, a HashObject out."""
    parameters, returns = get_args(HashF)
    assert parameters == []
    assert returns is HashObject
