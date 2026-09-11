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
| This repository | iterate, arms, verify, cross-check, replicate and ledger skills |
| Karpathy autoresearch | Inspiration and attribution; no imported runtime |
| Nextflow / Singularity/Apptainer | Execution infrastructure, not skill repositories |

## Deterministic budget controls

`arh ask` defaults to bounded input/output bytes, elapsed time and attempts per
iteration. Failed attempts consume a round; concurrent reviews are locked and an
unchanged eligible review is reused. `arh context` supplies a compact deterministic
handoff, while execution, polling and status do not call a model.

These controls do not cap provider billing, system prompts or hidden harness
reasoning. Token savings for AutoResearch HPC have not been empirically measured.
