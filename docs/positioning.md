# Positioning proposal

**Auditable AI-assisted research on your existing HPC cluster.**

Target research software engineers and labs that already operate Slurm and
Singularity, need to compare hypotheses across agent harnesses, and must explain
how a result was produced. Lead with a reviewable research record: the frozen
question, execution trace, failures, controls and independent-family critique.

The differentiator is the combination of a research protocol with existing HPC
execution and bounded model interactions. Local execution, provenance and
multi-model review are established capabilities; avoid “first”, “only” or claims
that protocol compliance proves scientific truth.

| Existing stack | Use it for | Our additional layer |
|---|---|---|
| [ARIS](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep) | Research/review guidance; currently a pinned adapted review rubric | Frozen plans, append-only records, eligible foreign review and review budgets |
| [Nextflow](https://training.nextflow.io/latest/nextflow_run/03_config/) | Scheduling, task execution and caching | Claim/predeclaration checks and iteration-owned evidence |
| [AiiDA](https://aiida.net/) | Established computational workflows and provenance | A different emphasis on agent research declarations and critique; no replacement claim |
| [AI Scientist v2](https://github.com/SakanaAI/AI-Scientist-v2) | Automated scientific experimentation | Focus on operator-governed, harness-portable studies using existing HPC infrastructure |

Show a five-minute product demonstration: declare a hypothesis, freeze it,
submit a container task, resume without recomputation, show a failed control,
request one bounded foreign review, and inspect the evidence record. Include
the unsuccessful attempt; retaining it is part of the value.

The model budget story is concrete: no model for polling, scheduling, status or
context assembly; reuse an unchanged eligible review; cap submitted prompt bytes,
captured output bytes, elapsed time and calls per iteration. These are not exact
provider token or billing caps. Harness system prompts and internal work add cost.

Do not promise an air-gapped system when external model APIs are enabled. Compute
runs locally; supplied review context can leave the cluster. Do not imply that
cross-family agreement is orthogonal scientific validation. Results remain
candidates without the required independent scientific evidence.

A practical initial offering is the open protocol and adapters, with optional
paid site deployment, training and support. Validate demand with HPC teams using
the demo before building hosted orchestration, a new scheduler or a broad UI.
