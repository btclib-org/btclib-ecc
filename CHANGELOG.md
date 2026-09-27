# Changelog

<!-- markdownlint-configure-file
  {
    // MD024/no-duplicate-heading - every release repeats the same few
    // headings, which is what keeps the page readable scrolling down it;
    // only a duplicate under the same release heading would be the
    // accident this rule looks for
    "MD024": { "siblings_only": true }
  }
-->

An entry for anything a reader would notice: what changed, and the issue
it answers. That is section 9 of [the organization standard][std], and it
is narrower than "every change" — a comment reworded inside a workflow
changes nothing a reader of this repository meets, and lands without an
entry. [RELEASE_NOTES.md](./RELEASE_NOTES.md) has the release notes,
which say what a user has to act on; this file is the record behind them.

[std]: https://github.com/btclib-org/.github

Neither file states how many entries it holds: a stated number is a line
every open branch has to edit, and the two files carry a union merge
driver that would keep both sides' numbers.

## v2026.10 (work in progress, not released yet)

### `REVIEWING.md` lets a filed issue carry its fix

An issue filed from a review may say the fix where one is known: *What is
filed, and what is not* dropped its "no fix", the filing bar standing as it
was (issue btclib-org/.github#1378).

### `codeql.yml`, `REPOSITORY.md` and `dependabot.yml` follow sections 10 and 11

The aggregate accepts `analyze`'s lagging rows (issue btclib-org/.github#1395),
signatures and SHA pinning are read back (issue btclib-org/.github#1409), and
`pre-commit` is an ecosystem left unused (issue btclib-org/.github#1391).

### The fuzz image is pinned by digest, and Dependabot moves it

`.clusterfuzzlite/Dockerfile` builds from `base-builder-python:latest`
pinned to its digest (closes #12), and `dependabot.yml`'s `docker` block is
what proposes the next one (issue btclib-org/.github#1405).

### `codeql.yml` rereads a lagging row and fails on a failed `needs` result

An `analyze` row listed unfinished is read again before it is accepted
(issue btclib-org/.github#1416), and an `analyze` result other than
`success` or `skipped` fails the step (issue btclib-org/.github#1424).

### `REPOSITORY.md` records the `btclib-ecc`/`ellipticcurves` naming exception

Section 3's name-equals-repository rule is declined here, with the
maintainer's decision and its citation, rather than left unexplained
(closes #17).

### The fuzz build installs from `uv.lock`, not the index

`.clusterfuzzlite/build.sh` installs `requirements.txt`, `uv.lock`'s base
dependencies exported with their hashes, with `--require-hashes --no-deps`
before the package itself, instead of resolving off the index (closes #13).

### `_utils.int_from_integer` reads only ASCII hex digits after `0x`

Only ASCII whitespace is stripped, and the refusal no longer quotes the
string, which may be a private key (closes #21).

### `Sig.parse` refuses a long-form or oversized DER length under strict

A DER length octet at 0x80 or above, or an oversized r,s total, is refused
under `strict` instead of CompactSize; errors now name the DER length, not
`var_int` or a psbt caller this tree lacks (closes #8) (closes #14).

### `is_on_curve` and the two cofactor-4 curves get their missing checks

`is_on_curve` refuses an x outside `0..p-1` (closes #7) and a tuple
`(x, 0)` ambiguous with `INF` on a cofactor curve (closes #16); every
public key is confined to the subgroup `G` generates (closes #15).

### The fuzz build's own build backend installs from `uv.lock` too

`requirements.txt`'s `fuzz` group hashes it, and `build.sh` installs the
package `-e --no-build-isolation`, its own backend built from that hash
rather than the index (closes #24).

### `dh.diffie_hellman` validates `dU` before either arithmetic arm sees it

`dU` is read through `curves.scalar_from_prv_key`, and an infinity `QV` is
refused, before the bindings or the Python arithmetic can disagree on
either one (closes #10).

## v2026.9.26

### The repository opens

The package: elliptic curve arithmetic over any short Weierstrass curve,
the signature, commitment and key-agreement schemes built on it, and the
vectors they answer to (issue btclib-org/btclib#2282).

### `REPOSITORY.md` records what each read-back answers

Each read-back carries what it answered on 2026-09-26; classic
protection's also reads its force-push and deletion switches, and the
environments' their required reviewers (issue btclib-org/btclib#2282).

### The distribution is `btclib-ecc`, imported as `btclib_ecc`

Its exceptions are `BTClibEcc*` and its switch `BTCLIB_ECC_NO_LIBSECP256K1`;
the documentation is `btclib-ecc.readthedocs.io` (issue btclib-org/btclib#2282).
