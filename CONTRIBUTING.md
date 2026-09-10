# Contributing

## The bar for a change

This is a protocol, so the interesting question about any change is **which
failure it prevents**. A pull request that adds a rule, a role or a gate should
name the thing that went wrong without it — ideally something that actually
happened, not something that might.

Changes to `PROTOCOL.md` are versioned and need a `CHANGELOG.md` entry. Changes
that make an existing project non-conforming need a migration note.

## Running the tests

Follow [HPC setup](docs/hpc-execution.md) to configure a local test site first.

```bash
export DL_TEST_SITE=/absolute/path/to/local/site.md
test/run_tests.sh
python3 test/test_hardening.py
KEEP=1 test/run_tests.sh   # preserve the scratch project
```

CI provisions Nextflow and Singularity on Linux, runs the integration suite,
validates schemas and lints shell scripts. macOS container integration is not
supported.

## Shell style

- `set -euo pipefail`, quoted expansions, explicit paths.
- **POSIX-portable, bash 3.2 compatible.** No `mapfile`, no `declare -A`, no
  `${var,,}`. Keep the protocol shell portable where practical.
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

**A scheduler** — configure a Nextflow executor in `lib/nextflow.py`.
Direct container commands are implemented in `lib/container.sh`.

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

Integration tests need Linux, a configured host Nextflow environment and a task SIF.
Follow [HPC setup](docs/hpc-execution.md), set `scheduler = local` in the test site,
then run `DL_TEST_SITE=/absolute/site.md test/run_tests.sh` and
`DL_TEST_SITE=/absolute/site.md python3 test/test_hardening.py`. The controller
tests run on the host and their submitted work runs in Singularity. CI provisions
this boundary on Linux; macOS container integration is not supported.
