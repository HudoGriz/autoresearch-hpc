# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions are the **protocol** version; see `PROTOCOL.md`.

## [Unreleased]

### Added
- `dl verify` — the verification track had a skill and templates but no
  command. Its gate requires a membership-based success criterion, per §6.4.
- `dl --version`.
- CI on Linux and macOS, shellcheck, and JSON schema validation.
- `CITATION.cff`, `CONTRIBUTING.md`, `SECURITY.md`, issue and PR templates.

### Fixed
- Portability: `readlink -m`, `readlink -f` and `sed -i` are GNU-only. The first
  of those made the immutable-input guard fail outright on macOS/BSD, which
  disabled a safety check rather than merely erroring.
- The test suite called `sha256sum` directly, bypassing the library's fallback.

## [0.1.0] — 2026-09-08

First working version: protocol, tooling and harness wiring.

### Added
- `PROTOCOL.md` — normative spec. §10 names the seven clauses a conforming
  implementation must enforce mechanically.
- `bin/dl` — claim, new, gate, ask, run, submit, guard, ledger, status, doctor.
- `lib/` — pluggable scheduler (slurm/pbs/local) and container runtime
  (apptainer/singularity/docker/none), both selected from Markdown config.
- `skills/` — iterate, verify, cross-check (four roles), ledger.
- `harness/` — Claude Code, Codex and OpenCode wiring from one `AGENTS.md`.
- `schema/` — claim, finding and cross-check types.
- `test/run_tests.sh` — 78 checks, no cluster or network required.

### Fixed
- Pre-declaration placeholder detection was line-anchored, so an untouched
  template passed the gate.
- `required_sections` split on whitespace, breaking multi-word headings.
- `codex exec` needs `--skip-git-repo-check` outside a git repo, and blocked on
  stdin when the prompt was passed as an argument. Both surfaced on the first
  live dispatch; neither was reachable from the stubbed test suite.
