---
name: cross-check
description: Have a different agent harness review an iteration as adversary, re-implementer, estimand auditor, or gotcha scanner. Use before concluding any iteration, and whenever a result is surprising enough to be attractive.
---

# Cross-check with a foreign harness

```bash
dl ask --role adversary -n N
dl ask --role reimplementer    -n N --harness codex
dl ask --role estimand-auditor -n N
dl ask --role gotcha-scanner   -n N
```

## Why the harness must be foreign

A model reviewing its own output is checking whether the work *looks* like it
was generated correctly — not whether it is correct. It reproduces the reasoning
errors it made while generating, and returns a confident pass. `dl ask` refuses
a verifier in the same model family as the producer; `--same-family` overrides
that, and the resulting record is stamped as the weaker check.

Configure the roster in `.dl/config/harnesses.md`.

## Choosing a role

| role | use it when |
|---|---|
| `adversary` | always, before concluding |
| `estimand-auditor` | the estimand is subtle — a proxy, a ratio, a change over time, anything with a filter in front of it |
| `reimplementer` | the result is load-bearing and you need independence from the code |
| `gotcha-scanner` | the pipeline gained a new tool or a new format conversion |

## Reading the result

Every run writes `CROSSCHECK_<role>_<harness>_<timestamp>.md`, opening with
`VERDICT: SOUND | QUALIFIED | UNSOUND`.

**The verdict is evidence, not a ruling.** Cross-checking models hallucinate
plausible-sounding constraints as readily as they catch real ones. Work through
each finding and decide, with a stated reason, whether it holds. Record both the
findings you accepted and the ones you rejected — a cross-check whose rejections
are undocumented is indistinguishable from one that was ignored.

An `UNSOUND` verdict you disagree with is worth recording in full, with your
counter-argument. If a later iteration proves the cross-check right, that record
is how the loop learns.
