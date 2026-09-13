# Evaluation plan for a publication release

This is a **pre-specified evaluation plan** for the software paper. It separates
what AutoResearch HPC is designed to enforce from broader claims about scientific
correctness that the software cannot guarantee.

## Research questions

**RQ1 — Enforcement.** Does AutoResearch HPC detect or prevent the protocol
violations it claims to make mechanical?

**RQ2 — Recoverability.** Can a project be resumed from files on disk without
reconstructing state from an earlier model conversation?

**RQ3 — Portability.** Can the same declared analysis run on at least two
execution environments while preserving the same protocol record?

**RQ4 — Cost.** What wall-clock and workflow overhead does the protocol layer add
relative to running the underlying analysis directly?

**RQ5 — Review utility.** For a fixed set of injected analysis defects, how often
do the shipped cross-check roles identify the defect, and how often do they
raise an unsupported objection?

RQ5 is intentionally separate from RQ1–RQ4. Deterministic gates can be tested as
software behavior; model review is stochastic evidence and must be measured as
such.

## Systems to compare

Use the same small synthetic analysis in both conditions.

### Baseline

A coding agent (or scripted equivalent) + Nextflow + local/Slurm execution,
without AutoResearch HPC protocol enforcement.

### AutoResearch HPC

The identical analysis executed inside a normal `arh` iteration, with the
pre-declaration, gate, run receipt, cross-check and ledger enabled.

The baseline is not intended to make another tool look bad. Its purpose is to
show which behavior comes from Nextflow/container execution and which behavior
is added by the protocol layer.

## Deterministic failure-injection matrix

Each scenario should be implemented as a small test fixture and run from a clean
checkout. Repeat concurrency tests enough times to expose races; deterministic
single-process tests need only enough repetitions to establish stability.

| ID | Injected condition | Expected result under ARH | Primary measure |
|---|---|---|---|
| E1 | leave a required pre-declaration field unfilled | pre-declaration gate refuses | detected / not detected |
| E2 | create a result before freezing the declaration | pre-declaration gate refuses | detected / not detected |
| E3 | edit frozen declaration after execution | result gate refuses altered hash | detected / not detected |
| E4 | concurrently claim the next iteration | unique iteration numbers | collisions / attempts |
| E5 | write to declared immutable input | guard/container policy refuses | rejected / allowed |
| E6 | task exits non-zero | controller reports failure and preserves receipt/logs | status + retained evidence |
| E7 | request review from producer model family | foreign-family requirement refuses by default | detected / not detected |
| E8 | modify evidence after a successful review | old review becomes ineligible | detected / not detected |
| E9 | interrupt a running submission | signal reaches controller/task and lock is released or recoverable | cleanup correctness |
| E10 | resume in a fresh shell with no chat history | `arh status`, `arh next` and ledger identify the state | correct next action |

The provider-free E1/E2/E3/E4/E5/E7/E8/E10 subset is implemented in
`test/publication_evaluation.py`. E6/E9 are captured separately through
`test/publication_execution_evaluation.py` because they require the configured
Nextflow/container integration environment. Both write machine-readable JSON and
must be rerun on the exact publication release tag.

Report failures as failures. Do not silently exclude scenarios that expose a bug.

## Reproducibility fixture

Use `examples/mean-shift/` as the publication fixture. It contains only synthetic
data and a deterministic exact sign-flip test.

For each environment record:

- OS and architecture;
- `arh --version`;
- Nextflow version;
- scheduler and version;
- Singularity/Apptainer version;
- task-image digest;
- commit/tag under test;
- expected-result hash and observed-result hash;
- total setup time and execution time.

Target environments:

1. GitHub Actions / local executor / Apptainer;
2. one real Slurm environment;
3. ideally one independent external environment not administered by the main
   developer.

## Overhead measurement

Use the same synthetic task and measure separately:

- direct analysis runtime;
- Nextflow-only runtime;
- ARH pre-declaration/gating time;
- ARH submission/controller time;
- cross-check latency (reported separately because it depends on an external
  provider and is not deterministic);
- bytes of durable protocol evidence written per iteration.

For very short toy tasks, startup dominates. Therefore report absolute time and
percentage overhead, and repeat the timing with a task lasting roughly 30–60 s
so the fixed overhead is visible in context.

## Cross-check benchmark

Do not claim that a foreign model family is independent scientific validation.
The benchmark asks a narrower question: can the supplied review roles identify
known defects in supplied artifacts?

The first synthetic corpus is frozen under
`benchmarks/review-corpus/v0.1/`. It contains six single-defect cases and three
clean controls. Reviewer-visible artifacts (`cases.json`) and hidden ground truth
(`labels.json`) are deliberately separate, and CI checks the corpus structure so
labels cannot accidentally appear as visible case fields.

Version 0.1 covers:

- paired design analysed as independent groups;
- selection threshold chosen after observing the result;
- negative control fires but conclusion ignores it;
- candidate set has the right size but wrong members;
- unit/denominator mismatch in the estimand;
- declared detection limit not supported by the analysis;
- three clean controls with no injected defect.

For each role/model combination, run every case at least three times with a
frozen model/provider configuration. Preserve each raw response and harness
metadata. Report:

- true-positive rate by defect class;
- false-positive rate on clean cases;
- abstention/qualified verdict rate;
- agreement between repeated runs;
- prompt/output budget used where available;
- provider failures and latency separately from accuracy.

Primary scoring remains case-level. A defective case is a true positive when the
response identifies the labelled defect or an equivalent formulation. A clean
case is a false positive when the response asserts a material defect that is not
present in the visible evidence. Additional plausible findings require blinded
human adjudication and do not alter v0.1 ground truth in place.

Preserve the exact frozen prompts, model/provider identifiers available to the
harness, and raw review records. Once any model has been evaluated against v0.1,
do not tune those cases after seeing results. Corrections create a new corpus
version.

## Independent usability test

The external tester should receive only:

1. repository URL;
2. one sentence asking them to install the software and reproduce the public
   example;
3. permission to report anything confusing.

Do not coach them through the setup unless they are blocked. Record every
intervention separately; an intervention means the README or diagnostics were
insufficient for that environment.

Suggested outcomes:

- setup success (yes/no);
- time to passing `arh doctor`;
- number of undocumented interventions;
- full example reproduction (yes/no);
- subjective setup difficulty on a simple 1–5 scale;
- free-text problems encountered.

## Publication acceptance criteria

The short paper is ready to submit when all of the following are true:

- deterministic failure injections are automated and pass on the release tag;
- the synthetic example reproduces from a clean public checkout;
- one real Slurm run is captured against the release candidate;
- at least one independent user has attempted setup from documentation alone;
- every paper claim is traceable to a test, run artifact, benchmark result or
  citation;
- known negative results and retained limitations are reported alongside the
  successful cases.
