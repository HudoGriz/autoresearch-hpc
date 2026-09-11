# Rule: association, not causation

An observational design cannot separate the exposure of interest from anything
else that changed alongside it — ageing, elapsed follow-up, composition shift,
treatment, secular time. Every contrast is *associated with*, never *caused by*.

**Enforcement.** An iteration report containing causal language in a conclusion
must also contain an explicit statement of the design's causal limits.

```arh-config
id       = association-not-causation
severity = error
applies  = report
forbid   = causes|caused by|leads to|results in|due to
requires = association|associated with|cannot separate|not causal
```
