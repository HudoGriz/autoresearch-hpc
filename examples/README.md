# Worked example

A complete pass through the AutoResearch HPC loop on a generic toy analysis — no
domain tools, cluster or network required.

## 1. Create and inspect a project

```console
$ arh init my-study
Initialised AutoResearch HPC project at /…/my-study
  detected scheduler: local
  detected container command: singularity

$ cd my-study
$ arh doctor
```

Configuration lives under `.arh/config/`. `arh init` discovers the obvious site
defaults; `arh doctor` tells you what still needs to be staged or configured.

## 2. Claim and pre-declare

```console
$ arh claim -t "Do groups A and B differ in mean?"
1
claimed iteration 1 at /…/my-study/iterations/iteration1
next: arh new -n 1

$ arh new -n 1
$ arh gate predeclare -n 1
gate: pre-declaration, iteration 1
  FAIL template placeholders remain unfilled
```

Nothing freezes on failure. Complete the required question, estimand, instrument,
acceptance criteria, negative controls, detection limit and prediction, then:

```console
$ arh gate predeclare -n 1
gate PASSED. Pre-declaration frozen:
  97f064ad8c07ed25f99175d6f99da0d03a44210702337d8493b201e2679ff8a5
```

That frozen hash is the mechanism that makes later edits detectable. A design
change is represented by a new iteration rather than rewriting the old one.

## 3. Run the work

```console
$ arh submit iterations/iteration1/scripts/experiment.nf -n it1_01
```

Nextflow owns the execution graph and caching. With `scheduler = slurm`, tasks
flow to Slurm; with `local`, they run locally. Scientific tasks use the configured
digest-pinned Singularity/Apptainer runtime.

## 4. Cross-check with a foreign model family

```console
$ arh ask --role estimand-auditor -n 1
cross-check: role=estimand-auditor harness=codex (openai) vs producer=claude (anthropic)
VERDICT: QUALIFIED
```

In the original toy example, the reviewer caught a real design mismatch: the
pre-declaration described paired observations while the permutation pooled all
observations, thereby testing a different null. This is exactly the sort of
error the protocol tries to make visible.

The verdict is evidence, not a ruling. Record what you accepted, rejected and
why.

## 5. Conclude without rewriting history

```console
$ arh gate results -n 1
$ arh ledger render
$ arh ledger check
$ arh status
```

Editing `iterations/iteration1/README.md` after freezing makes the results gate
fail with an altered-hash error. A correction is a new iteration that points
back to the superseded one.

## Standing rules

```console
$ arh gate rules draft_report.md
```

The shipped rules catch common reporting failures such as causal wording from an
observational design, a bare “no effect” claim without its detection bound,
missing negative-control reporting, and an unstated detection limit. They are
lint/gates, not proofs of scientific rigor.

## Verification later

```console
$ arh verify new panel_recalc -m re-implementation
$ arh verify gate panel_recalc
```

For set-valued results, success criteria must compare membership rather than only
the count. Use a frozen discovery DAG for stronger blind re-implementation:

```console
$ arh dag init -n 1
$ arh dag check -n 1
$ arh dag freeze -n 1
$ arh replicate -n 1 --agents 3
```
