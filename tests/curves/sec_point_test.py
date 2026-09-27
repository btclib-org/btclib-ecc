# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Tests for the `btclib_ecc.curves.sec_point` module."""

from collections.abc import Callable

import pytest

from btclib_ecc.alias import INF, Point
from btclib_ecc.curves import (
    Curve,
    PreparedPoint,
    bytes_from_point,
    bytes_from_prv_key_int,
    # the module, not only the names in it: `_libsecp256k1_available` is
    # an attribute of it, and switching it off is how the tests below
    # reach the Python arithmetic underneath
    curve,
    mult,
    point_from_octets,
    point_from_pub_key,
    scalar_from_prv_key,
    secp256k1,
)
from btclib_ecc.curves.curve import CURVES
from btclib_ecc.curves.sec_point import _mult_sec, mult_pub_key
from btclib_ecc.exceptions import BTClibEccTypeError, BTClibEccValueError
from tests import b58encode, needs_bindings
from tests.curves.curve_test import secp112r2_order_4_point, secp128r2_order_4_point

# test curves: very low cardinality
# 13 % 4 = 1; 13 % 8 = 5
low_card_curves = {"ec13_11": Curve(13, 7, 6, (1, 1), 11, 1, False)}
low_card_curves["ec13_19"] = Curve(13, 0, 2, (1, 9), 19, 1, False)
# 17 % 4 = 1; 17 % 8 = 1
low_card_curves["ec17_13"] = Curve(17, 6, 8, (0, 12), 13, 2, False)
low_card_curves["ec17_23"] = Curve(17, 3, 5, (1, 14), 23, 1, False)
# 19 % 4 = 3; 19 % 8 = 3
low_card_curves["ec19_13"] = Curve(19, 0, 2, (4, 16), 13, 2, False)
low_card_curves["ec19_23"] = Curve(19, 2, 9, (0, 16), 23, 1, False)
# 23 % 4 = 3; 23 % 8 = 7
low_card_curves["ec23_19"] = Curve(23, 9, 7, (5, 4), 19, 1, False)
low_card_curves["ec23_31"] = Curve(23, 5, 1, (0, 1), 31, 1, False)

# the union operator, as in curves.curve and tests/curves/curve_test.py
all_curves = low_card_curves | CURVES


