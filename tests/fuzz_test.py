# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Every class decoder, and the module-level ones listed, on unwritten input.

The rest of the suite is fixed vectors: exactly what conformance needs,
and blind to the malformed octets that never make it into a
specification's test section. This file is the converse. It does not
assert that a decoder accepts the right things -- the vectors do that --
but that it *fails the way the package says it fails*, whatever it is
handed: an IndexError off a short slice, an OverflowError off an
unchecked size or a silent short read reaches a caller who catches
`BTClibEccValueError` to reject bad input and has no reason to
expect anything else.

`fuzz/`'s atheris harnesses ask the same question of the signature and
envelope decoders for an hour a week; this asks it of every class
decoder and of the module-level decoders in `BINARY_PARSERS`, on every
run, for as long as hypothesis spends on a test. The wire inputs of
musig2, frost and dleq are not driven here.
"""

from __future__ import annotations

import contextlib
from collections.abc import Callable
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st

from btclib_ecc.curves.sec_point import point_from_octets
from btclib_ecc.ecc import dsa, ecies, ellswift, pedersen, ssa
from btclib_ecc.ecc.borromean import BorromeanSig
from btclib_ecc.ecc.rangeproof import RangeProof
from btclib_ecc.exceptions import (
    BTClibEccRuntimeError,
    BTClibEccTypeError,
    BTClibEccValueError,
)
from tests import public_classes_with

# What a decoder of this package is allowed to raise. Anything else
# leaves the contract src/btclib_ecc/exceptions.py documents
CONTRACT = (
    BTClibEccValueError,
    BTClibEccTypeError,
    BTClibEccRuntimeError,
)

# Bounded because these are decoders, not benchmarks: what a length field
# does with the octets behind it is decided in the first few of them. The
# mutation tests below are what reaches past the outermost check
MAX_INPUT = 512

BINARY_PARSERS: dict[str, Callable[[bytes], Any]] = {
    "dsa.Sig.parse": dsa.Sig.parse,
    "ssa.Sig.parse": ssa.Sig.parse,
    # `rsizes` left at its default, which is the ring structure a verifier
    # supplies and the wire format does not carry: what the default
    # reaches is the digest read, the trailing-octet refusal, and -- for
    # the input of exactly thirty-two octets that passes both --
    # `assert_valid`'s own "no rings"
    "BorromeanSig.parse": BorromeanSig.parse,
    # the proof that carries one of those signatures, whose own ring
    # structure a mutation *can* reach: the mantissa octet is what says
    # how many rings follow, so a flip there asks for a body the buffer
    # does not hold
    "RangeProof.parse": RangeProof.parse,
    "ecies.Envelope.parse": ecies.Envelope.parse,
    "point_from_octets": point_from_octets,
    "ssa.point_from_bip340pub_key": ssa.point_from_bip340pub_key,
    "ellswift.decode_var": ellswift.decode_var,
    "pedersen.commitment_from_octets": pedersen.commitment_from_octets,
    "pedersen.generator_from_octets": pedersen.generator_from_octets,
}

# The same contract, for what a user pastes rather than what a peer
# sends. `b64decode` decodes and then hands the octets to `parse`, so
# what it adds is the decoding -- a str that is not ascii, padding that
# is not canonical, a length no multiple of four -- a layer the binary
# entry point never sees
TEXT_PARSERS: dict[str, Callable[[str], Any]] = {
    "ecies.Envelope.b64decode": ecies.Envelope.b64decode,
}

# A class-level decoder is one of these three: `parse` for octets,
# `b64decode` and `b58decode` for the text encodings a class reads on its
# own. `serialization_boundary_test.py`'s `test_every_decoder_is_covered`
# draws the same three names for the same reason, so widening this tuple
# is what a class gaining a fourth would ask for, in both files at once.
# No walk finds a module-level decoder: that file's
# `test_no_codec_is_a_module_function` refuses only one named in its
# family, so each is listed above by hand
_CLASS_DECODER_METHODS = ("parse", "b64decode", "b58decode")


def _classes_driven_here() -> set[str]:
    """Every class the two dicts above drive, through which decoder.

    A bound classmethod carries in `__self__` the class it was read off,
    which is what the entry names. The method name is part of the key,
    since a class offering two of the three would otherwise collide.
    """
    driven = set()
    for entry_point in (*BINARY_PARSERS.values(), *TEXT_PARSERS.values()):
        cls = getattr(entry_point, "__self__", None)
        if isinstance(cls, type) and entry_point.__name__ in _CLASS_DECODER_METHODS:
            driven.add(f"{cls.__module__}.{cls.__qualname__}.{entry_point.__name__}")
    return driven


def test_every_class_that_decodes_is_driven_here() -> None:
    """The inventory is a promise only if omission is what fails.

    A class added to the package and given no line above is held to
    nothing here: the tests keep passing on the entry points they were
    given, and the new decoder answers hostile input however it likes.
    """
    found = {
        f"{name}.{method}"
        for method in _CLASS_DECODER_METHODS
        for name in public_classes_with(method)
    }
    # a walk returning nothing is a defect in the walk and not in the
    # inventory, and the equality alone answers it with a mismatch of
    # every name: this is what says which of the two a red run is
    assert found
    assert found == _classes_driven_here()


def _assert_contract(parse: Callable[[Any], Any], data: Any) -> None:
    """Call parse, and let anything outside the contract propagate.

    Rejecting the input is the expected answer to almost all of what
    these strategies generate, so there is nothing to assert about it.
    What the test is for is the third outcome, neither a value nor a
    refusal: hypothesis reports the exception, and the input it shrank
    to reach it.
    """
    with contextlib.suppress(*CONTRACT):
        parse(data)


@pytest.mark.parametrize(
    "parse", BINARY_PARSERS.values(), ids=list(BINARY_PARSERS.keys())
)
@given(data=st.binary(max_size=MAX_INPUT))
def test_binary_parser_honors_the_exception_contract(
    parse: Callable[[bytes], Any], data: bytes
) -> None:
    """Fuzz every binary decoder: refusals stay within the contract."""
    _assert_contract(parse, data)


@pytest.mark.parametrize("parse", TEXT_PARSERS.values(), ids=list(TEXT_PARSERS.keys()))
@given(data=st.text(max_size=MAX_INPUT))
def test_text_parser_honors_the_exception_contract(
    parse: Callable[[str], Any], data: str
) -> None:
    """Fuzz every text decoder: refusals stay within the contract."""
    _assert_contract(parse, data)


# a DER signature, whose tag, length and integer octets are what a
# mutation lands in: a flipped length asks for octets the buffer does
# not hold, and a flipped integer length moves the boundary between r
# and s
DSA_SIG_BIN = dsa.sign(b"btclib_ecc", 1).serialize()
# a BIE1 envelope, whose magic, ephemeral key, ciphertext and MAC sit at
# fixed offsets: a truncation or an extension lands in the ciphertext's
# block alignment, and a flipped octet in the key's prefix or on its
# x-coordinate. The ciphertext is opaque octets to the class, so one
# block of them is an envelope without a cipher; the ephemeral key is the
# generator, compressed
ENVELOPE_BIN = ecies.Envelope.from_ciphertext(
    "0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798",
    bytes(16),
    bytes(32),
).serialize()


def _mutations(sample: bytes) -> st.SearchStrategy[bytes]:
    """Return the near-misses of a valid serialization.

    Uniform random octets are rejected by the first field of a decoder
    and so exercise the outermost check and nothing beneath it. What
    reaches the code underneath is a serialization valid right up to the
    point where it is not: the truncation, the flipped length prefix, the
    trailing junk that must not be taken for a second record.
    """
    truncated = st.integers(min_value=0, max_value=len(sample)).map(
        lambda i: sample[:i]
    )
    flipped = st.builds(
        lambda i, byte: sample[:i] + bytes([byte]) + sample[i + 1 :],
        st.integers(min_value=0, max_value=len(sample) - 1),
        st.integers(min_value=0, max_value=0xFF),
    )
    extended = st.binary(max_size=32).map(lambda tail: sample + tail)
    return st.one_of(truncated, flipped, extended)


MUTATED_PARSERS: dict[str, tuple[Callable[[bytes], Any], bytes]] = {
    "dsa.Sig.parse": (dsa.Sig.parse, DSA_SIG_BIN),
    "ecies.Envelope.parse": (ecies.Envelope.parse, ENVELOPE_BIN),
}


@pytest.mark.parametrize(
    "parse, sample",
    MUTATED_PARSERS.values(),
    ids=list(MUTATED_PARSERS.keys()),
)
@given(data=st.data())
def test_mutated_serialization_honors_the_exception_contract(
    parse: Callable[[bytes], Any], sample: bytes, data: st.DataObject
) -> None:
    """Fuzz near-miss serializations: refusals stay within the contract."""
    _assert_contract(parse, data.draw(_mutations(sample)))


def test_the_mutated_samples_parse() -> None:
    """A sample the decoder refuses would make every mutation a refusal."""
    for parse, sample in MUTATED_PARSERS.values():
        assert parse(sample).serialize() == sample
