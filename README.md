<p align="center">
  <img src="docs/assets/banner.png" alt="autoresearch-hpc — auditable AI-assisted research on HPC. An agent pre-declares an experiment (arh claim, arh new, arh gate predeclare), executes it through Nextflow, Slurm/PBS and Apptainer, then reviews and records it: append-only, reproducible, auditable." width="100%">
</p>

<p align="center">
  <a href="https://github.com/HudoGriz/autoresearch-hpc/actions/workflows/test.yml"><img alt="Tests" src="https://github.com/HudoGriz/autoresearch-hpc/actions/workflows/test.yml/badge.svg"></a>
  <a href="docs/validation.md"><img alt="Status: experimental" src="https://img.shields.io/badge/status-experimental-orange"></a>
  <a href="PROTOCOL.md"><img alt="Protocol 0.2.0" src="https://img.shields.io/badge/protocol-0.2.0-blue"></a>
  <a href="LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/license-MIT-green"></a>
</p>

<p align="center">
  <strong>Declare the question. Freeze the plan. Run it on your cluster. Critique the result. Keep the evidence.</strong>
</p>

<p align="center">
  <a href="#quick-start">Quick start</a> ·
  <a href="#the-research-loop">Research loop</a> ·
  <a href="#skills-and-cli">Skills + CLI</a> ·
  <a href="docs/hpc-execution.md">HPC setup</a> ·
  <a href="PROTOCOL.md">Protocol</a> ·
  <a href="docs/validation.md">Validation</a> ·
  <a href="CHANGELOG.md">Changelog</a>
</p>

---

AutoResearch HPC (`arh`) is a small research-protocol layer for **AI-assisted experimentation on infrastructure you already own**. A coding agent can propose and implement an experiment. `arh` makes the important boundaries mechanical:

- claim an iteration;
- pre-declare it before results exist;
- execute it through the configured HPC stack;
- preserve failures;
- have a model from another family review it;
- write the outcome into an append-only research record.

It is deliberately **not** another scheduler, workflow engine or autonomous research daemon. Nextflow handles workflow execution and caching; Slurm/PBS/local provide compute; Singularity/Apptainer provides pinned task environments. AutoResearch HPC sits above those pieces and makes the *research process* inspectable.

> [!NOTE]
> **Two layers, one workflow.** **Skills** tell an agent *how to conduct the research task*; the **`arh` CLI** enforces the parts that should not depend on an agent remembering the rules.

## The research loop

The generic path is intentionally small:

```mermaid
flowchart LR
    Q["Research question"] --> D["1 · Pre-declare"]
    D --> E["2 · Execute"]
    E --> R["3 · Review & record"]
    R -. "next question" .-> Q
```

Each phase has a concrete protocol meaning:

| Phase | What happens | Core interface | Durable evidence |
|---|---|---|---|
| **1 · Pre-declare** | Claim one question, define the estimand, controls, detection limit and acceptance criteria, then freeze the plan | `arh claim` · `arh new` · `arh gate predeclare` | `CLAIM.json` · `README.md` · `PREDECLARATION.sha256` |
| **2 · Execute** | Run the declared workflow with pinned scientific tooling on the configured compute backend | `arh submit` · `arh run` | scripts · workflow metadata · run receipts · logs · results |
| **3 · Review & record** | Report the declared quantity, cross-check it, gate the result and update the project record | `arh ask` · `arh gate results` · `arh ledger` | report · cross-check record · review response · `PROGRESS.md` |

Phase 2 runs on infrastructure you already know:

```text
Nextflow controller  →  Slurm / PBS / local  →  Singularity / Apptainer tasks
```

The controller stays on the host so it can see the site's scheduler. Scientific dependencies run in the declared task image; shared paths and site policy live in configuration rather than inside the workflow.

## Skills and CLI

You can drive the workflow as a **skill**, but skills and commands are not the same thing.

**Skills are high-level agent playbooks.** They describe how to approach a research action and which checks matter. **`arh` commands are deterministic operations.** They create state, freeze declarations, launch execution, validate gates and maintain the record.

