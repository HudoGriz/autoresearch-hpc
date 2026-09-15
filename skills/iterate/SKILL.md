---
name: iterate
description: Run one complete AutoResearch HPC iteration — claim a number, pre-declare the design before any result exists, execute, cross-check with a foreign harness, and record the outcome in the ledger.
---

# Run an iteration

One iteration answers **one question**. If the question becomes “and also…”,
that is normally another iteration.

## 1. Claim

```bash
arh claim -t "the question, stated as a question"
```

This is the only supported way to take an iteration number.

## 2. Pre-declare

```bash
arh new -n N
```

Complete every section of `iterations/iterationN/README.md`, then freeze it:

```bash
arh gate predeclare -n N
```

The frozen declaration is immutable. A changed design is a new iteration.

## 3. Execute

Keep scripts under the producing iteration and pin scientific tools:

```bash
arh run samtools -- samtools view -c input.bam
arh submit iterations/iterationN/scripts/experiment.nf -n itN_01
```

Scientific packages come from `arh env create NAME pkg=version ...`, solved once in
the task image and locked. `arh submit WORKFLOW.nf --lint` checks a workflow before
it runs; `AGENTS.md` shows a minimal one.

Check acceptance criteria before interpretation. A failed criterion is this
iteration's result: report and conclude it, then pre-declare the handling in a new
iteration. It is not a reason to stop.

## 4. Report

Write `results/report/iterationN_report.md`. Report the pre-declared quantity,
negative-control behaviour, detection limit and missed predictions.

## 5. Cross-check

```bash
arh ask --role adversary -n N
arh ask --role estimand-auditor -n N
```

Evaluate findings on their merits. A verdict is evidence, not a ruling.

`arh ask` blocks until the review is written; stay in the session until it returns.
Exit 75 (usage or rate limit, authentication) and exit 77 (the provider refused the
content) spend no review round. After 75, wait for the stated reset and run it again;
after 77, the configured fallback verifiers have already been tried.

**Where to record it.** A review is bound to the report's sha256 and to every
file under `results/`. Editing the report, or adding a file under `results/`,
after the review makes it ineligible. So:

- write the report's *Cross-check* section before `arh ask`, as a pointer;
- put your evaluation in `iterations/iterationN/REVIEW_RESPONSE.md` — at the
  iteration root, outside `results/`, and not named `CROSSCHECK_*` (that glob
  counts review attempts);
- if a finding needs new computation, do it through `arh verify`, not by
  changing the iteration, and append the outcome to the response file.

## 6. Conclude

```bash
arh gate results -n N
arh ledger render
arh ledger check
```

Record what the iteration established, its strongest limit and what it
supersedes. Never edit an older conclusion to make history look cleaner.
