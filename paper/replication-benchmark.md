# Replication benchmark: methods and interim results

> **Status:** work in progress. The benchmark is still running. This document
> reports an interim snapshot; it is not a final performance estimate.

## Question

The benchmark asks whether AutoResearch HPC (`arh`) iteration loops, operated by
coding agents on an existing HPC cluster, can converge on published results from
real studies while leaving a complete, auditable record of the path taken. These
are separate outcomes. A published value may remain unmatched even when the
protocol correctly preserves the plan, executions, failed attempts, reviews and
operator challenges. Conversely, a numerical match does not establish that the
analysis is scientifically valid or independently reproduced.

## Design

Each of the twelve studies is isolated in its own directory, with a separate ARH
clone and initialized project. Inputs are checksummed, declared immutable and
mounted read-only for compute tasks. The producing agent receives a study brief
containing the research question, claim definitions, units, required uncertainty,
data description and a methods-level summary, but no published numerical results.

Published targets and tolerance bounds are held by the operator outside the study
trees. After a round, a grader reads the latest concluded iteration's structured
claims and returns only `MATCH`, `MISS` or `MISSING` for each claim. It does not
reveal a target, direction or distance. A challenge therefore starts a new
append-only iteration rather than changing the earlier one. Agents are instructed
not to search for the paper's reported results, and web tools are disabled where
the harness permits. This is cooperative blinding, not an operating-system
security boundary; the final analysis includes a transcript audit for possible
target access, web lookup or memorized values.

A round is one producer session and ends when at least one new iteration passes
`arh gate results`, or when the producer records that it is blocked. The round
driver starts the producer, preserves its session record, invokes grading and
writes the next operator note. Provider usage-limit attempts do not count as
rounds. Every concluded iteration must pass the results gate with a review from a
different configured model family. Producers and reviewers are pinned to Codex
`gpt-6-astra` at `xhigh` reasoning effort and Claude `claude-opus-5` at default
effort. The initial assignment alternates producer family by study; the
transcriptomics study was switched from Codex to Claude after provider refusals,
with Codex retained as reviewer.

A study stops when all primary claims match, after six rounds, after two
consecutive rounds without a newly concluded iteration, or after 48 hours. A
producer session is capped at six hours. Matching tolerances were frozen by
estimand before agents ran: depending on the study, these use a published
confidence interval, a relative tolerance, a published range, an absolute
tolerance for deterministic re-analysis, a published uncertainty interval, or
an exact direction. Results are descriptive; the study set is not used for
statistical inference about agents.

## Study set

The original set combined six external, highly cited studies with public data
and three in-house clinical studies. The external studies span cancer genomics,
social psychology, cosmology, a stroke trial, labour economics and ecology. This
mix exercises survival models, analyst-choice distributions, likelihood fitting,
randomised-trial outcomes, difference-in-differences and Bayesian trend models.
The in-house set adds an imaging study in clinical genetics, a long-read genetics
study in haematology and a paediatric epigenetics study. Only pseudonymised,
derived inputs are exposed to agents for these studies.

An amendment added three highly cited public bioinformatics studies—population
variant genomics, bulk transcriptomics and single-cell transcriptomics—so the
benchmark includes realistic genomics workflows as well as compact public
datasets. Amendments remain appended to the frozen design, and each round records
the framework commit it used. This matters because fixes found during the
benchmark were incorporated into later rounds; the benchmark therefore evaluates
a documented sequence of versions rather than one unchanged binary.

## Interim results

At the current central-ledger snapshot, three of the twelve studies have
converged. Two studies stalled when headless producer sessions exited with
unfinished background work; their records were retained and they were queued to
resume. One study stopped
when the agent correctly refused to recode an undefined primary-outcome value.
That scientific acceptance failure was accepted as correct protocol behaviour and
the study was re-queued with an operator note that disclosed no target. One study
encountered a provider content filter on a public transcriptomics analysis. The
remaining studies are running, queued or awaiting inputs.

