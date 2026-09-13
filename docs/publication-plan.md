# Publication readiness plan

AutoResearch HPC is ready to move from feature-building toward **evidence-building**.
The publication question is no longer "can this be made more sophisticated?" but
"can an independent reader install it, reproduce the intended workflow, observe
the protocol boundaries, and understand what evidence supports each claim?"

This document is the working roadmap for a short research-software paper.

## Target venues

### Near-term: Software Impacts

Software Impacts is the practical first target. It publishes short,
peer-reviewed articles describing reusable software that addresses a research
challenge. The code must be publicly available at submission.

Target manuscript framing:

> **AutoResearch HPC: an auditable protocol layer for AI-assisted computational
> research on HPC systems**

The paper should emphasize the software contribution and a compact evaluation,
not claim that cross-model agreement establishes scientific truth.

### Later: JOSS

JOSS is an excellent fit once the project has a longer public development and
adoption record. Current JOSS screening requires at least six months of public,
active development and demonstrated research impact; simply making a repository
public and waiting is not enough. Treat JOSS as the follow-on target after
external use has accumulated.

Useful links:

- https://joss.readthedocs.io/en/latest/submitting.html
- https://joss.readthedocs.io/en/latest/paper.html
- https://www.elsevier.com/researcher/author/tools-and-resources/research-elements-journals

## Publication claim

The defensible contribution is:

> AutoResearch HPC is a protocol-enforcement layer for AI-assisted
> computational research that makes pre-declaration, append-only evidence,
> workflow execution, independent critique, and resumable research state
> mechanically inspectable on existing HPC infrastructure.

Do **not** position it as another scheduler, workflow engine, autonomous scientist,
or guarantee of scientific correctness.

## Phase 0 — public-release safety

**Exit criterion:** the repository can be made public without exposing research
material, machine-specific details, credentials, private model-session links or
personal metadata that the maintainers do not intend to publish.

- [ ] Replace private-study examples in documentation with synthetic examples.
- [ ] Run a secret scan over the working tree **and full Git history**.
- [ ] Remove or rewrite private Claude/session URLs in historical commit messages.
- [ ] Decide whether historical commit author email should remain public; use a
      GitHub noreply address for future commits if not.
- [ ] Confirm that no private fork retains history that is intended to be purged.
- [ ] Keep `.env`, local audit studies, runtime images, caches and machine-specific
      state ignored.

A branch-only cleanup does not remove sensitive material from existing Git
history. If history rewriting is required, perform it immediately before the
first public release and coordinate any forks/clones.

## Phase 1 — citable public release

**Exit criterion:** a stranger can cite an immutable release rather than a
moving branch.

- [ ] Make the sanitized repository public.
- [ ] Tag a release candidate and then a stable pre-1.0 release (for example,
      `v0.3.0`).
- [ ] Archive the tagged release in Zenodo and record the software DOI.
- [ ] Request/confirm Software Heritage archival.
- [ ] Complete `CITATION.cff` with the intended author list and affiliations.
- [ ] Add the software DOI to the README after minting it.
- [ ] Confirm CI passes from a clean public checkout.

## Phase 2 — one completely reproducible public example

**Exit criterion:** a new user can reproduce the example without private data or
institution-specific infrastructure.

The example should exercise the complete logical path:

```text
question -> pre-declaration -> frozen plan -> execution -> report
         -> foreign-family review -> result gate -> ledger
```

The repository now contains `examples/mean-shift/`, a small deterministic
synthetic analysis with no scientific-domain dependency. It is intended as the
seed for this publication example.

Still required:

- [ ] Capture a complete `arh` transcript from a clean checkout.
- [ ] Package the final example as a self-contained study fixture.
- [ ] Record expected outputs and hashes.
- [ ] Test the example in CI.
- [ ] Document the no-network/offline variant where practical.

## Phase 3 — protocol evaluation

**Exit criterion:** the paper can support its central claims with measured
behavior rather than architecture alone.

The primary evaluation is a **failure-injection study**, not a benchmark of
scientific truth. Compare an ordinary AI-assisted workflow with the same workflow
under AutoResearch HPC, using controlled failure scenarios.

Minimum scenarios:

| Scenario | Expected ARH behavior |
|---|---|
| result exists before pre-declaration | pre-declaration gate refuses it |
| frozen declaration edited | result gate detects hash mismatch |
| two agents claim simultaneously | exactly one gets each iteration number |
| immutable input is modified | guard/container policy rejects the write |
| task exits non-zero | failure is propagated and preserved |
| same-family reviewer used | foreign-family gate refuses it by default |
| reviewed evidence changes | prior review becomes ineligible |
| process resumes without chat history | status/context/ledger identify next state |

Measure at least: detection rate, false-refusal rate on valid workflows,
wall-clock overhead of protocol operations, and amount of durable evidence
created. See [`evaluation-plan.md`](evaluation-plan.md).

## Phase 4 — independent reproduction

**Exit criterion:** at least one person who did not develop AutoResearch HPC can
install and run the example from documentation alone.

Ask an external colleague/lab to record:

- machine / scheduler / container runtime;
- whether installation succeeded from the README alone;
- time to first successful `arh doctor`;
- confusing or missing instructions;
- whether the full public example reproduced;
- any changes needed to the repository.

Treat every needed intervention as a usability defect and record the fix.

A second environment is more valuable than another large batch of unit tests.

## Phase 5 — manuscript

**Exit criterion:** every factual claim in the paper points to a repository
artifact, evaluation result or cited source.

A draft lives in [`../paper/draft.md`](../paper/draft.md). Keep the final short:

1. Summary / motivation
2. Statement of need and state of the field
3. Software design
4. Evaluation and research impact
5. Limitations
6. AI-use disclosure

For JOSS, keep the final manuscript within its current 750–1750 word range and
retain the required state-of-the-field, software-design, impact and AI-use
sections.

## Evidence ledger for the paper

Do not write stronger prose than the evidence supports.

| Claim | Evidence available now | Still needed |
|---|---|---|
| protocol boundaries are mechanically checked | core + boundary regression tests | public failure-injection summary |
| runs on HPC | observed Slurm success/failure | independent second environment |
| supports reproducible task environments | digest checks + container execution | clean public reproduction |
| can resume without chat history | ledger/status/context design and tests | independent usability test |
| cross-check roles improve error discovery | anecdotal/internal examples | controlled benchmark |
| useful beyond one domain/lab | architecture is domain-agnostic | second independent use case |

## Stop conditions

Do **not** delay the first paper for ambitious additions such as a knowledge
graph, MCP server, SHACL conversion, nanopublications or Nix/Guix integration.
Those may be useful later, but they do not close the principal publication gap.

The highest-value next work is:

1. sanitize and release publicly;
2. make one example completely reproducible;
3. run the failure-injection evaluation;
4. obtain one independent reproduction;
5. submit the short software paper.
