# Knowledge graph: design sketch

**Proposal P7, not a decision.** Tracked in
[`proposals.md`](proposals.md#p7) and not committed to. Options considered are
in [`prior-art.md`](prior-art.md) §4; this file is the detail behind the
proposal — what it would look like if built.

## The short answer

**Do not adopt a "knowledge graph framework".** Every candidate either drags in
a server you must operate, or a vendor who may disappear —
[Kùzu was archived in October 2025](https://www.theregister.com/software/2025/10/14/kuzudb_graph_database_abandoned/)
after Apple acquired it.

Build it from four thin layers instead, of which **three already exist as files
in the project**:

| Layer | Choice | Why |
|---|---|---|
| Truth | Files in git — iteration record + Obsidian vault | Already there; survives any tool dying |
| Vocabulary | PROV-O + CiTO + FaBiO + a small local `dl:` | Reuse standards; invent only what is genuinely ours |
| Generation | [Morph-KGC](https://github.com/morph-kgc/morph-kgc) RML mappings, enriched from [OpenAlex](https://openalex.org) | Declarative, reviewable, versioned |
| Store & view | Oxigraph (default) · Neo4j + MCP (agent querying) · Cytoscape.js (viewing) | All disposable and rebuildable |

## The insight that makes this worth doing

The iteration record and the literature vault are **the same graph seen from two
sides**, and they currently never meet.

The project's Evidence Matrix says:

> | Genome-wide DMR | dmrseq | DSS | High | *Paired design and covariates must be encoded correctly* |

Iteration 51's Arm C found that dmrseq **failed on all 48 array tasks at
`BSseq()`**, so chr6 was never region-tested and the candidate has no DMR-level
evidence at all.

Those two facts belong on the same node. One says what the method *should* do;
the other says what it *did*. Nothing in the current setup brings them together,
and a reader of either file alone gets a misleading picture.

> **The literature says what should work. The iterations say what did. Joining
> them is the entire point of the graph.**

## Layer 1 — truth stays in files

Two halves, both already present:

**Project side** — `CLAIM.json`, the frozen `README.md`, `DAG.md`,
`finding.json`, `CROSSCHECK_*.md`, arm `FATE`, `PREDECLARATION.sha256`.

**Literature side** — the Obsidian vault. It is already machine-readable and
nobody has noticed: YAML frontmatter is structured metadata, `[[wikilinks]]` are
edges, and the templates already carry the right fields. The Article Note
Template has `DOI`, `Study type`, `Genome build`, `Software/version`,
**`Parameters or decisions informed`** and **`Quotable facts to verify`** — the
last two are precisely the edges into the iteration record.

Nothing enters the graph that does not exist as a file first.

## Layer 2 — vocabulary: reuse, invent sparingly

| Concept | Term | Notes |
|---|---|---|
| Iteration | `prov:Activity` | `prov:startedAtTime`, `prov:wasAssociatedWith` the harness |
| Finding | `prov:Entity` | `prov:wasGeneratedBy` the iteration |
| Harness / agent | `prov:Agent` | claude, codex, opencode — attribution is already recorded |
| Derivation | `prov:wasDerivedFrom` | how a finding depends on inputs and earlier findings |
| Paper | `fabio:ResearchPaper` | from the vault's DOIs |
| **Paper supports finding** | `cito:supports` | |
| **Paper contradicts finding** | `cito:disagreesWith` | |
| **Method taken from paper** | `cito:usesMethodIn` | this is what the Evidence Matrix encodes informally |
| **Cited as evidence** | `cito:citesAsEvidence` | |

[CiTO](https://sparontologies.github.io/cito/current/cito.html) is the important
one. It exists precisely to type *why* something is cited, which is the
distinction the Evidence Matrix makes in prose and no bibliography makes at all.

A small local vocabulary covers what is genuinely ours and has no standard term:

```
dl:Arm  dl:fate  dl:Gate  dl:preDeclarationHash  dl:preDeclaredAt
dl:CrossCheck  dl:verdict  dl:verifierFamily  dl:producerFamily
dl:detectionLimit  dl:negativeControlBehaved  dl:supersededBy
dl:DagNode  dl:nodeKind  dl:branchCount
```

## Layer 3 — generation

```
iteration files ─┐
Obsidian vault ──┼─→ CSV/JSON ─→ Morph-KGC (RML mappings) ─→ RDF ─→ Oxigraph
OpenAlex ────────┘
```

**Morph-KGC** with RML mappings, not bespoke conversion code. The mapping is
then itself a reviewable, versioned artifact — and when the schema changes, the
diff shows what changed about the *meaning*, not about someone's Python.

**OpenAlex** for literature metadata: 250M+ works, fully open API, **no
authentication**, run by the nonprofit OurResearch. Feed it the DOIs already in
the vault's frontmatter and get authors, venue, year, citations and open-access
status back. No key to manage, nothing to expire.

## Layer 4 — store, query, view

**Oxigraph** as the default store: embedded, SPARQL, no daemon, one directory.
Rebuildable from files in a single command, so if it dies the way Kùzu did, the
cost is an afternoon.

**Neo4j + [`mcp-neo4j-cypher`](https://github.com/neo4j-contrib/mcp-neo4j)** when
interactive agent querying earns its keep — its MCP and Text2Cypher tooling is
materially ahead of anything else. Run it under Apptainer inside a SLURM
allocation; see [`prior-art.md`](prior-art.md) §4.5.

**Viewing**, three tiers, none needing a server:

- **Obsidian's own graph view** — already installed, already works, zero effort
- **Mermaid** for a single iteration's DAG — already in `DAG.md`, renders on GitHub
- **Cytoscape.js** static page for the whole project graph — offline, embeddable
- **Graphviz** when a figure has to go in a paper

## Proposed interface

```bash
dl graph build     # files → RDF via the RML mappings
dl graph enrich    # DOIs → OpenAlex → literature metadata
dl graph query     # SPARQL; or emit a Cypher load script for Neo4j
dl graph view      # static Cytoscape.js page
dl graph check     # SHACL shapes over the result (see below)
```

## What the graph is actually for

Questions that are currently unanswerable without reading 6,800 lines of
`PROGRESS.md` by hand:

- Which findings were superseded, by what, and how long did each take to overturn?
- Which claims rest on a method the Evidence Matrix flags as caveated — and did
  that caveat actually bite?
- Which papers support a finding that a later iteration retracted?
- Which DAG nodes have no `create`-path from a declared input?
- Which arms were `INFEASIBLE`, and does the literature explain why?
- Which cross-check verdicts were `UNSOUND` and rejected, and were the rejections
  later vindicated?

That last one is the loop learning about itself.

## SHACL, later

Once findings are RDF, the standing rules can become **SHACL shapes over the
data** rather than regexes over prose: *every finding with status `supported`
must have a `dl:detectionLimit` carrying a value, units and a basis*. That is a
structural constraint, and unlike a regex it cannot be satisfied by rephrasing.
The regex rules stay — they catch a sound analysis written up in overreaching
language, which is a different and commoner failure.

## Two things not to do

**Do not let an LLM infer the edges.** `LLMGraphTransformer` and
`PropertyGraphIndex` are well-supported and wrong here: a provenance record whose
edges were guessed by a model is not evidence. Every `cito:supports` must be
asserted by a person or produced by an iteration, and must carry its source.
LLM extraction is fine for *searching* the prose; never for the backbone.

**Do not make the database the source of truth.** It is an index. If it cannot
be dropped and rebuilt from files in one command, the design is wrong.
