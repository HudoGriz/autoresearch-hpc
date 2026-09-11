<p align="center">
  <img src="docs/assets/autoresearch-hpc-banner.webp" alt="AutoResearch HPC — auditable AI-assisted research on HPC" width="100%">
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
  <a href="docs/validation.md">Validation</a>
</p>

---

AutoResearch HPC (`arh`) is a small research-protocol layer for **AI-assisted experimentation on infrastructure you already own**. A coding agent can propose and implement an experiment, while `arh` makes the important boundaries mechanical: claim an iteration, pre-declare it before results exist, execute through the configured HPC stack, preserve failures, request a review from another model family, and write the outcome into an append-only research record.

It is deliberately **not** another scheduler, workflow engine, or autonomous research daemon. Nextflow handles workflow execution and caching; Slurm/PBS/local provide compute; Singularity/Apptainer provides pinned task environments. AutoResearch HPC sits above those pieces and makes the *research process* inspectable.

> **Two layers, one workflow:** **skills** tell an agent *how to conduct the research task*; the **`arh` CLI** enforces the parts that should not depend on an agent remembering the rules.

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
| **2 · Execute** | Run the declared workflow with pinned scientific tooling on the configured compute backend | `arh submit` · `arh run` | scripts · workflow metadata · logs · results |
| **3 · Review & record** | Report the declared quantity, cross-check it, gate the result and update the project record | `arh ask` · `arh gate results` · `arh ledger` | report · cross-check record · `PROGRESS.md` |

The execution path underneath phase 2 is the infrastructure you already know:

```text
Nextflow controller  →  Slurm / PBS / local  →  Singularity / Apptainer tasks
```

The controller stays on the host so it can see the site's scheduler. Scientific dependencies run in the declared task image; shared paths and site policy live in configuration rather than inside the workflow.

## Skills and CLI

Yes — **the workflow can be invoked as a skill**, but the skills and commands are not the same thing.

**Skills are high-level agent playbooks.** They describe how to approach a research action and which checks matter. **`arh` commands are deterministic operations.** They create state, freeze declarations, launch execution, validate gates, and maintain the record.

| Skill / workflow | What the agent is being asked to do | Main `arh` machinery underneath |
|---|---|---|
| **[Iterate](skills/iterate/SKILL.md)** | Run one complete research iteration | `claim` → `new` → `gate predeclare` → `submit/run` → `ask` → `gate results` → `ledger` |
| **[Cross-check](skills/cross-check/SKILL.md)** | Critique an iteration from a defined role | `arh ask --role ...` |
| **[Verify](skills/verify/SKILL.md)** | Re-examine an existing result without rewriting history | `arh verify ...` |
| **[Arms](skills/arms/SKILL.md)** | Track parallel sub-analyses with explicit fates | `arh arm ...` |
| **[Replicate](skills/replicate/SKILL.md)** | Reimplement from a frozen specification, blind to the original code | `arh dag ...` · `arh replicate ...` |
| **[Ledger](skills/ledger/SKILL.md)** | Maintain and check the authoritative research record | `arh ledger render/check` |
| **[Ponytail](skills/ponytail/SKILL.md)** | Coding, debugging, refactoring and dependency choices | coding guidance; not a protocol gate |

For **Claude Code**, `harness/install.sh` copies the skills into `.claude/skills/`, where they appear as skills such as `/iterate`, `/verify`, `/cross-check` and `/ledger`. Other harnesses consume the same project contract and skill material through their adapters. The portable source of truth remains the files in `skills/` and `AGENTS.md`.

That separation is important: an agent may choose to *use the Iterate skill*, but `arh gate predeclare` is what actually refuses a late or altered pre-declaration.

## Quick start

### 1. Initialize a study

```bash
git clone https://github.com/HudoGriz/autoresearch-hpc.git
cd autoresearch-hpc
export PATH="$PWD/bin:$PATH"

arh init /shared/my-study
cd /shared/my-study
arh doctor
```

`arh init` detects Slurm/PBS/local and the available Singularity/Apptainer command. `arh doctor` reports what still needs configuration.

If micromamba is available, bootstrap the host-side Nextflow environment during initialization:

```bash
arh init /shared/my-study --bootstrap \
  --micromamba "$(command -v micromamba)" \
  --runtime /shared/images/runtime.sif
```

Project state lives under `.arh/`:

```text
.arh/config/site.md        scheduler, resources, runtime and shared paths
.arh/config/project.md     immutable inputs and standing project rules
.arh/config/harnesses.md   producer / verifier harnesses and model families
```

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

`PROGRESS.md` is the authoritative project state. The goal is that a project can be resumed cold from what is on disk rather than from an old chat transcript.

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
│       ├── results/  logs/
│       └── CROSSCHECK_*.md
└── verification/                    re-examinations of existing results
```

Failed attempts, nulls, killed controls and superseded conclusions stay visible. A correction becomes a **new iteration**; the old evidence is not rewritten to make the history cleaner.

## Beyond the basic loop

The top-level diagram above is a **research loop**, not the discovery DAG. `arh dag` is an advanced feature used when a load-bearing result needs its actual dependency path reconstructed from inputs to claim.

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

AutoResearch HPC is **experimental and pre-1.0**. The current validation baseline passes **137 core checks and 31 boundary regressions**, including real Slurm success/failure, native cache reuse and an immutable-input container probe.

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
| **HPC execution** | [Nextflow, schedulers and containers](docs/hpc-execution.md) |
| **Skills & model budget** | [Skills, harnesses and bounded review](docs/skills-and-token-budget.md) |
| **Validation** | [Tested behavior and limitations](docs/validation.md) |
| **Migration / hardening** | [Implementation notes](docs/migration-hardening.md) |
| **Positioning** | [What this project is — and is not](docs/positioning.md) |
| **Contributing** | [CONTRIBUTING.md](CONTRIBUTING.md) |

## Built on existing work

AutoResearch HPC is an independent project. It builds on ideas and infrastructure from:

- **[Nextflow](https://www.nextflow.io/)** — workflow execution, scheduling and caching.
- **[Ponytail](https://github.com/DietrichGebert/ponytail)** — default coding guidance.
- **[ARIS](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep)** — adapted adversarial review guidance.
- **[autoresearch](https://github.com/karpathy/autoresearch)** — inspiration for understandable agent-driven experimentation.

## License

MIT. See [LICENSE](LICENSE). Citation metadata is available in [CITATION.cff](CITATION.cff).
