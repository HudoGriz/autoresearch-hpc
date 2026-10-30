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
| [basic-memory](https://github.com/basicmachines-co/basic-memory) 0.23.2: `arh memory search` over `knowledge/` | on | — | `scripts/setup-tools.sh` (PyPI, with uv) | `memory_search_cmd = <another tool's command>` |
| [Ponytail](https://github.com/DietrichGebert/ponytail): coding guidance, named by `arh context` | on | — | vendored in `skills/ponytail/` | `coding_skill = off` |
| Resume after a usage limit (`arh dispatch`) | `fallback` | `orchestration = per-iteration` | ARH | `dispatch_on_limit = stop` |
| Restart after a reboot (`arh dispatch tick`) | when cron runs it | cron or `scrontab` | ARH | do not schedule it |
| `arh ask --wait-on-limit` | per call | — | ARH | leave the flag out |
| Secret scan of everything sent to a provider | on | — | ARH | `secret_scan = off` (with a recorded reason) |
| External research generators (`arh evoke`: Biomni, AI Scientist v2, Agent Laboratory) | **off** | each tool's own install and API keys | the site ([external-generators.md](external-generators.md)) | — (`generator_<tool>_enabled = true` and `--allow-external` per call turn one on) |

The generators stay off: each needs its own model keys and a multi-gigabyte environment, runs its
own code and sends project content to its provider.

### Installing

`arh init --bootstrap` builds both pinned environments and enables the record:

```bash
arh init /shared/my-study --bootstrap
```

For an existing project:

```bash
scripts/setup-tools.sh <study>        # Entire, gitleaks, uv, basic-memory: <tools_dir>/<key>, locked
scripts/enable-record.sh <study>      # git init + templates/gitignore, Entire hooks, basic-memory index
```

The tools are separate from the host Nextflow environment, so adding or upgrading one never
touches the environment that runs workflows. There is no conda solve: Entire, gitleaks and
[uv](https://github.com/astral-sh/uv) are single release binaries checked against the sha256 in
`config/dependencies.json`, and uv installs basic-memory into a virtual environment with a
uv-managed Python. The build writes `.arh/tools-pip.lock` (`uv pip freeze`) and later builds
install exactly that lock; it also writes `tools_prefix` in `site.md`. `arh` puts the tools
**last** on PATH, so a site's own copy of a tool wins.

Where they go: `tools_dir` in `site.md`, else `$ARH_ENV_CACHE/tools` (built once and shared
between projects), else `.arh/envs/tools`. The tools run where `arh` runs, never in a job, so on a
slow shared filesystem (CephFS, NFS) point `tools_dir` at a node-local disk:

```text
tools_dir = /var/tmp/arh-tools-$USER
```

A cold build there takes about 15 s (about 6 min on CephFS; the earlier micromamba build took over
25 min). If the tools are missing (a new login node, a cleaned `/var/tmp`), `arh doctor` says so; rerun
`scripts/setup-tools.sh`. On a platform with no pinned builds (not Linux x86-64 or arm64), install
the tools yourself or switch them off.

## Git record

`templates/gitignore` ignores everything except the record: the Markdown files, `rules/`,
`skills/`, `knowledge/`, `.arh/config/` and the locks, and in each iteration the pre-declaration,
claims, freezes, reviews, scripts, resources, metadata (not Nextflow work) and the report. Results,
work directories, environments, images and caches stay out. Any single file over
`git_max_file_bytes` (2 MB) is left out too, and named in `.git/info/exclude`.

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
`arh delegate`, `arh evoke`, dispatch briefs and session logs, and `arh memory add`. **Both are
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
3. It restarts at most `dispatch_max_resumes` times. After that, the dispatch ends with the
   controller's exit code.

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
