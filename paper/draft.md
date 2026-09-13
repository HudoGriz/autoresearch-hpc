# AutoResearch HPC: an auditable protocol layer for AI-assisted computational research on HPC systems

> **Draft status:** publication working copy. Claims marked `TODO-EVIDENCE` must
> not survive into a submission without a corresponding public artifact or
> measured result. Author names, affiliations, acknowledgements and the final
> venue format are intentionally left open.

## Summary

AI coding agents can now write analysis code, inspect results and iterate rapidly
on computational research questions. The same flexibility creates a research-
process problem: an agent can alter an analysis after seeing a result, silently
replace a failed attempt, lose the distinction between a planned and exploratory
analysis, or rely on conversation history that is unavailable to a later
reviewer. Workflow engines solve execution and caching, but do not by themselves
enforce when a research plan was declared, whether it changed after results
existed, how corrections are represented, or whether an automated critique was
performed against the same frozen evidence.

AutoResearch HPC (`arh`) is a small protocol-enforcement layer for AI-assisted
computational research on infrastructure a research group already operates. It
combines hash-frozen pre-declarations, append-only iterations, workflow execution
through Nextflow, scheduler-backed compute, content-identified task environments,
foreign-model-family cross-checks, and a durable project ledger. The software is
not an autonomous scientist and does not treat model agreement as scientific
validation. Its purpose is narrower: make important research-process boundaries
mechanically inspectable and make the project resumable from files on disk rather
than from an earlier chat transcript.

## Statement of need

Modern computational research commonly combines a workflow engine, a batch
scheduler, containers, version control and one or more AI coding assistants.
These components are individually useful but leave a gap between **executing a
workflow reproducibly** and **conducting an auditable sequence of research
claims**.

For example, Nextflow can preserve a task graph and resume cached computation,
but it does not require the scientific estimand, acceptance criteria, negative
controls or detection limit to be written before a result exists. Git records
changes, but it does not by itself make an iteration append-only or refuse a
conclusion whose declaration was edited after execution. Agent transcripts can
contain rationale, but they are provider-specific, difficult to resume across
harnesses, and unsuitable as the authoritative research record.

AutoResearch HPC targets research software engineers, computational scientists
and HPC users who want to use coding agents while preserving a reviewable chain
from research question to declared analysis, execution evidence, critique and
conclusion.

## State of the field

AutoResearch HPC is deliberately complementary to existing research software.
Nextflow remains responsible for workflow execution and caching; Slurm, PBS or a
local executor provide compute; Singularity/Apptainer provide task environments.
Version-control and provenance systems such as Git, DataLad, Sumatra and AiiDA
address overlapping aspects of history and execution provenance. Electronic lab
notebooks and preregistration systems address other parts of the research record.
Agentic research systems focus on generating hypotheses, analyses or manuscripts.

The distinct contribution here is the composition of these ideas into a small
set of **mechanically enforced research boundaries** designed for agent-driven
iteration: atomic iteration claiming, pre-declaration before results, tamper
checks on the frozen declaration, append-only correction, bounded cross-model
review, and an authoritative disk-based ledger. AutoResearch HPC does not replace
existing workflow/provenance tools; it adds a protocol layer above them.

## Software design

A project is a directory containing `.arh/` configuration and state, an
append-only ledger, standing rules, and numbered iterations. A normal iteration
has three phases:

1. **Pre-declare.** `arh claim` allocates an iteration atomically; `arh new`
   scaffolds its declaration; `arh gate predeclare` checks required fields and
   freezes a cryptographic hash before results are permitted.
2. **Execute.** `arh submit` delegates execution to Nextflow and the configured
   scheduler. Scientific tasks run in declared container environments and
   execution metadata, logs, failures and receipts remain owned by the
   iteration.
3. **Review and record.** `arh ask` dispatches a bounded review using a separately
   configured model family, `arh gate results` verifies the evidence still
   matches the frozen declaration, and `arh ledger` updates the durable project
   state.

Skills and CLI commands are intentionally separate. Skills describe how an
agent should approach tasks such as iteration, verification or replication;
`arh` commands perform deterministic state transitions and checks that should not
depend on an agent remembering instructions.

