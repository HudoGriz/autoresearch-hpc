---
name: verify
description: Re-examine an object an iteration already produced — recompute it from primary data, re-implement it from its written specification, or test it under a different analytic choice. Use when a result matters enough that its correctness must be established independently, rather than assumed from the code that produced it.
---

# Verify a result

Verification is **not** an iteration. An iteration is a claim on a new analysis;
verification takes an object that already exists and asks whether it holds up.
It lives under `verification/<object>/`, reads iteration outputs, and never
writes to them.

## The four rules

1. **Read-only upstream.** Iteration directories are read, never written.
   Primary data stays immutable.

2. **Pre-declare before running.** A verification that picks its analytic
   variant *after* seeing the answer is not a verification. Write
   `PREDECLARATION.md` — the variant, the seed, the success criterion — before
   any result is recorded.

3. **Membership, not counts.** Reproducing the *size* of a candidate set is not
   reproducing the set. State success in terms of which elements come back, by
   name. This distinction is what catches binning artefacts, off-by-one
   boundaries and silent ordering dependence.

4. **State what is being verified, including its original statistics.** If the
   object was never significant to begin with, that goes at the top, not in a
   footnote.

## Three modes, strongest last

**Recalculation** — rerun the original code on the original inputs. Catches
non-determinism and environment drift. Does not catch a wrong method.

**Re-implementation** — build it again from the written specification alone,
never reading the original code:

```bash
dl ask --role reimplementer -n N
```

This is the strong one. Every ambiguity the re-implementer had to resolve is a
place the specification failed to pin the result down, and those gaps are the
finding whether or not the numbers agree.

**Replication** — a new cohort, or an orthogonal assay. The only mode that tests
the claim rather than the computation. Usually out of reach; say so plainly
rather than letting recalculation stand in for it.

## Recording the outcome

Write `RESULT.md` stating the mode, the agreement to stated precision, every
disagreement characterised (arithmetic / ambiguity / defect), and any
non-determinism found.

**A verification that finds a defect has succeeded.** Say what the defect changes
about the original claim — and if it changes nothing, say that too, with the reason.
