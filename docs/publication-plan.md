# Publication readiness plan

AutoResearch HPC is ready to move from feature-building toward **evidence-building**.
The publication question is no longer "can this be made more sophisticated?" but
"can an independent reader install it, reproduce the intended workflow, observe
the protocol boundaries, and understand what evidence supports each claim?"

This document is the working roadmap for a short research-software paper. Venue-
specific preparation notes are in [`../paper/venue-notes.md`](../paper/venue-notes.md).

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

- [x] Replace private-study examples in publication-facing documentation with
      synthetic/general examples.
- [x] Add a repository tree/history audit tool and CI hygiene workflow.
- [ ] Run a specialist secret scanner over the working tree **and full Git history**.
- [ ] Remove or rewrite private Claude/session URLs in historical commit messages.
- [ ] Replace the remaining private-study-derived test fixture in
      `test/run_tests.sh` with a fully synthetic label.
- [ ] Decide whether historical commit author email should remain public; use a
      GitHub noreply address for future public history if not.
- [ ] Confirm that no private fork retains history that is intended to be purged.
- [x] Keep `.env`, local audit studies, runtime images, caches and machine-specific
      state ignored.

The safety tooling lives in `scripts/public-release-audit.py`; operational steps
are in [`public-release.md`](public-release.md). Audit output redacts credential-
like values, session identifiers, private IPs and personal email rather than
copying sensitive values into CI logs.

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

The repository contains `examples/mean-shift/`, a small deterministic synthetic
analysis with no scientific-domain dependency.

Progress:

- [x] Deterministic analysis, expected output and self-check committed.
- [x] Direct synthetic result reproduced in CI.
- [x] Expected numerical output documented.
- [ ] Capture a complete `arh` transcript from a clean checkout.
- [ ] Package the final full-loop example as a self-contained study fixture.
- [ ] Record release-tag output hashes and execution receipts.
- [ ] Exercise the full ARH path in CI or a publication-candidate environment.
- [ ] Document the no-network/offline variant where practical.

The provider-free deterministic fixture is useful CI evidence, but it does not
replace the full path because a real eligible foreign-family review is one of the
framework's protocol steps.

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

A first engineering pilot now runs automatically in
`test/publication_evaluation.py`. On commit
`7b4be1d5c6e23f11177fcf4dfdb52340e856aba1`, **8/8 provider-free deterministic
scenarios passed** in a clean GitHub Actions checkout. The pilot is recorded in
[`../paper/pilot-results.md`](../paper/pilot-results.md). It is not the final
publication result: E6/E9 still need execution-controller artifacts and every
scenario must be rerun against the frozen release tag.

Progress:

- [x] Pre-specify deterministic failure injections.
- [x] Implement provider-free E1/E2/E3/E4/E5/E7/E8/E10 harness.
- [x] Run and preserve the first clean-CI pilot.
- [ ] Add release-candidate E6 task-failure artifact.
- [ ] Add release-candidate E9 interrupt/recovery artifact.
- [ ] Measure false refusals on valid controls.
- [ ] Measure direct vs Nextflow vs ARH wall-clock overhead with repetitions.
- [ ] Measure durable evidence volume/count.
- [ ] Freeze and run the separate stochastic review-role benchmark.
- [ ] Rerun all publication tables on the exact tagged release.

See [`evaluation-plan.md`](evaluation-plan.md) and
[`../paper/evidence-matrix.md`](../paper/evidence-matrix.md).

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

A ready-to-use record is in
[`independent-reproduction.md`](independent-reproduction.md). Treat every needed
intervention as a usability defect and record the fix. Preserve failed attempts;
do not report only the final successful rerun.

A second environment is more valuable than another large batch of unit tests.

## Phase 5 — manuscript

**Exit criterion:** every factual claim in the paper points to a repository
artifact, evaluation result or cited source.

A working draft lives in [`../paper/draft.md`](../paper/draft.md), with its claim-
to-evidence ledger in [`../paper/evidence-matrix.md`](../paper/evidence-matrix.md).
Keep the final short:

1. Summary / motivation
2. Statement of need and state of the field
3. Software design
4. Evaluation and research impact
5. Limitations
6. AI-use disclosure

For the first target, convert the evidence-complete working draft into the
Software Impacts Original Software Publication template rather than submitting
the generic Markdown structure directly. For JOSS later, retain the required
state-of-the-field, software-design, impact and AI-use sections and observe its
current 750–1750 word range.

## Evidence ledger for the paper

Do not write stronger prose than the evidence supports.

| Claim | Evidence available now | Still needed |
|---|---|---|
| protocol boundaries are mechanically checked | regression tests + 8/8 deterministic pilot subset | release-tag E1–E10 table |
| runs on HPC | observed Slurm success/failure | release-candidate public-safe Slurm artifact + independent environment |
| supports reproducible task environments | digest checks + container execution | clean public reproduction |
| can resume without chat history | ledger/status/context + pilot cold-resume case | independent usability test |
| cross-check roles improve error discovery | anecdotal/internal examples | controlled benchmark |
| useful beyond one domain/lab | architecture is domain-agnostic | second independent use case |

## Stop conditions

Do **not** delay the first paper for ambitious additions such as a knowledge
graph, MCP server, SHACL conversion, nanopublications or Nix/Guix integration.
Those may be useful later, but they do not close the principal publication gap.

The highest-value next work is:

1. finish sanitization and establish clean public history;
2. capture the full-loop synthetic example;
3. finish release-tag failure-injection and overhead measurements;
4. obtain one independent reproduction;
5. mint a citable release and submit the short software paper.
