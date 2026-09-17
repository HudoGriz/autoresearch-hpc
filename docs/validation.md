# Validation scope

## Current baseline

A local run on 2026-09-17 against a configured local site (Nextflow 26.04.6 from a
host micromamba environment, scientific tasks through Singularity-compatible
Apptainer on Linux) passed:

| Suite | Command | Result |
|---|---|---|
| Core protocol checks | `test/run_tests.sh` | 154 / 154 |
| Boundary regressions | `python3 test/test_hardening.py` | 55 passed, 1 skipped, 0 failed |
| Deterministic synthetic example | `bash examples/mean-shift/check.sh` | OK |

The skipped regression (`test_env_create_locks_and_is_immutable`) solves real
packages and needs `ARH_TEST_NETWORK=1`; CI runs it with network enabled.

Six core checks — `arh doctor` on a fresh project, the three `arh submit`
execution checks and the Singularity-runtime check — require a site whose
`runtime_image`, `runtime_sha256` and `nextflow_prefix` are actually populated.
Pointing `ARH_TEST_SITE` at the repository's own `config/site.md` template, which
leaves those empty, fails them. This is a property of the site, not of the code.

## Earlier runs

Local validation on 2026-09-10 passed 137 core protocol checks and 31 boundary
regressions. After the field fixes listed in the [changelog](../CHANGELOG.md), a
re-run on 2026-09-11 passed 137/137 core checks and 37/37 boundary regressions.
The counts have grown since because regressions were added, not because coverage
was restated.

Observed behaviors across those runs included native local success, cached
resume, real Slurm success, deliberate task failure propagated to the
controller, and rejection of a write to an immutable input inside a compute-node
container. The real-Slurm and cache-reuse observations come from those earlier
runs; the 2026-09-17 baseline above was a local-executor run and does not
re-establish them.

One bounded Claude review returned **QUALIFIED**. Five predeclared follow-up
probes passed: final-adapter local success, Slurm success, Slurm failure,
concurrent review refusal, and confirmation of the packaged Nextflow jar.
These probes were authored by the producing family, not independently rerun
by the reviewer. The original review remains unchanged.

## Retained limits

Remaining limits include mutable host environment storage, controller writes
outside task-container protections, untested PBS and heterogeneous/GPU tasks,
and model overhead beyond submitted prompt/output limits. This is a cooperative
research protocol, not containment for hostile workflow code or a scientific
truth guarantee.

The original append-only audit records stay in the maintainer's local study.
They include machine-specific paths and runtime data and are not included in
this source release. This page is a publication summary, not a replacement for
the original evidence. GitHub Actions runs the suite on every push; that
validation becomes independently visible once the repository is public.
