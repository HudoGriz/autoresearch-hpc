# Harness wiring

One source of truth — `AGENTS.md` at the repo root — is served to each harness
in its own idiomatic form. These files point at the contract rather than
restate it.

Install into a project with:

```bash
./harness/install.sh <project-dir> [harness...]
```

| harness | reads | this directory provides |
|---|---|---|
| Claude Code | `CLAUDE.md`, `.claude/skills/` | symlink to `AGENTS.md`; skills copied in |
| Codex CLI | `AGENTS.md`, `.codex/config.toml` | profile with the protocol approval posture |
| OpenCode | `AGENTS.md`, `opencode.json` | agent definitions per cross-check role |
| Cursor / Copilot | `AGENTS.md` | nothing extra needed |

For reviews, `claude/review.sh` and `codex/review.sh` wrap the CLIs so `arh ask`
records token usage (`{usage}` in the command template; see `config/harnesses.md`).
Running producer sessions unattended is covered in
[`docs/headless.md`](../docs/headless.md).

Adding a harness means keys in `.arh/config/harnesses.md`
(`harness_<n>_cmd`, `harness_<n>_family`, and the name in `harnesses`) plus any
native config here. Use `arh doctor` to check the configured producer/verifier
families and installed CLIs.
