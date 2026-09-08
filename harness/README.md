# Harness wiring

One source of truth — `AGENTS.md` at the repo root — served to each harness in
its own idiomatic form. Nothing here restates the contract; these files only
point at it.

Install into a project with `./harness/install.sh <project-dir> [harness...]`.

| harness | reads | this directory provides |
|---|---|---|
| Claude Code | `CLAUDE.md`, `.claude/skills/` | symlink to `AGENTS.md`; skills copied in |
| Codex CLI | `AGENTS.md`, `.codex/config.toml` | profile with the loop's approval posture |
| OpenCode | `AGENTS.md`, `opencode.json` | agent definitions per cross-check role |
| Cursor / Copilot | `AGENTS.md` | nothing extra needed |

Adding a harness means three keys in `.dl/config/harnesses.md`
(`harness_<n>_cmd`, `harness_<n>_family`, and the name in `harnesses`) plus any
native config here.
