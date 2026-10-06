---
name: verify
description: Re-examine an object an iteration already produced by recalculation, re-implementation, or an alternate analytic choice.
---

# Verify a result

Verification is not a new analysis claim. It lives under `verification/<object>/`,
reads upstream evidence and never rewrites the producing iteration.

Pre-declare the verification before running it, compare membership rather than
only counts when the object is a set, and state the original result being tested.

```bash
arh verify new <object> -m recalculation --of N   # N: the iteration whose object is checked
arh verify gate <object>                          # freezes the plan (and any declared imports)
arh verify run <object> verification/<object>/scripts/check.nf
arh verify conclude <object>                      # RESULT.md: one OUTCOME line; needs a run receipt
```

The computation runs through `arh verify run`, in the pinned task image with a
run receipt, never on a login node by hand. `arh verify conclude` checks that the
plan is still frozen, that `RESULT.md` carries one `OUTCOME: CONFIRMED`,
`REFUTED` or `INCONCLUSIVE` line, and that a successful receipt of this plan
exists (or takes `--without-run REASON`). The outcome then appears in the ledger
beside the iteration it verifies.

For a code-independent re-implementation:

```bash
arh ask --role reimplementer -n N
```

Record the mode, agreement to declared precision, every disagreement and any
ambiguity the independent implementation had to resolve. Finding a defect is a
successful verification outcome; state what it changes about the original claim.