def test_octets2point() -> None:
    """Round-trip SEC encodings on every curve, and check the refusals."""
    for ec in all_curves.values():
        G_bytes = bytes_from_point(ec.G, ec)
        G_point = point_from_octets(G_bytes, ec)
        assert G_point == ec.G

        G_bytes = bytes_from_point(ec.G, ec, False)
        G_point = point_from_octets(G_bytes, ec)
        assert G_point == ec.G

        # just a point, not INF
        Q = ec.G

        Q_bytes = b"\x03" if Q[1] & 1 else b"\x02"
        Q_bytes += Q[0].to_bytes(ec.p_size, byteorder="big", signed=False)
        Q_point = point_from_octets(Q_bytes, ec)
        assert Q_point[0] == Q[0]
        assert Q_point[1] == Q[1]
        assert bytes_from_point(Q_point, ec) == Q_bytes

        Q_hex_str = Q_bytes.hex()
        Q_point = point_from_octets(Q_hex_str, ec)
        assert Q_point == Q

        Q_bytes = b"\x04" + Q[0].to_bytes(ec.p_size, byteorder="big", signed=False)
        Q_bytes += Q[1].to_bytes(ec.p_size, byteorder="big", signed=False)
        Q_point = point_from_octets(Q_bytes, ec)
        assert Q_point == Q
        assert bytes_from_point(Q_point, ec, False) == Q_bytes

        Q_hex_str = Q_bytes.hex()
        Q_point = point_from_octets(Q_hex_str, ec)
        assert Q_point == Q

        Q_bytes = b"\x01" + b"\x01" * ec.p_size
        with pytest.raises(BTClibEccValueError, match="not a point: "):
            point_from_octets(Q_bytes, ec)

        Q_bytes = b"\x01" + b"\x01" * 2 * ec.p_size
        with pytest.raises(BTClibEccValueError, match="not a point: "):
            point_from_octets(Q_bytes, ec)

        Q_bytes = b"\x04" + b"\x01" * ec.p_size
        with pytest.raises(
            BTClibEccValueError, match="invalid size for uncompressed point: "
        ):
            point_from_octets(Q_bytes, ec)

        Q_bytes = b"\x02" + b"\x01" * 2 * ec.p_size
        with pytest.raises(
            BTClibEccValueError, match="invalid size for compressed point: "
        ):
            point_from_octets(Q_bytes, ec)

        Q_bytes = b"\x03" + b"\x01" * 2 * ec.p_size
        with pytest.raises(
            BTClibEccValueError, match="invalid size for compressed point: "
        ):
            point_from_octets(Q_bytes, ec)

    # invalid x_Q coordinate
    ec = CURVES["secp256k1"]
    x_Q = 0xEEFDEA4CDB677750A420FEE807EACF21EB9898AE79B9768766E4FAA04A2D4A34
    xstr = format(x_Q, "32X")
    with pytest.raises(BTClibEccValueError, match="invalid x-coordinate: "):
        point_from_octets(f"03{xstr}", ec)
    with pytest.raises(BTClibEccValueError, match="point not on curve: "):
        point_from_octets("04" + 2 * xstr, ec)
    with pytest.raises(BTClibEccValueError, match="point not on curve"):
        bytes_from_point((x_Q, x_Q), ec)
    with pytest.raises(BTClibEccValueError, match="point not on curve"):
        bytes_from_point((x_Q, x_Q), ec, False)


def test_hybrid_prefixes_are_admitted_only_when_asked() -> None:
    """0x06 and 0x07 are SEC 1 too, and consensus takes them.

    The bindings' ec_pubkey_parse takes all three 65-byte prefixes
    (eckey_impl.h), and Core refuses the hybrid pair only under STRICTENC, so a
    script spending to one must verify -- the script_tests.json vector "P2PK NOT
    with hybrid pubkey but no STRICTENC" is the generator with a 0x06 in front,
    and the Python path could not parse it at all (issue btclib-org/btclib#129).
    Off by default because an address, a WIF and a descriptor have no hybrid
    form to render.
    """
    ec = CURVES["secp256k1"]
    Q = ec.G
    body = Q[0].to_bytes(ec.p_size, byteorder="big", signed=False)
    body += Q[1].to_bytes(ec.p_size, byteorder="big", signed=False)
    prefix = b"\x07" if Q[1] & 1 else b"\x06"
    mismatched = b"\x06" if Q[1] & 1 else b"\x07"

    assert point_from_octets(prefix + body, ec, hybrid=True) == Q
    assert point_from_octets((prefix + body).hex(), ec, hybrid=True) == Q

    with pytest.raises(BTClibEccValueError, match="not a point: prefix "):
        point_from_octets(prefix + body, ec)

    # the prefix repeats the parity of the y that follows it, so the two
    # can contradict each other, and then it is not a point
    with pytest.raises(BTClibEccValueError, match="against the hybrid prefix "):
        point_from_octets(mismatched + body, ec, hybrid=True)

    # and 0x04 does not acquire a parity rule it never had
    assert point_from_octets(b"\x04" + body, ec, hybrid=True) == Q
    assert point_from_octets(b"\x04" + body, ec) == Q


