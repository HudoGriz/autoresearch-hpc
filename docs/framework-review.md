# Framework review and rebuild — 2026-09-09

The useful core is a portable research protocol with executable gates. Keep it small, harden its evidence handling, and delegate execution graphs to established workflow engines. The original code is a working prototype, but its documentation promises stronger guarantees than its gates provide.

## Existing frameworks: checked against primary sources

| System | What it supplies | Implication for AutoResearch HPC |
|---|---|---|
| [ARIS](https://github.com/wanshuiyin/auto-claude-code-research-in-sleep) | Markdown skills, research workflows and cross-model reviews usable across agent harnesses | Closest match. Portable prompts and cross-model review alone are not a differentiator; explicit estimands, frozen plans, negative controls and durable evidence checks are the useful focus here. |
| [AI Scientist v2](https://github.com/SakanaAI/AI-Scientist-v2) | Automated ideation, experiment execution and manuscript production, with experiment search | A reference for research automation, not a drop-in HPC protocol or proof that generated conclusions are reliable. |
| [AutoRA](https://github.com/AutoResearch/autora) | Components for experimental design, data collection and model discovery | A useful domain-loop integration when those interfaces fit the study. Avoid reimplementing its experiment-design machinery. |
| [AiiDA](https://aiida.readthedocs.io/projects/aiida-core/en/stable/topics/provenance/concepts.html) | Data and process provenance with distinct calculation and workflow semantics | Learn its type distinctions; an untyped Mermaid picture does not establish data lineage. |
| [Nextflow](https://docs.seqera.io/nextflow/cache-and-resume) | Task caching and resumability based on execution metadata and retained outputs | Use as an execution layer for larger pipelines. Keep research pre-declaration and interpretation gates above it. |
| [DataLad](https://docs.datalad.org/en/latest/generated/man/datalad-rerun.html) | Re-execution of recorded commands | A model for eventual replay; logging a script path is not sufficient to reproduce a run. |

This is a targeted comparison of documented capabilities, not an empirical benchmark of these systems. Source pages were inspected on 2026-09-09. No external framework was installed or tested.

## Source review and implemented changes

1. **Reviews were accepted by filename.** An empty, failed, same-family or stale `CROSSCHECK_*.md` could satisfy the results gate. Reviews now get JSON execution records; the gate checks successful execution, exactly one recognized verdict, distinct concrete family declarations, and hashes of the reviewed declaration, report and review text. Status, ledger and next-step guidance use the same eligibility check. `UNSOUND` remains a completed review, not an endorsement: the protocol treats verdicts as evidence, and operators must address objections in the record.
2. **Frozen declarations could be overwritten.** The predeclare gate now refuses an existing freeze and creates the first record without clobbering another concurrent writer. It also fails on missing standing-rule files.
3. **Harness argument handling was unreliable.** A stdlib Python adapter parses quoted argument templates without a shell, supports `{prompt}` and `{cwd}`, sets the project working directory and enforces a process-group timeout. Repeated reviews get unique output filenames. Invalid or timed-out responses return failure and retain diagnostic records.
4. **Local jobs did not report reliable completion.** The submitting shell now waits on its actual child and propagates its exit status. Local jobs write JSON with script hash, working directory, hostname, PID, start/end and exit status, plus unique logs. Submission requires a script under a claimed, frozen, unchanged iteration.
5. **Images were only pinned by name.** Non-smoke container runs now require declared images: explicit SHA-256 for local image files, or a digest-qualified remote reference. Docker URI prefixes are normalized. Relative image directories resolve from the project root.
6. **Relative immutable input paths bypassed the write guard.** The guard now resolves them against the project root before comparison.
7. **Tests asserted a weak contract.** Added negative-control regressions for the boundaries above; the legacy review fixture now supplies matching metadata, and its deliberate tamper is restored before unrelated tests.

## Proposal-by-proposal decisions

These are implementation decisions under the operator's request to evaluate and rebuild. They do not imply every proposed feature is shipped.

| Proposal | Decision | Reason / required next step |
|---|---|---|
| P1: waivers | Defer | Useful, but a waiver must be scoped, reasoned and frozen before results. A mutable switch would weaken the gates just repaired. |
| P2: trusted timestamps | Accept direction; defer external integration | Local hashes detect changes; they do not prove temporal priority against an actor who controls the filesystem. [OpenTimestamps](https://opentimestamps.org/) supplies independently verifiable timestamp proofs. Pending and verified proofs must be distinct; a non-blocking stamp must never be reported as verified. A signed git timestamp alone is not a trusted timestamp. |
| P3: typed DAG | Accept direction; defer migration | Follow AiiDA's data/process distinctions. Do not default unknown node kinds to calculation: that fabricates semantics. Define an explicit versioned schema and validate edge types and input-to-output reachability. |
| P4: digest pinning | Implemented | Require an explicit expected digest, rather than silently trusting first use. `none` remains an explicitly unpinned smoke-test mode. |
| P5: execution provenance | Implemented local subset | Local code hash and completion metadata shipped. Full input/output manifests, container linkage, scheduler accounting and replay remain necessary before claiming complete provenance. |
| P6: workflow runner | Defer adapter | Nextflow is a sensible first supported engine when a real pipeline exists. Do not conflate scheduler choice with workflow-engine choice. Integration tests need an actual workflow and execution environment. |
| P7: knowledge graph | Defer stack; accept file-derived index design | Keep publication-facing examples synthetic. Start from explicit typed relations and stable artifact IDs. Morph-KGC, Oxigraph and Cytoscape are dependencies; choose one concrete query need before building multiple stores. |
| P8: claim profile | Defer external alignment | Stable IDs, hashes, creators and statuses are useful independently. A new paper is not automatically an interoperability standard; specify a versioned local schema and a mapping first. |
| P9: RO-Crate | Accept later | Good archival export after execution manifests exist. Export locally; publication requires its own authorization. |
| P10: nanopublications | Defer | A publication mechanism is premature before stable finding identifiers and adjudication. Candidate status should be represented accurately; public publication must be an explicit action. |
| P11: SHACL | Defer until RDF exists | Structural validation adds value. It still cannot prove the scientific adequacy of a detection limit or control. Keep prose checks labeled as lint. |
| P12: in-toto | Defer format replacement | Attestations authenticate statements, not scientific truth. Add signed exports later without destroying old evidence formats. |
| P13: MCP | Defer | The CLI already provides a useful integration seam. Stabilize its semantics before adding another interface. |
| P14: generated reports | Accept explicit bindings; reject number-search heuristic | “Every number appears in a result file” can accept a wrong denominator and reject dates or citations. Bind named report metrics to machine-readable result fields and units instead. |
| P15: Nix/Guix | Optional documentation only | Content pinning and deterministic analysis are the immediate wins. Do not impose a new environment manager as a prerequisite. |
| P16: role benchmark | Highest research priority, not completed here | A live review is an integration test, not a sensitivity estimate. Predeclare a labeled defect set, false-positive controls, models, repetitions, cost and held-out evaluation before collecting results. |
| R1: release chores | Leave identity/publication steps pending | Fix local documentation paths, but do not invent the owner's identity, publish the repository or rewrite commit history automatically. Unsigned historical commits alone do not justify a repository-wide rebase. |

## Corrections to the design claims

- Cross-family review reduces one source of correlated errors; it does not establish statistical independence. The family is configured metadata, not provider attestation. A multi-provider harness must declare the actual selected model family, never `mixed` as evidence of diversity.
- Copies of a specification and a different working directory are not filesystem isolation. Current blind-replication commands still require trusted agents or externally enforced filesystem permissions. They are not a confidentiality boundary.
- A local hash and clock cannot prove a plan predates privately computed results. Freeze protection catches normal accidental edits; it is not tamper-proof against the workspace owner.
- Regexes over prose are lint, not validation of experimental design. A qualifying sentence elsewhere can satisfy a lexical rule without justifying a specific claim.
- The graph proposal's no-authentication promise for OpenAlex should not be a design dependency. Its current [access documentation](https://help.openalex.org/access/) describes multiple products and access/pricing tiers. Verify the chosen endpoint's current contract and handle credentials, rate limits and cached responses explicitly.
- Container digests identify bytes, but do not guarantee deterministic results or reproducible image builds. Host smoke tests do not validate container isolation.

## Validation and remaining scope

The original baseline passed 136 checks. Validation evidence and a live review are retained in the maintainer's ignored local audit study. The public source release summarizes the tested behavior without publishing machine-specific or source-study artifacts.

This rebuild strengthens the existing protocol. It does not ship all sixteen proposals or claim unattended scientific discovery is solved. Remaining work includes enforced blind execution, full scheduler accounting, append-only storage outside the writer's authority, complete input/output provenance, review adjudication and benchmarked scientific error detection.

## Foreign-review corrections

A bounded live review returned `QUALIFIED` during hardening. Follow-up work fixed concurrent-job temporary-path collisions, a local digest-shaped filename bypass, literal prompt substitution, binding reviews to result artifacts, review snapshots, verdict diagnostics, unpinned-host warnings, harness-name validation, numeric threshold parsing and signal exit-code normalization.

The maintained test count is not an empirical no-regression estimate; it records passing behavior checks that were written and corrected during engineering work, not a preregistered scientific-efficacy benchmark.

This document describes the earlier hardening baseline. See [validation](validation.md)
for subsequent Singularity/Slurm validation and the source-release evidence scope, and see
[publication plan](publication-plan.md) for the external-evidence work required before a paper submission.
