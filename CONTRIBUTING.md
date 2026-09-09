# Contributing

## The bar for a change

This is a protocol, so the interesting question about any change is **which
failure it prevents**. A pull request that adds a rule, a role or a gate should
name the thing that went wrong without it — ideally something that actually
happened, not something that might.

Changes to `PROTOCOL.md` are versioned and need a `CHANGELOG.md` entry. Changes
that make an existing project non-conforming need a migration note.

## Running the tests

```bash
test/run_tests.sh          # 78 checks, no cluster or network
KEEP=1 test/run_tests.sh   # keep the scratch project to inspect
```

CI additionally runs the suite on macOS and lints with shellcheck. The macOS job
is not decoration: `readlink -m`, `readlink -f` and `sed -i` are GNU-only, and
the first of those once made the immutable-input guard fail outright — a safety
check silently not running is worse than an error.

## Shell style

- `set -euo pipefail`, quoted expansions, explicit paths.
- **POSIX-portable, bash 3.2 compatible.** No `mapfile`, no `declare -A`, no
  `${var,,}`. macOS ships bash 3.2 and CI will catch you.
- No GNU-only flags. Where one is unavoidable, feature-detect and fall back —
  `dl_abspath` in `lib/common.sh` is the pattern.
- Commands live in `bin/dl-<name>` and are dispatched by `bin/dl`. Shared code
  goes in `lib/`.

## Adding things

**A standing rule** — a file in `config/rules/` declaring `id`, `severity`,
`applies` (`predeclaration` and/or `report`) and `forbid`/`requires` regexes in
its `dl-config` block. Rules constrain what an iteration may *claim*, never what
it may compute. Add a test that the rule both fires and stays quiet correctly:
a rule with no negative test is a rule nobody can refactor.

**A cross-check role** — a prompt in `skills/cross-check/roles/`. It must ask
for a `VERDICT:` line and must say what would change the reviewer's mind.
Adversarial roles that only ever return `SOUND` are worse than none.

**A harness** — three keys in `config/harnesses.md` (`harness_<n>_cmd`,
`harness_<n>_family`, plus the name in `harnesses`) and any native config under
`harness/`. Get the model family right; the same-family refusal depends on it.

**A scheduler or container runtime** — a case in `lib/scheduler.sh` or
`lib/container.sh`. Both are small and do one job each; keep them that way.

## Reporting a defect in the protocol itself

Most valuable contribution there is. If a rule is wrong, or a gate can be
satisfied by work that should have failed, open an issue with the case that
gets through. Per §4.4, a correction to a rule is a dated amendment that leaves
the original visible — including here.

## Provenance of the design

The protocol generalises one real project: 69 append-only iterations over
thirteen months, worked concurrently by more than one harness. Every mechanism
exists because something went wrong without it. It is nonetheless one project,
one lab, one domain — evidence that it generalises is welcome, and so is
evidence that it does not.