def test_bytes_from_prv_key_int() -> None:
    """It composes mult and bytes_from_point, so it must answer as they do.

    For secp256k1 it does not: it calls the bindings' pubkey_from_prvkey
    directly, without ever building a point of this module's own (issue
    btclib-org/btclib#459), which is why the equality is asserted here scalar by
    scalar rather than taken as read.
    """
    ec = CURVES["secp256k1"]
    prefixes = set()
    for q in range(1, 13):
        Q = mult(q, ec.G, ec)
        assert bytes_from_prv_key_int(q) == bytes_from_point(Q, ec)
        assert bytes_from_prv_key_int(q, ec, False) == bytes_from_point(Q, ec, False)
        prefixes.add(bytes_from_prv_key_int(q)[0])
    # 6G is the first odd y of the twelve, so both prefixes are covered,
    # i.e. both answers of the parity rule and not one of them twice
    assert prefixes == {0x02, 0x03}

    # the edges of the scalar range, and the reduction mod n that mult
    # applies and this has to keep applying
    for q in (1, ec.n - 1):
        assert bytes_from_prv_key_int(q) == bytes_from_point(mult(q, ec.G, ec), ec)
        assert bytes_from_prv_key_int(q + ec.n) == bytes_from_prv_key_int(q)

    # an Integer, not an int: the octets of a scalar are that scalar
    q_bytes = (ec.n - 1).to_bytes(32, byteorder="big", signed=False)
    assert bytes_from_prv_key_int(q_bytes) == bytes_from_prv_key_int(ec.n - 1)
    assert bytes_from_prv_key_int(q_bytes.hex()) == bytes_from_prv_key_int(ec.n - 1)

    # every other curve is the Python path, which is the composition
    for ec in (CURVES["secp256r1"], low_card_curves["ec13_11"]):
        for q in range(1, min(ec.n, 13)):
            Q = mult(q, ec.G, ec)
            assert bytes_from_prv_key_int(q, ec) == bytes_from_point(Q, ec)
            assert bytes_from_prv_key_int(q, ec, False) == bytes_from_point(
                Q, ec, False
            )

    # a zero scalar is the infinity point, on either path, and the
    # bindings reject it rather than answering a serialization of it
    for ec in (CURVES["secp256k1"], low_card_curves["ec13_11"]):
        for q in (0, ec.n):
            with pytest.raises(
                BTClibEccValueError,
                match="no bytes representation for infinity point",
            ):
                bytes_from_prv_key_int(q, ec)


def test_infinity_point_bytes() -> None:
    """Refuse to serialize the point at infinity."""
    with pytest.raises(
        BTClibEccValueError, match="no bytes representation for infinity point"
    ):
        bytes_from_point(INF)


def test_infinity_point_from_octets() -> None:
    """Refuse an uncompressed encoding spelling the point at infinity."""
    curve_size = CURVES["secp256k1"].p_size
    inf_bytes = b"\x04"
    inf_bytes += INF[0].to_bytes(curve_size, byteorder="big", signed=False)
    inf_bytes += INF[1].to_bytes(curve_size, byteorder="big", signed=False)
    with pytest.raises(
        BTClibEccValueError, match="no bytes representation for infinity point"
    ):
        point_from_octets(inf_bytes)


def test_point_from_pub_key_refuses_a_point_outside_the_subgroup() -> None:
    """A point outside ⟨G⟩ is not a public key, on a curve with a cofactor.

    secp112r2 is cofactor 4, and its own order-4 point is on the curve --
    `bytes_from_point` serializes it without complaint -- but not a point
    of ⟨G⟩, `n*T` not being INF: `mult` would answer `dU*T` reduced mod n,
    a wrong point for any dU, which is the whole of issue
    btclib-org/ellipticcurves#15. Every spelling that reaches a point --
    the bare tuple, the compressed octets, the uncompressed ones -- is
    refused the same way.
    """
    ec = CURVES["secp112r2"]
    t = secp112r2_order_4_point()
    err_msg = "point not in the subgroup generated by G"

    with pytest.raises(BTClibEccValueError, match=err_msg):
        point_from_pub_key(t, ec)
    with pytest.raises(BTClibEccValueError, match=err_msg):
        point_from_octets(bytes_from_point(t, ec, compressed=False), ec)
    with pytest.raises(BTClibEccValueError, match=err_msg):
        point_from_octets(bytes_from_point(t, ec, compressed=True), ec)

    # a point of ⟨G⟩ itself is unaffected, on the very same curve
    assert point_from_pub_key(ec.G, ec) == ec.G


