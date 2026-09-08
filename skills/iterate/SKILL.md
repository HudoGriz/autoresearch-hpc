---
name: iterate
description: Run one complete iteration of the discovery loop — claim a number, pre-declare the design before any result exists, execute, cross-check with a foreign harness, and record the outcome in the ledger. Use whenever starting a new analysis question in a discovery-loop project.
---

# Run an iteration

One iteration answers **one question**. If you find yourself writing "and also",
that is a second iteration.

## 1. Claim

```bash
dl claim -t "the question, stated as a question"
```

Returns `N`. This is the only way to take a number — `mkdir` by hand races
against every other agent on the project.

## 2. Pre-declare

```bash
dl new -n N
```

Complete every section of `iterations/iterationN/README.md`. The sections are
not paperwork; each one blocks a specific failure:

| section | the failure it blocks |
|---|---|
| Question | scope creep into an unanswerable composite |
| **Estimand** | a technically correct computation of the wrong quantity |
| Instrument | an unpinned tool making the run unreproducible |
| Acceptance criteria | interpreting output from a run that silently failed |
| Negative controls | reporting a pipeline artefact as a finding |
| **Detection limit** | a threshold discarding the events you are looking for |
| Prediction | remembering, afterwards, that you expected this all along |

Then:

```bash
dl gate predeclare -n N
```

The gate freezes the README's hash. **From here the README is immutable.** If
the design must change, conclude this iteration as abandoned and claim a new one.

## 3. Execute

Scripts go in `iterations/iterationN/scripts/`, named `itN_NN_description.sh`.
Source nothing from a later iteration. Pin every tool:

```bash
dl run samtools -- samtools view -c input.bam
dl submit iterations/iterationN/scripts/itN_01_align.sh -n itN_01
```

Check the acceptance criteria **before** looking at the result. A run that
failed its criteria has no result to interpret.

## 4. Report

Write `results/report/iterationN_report.md` from `templates/iteration/REPORT.md`.

Report the number you pre-declared. Where the prediction missed, say so. Where
the result is null, the headline is the upper bound — "no effect" is not a
finding a two-arm design can support.

## 5. Cross-check

```bash
dl ask --role adversary -n N
dl ask --role estimand-auditor -n N     # whenever the estimand is at all subtle
```

Then **evaluate every finding on its merits**. Agree or disagree with reasons —
never accept a cross-check verdict wholesale, and never dismiss one because it
is inconvenient. Record what you did about each finding, including the ones you
rejected and why.

## 6. Conclude

```bash
dl gate results -n N     # fails if the pre-declaration changed, or nothing cross-checked
dl ledger render
dl ledger check
```

Add a paragraph to `PROGRESS.md` §4: the claim, its strongest limit, and what it
supersedes. Supersession is stated in the new entry — never by editing the old one.
