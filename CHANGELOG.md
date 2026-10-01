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

### The OpenSSF Baseline badge

`README.md`'s badge row ends with the OpenSSF Baseline badge, beside the
Best Practices badge, section 2 of the organization standard admitting it
on the same property (issue btclib-org/.github#1460).

### `pypi-install.yml` retries the install of the version the release published

Each install cell runs `pip install btclib-ecc==<version>` through
btclib-org/.github's `install_published_release.py`, which retries only while
the installer says the pin is not resolvable (issue btclib-org/.github#1458).

### The release's attestation bundle is attached as `*.intoto.jsonl`

`RELEASING.md`'s verification and recovery commands name the bundle
`<tag>.intoto.jsonl`, the name `reusable-github-release.yml` attaches it under
(issue btclib-org/.github#1468).

### `codeql.yml`'s aggregate runs `check_run_jobs.py`

The aggregate's step runs `check_run_jobs.py`, which reads the run's jobs
listing again up to a deadline while a row of `analyze` is unfinished
(issue btclib-org/.github#1463).

### `generate_sbom.py` carries a not-affected list into the bill of materials

`generate_sbom.py` reads `.github/vex.toml`, where the tree lists the
vulnerabilities its release is not affected by, into the document's
`vulnerabilities`; no list, no key (issue btclib-org/.github#1469).

### `SECURITY.md` promises a response time

`SECURITY.md` says a report is acknowledged within 7 days, and a fix or a
published advisory within 90 (issue btclib-org/.github#1460).

### MuSig2 refuses a signer index outside its participant arrays

`partial_sig_verify` raises `BTClibEccValueError` when the signer index is
negative or at least the number of public keys, instead of selecting from the
end or leaking `IndexError` (closes #78).

### `release.yml` audits the lock before it publishes

The `audit` job calls btclib-org/.github's `reusable-audit.yml`, which runs
`uv audit` over what the wheel declares, and both publish jobs wait for its
success (issue btclib-org/.github#1466).

### `CLAUDE.md` carries the shared primary-checkout section

The section *The primary checkout is the maintainer's* is the organization's
shared text, and the *Model* section names only the model to use (issue
btclib-org/.github#1494).

### `generate_sbom.py` is btclib-org/.github's

The `dist` job writes the bill of materials with btclib-org/.github's
`generate_sbom.py`, served from `main`, and the tree keeps no copy of it
(issue btclib-org/.github#1478).

### `CLAUDE.md` names both aggregates a draft pull request fails

`codeql: every job passed` fails a draft as `test: every job passed` does;
only the second is a required check on `main` (issue
btclib-org/.github#1494).

### `Dependency review` is a required check

- **`REPOSITORY.md` reads `lint / Dependency review` back with the other
  required checks** (issue btclib-org/.github#1465).

### `[tool.uv] required-version` is `>=0.12.18`

- **`required-version` reads `>=0.12.18`, not `>=0.12.19`** (issue
  btclib-org/.github#1482): the Dependabot service refused `0.12.19` with
  `tool_version_not_supported`.

### `SECURITY.md` names the latest security review

`SECURITY.md` gives the date of the latest security review and links the issue
that records it (issue btclib-org/.github#1362).

### The curve constructor tests p and n with Baillie-PSW

A base-2 Fermat pseudoprime such as 341 or 561 is refused as p or n
(closes #80).

### A hybrid public key is refused on both arms

`mult_pub_key`, `ecies.derive_keys`, `dsa.assert_as_valid`,
`dsa.assert_as_valid_` and `dsa.sign_` raise `BTClibEccValueError` for a key
with the prefix `0x06` or `0x07`, as `point_from_octets` does (closes #75).

## v2026.9.30

### Vendored-vector pins follow upstream's tip

Every entry of `tests/_data/README.md` the weekly job reports behind is
pinned at upstream's tip, and no vendored content changes (closes #48).

### `[tool.uv] required-version` follows the `uv` `dependabot-core` bundles to `0.12.19`

`required-version` reads `>=0.12.19`: a floor below the `uv` pin
`dependabot-core` bundles admits a `uv` older than the one Dependabot writes
`uv.lock` with (issue btclib-org/.github#1438).

### `REPOSITORY.md` reads back the imported Read the Docs project

`btclib-ecc.readthedocs.io` serves the documentation, and *Read the Docs*
records the project's settings with the answers their read-backs give
(issue #51).

### `RELEASING.md`'s bundle verification names the signer workflow

The `--bundle` form of *Verify the provenance of an asset* passes
`--signer-workflow "$signer"`, without which `gh attestation verify` refuses
a good release (issue btclib-org/.github#1446).

### A `btclib-secp256k1` too old to import says which version and what to install

An installed release lacking a name `_libsecp256k1` imports still raises, and
the `ImportError` names the installed version, the floor the `secp256k1` extra
declares and how to meet it, instead of the missing symbol alone (closes #56).

### `CONTRIBUTING.md` points a newcomer at `good first issue`

The shared half takes `btclib-org/.github`'s paragraph on the label and its
one search across the organization (issue btclib-org/.github#1362, closes #53).

### `.clusterfuzzlite/.python-version` pins the fuzz image's interpreter

`.clusterfuzzlite/.python-version` names `3.11`, the fuzz image's interpreter,
so that the Dependency Graph's pip job there reads it rather than a root pin
Dependabot does not support yet (issue btclib-org/.github#1436).

### The README carries the OpenSSF Best Practices badge

The row links the tree's bestpractices.dev registration (closes #1).

### An assurance case, and a first use the suite runs

`ASSURANCE_CASE.md` argues the threat model, the trust boundaries and the
design principles, and the README shows a signature made and verified,
which `tests/readme_test.py` runs (issue #52).

### `RELEASING.md`'s griffe step searches `src`

`griffe check` takes `-s . -s src`, the pair `release.yml`'s `public-api`
job passes, where it answered `ModuleNotFoundError` for the previous
release (issue btclib-org/.github#1447).

### `pypi-install.yml` installs the version the release published

The install names `btclib-ecc==<version>` from the tag `release.yml` passes,
where a bare name let a lagging index serve the release before it
(issue btclib-org/.github#1456).

## v2026.9.28

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

### `Curve()` accepts a cofactor Hasse's bound cannot pin down on its own

The constructor now checks `cofactor*n` against Hasse's bound, in place
of refusing every cofactor but the interval's largest multiple of `n`,
wrong wherever several multiples fit (closes #19).

### `tonelli_var` and `mod_sqrt_var` raise, not hang, on a composite p

The z search is bounded at p, and the inner loop raises
`BTClibEccValueError` when it is exhausted, instead of an outer loop
that ran forever past the "p must be a prime" precondition (closes #9).

### `kdf`, `tagged_hash`, `ecies.encrypt` and `sign` refuse a malformed input

A bare `bytes`, `bytearray` or hash function used to leak a builtin
`TypeError` for a malformed input in `kdf`, `hashes.tagged_hash`,
`ecies.encrypt` and the two `sign`s; each now refuses it by name (issue #11).

### `signed_odd_digits` refuses a non-integer `m`, `w` or `size`

A non-integer used to leak a bare builtin `TypeError` from the comparisons
guarding the recoding; each of the three is now checked and refused as a
`BTClibEccTypeError` ahead of them (closes #34).

### `_libsecp256k1` no longer reads an installed, too-old package as absent

Only `ModuleNotFoundError` naming `btclib_secp256k1` itself means absent; a
name an older, installed package lacks now raises instead of a silent
fallback (closes #25).

### `ec17_13` and `ec19_13`'s test fixtures carry their true cofactor, 1

A genuinely cofactor-2 curve this small has a two-torsion point
`is_on_curve` refuses outright, which an exhaustive sweep reaches;
`secp112r2` carries the cofactor above 1 case now (closes #32).

### `Curve.__init__`'s `order_check` no longer mistakes 2n for n

`_mult_jac_var`, never leaving Jacobian coordinates, replaces the windowed
`_mult`, whose affine table of odd multiples of `G` could hold the curve's
own two-torsion point and read it as infinity (closes #39).

### `_assert_in_subgroup` no longer mistakes 2n for n

The same collision `order_check` was fixed against, at the call site that
confines a parsed public key to ⟨G⟩ on a cofactor > 1 curve: `_mult_jac_var`
replaces the windowed `_mult` there too (closes #42).

### The repository is `btclib-org/btclib-ecc`, not `btclib-org/ellipticcurves`

GitHub's repository was renamed to match the PyPI distribution; every
hardcoded reference in this tree, from `release.yml`'s publish guards to
its own issue citations, now reads `btclib-org/btclib-ecc`.

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