@pytest.mark.parametrize(
    "curve_name, order_4_point",
    [
        ("secp112r2", secp112r2_order_4_point),
        ("secp128r2", secp128r2_order_4_point),
    ],
)
def test_point_from_octets_refuses_the_real_two_torsion_point(
    curve_name: str, order_4_point: Callable[[], Point]
) -> None:
    """The compressed encoding of a real two-torsion x is refused too.

    `_y_even_var` lifts that x to y == 0 without complaint -- it is a
    genuine square root of `_y2(x)`, 0 included -- building exactly the
    tuple `Curve.is_on_curve` refuses as ambiguous with INF for the 0x02
    prefix, and an out-of-range `ec.p - 0 == ec.p` for 0x03's negated
    one. The compressed branch of `point_from_octets` used to go straight
    to `_assert_in_subgroup` without asking `is_on_curve` first, where
    the uncompressed branch a few lines below already did:
    `_assert_in_subgroup` itself does not catch either shape --
    `_jac_from_aff` reads affine y == 0 as Jacobian Z == 0 exactly as the
    convention this refuses does, and it never reduces y at all -- so
    both compressed keys passed silently (issue
    btclib-org/ellipticcurves#16). Both prefixes, and both entry points,
    are checked; the hybrid and plain uncompressed forms are refused
    already -- no bytes representation exists for a y == 0 uncompressed
    point at all, ambiguous or not -- and are checked here too so a
    regression there is caught the same way.
    """
    ec = CURVES[curve_name]
    t = order_4_point()
    t2 = ec.add_var(t, t)
    assert t2[1] == 0
    x_bytes = t2[0].to_bytes(ec.p_size, byteorder="big")

    def refused(octets: bytes, err_msg: str) -> None:
        with pytest.raises(BTClibEccValueError, match=err_msg):
            point_from_octets(octets, ec)
        # point_from_pub_key's octets branch translates whatever
        # point_from_octets raises into its own "not a public key",
        # chaining the original as __cause__ (never echoing the octets,
        # which may be private material passed by mistake)
        with pytest.raises(BTClibEccValueError, match="not a public key") as exc:
            point_from_pub_key(octets, ec)
        assert err_msg in str(exc.value.__cause__)

    # 0x02 lifts the two-torsion x to y == 0 itself, the tuple
    # Curve.is_on_curve refuses as ambiguous with INF
    refused(b"\x02" + x_bytes, "ambiguous point")
    # 0x03 negates that same y to ec.p - 0 == ec.p, out of range rather
    # than ambiguous -- a different refusal, equally not a silent accept
    refused(b"\x03" + x_bytes, "y-coordinate not in 1..p-1")

    y_bytes = (0).to_bytes(ec.p_size, byteorder="big")
    inf_msg = "no bytes representation for infinity point"
    with pytest.raises(BTClibEccValueError, match=inf_msg):
        point_from_octets(b"\x04" + x_bytes + y_bytes, ec)
    with pytest.raises(BTClibEccValueError, match="not a public key") as exc:
        point_from_pub_key(b"\x04" + x_bytes + y_bytes, ec)
    assert inf_msg in str(exc.value.__cause__)
    # hybrid has no point_from_pub_key spelling: that function takes no
    # hybrid flag, so 0x06 there is "not a point" rather than this refusal
    with pytest.raises(BTClibEccValueError, match=inf_msg):
        point_from_octets(b"\x06" + x_bytes + y_bytes, ec, hybrid=True)


