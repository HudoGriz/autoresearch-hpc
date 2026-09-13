# Pilot deterministic evaluation — 2026-09-13

This is an **engineering pilot**, not the final software-paper result table. It
exists to prove that the pre-specified evaluation harness runs in a clean GitHub
Actions checkout before the release candidate is frozen.

The final manuscript must rerun the same evaluation against the exact tagged
release and archive the resulting JSON artifact.

## Provenance

- AutoResearch HPC commit: `7b4be1d5c6e23f11177fcf4dfdb52340e856aba1`
- GitHub Actions workflow: `publication evaluation`
- Workflow run: `34769182227`
- Job: `Deterministic failure injection`
- Runner: Ubuntu 24.04 hosted GitHub Actions runner
- Evaluation program: `test/publication_evaluation.py`
- Result: **8 / 8 deterministic scenarios passed**

E6 (failed execution is propagated/preserved) and E9 (interrupt/recovery) were
not included in this fast provider-free suite; they require the execution
controller and remain part of the integration evaluation. Model-review accuracy
is also deliberately excluded because it is stochastic and has a separate
benchmark design.

## Pilot results

| ID | Injected condition | Expected ARH behavior | Pilot result | Gate/runtime time (ms) |
|---|---|---|---|---:|
| E1 | required pre-declaration remains unfilled | refuse freeze | passed | 175.335 |
| E2 | result exists before declaration is frozen | refuse freeze | passed | 143.223 |
| E3 | frozen declaration is edited | detect hash mismatch at results gate | passed | 241.066 |
| E4 | eight agents claim concurrently | eight unique iteration numbers | passed | 305.380 |
| E5 | write targets a declared immutable input | guard refuses | passed | 38.389 |
| E7 | verifier is configured to the producer family | review request refuses by default | passed | 165.985 |
| E8 | report changes after successful review | old review becomes ineligible | passed | 208.296 |
| E10 | project is resumed from a fresh working directory | disk state resolves through `ARH_PROJECT`/status/next | passed | 661.883 |

The timing column is the observed wall time for the relevant gate/test operation
on one hosted runner. It is **not yet an overhead estimate**. The publication
analysis will measure direct analysis, Nextflow-only and ARH execution separately
with repeated runs and a longer 30–60 second task, as pre-specified in
`docs/evaluation-plan.md`.

## Observations

The concurrency injection allocated iteration numbers 3 through 10 exactly once
each in the eight concurrent processes. The immutable-input test was rejected
before a write occurred. Same-family review was refused before a provider call.
Changing the reviewed report made its synthetic hash-bound review ineligible.

The cold-resume scenario intentionally started outside the study directory and
provided only `ARH_PROJECT`; both `arh status --json` and `arh next` resolved the
project without conversation history. This pilot establishes the mechanism in a
clean CI environment, not independent-user usability.

## Interpretation boundary

These eight passes support only a narrow statement: on this commit, the tested
deterministic gates behaved as specified for the injected cases. They do not
show that AutoResearch HPC improves scientific correctness, that model reviewers
are reliable, that every supported scheduler behaves identically, or that the
software is easy for an independent user to install.

Those claims remain gated on the release-tag evaluation, Slurm reproduction,
review benchmark and independent reproduction described in the publication plan.
