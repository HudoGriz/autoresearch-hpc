# Proposals

This is the historical proposal register. Updated implementation decisions live
in [the framework review](framework-review.md#proposal-by-proposal-decisions).
For publication priorities, use [`publication-plan.md`](publication-plan.md)
rather than this list.

The purpose of keeping the register is to preserve design rationale without
turning every interesting idea into a requirement for the first release.
Publication-facing examples are synthetic; private study details do not belong
in this repository.

| # | Proposal | Original effort estimate | Status in this register |
|---|---|---:|---|
| [P1](#p1) | Rule waivers, with a required reason | 0.5 day | `PROPOSED` |
| [P2](#p2) | Trusted timestamping of pre-declarations | 0.5 day | `PROPOSED` |
| [P3](#p3) | Typed DAG nodes and edges | 1 day | `PROPOSED` |
| [P4](#p4) | Digest-pin container images | 0.5 day | `PROPOSED` |
| [P5](#p5) | Execution-time provenance capture | 1–2 days | `PROPOSED` |
| [P6](#p6) | Workflow-engine runner | 2–3 days | `PROPOSED` |
| [P7](#p7) | Rebuildable knowledge graph | 1–2 weeks | `PROPOSED` |
| [P8](#p8) | Align finding schema with external profiles | 0.5 day | `PROPOSED` |
| [P9](#p9) | RO-Crate export | 2–3 days | `PROPOSED` |
| [P10](#p10) | Nanopublications for findings | 3–4 days | `PROPOSED` |
| [P11](#p11) | Standing rules as SHACL shapes | 2–3 days | `PROPOSED` |
| [P12](#p12) | in-toto attestations | 3–4 days | `PROPOSED` |
| [P13](#p13) | MCP server for `arh` | 2 days | `PROPOSED` |
| [P14](#p14) | Reports as build artifacts | 2 days | `PROPOSED` |
| [P15](#p15) | Guix/Nix environments | 1–2 weeks | `PROPOSED` |
| [P16](#p16) | Benchmark cross-check roles | 1–2 weeks | `PROPOSED` |

> The implementation has moved since this register was written. Some ideas above
> are now partially or substantially implemented. The register is design history,
> not a live feature matrix.

---

## P1 — Rule waivers, with a required reason {#p1}

**Problem.** Standing rules that are all-or-nothing invite users to delete a rule
project-wide when it is inappropriate for one iteration.

**Proposal.** Per-iteration waivers with a mandatory reason. Gates should print
active waivers, and reports should carry them forward so exceptions remain
visible.

**Risk.** Waivers become routine. Surface waiver counts in project status and
make them conspicuous rather than silent.

---

## P2 — Trusted timestamping of pre-declarations {#p2}

**Problem.** `PREDECLARATION.sha256` proves that a declaration has not changed;
it does not prove to an external party that the declaration existed before the
results.

**Proposal.** Add an optional third-party timestamp path such as RFC 3161,
OpenTimestamps, or a transparency-log-backed attestation. Sites without network
egress must remain usable, so external timestamping should be separable from the
local gate.

**Publication note.** Do not claim trusted temporal priority until such an
external mechanism is implemented and evaluated.

---

## P3 — Typed DAG nodes and edges {#p3}

**Problem.** Presence in a graph does not prove that a terminal claim derives
from declared inputs.

**Proposal.** Adopt typed provenance nodes/edges (for example data,
calculation/workflow and input/create/return/call relationships) and require a
valid derivation path from declared inputs to the terminal claim.

**Risk.** Manual burden. Require richer typing only where it enables a concrete
check.

---

## P4 — Digest-pin container images {#p4}

**Problem.** A path is not content identity; a file can change in place.

**Proposal.** Record and verify SHA-256 for local images and require digest-
qualified remote references. This should fail before execution when declared
content identity no longer matches.

---

## P5 — Execution-time provenance capture {#p5}

**Problem.** Human-authored execution notes are incomplete and drift from what
actually ran.

**Proposal.** Capture code identity, parameters, input/output identity,
container identity, scheduler metadata, timing and exit status at execution
time. Prefer records that are sufficient to reconstruct or replay the run.

**Risk.** Hashing very large data can be expensive; allow explicitly documented
policies rather than silently skipping identity.

---

## P6 — Workflow-engine runner {#p6}

**Problem.** AutoResearch HPC should not become a second scheduler or workflow
engine.

**Proposal.** Delegate execution to an established workflow engine and extend
site configuration rather than reimplementing scheduling, DAG execution and
cache semantics.

**Design constraint.** Keep the runner a dispatch target, not a bespoke
abstraction over every workflow system.

---

## P7 — Rebuildable knowledge graph {#p7}

**Problem.** As append-only research histories grow, links between literature,
methods, intermediate artifacts, superseded findings and later corrections
become difficult to navigate from prose alone.

A synthetic example is sufficient to illustrate the need: a literature record
may state that method `M` is valid only under a paired design, while an iteration
records that a specific analysis used an independent-groups formulation and was
rejected. Those two facts should be navigable from the same method/claim node.

**Proposal.** Build a disposable graph index from versioned source files rather
than making a graph database authoritative. Reuse PROV-O/CiTO where possible,
with a small `arh:` vocabulary for protocol-specific concepts. See
[`knowledge-graph-design.md`](knowledge-graph-design.md).

**Two hard rules.** The graph is rebuildable from files, and provenance edges are
not invented by an LLM.

**Publication priority.** Low for the first paper. Independent reproduction and
evaluation close a much more important evidence gap.

---

## P8 — Align `finding.schema.json` with external claim/provenance profiles {#p8}

**Problem.** A private finding type is harder to exchange with other research
infrastructure.

**Proposal.** Map stable artifact ID, kind, payload hash, creator, timestamp and
status onto a maintained external profile where that creates real
interoperability.

**Risk.** Emerging profiles can move. Keep the internal record stable enough to
remap later.

---

## P9 — RO-Crate export {#p9}

**Proposal.** Export a concluded iteration as Workflow Run RO-Crate so it can be
archived or deposited using established provenance conventions.

**Depends on.** Sufficient execution-time provenance to make the crate more than
a wrapper around prose.

---

## P10 — Nanopublications for findings {#p10}

**Proposal.** Optionally emit supported findings as assertion + provenance +
publication-info graphs.

**Risk.** Public claim publication can be irreversible. Never publish
`candidate` findings automatically.

---

## P11 — Standing rules as SHACL shapes {#p11}

**Problem.** Regex rules over prose catch language problems but can be satisfied
by rephrasing.

**Proposal.** If a structured graph exists, add structural constraints such as
requiring every supported finding to carry a detection limit with value, units
and basis.

**Keep the prose checks.** Lexical and structural validation catch different
failure classes.

---

## P12 — in-toto attestations {#p12}

**Proposal.** Represent key protocol transitions with standard attestations so
pre-declaration, cross-check and gate evidence can be verified by external
tooling.

**Relationship to P2.** Trusted timestamping is a smaller problem; do not adopt a
large attestation stack merely to obtain a timestamp.

---

## P13 — MCP server for `arh` {#p13}

**Proposal.** Expose stable operations such as claim, gate, ask and status as MCP
tools for agent clients.

**Note.** Machine-readable CLI output already provides a simpler integration
surface. MCP is an ergonomics feature, not a publication blocker.

---

## P14 — Reports as build artifacts {#p14}

**Problem.** Hand-transcribed numbers can drift from result files.

**Proposal.** Generate or verify load-bearing report values from result
artifacts. Start with consistency checks before imposing a report generator.

---

## P15 — Guix/Nix for bit-reproducible environments {#p15}

**Problem.** Content-identified containers improve replayability but do not prove
that an image itself can be rebuilt bit-for-bit.

**Proposal.** Document Guix/Nix as an optional stronger environment path where a
site needs it.

**Risk.** High operational cost and inappropriate as a mandatory dependency.

---

## P16 — Benchmark the cross-check roles {#p16}

**Problem.** It is easy to demonstrate that a reviewer sometimes catches an
error and much harder to quantify what the review roles contribute.

**Proposal.** Evaluate shipped review roles on a frozen corpus of known defects
and clean controls. Candidate defect classes include paired-vs-independent
analysis, post-result threshold selection, negative-control failure, set
membership mismatch, estimand denominator mismatch and unsupported detection
limits.

Report sensitivity by defect class, false positives on clean cases, qualified or
abstaining verdicts, and repeatability across reruns. Preserve prompts and raw
review records.

This is a high-value publication artifact because it turns an anecdotal benefit
into a measurable one. See [`evaluation-plan.md`](evaluation-plan.md).

---

## Publication-first ordering

For the first short software paper, prioritize:

1. sanitized public release and citable archive;
2. deterministic public example;
3. failure-injection evaluation;
4. one independent reproduction;
5. cross-check benchmark if time permits.

Do **not** delay submission to build P7, P10, P11, P13 or P15. They may support
future work but do not address the principal evidence gap for the first paper.
