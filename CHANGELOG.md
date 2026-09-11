# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions are protocol/tooling versions; see `PROTOCOL.md`.

## [Unreleased]

Most fixes below were found by running AutoResearch HPC on a real study: nine iterations of an
exome structural-variant project on a Slurm + Singularity cluster, with Codex as
the foreign reviewer.

### Fixed
- **Reviews no longer die on stderr volume.** `codex exec` echoes the whole
  prompt to stderr, and the 16 KB stderr cap SIGKILLed every review whose prompt
  exceeded it (exit 66). The dead attempt still spent a review round. Only
  stdout, the review itself, is bounded now; stderr is truncated on disk but
  drained.
- **Provider refusals no longer consume a review round.** `codex exec` exits 0
  on "You've hit your usage limit". Refusals (quota, rate limit,
  authentication) are recorded with `provider_error: true`, exit 75, and are
  named in `arh gate results`.
- **Standing rules are checked before a review is dispatched.** They used to run
  only in `arh gate results`, after the review, so a one-word fix to the report
  invalidated the hash-bound review and cost a second round. `arh ask` now
  refuses a report that the results gate would reject (non-blind roles).
- **Review responses have a home.** The report template and the `iterate` skill
  asked for the cross-check evaluation to be written into the report after
  review, which invalidated the review. The evaluation now goes in
  `REVIEW_RESPONSE.md` at the iteration root; follow-up computation goes through
  `arh verify`.
- **A running submission can be stopped cleanly.** The wrapper forwards
  SIGTERM/SIGINT/SIGHUP to Nextflow (a second signal escalates to SIGKILL),
  records the signal in `run.json` and releases the launch lock. Signalling it
  used to kill it before the lock was released, so every later submit under that
  name refused. The lock records its owner in `owner.json`. A lock left by a dead
  process on the same host is reclaimed atomically; bare, live or remote locks
  still refuse.
- **Run receipts hash the scripts a workflow calls.** `run.json` records
  `script_sha256` for every file under the iteration's `scripts/`. It used to
  hash only the workflow, so two runs that did different things could have
  identical receipts.
- **Setup scripts no longer race.** `setup-nextflow.sh` and `setup-runtime.sh`
  serialise their rewrite of `site.md`. Both now record replayable `@EXPLICIT`
  locks; plain `micromamba list --explicit` output has a header and cannot be
  passed to `--file`. A duplicated `.arh` branch left in both scripts by the
  rename is gone.
- The "not inside a project" error names `ARH_PROJECT`, the override for
  harnesses that reset the working directory between commands. The README and
  `AGENTS.md` document it.
- The 0.2.0 notes below were garbled by the automated rename. They described a
  compatibility layer that 0.2.0 does not ship, and now match the code.
- Leftover `discovery-loop` names: the Claude Code `PATH` example (it pointed at
  `../discovery-loop/bin`), the Codex profile, the adversary role and the test
  banner.

### Added
- `scripts/lock-env.sh` exports an existing conda/micromamba environment as a
  replayable `@EXPLICIT` lock. It can also recreate the environment and verify
  that the package list is identical.
- `docs/hpc-execution.md` covers pulling the runtime image, run receipts and
  caching, stopping a submission, and Nextflow strict syntax (a Groovy `import`
  is a compile error that surfaces only after submit).
- A tested procedure for migrating a 0.1 study, in
  [docs/migration-hardening.md](docs/migration-hardening.md).
- Six regression tests: `test_verbose_stderr_does_not_abort_review`,
  `test_provider_error_does_not_consume_round`,
  `test_rule_violation_blocks_review_before_dispatch`,
  `test_sigterm_to_wrapper_releases_lock`,
  `test_dead_owner_lock_reclaimed_and_scripts_hashed` and
  `test_live_owner_lock_is_kept`.

### Changed
- Host bootstrap no longer requires micromamba to be installed beforehand. The
  pinned standalone binary is downloaded on demand, SHA-256 verified, cached
  under the project `.arh/tools/` directory, and recorded in `micromamba.lock`.
  Explicit `--micromamba` / staged-binary use remains available for offline HPCs.
- The README uses the full-resolution banner (`docs/assets/banner.png`). The
  low-resolution JPEG and the unreferenced WebP are gone. Setup steps are
  numbered consistently, and the README documents SSH cloning and
  `ARH_PROJECT`.

## [0.2.0] — 2026-09-11

### Changed
- Renamed the public CLI from `dl` to **`arh`** (AutoResearch HPC) across
  commands, paths and documentation. Project state lives in `.arh/`,
  configuration fences are `arh-config`, and environment variables use the
  `ARH_` prefix (`ARH_HOME`, `ARH_PROJECT`, `ARH_TEST_SITE`). There is no
  compatibility layer: `dl`, `.dl/`, `dl-config` and `DL_*` are no longer
  recognised.
- `arh init` now discovers Slurm/PBS/local and Singularity/Apptainer defaults,
  supports `--bootstrap`, `--micromamba`, `--runtime`, and `--scheduler`, and
  points directly to `arh doctor` for remaining setup work.
- `arh doctor` now diagnoses the host Nextflow environment, runtime image digest,
  scheduler clients, harness families and standing rules, with concrete fix
  commands for missing setup.
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
- 0.1 studies (`.dl/`) must be migrated before `arh` can open them; see
  [docs/migration-hardening.md](docs/migration-hardening.md). Frozen iteration
  files are not rewritten.

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
