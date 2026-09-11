# Validation scope

Local validation on 2026-09-10 passed 137 core protocol checks and 31 boundary
regressions. Nextflow 26.04.6 ran from a host micromamba environment. Scientific
tasks ran through Singularity-compatible Apptainer on Linux.

After the field fixes listed in the [changelog](../CHANGELOG.md), a re-run on
2026-09-11 (local executor, Apptainer tasks) passed 137/137 core checks and 37/37
boundary regressions. The six new regressions cover:

- reviewer stderr volume;
- provider refusals;
- the standing-rule check before review;
- signal forwarding to a running submission;
- reclaiming a dead owner's lock, with script hashing;
- keeping a live owner's lock.

Observed behaviors included native local success, cached resume, real Slurm
success, deliberate task failure propagated to the controller, and rejection
of a write to an immutable input inside a compute-node container.

One bounded Claude review returned **QUALIFIED**. Five predeclared follow-up
probes passed: final-adapter local success, Slurm success, Slurm failure,
concurrent review refusal, and confirmation of the packaged Nextflow jar.
These probes were authored by the producing family, not independently rerun
by the reviewer. The original review remains unchanged.

Remaining limits include mutable host environment storage, controller writes
outside task-container protections, untested PBS and heterogeneous/GPU tasks,
and model overhead beyond submitted prompt/output limits. This is a cooperative
research protocol, not containment for hostile workflow code or a scientific
truth guarantee.

The original append-only audit records stay in the maintainer's local study.
They include machine-specific paths and runtime data and are not included in
this source release. This page is a publication summary, not a replacement for
the original evidence. GitHub Actions supplies fresh, independently visible
source-checkout validation once the repository is pushed.
