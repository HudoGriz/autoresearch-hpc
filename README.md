<div align="center">

# AutoResearch HPC

**AI research on your cluster. Every experiment leaves a record.**

Multiple agent harnesses · Nextflow execution · Singularity tasks · Auditable research

[![Tests](https://github.com/HudoGriz/autoresearch-hpc/actions/workflows/test.yml/badge.svg)](https://github.com/HudoGriz/autoresearch-hpc/actions/workflows/test.yml)
[![Status](https://img.shields.io/badge/status-experimental-orange)](docs/validation.md)
[![Protocol](https://img.shields.io/badge/protocol-0.1.0-blue)](PROTOCOL.md)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

[Quick start](#quick-start) · [Skills we use](#skills-we-use) · [How it works](#how-it-works) · [HPC setup](docs/hpc-execution.md) · [Validation](docs/validation.md) · [Contributing](CONTRIBUTING.md)

</div>

Give your coding agent a research question, a declared experiment and access to
your existing compute cluster. AutoResearch HPC provides the protocol and CLI
for running that work as an auditable loop: freeze the plan, execute the
workflow, preserve the outcome and request a review from another model family.

The agent works through the `dl` CLI and portable Markdown instructions.
Nextflow handles scheduling and caching. Singularity runs scientific tasks.
You keep the question, controls, failed attempts and review together.

> **Experimental, pre-1.0.** Local and real Slurm execution have been exercised.
> Review verdicts are evidence to assess; scientific claims still need independent
> validation. See [tested behavior and limitations](docs/validation.md).

## Why AutoResearch HPC?

| Capability | What you get |
|---|---|
| **Use your cluster** | A host Nextflow controller with access to Slurm; Singularity on compute nodes |
| **Choose your harness** | Portable instructions and configurable Claude Code, Codex and OpenCode integrations |
| **Declare before running** | Atomic iteration claims and a hash-frozen experiment plan |
| **Keep the evidence** | Iteration-owned results, execution traces, run receipts and review records |
| **Spend model calls deliberately** | Deterministic status/context, bounded reviews and reuse of unchanged eligible reviews |
| **Preserve corrections** | Append-only iterations retain failed attempts and superseded conclusions |

## Skills we use

**Ponytail is the default coding skill. ARIS informs the adversarial review.**
Both are pinned to upstream commits with MIT attribution; the research-loop
skills are maintained in this repository.

| Skill | Source | When it is used |
|---|---|---|
| **[Ponytail](skills/ponytail/SKILL.md)** | [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) | **Default for coding**, debugging, refactoring and dependency choices: reuse existing solutions, avoid unnecessary code |
| **[ARIS review rubric](skills/cross-check/roles/adversary.md)** | [Auto-Research-In-Sleep](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep) | Adapted guidance for `dl ask --role adversary`; challenge assumptions, evidence and claims |
| **[Iterate](skills/iterate/SKILL.md)** | AutoResearch HPC | Follow the declare → execute → review → record research loop |
| **[Cross-check](skills/cross-check/SKILL.md)** | AutoResearch HPC | Request review from another model family with a defined role |
| **[Verify](skills/verify/SKILL.md)** | AutoResearch HPC | Re-examine an existing result against a declared success criterion |
| **[Arms](skills/arms/SKILL.md)** | AutoResearch HPC | Organize separately tracked sub-analyses within an iteration |
| **[Replicate](skills/replicate/SKILL.md)** | AutoResearch HPC | Reimplement from a frozen specification when replication is requested |
| **[Ledger](skills/ledger/SKILL.md)** | AutoResearch HPC | Maintain the record and check it against artifacts on disk |

Ponytail activates through the agent contract; it is not a mandatory runtime
hook. It never overrides requested work, scientific controls or validation.
The full ARIS workflow and Ponytail's auxiliary plugins are not bundled.
Other skills are available for the relevant task rather than loaded on every
turn. [Installation, upstream pins and token-budget scope →](docs/skills-and-token-budget.md)

## How it works

```mermaid
flowchart LR
    A[Research question] --> B[Claim iteration]
    B --> C[Declare and freeze plan]
    C --> D[Nextflow on host]
    D --> E[Slurm or local executor]
    E --> F[Singularity tasks]
    F --> G[Results and evidence]
    G --> H[Foreign-family review]
    H --> I[Gate and ledger]
    I --> A
```

**The controller stays on the host.** Its versioned micromamba environment
provides Nextflow and Java while preserving the site's scheduler access.
Scientific dependencies run inside the configured task container, optionally
using a read-only mounted task environment. Shared paths and site policy are
configured in Markdown. [Execution details →](docs/hpc-execution.md)

## Quick start

You need Linux, Bash/basic shell tools, Python for bootstrap, a micromamba binary
and Singularity (or an Apptainer installation providing the `singularity` command).
Cluster execution also needs Slurm clients and shared storage. Model review
requires an authenticated verifier CLI from a different family than the producer.

### 1. Install and configure

```bash
git clone https://github.com/HudoGriz/autoresearch-hpc.git
cd autoresearch-hpc
export PATH="$PWD/bin:$PATH"

dl init /shared/my-study
scripts/setup-nextflow.sh /shared/my-study /absolute/path/to/micromamba
scripts/setup-runtime.sh /shared/my-study /shared/images/runtime.sif
```

Stage a compatible runtime SIF first; the tested bootstrap image is
`docker://mambaorg/micromamba:2.8.1`. Setup records its local digest and resolved
package lists. Add your domain dependencies before using it for scientific work.
See the [complete HPC setup guide](docs/hpc-execution.md).

```bash
cd /shared/my-study
# Edit .dl/config/site.md: scheduler, partition, account and resources.
# Edit .dl/config/project.md: immutable inputs and standing rules.
# Edit .dl/config/harnesses.md: producer and foreign-family verifier.
dl doctor
```

### 2. Run a declared experiment

```bash
N=$(dl claim -t "Does the proposed method improve the declared metric?")
dl new -n "$N"
# Complete every section of iterations/iterationN/README.md first.
dl gate predeclare -n "$N"

# Write your native Nextflow workflow under this iteration's scripts/.
dl submit "iterations/iteration${N}/scripts/experiment.nf" -n experiment

# Write results/report/iterationN_report.md, including controls and limits.
dl ask --role adversary -n "$N"
dl gate results -n "$N"
dl ledger render && dl ledger check
```

Native workflows can use `--resume` to reuse unchanged tasks. Legacy `.sh`
submission is supported as a migration adapter and is deliberately not cached.
Complete results before review; modifying reviewed evidence invalidates that review.

### 3. Work with your agent

From the source checkout, install optional harness wiring:

```bash
harness/install.sh /shared/my-study claude codex opencode
```

Then open your agent in the study and ask:

> Read PROGRESS.md and AGENTS.md. Propose one experiment for this question,
> declare its metric and negative controls, and follow the discovery loop.
> Use the configured Nextflow/Singularity runtime and keep the evidence in its iteration.

The instructions guide the agent; you supply the scientific question, data and
site configuration. There is no separate always-running research daemon.

## Keep model calls focused

**Ponytail is on by default for coding.** Its pinned core skill guides agents to
reuse existing code and tools before adding implementation. Load it once per
coding session; keep required controls and validation. [Skills and budget details →](docs/skills-and-token-budget.md)

Execution, polling, cache reuse, ledger checks and `dl context -n N` use no LLM.
The default review policy limits submitted prompt bytes to **24,000**, captured
output to **8,000 bytes**, and attempts to **two per iteration**. Further reviews
require a concrete unresolved issue; unchanged eligible reviews are reused.

These are operational bounds, not exact token or billing caps. Harness system
prompts and internal work can add cost. External model services receive the
context supplied to them; local compute does not imply air-gapped inference.

## Your research record

```text
my-study/
├── PROGRESS.md                  # resume point and ledger
├── AGENTS.md                    # agent contract
├── .dl/config/                  # site, study and harness settings
├── rules/                       # standing research rules
├── iterations/iterationN/
│   ├── CLAIM.json
│   ├── README.md                # declared before results
│   ├── PREDECLARATION.sha256
│   ├── scripts/  resources/  metadata/
│   ├── results/  logs/
│   └── CROSSCHECK_*.md          # hash-bound foreign reviews
└── verification/                # re-examination of existing results
```

| Command | Purpose |
|---|---|
| `dl status` / `dl next` | Inspect state and the next protocol action |
| `dl context -n N` | Generate a compact deterministic handoff |
| `dl run IMAGE -- CMD` | Execute a tool in a declared container |
| `dl guard PATH` | Check a proposed output path |
| `dl verify new OBJECT` | Start a verification of an existing result |
| `dl dag init -n N` | Describe the path from inputs to conclusions |
| `dl replicate --help` | Explore specification-based replication |

Run `dl --help` for the full CLI. Blind review is a cooperative protocol;
separate permissions are needed when access must be technically prevented.

## Validation and development

The local validation baseline passed **137 core checks and 31 boundary
regressions**, with real Slurm success/failure, native cache reuse and an
immutable-input container probe. A bounded Claude review returned **QUALIFIED**;
five focused follow-up probes passed. [Evidence scope and retained limits →](docs/validation.md)

```bash
export DL_TEST_SITE=/absolute/path/to/configured/local/site.md
test/run_tests.sh
python3 test/test_hardening.py
```

CI provisions the Linux execution boundary and runs integration tests, shell
lint and schema validation. See [CONTRIBUTING.md](CONTRIBUTING.md) for setup.

## Built on existing work

- **[Ponytail](https://github.com/DietrichGebert/ponytail):** default coding guidance; pinned core skill with MIT attribution.
- **[Nextflow](https://www.nextflow.io/):** execution, scheduling and caching.
- **[ARIS](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep):** a
  pinned, adapted adversarial review rubric. The full ARIS autonomous workflow
  is not bundled; attribution and license are in [third_party/aris](third_party/aris).
- **[autoresearch](https://github.com/karpathy/autoresearch):** inspiration for
  making agent-driven experimentation understandable and accessible.

AutoResearch HPC is an independent project, not an official Karpathy or ARIS
release. Its `dl` CLI implements the discovery-loop protocol.

## Documentation

[HPC setup](docs/hpc-execution.md) · [Protocol](PROTOCOL.md) ·
[Agent contract](AGENTS.md) · [Validation](docs/validation.md) ·
[Migration](docs/migration-hardening.md) · [Framework review](docs/framework-review.md) ·
[Positioning](docs/positioning.md) · [Proposals](docs/proposals.md)

## License

[MIT](LICENSE). Citation metadata is available in [CITATION.cff](CITATION.cff).
