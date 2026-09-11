---
name: arms
description: Split one iteration into parallel routes that fail independently, each with its own acceptance criteria, negative control and recorded fate.
---

# Arms

An iteration answers one question; an arm is one route to that answer.

```bash
arh arm new  -n N -a A -t "the route"
arh arm gate -n N -a A
arh arm fate -n N -a A -f CONCLUDED
arh arm list -n N
```

Arms are created only after the parent iteration is pre-declared. Each arm has
its own acceptance criteria and negative control.

Valid fates are `CONCLUDED`, `NULL`, `INFEASIBLE`, `KILLED_BY_CONTROL` and
`ABANDONED`. Failed/infeasible/killed arms are reportable outcomes, not work to
hide. If the sub-analyses have different estimands, use separate iterations
instead of arms.
