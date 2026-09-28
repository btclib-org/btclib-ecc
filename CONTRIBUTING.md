# Contributing

What this repository holds in common with the others of the organization
— the toolchain, the lint gate, the tool tables behind it, the workflow
set and the branch rules — is stated once in the
[btclib-org repository standard](https://github.com/btclib-org/.github),
each rule with the alternative it was decided against. It binds this
repository, so a change departing from it is a divergence, and one filed
as an issue in that repository rather than here: a difference between two
repositories belongs to neither of them.

**This file is the same in every repository of the organization up to
its last section.** What is true of one tree only — the commands that
build its environment, the gates it runs, which of its workflows decide
a merge — is under that heading, and the comparison stops there.

How the organization decides, and who holds which role, is
[`GOVERNANCE.md`][governance]; what it intends to do, and what it
deliberately does not, is [`ROADMAP.md`][roadmap]. Both are the
organization's, one copy each beside the standard.

## The issue tracker

Where an issue is filed, and what an alignment finding has to name, is
[the standard's *What this repository is*][s-what]: an issue spanning
repositories, or whose subject is the standard, goes to
[btclib-org/.github](https://github.com/btclib-org/.github/issues), and
one about this tree alone stays here.

A finding noticed while doing something else goes where `REVIEWING.md`'s
*What is filed, and what is not* says, for an author as much as for a
reviewer: a pull request answering two questions cannot be accepted for
either.

## Documentation and comments

[Section 9 of the standard][s9] is the prose style, and it governs the
prose this tree ships — comments, docstrings and markdown. It is not
restated here: a second wording is the one that goes stale, which is
that section's own *One fact in one place*.

A commit message is prose this tree ships too, though section 9 does not
say so: [the only merge method the rule accepts][s11] puts it on `main`
as the landing commit's body, so what is written in one is read there
long after the branch is gone.

## Pull requests

What `main` accepts, and what it refuses to everyone, is [section 11 of
the standard][s11]. Run the gates locally before opening anything —
the last section of this file says which they are — because CI runs
exactly them, so a red run there is a local run that was not done.

What a pull request's title and description have to say about the issues
it closes, and why a manual link in the Development panel is a trap
neither of them shows, is [the standard's *What a pull request says it
is*][s-title]. Read it before opening one; it is the rule most often
found broken after the fact.

**Before it is opened, the branch's own commit subjects and bodies are
read against that same rule.** The description does not exist yet to
disagree with them, and [the standard][s-title] has the command that
scans the branch's own commit text for a verb in front of a reference.

**The two spellings are named here as well as there, against [section 9's
*One fact in one place*][s9]**, the paragraph above naming the section
and not the forms, which are the half a citation is got wrong in:
`(closes #N)` cites an issue the change closes, wherever the citation
sits — the title, the commit subject where [*Merge method*][s11] makes
that the thing that lands, and a `CHANGELOG.md` entry — and `(issue #N)`
cites, in those same places, an issue the change advances and does *not*
close. One token holds one meaning whichever file it sits in, so the
pair is chosen by what is true of the change rather than by which file
is being written, and a tree's own landed subjects are not what to copy
it from: nothing already landed is rewritten, so what a repository wrote
before the rule stays where it is.

`REVIEWING.md` is the standard a review is written against, and is this
file's other half. Read before opening a pull request, it is what the
pull request will be answered against.

`CHANGELOG.md` gets an entry for anything a reader would notice, and the
release notes move only for something a user has to *act* on, in the
repositories that publish.

Where that entry goes is [section 9][s9]'s — the end of the open
section — and no gate reads it: `check-changelog` is handed the file and
no base, so it cannot tell which entry the branch wrote. The open
section's headings, in the order the file holds them, a branch's own
last:

```shell
awk '/^## /{n++} n==1 && /^### /' CHANGELOG.md
```

`n==1` takes the open section, from the first `##` heading to the next,
and the scan is `/^## /` rather than `/^## v/`: a section headed
`## Unreleased` is no match for `/^## v/`, which counts from the first
release heading instead and prints a released section's entries — or
nothing, where the tree has released nothing — while reading as a
check that passed.

### One subject, opened as soon as it is written

A pull request answers one question. Issues that share a subject are one
pull request, closing each of them; issues that do not are one pull
request each, however small either of them is.

It is opened the moment it is written and verified — not held for the
previous one to be reviewed or to land, and not batched with the next. A
batch arrives as one reviewing job with several subjects, which is the
shape that costs the most to read; a finished pull request held back is
review that could have started and did not.

Working this way stacks branches, which is fine and costs one rule: a
child whose base was amended is moved with the old base named,

```shell
git rebase --onto <new-base> <old-base-sha> <child>
```

because a plain rebase replays the base's old commit inside the child,
and the forge then shows the base's old text as additions with nothing
red anywhere. Read the child's diff afterwards rather than trusting the
rebase, and retarget each child onto `main` as its parent lands.

### The landing queue

Where more than one pull request is open against this repository, only
one is carried to `main` at a time: rebased onto the tip, reviewed on
that head, and landed, while every other one waits, untouched, for its
turn. This governs which of several *already open* pull requests reaches
`main` next; *One subject, opened as soon as it is written* above governs
the moment before that, when a finished one is opened — the two do not
conflict, since a pull request is still opened without delay and still
waits its turn once several are open.

The reason is CI throughput, not the ack a waiting pull request keeps —
`REVIEWING.md`'s *The verdict* states what an ack belongs to, and
*Landing it* below states which rebase voids one. Every rebase queues
this repository's whole check matrix against the organization's ceiling
on concurrent jobs, so rebasing every waiting pull request after each
landing spends that capacity on runs the next landing invalidates
anyway, and delays the one pull request that is actually next: work
spent on a pull request that is not next is work that delays the one
that is. The ceiling's figure is `REPOSITORY.md`'s, under *Plan-gated
settings*, beside the command that re-derives it.

Order is cheapest and least contended first, most invasive last, so that
a large change does not sit at the head blocking everything behind it.

The maintainer may declare a bounded exception — several pull requests in
flight against one repository, for a named piece of work — trading the
cost above for throughput; it is recorded as a comment in
[btclib-org/.github](https://github.com/btclib-org/.github/issues), by
*The issue tracker* above, and holds only for the work it names.

### The review

A review is given promptly and on local evidence. It does not wait for
CI, does not report a check as a finding, and does not discuss a run at
all: whether CI is green is the author's business, once, at landing time.

The exchange is anchored to a sha rather than to a branch, a branch being
free to move under a review:

- the author hands off by naming the sha pushed and the evidence run
  against it, then leaves that head alone;
- the reviewer answers with findings — where, what is wrong, how they
  know it, and whether each is blocking;
- the author accepts what is reasonable, declines the rest with a reason
  in the thread, and pushes the answer without waiting for CI;
- the reviewer resolves the threads they opened, that being what says a
  finding is closed, and re-reviews the delta rather than the branch.

**What ends the loop is the ack of record**, and the author does not
supply their own. A reading that says what it found and delivers no
verdict is a review too and ends nothing; [the standard's *Review*][s-rev]
has which is which, and `REVIEWING.md` has how each is written. A
disagreement that survives a second exchange goes to the maintainer
instead of into a third round.

### Landing it

CI is read once, and this is where. Rebase onto `main`'s tip, push that
head so the checks run on the tree that will land, and only then wait for
them: checks read before a rebase describe a tree nobody is landing. A
rebase that moved nothing but the base leaves the ack standing; one that
resolved a conflict does not, that resolution being a change no reviewer
has seen.

Then squash, [the only method the rule accepts][s11].

**The maintainer's bypass is not automatic — it has to be invoked, and
`gh pr merge` cannot invoke it**, refusing client-side before it asks
GitHub anything:

```text
Pull request is not mergeable: the base branch policy prohibits the merge
```

The merge endpoint applies it server-side, and it is the same endpoint
the merge button asks:

```shell
gh api -X PUT repos/{owner}/{repo}/pulls/<n>/merge \
  -f merge_method=squash -f sha=<the head the checks ran on>
```

**The `sha` is not optional.** Reading the ack and merging are two
calls, and the head is free to move between them — the push that would
move it comes out of the same round the verdict does. Unpinned, the
command takes whatever sits at the head when it runs; pinned, [the
endpoint answers `409` where the head has moved][gh-merge], and a round
lost that way is cheaper than a tree nobody has read reaching `main`.
*The review* above anchors the exchange to a sha and [section 11][s11]
has an ack name one: the pin is that rule reaching the call that
performs the landing.

**Verify what landed rather than trusting the answer**, the signature
[the standard asks for][s-sigs] being a valid one rather than a
particular signer's:

```shell
gh api repos/{owner}/{repo}/commits/main \
  --jq '.commit.verification | {verified, reason}'
```

**What it closed is read again here too, from the landed sha rather
than from the pull request**: [the standard's *What a pull request says
it is*][s-title] has the second read, and why the first alone does not
reach a squash subject composed after it runs.

The forge deletes the head branch itself, per the setting section 11
names. What is still yours is bringing every checkout sitting on `main`
up to date,
that being where the next session starts from and a stale one being where
a branch gets built on a base that has moved. `REPOSITORY.md` carries the
settings and why they are what they are.

[s-what]: https://github.com/btclib-org/.github#what-this-repository-is
[s11]: https://github.com/btclib-org/.github#11-github-settings
[s9]: https://github.com/btclib-org/.github#9-prose-comments-and-docstrings
[s-title]: https://github.com/btclib-org/.github#what-a-pull-request-says-it-is
[s-rev]: https://github.com/btclib-org/.github#review
[s-sigs]: https://github.com/btclib-org/.github#signatures
[gh-merge]: https://docs.github.com/en/rest/pulls/pulls#merge-a-pull-request
[governance]: https://github.com/btclib-org/.github/blob/main/GOVERNANCE.md
[roadmap]: https://github.com/btclib-org/.github/blob/main/ROADMAP.md

## This repository in particular

Everything above is the same file in every repository of the
organization; everything below is this one's, and the comparison stops at
this heading.

<!-- The toolchain badges are here rather than in the README because they
report no state: each names a choice, and this is the file that says how
the choice is enforced and what the command for it is. The README keeps
the badges that can turn red. --> [![calendar versioning:
yyyy.m.d](<https://img.shields.io/badge/cal_ver-yyyy.m.d-1674b1.svg?logo=calver>)](<https://calver.org/>)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![format:
ruff](https://img.shields.io/badge/format-ruff-yellowgreen.svg?logo=ruff)](https://docs.astral.sh/ruff/formatter/)
[![lint:
ruff](https://img.shields.io/badge/lint-ruff-yellowgreen.svg?logo=ruff)](https://docs.astral.sh/ruff/)
[![docstrings:
ruff](https://img.shields.io/badge/docstrings-ruff-yellowgreen.svg?logo=ruff)](https://docs.astral.sh/ruff/rules/#pydocstyle-d)
[![type check:
mypy](https://img.shields.io/badge/type_check-mypy-yellowgreen.svg?logo=mypy)](https://mypy-lang.org/)
[![lint:
markdownlint-cli2](https://img.shields.io/badge/lint-markdownlint--cli2-yellowgreen.svg?logo=markdown)](https://github.com/DavidAnson/markdownlint-cli2)
[![pre-commit
enabled](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![GitHub repository:
btclib-org/btclib-ecc](https://img.shields.io/badge/GitHub-btclib--org%2Fbtclib--ecc-181717?logo=github)](https://github.com/btclib-org/btclib-ecc/)

To get an overview of the project, read the [README](./README.md).

### The public surface

**Every module and every package declares `__all__`**, at every depth of
the tree. A name is public here because a list says so, not because it
happens to lack a leading underscore. An empty list is a legitimate
answer, for a module with nothing public of its own; declaring nothing is
not. For a package the list is what the `__init__` publishes, submodules
included; for a module it is what the module itself defines, a name it
imported belonging to the module that defines it. `btclib_ecc.__all__`
is the root of that tree, written out rather than discovered, so that a
new module is published by somebody deciding to. `tests/all_test.py`
checks all of this and finds the modules rather than listing them: a
public name kept out of a list is recorded in its `UNEXPORTED` table.

**The package imports nothing of this organization's other packages.** It
is the arithmetic the others are built on, and `tests/imports_test.py`
imports each module alone and refuses one that loads anything above it.

**Every public function validates its inputs.** Whatever it is handed — a
string, octets, or an object somebody built earlier — a name a caller can
reach checks it before acting on it, and a malformed argument leaves as a
`BTClibEccTypeError` or a `BTClibEccValueError`, which is what
the callers of this package are written to catch. The work itself may be
deferred to a private twin that does not validate; that twin is then what
the package composes internally, where the inputs have already been
checked and checking them a second time buys nothing.

**A function that answers a `bool` is total over the types it declares,
and only those.** `dsa.verify` answers False for a signature that does
not verify: that is what the bool is for, and a caller filtering a list
of them wants an answer and not an exception. A value of a type the
signature does not declare is not such an answer — it is the caller's own
mistake, it is a call mypy already refuses, and it leaves as a
`BTClibEccTypeError` like any other. So `dsa.verify(msg, 12, sig)`
raises, 12 being a private key in this package and never a public one,
where a well-formed public key that simply did not sign is False.

**`ecc`'s verifications carve one case out of that**, as `ecc.musig2` and
`ecc.frost` do: a value of a declared type whose size or encoding makes it
impossible to read as a signature, a key, a digest or an opening raises
rather than answering False. The function is not saying the signature is
forged, it is saying it has no way to find out (btclib-org/btclib#2170).
So `dsa.verify(msg, "not a key", sig)` raises `BTClibEccValueError`,
while a signature that is well formed and simply does not verify is False.

**What decides is whether the parameter declares a size**, which is what
makes the carve-out one rule rather than a judgement per call site. A
message of any length is a message, so nothing about it can be the wrong
length and the rule never fires: `ssa.verify_` answers False for a short
one, an ordinary message that was not signed. A digest is of its hash
function's size and a BIP374 message is of 32 octets, so `dsa.verify_`
and `dleq.verify_proof` refuse any other length — 31 octets are no
SHA-256 digest, and the equation has nothing to be about. BIP374's own
reference reads the same way: `dleq_verify_proof` asserts
`len(proof) == 64`, and the `dleq_challenge` it reaches at its last step
asserts `len(m) == 32`, while `s >= GE.ORDER` and a challenge that does
not match are its False.

`ecc.dsa`'s malformed DER encoding is the one thing on the other side of
the line, and it is there because a measurement put it there rather than
because the rule reaches it: its own wycheproof vectors ask that question
over profiles built for it, and answer False.

The line is the annotation, and deliberately not which built-in a helper
happens to derive from: those two coincide only by accident
(btclib-org/btclib#745). The `assert_*` twin beside each of these is the
spelling that says *why* a value was refused, and the two are how a
caller chooses between an answer and a reason.

**Both halves are gated.** `tests/input_validation_test.py` drives the two
rules over every public function whose required parameters are all
package input types. `tests/bool_contract_test.py` drives them from
hand-written fixtures over the verifications that walk cannot reach — a
signature verification needs a valid message, key and signature, and a
`Sig | Octets` no vocabulary of wrong values can build.
`tests/curve_parameter_test.py` drives the same rules over a parameter
that carries a *default*: reaching one means every argument in front of
it has to be valid, which is the table of valid values the automatic walk
exists to do without, so `ec` is driven from a table there. None of these
test files has an exemption list, which is the state to keep: a finding
is a red test, to be fixed or to be given a reason of its own.

**A `bool` parameter is a kind or a truth, and only the first is
type-checked.** A flag that decides *what is computed* refuses a non-bool,
`musig2._flag` stating the reason: a kind written down and read back —
json, a configuration file, a coordinator's message — arrives as whatever
it was written as, and `"false"` is true. A flag that decides only
*whether a check runs* is read for its truth: `check_validity` either runs
a check or skips one, and never changes an answer.
`tests/check_validity_test.py` owns that convention.

**A truth's `True` has to be its conservative value**
(btclib-org/btclib#884). Every wrong value is true, so the misreading is
never "the flag was off": it is always the one the flag's `True` stands
for. That is what makes a truth safe — `strict="no"` is strict,
`order_check="no"` checks the order — and it is a fact about the *name*,
not about the check. So a flag whose `True` is the permissive value is a
kind however little it computes, because the misreading waives the very
refusal it was written to make: `point_from_octets`' `hybrid` parses the
prefixes it was written to keep out.

**Which of the two a flag is, is written down for every one of them.**
`tests/bool_parameter_test.py` is the census: two tables, a kind driven
until it refuses `"no"`, `0` and `1`, a truth driven until it accepts all
three, and a walk that fails on a `bool` parameter in neither table. So a
flag added anywhere is a decision somebody makes rather than one the
default makes for them — and `0` and `1` are in that vocabulary because
`bool` is a subclass of `int`, which is what leaves `isinstance(value,
int)` no check at all here. `check_validity` is the one name subtracted
by the walk, its own file holding it.

**What a function answers, its name says**, and the vocabulary is
closed: a public function that answers a `bool` carries one of the
prefixes below, or is one of the English predicates
`tests/name_contract_test.py` names. A bool that is neither fails that
gate, so a new one is a prefix or a decision somebody wrote down.

- `assert_*` refuses and returns `None`, and is the reason half of the
  pair above.
- `is_*` answers a `bool` about a value, and is total over the declared
  types.
- `verify*` answers a `bool` about a signature or a proof, on the same
  terms. `assert_as_valid` beside it says why.
- `check_*` answers a `bool` **and refuses what cannot be an answer** --
  the one prefix that warns a caller it still needs an `except`.

A converter is named for what it returns -- `bytes_from_octets`,
`point_from_octets` -- and a query for what it answers.

**A member that takes nothing but `self` is a `@property`**, whatever it
answers, and that is gated too: it is read off the object rather than
called. What is *not* a read is exempt by shape rather than by a list of
names: `assert_*` refuses, and a property that refuses is a trap, since
reading `obj.assert_valid` evaluates the method and throws it away;
`to_*` hands back a new object. The one exemption named individually is
`alias.HashObject`'s `digest`, `hexdigest` and `copy`, because hashlib
calls them that way.

**`check_validity` is a parameter and not one of those prefixes**: there
`check` is a verb governing an object — "check the validity" — where a
prefix on a function name classifies what the call answers. It is
keyword-only throughout, and `tests/check_validity_test.py` holds every
signature to that. `check_validity=False` is not an exemption from the
rule above either: it says "do not check *now*", not "this object is
exempt from here on", so a public function that takes an already-built
object and asks it nothing is one a caller can reach with an object the
package itself would refuse.

**The leading underscore means what it means anywhere in Python:
private.** `__all__` is what decides publicity, so it is a reader's hint
rather than the rule, but an unvalidating twin belongs on the private side
of that list, and calling one asserts that its caller validated.

**A private function takes no default argument either**, which is the
same absence of an outside caller read the other way: a default is
written for one the author cannot see, and there is none here. So the
value the call is made with is at the call site, where it is read —
`dsa._deserialize_scalar`'s `strict` decides whether BIP66's minimal
encoding is enforced at all. `tests/private_defaults_test.py` is the gate,
and its docstring carries what the rule does not reach.

**A trailing underscore is the other convention, and it is public.** It
marks the spelling whose input the caller has already prepared:
`dsa.sign_` takes the hash `sign` would compute, `musig2.nonce_gen_` the
randomness `nonce_gen` draws, `musig2.partial_sig_verify_` the session
context `partial_sig_verify` aggregates. Both names of the pair are in
`__all__`, so it is an offer to skip work the caller has already paid
for, not a way past the validation above: `sign_` checks its `msg_hash`
as `sign` checks its `msg`. The two conventions are independent, and
`btclib_ecc.ecc.dsa._assert_as_valid_` carries both.

Publishing both names is what makes their agreement a promise rather than
a tidiness. A keyword added to `verify` is added to `verify_` or to
neither, with the same default in both: a flag that changes the answer on
one and is missing or defaulted differently on the other makes the pair
two functions instead of two spellings.

Prepared is not unchecked, and a bare `int` the trailing underscore takes
instead of an `Integer` still refuses a `bool`: `_utils.is_integer` is the
policy `int_from_integer` carries for every coerced parameter, and the
underscore spelling asks it of what it is handed already prepared rather
than skipping it -- `ssa.challenge_`'s `x_Q` and `x_K`, and
`dsa.recover_pub_key_`'s `key_id`, all pinned in
`tests/integer_policy_test.py`'s census (btclib-org/btclib#1248).

### A `_var` suffix means the operand decides the work

A function whose duration follows the value it is given ends in `_var`,
and the plain name beside it is the one a secret may be handed. It is
libsecp256k1's convention and it is used there for the same two halves:
`secp256k1_scalar_inverse_var` sits beside `secp256k1_scalar_inverse`,
`secp256k1_gej_add_var` beside `secp256k1_gej_add_ge`. The point of it is
that the question is answered at the call site rather than in the
docstring of the thing being called. A leading underscore changes none of
this: the suffix states the implementation's timing, for a private
function as for a public one.

What "the work" is depends on the function, and each of these was
measured rather than assumed — on secp256k1's order or its `p`, over
random operands of 256 bits down to 64, the ratio between the two ends:

- the count of point operations, for a scalar multiplication:
    `curve_group._mult_jac_var` and `curve_group_2._double_mult_w_NAF_var`
    against `_mult_regular_window`, `_mult_fixed_base` and
    `_double_mult_regular_window`, which make the same number for every
    scalar of the curve. `curves.double_mult_var` and
    `curves.multi_mult_var` carry it for that reason and `curves.mult`
    does not
- the iteration count of an extended Euclid: `mod_inv_var` at 4.21x,
    `xgcd_var` at 4.84x, `mod_inv_batch_var` at 2.01x
- the length of a loop over the operand: `legendre_symbol_var` at 4.26x,
    and `tonelli_var`, whose 1.54x is spread within one operand size
    rather than across sizes — Tonelli-Shanks iterates on the value, not
    on its length. `mod_sqrt_var` reaches that loop only for a `p` of 1
    mod 4: on a 3 mod 4 one it is a single exponentiation with a fixed
    exponent and measures 1.01x, and the catalogue holds both kinds —
    `secp224k1`, `secp224r1` and `nistp224` are 1 mod 4 — so the caller
    picks which it gets and the suffix states the worse case
- one modular inverse, in the layer above: `aff_from_jac_var` at 2.96x,
    `x_aff_from_jac_var` at 1.93x, `aff_from_jac_batch_var` at 1.67x and
    `y_aff_from_jac_var` at 1.42x follow the `Z` they are handed;
    `double_aff_var` at 1.32x, `add_aff_var` at 1.23x and the `add_var`
    over them at 1.22x follow the coordinates. `y_var` and its three
    tiebreakers follow their `x` on the 1 mod 4 curves above, 1.84x on
    `secp224k1`, where on secp256k1 they are flat

**The suffix is measured, never inherited, and that is what stops it.**
Every function that *reaches* one of these through some chain of calls
would otherwise take it: most of the package's own call graph, public
functions included — a suffix on the package, saying nothing. Two things
break the chain, and both are facts about the caller rather than about
the callee. Blinding is one: `mult` calls `aff_from_jac_var` and is 0.99x
in its scalar, because `_blinded_jac` randomized the `Z` that inverse is
timed on. A public operand is the other: `point_from_octets` measures
1.05x, its `y_even_var` being one fixed exponent on secp256k1 and its
`_is_x_coordinate_var` reaching the bindings. So the question to ask of a
new name is not what it calls, but what its own clock does with what it
was handed — and the answer is a measurement.

**These are the exceptions the census leaves.** Every function that
spends one of these primitives has been timed over random inputs of one
class, against `add_jac` as the floor — 1.05x, the group law having
nothing to branch on. What measures at that floor keeps its plain name,
and each is here so that the next reader does not have to re-derive it:
`dsa._assert_as_valid_` 1.07x and `dsa._recover_pub_key_` 1.05x,
`ssa._assert_as_valid_` 1.07x and `ssa._recover_pub_key_` 1.06x,
`ellswift._try_sqrt` 1.05x, `sec_point.point_from_octets` 1.01x,
`ssa.point_from_bip340pub_key` 1.03x and `Sig.assert_valid` 1.03x. The
inverse or the root inside each of them is real, and it is diluted: an
inverse varying by 1.32x is 10 us of a 40 us verification.
`ellswift._constants` is memoized on the curve and receives no value at
all.

The one number worth keeping in view is `ellswift._xswiftec_inv_var`, at
**29.62x**. That is an early return and not a slower sum, which is what a
data-dependent branch looks like on a clock, and it is why the SwiftEC
map carries the suffix.

Three tiers of duration follow, of which only the first is constant-time:

- **constant-time is libsecp256k1's alone.** Every claim of it in this
    package is a claim about the C behind the bindings, which is why
    `SECURITY.md` states argument by argument when a call crosses that
    boundary. Nothing written in Python is constant-time, and no name
    here should be read as promising it.
- **regular, or blinded: the operand does not decide the duration, and
    something else does.** `_mult_regular_window`, `_mult_fixed_base` and
    `_double_mult_regular_window` make the same operations for every
    scalar of the curve; `_blinded_jac` leaves the intermediate values a
    function of a random factor rather than of the scalar alone; and
    `mod_inv` leaves an extended Euclid's iteration count following a
    random factor rather than the caller's operand, at 1.02x where
    `mod_inv_var` is 2.06x over the same range. This is decorrelation and
    not uniformity — the duration still varies, and what changes is what
    it varies with.
- **variable: the operand decides.** Everything suffixed above, and every
    reduction whose cost is the size of what it reduces.

So **a secret takes the plain name and a public value takes the `_var`
one**, which is the opposite of an optimization default and is meant to
be: the fail-safe direction is that forgetting to choose gives the slower
and safer call. `dsa`'s signing inverts the nonce with `mod_inv` while
its `r`, its `s` and a verification's `Z` take `mod_inv_var`, and a
reviewer should be able to tell which is which without tracing where
each value came from.

Add the suffix when adding such a function, having measured that it earns
one, and do not add it to the recodings, the tables or the group law:
those take no operand whose size varies, and a suffix on everything says
nothing about anything.

What none of this does is make the Python path safe, and `SECURITY.md`'s
limitations section is what says so at length: a table is still indexed
by a secret digit, and that is out of reach from bytecode. A name in the
second tier closes one measured channel, and the honest form of the claim
is that one — which channel, measured how, and what is left.

### The environment and the gates

uv is the only tool that must be installed; it fetches interpreters,
linters and packaging tools itself. `uv sync` creates the environment.

```shell
uv sync
```

No test reaches the network. [tests/README.md](./tests/README.md) is
where the suite and its switches are described.

The gate is the suite, the hooks and the documentation build:

```shell
uv run pytest
uv run pre-commit run --all-files
uv run --locked --no-default-groups --group docs \
    sphinx-build -n -W -b html docs/source docs/build/html
```

`--cov` is in `addopts`, so the bare `pytest` above is the coverage gate
and `fail_under` is what it answers against — 100%, and coverage takes
that literally: a statement or a branch no test reaches fails it. A
selective run is reported and not gated, and `tests/conftest.py`'s
`coverage_fail_under` is what makes that difference.

The documentation build is the one to remember, because no hook reads
reStructuredText: a docstring docutils cannot parse fails it with every
hook green — a name ending in an underscore is a reference to a link
target, and the fix is double backticks around it. `-n` turns an
unresolved cross-reference into a warning for `-W` to fail on, and
`conf.py`'s `intersphinx_mapping` is what resolves a reference into the
standard library.

**Check exit codes, not filtered output.** `pre-commit run ... | grep -v
Passed` hides a failure, and `grep` finding nothing exits 1, which is not
the gate's answer to anything.

**The lint gate is not installed as a git hook.** `pre-commit install`
writes into the common git directory, which every worktree of this
repository shares: `git -C <worktree> rev-parse --git-path hooks` answers
with the primary checkout's `.git/hooks` from every one of them. So one
session installing it installs it for every other. Run the gate by hand
before committing — the `uv run pre-commit run --all-files` above.

**Prefix any `--python <version>` command with
`UV_PROJECT_ENVIRONMENT=.venv-<version>`, naming the interpreter that
command selects — `.venv-3.11` for `--python 3.11`, `.venv-pypy3.11` for
`--python pypy3.11`.** Without it, `uv run --python <version>` removes
`.venv`, builds it again on that interpreter and with that command's own
group set, and leaves it there. `uv sync` restores it.

### The editor

`.vscode/settings.json` and `.vscode/extensions.json` are tracked, and they
hold no preference: the recommended extensions are the tools
`.pre-commit-config.yaml` already runs, and the settings put the fixing ones
on save. Installing them is optional and changes nothing about what a local
run enforces.

Anything machine-local — an interpreter path, a telemetry answer, a theme —
belongs in the editor's own user settings instead, those two files being
read by every checkout of this repository.

### Reproducing what CI runs

Each command below is the one a CI job runs. Keep this section true when a
workflow changes.

`os-ubuntu.yml`, `os-macos.yml`, `os-windows.yml` and `deps-oldest.yml`,
the suite job of each — the suite, on one cell of a matrix. `--no-cov`
undoes the `--cov` addopts carries, the `coverage` job below being where
coverage is measured and gated:

```shell
uv run --locked --no-default-groups --group test pytest --no-cov
```

`test.yml`, the `coverage` job, whose data file is named apart from the
default so that `coverage-union` below can download it beside the
`no-bindings` job's:

```shell
COVERAGE_FILE=coverage-data-bindings \
    uv run --locked --no-default-groups --group test pytest
```

`test.yml`, the `no-bindings` job — the suite in an environment without
`btclib-secp256k1`, which asserts the absence first and collects coverage
without gating on it. `UV_PROJECT_ENVIRONMENT` keeps the run out of
`.venv`, which `uv run` would otherwise rebuild without the bindings:

```shell
UV_PROJECT_ENVIRONMENT=.venv-no-bindings \
    uv run --locked --no-default-groups --group harness \
    python -c "from btclib_ecc._libsecp256k1 import INSTALLED; assert not INSTALLED"
UV_PROJECT_ENVIRONMENT=.venv-no-bindings \
    COVERAGE_FILE=coverage-data-no-bindings \
    uv run --locked --no-default-groups --group harness pytest --cov-fail-under=0
```

`test.yml`, the `coverage-union` job — the two runs' data combined and
gated at `[tool.coverage.report]`'s floor:

```shell
uv run --locked --no-default-groups --group harness \
    coverage combine --rcfile=pyproject.toml coverage-data-bindings coverage-data-no-bindings
uv run --locked --no-default-groups --group harness \
    coverage report --rcfile=pyproject.toml
```

`test.yml`, the `dist` job — build the distribution files, check them and
install one. `release.yml`'s `test` job calls this workflow, and its
publish jobs download the `dist` artifact this job uploads, so what the
checks below judge is what an index ends up serving. `normalize_sdist.py`
is what puts the commit's own time into every member of the sdist, and
its docstring says why the backend's archive is not published as it
stands; `sha256sum` after it is the digest a rebuild from the tag is
compared against, per RELEASING.md's
[Rebuild a release from its tag](./RELEASING.md#rebuild-a-release-from-its-tag).
`generate_sbom.py` writes the CycloneDX bill of materials into `sbom/`,
which `release.yml`'s `attest` job signs beside the two files:

```shell
export SOURCE_DATE_EPOCH=$(git log -1 --pretty=%ct)
uv build
uv run --no-project --python 3.15 .github/scripts/normalize_sdist.py dist/
sha256sum dist/*
uv run --no-project --python 3.15 .github/scripts/generate_sbom.py dist/ sbom/
uv run --locked --only-group check twine check --strict dist/*
uv run --locked --only-group check check-wheel-contents dist/*.whl
uv run --locked --only-group check pyroma --min 10 dist/*.tar.gz
```

The job then installs the wheel it just built from an empty directory,
bare and then with the `secp256k1` extra, and in each reads the version
back, asserts which arithmetic serves, and signs and verifies once:

```shell
tmp=$(mktemp -d)
set -- "$PWD"/dist/*.whl
cd "$tmp"
for extra in "" "[secp256k1]"; do
  rm -rf .venv
  uv venv
  uv pip install "$1$extra"
  .venv/bin/python -c "
import sys
from importlib.metadata import requires, version
import btclib_ecc
from btclib_ecc.curves import is_libsecp256k1_serving, mult
from btclib_ecc.ecc import dsa

print(version('btclib-ecc'), requires('btclib-ecc'))
assert btclib_ecc.__version__ == version('btclib-ecc')
assert is_libsecp256k1_serving() is (sys.argv[1] != '')
sig = dsa.sign(b'btclib_ecc', 1)
assert dsa.verify(b'btclib_ecc', mult(1), sig)
" "$extra"
done
```

Last, it unpacks the sdist outside the checkout and runs the suite
there, under the coverage job's floor; from the checkout's root:

```shell
tmp=$(mktemp -d)
tar -xzf dist/*.tar.gz -C "$tmp" --strip-components=1
cd "$tmp"
uv run --locked --python 3.15 --no-default-groups --group test pytest
```

`lint.yml`, the `lint` job — this file *is* the lint gate, so there is no
second list of tools anywhere:

```shell
uv run --locked --only-group lint \
    pre-commit run --all-files --show-diff-on-failure
```

`docs.yml`, the `docs` job — the build, and then a read of the pages it
wrote:

```shell
uv run --locked --no-default-groups --group docs \
    sphinx-build -n -W -b html docs/source docs/build/html
if grep -rn 'href="#\.\.\?/' docs/build/html --include='*.html'; then
    echo "::error::the links above resolve to no page (unresolved relative path)"
    exit 1
fi
```

What myst renders for a destination it cannot resolve is an anchor to an
id no page has. `-W` reports it because `docs/source/conf.py` resolves the
links the included root files carry and suppresses no myst warning; the
`grep` is what still finds one the day a suppression goes back in.

`codeql.yml` has no line here: its jobs run `github/codeql-action` and no
command of this project's, so reproducing it locally means the CodeQL CLI
and a database rather than a `uv run`.

### What gates a merge, and what only reports

`lint.yml`, `test.yml` and `docs.yml` produce the required checks, and
`REPOSITORY.md` reads the rule back from the endpoint rather than
restating it. So a diff does not reach a review without having passed
them or passing them beside it on the same sha, which is the reliance
`REVIEWING.md` provides for.

| workflow | when | what it varies |
| --- | --- | --- |
| `test` | pull request, push | — |
| `lint`, `docs` | pull request, push | — |
| `claude-review` | pull request, and `@claude` in a comment | — |
| `codeql` | pull request, push, and weekly | the languages |
| `os-ubuntu` | weekly, a release | images × interpreters |
| `os-macos` | weekly, a release | images × interpreters |
| `os-windows` | weekly, a release | images × interpreters |
| `deps-latest` | weekly | dependencies upgraded |
| `deps-oldest` | weekly | the floor interpreter, dependencies at their floors |
| `zkp-oracle` | weekly | a `secp256k1-zkp` build |
| `scorecard` | weekly, push to main | — |
| `links` | weekly | — |
| `mutation` | weekly | the `.github/mutation/` profiles |
| `fuzz` | weekly, and by hand before a release | — |
| `vendored-vectors` | weekly | the pin ledger |
| `py-arm-authority` | weekly, push to main | the arm table |
| `pypi-install` | weekly, a release | what PyPI serves |
| `sdist-rebuild` | weekly | the latest release's sdist, rebuilt |
| `release` | a tag, and a rehearsal | the workflows it calls |

Which workflows that last row covers is
`grep -n 'uses: \./\.github/workflows/' .github/workflows/release.yml`,
not a list here. Which day each of the rest runs is section 10 of
[the organization standard](https://github.com/btclib-org/.github), and
not this file's to restate.

The gates run one image on one interpreter: `ubuntu-latest`, and the
version `.python-version` names. `claude-review` gates nothing: a review
that gates a merge would make a model's judgement a branch rule. Why so
little gates is the ceiling on concurrent jobs the plan puts on the whole
organization, and `REPOSITORY.md`'s *Plan-gated settings* is where that
lives.

### The secrets baseline

`detect-secrets` reads `.secrets.baseline` to decide which findings have
already been reviewed. A test vector's private key is a finding, and
adding one means regenerating it. The command preserves the plugin
selection the file already carries, which is deliberate: the two entropy
plugins are off, because in vectors made of 64-character hex strings a
new high-entropy string is what a legitimate addition looks like:

```shell
uvx detect-secrets scan --baseline .secrets.baseline
uv run --locked --only-group lint pre-commit run detect-secrets --all-files
```

Read the diff before committing it: a new entry is a finding somebody has
to have looked at, which is the whole point of a baseline over an
exclusion.
