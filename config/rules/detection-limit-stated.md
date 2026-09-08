# Rule: state the detection limit in the units of the estimand

A threshold chosen for convenience silently discards the events the study is
looking for. A candidate may be excluded by a stated detection limit; it may
never be excluded by an unexamined floor or cap.

**Enforcement.** Pre-declaration and report must both state the detection limit.

```dl-config
id       = detection-limit-stated
severity = error
applies  = predeclaration report
requires = detection limit|limit of detection|LoD
```
