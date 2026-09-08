# Rule: negative controls are not optional

An enrichment, a classifier or a screen that has never been run against a set
expected to be null has not been tested — it has only been described. The
control must be pre-declared, not chosen after the result.

**Enforcement.** The pre-declaration must name its negative controls; the report
must state how they behaved.

```dl-config
id       = negative-controls-required
severity = error
applies  = predeclaration report
requires = negative control|negative controls
```