@pytest.mark.parametrize(
    "bindings",
    [
        pytest.param(True, marks=needs_bindings, id="bindings"),
        pytest.param(False, id="python"),
    ],
)
def test_mult_sec(bindings: bool, monkeypatch: pytest.MonkeyPatch) -> None:
    """m*P from the octets is m*P from the point, on every curve.

    `_mult_sec` skips the round trip `mult(m, point_from_octets(sec))`
    makes -- the lift on the way in and the serialization back out, of a
    point neither side reads a coordinate of -- so what has to be asserted
    is that identity, for both forms of the octets and for the scalars the
    bindings decline: zero, which is infinity and no libsecp256k1 answer,
    and the ones landing on the point itself.

    The low-cardinality curves reach the same lines with no bindings under
    them at all, which is what the `python` case then repeats for
    secp256k1.
    """
    if not bindings:
        monkeypatch.setattr(curve, "_libsecp256k1_available", False)

    for ec in all_curves.values():
        for Q in (ec.G, mult(2, ec.G, ec), mult(3, ec.G, ec)):
            for compressed in (True, False):
                sec = bytes_from_point(Q, ec, compressed)
                for m in (0, 1, 2, ec.n - 1):
                    assert _mult_sec(sec, m, ec) == mult(m, Q, ec)

    # every width of a secp256k1 scalar, where the bindings arm is
    # `secp256k1_ecdh`; and a scalar at or above n, which it refuses and
    # the fallthrough reduces
    ec = CURVES["secp256k1"]
    Q = mult(7, ec.G, ec)
    sec = bytes_from_point(Q, ec)
    for w in (256, 128, 64, 32, 1):
        m = (1 << (w - 1)) | (0x5A5A5A5A5A5A5A5A % (1 << (w - 1)))
        assert _mult_sec(sec, m % ec.n, ec) == mult(m, Q, ec)
    assert _mult_sec(sec, ec.n + 2, ec) == mult(2, Q, ec)

    # and octets that are no point at all are the lift's refusal, which is
    # what the fallthrough exists to keep saying
    ec = CURVES["secp256k1"]
    x_Q = 0xEEFDEA4CDB677750A420FEE807EACF21EB9898AE79B9768766E4FAA04A2D4A34
    with pytest.raises(BTClibEccValueError, match="invalid x-coordinate: "):
        _mult_sec(b"\x02" + x_Q.to_bytes(ec.p_size, "big"), 2, ec)


@pytest.mark.parametrize(
    "bindings",
    [
        pytest.param(True, marks=needs_bindings, id="bindings"),
        pytest.param(False, id="python"),
    ],
)
def test_mult_pub_key(bindings: bool, monkeypatch: pytest.MonkeyPatch) -> None:
    """m*P for a public key of any spelling, the scalar checked and reduced.

    The two twins it composes are asserted above; what is left is the
    public spelling's own part: every form of `PubKey`, a scalar as any
    `Integer` and reduced mod n, and a key that is no point refused as a
    `BTClibEccValueError` whichever form it arrived in.
    """
    if not bindings:
        monkeypatch.setattr(curve, "_libsecp256k1_available", False)

    ec = CURVES["secp256k1"]
    Q = mult(3)
    for pub_key in (
        Q,
        PreparedPoint(Q),
        bytes_from_point(Q),
        bytes_from_point(Q, compressed=False),
        bytes_from_point(Q).hex(),
    ):
        assert mult_pub_key(5, pub_key) == mult(5, Q)
        assert mult_pub_key(ec.n + 5, pub_key, ec) == mult(5, Q)
        assert mult_pub_key("05", pub_key) == mult(5, Q)
        assert mult_pub_key(0, pub_key) == INF

    x_Q = 0xEEFDEA4CDB677750A420FEE807EACF21EB9898AE79B9768766E4FAA04A2D4A34
    for not_a_point in (
        b"\x02" + x_Q.to_bytes(ec.p_size, "big"),
        (ec.G[0], ec.G[1] + 1),
        INF,
    ):
        with pytest.raises(BTClibEccValueError):
            mult_pub_key(5, not_a_point)

    with pytest.raises(BTClibEccTypeError):
        mult_pub_key(1.5, Q)  # type: ignore[arg-type]
    with pytest.raises(BTClibEccTypeError):
        mult_pub_key(5, 7)  # type: ignore[arg-type]


