# Release notes

Notable changes are documented here.
[CHANGELOG.md](./CHANGELOG.md) is the record behind them: this file says
what a user has to act on, that one says what changed.

Versions are *[calendar versions](https://calver.org/)*, `YYYY.M.D`: the
number says when a release was cut, and promises nothing about
compatibility, so a breaking change is announced in this file — read it
before upgrading, rather than a digit.

## v2026.10 (work in progress, not released yet)

- **`mult_pub_key`, `ecies.derive_keys`, `dsa.assert_as_valid`,
  `dsa.assert_as_valid_` and `dsa.sign_`'s `pub_key` refuse a hybrid public
  key (prefix `0x06` or `0x07`) as `not a public key`** (closes #75). With
  `btclib-secp256k1` installed they accepted it, and without it they refused
  it.

  Act on it if you pass such a key: convert it first, with
  `point_from_octets(key, hybrid=True)`, and pass the point.

- **`pedersen.verify` raises `BTClibEccValueError` for a generator off the
  curve, at infinity or, on a cofactor curve, outside the subgroup generated
  by G** (closes #76). Before, it answered False for an off-curve generator
  and True for an opening under INF, which opens to every value.
  On a cofactor curve `second_generator` returns a different H where its old
  H was outside the subgroup, as at sha256 on secp112r2 and secp128r2.

  Act on it if you pass a generator of your own: pass one from
  `second_generator` or `generator_from_seed`, or catch `BTClibEccValueError`.
  Commitments made under that old H no longer verify.

## v2026.9.30

No breaking changes. An installed `btclib-secp256k1` older than the floor
the `secp256k1` extra names still fails the import, and its `ImportError`
now names the installed version and that floor: upgrade `btclib-secp256k1`,
or install `btclib-ecc[secp256k1]`.

## v2026.9.28

### Breaking changes

- **`_utils.int_from_integer` and `hex_string` refuse a `0x` string whose
  digits are not ASCII hex, as `invalid hex integer: what follows 0x is
  not ASCII hex digits`** (closes #21). Before, `int(i, 16)` alone read
  `0x1_0`, and `0x` followed by fullwidth or Arabic-Indic digits, as 16,
  and quoted the string in its refusal. Only ASCII whitespace is
  stripped now: a `0x` string padded with U+00A0, U+3000 or another
  character `str.isspace` counts, ahead of the prefix or after its
  digits, is refused too — by the message above, or by `bytes.fromhex`'s
  own where the padding leaves neither a `0x` spelling nor valid hex.
  Every `Integer` parameter reads through here, `curve.mult`'s private
  key `m` among them.

  Act on it if you pass such a string, or match this refusal's text: pass
  ASCII hex digits, and match `invalid hex integer` alone rather than the
  string it used to quote.

## v2026.9.26

The first release of `btclib-ecc`: there is no earlier version of it
to upgrade from.
