# Framework development state — 2026-09-10

The current implementation uses a host micromamba-pinned Nextflow controller,
Singularity workflow tasks, and protocol gates with bounded foreign reviews.
See [validation](docs/validation.md), [setup](docs/hpc-execution.md), and
[positioning](docs/positioning.md).

For maintainers in the original workspace, `.audit-study/PROGRESS.md` remains
the authoritative append-only audit resume point. That local study, runtime
images, caches and machine configuration are excluded from the source release.
A fresh clone should initialize its own study with `dl init`.

The source release is prepared for the private HudoGriz/autoresearch-hpc repository. This remains an experimental pre-1.0
framework; do not treat protocol compliance as scientific validation.

Ponytail default-skill integration and the CI dry-run correction are under
validation in local audit iteration 6. See docs/skills-and-token-budget.md.
