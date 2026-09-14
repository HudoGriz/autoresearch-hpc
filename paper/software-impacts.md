# AutoResearch HPC: auditable AI-assisted computational research on existing HPC clusters

> **Working copy for Software Impacts** (Original Software Publication template, version 2).
> Follows the template's sections and limits: abstract ≈100 words, ≤6 keywords, code
> metadata C1–C9, body ≤3 pages. Items marked `TODO` need author input or release
> evidence; `TODO-EVIDENCE` items must not reach submission without an artifact.
> Keep facts in step with `draft.md` and `evidence-matrix.md`.

## Authors

`TODO:` names, affiliations, addresses, corresponding author e-mail.

## Abstract

AutoResearch HPC is a protocol layer for computational research carried out with AI
coding agents on infrastructure a group already runs. A command-line tool, `arh`,
enforces the research boundaries agents most easily blur: an iteration is claimed
atomically, its plan is written and hash-frozen before results exist, analyses run as
Nextflow workflows on Slurm or local executors inside digest-pinned containers, a model
from a different family reviews the frozen evidence, and corrections become new
iterations rather than edits. A disk-based ledger lets any agent or person resume a
project without chat history. The software is harness-agnostic and domain-agnostic.

## Keywords

AI agents; research reproducibility; preregistration; provenance; high-performance computing; Nextflow

## Code metadata

| Nr. | Code metadata description | Value |
|---|---|---|
| C1 | Current code version | `TODO` — release tag (for example `v0.3.0`) |
| C2 | Permanent link to code/repository used for this code version | `TODO` — Zenodo DOI of the tagged release; repository https://github.com/HudoGriz/autoresearch-hpc |
| C3 | Permanent link to Reproducible Capsule | `TODO` — optional; `examples/mean-shift` is the candidate |
| C4 | Legal Code License | MIT License |
| C5 | Code versioning system used | git |
| C6 | Software code languages, tools, and services used | Bash, Python 3, Nextflow, Singularity/Apptainer, Slurm/PBS/local executors; optional agent CLIs (Claude Code, Codex, OpenCode) |
| C7 | Compilation requirements, operating environments & dependencies | Linux (x86-64, ARM64, ppc64le); Bash; Python 3; Singularity or Apptainer; Slurm/PBS clients for cluster use. No compilation. `arh init --bootstrap` installs a pinned micromamba, Java and Nextflow into the project |
| C8 | If available, link to developer documentation/manual | `TODO` — repository `README.md`, `PROTOCOL.md`, `docs/` at the release tag |
| C9 | Support email for questions | `TODO` |

## Body

### Purpose and functionality

Coding agents can now write analysis code, run it and interpret results quickly. That
speed creates process risks that a better model does not remove: an analysis can change
after its result is seen, failed attempts can disappear, planned and exploratory analyses
can blur together, and the project's real state can live only in a chat transcript.
Workflow engines solve execution and caching but not these research-process boundaries.

AutoResearch HPC adds a thin, mechanical layer on top of existing tools. A project is a
directory with a ledger, standing rules and numbered, append-only iterations. Each
iteration follows the same path:

1. **Claim and declare.** `arh claim` takes the next iteration number atomically (the
   directory creation is the lock), and `arh new` scaffolds a pre-declaration with the
   question, estimand, instrument, acceptance criteria, negative controls, detection limit
   and prediction. `arh gate predeclare` checks it and freezes its SHA-256 hash; it refuses
   if results already exist.
2. **Execute.** `arh submit` runs a Nextflow workflow through the site's scheduler with
   scientific tasks in a digest-pinned Singularity/Apptainer image and declared inputs
   mounted read-only. Each run leaves a receipt with hashes of the workflow, configuration,
   image and scripts, including runs that fail.
3. **Review and record.** `arh ask` sends a size-bounded review packet to an agent CLI from
   a different model family than the producer and stores the verdict bound to the hashes of
   the declaration, report and results. `arh gate results` accepts the iteration only if
   the declaration is unchanged and an eligible foreign review exists. `arh ledger` renders
   the project state and checks it against disk.

Instructions live in a single `AGENTS.md` contract and reusable skills that Claude Code,
Codex, OpenCode and other harnesses read natively, while enforcement stays in the CLI so it
does not depend on an agent remembering the rules. Arms, discovery DAGs and blind
reimplementation from a frozen specification support more complex studies.

### Impact overview

The software targets research groups and research software engineers who want to use
coding agents on their own clusters and still be able to show, afterwards, how each result
was produced. It changes daily practice in three ways. First, the plan-before-results rule
becomes a refusal by the tool, not a convention. Second, failure is preserved: failed runs,
null results, killed controls and superseded conclusions stay in the record. Third, work
moves between agents, harnesses and people through files on disk rather than conversation
history.

The protocol grew out of agent-assisted analysis in a clinical genomics laboratory, where
concrete failures — two agents creating the same iteration, a framing error propagating
through several iterations, a set reproduced in size but not in membership — were turned
into mechanical checks and regression tests.

Evaluation so far is deliberately narrow. A pre-specified failure-injection matrix
exercises ten protocol violations (for example results before freezing, an edited frozen
plan, concurrent claims, writes to immutable inputs, failed tasks, same-family review,
stale reviewed evidence, interrupted submission and cold resumption); all ten produced the
specified behaviour in clean CI pilots. `TODO-EVIDENCE:` final release-tag table.

`TODO-EVIDENCE:` replication benchmark — agent loops on six highly cited studies from
cancer genomics, social psychology, cosmology, a stroke trial, labour economics and ecology,
with blind grading against published results; report rounds to convergence, wall time and
tokens per study, and every framework defect found and fixed.

`TODO-EVIDENCE:` independent installation by a user outside the development team.

### Ongoing research using the software

`TODO:` list projects that use AutoResearch HPC, if the authors choose to name them.

### Limitations and future work

Hashes detect later changes to a pre-declaration but do not prove when it was written;
trusted timestamping is future work. Cross-family review reduces one source of correlated
error; it is not independent scientific validation, and reviewers can be wrong. Containment
is cooperative: read-only mounts protect declared inputs inside tasks, but the host-side
controller is not a sandbox for hostile code, and blinding an agent to information requires
operating-system permissions the tool does not set up. Model services receive the context
they are given, so on-premises execution does not imply air-gapped inference. Producer
sessions are not budgeted by the tool, and provider usage limits can dominate throughput.
PBS and GPU workloads are less tested than Slurm and local execution. Planned work includes
typed discovery DAGs, RO-Crate export of concluded iterations, and a reference runner for
unattended rounds.

### Publications enabled by the software

`TODO:` list, or state that none are published yet.

## Acknowledgements

`TODO` (optional).

## References

`TODO:` software DOI (Zenodo) first, then Nextflow; Singularity/Apptainer; RO-Crate
(Leo et al. 2024, PLoS ONE, doi:10.1371/journal.pone.0309210); AI Scientist v2
(arXiv:2504.08066); SPOT (arXiv:2505.11855); BadScientist (arXiv:2510.18003); agentic
provenance (PROV-AGENT, arXiv:2508.02866). All identifiers above were checked on 2026-09-14.
