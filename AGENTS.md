# Repository instructions

Follow [CONTRIBUTING.md](./CONTRIBUTING.md) for issues, pull requests,
local gates, and worktree commands. Use [REVIEWING.md](./REVIEWING.md)
for reviews, [README.md](./README.md) for the package, and
[SECURITY.md](./SECURITY.md) for vulnerability reporting.

Keep the primary checkout clean and on `main`. Use a separate worktree
for each task and follow the setup and cleanup commands in
`CONTRIBUTING.md`.

Choose the least capable model that can reliably complete the task: use
a fast model for straightforward execution, a reasoning-focused model
for multi-step work, and the most capable available model for difficult
or ambiguous problems. Increase capability if progress stalls.

The `ecc` modules must not import other btclib-org packages; the
optional `btclib_secp256k1` extra is the exception. See
`tests/imports_test.py`.
