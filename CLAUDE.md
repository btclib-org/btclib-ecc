# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working
with code in this repository.

How to work here — what the issue tracker takes, the prose style, and how
a pull request is opened and landed — is `CONTRIBUTING.md`, which is the
same file in every repository of the organization up to its last section,
which is this tree's and holds the commands and the gates. Repository
configuration is `REPOSITORY.md`: read it before changing a workflow, a
branch rule or a setting. Reviewing is `REVIEWING.md`, and `/review` is
that file as a command; read it before reviewing a pull request and
before opening one, since it is what the pull request will be answered
against.

## Architecture

`src/btclib_ecc/` is the package, and it imports nothing of this
organization's other packages but the optional `btclib_secp256k1`: it is
the arithmetic they are built on, and `tests/imports_test.py` imports each
module alone to hold that.
`btclib-secp256k1` is an optional extra, never a dependency.

Layers, bottom-up: `number_theory` and `hashes`, then `curves/` (curve
arithmetic, SEC 1 octet encodings), then `ecc/` (dsa, ssa, musig2, frost,
dleq, dh, ellswift, ecies, pedersen, borromean, rangeproof, and the
rfc6979, bip340 and sign-to-contract nonces). `ecc` imports `curves`, and
never the reverse. `alias`, `exceptions` and the private `_utils` are the
substrate every layer uses, and `_libsecp256k1` is the one module that
imports the bindings at run time.

secp256k1 arithmetic is delegated to the bindings conditionally, which is
the single most important thing to know before touching `curves/` or
`ecc/`. One predicate, `curves.curve._libsecp256k1_serves`, asks for a
process-wide switch, secp256k1 as the curve and sha256 or no hash
function; each call site ands its own conditions onto it, and
`SECURITY.md`'s "Limitations, not vulnerabilities" states them. What the
predicate declines runs the Python arithmetic of `curves/curve_group.py`,
which is not dead code and not constant-time: it serves every other
curve, other hash functions and caller-supplied nonces, and the suite
validates it against the bindings, which are the authority on the
answer. `BTCLIB_ECC_NO_LIBSECP256K1` in the environment turns the
switch off from the first call.

## The primary checkout is the maintainer's

Never work in it: no edit, no `git add`, no commit, no branch switch, no
rebase, no `git stash` — the hooks fix files in place. The one write
allowed there brings it forward, and only while it is on `main` and
`git status --porcelain` prints nothing; where it is not, stop:

```shell
checkout=<checkout>
```

```shell
git -C "${checkout:?}" pull --ff-only
```

Read it only after that, once this prints one sha twice:

```shell
git -C "${checkout:?}" rev-parse HEAD origin/main
```

A measurement that has to hold at a named revision reads
`git -C "${checkout:?}" show <sha>:<path>` instead.

Every session works in a worktree of its own, from its first edit, named
`wt-<tracker>-<issue>-<repo>-<role>` — `wt-github-255-btclib-writer` for
issue 255 of `btclib-org/.github`'s tracker, worked in `btclib` by a
writer. The environment is created there, with the command `CONTRIBUTING.md`
names under *The environment and the gates*. Every path is written out in
full, `<scratchpad>` being the session's scratch directory:

```shell
git worktree add \
  <scratchpad>/wt-<tracker>-<issue>-<repo>-<role> origin/main -b <branch>
```

Removing it is part of finishing:

```shell
git worktree remove --force <scratchpad>/wt-<tracker>-<issue>-<repo>-<role>
```

`refs/stash` and the local `main` are shared by every worktree: never
`git stash`, and move `main` only by the `git pull --ff-only` above.

## Model

Default model: Sonnet; Opus for design decisions with conflicting
constraints. Do not use Fable unless instructed.

## Non-obvious facts that will otherwise waste a session

- **A branch's CI run can be `cancelled` rather than green.** `test.yml`'s
  concurrency group is
  `test-${{ github.event.pull_request.number || github.ref }}` (plus a
  release-only suffix) with cancel-in-progress, so the next push kills
  the run for the previous commit. The local gates are the evidence;
  `cancelled` is not `failure`.
- **A draft pull request is checked by nothing but aggregates that fail
  to say it is a draft.** The jobs doing work decline a draft in their
  `if:`; `test: every job passed` and `codeql: every job passed` run
  anyway and fail on their first step, so they read red rather than
  skipped. Only the first is a required check on `main`. Mark the pull
  request ready to be checked.
- **mypy is a *local* hook shelling out to uv on purpose.** The
  mirrors-mypy hook injects `--ignore-missing-imports`, and it type
  checks in an isolated environment where the project is not installed —
  so `import btclib_ecc` in a test would be `Any` and every assertion
  about it would pass vacuously.
- **The version is declared once**, in `pyproject.toml`.
  `docs/source/conf.py` parses that file (not the metadata, which would
  need the package installed).

## Conventions to match

Section 9 of `btclib-org/.github` is the prose style and section 10 its
workflow conventions, and neither is re-listed here, that section's own
*One fact in one place* being the reason. They govern the workflows and
the pre-commit config as much as the docstrings. `actionlint` and
`zizmor` read the workflows as hooks of the lint gate, so a finding from
either fails a commit rather than reporting one.

## Verifying

Run the command as documented before claiming it works, and read its exit
code rather than its filtered output, for the reason `CONTRIBUTING.md`'s
*This repository in particular* gives.
