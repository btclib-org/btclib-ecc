# Release notes

Notable changes are documented here.
[CHANGELOG.md](./CHANGELOG.md) is the record behind them: this file says
what a user has to act on, that one says what changed.

Versions are *[calendar versions](https://calver.org/)*, `YYYY.M.D`: the
number says when a release was cut, and promises nothing about
compatibility, so a breaking change is announced in this file — read it
before upgrading, rather than a digit.

## v2026.10 (work in progress, not released yet)

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
