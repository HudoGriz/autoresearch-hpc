# Proposals

**Original proposal register.** Updated decisions and implementation status are
in [the 2026-09-09 review](framework-review.md#proposal-by-proposal-decisions).
The original proposals below are preserved as design history. Nothing here is
committed to. Evidence for each is in [`prior-art.md`](prior-art.md);
positioning is in [`related-work.md`](related-work.md).

Status is one of `PROPOSED` · `ACCEPTED` · `REJECTED` · `DONE`. Everything is
`PROPOSED` until you say otherwise. Effort is calendar-honest for one person who
already knows the codebase.

| # | Proposal | Effort | Status |
|---|---|---|---|
| [P1](#p1) | Rule waivers, with a required reason | half a day | `PROPOSED` |
| [P2](#p2) | Trusted timestamping of pre-declarations | half a day | `PROPOSED` |
| [P3](#p3) | Typed DAG nodes and edges | 1 day | `PROPOSED` |
| [P4](#p4) | Digest-pin container images | half a day | `PROPOSED` |
| [P5](#p5) | Execution-time provenance capture in `arh submit` | 1–2 days | `PROPOSED` |
| [P6](#p6) | Workflow-engine runner (Nextflow / Snakemake) | 2–3 days | `PROPOSED` |
| [P7](#p7) | `arh graph` — the knowledge graph | 1–2 weeks | `PROPOSED` |
| [P8](#p8) | Align `finding.schema.json` with the claim-aware profile | half a day | `PROPOSED` |
| [P9](#p9) | RO-Crate export | 2–3 days | `PROPOSED` |
| [P10](#p10) | Nanopublications for findings | 3–4 days | `PROPOSED` |
| [P11](#p11) | Standing rules as SHACL shapes | 2–3 days | `PROPOSED` |
| [P12](#p12) | in-toto attestations as the record format | 3–4 days | `PROPOSED` |
| [P13](#p13) | MCP server for `arh` | 2 days | `PROPOSED` |
| [P14](#p14) | Reports as build artifacts | 2 days | `PROPOSED` |
| [P15](#p15) | Guix/Nix for bit-reproducible environments | 1–2 weeks | `PROPOSED` |
| [P16](#p16) | Benchmark the cross-check roles | 1–2 weeks | `PROPOSED` |
| [R1](#r1) | Repository release chores | 1 hour | `BLOCKED — needs your identity` |

---

## P1 — Rule waivers, with a required reason {#p1}

**Problem.** Standing rules are all-or-nothing. When a rule is wrong for one
iteration, the only escape is deleting it from `project.md` — silently, for the
whole project, leaving no trace.

> A rule that cannot be waived honestly will be evaded dishonestly.

**Proposal.** Per-iteration waivers with a mandatory reason. `arh gate` *prints*
active waivers rather than passing quietly, and the waiver is carried into the
report so a reader sees which rule was set aside and why.

**Evidence.** nf-core allows specific lint tests to be disabled in
`.nf-core.yml`, with per-file granularity, and only "in exceptional
circumstances… if agreed upon by the community". See `prior-art.md` §2.2.

**Risk.** Waivers become routine. Mitigate by surfacing the count in
`arh status` — a project with many waived rules should look like one.

---

## P2 — Trusted timestamping of pre-declarations {#p2}

**Problem.** `PREDECLARATION.sha256` proves the pre-declaration has not
*changed*. It does not prove it *predates the results* — anyone can delete it
and regenerate it from an edited README. For a preregistration mechanism that is
the half that matters when a result is challenged.

**Proposal.** Follow eLabFTW's RFC 3161 flow: export, hash, request a token from
a Time Stamping Authority, store the export and the token together.

| Option | Cost | Proves |
|---|---|---|
| Signed git tag pushed to a public remote | ~10 lines | a third party attests the hash existed by date X |
| **OpenTimestamps** (`ots stamp`) | one binary, no account | Bitcoin-anchored, verifiable indefinitely |
| RFC 3161 TSA token | free public TSAs | the standard; what ELNs actually use |
| Sigstore cosign + Rekor | needs OIDC | ties the stamp to *who*, in a public log |

**Recommendation:** OpenTimestamps — no account, no key management, one line in
`arh gate predeclare`. Add RFC 3161 as an option for sites that require it.

**Risk.** External dependency at gate time. Make it non-blocking with a
`arh gate stamp` catch-up command, so a cluster without egress still works.

---

## P3 — Typed DAG nodes and edges {#p3}

**Problem.** `arh dag check` can verify a node appears in the graph, but not that
the terminal claim actually *derives* from the declared inputs. A step that only
passes data through is indistinguishable from one that produces something.

**Proposal.** Adopt AiiDA's model: node `kind` of `data` / `calculation` /
`workflow`, and edge types `input` / `create` / `return` / `call`. Then enforce:

> Data provenance must be a strict DAG. Logical provenance may contain cycles —
> a workflow can legitimately return its own input.

`arh dag check` gains a real test: the terminal claim must have a `create`-path
back to a declared input.

**Evidence.** `prior-art.md` §2.1.

**Risk.** More to fill in by hand. Mitigate by defaulting `kind` to
`calculation` and only requiring the distinction where the check would fire.

---

## P4 — Digest-pin container images {#p4}

**Problem.** `image_samtools = /opt/….sif` is a *path*. Swap the file and
nothing notices. The README claims runs are reproducible; without this they are
merely pinned by name.

**Proposal.** Record each image's sha256 on first use; `arh run` refuses a
changed digest unless the config is updated deliberately. Support
`docker://…@sha256:…` for remote images.

**Risk.** None material. This one is close to free and closes an overstatement.

---

## P5 — Execution-time provenance capture in `arh submit` {#p5}

**Problem.** `arh submit` records almost nothing. The human is expected to write
down what ran, which they will not do reliably.

**Proposal.** Capture automatically at execution: code version, parameters,
input and output hashes, container digest, hostname, scheduler job id, wall time,
exit status. Write it beside the job's logs. Make the record **re-executable**,
not merely descriptive.

**Evidence.** Sumatra's `smt run` and DataLad's `datalad run` / `datalad rerun`
have done exactly this for years. `prior-art.md` §2.4.

**Risk.** Hashing large outputs is slow. Make hashing opt-out per job.

---

## P6 — Workflow-engine runner (Nextflow / Snakemake) {#p6}

**Problem.** `arh submit` is a thin `sbatch` wrapper — no DAG, no resume, no
per-rule containers, no provenance.

**Proposal.** `runner = slurm | snakemake | nextflow` in `site.md`.
Scheduling is now delegated to Nextflow; extend its site configuration rather than adding a custom scheduler.

**Note.** Nextflow is the obvious choice here given you already run nf-core
pipelines; Snakemake has the better built-in reporting.

**Risk.** Scope creep — this framework is not a workflow engine and should not
become one. Keep the runner a dispatch target, not an abstraction over both.

---

## P7 — `arh graph`, the knowledge graph {#p7}

**Problem.** The iteration record and the literature vault are **the same graph
seen from two sides**, and they never meet.

A literature note can recommend a method with a caveat, while an iteration
records that the same method failed to run. Those two facts belong on one
node, and a reader of either file alone gets a misleading picture.

> The literature says what should work. The iterations say what did.

**Proposal.** Four thin layers, three of which already exist as files. Full
design in [`knowledge-graph-design.md`](knowledge-graph-design.md).

| Layer | Choice |
|---|---|
| Truth | files in git — iteration record **+ the existing Obsidian vault** |
| Vocabulary | PROV-O + CiTO + FaBiO + a small local `arh:` |
| Generation | Morph-KGC RML mappings, enriched from OpenAlex (no auth needed) |
| Store & view | Oxigraph default · Neo4j+MCP for agent querying · Cytoscape.js + Mermaid |

```bash
arh graph build | enrich | query | view | check
```

**Two hard rules.** The database is a rebuildable index, never the source of
truth — Kùzu was archived in October 2025 and anyone who made it their truth is
now migrating. And **no LLM-inferred edges**: a provenance record whose edges
were guessed by a model is not evidence.

**Suggested first slice:** `build` + `view` only — extract the vault and the
iteration record to RDF, render a static Cytoscape.js page. No external
dependencies, and it shows the join immediately.

**Risk.** The largest item here, and the easiest to over-build. If the first
slice does not produce a picture worth looking at, stop.

---

## P8 — Align `finding.schema.json` with the claim-aware profile {#p8}

**Problem.** Our finding type is private. An emerging profile covers the same
ground.

**Proposal.** Adopt the [claim-aware observability](https://arxiv.org/abs/2608.18312)
minimum: stable artifact ID, kind, payload hash, creator operator, timestamp,
status. We are close already; this makes us interoperable rather than bespoke,
and gives a citation.

**Risk.** The profile is new and may move. Cheap enough to redo.

---

## P9 — RO-Crate export {#p9}

**Proposal.** `arh crate` emitting a
[Workflow Run RO-Crate](https://doi.org/10.1371/journal.pone.0309210) per
concluded iteration: depositable to WorkflowHub/Zenodo, W3C PROV aligned,
citable. This is the publication path for an *iteration*.

**Depends on:** P5 (there is little provenance to package until then).

---

## P10 — Nanopublications for findings {#p10}

**Proposal.** Emit each finding as a nanopublication — assertion, provenance and
publication-info graphs, individually citable. This is how a *finding* leaves
the repo and enters the literature graph, and it maps almost one-to-one onto
`finding.schema.json`.

**Depends on:** P8, and ideally P7.

**Risk.** Publishing claims into a public graph is irreversible. Only findings
with status `supported` should ever be emitted, never `candidate`.

---

## P11 — Standing rules as SHACL shapes {#p11}

**Problem.** Rules are regexes over prose. That catches a sound analysis written
up in overreaching language — the common case — but it is lexical, and can be
satisfied by rephrasing.

**Proposal.** Once findings are RDF, express the same rules as SHACL shapes over
the data: *every finding with status `supported` must have a `detectionLimit`
carrying a value, units and a basis*. Structural, not lexical.

**Keep the regex rules.** They catch a different failure and both are needed.

**Depends on:** P7.

---

## P12 — in-toto attestations as the record format {#p12}

**Proposal.** Replace ad-hoc `.sha256` files and `CROSSCHECK_*.md` with signed
in-toto statements (subject = iteration artifacts, predicate = pre-declaration /
cross-check / gate result). Verifiable with standard supply-chain tooling;
GitHub Actions provides artifact attestations for free.

**Overlaps P2** — decide whether timestamping is a small addition to the current
format or the trigger to move to in-toto wholesale. Doing P2 cheaply first and
P12 later is the low-risk order.

---

## P13 — MCP server for `arh` {#p13}

**Proposal.** Expose claim / gate / ask / status / graph-query as MCP tools, so
any MCP client participates without shelling out. Also the natural seam with
PROV-AGENT, which already speaks MCP.

**Note.** `arh status --json` already makes `arh` callable from code; this is
about *agent* ergonomics, not capability.

---

## P14 — Reports as build artifacts {#p14}

**Problem.** `iterationN_report.md` is hand-written and can silently drift from
`results/`. Numbers get retyped.

**Proposal.** Follow showyourwork: numbers and figures in a report are
*generated* from results, not transcribed. At minimum, a check that every number
in the report appears in a result file.

**Risk.** Over-rigid templating makes reports unwritable. Start with the check,
not the generator.

---

## P15 — Guix/Nix for bit-reproducible environments {#p15}

**Problem.** Container *builds* are rarely reproducible, so "pinned" is not
"reproducible".

**Proposal.** Guix + Apptainer gives bit-for-bit rebuilds from a git commit and
composes with HPC deployment.

**Risk.** Large lift, and it imposes Guix on every user of the framework. Likely
belongs as a documented option rather than a default. **Lowest priority here** —
P4 captures most of the practical benefit for a fraction of the cost.

---

## P16 — Benchmark the cross-check roles {#p16}

**Problem.** We assert that adversary / estimand-auditor / reimplementer catch
real defects. We have one anecdote — codex catching the toy analysis pooling
paired observations — and no measurement.

**Proposal.** Evaluate against SPOT, CORE-Bench and BadScientist. Then, if the
study team agrees, derive an in-the-wild benchmark from the reference project's
own record: iterations where a later one overturned an earlier gives
(pre-declaration, results, flawed conclusion, known correction) with ground truth.

**This is the strongest publication artifact available** — real errors, not
synthetic injections. It is also the item most dependent on other people
agreeing.

---

## R1 — Repository release chores {#r1}

Blocked on information only you have:

- Repository badge and clone URL now target `HudoGriz/autoresearch-hpc`.
- `CITATION.cff:15` — `repository-code` URL
- `CITATION.cff:24-25` — your name, ORCID if you have one
- `LICENSE:3` — copyright holder
- add a remote and push; first push is CI's first real run
- re-sign the commits: all are unsigned (no pinentry in the authoring
  environment). `git rebase --exec 'git commit --amend --no-edit -S' --root`

---

## Suggested order, if you want one

**Now, cheap, closes overstatements:** P4, P1, P2 — in that order. Each is under
a day and each fixes something the repo currently claims but does not do.

**Next, the practical win:** P5 then P6. Provenance capture makes P9 possible;
the runner is the biggest day-to-day gain.

**Then the ambitious one:** P7 first slice only. Stop if the picture is not
worth looking at.

**Publication track, when the study team is ready:** P8 → P10, and P16.

**Probably never:** P15 as a default.
