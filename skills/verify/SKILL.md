---
name: verify
description: Re-examine an object an iteration already produced by recalculation, re-implementation, or an alternate analytic choice.
---

# Verify a result

Verification is not a new analysis claim. It lives under `verification/<object>/`,
reads upstream evidence and never rewrites the producing iteration.

Pre-declare the verification before running it, compare membership rather than
only counts when the object is a set, and state the original result being tested.

For a code-independent re-implementation:

```bash
arh ask --role reimplementer -n N
```

Record the mode, agreement to declared precision, every disagreement and any
ambiguity the independent implementation had to resolve. Finding a defect is a
successful verification outcome; state what it changes about the original claim.
