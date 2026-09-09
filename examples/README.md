# Worked example

A complete pass through the loop on a generic toy analysis — no domain tools, no
cluster, no network. Every block below is real captured output.

The same sequence runs as `test/run_tests.sh`, so if this drifts, CI fails.

## 1. Create a project

```console
$ dl init my-study && cd my-study
Initialised discovery-loop project at /…/my-study

  PROGRESS.md                the record — read this first
  AGENTS.md                  harness contract (CLAUDE.md symlinks here)
  GOTCHAS.md                 silent failure modes, as executable assertions
  rules/                     standing rules every iteration inherits
  .dl/config/                edit these before your first iteration

Next: edit .dl/config/site.md, then  dl claim -t "your first question"
```

## 2. Check the machine against the config

```console
$ dl doctor
  OK   scheduler local (no cluster required)
dl: container_runtime=none — tools are unpinned, results are not reproducible
  acceptable for smoke tests only

harnesses:
  OK   claude (anthropic) — claude 2.1.265 (Claude Code)
  OK   codex (openai) — codex codex-cli 0.149.1
  OK   opencode (mixed) — opencode 1.14.50
  OK   producer claude (anthropic) != verifier codex (openai)

rules:
  OK   association-not-causation
  OK   null-is-upper-bound
  OK   negative-controls-required
  OK   detection-limit-stated

No problems found.
```

`dl doctor` warns rather than fails on `container_runtime = none`: unpinned tools
are fine for a smoke test and disqualifying for a result.

## 3. Claim a number

```console
$ dl claim -t "Do groups A and B differ in mean?"
1
claimed iteration 1 at /…/my-study/iterations/iteration1
next: dl new -n 1   (writes the pre-declaration you must complete BEFORE running anything)
```

Claiming is atomic — the directory *is* the lock. The test suite fires six
concurrent claims and asserts they get six distinct numbers, because two agents
once created the same iteration eleven minutes apart on a real project.

## 4. The gate refuses an unfilled pre-declaration

```console
$ dl new -n 1 && dl gate predeclare -n 1
gate: pre-declaration, iteration 1
  OK   results/ is empty
  OK   section: Question
  OK   section: Estimand
  OK   section: Instrument
  OK   section: Acceptance criteria
  OK   section: Negative controls
  OK   section: Detection limit
  OK   section: Prediction
  FAIL template placeholders remain unfilled
  OK   negative-controls-required
  OK   detection-limit-stated

gate FAILED (1). Nothing was frozen; fix and re-run.
```

Nothing is frozen on failure. Fill the sections in and re-run:

```console
$ dl gate predeclare -n 1
gate PASSED. Pre-declaration frozen:
  97f064ad8c07ed25f99175d6f99da0d03a44210702337d8493b201e2679ff8a5
The README is now immutable. Corrections go in a new iteration.
```

That hash is the whole mechanism. It is what makes "we planned this in advance"
checkable rather than asserted.

## 5. Run the work

```console
$ dl submit iterations/iteration1/scripts/it1_01_run.sh -n it1_01 -w
submitted it1_01 as job 1831084 via local
```

Identical command under SLURM once `scheduler = slurm` is set in `site.md`; the
job id is then an `sbatch` id rather than a pid.

## 6. Cross-check with a foreign harness

```console
$ dl ask --role estimand-auditor -n 1
cross-check: role=estimand-auditor harness=codex (openai) vs producer=claude (anthropic)
wrote iterations/iteration1/CROSSCHECK_estimand-auditor_codex_20260908T093907Z.md
VERDICT: QUALIFIED
```

**This is a real result from a real run, and it found a real defect.** Codex,
reading only the pre-declaration, wrote:

> Because observations are paired, permutations should preserve pairing —
> normally by swapping A/B labels within pairs. Unrestricted permutation across
> all 200 observations would test a different null and discard the matched design.

The toy script did exactly that: it pooled all 200 observations and shuffled.
The pre-declaration said *paired*; the test was not. Every individual step was
correct and the number answered a different question — which is the error class
the `estimand-auditor` role exists for, caught on the first live dispatch by a
model from a different family.

The verdict is evidence, not a ruling. Record what you accepted, what you
rejected, and why.

## 7. Conclude

```console
$ dl gate results -n 1
gate: results, iteration 1
  OK   pre-declaration unchanged since freeze
  OK   report present
  OK   association-not-causation
  OK   null-is-upper-bound
  OK   negative-controls-required
  OK   detection-limit-stated
  OK   cross-checked by a foreign harness

gate PASSED. Iteration 1 may be concluded in the ledger.
```

Edit the README after freezing and the same gate says so:

```console
  FAIL README.md CHANGED after pre-declaration was frozen
     frozen: 97f064ad8c07ed25f99175d6f99da0d03a44210702337d8493b201e2679ff8a5
     now:    3e2b8c14f0a97d5be1c6f2803a5d4977ce9a1b0e64f7a2d83b95c07e1a4f6d20
```

## 8. Update the record

```console
$ dl ledger render && dl ledger check && dl status
rendered status table into PROGRESS.md

Ledger consistent with 1 iteration(s) on disk.

IT    AGENT        PREDECL     RESULTS   XCHECK  TITLE
----- ------------ ----------- --------- ------- -----
1     claude       frozen      report    yes     Do groups A and B differ in mean?
```

## What the standing rules refuse

```console
$ dl gate rules draft_report.md
  FAIL association-not-causation — uses 'causes|caused by|leads to|…' language without stating 'association|…'
  FAIL null-is-upper-bound — uses 'no effect|there is no|…' language without stating 'upper bound|…'
```

Both are satisfiable by an author writing in bad faith, and neither is meant to
be a proof of rigour. They catch the far commoner case: a correct analysis
written up in language stronger than it supports.

## Verifying a result later

```console
$ dl verify new panel_recalc -m re-implementation
$ dl verify gate panel_recalc
  FAIL success criterion must name which elements must come back, not how many
```

Reproducing the *size* of a candidate set is not reproducing the set. On a real
project a 41-element set reproduced at the right size and differed in
membership; the odd element out was a binning artefact.
