# Prior art, and technologies worth adopting

Research notes, September 2026. What already exists, what we should learn from
it, and what we should not build ourselves.

Companion to [`related-work.md`](related-work.md), which covers positioning
against autonomous-scientist systems. This file is about **tooling we can
borrow from**.

---

## 1. Frameworks worth reading

| Framework | What it is | Why it matters here |
|---|---|---|
| [AiiDA](https://github.com/aiidateam/aiida-core) ([Sci Data 2020](https://www.nature.com/articles/s41597-020-00638-4)) | Workflow manager built around a provenance graph. SLURM/PBS/SGE/LSF out of the box; millions of queryable nodes | The mature version of what `dl dag` does by hand |
| [nf-core](https://nf-co.re/docs/guidelines/pipelines/overview) | Convention + `nf-core lint` + template, for Nextflow pipelines | Exactly our genre: MUST-level rules with a linter enforcing them |
| [eLabFTW](https://github.com/elabftw/elabftw) | Open-source electronic lab notebook with RFC 3161 timestamping | The production recipe for our pre-declaration timestamping gap |
| [Sumatra](https://github.com/open-research/sumatra) | "Automated electronic lab notebook for computational projects" | Closest ancestor in spirit; captures at execution time |
| [DataLad](https://joss.theoj.org/papers/10.21105/joss.03262.pdf) | git-annex data management with `datalad run` / `rerun` | Provenance records that are *executable*, not just descriptive |
| [showyourwork](https://show-your.work/en/latest/intro/) | Snakemake + tectonic + CI; the article is a build target | Every figure traceable to the code and data that made it |
| [Popper convention](http://alumni.soe.ucsc.edu/~msevilla/papers/jimenez-ipdpsw17.pdf) | A *convention*, not a tool, for reproducible systems evaluation | Direct genre precedent for `PROTOCOL.md` |

---

## 2. Three lessons that change our design

### 2.1 AiiDA — our DAG nodes and edges are untyped, and that is why `dl dag check` is weak

AiiDA distinguishes **data nodes** from **process nodes**, and splits processes
into *calculations* (which create new data) and *workflows* (which only
orchestrate, returning data that already exists). Four link types connect them:
`input`, `create`, `return`, `call`.

The payoff is a rule we currently cannot express:

> **Data provenance must be a strict DAG. Logical provenance may contain
> cycles** — because a workflow can legitimately return its own input.

Our DAG has generic nodes and one arrow type. With typing, `dl dag check` could
verify that the terminal claim has a `create`-path back to the declared inputs.
That is precisely how a claim comes to rest on a step which only passed data
through without producing anything — a defect invisible in any narrative report.

**Action:** add a `kind` column to the DAG node table (`data` / `calculation` /
`workflow`) and an edge-type annotation; extend `dl dag check` to require a
`create`-path from inputs to the terminal claim.

### 2.2 nf-core — our standing rules have no waiver mechanism, and that is a design flaw

nf-core lets a pipeline disable specific lint tests in `.nf-core.yml`, with
granularity down to a single file, and only *"in exceptional circumstances… if
agreed upon by the community."*

Our rules are all-or-nothing. When a rule is wrong for one iteration, the only
escape is deleting it from `project.md` — silently, for the whole project,
leaving no trace. That is strictly worse than an explicit waiver.

> **A rule that cannot be waived honestly will be evaded dishonestly.**

**Action:** per-iteration waivers with a **required reason**; `dl gate` prints
active waivers rather than passing quietly; the waiver is carried into the
report so a reader sees which rule was set aside and why.

### 2.3 eLabFTW — the timestamping recipe already exists, proven in real labs

`PREDECLARATION.sha256` proves the pre-declaration has not *changed*. It does
not prove it *predates the results* — anyone can delete it and regenerate it
from an edited README. For a preregistration mechanism that is the half that
matters when a result is challenged.

eLabFTW's RFC 3161 flow, in production use:

1. export the entity as JSON
2. hash it
3. request a timestamp token from a Time Stamping Authority
4. store the JSON **and** the token together in an immutable archive

**Action:** copy it. Options, ascending in strength:

| Mechanism | Cost | What it proves |
|---|---|---|
| Signed git tag pushed to a public remote | free, ~10 lines | a third party attests the hash existed by date X |
| [OpenTimestamps](https://gwern.net/timestamping) (`ots stamp`) | free, one binary, no account | Bitcoin-anchored, verifiable by anyone, indefinitely |
| RFC 3161 TSA token | free public TSAs | the standard, and what ELNs actually use |
| [Sigstore](https://slsa.dev/blog/2023/05/in-toto-and-slsa) cosign keyless + Rekor | needs an OIDC identity | ties the stamp to *who*, in a public append-only log |

### 2.4 Sumatra and DataLad — capture provenance at execution time, automatically

`smt run` and `datalad run` wrap the command and record code version,
parameters, inputs, outputs and platform without asking the human for anything.
`datalad rerun` then re-executes from that record.

Our `dl submit` records almost nothing. It should capture the same record
itself, and the record should be re-executable rather than merely descriptive.

### 2.5 showyourwork — the report should be a build artifact

Our `results/report/iterationN_report.md` is hand-written and can silently drift
from `results/`. showyourwork ties every figure to the code and data that
produced it, and CI rebuilds the paper. Worth adopting at least partially: the
numbers in a report should be generated, not retyped.

---

## 3. Standards worth targeting

- **[Workflow Run RO-Crate](https://doi.org/10.1371/journal.pone.0309210)** —
  package a concluded iteration for deposit to WorkflowHub/Zenodo. W3C PROV
  aligned.
- **[in-toto](https://slsa.dev/blog/2023/05/in-toto-and-slsa) attestations** —
  replace ad-hoc `.sha256` files and `CROSSCHECK_*.md` with signed statements
  (subject = iteration artifacts, predicate = pre-declaration / cross-check /
  gate result). Verifiable with standard tooling.
- **[Nanopublications](https://nanopub.readthedocs.io/en/latest/getting-started/what-are-nanopubs.html)**
  — assertion + provenance + publication-info graphs, individually citable. How
  a *finding* leaves the repo and enters the literature graph. Maps almost
  one-to-one onto `schema/finding.schema.json`.
- **[Claim-aware observability profile](https://arxiv.org/abs/2608.18312)** —
  emit stable artifact IDs with kind, payload hash, creator operator, timestamp
  and status. `finding.schema.json` is nearly this already; aligning makes us
  interoperable rather than private.
- **[PROV-AGENT](https://arxiv.org/abs/2508.02866)** / [Flowcept](https://github.com/ORNL/flowcept)
  (ORNL) — W3C PROV extended for agent interactions, MCP-aware, HPC-native.
  Complementary, not competing: they capture what happened, we govern what may
  be claimed.

---

## 4. The knowledge graph: what to store it in

### 4.1 Get the scale right first

Our graph is **small**. 69 iterations × ~20 DAG nodes ≈ 1,400 nodes, plus
findings, arms, cross-checks and supersession edges. Call it low tens of
thousands at project maturity.

Neo4j is engineered for hundreds of millions. Standing up a JVM server on HPC to
query 1,400 nodes buys nothing on performance grounds. **The reason to want a
graph database here is the query and LLM interface, not the scale** — and that
is a legitimate reason, but it should be named honestly.

### 4.2 The architectural rule: files are the truth, the database is an index

> **The graph database must be a rebuildable cache, never the source of truth.**

Source of truth stays as files in git: pre-declarations, DAGs, `finding.json`
records, cross-check records. A `dl graph build` materialises those into
whatever store you like; `dl graph rebuild` reconstructs it from scratch.

This is not architectural fastidiousness. **Kùzu — the obvious embedded choice
until recently — was acquired by Apple, its repository archived on 10 October
2025 and its website shut down**
([The Register](https://www.theregister.com/software/2025/10/14/kuzudb_graph_database_abandoned/)).
Anyone who had made it their source of truth is now migrating. Treat the store
as disposable and that event costs you an afternoon instead of a project.

### 4.3 Options

| Store | Model | Daemon? | LLM interface | Verdict |
|---|---|---|---|---|
| **Neo4j Community** | property graph, Cypher | yes (JVM) | **best available** — official MCP servers | best LLM story; heaviest to run |
| **Oxigraph** | RDF, SPARQL | embeddable | weaker tooling | best fit if we go PROV/nanopub |
| **Apache Jena / Fuseki** | RDF, SPARQL | yes | weaker tooling | mature RDF, heavier |
| **DuckDB** (+ DuckPGQ) | relational + property graph | no | good text-to-SQL | excellent on HPC, zero ops |
| **FalkorDB** | property graph, Cypher | yes (Redis) | has an MCP server | lighter than Neo4j; the Kùzu migration path |
| **NetworkX / rustworkx** | in-process | no | none | fine for `dl dag check` itself |
| ~~Kùzu~~ | embedded property graph | no | — | **archived Oct 2025, do not adopt** |

### 4.4 Does Neo4j have an effective LLM interface? Yes — the best of any of them

This is where Neo4j genuinely wins:

- **[`mcp-neo4j-cypher`](https://github.com/neo4j-contrib/mcp-neo4j/blob/main/servers/mcp-neo4j-cypher/README.md)**
  — official MCP server. Extracts the schema so an agent can generate Cypher,
  then runs read and write queries. Any MCP client gets graph access with no
  bespoke integration.
- **[GraphRAG MCP server](https://neo4j.com/blog/developer/neo4j-graphrag-retrievers-as-mcp-server/)**
  — adds vector search, fulltext search, and `search_cypher_query` combining
  semantic retrieval with graph traversal. The agent does not need to know
  anything about embedding models or index structures.
- **[Text2Cypher](https://medium.com/neo4j/text2cypher-guide-cc161518a509)** —
  documented patterns, with query validation inside the tool call rather than
  hoping the model emits valid Cypher.
- **[Full MCP integration guide](https://neo4j.com/developer/genai-ecosystem/model-context-protocol-mcp/)**.

For our purposes that means an agent could be asked *"which findings were
superseded, and how long did each take to overturn?"* or *"show every claim
whose DAG has no create-path from a declared input"* and get a real answer.

### 4.5 Running Neo4j under Apptainer on HPC

Feasible, with caveats. Apptainer runs as **your** user with no root daemon, so
there is no privilege problem — a container is just an executable.

```bash
apptainer pull neo4j.sif docker://neo4j:5-community

# Neo4j writes to four directories; bind them into the project.
mkdir -p .dl/neo4j/{data,logs,conf,plugins}
apptainer instance start \
  --bind .dl/neo4j/data:/data \
  --bind .dl/neo4j/logs:/logs \
  --bind .dl/neo4j/conf:/var/lib/neo4j/conf \
  --bind .dl/neo4j/plugins:/plugins \
  --env NEO4J_AUTH=none \
  neo4j.sif dlgraph
```

Caveats that decide whether this is worth it:

1. **It is a long-running daemon.** Many sites forbid those on login nodes. In
   practice it belongs inside a SLURM allocation, with an SSH tunnel to reach
   Bolt (7687) or HTTP (7474) from your laptop. Both ports are unprivileged, so
   no root is needed — but two users on the same node will collide, so bind a
   port derived from `$SLURM_JOB_ID`.
2. **It is stateful.** That is exactly why §4.2 matters: keep it rebuildable.
3. **JVM heap** needs setting or it will guess badly inside a cgroup.
4. **Licence:** Community edition is GPLv3, which is fine for this; Enterprise
   is commercial.

### 4.6 Building the graph — do not hand-write the conversion

| Tool | What it does | Fit |
|---|---|---|
| **[Morph-KGC](https://github.com/morph-kgc/morph-kgc)** | R2RML/RML mappings → RDF from heterogeneous sources; integrates RDFLib, **Oxigraph**, Kafka | **Best fit.** Declarative mappings from our JSON/TSV to RDF, versioned as files, instead of bespoke conversion code |
| **[pySHACL](https://kg-construct.github.io/awesome-kgc-tools/)** | validates RDF against SHACL shapes | **The RDF analogue of `dl gate`** — see below |
| **[KG-Hub](https://kghub.org/)** / Biolink / KGX | modular ETL for biological KGs; versioned automatic builds, stable URLs, OBO ontology integration | Relevant if findings need to join a biomedical KG |
| **LangChain `LLMGraphTransformer`** / LlamaIndex `PropertyGraphIndex` | LLM extracts entities and relations from text into Neo4j | Useful for *navigating* prose. **Not for the provenance backbone** |
| [awesome-kgc-tools](https://kg-construct.github.io/awesome-kgc-tools/) | curated list of construction tooling | Starting point |

Two notes that matter more than the tool choice:

**pySHACL is worth serious thought.** Our standing rules are currently regexes
over prose — `forbid`/`requires` patterns in `rules/*.md`. That catches a
correct analysis written up in overreaching language, which is the common case,
but it is a blunt instrument. Once findings exist as RDF, the same rules can be
expressed as **SHACL shapes over the data**: *every finding of status
`supported` must have a `detection_limit` with a value, units and a basis*;
*every claim node must have a `create`-path to a declared input*. That is a
structural check rather than a lexical one, and it cannot be satisfied by
rephrasing.

**Do not let an LLM build the provenance graph.** LLM extraction into a
knowledge graph is a well-supported pattern and it is the wrong pattern here: a
provenance record whose edges were inferred by a model is not evidence, and it
breaks §4.2's rule that nothing enters the graph that does not exist as a file
first. Use LLM extraction to *search* the prose in `PROGRESS.md` if that helps;
never to populate the backbone.

### 4.7 Viewing it

| Tool | Kind | Fit |
|---|---|---|
| **Mermaid** | text-in-Markdown | **Already in use** in `DAG.md`. Renders natively on GitHub and in Artifacts. Zero dependencies — the default for per-iteration DAGs |
| **[Cytoscape.js](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9889963/)** | JS library, browser | **Best for the project-wide graph.** No server, works offline, embeds in a static HTML page or a published Artifact |
| **Graphviz** | static images | What AiiDA uses for provenance graphs. Good for a figure in a paper |
| **[Gephi](https://gephi.org/)** | desktop | Layout algorithms, metrics, filtering. For exploring structure, not for publishing |
| **Cytoscape (desktop)** | desktop | Broader visual range than Gephi — heat maps, scatter plots as well as networks |
| **Graphia** | desktop | Fastest of the three on large graphs; ours are not large |
| **[Neo4j Bloom](https://neo4j.com/product/bloom/)** | browser | Natural-language querying, no code. Tied to the Neo4j ecosystem |
| **[Memgraph Lab](https://hub.docker.com/r/memgraph/lab)** | browser | Free, Neo4j-compatible; a lighter Bloom substitute |
| **[Argo Lite](https://arxiv.org/pdf/2008.11844)** | browser, open source | Shareable interactive exploration without a server |

The practical split: **Mermaid for one iteration's DAG** (it is already there and
GitHub renders it), **Cytoscape.js in a static page for the whole project
graph** — iterations, arms, findings, supersession edges, cross-checks — and
**Graphviz when a figure has to go into a paper**. A database-backed viewer like
Bloom only earns its place once the graph is large enough that you cannot see it
whole, which for us is a long way off.

### 4.8 Recommendation

1. **Model findings and DAGs as files, in a PROV-aligned schema.** That is the
   source of truth and it is what gets published.
2. **Add `dl graph build`** emitting both an RDF dump and a Cypher load script,
   so the store is a choice rather than a commitment.
3. **Generate RDF with Morph-KGC mappings**, not bespoke code, so the mapping
   is itself a reviewable, versioned artifact.
4. **Ship a static Cytoscape.js page** for the project graph and keep Mermaid
   for per-iteration DAGs. Neither needs a server.
5. **Run Neo4j + `mcp-neo4j-cypher` when interactive agent querying earns its
   keep** — that is the one thing files cannot give you, and Neo4j's MCP tooling
   is materially ahead of the alternatives.
6. **Do not put anything in the graph that does not exist as a file first**, and
   never let a model infer the edges.

---

## 5. What none of them do

Every framework in §1 assumes a well-intentioned single researcher. None has
pre-declaration enforcement, adversarial cross-model verification, arms with
recorded fates, or a firewall between a specification and the code that
implemented it. **AiiDA would capture a p-hacked analysis in perfect detail.**

So the niche holds. But these projects are far ahead of us on provenance
*capture*, and the honest framing is that we are a governance layer to sit on
top of that stack — not a replacement for it.

## 6. Proposals arising

Every action this research implies is tracked in
[`proposals.md`](proposals.md) — the single register — rather than duplicated
here. Nothing is committed to.