| Skill / workflow | What the agent is being asked to do | Main `arh` machinery underneath |
|---|---|---|
| **[Iterate](skills/iterate/SKILL.md)** | Run one complete research iteration | `claim` → `new` → `gate predeclare` → `submit/run` → `ask` → `gate results` → `ledger` |
| **[Cross-check](skills/cross-check/SKILL.md)** | Critique an iteration from a defined role | `arh ask --role ...` |
| **[Verify](skills/verify/SKILL.md)** | Re-examine an existing result without rewriting history | `arh verify ...` |
| **[Arms](skills/arms/SKILL.md)** | Track parallel sub-analyses with explicit fates | `arh arm ...` |
| **[Replicate](skills/replicate/SKILL.md)** | Reimplement from a frozen specification, blind to the original code | `arh dag ...` · `arh replicate ...` |
| **[Ledger](skills/ledger/SKILL.md)** | Maintain and check the authoritative research record | `arh ledger render/check` |
| **[Ponytail](skills/ponytail/SKILL.md)** | Coding, debugging, refactoring and dependency choices | coding guidance; not a protocol gate |

For **Claude Code**, `harness/install.sh` copies the skills into `.claude/skills/`, where they appear as `/iterate`, `/verify`, `/cross-check` and `/ledger`. Other harnesses read the same project contract and skill material through their adapters. The portable source of truth remains `skills/` and `AGENTS.md`.

The separation matters: an agent may choose to *use the Iterate skill*, but it is `arh gate predeclare` that refuses a late or altered pre-declaration.

## Quick start

### 1. Set up

**Easiest: ask your coding agent.** If you use Claude Code, Codex, OpenCode, Cursor, Copilot or another coding agent, give it this repository:

```text
https://github.com/HudoGriz/autoresearch-hpc
```

and ask:

> Set up AutoResearch HPC for this project. Inspect the repository instructions first, detect my scheduler and container runtime, run the automatic bootstrap, configure the harness integration, then run `arh doctor` and resolve the required setup checks. Do not modify the scientific project or data beyond what AutoResearch HPC setup requires.

The repository ships `AGENTS.md`, reusable skills and harness adapters, so the agent can inspect the machine and follow the repository's own setup path. The host bootstrap does **not** require a pre-installed Conda or micromamba environment.

**By hand:**

```bash
git clone https://github.com/HudoGriz/autoresearch-hpc.git   # or: git@github.com:HudoGriz/autoresearch-hpc.git
cd autoresearch-hpc
export PATH="$PWD/bin:$PATH"

arh init /shared/my-study --bootstrap
cd /shared/my-study
arh doctor
```

`arh init` detects Slurm/PBS/local and the available Singularity/Apptainer command. With `--bootstrap`, it also prepares the pinned host-side Nextflow/Python environment. `arh doctor` reports what still needs configuration.

**You do not need to install micromamba yourself.** Micromamba is a standalone executable. AutoResearch HPC first reuses its own pinned project-local copy, then a matching version already on `PATH`; if neither exists it downloads the pinned binary, verifies its SHA-256 checksum, and caches it under `.arh/tools/micromamba/`. It does not run `micromamba shell init` or modify your shell configuration.

If your HPC cannot access GitHub, stage a micromamba binary once and provide it explicitly:

```bash
arh init /shared/my-study --bootstrap \
  --micromamba /shared/tools/micromamba
```

To configure the task runtime at the same time, pull its image once and pass it in:

```bash
singularity pull /shared/images/runtime.sif docker://mambaorg/micromamba:2.8.1

arh init /shared/my-study --bootstrap \
  --runtime /shared/images/runtime.sif
```

Project state lives under `.arh/`:

```text
.arh/config/site.md        scheduler, resources, runtime and shared paths
.arh/config/project.md     immutable inputs and standing project rules
.arh/config/harnesses.md   producer / verifier harnesses and model families
```

> [!TIP]
> `arh` finds the study by walking up from the working directory. Agent harnesses often reset the shell's directory between commands, so `export ARH_PROJECT=/shared/my-study` to make every command resolve the study from anywhere.

### 2. Run one declared experiment

```bash
N=$(arh claim -t "Does the proposed method improve the declared metric?")
arh new -n "$N"

# Complete iterations/iterationN/README.md before any result exists.
arh gate predeclare -n "$N"

arh submit "iterations/iteration${N}/scripts/experiment.nf" -n experiment

# Write results/report/iterationN_report.md.
arh ask --role adversary -n "$N"
arh gate results -n "$N"
arh ledger render && arh ledger check
```

Or hand the workflow to a configured agent and ask it to **use the Iterate skill** for one research question. The skill describes the procedure; the CLI still supplies the enforcement.

### 3. Resume without conversation history

```bash
arh status
arh next
arh context -n N
```

`PROGRESS.md` is the authoritative project state. A project should be resumable cold from what is on disk rather than from an old chat transcript.

## What gets recorded

