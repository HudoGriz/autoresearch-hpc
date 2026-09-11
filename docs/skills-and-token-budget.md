# Skills and token budget

## Default: Ponytail for coding

[Ponytail](https://github.com/DietrichGebert/ponytail) is enabled by default in
full mode for coding, debugging, refactoring and dependency decisions. Its core
skill is vendored unchanged at `skills/ponytail/SKILL.md`, pinned to commit
`356918eba965ee1eac64bd3a7f0dd02108350de5`. The license and content hashes are
in `third_party/ponytail/`.

`dl init` supplies the shared skills and default policy. For an older study,
run `harness/install.sh /path/to/study` from the framework checkout. The installer
adds the Ponytail policy without replacing the rest of AGENTS.md, copies shared
skills and installs the selected harness configuration (which replaces that
harness's existing configuration file). Choose only the harnesses you use.

Agents read the skill once when starting coding work. Its reuse-first guidance
stays active unless the user says “stop ponytail” or “normal mode”. Research
controls, validation and explicit user requests take precedence over brevity.
Non-coding scientific reports still receive the detail the protocol requires.

Default activation is an instruction in AGENTS.md, not an enforced lifecycle
hook. Claude reads it through CLAUDE.md; other supported harnesses use AGENTS.md.
We do not install Ponytail's Node hooks, MCP service or auxiliary audit/debt
skills. No extra model call is made merely to select or load this skill.

## What is actually integrated?

| Source | Integration |
|---|---|
| Ponytail | Exact pinned core coding skill, default activation policy |
| ARIS | Pinned adapted adversarial review rubric; full autonomous workflow is not bundled |
| This repository | iterate, arms, verify, cross-check, replicate and ledger skills |
| Karpathy autoresearch | Inspiration and attribution; no imported skill or runtime code |
| Nextflow / Singularity | Execution infrastructure, not skill repositories |

Additional skills available in a developer's personal environment are not
implicitly dependencies of this repository.

## Deterministic budget controls

`dl ask` defaults to 24,000 input bytes, 8,000 captured output bytes, 180 seconds
and two attempts per iteration. Failed attempts consume a round. Concurrent
reviews are locked; unchanged eligible reviews are reused. A further review
needs a note naming the concrete unresolved issue. `dl context` supplies a
compact handoff, while execution, polling and status do not call a model.

These limits apply to `dl ask`, not every interactive agent session or the
separate `dl replicate` command. They do not cap provider billing or hidden
harness reasoning. Upstream Ponytail benchmarks describe other workloads and
models; token savings for AutoResearch HPC have not been measured.
