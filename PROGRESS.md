# Framework development state — 2026-09-11

The current implementation uses a host micromamba-pinned Nextflow controller,
Singularity/Apptainer workflow tasks, and protocol gates with bounded foreign
reviews. The public CLI is `arh`; protocol 0.2.0 uses `.arh/` for project state.
See [validation](docs/validation.md), [setup](docs/hpc-execution.md), and
[positioning](docs/positioning.md).

For maintainers in the original workspace, `.audit-study/PROGRESS.md` remains
the authoritative append-only audit resume point. That local study, runtime
images, caches and machine configuration are excluded from the source release.
A fresh clone should initialize its own study with `arh init` and inspect its
environment with `arh doctor`.

This remains an experimental pre-1.0 framework; protocol compliance and
cross-family agreement are not substitutes for scientific validation.
