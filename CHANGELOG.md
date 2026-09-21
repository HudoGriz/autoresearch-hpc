# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions are protocol/tooling versions; see `PROTOCOL.md`.

## [Unreleased]

Most fixes below were found during internal field deployment on a Slurm +
Singularity workflow with a separately configured reviewer. The source research
material is intentionally not part of this software release; the failure classes
that mattered are preserved as tests and generic documentation instead.

### Added
- **Optional external generators via `arh evoke`.** Biomni, AI Scientist v2 and
  Agent Laboratory now have disabled-by-default registry entries. ARH sends a
  bounded request through a site-owned, shell-free command adapter and retains
  request/config hashes, version, response, artifacts and exit status under the
  iteration. No upstream source is vendored, and generated output is advisory:
  it cannot satisfy a results gate. The Evoke skill selects a tool only when its
  specialist workflow materially fits and requires a request preview plus an
  explicit per-run external-code/data acknowledgement.
- **`arh site detect`** probes the machine and proposes a `site.md` block instead of
  leaving every resource key to be typed by hand. `arh init` only tested whether a
  scheduler's client commands existed, so `slurm_partition`, `slurm_account` and the
  time/cpu/memory defaults were hand-filled for each project — the same edit twelve
  times across a replication benchmark, with a wrong queue name only surfacing when
  the first job was rejected. It lists the queues visible to you with their walltime,
  core, memory and generic-resource limits, reports the accounts and QOS you can
  charge to (saying so plainly when `sacctmgr` is unreachable rather than quietly
  proposing none), and inside a project checks the current settings against the
  machine, failing on a queue that does not exist or a request larger than any node
  in it. It never writes the file: choosing a queue is a policy decision. Schedulers
  are a table of probes rather than hardcoded branches, and one the framework cannot
  yet drive is reported with what adding it needs instead of being silently treated
  as `local`.
- **`arh wait [-n N]`** blocks until an iteration's submissions and reviews have
  finished. Headless sessions get no completion notice and end when their reply
  ends: in a replication benchmark, Claude Code producers that backgrounded work and
  ended their reply to wait lost two rounds in each of two studies.
- **`arh env create NAME pkg=version ...`** solves a scientific environment once
  inside the task image, writes a replayable lock (`.arh/NAME-explicit.lock`, hashed
  by every run receipt) and prints the prefix. Without packages it rebuilds from the
  lock and verifies the package list. A built environment does not change; a new
  package set is a new name. Producers had built environments in several different
  ways, unpinned until someone locked them, one of them in the background.
- **Content-policy refusals are their own outcome.** `arh ask` exits 77 when the
  provider refuses the content itself (Codex flagged a public RNA-seq count table as
  a biological risk). Like a limit, it spends no review round. Each harness in the
  new `verifier_fallback` setting is then tried in turn; `arh doctor` checks their
  families.
- `arh ask` prints the provider's own refusal line. The review record keeps it, its
  kind (`limit`, `auth` or `refusal`) and any stated reset time (`retry_hint`).
- **Review token usage.** A command template may pass `{usage}`, a file the reviewer
  writes token counts or cost to; the record stores it as `usage`.
  `harness/claude/review.sh` and `harness/codex/review.sh` do this for the two CLIs.
- **Shared environments.** `arh init --env-cache DIR` (or `ARH_ENV_CACHE` for the
  setup scripts) builds the pinned host and task environments once per pin set and
  reuses them across projects; each project used to build its own, about 1.5 GB.
- `nextflow_reports = html | gzip | none` in `site.md`. The HTML report and timeline
  were 99% of a submission's evidence bytes (1.9 MB per run).
- `arh submit WORKFLOW.nf --lint` runs `nextflow lint` with the pinned controller,
  before any attempt directory exists.
- `AGENTS.md` shows a minimal workflow for `arh submit` (what a task sees, where the
  evidence goes, how packages are declared), says how to run unattended, and says
  that a failed acceptance criterion is a result to report, not a reason to stop.
  Producers had read ARH internals to work out how to submit, and one stopped a study
  as blocked on a failed criterion. `arh next` says the same and points to `arh wait`
  while work is running. The iterate and cross-check skills match.
- `docs/headless.md`: lessons from driving producers and reviewers unattended on Slurm.