def test_a_scalar_is_an_int_or_its_octets_and_nothing_else() -> None:
    """What a private key may be spelled as here (btclib-org/btclib#1188).

    The integer, its `n_size` octets, their hex, and the buffers
    `bytes_from_octets` takes beside them. A WIF and an extended key are
    not among them: each carries a network, and this file knows about a
    curve and not about bitcoin, so it could not decode one without
    importing a layer above itself.

    On secp256k1 the size alone separates a scalar from a point --
    `n_size` is 32 where a point is 33 or 65. That is a coincidence and
    not a rule: `sec_point` names the catalogued curves whose `n_size`
    is their compressed size, and there a point is refused by the range
    check instead.
    """
    q = 0xC0FFEE
    octets = q.to_bytes(32, "big")
    for spelling in (q, octets, octets.hex(), bytearray(octets), memoryview(octets)):
        assert scalar_from_prv_key(spelling) == q

    # a WIF and an xprv reach here as text, and text is hex or nothing;
    # the xprv is BIP32's root key of the seed `"5e" * 32`
    xprv = (
        "xprv9s21ZrQH143K3jDQ9kSBrkWCHhPnhmGaTk3LkDNedVbXcXMERAJzNVtb8oi8f3k"
        "mzhNe8gj7WMbGNpsRRbE59dWU27jWqmKvFsg7A4vgdAD"
    )
    for text in (b58encode(b"\x80" + q.to_bytes(32, "big") + b"\x01").decode(), xprv):
        with pytest.raises(BTClibEccValueError, match="invalid hex string"):
            scalar_from_prv_key(text)

    for out_of_range in (0, secp256k1.n):
        with pytest.raises(BTClibEccValueError, match="private key not in 1..n-1"):
            scalar_from_prv_key(out_of_range)


def test_a_public_key_is_a_point_or_its_octets_and_nothing_else() -> None:
    """What a public key may be spelled as here (btclib-org/btclib#1188).

    `scalar_from_prv_key`'s twin above, asked of the other half: the
    point as a tuple, as a `PreparedPoint`, or as the SEC octets
    `point_from_octets` parses. A WIF and an extended key are not among
    them for that test's reason, and neither is a scalar -- in this
    library an int is a private key and never a public one, so it is
    refused as a type rather than reported as a key that does not verify.

    What a caller does with the point afterwards -- an address, a
    verification -- is its own module's test; what is here is the parse
    itself.
    """
    q = 0xC0FFEE
    point = mult(q)
    for spelling in (
        point,
        PreparedPoint(point),
        bytes_from_point(point),
        bytes_from_point(point, compressed=False),
        bytes_from_point(point).hex(),
        bytearray(bytes_from_point(point)),
    ):
        assert point_from_pub_key(spelling) == point

    # a type no spelling has, the scalar among them: refused as a type, and
    # never echoed -- it may be the private material issue btclib-org/btclib#143
    # is about
    for wrong_type in (q, 1.5, None):
        with pytest.raises(BTClibEccTypeError, match="not a public key"):
            point_from_pub_key(wrong_type)  # type: ignore[arg-type]

    # a tuple of the right shape that is no point of the curve, and the
    # infinity point, which has no public key
    for not_a_point in ((1, 2), INF):
        with pytest.raises(BTClibEccValueError, match="not a valid public key"):
            point_from_pub_key(not_a_point)

    # octets of a declared type whose content is no point: a value error,
    # and the parse's own reason is chained under it
    with pytest.raises(BTClibEccValueError, match="not a public key"):
        point_from_pub_key(
            b58encode(b"\x80" + q.to_bytes(32, "big") + b"\x01").decode()
        )
