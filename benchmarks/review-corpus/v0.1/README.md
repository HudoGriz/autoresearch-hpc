# Cross-check benchmark corpus v0.1

This is the first **synthetic, frozen pilot corpus** for evaluating AutoResearch
HPC review roles. It is not yet a publication result and it is deliberately kept
separate from the deterministic gate tests.

The benchmark asks a narrow question:

> Given a frozen pre-declaration, result summary and report, does a configured
> reviewer identify a known analysis/reporting defect without inventing one in a
> clean control?

It does **not** test whether a model can discover new science and it does not make
cross-model agreement independent scientific validation.

## Files

- `cases.json` — artifacts visible to the reviewer;
- `labels.json` — hidden ground truth used only for scoring;
- `validate.py` — checks corpus integrity and keeps visible cases label-free.

Never concatenate `labels.json` into a model prompt. The benchmark runner should
load a case from `cases.json`, render only its `predeclaration`, `results` and
`report`, collect the reviewer response, and score the response afterwards.

## Corpus composition

Version 0.1 contains six single-defect cases and three clean controls:

| Class | Cases |
|---|---:|
| paired design analysed as independent | 1 |
| post-result threshold selection | 1 |
| fired negative control ignored | 1 |
| set size right but membership wrong | 1 |
| estimand denominator/unit mismatch | 1 |
| unsupported detection-limit claim | 1 |
| clean controls | 3 |

All values and entities are synthetic. No case is derived verbatim from a private
study.

## Pre-specified scoring

For each reviewer role/model/provider combination, run each case at least three
times at the same declared model configuration. Preserve the raw output and the
harness metadata for every attempt.

Score at the **case level**:

- **TP** — a defective case where the response identifies the labelled defect or
  an equivalent formulation;
- **FN** — a defective case where it does not;
- **FP** — a clean case where the response asserts a material defect not present
  in the visible evidence;
- **TN** — a clean case without a material unsupported objection;
- **qualified/abstain** — report separately; do not silently force these into
  correct/incorrect.

A response may identify additional genuine issues. Those should be adjudicated by
reviewers blind to model identity and logged separately; do not retroactively
change the primary label unless the corpus is versioned as v0.2.

Primary outputs:

- sensitivity overall and by defect class;
- false-positive rate on clean controls;
- qualified/abstention rate;
- within-case repeat agreement;
- input/output token or byte budget where the provider exposes it;
- latency and provider errors, reported descriptively rather than as accuracy.

## Freeze rule

Once any model is evaluated on v0.1, these cases and labels must not be edited in
place. A correction creates `v0.2/` and documents the changed case IDs. The exact
commit/tag used for the paper must be recorded with the results.

Run the integrity check with:

```bash
python3 benchmarks/review-corpus/v0.1/validate.py
```
