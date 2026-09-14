# Paper evidence matrix

This file prevents the manuscript from drifting ahead of the evidence. A claim
should move into `draft.md` as a factual statement only when its evidence cell
points to a stable repository artifact, evaluation result or external citation.

The first deterministic engineering pilot is recorded in
[`pilot-results.md`](pilot-results.md): **8/8 provider-free scenarios passed** on
commit `7b4be1d5c6e23f11177fcf4dfdb52340e856aba1`. Those results are useful
implementation evidence, but the final paper must rerun them against the exact
release tag.

| Manuscript claim | Evidence available now | Publication evidence still required | Status |
|---|---|---|---|
| ARH freezes a pre-declaration and detects later edits | regression suite + pilot E1–E3 passed | rerun E1–E3 on release tag and archive JSON | strong pilot |
| concurrent agents do not allocate the same iteration | atomic claim implementation + pilot E4: 8 concurrent claims, 8 unique IDs | repeat E4 on release tag and report collision count | strong pilot |
| failed execution remains visible | run receipts/logging + failure regressions + pilot E6 passed in Singularity CI (run 34824408618) | rerun E6 on release tag and archive JSON | strong pilot |
| same-family cross-check is refused by default | gate/harness implementation + pilot E7 passed before provider call | rerun E7 on release tag | strong pilot |
| stale review evidence becomes ineligible | hash-bound review records + pilot E8 passed | rerun E8 on release tag | strong pilot |
| a study can resume without chat history | `PROGRESS.md`, status/next/context + pilot E10 passed from a fresh cwd | independent tester completes RQ2 with no prior chat | partial |
| ARH works with a real Slurm environment | prior internal Slurm validation summary | capture release-candidate Slurm run with public-safe metadata | partial |
| ARH can use pinned task environments | digest enforcement + Apptainer CI | clean release checkout reproduction and recorded digest | partial |
| automatic host bootstrap does not require preinstalled micromamba | bootstrap implementation + CI path | clean independent installation from public docs | partial |
| protocol overhead is small enough for research workflows | overhead pilot: +0.52 s (1.5%) over Nextflow on a ~30 s task, +1.1 s on a trivial task; protocol commands 0.1–0.5 s (`paper/overhead-pilot.md`) | rerun on release tag; add a Slurm-queued variant | strong pilot |
| cross-check roles help identify known defects | anecdotal engineering experience only | frozen defect corpus, repeats, TPR/FPR/qualified rate | missing |
| software is usable outside the developer's environment | architecture + CI only | one independent reproduction; preferably second scheduler/site | missing |
| software is useful beyond one scientific domain | domain-agnostic design only | second public use case or external adoption | missing |

## Evidence rules

1. **Do not infer validation from implementation.** A feature existing in code is
   evidence that it was implemented, not that it works in every supported
   environment.
2. **Do not turn a test suite count into a scientific performance metric.** Tests
   show maintained behavior; they do not estimate scientific error detection.
3. **Do not call model-family diversity independence.** Cross-family review is a
   reduction in one source of correlated error, not orthogonal validation.
4. **Retain negative evidence.** Failed installs, failed tasks and false reviewer
   objections belong in the evaluation record.
5. **Bind the paper to a tag.** Final tables and figures must name the exact
   release/commit used to produce them.

## Planned tables/figures

### Figure 1 — research loop

```text
Research question
      ↓
Pre-declare + freeze
      ↓
Execute on existing compute
      ↓
Report + foreign-family critique
      ↓
Gate + append-only record
      ↺ next question
```

### Table 1 — deterministic protocol failures

The values below are the engineering pilot where available. Replace all pilot
entries with release-tag results before submission.

| ID | Scenario | Expected | Pilot observed | Pilot pass? | Final release result |
|---|---|---|---|---|---|
| E1 | unfilled pre-declaration | refuse | freeze refused | yes | TODO |
| E2 | result before freeze | refuse | freeze refused | yes | TODO |
| E3 | frozen declaration edited | refuse | results gate detected mismatch | yes | TODO |
| E4 | concurrent claim | unique IDs | 8/8 IDs unique | yes | TODO |
| E5 | immutable input write | refuse | guard refused | yes | TODO |
| E6 | task exits non-zero | preserve failure | submit exit 1; non-zero receipt retained (CI run 34824408618) | yes | TODO |
| E7 | same-family reviewer | refuse | review request refused | yes | TODO |
| E8 | reviewed evidence changes | stale review rejected | old review ineligible | yes | TODO |
| E9 | interrupted submission | recoverable lock/state | SIGTERM recorded; launch lock released (CI run 34824408618) | yes | TODO |
| E10 | cold resume | correct next state | status/next resolved from fresh cwd | yes | TODO |

### Table 2 — portability/reproduction

| Environment | Setup success | `arh doctor` | Example reproduced | ARH iteration completed | Interventions |
|---|---|---|---|---|---:|
| GitHub Actions / local / Apptainer | CI setup path exercised | CI path exercised | direct deterministic fixture passes | TODO | 0 |
| maintainer Slurm site | TODO | TODO | TODO | TODO | TODO |
| independent environment | TODO | TODO | TODO | TODO | TODO |

### Table 3 — review benchmark

Do not populate until the corpus and evaluation protocol are frozen.

| Defect class | Cases | True-positive rate | False-positive rate | Qualified/abstain rate | Repeats |
|---|---:|---:|---:|---:|---:|
| paired vs independent | TODO | TODO | TODO | TODO | TODO |
| post-result selection | TODO | TODO | TODO | TODO | TODO |
| negative-control ignored | TODO | TODO | TODO | TODO | TODO |
| set membership mismatch | TODO | TODO | TODO | TODO | TODO |
| estimand denominator/unit mismatch | TODO | TODO | TODO | TODO | TODO |
| unsupported detection limit | TODO | TODO | TODO | TODO | TODO |
