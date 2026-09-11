<div align="center">

# AutoResearch HPC

**Auditable AI-assisted research on your existing compute cluster.**

Multiple agent harnesses · Nextflow execution · Singularity/Apptainer tasks · Reviewable evidence

[![Tests](https://github.com/HudoGriz/autoresearch-hpc/actions/workflows/test.yml/badge.svg)](https://github.com/HudoGriz/autoresearch-hpc/actions/workflows/test.yml)
[![Status](https://img.shields.io/badge/status-experimental-orange)](docs/validation.md)
[![Protocol](https://img.shields.io/badge/protocol-0.2.0-blue)](PROTOCOL.md)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

[Quick start](#quick-start) · [How it works](#how-it-works) · [Skills](#skills-we-use) · [HPC setup](docs/hpc-execution.md) · [Validation](docs/validation.md) · [Contributing](CONTRIBUTING.md)

</div>

Give a coding agent a research question, a declared experiment and access to your
existing compute cluster. AutoResearch HPC (`arh`) provides the protocol and CLI
for an auditable loop: declare and freeze the plan, execute it through Nextflow,
preserve outcomes and failures, request a review from another model family, and
keep the evidence in an append-only record.

Nextflow handles scheduling and caching. Slurm/PBS/local provide execution.
Singularity/Apptainer runs scientific tasks. The framework does **not** treat
model agreement as scientific truth: cross-check verdicts are evidence to assess,
and claims still require appropriate independent scientific validation.

> **Experimental, pre-1.0.** Local and real Slurm execution have been exercised.
> See [tested behavior and limitations](docs/validation.md).

## Why AutoResearch HPC?

| Capability | What you get |
|---|---|
| **Use your cluster** | Host Nextflow controller with Slurm/PBS/local execution and pinned task containers |
| **Choose your harness** | Portable instructions and configurable Claude Code, Codex and OpenCode integrations |
| **Declare before running** | Atomic iteration claims and cryptographically frozen experimental plans |
| **Keep the evidence** | Iteration-owned results, execution traces, receipts and review records |
| **Preserve failures** | Append-only iterations retain failed attempts, nulls and superseded conclusions |
| **Spend model calls deliberately** | Deterministic status/context and bounded, reusable cross-checks |

## How it works

```mermaid
flowchart LR
    A[Research question] --> B[Claim iteration]
    B --> C[Declare + freeze]
    C --> D[Nextflow controller]
    D --> E[Slurm / PBS / local]
    E --> F[Singularity / Apptainer tasks]
    F --> G[Results + evidence]
    G --> H[Foreign-family review]
    H --> I[Gate + ledger]
    I --> A
```

The controller stays on the host so it sees the site's scheduler. Scientific
dependencies run inside the configured task image. Shared paths and site policy
are configuration, not hard-coded workflow behavior. [Execution details →](docs/hpc-execution.md)

## Quick start

Requirements are Linux, Bash/basic shell tools and Python. HPC execution needs
the scheduler clients and shared storage. A pinned host Nextflow environment is
built with micromamba; scientific tasks use a staged SIF. Model review requires
an authenticated verifier CLI from a different configured model family.

### 1. Initialize

```bash
git clone https://github.com/HudoGriz/autoresearch-hpc.git
cd autoresearch-hpc
export PATH="$PWD/bin:$PATH"

arh init /shared/my-study
cd /shared/my-study
arh doctor
```

`arh init` now detects Slurm/PBS/local and the available Singularity/Apptainer
command. `arh doctor` reports exactly what remains to configure instead of making
you guess which setup step failed.

If micromamba is already available, the host controller can be prepared during
initialization:

```bash
arh init /shared/my-study --bootstrap --micromamba "$(command -v micromamba)"
```

To configure the task runtime at the same time, add:

```bash
arh init /shared/my-study --bootstrap \
  --micromamba "$(command -v micromamba)" \
  --runtime /shared/images/runtime.sif
```

For an existing initialized study, the equivalent setup helpers remain:

```bash
scripts/setup-nextflow.sh /shared/my-study /absolute/path/to/micromamba
scripts/setup-runtime.sh /shared/my-study /shared/images/runtime.sif
```

Project state lives under `.arh/`. Edit `.arh/config/site.md` for scheduler and
resources, `.arh/config/project.md` for immutable inputs and standing rules, and
`.arh/config/harnesses.md` for producer/verifier harnesses. Then rerun:

```bash
arh doctor
```

### 2. Run a declared experiment

```bash
N=$(arh claim -t "Does the proposed method improve the declared metric?")
arh new -n "$N"
# Complete every section of iterations/iterationN/README.md first.
arh gate predeclare -n "$N"

arh submit "iterations/iteration${N}/scripts/experiment.nf" -n experiment

# Write results/report/iterationN_report.md, including controls and limits.
arh ask --role adversary -n "$N"
arh gate results -n "$N"
arh ledger render && arh ledger check
```

Native workflows can use `--resume`. Legacy `.sh` submission remains a migration
adapter and is deliberately not cached. Modifying reviewed evidence invalidates
the corresponding review.

### 3. Work with your agent

Optional harness wiring:

```bash
harness/install.sh /shared/my-study claude codex opencode
```

Then ask the agent to read `PROGRESS.md` and `AGENTS.md`, propose one experiment,
declare its metric and negative controls, and follow the protocol. There is no
always-running research daemon.

## Skills we use

**Ponytail is the default coding skill. ARIS informs adversarial review.** The
research-loop skills are maintained here.

| Skill | Use |
|---|---|
| **[Ponytail](skills/ponytail/SKILL.md)** | Coding, debugging, refactoring and dependency choices |
| **[ARIS review rubric](skills/cross-check/roles/adversary.md)** | Guidance for `arh ask --role adversary` |
| **[Iterate](skills/iterate/SKILL.md)** | Declare → execute → review → record |
| **[Cross-check](skills/cross-check/SKILL.md)** | Defined-role review from another model family |
| **[Verify](skills/verify/SKILL.md)** | Re-examine an existing result |
| **[Arms](skills/arms/SKILL.md)** | Separately tracked sub-analyses |
| **[Replicate](skills/replicate/SKILL.md)** | Reimplement from a frozen specification |
| **[Ledger](skills/ledger/SKILL.md)** | Maintain and check the research record |

[Installation, upstream pins and token-budget scope →](docs/skills-and-token-budget.md)

## Keep model calls focused

Execution, polling, cache reuse, ledger checks and `arh context -n N` use no LLM.
The default review policy limits submitted prompt bytes to 24,000, captured
output to 8,000 bytes, and attempts to two per iteration. These are operational
bounds, not exact provider token or billing caps.

## Your research record

```text
my-study/
├── PROGRESS.md                  # resume point and ledger
├── AGENTS.md                    # agent contract
├── .arh/config/                 # site, study and harness settings
├── rules/                       # standing research rules
├── iterations/iterationN/
│   ├── CLAIM.json
│   ├── README.md                # declared before results
│   ├── PREDECLARATION.sha256
│   ├── scripts/  resources/  metadata/
│   ├── results/  logs/
│   └── CROSSCHECK_*.md
└── verification/
```

| Command | Purpose |
|---|---|
| `arh status` / `arh next` | Inspect state and the next protocol action |
| `arh context -n N` | Generate a deterministic handoff |
| `arh run IMAGE -- CMD` | Execute a tool in a declared container |
| `arh guard PATH` | Check a proposed output path |
| `arh verify new OBJECT` | Start verification of an existing result |
| `arh dag init -n N` | Describe the path from inputs to conclusions |
| `arh replicate --help` | Explore specification-based replication |

Run `arh --help` for the full CLI.

## Validation and development

The validation baseline passed **137 core checks and 31 boundary regressions**,
with real Slurm success/failure, native cache reuse and an immutable-input
container probe. [Evidence scope and retained limits →](docs/validation.md)

```bash
export ARH_TEST_SITE=/absolute/path/to/configured/local/site.md
test/run_tests.sh
python3 test/test_hardening.py
```

## Built on existing work

- **[Ponytail](https://github.com/DietrichGebert/ponytail)** — default coding guidance.
- **[Nextflow](https://www.nextflow.io/)** — workflow execution, scheduling and caching.
- **[ARIS](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep)** — adapted adversarial review guidance.
- **[autoresearch](https://github.com/karpathy/autoresearch)** — inspiration for understandable agent-driven experimentation.

AutoResearch HPC is an independent project. Its `arh` CLI implements the
AutoResearch HPC discovery-loop protocol.

## Documentation

[HPC setup](docs/hpc-execution.md) · [Protocol](PROTOCOL.md) · [Agent contract](AGENTS.md) ·
[Validation](docs/validation.md) · [Migration](docs/migration-hardening.md) ·
[Framework review](docs/framework-review.md) · [Positioning](docs/positioning.md)

## License

[MIT](LICENSE). Citation metadata is available in [CITATION.cff](CITATION.cff).
