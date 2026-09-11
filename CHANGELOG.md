# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions are protocol/tooling versions; see `PROTOCOL.md`.

## [0.2.0] — 2026-09-11

### Changed
- Renamed the public CLI from `arh` to **`arh`** (`AutoResearch HPC`) across the
  user-facing documentation and command paths. New projects use `.arh/` as the
  authoritative state directory. A temporary `.arh -> .arh` compatibility symlink
  is created for pre-1.0 migration and older internal adapters.
- `arh init` now discovers Slurm/PBS/local and Singularity/Apptainer defaults,
  supports `--bootstrap`, `--micromamba`, `--runtime`, and `--scheduler`, and
  points directly to `arh doctor` for remaining setup work.
- `arh doctor` now diagnoses the host Nextflow environment, runtime image digest,
  scheduler clients, harness families and standing rules, with concrete fix
  commands for missing setup.
- Configuration fences are now `arh-config`; the parser accepts legacy
  `arh-config` only for migration.
- The normative protocol is now **0.2.0**. The former “unreleased hardening
  amendment” has been integrated into the relevant normative sections instead
  of living outside the released specification.
- Protocol §10 now explicitly identifies **eight** mechanically enforced
  boundaries, matching the conformance suite.

### Added
- `arh arm` — parallel sub-analyses with their own acceptance criteria,
  negative control and recorded fate.
- `arh dag` — reconstruct and freeze the path a result took.
- `arh replicate` — fan-out blind replication from the frozen DAG.
- `arh next` — deterministic next-action guidance.
- `arh status --json` — machine-readable state.
- `arh verify` — explicit verification track.
- CI integration, shellcheck/schema validation, citation metadata, security and
  contribution guidance.

### Hardened
- Cross-check eligibility is hash-bound to the declaration, report and review,
  with concrete producer/verifier families and successful invocation metadata.
- Pre-declaration freezes cannot be silently overwritten.
- Harness argument parsing avoids shell evaluation and uses bounded execution.
- Local execution propagates failures and records execution metadata.
- Non-smoke container execution requires declared image identity.
- Relative immutable input paths are normalized before write checks.

### Migration
- Use `arh` in scripts and documentation from this release onward.
- New projects store configuration and framework state in `.arh/`.
- Existing 0.1 `.arh/` studies remain readable during the pre-1.0 transition;
  migrate their state directory and replace `arh` command invocations before 1.0.

## [0.1.0] — 2026-09-08

First working version of the discovery-loop protocol and tooling.

### Added
- Normative protocol and mechanically enforced pre-declaration boundaries.
- Initial `arh` CLI with claim, new, gate, ask, run, submit, guard, ledger,
  status and doctor commands.
- Pluggable scheduler/container configuration and portable agent instructions.
- Initial schemas, skills and regression tests.

### Fixed
- Pre-declaration placeholder detection, multi-word required sections, and the
  first live Codex non-interactive dispatch issues.