| ID | Field and design | Interim status |
|---|---|---|
| 01 | cancer genomics; survival analysis after immunotherapy | converged |
| 02 | social psychology; many-analyst association study | stalled after two rounds; queued to resume |
| 03 | cosmology; likelihood fit with statistical and systematic covariance | converged |
| 04 | in-house clinical genetics; dental-radiograph measurements | awaiting its input table; not started |
| 05 | in-house haematology; long-read genetics | awaiting its reference findings; not started |
| 06 | in-house paediatric epigenetics; region-level methylation analysis | converged |
| 07 | stroke trial; factorial randomised comparison | scientific acceptance failure accepted as correct behaviour; queued to resume |
| 08 | labour economics; difference-in-differences | stalled after two rounds; queued to resume |
| 09 | ecology; Bayesian biomass-trend model | queued; incomplete |
| 10 | population genomics; per-genome variant counts | queued; incomplete |
| 11 | bulk transcriptomics; differential expression | refused by a provider content filter; re-queued with the other producer family |
| 12 | single-cell transcriptomics; reference-based cell classification | running |

These outcomes do not show that agents generally replicate published studies.
They show, so far, that successful matches, scientific refusals, orchestration
failures and provider failures can all remain visible in the same protocol
record. The benchmark is still running, and studies 02, 04, 05, 07, 08, 09, 10,
11 and 12 are incomplete in that ledger snapshot.

`TODO-EVIDENCE:` when the benchmark finishes, replace this snapshot with the
final per-study claim status, rounds and iterations to first match, wall-clock and
agent-session time, Slurm jobs, model calls, token or cost measurements, review
outcomes, gate refusals, arm fates and the completed blinding audit.

## Framework defects surfaced by the benchmark

Running the protocol with real headless agents exposed six framework or operating-
contract defects. These are a benchmark result, not housekeeping omitted from the
evaluation. Each was recorded in the central ledger and linked to a fix commit.

| # | Observed problem | Resolution recorded in the ledger |
|---:|---|---|
| 1 | The shipped harness template overrode the review timeout with 180 seconds, risking the loss of review rounds to timeouts. | Set study timeouts to 900 seconds; fixed in `3c6ae9a`. |
| 2 | Five site-dependent hardening tests failed or errored when the site-test variable was unset instead of explaining that they were skipped. | The submission tests now skip with a message in `1733388`. |
| 3 | A Codex producer inherited Claude environment markers and was misattributed in its claim; the provenance record did not show how the identity was inferred. | The driver clears inherited harness state and sets the producer explicitly; `271d48e` records the identity source and warns on mismatch. |
| 4 | Non-interactive Claude producers backgrounded long work and exited while waiting for notifications that could never arrive, losing two rounds in each of two studies. | The driver requires foreground waiting and disables background tasks; `8bf4b8d` adds `arh wait` and unattended-session rules. |
| 5 | A provider safety classifier refused two producer sessions for a legitimate public transcriptomics analysis, while the foreign-family rule left no equivalent reviewer path. | The producer family was switched; `8bf4b8d` records content refusal separately, does not spend a review round on it and supports configured verifier fallbacks. |
| 6 | Updating the framework did not refresh the copies of `AGENTS.md` and skills inside existing projects, so running agents continued to read an obsolete contract. | `8bf4b8d` adds migration of the contract with backup and a diagnostic warning; the driver migrates before each round. |

The fixes changed the framework during the benchmark and are therefore recorded
as deviations, with the commit used by every round. This limits comparisons
between early and late studies, but preserves the more important fact for this
evaluation: exercising the protocol under realistic agent and scheduler
conditions revealed faults that unit and pilot tests had not exposed.

## Interpretation and limitations

The benchmark tests whether a difficult and sometimes unsuccessful replication
path remains inspectable. It does not test autonomous scientific discovery, and
convergence is not proof of correctness. Famous papers may have been represented
in model training data; blinding is cooperative; the operator wrote the briefs,
matching rules and grader; and the grader is not independent of the operator.
Provider limits and filters affect throughput, while fixes introduced during the
run make the system under test non-stationary. Every study, including stalls and
failures, will remain in the final report.
