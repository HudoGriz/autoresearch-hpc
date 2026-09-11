# Contributing

## The bar for a change

This is a protocol, so the interesting question about a change is **which
failure it prevents**. A pull request adding a rule, role or gate should name the
failure mode it addresses and, where possible, include a regression test.

Changes to `PROTOCOL.md` are versioned and need a `CHANGELOG.md` entry. Changes
that make an existing project non-conforming need a migration note.

## Running the tests

Follow [HPC setup](docs/hpc-execution.md) to configure a local test site first.

```bash
export ARH_TEST_SITE=/absolute/path/to/local/site.md
test/run_tests.sh
python3 test/test_hardening.py
KEEP=1 test/run_tests.sh
```

CI provisions Nextflow and Singularity/Apptainer on Linux, runs integration
tests, validates schemas and lints shell scripts.

## Shell style

- `set -euo pipefail`, quoted expansions, explicit paths.
- Bash 3.2 compatible where practical: avoid `mapfile`, `declare -A` and `${var,,}`.
- No GNU-only flags without feature detection and a portable fallback.
- Public commands live in `bin/arh-<name>` and are dispatched by `bin/arh`.
- Project state belongs under `.arh/`.
- Shared implementation belongs in `lib/`.

## Adding things

**A standing rule** — a file in `config/rules/` declaring `id`, `severity`,
`applies` and `forbid`/`requires` regexes in its `arh-config` block. Rules
constrain what an iteration may claim, never what it may compute. Test both the
firing and non-firing case.

**A cross-check role** — a prompt in `skills/cross-check/roles/`. It must ask for
a `VERDICT:` line and say what evidence would change the conclusion.

**A harness** — keys in `config/harnesses.md` plus any native config under
`harness/`. Configure the actual model family; the foreign-family gate depends
on it.

**A scheduler/executor** — extend the Nextflow execution layer rather than
building a second workflow engine inside `arh`.

## Protocol defects

If a rule is wrong, or a gate can be satisfied by work that should have failed,
open an issue with the smallest case that gets through. Per §4.4, corrections to
standing rules are dated amendments that leave the original visible.

## Provenance of the design

The protocol generalises mechanisms that emerged from a long-running append-only
research project worked concurrently by multiple harnesses. That history is a
source of failure cases, not proof that the design generalises to every lab or
domain. Evidence that it does not generalise is especially useful.
