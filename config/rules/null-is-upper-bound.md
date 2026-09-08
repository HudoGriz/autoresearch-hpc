# Rule: every null is an upper bound

A negative result is a statement about what the design could have detected, not
a statement that the effect is zero. Reporting "no effect" without the bound
overstates the result and is not recoverable by a later reader.

**Enforcement.** A report concluding null must state the upper bound it can
exclude, with its power or detection basis.

```dl-config
id       = null-is-upper-bound
severity = error
applies  = report
forbid   = no effect|there is no|nothing was found|effect is zero
requires = upper bound|cannot exclude|detection limit|power
```
