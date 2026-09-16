# Paper workspace

`draft.md` is a **venue-neutral working manuscript**, not yet a submission file.
It is intentionally conservative: placeholders marked `TODO-EVIDENCE` identify
claims that require public evaluation evidence before submission.

## Near-term path

The current plan is to prepare the software and evidence for a short
**Software Impacts** submission first. Adapt the final text to that journal's
required Original Software Publication template only after the public release
candidate and evaluation artifacts exist.

`software-impacts.md` is the working copy in that template's structure (abstract,
keywords, code metadata C1–C9, body sections). It mirrors `draft.md`; update both
together until submission.

## The replication benchmark and this repository

`replication-benchmark.md` describes an evaluation that is **run outside this repository**, and
the boundary is deliberate. The benchmark's operational record — study trees, briefs, the private
target values, the grader, operator notes and host paths — is held separately so that a published
target can never reach an agent through the repository, and so that a public release carries no
part of it. Three of the studies are the authors' own clinical work on human data; those are
referred to here by field and design only.

What may cross into this repository is the write-up itself: prose, aggregate outcomes and counts
that carry no path, no study identifier and no target value. Framework defects the benchmark finds
cross the other way, as ordinary fixes with tests. Keep it that way when updating this section.

## JOSS path

The same draft already follows the major JOSS content headings: summary,
statement of need, state of the field, software design, research impact, and AI
usage disclosure. JOSS is a later target because its current screening requires
at least six months of public active development plus demonstrated research
impact.

Before any submission:

- replace all `TODO-EVIDENCE` markers with evidence or remove the claim;
- add final authors, affiliations, acknowledgements and funding;
- add a proper bibliography;
- cite the immutable software release/DOI;
- report the failure-injection evaluation and independent reproduction;
- verify the target venue's current author instructions again.

The publication roadmap is in [`../docs/publication-plan.md`](../docs/publication-plan.md).
