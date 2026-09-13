# Knowledge graph: design sketch

**Proposal P7, not a decision.** Tracked in
[`proposals.md`](proposals.md#p7) and not committed to. Options considered are
in [`prior-art.md`](prior-art.md) §4; this file is the detail behind the
proposal — what it would look like if built.

## The short answer

**Do not adopt a "knowledge graph framework" as the source of truth.** Keep the
research record in ordinary files and make any graph a disposable, rebuildable
index.

A possible implementation has four thin layers:

| Layer | Choice | Why |
|---|---|---|
| Truth | Files in git — iteration record + literature notes | Durable and reviewable |
| Vocabulary | PROV-O + CiTO + FaBiO + a small local `arh:` | Reuse standards; invent only what is genuinely ours |
| Generation | [Morph-KGC](https://github.com/morph-kgc/morph-kgc) RML mappings, enriched from [OpenAlex](https://openalex.org) | Declarative, reviewable, versioned |
| Store & view | Oxigraph (default) · Neo4j + MCP (agent querying) · Cytoscape.js (viewing) | Disposable and rebuildable |

## The insight that makes this potentially useful

The iteration record and the literature record are **the same graph seen from
two sides**, but ordinary project files rarely connect them mechanically.

A synthetic example illustrates the gap. Suppose a literature note records that
method `M` is valid only when a paired design is encoded correctly. A later
iteration records that an attempted analysis silently treated paired samples as
independent and was therefore rejected. Those facts should meet on the same
method/claim node:

> **The literature says what should work. The iterations say what did. Joining
> them is the point of the graph.**

No private research example is required to express that design.

## Layer 1 — truth stays in files

**Project side** — `CLAIM.json`, the frozen `README.md`, `DAG.md`,
`finding.json`, `CROSSCHECK_*.md`, arm `FATE`, and
`PREDECLARATION.sha256`.

**Literature side** — ordinary structured notes or bibliographic records. YAML
frontmatter, DOI fields and explicit links can already encode useful metadata
without making the graph database authoritative.

Nothing enters the graph that does not exist as a source artifact first.

## Layer 2 — vocabulary: reuse, invent sparingly

| Concept | Term | Notes |
|---|---|---|
| Iteration | `prov:Activity` | `prov:startedAtTime`, `prov:wasAssociatedWith` the harness |
| Finding | `prov:Entity` | `prov:wasGeneratedBy` the iteration |
| Harness / agent | `prov:Agent` | attribution is already recorded |
| Derivation | `prov:wasDerivedFrom` | how a finding depends on inputs and earlier findings |
| Paper | `fabio:ResearchPaper` | from DOI/bibliographic metadata |
| **Paper supports finding** | `cito:supports` | typed citation relation |
| **Paper contradicts finding** | `cito:disagreesWith` | typed citation relation |
| **Method taken from paper** | `cito:usesMethodIn` | method provenance |
| **Cited as evidence** | `cito:citesAsEvidence` | evidence provenance |

[CiTO](https://sparontologies.github.io/cito/current/cito.html) is useful because
it types *why* something is cited rather than representing every citation as the
same edge.

A small local vocabulary would cover concepts that are specific to the
protocol:

```text
arh:Arm  arh:fate  arh:Gate  arh:preDeclarationHash  arh:preDeclaredAt
arh:CrossCheck  arh:verdict  arh:verifierFamily  arh:producerFamily
arh:detectionLimit  arh:negativeControlBehaved  arh:supersededBy
arh:DagNode  arh:nodeKind  arh:branchCount
```

## Layer 3 — generation

```text
iteration files ─┐
literature notes ┼─→ CSV/JSON ─→ Morph-KGC (RML mappings) ─→ RDF ─→ Oxigraph
OpenAlex ────────┘
```

**Morph-KGC** with RML mappings is preferable to bespoke conversion code because
the mapping itself becomes a reviewable, versioned artifact.

**OpenAlex** can supply open literature metadata for DOIs already present in the
project record, avoiding a new private API credential in the default path.

## Layer 4 — store, query, view

**Oxigraph** is a reasonable default store: embedded, SPARQL-capable and without
a required daemon.

**Neo4j + [`mcp-neo4j-cypher`](https://github.com/neo4j-contrib/mcp-neo4j)** may
be useful if interactive agent querying later justifies the operational cost.

For viewing, prefer layers that do not create a new source of truth:

- **Mermaid** for a single iteration DAG;
- **Cytoscape.js** for a static project graph;
- **Graphviz** for publication figures.

## Proposed interface

```bash
arh graph build     # files -> RDF via RML mappings
arh graph enrich    # DOIs -> literature metadata
arh graph query     # SPARQL; optionally emit a Cypher load script
arh graph view      # static Cytoscape.js page
arh graph check     # structural checks over the generated graph
```

## What the graph would be for

Questions that become difficult as an append-only project grows include:

- Which findings were superseded, by what, and how long did each take to overturn?
- Which claims depend on a method carrying an explicit literature caveat?
- Which papers support a finding that a later iteration retracted?
- Which DAG nodes have no creation path from a declared input?
- Which arms were infeasible, and is there recorded evidence explaining why?
- Which cross-check objections were rejected, and what later evidence bears on
  those decisions?

The graph is therefore primarily a navigational and consistency layer over the
existing evidence.

## SHACL, later

If findings are represented as RDF, standing rules could later become **SHACL
shapes over structured data** in addition to regex checks over prose. For
example, every finding with status `supported` could be required to carry a
detection limit with value, units and basis.

The prose rules should remain: structural and lexical checks catch different
failure classes.

## Two things not to do

**Do not let an LLM infer provenance edges.** LLM extraction may help search
prose, but a provenance backbone whose edges were guessed by a model is not
reliable evidence. Typed support/derivation edges must be grounded in source
artifacts.

**Do not make the graph database the source of truth.** It is an index. If it
cannot be dropped and rebuilt from versioned files in one command, the design is
wrong.

## Publication priority

This proposal is **not required for the first software paper**. The current
publication gap is independent validation and reproducible evaluation, not graph
infrastructure. See [`publication-plan.md`](publication-plan.md).
