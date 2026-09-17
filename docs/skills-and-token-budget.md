# Skills and token budget

## Default: Ponytail for coding

[Ponytail](https://github.com/DietrichGebert/ponytail) is enabled by default in
full mode for coding, debugging, refactoring and dependency decisions. Its core
skill is pinned in `skills/ponytail/SKILL.md`; attribution and hashes live under
`third_party/ponytail/`.

`arh init` supplies the shared skills and default agent policy. For an older
study, run `harness/install.sh /path/to/study` after migrating it to the `.arh/`
layout. Research controls, validation and explicit user requests always take
precedence over coding-style preferences.

Default activation is an instruction in `AGENTS.md`, not a mandatory runtime
hook. Claude reads it through `CLAUDE.md`; other supported harnesses use
`AGENTS.md`. The full Ponytail plugin stack is not a runtime dependency.

## What is integrated?

| Source | Integration |
|---|---|
| Ponytail | Pinned core coding guidance and default activation policy |
| ARIS | Adapted adversarial-review guidance; full autonomous workflow is not bundled |
| This repository | iterate, arms, verify, cross-check, replicate, ledger and evoke skills |
| Karpathy autoresearch | Inspiration and attribution; no imported runtime |
| Nextflow / Singularity/Apptainer | Execution infrastructure, not skill repositories |

The Evoke skill selects among optional, independently installed specialist
generators. It does not install them or promote their output to evidence. See
[External generators](external-generators.md).

## Deterministic budget controls

`arh ask` defaults to bounded input/output bytes, elapsed time and attempts per
iteration. Failed attempts consume a round, except provider refusals (quota,
rate limit, authentication, content policy), which are recorded but not counted. Concurrent
reviews are locked and an unchanged eligible review is reused. `arh context` supplies a compact deterministic
handoff, while execution, polling and status do not call a model.

These controls do not cap provider billing, system prompts or hidden harness
reasoning. Token savings for AutoResearch HPC have not been empirically measured.

## What the bounds do not cover

The bounds apply to **reviews only**. The producing agent's session is not bounded
by `arh`: its turns, tool calls and tokens are whatever the harness spends. In a
replication benchmark on a Slurm cluster, single producer sessions used roughly 3 to
9 million input tokens (mostly cached), and two parallel Claude Opus producer
sessions reached a subscription session limit within 6 to 7 minutes, about USD 1.7
each at API prices. Budget producer sessions with the harness's own controls.

To see what a review cost, put `{usage}` in the verifier's command template. The
wrappers `harness/claude/review.sh` and `harness/codex/review.sh` write token counts
(and Claude's reported cost) there, and `arh ask` stores them as `usage` in the
review record.
