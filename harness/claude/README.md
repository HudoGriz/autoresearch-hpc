# Claude Code

`harness/install.sh` copies `skills/` into `.claude/skills/` and symlinks
`CLAUDE.md` to `AGENTS.md`. The skills then appear as `/iterate`, `/verify`,
`/cross-check` and `/ledger`.

Optional — put `bin/` on PATH for every session in the project, in
`.claude/settings.json`:

```json
{
  "env": { "PATH": "${PWD}/../autoresearch-hpc/bin:${PATH}" },
  "permissions": {
    "allow": ["Bash(arh:*)", "Bash(arh-*:*)", "Bash(sbatch:*)", "Bash(squeue:*)"]
  }
}
```