Several design choices are conservative. Corrections create new iterations
rather than rewriting old ones. A cross-check verdict is evidence rather than a
scientific ruling. Hashes detect later changes but are not trusted timestamps.
The guard and container-bind policy are safety rails for cooperative workflows,
not a sandbox for hostile code.

## Evaluation

The source tree currently includes a regression suite covering the core protocol
and boundary conditions, and validation has exercised local and Slurm execution,
cached resume, deliberate task failure, and rejection of an attempted immutable-
input write inside a compute task. These tests establish software behavior, but
they are not sufficient evidence for broad claims about research quality or
cross-model review effectiveness.

The publication evaluation therefore separates deterministic protocol behavior
from stochastic model review. A pre-specified failure-injection matrix tests
conditions including late results, declaration tampering, concurrent iteration
claims, immutable-input writes, failed tasks, same-family review, stale reviewed
evidence and cold project resumption. The same small synthetic analysis is run
with and without the protocol layer so execution behavior can be distinguished
from AutoResearch HPC's added checks.

An engineering pilot of the provider-free deterministic subset ran from a clean
GitHub Actions checkout on 13 September 2026. Eight injected scenarios were
executed: incomplete pre-declaration, result-before-freeze, frozen-declaration
tampering, eight concurrent claims, an immutable-input write, same-family review,
stale reviewed evidence, and cold resumption from a fresh working directory.
All eight produced the pre-specified behavior. This pilot is retained in
`paper/pilot-results.md` and is explicitly not the final release-tag evaluation;
failed-task and interrupt/recovery scenarios remain in the integration path, and
the observed per-gate timings are not interpreted as workflow overhead.

A second benchmark will evaluate review roles against a frozen corpus of known
analysis defects and clean controls, reporting defect-class sensitivity,
false-positive rate, qualified/abstaining verdicts and repeatability. Cross-model
agreement will not be interpreted as independent scientific validation.

`TODO-EVIDENCE:` replace the pilot with the final release-tag failure-injection
result table; add runtime overhead, public example hashes, release-candidate
Slurm evidence and the independent-user reproduction outcome.

## Research impact

AutoResearch HPC was motivated by field use of agent-assisted computational
analysis and by defects discovered while operating that workflow. Those defects
were converted into regression tests and protocol checks rather than retained as
informal lessons. The software is intentionally domain-agnostic: the protocol
records questions, estimands, evidence and execution state without encoding a
specific scientific assay or analysis package.

The strongest remaining evidence gap is external use. Before submission, the
release candidate should be installed and used by at least one person who did
not develop the software, from repository documentation alone. A second research
use case outside the originating workflow would substantially strengthen the
claim of domain independence.

`TODO-EVIDENCE:` cite the public release DOI, independent installation report,
and any externally documented research use.

## Limitations

AutoResearch HPC does not prove that a pre-declaration existed at a trusted
external time; the current local hash only detects later change. It cannot make a
scientifically weak design valid, and a model reviewer can be wrong in correlated
ways with the producing model. External model services may receive context
supplied by the harness, so local/HPC execution does not imply air-gapped
inference. Host-side controller state is less isolated than task containers, and
some execution backends and heterogeneous/GPU workloads have less validation
than the principal local/Slurm path.

These limitations are part of the design contract rather than hidden behind a
"fully autonomous" claim.

## AI usage disclosure

Generative AI systems were used substantially in the development of AutoResearch
HPC, including code drafting, documentation, design review and adversarial
critique. AI-generated changes were treated as untrusted contributions: they
were inspected by the maintainer, exercised by automated tests, and where
appropriate cross-checked through a separately configured model family. The
paper draft was also prepared with generative AI assistance and must receive
normal author review before submission. The software does not treat AI-generated
text or model agreement as ground truth.

## Acknowledgements

`TODO:` add contributors, institutional support, funding and any infrastructure
acknowledgements that the authors intend to publish.

## References to complete for submission

The final bibliography should include at minimum: Nextflow, Singularity or
Apptainer, DataLad, Sumatra/AiiDA or another representative provenance system,
Workflow Run RO-Crate/W3C PROV where discussed, relevant preregistration work,
and the agentic-research/reviewer benchmark literature used to motivate the
failure modes.
