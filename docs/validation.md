# Validation scope

## Current baseline

A run on 2026-09-21 against a configured local site (Nextflow 26.04.6 from a host
micromamba environment, scientific tasks through Singularity-compatible Apptainer on
Linux) passed:

| Suite | Command | Result |
|---|---|---|
| Core protocol checks | `test/run_tests.sh` | 158 / 158 |
| Boundary regressions | `python3 test/test_hardening.py` | 70 / 70 (1 network case skipped) |
| Protocol conformance matrix | `python3 test/conformance.py --site SITE` | 12 / 12 |
| Deterministic synthetic example | `bash examples/mean-shift/check.sh` | OK |

## Protocol conformance matrix

`test/conformance.py` injects one violation per protocol boundary into a scratch project
and checks the specified refusal. A stand-in reviewer answers `arh ask`, so no model is
called. The cases that run real tasks (E5b, E6, E9) need `--site`; without it they are
reported as skipped. The result is written as JSON with the commit it ran on, marked
`-dirty` when the checkout had uncommitted changes.

| ID | Injected violation | Specified behaviour |
|---|---|---|
| E1 | required pre-declaration field left empty | predeclare gate refuses |
| E2 | result written before the plan is frozen | predeclare gate refuses |
| E3 | frozen plan edited after the result | results gate refuses the changed hash |
| E4 | concurrent claims | distinct iteration numbers |
| E5 | write to a declared immutable input through `arh` | refused |
| E5b | task writes to a declared immutable input | refused by the read-only mount |
| E6 | task exits with an error | failure reported; receipt and logs kept |
| E7 | review requested from the producer's own family | refused by default |
| E8 | evidence changed after a review | review becomes ineligible |
| E9 | submission interrupted while its task runs | signal recorded; launch lock released; scheduler job gone |
| E10 | fresh shell with no chat history | status, next and the ledger name each iteration's state |
| E11 | review configuration changed after the claim | review refused unless the reason is recorded |

On 2026-09-21 all twelve cases passed on a local site, and again on Slurm with the
scratch project on a shared CephFS directory. With
`--claim-launcher 'srun -N 4 --ntasks-per-node 8'`, 32 tasks on four compute nodes made
96 claims against one CephFS project and received 96 distinct iteration numbers. CI runs
the matrix on every push with a local site and keeps `conformance.json` as an artifact.

The network-dependent regression (`test_env_create_locks_and_is_immutable`)
solves real packages and needs `ARH_TEST_NETWORK=1`; CI runs it with network
enabled. Without a configured site and network, the boundary suite skips eight
integration cases while retaining all generator-evocation checks.

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