```text
my-study/
├── PROGRESS.md                      authoritative resume point / ledger
├── AGENTS.md                        harness-agnostic agent contract
├── .arh/config/                     site, project and harness settings
├── rules/                           standing research rules
├── iterations/
│   └── iterationN/
│       ├── CLAIM.json
│       ├── README.md                pre-declaration written before results
│       ├── PREDECLARATION.sha256    frozen declaration hash
│       ├── scripts/  resources/  metadata/
│       ├── results/  logs/          results, run receipts, traces
│       ├── CROSSCHECK_*.md          foreign-family reviews
│       └── REVIEW_RESPONSE.md       what was done about each finding
└── verification/                    re-examinations of existing results
```

Failed attempts, nulls, killed controls and superseded conclusions stay visible. A correction becomes a **new iteration**; the old evidence is not rewritten to make the history cleaner.

## Beyond the basic loop

The diagram above is a **research loop**, not the discovery DAG. `arh dag` is an advanced feature, used when a load-bearing result needs its actual dependency path reconstructed from inputs to claim.

```bash
arh arm new ...             # parallel sub-analysis inside one iteration
arh verify new OBJECT       # re-examine an existing result
arh dag init -n N           # reconstruct the discovery path
arh dag freeze -n N         # freeze the specification
arh replicate run ...       # blind reimplementation from that frozen DAG
```

The protocol treats disagreement between replicators as useful evidence; agreement is not promoted to scientific confirmation by majority vote.

## Why this layer exists

| Existing component | Keep using it for | AutoResearch HPC adds |
|---|---|---|
| **Nextflow** | scheduling, workflow execution, caching | declared iterations and iteration-owned evidence |
| **Slurm / PBS / local** | compute allocation | a portable execution target rather than a new scheduler |
| **Singularity / Apptainer** | scientific environments | pinned task execution tied to the record |
| **Claude / Codex / OpenCode** | implementation and critique | harness-portable rules, bounded review and explicit model-family provenance |

The framework does **not** treat model agreement as scientific truth. Cross-family critique is evidence to assess, not orthogonal validation. Claims still need whatever independent scientific validation their domain requires.

## Validation and boundaries

AutoResearch HPC is **experimental and pre-1.0**. The current baseline passes **137 core checks and 37 boundary regressions**. Earlier validation runs added real Slurm success/failure, native cache reuse and an immutable-input container probe.

It has also been used on a real nine-iteration exome structural-variant study on a Slurm + Singularity cluster. The review, submission and provenance defects that study surfaced are fixed; see the [changelog](CHANGELOG.md).

```bash
export ARH_TEST_SITE=/absolute/path/to/configured/local/site.md
test/run_tests.sh
python3 test/test_hardening.py
```

The protocol is a cooperative research-integrity system, not a hostile-code sandbox or trusted timestamp authority. Local hashes detect later changes; they do not prove temporal priority against an actor controlling the filesystem. External model services receive the context supplied to them, so local/HPC execution does not imply air-gapped inference.

[Read the tested behavior and retained limitations →](docs/validation.md)

## Documentation

| | |
|---|---|
| **Protocol** | [Normative protocol v0.2.0](PROTOCOL.md) |
| **Agent contract** | [AGENTS.md](AGENTS.md) |
| **HPC execution** | [Nextflow, schedulers, containers, receipts and stopping a run](docs/hpc-execution.md) |
| **Skills & model budget** | [Skills, harnesses and bounded review](docs/skills-and-token-budget.md) |
| **Validation** | [Tested behavior and limitations](docs/validation.md) |
| **Migration / hardening** | [`arh migrate` for 0.1 studies, and implementation notes](docs/migration-hardening.md) |
| **Positioning** | [What this project is — and is not](docs/positioning.md) |
| **Changes** | [CHANGELOG.md](CHANGELOG.md) |
| **Contributing** | [CONTRIBUTING.md](CONTRIBUTING.md) |

## Built on existing work

AutoResearch HPC is an independent project. It builds on ideas and infrastructure from:

- **[Nextflow](https://www.nextflow.io/)** — workflow execution, scheduling and caching.
- **[Ponytail](https://github.com/DietrichGebert/ponytail)** — default coding guidance.
- **[ARIS](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep)** — adapted adversarial review guidance.
- **[autoresearch](https://github.com/karpathy/autoresearch)** — inspiration for understandable agent-driven experimentation.

## License

MIT. See [LICENSE](LICENSE). Citation metadata is available in [CITATION.cff](CITATION.cff).