### Changed
- **`verifier_fallback` now also covers provider limits.** `arh ask` tried the fallback
  list only after a content refusal (exit 77) and gave up on a usage limit (exit 75),
  telling the agent to sleep until the reset the provider stated. That time is not
  reliable: a provider once named a reset five days out, and a probe 44 minutes later
  succeeded. A limit now moves on to the next fallback verifier, and the advice in
  `arh ask`, `AGENTS.md` and `docs/headless.md` treats a stated reset as an upper
  bound to re-probe within, not a schedule.
- `arh migrate` also refreshes a study's copies of `AGENTS.md` and `skills/` from the
  framework, after a backup; skills the study added are kept. Agents read those
  copies, so a framework update never reached them. `arh doctor` warns when they differ.
- The review lock records its owner: `arh wait` tells a running review from a dead
  one, and a lock left by a dead process on the same host is reclaimed instead of
  refusing every later review.
- A reviewer's stderr beyond 16 KB keeps its last 8 KB, where CLIs print refusals.
- CI runs on pushes to every branch, not only `main`.
- `docs/skills-and-token-budget.md` states that the bounds cover reviews only;
  producer sessions are not bounded by `arh`.

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
- **`arh ledger render` no longer adds a second status table.** Given a ledger whose
  status block uses another marker (a 0.1 ledger's), it used to append a second
  table, and `arh ledger check` still passed. `render` now refuses and names the
  marker. `check` now fails whenever the table differs from a fresh render
  (stale, missing or duplicated), not only when an iteration number is absent.
- `arh doctor` compares the protocol recorded in `.arh/VERSION` with the
  framework's, and names `arh migrate` on a mismatch.
- The review-size refusal states the prompt's size, the limit and the size of
  each part. It used to ask for "a smaller explicit evidence packet", which no
  option supplies.
- `arh gate results` warns when a reviewed iteration has no `REVIEW_RESPONSE.md`
  (protocol 6.5 requires every finding to be evaluated).

### Added
- `scripts/lock-env.sh` exports an existing conda/micromamba environment as a
  replayable `@EXPLICIT` lock. It can also recreate the environment and verify
  that the package list is identical.
- `docs/hpc-execution.md` covers pulling the runtime image, run receipts and
  caching, stopping a submission, and Nextflow strict syntax (a Groovy `import`
  is a compile error that surfaces only after submit).
- **`arh migrate [DIR] [--apply]`** moves a 0.1 study to the current layout: state
  directory, fences, ledger markers, `site.md` paths, `AGENTS.md`, `skills/` and
  `.arh/VERSION`. It is a dry run by default and writes a backup before changing
  anything. It never touches iteration or verification files, and running it
  again changes nothing
  ([docs/migration-hardening.md](docs/migration-hardening.md)).
- Standing rules may set `scope = paragraph`, so a forbidden term must be
  qualified in the same paragraph rather than anywhere in the document. The
  default stays `document`, so existing reports are judged as before.
- `harness_<name>_version_cmd`: its first output line is stored in each review
  record as `verifier_version`. The shipped harnesses declare one.
- Regression tests for the above: `test_migrate_legacy_study`,
  `test_ledger_render_refuses_a_foreign_status_block`,
  `test_ledger_check_detects_a_stale_table`, `test_rule_scope_paragraph`,
  `test_review_records_verifier_version`,
  `test_doctor_names_a_protocol_mismatch` and
  `test_gate_warns_without_review_response`.
- Six regression tests: `test_verbose_stderr_does_not_abort_review`,
  `test_provider_error_does_not_consume_round`,
  `test_rule_violation_blocks_review_before_dispatch`,
  `test_sigterm_to_wrapper_releases_lock`,
  `test_dead_owner_lock_reclaimed_and_scripts_hashed` and
  `test_live_owner_lock_is_kept`.
- **Publication-readiness track:** a publication roadmap, a pre-specified
  evaluation plan, a venue-neutral short-paper draft, and a synthetic
  deterministic mean-shift example that is checked in CI.

### Changed
- Host bootstrap no longer requires micromamba to be installed beforehand. The
  pinned standalone binary is downloaded on demand, SHA-256 verified, cached
  under the project `.arh/tools/` directory, and recorded in `micromamba.lock`.
  Explicit `--micromamba` / staged-binary use remains available for offline HPCs.
- The README uses the full-resolution banner (`docs/assets/banner.png`). The
  low-resolution JPEG and the unreferenced WebP are gone. Setup steps are
  numbered consistently, and the README documents SSH cloning and
  `ARH_PROJECT`.
- Publication-facing documentation now uses synthetic or generalized examples
  rather than details copied from the internal source study.

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
