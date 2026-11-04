# Integrations

AutoResearch HPC keeps its own code to what the protocol needs: binding records to hashes and
refusing steps. Where a maintained tool already does a job, ARH calls it. Every integration below
is **on by default**, and each can be switched off in `.arh/config/harnesses.md`.

## What is on, what it needs, how to switch it off

| Feature | Default | Needs | Installed by | Switch off |
|---|---|---|---|---|
| Git record: the project is a git repository of its record, and every command that changes the record is committed | on | git | the system | `git_record = off` |
| [Entire CLI](https://github.com/entireio/cli) 0.11.6: agent, model, tokens and transcript of each session behind those commits | on | git record | `scripts/setup-tools.sh` (release binary, sha256-checked) | `entire = off` |
| [gitleaks](https://github.com/gitleaks/gitleaks) 8.30.1: maintained credential rules on top of ARH's built-in patterns | on (`auto`) | — | `scripts/setup-tools.sh` (release binary, sha256-checked) | `secret_scanner = builtin` |
| [basic-memory](https://github.com/basicmachines-co/basic-memory) 0.23.2: `arh memory search` over `knowledge/` | on | — | `scripts/setup-tools.sh` (PyPI, with pixi) | `memory_search_cmd = <another tool's command>` |
| [Ponytail](https://github.com/DietrichGebert/ponytail) 5.3.3: coding guidance, named by `arh context` | on | — | `scripts/setup-tools.sh` (release archive, sha256-checked, into `.arh/skills/`) | `coding_skill = off` |
| Resume after a usage limit (`arh dispatch`) | `fallback` | `orchestration = per-iteration` | ARH | `dispatch_on_limit = stop` |
| Restart after a reboot (`arh dispatch tick`) | when cron runs it | cron or `scrontab` | ARH | do not schedule it |
| `arh ask --wait-on-limit` | per call | — | ARH | leave the flag out |
| Secret scan of everything sent to a provider | on | — | ARH | `secret_scan = off` (with a recorded reason) |
| [abtop](https://github.com/graykode/abtop) 0.5.5: tokens, context and status of the live Claude Code, Codex and OpenCode sessions linked to an iteration, in `arh sessions -n N` | on | — | `scripts/setup-tools.sh` (release binary, sha256-checked) | — |
| Research skills: [ARIS](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep) 0.4.28 and [Anti-Autoresearch](https://github.com/wanshuiyin/Anti-Autoresearch) (report forensics), for `arh skill` and `arh ask --skill NAME` | on | — | `scripts/setup-tools.sh` (pinned archives, sha256-checked, into `.arh/skills/`) | — |
| Notify the operator (failed run, controller ended, UNSOUND or maintained review) | off | a command, e.g. [apprise](https://github.com/caronc/apprise) for Slack, e-mail or Matrix | site.md `notify =` (`ARH_EVENT`, `ARH_ITERATION`, `ARH_MESSAGE`) | leave it empty |
| [Chaperone](https://github.com/HudoGriz/hpc-chaperone): each agent as its own Unix user | off | Chaperone on the cluster | prefix `harness_<name>_cmd` with `chaperone` | — |

External research generators (AI Scientist v2, Biomni, Agent Laboratory) are not wrapped; ARH's
`arh evoke` was removed on 2026-10-30. Run one yourself and record it with `arh note`.

### Access control is Chaperone's

ARH writes deny rules into the harness configurations it knows (Claude Code, OpenCode, Codex), and
covers sealed inputs with empty mounts in task containers. That does not hold for a harness it
cannot configure, nor against an agent that runs as you. [Chaperone](https://github.com/HudoGriz/hpc-chaperone)
runs a harness as `<you>-<profile>`, a real Unix user with your groups minus banned ones: keep
sealed and restricted data in a group the persona does not hold, and give it access when a freeze
releases a group. With `harness_<name>_cmd = chaperone claude -p {prompt} ...`, `arh doctor` checks
that the persona cannot read any sealed input, and arh still knows the harness as `claude`.

### Installing

`arh init --bootstrap` builds both pinned environments and enables the record:

```bash
arh init /shared/my-study --bootstrap
```

For an existing project:

```bash
scripts/setup-tools.sh <study>        # Entire, gitleaks, abtop, basic-memory, skills (~15 s)
scripts/enable-record.sh <study>      # git init + templates/gitignore, Entire hooks, basic-memory index
```

Entire, gitleaks and abtop are release binaries checked against the sha256 in
`config/dependencies.json`; basic-memory is a pixi environment locked in `.arh/tools-pixi.lock`,
which later builds install exactly. The binaries and the package cache go to `tools_dir` in
`site.md` (else `$ARH_ENV_CACHE/tools`, else `.arh/envs/tools`); on a slow shared filesystem make it
node-local, `tools_dir = /var/tmp/arh-tools-$USER`. The skills go into the project, `.arh/skills/`,
so reviewers on other nodes and other accounts of the project can read them. `arh` puts the tools
**last** on PATH, so a site's own copy wins. If they are missing (a new login node, a cleaned
`/var/tmp`), `arh doctor` says so; rerun `scripts/setup-tools.sh`.

## Git record

`templates/gitignore` ignores everything except the record: the Markdown files, `rules/`,
`skills/`, `knowledge/`, `.arh/config/` and the locks, and in each iteration the pre-declaration,
claims, freezes, reviews, scripts, resources, the files `arh` writes in `metadata/` (not its
subdirectories, except `dispatch/`, `delegations/` and `evocations/`) and the report. Results,
work directories, environments, images and caches stay out. Any single file over
`git_max_file_bytes` (2 MB) is left out too, and named in `.git/info/exclude`. Sealed inputs inside the
project never enter it: before each commit `arh` lists them in `.git/info/exclude` and drops any
that were tracked from the index. Commits made before a path was sealed keep it; a study that
seals a tracked file should rewrite its history (`git filter-repo --path <file> --invert-paths`).

After every successful `claim`, `new`, `gate`, `freeze`, `ask`, `memory`, `ledger`, `note`,
`dispatch` and `verify`, `arh` commits the changes under a lock, so concurrent sessions do not race.
A failed commit only warns: the change stays in the working tree for the next one. The history is
local; nothing is pushed.

## Entire CLI: agent sessions and transcripts

Entire records each agent session and, at every commit, stores a checkpoint (transcript, prompts,
tool calls, files, tokens) as a git ref, and adds an `Entire-Checkpoint: <id>` trailer to the
commit. `scripts/enable-record.sh` enables it for every configured harness Entire knows
(`harness_<name>_entire_agent`: `claude-code`, `codex`, `opencode`), with telemetry off and
session pushing off. Agent hooks name the pinned binary in full, so they work even when an
agent's PATH does not hold the tools environment.

```bash
arh sessions -n N                           # checkpoints, with agent, model and tokens
entire checkpoint explain <id>              # the session itself
entire session tokens <session-id>          # token use of one session
```

The conclusion receipt (`metadata/conclusions.jsonl`) records the checkpoint ids and the model
each session ran: evidence the harness configuration alone does not give. Transcripts can hold host
paths and data excerpts, so check them before you publish a repository.

## gitleaks: credential rules ARH does not maintain

`secret_scanner = auto` applies gitleaks's rules on top of the built-in patterns, for `arh ask`,
`arh delegate`, dispatch briefs and session logs, and `arh memory add`. **Both are
needed.** On 2026-10-30, gitleaks 8.30.1 missed Anthropic, OpenAI, AWS, Google and Hugging Face key
shapes, assigned passwords and a lone private-key header that the built-in patterns catch, while it
alone caught a Slack webhook URL. `secret_scanner = gitleaks` refuses to run without gitleaks;
`builtin` never calls it.

## basic-memory: searching findings

`arh memory add` writes each finding of a concluded iteration as a Markdown file with YAML front
matter under `knowledge/`, then reindexes. `arh memory search QUERY` hands the query to
basic-memory. Its configuration and index stay in the project (`BASIC_MEMORY_CONFIG_DIR =
.arh/basic-memory`), and `disable_permalinks` and `ensure_frontmatter_on_sync = false` keep it from
rewriting a finding. The first index downloads a small embedding model. basic-memory also serves
the findings to any MCP-capable agent (`bm mcp`). Another Markdown knowledge tool can take its
place: `memory_search_cmd = <command with {query} and {dir}>`.

## Resume after a usage limit

None of the tools above handles a provider's usage limit, so `arh dispatch` does it. A controller
that exits before it hands back, with a usage-limit message in its output, is continued:

1. **`fallback`** (default): it continues at once on `iteration_controller_fallback`, for example a
   second account of the same harness or another family. It waits only when both are at their limit.
2. **`wait`**: it continues on the same harness when the limit lifts. The stated reset is an upper
   bound, not a schedule, so ARH probes again after `dispatch_limit_backoff` (30 min) at the latest.
3. It restarts at most `dispatch_max_resumes` times that did work. A probe that meets the limit at
   once (no model turn) does not count; `dispatch_limit_max_wait` (24 h) bounds the waiting instead.
   After that, the dispatch ends with the controller's exit code.

The continuation also gets the earlier session's last `dispatch_resume_tail` steps (30: what it said
and which commands it ran) and is told not to open earlier transcripts, so it continues from the
project's state and that tail instead of re-reading the whole earlier conversation.

**Parking.** A controller polling `arh wait` costs a model turn per poll, and the turn re-reads the
whole conversation (one iteration spent 162 M tokens waiting on a GPU queue). After a detached
submission, `arh dispatch park -n N --summary TEXT` ends its session; the supervisor checks every
`dispatch_park_poll` seconds (300) and starts a fresh session, with the note and the last steps, when
no submission or review of N runs, when a message arrives, or after `dispatch_park_max_hours` (168).
`arh dispatch message -n N TEXT` is the main controller's way in: it wakes a parked controller, and a
running one's next `arh wait` prints it and exits 4. Wakes do not count against `dispatch_max_resumes`.

**Per iteration.** `arh claim --worker H --reviewer H --orchestrator H --on-limit fallback|wait|stop`
(also `--worker-fallback`, `--reviewer-fallback`, `--set KEY=VALUE`) writes `iterationN/harnesses.md`,
whose keys override `.arh/config/harnesses.md` for that iteration only; unset roles use the project's.
`arh roles -n N` shows each role and where it comes from, and changes it later. The iteration's
settings are part of its review terms: changed after the claim, `arh ask` asks for `--terms-changed`.

The continuation is a **fresh session** of the controller harness. It gets the brief, a current
`arh context -n N`, and a preamble telling it to check `arh status` first and not redo recorded
steps. That works for any harness, because the state is in the project. It is also usually cheaper
than reloading a long conversation whose prompt cache has expired. When a harness defines
`harness_<name>_resume_cmd` (placeholders `{prompt}`, `{session_id}`; e.g. `claude -p {prompt}
--resume {session_id}`) and Entire names exactly one session for the attempt, the harness resumes
its own conversation instead. Entire's own `entire session resume` is not used: it checks out a
branch, which would disturb other sessions sharing the working tree.

The supervisor keeps the lease and the dispatch lock throughout, so no other session can step in.
`arh dispatch status` shows `paused until <time>`. Every restart is in `run.json` (`restarts[]`:
time, provider line, harness, wait, mode) and in the iteration's notes.

**Reboots.** `arh dispatch tick` restarts the supervisor of any dispatch whose supervisor died
before its controller handed back. It calls no model. Run it from cron:

```text
*/15 * * * * ARH_PROJECT=<study> <arh>/bin/arh dispatch tick >/dev/null 2>&1
```

**Reviews and delegations.** `arh ask --wait-on-limit` probes again every `ask_limit_backoff`
(30 min) for up to `ask_limit_max_wait` (6 h) when no verifier is available, and a failed probe
spends no round. `arh delegate` exits 75 when the delegated harness is at its limit.

## Harness logins under a fresh home

`arh replicate` (and `arh dispatch` with `dispatch_home = fresh`) run agents with a fresh home
holding only the login files in `fresh_home_files`. Checked with real logins: Claude Code and
Codex. OpenCode started and reached its provider but could not be confirmed (the account was out
of credits); the Gemini CLI entry is untested. A fresh home also hides a harness's user-level
settings, so pin the model in the harness command template.
