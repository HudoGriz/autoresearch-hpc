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

Check acceptance criteria before interpretation.

## 4. Report

Write `results/report/iterationN_report.md`. Report the pre-declared quantity,
negative-control behaviour, detection limit and missed predictions.

## 5. Cross-check

```bash
arh ask --role adversary -n N
arh ask --role estimand-auditor -n N
```

Evaluate findings on their merits. A verdict is evidence, not a ruling.

## 6. Conclude

```bash
arh gate results -n N
arh ledger render
arh ledger check
```

Record what the iteration established, its strongest limit and what it
supersedes. Never edit an older conclusion to make history look cleaner.
