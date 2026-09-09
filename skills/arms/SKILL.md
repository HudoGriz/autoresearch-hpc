---
name: arms
description: Split an iteration into parallel sub-analyses that fail independently, each with its own acceptance criteria, negative control and recorded fate. Use when one question needs several routes to an answer, or when part of a design might turn out to be infeasible.
---

# Arms

An iteration answers **one question**. An arm is **one route to that answer**.
Arms exist because routes fail independently: in a real project, one iteration
ran arms A through L, and among them Arm C was computationally infeasible as
designed while Arm I-delta produced a positive that its own matched null then
killed. Neither is a footnote — both are results.

```bash
dl arm new  -n N -a A -t "the route"
dl arm gate -n N -a A
dl arm fate -n N -a A -f CONCLUDED
dl arm list -n N
```

Arms may only be created after the iteration itself is pre-declared. They
specialise a pre-declaration; they do not replace one. Each arm gets its own
frozen README with its own acceptance criteria and — this is the part people
skip — **its own negative control**. An arm inherits nothing useful from a
sibling's control.

## Fates

| fate | meaning |
|---|---|
| `CONCLUDED` | ran, produced an interpretable result |
| `NULL` | ran cleanly, nothing above its detection limit |
| `INFEASIBLE` | could not be run as designed |
| `KILLED_BY_CONTROL` | produced a positive its own negative control also produced |
| `ABANDONED` | dropped before completion |

**The last three are results and must appear in the report.** This is the
commonest way a multi-arm iteration overstates itself: arms that did not work
are quietly dropped, and the survivors are written up as though they were the
whole design. Ten arms with one hit is a very different claim from one arm with
one hit, and only the arm record can tell them apart.

`INFEASIBLE` in particular is worth reporting precisely: *what* stopped it, at
which step, and whether a different design could get past it. That is the most
useful thing the next iteration can inherit.

## When not to use arms

If the sub-questions have different estimands, they are different iterations,
not arms of one. The test: could two arms' results contradict each other and
both still be right? If yes, they are answering different questions.
