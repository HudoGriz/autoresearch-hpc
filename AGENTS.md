# Automated discovery loop — agent contract

You are working inside a **discovery-loop** project. This file is the contract.
It is harness-agnostic: Codex, OpenCode, Cursor and Copilot read it directly,
Claude Code reads it through `CLAUDE.md`, which symlinks here.

**Read `PROGRESS.md` first.** It is the authoritative project state and the
resume point. Never reconstruct state from conversation history.

## The shape of the work

Work happens in numbered, **append-only** iterations under `iterations/`. One
iteration answers one question. A complete iteration contains:

```
iterations/iterationN/
  CLAIM.json                    written by `dl claim` — do not hand-edit
  README.md                     the pre-declaration, written BEFORE any result
  PREDECLARATION.sha256         the frozen hash — proof the README predates results
  scripts/  slurm/  resources/  metadata/
  results/report/iterationN_report.md
  logs/
  CROSSCHECK_<role>_<harness>_<ts>.md
```

## The loop

```bash
dl claim -t "the question"          # atomic; returns N. Never mkdir by hand.
dl new -n N                         # scaffold the pre-declaration
#   ... complete every section of README.md ...
dl gate predeclare -n N             # freezes the README hash. Results are now permitted.
#   ... write scripts/, run them ...
dl submit iterations/iterationN/scripts/run.sh -n itN_01
dl ask --role adversary -n N        # cross-check with a foreign harness
dl gate results -n N                # verifies the pre-declaration never changed
dl ledger render && dl ledger check
```

## Rules that are not negotiable

1. **Claim before you create.** `dl claim` is the only way to take an iteration
   number. Two agents once created the same iteration directory eleven minutes
   apart; `mkdir` is the lock precisely so that cannot recur. Never `mkdir -p`
   an iteration — on a live directory it is silent.

2. **Pre-declare before you run.** The README is written before any result
   exists, and `dl gate predeclare` freezes its hash. Choosing an analysis after
   seeing the answer is the failure this prevents, and it is invisible in the
   output. If the design must change, that is a **new iteration**.

3. **Append-only. Never revise an earlier iteration to change its conclusion.**
   A correction is a new iteration that states what the earlier one got wrong.
   The superseded files stay exactly as they were. The record of having been
   wrong is part of the result.

4. **Immutable inputs are immutable.** Bound read-only in every container. All
   output stays under the project root. Use `dl guard` before writing.

5. **Pin every tool.** Run through `dl run <image> -- cmd`, with the image
   declared in `.dl/config/site.md`. An unpinned tool means the run is not
   reproducible, whatever the numbers say.

6. **Verification comes from a different model family.** `dl ask` enforces this.
   A model reviewing its own output checks whether the work *looks* correctly
   generated — it reproduces the reasoning errors it made while generating.

7. **Standing rules bind every conclusion.** They are in `rules/`, enforced by
   `dl gate`. They constrain what you may *claim*, not what you may compute.

8. **Record predictions, including wrong ones.** §7 of every pre-declaration is
   a prediction. When it misses, the report says so. Do not revise it.

## Reporting

- Report the number you pre-declared, even when another number is more attractive.
- A null result is an **upper bound**, never an absence. State what you could
  have detected.
- Anything without orthogonal validation is a **candidate**, not a finding.
- Say *associated with*, not *causes*, unless the design supports the stronger word.
- State the detection limit in the units of the estimand.
- Negative controls that fired mean you have diagnosed the pipeline, not found a result.

## When the operator challenges a result

Treat the challenge as the trigger for a **new iteration**, not as an
instruction to edit the old one. Record the challenge verbatim in the new
iteration's README as its motivation. The operator is an adversary in this
system by design, and their objections are part of the scientific record.

## Style

- Shell: `set -euo pipefail`, quote expansions, explicit paths.
- Scripts: `itN_NN_description.{sh,py}`, deterministic seeds, sorted inputs.
- Tabular data is real TSV; parse with `awk -F'\t'`, never shell `read`.
- Write outputs only under the iteration that produced them.

## Before you finish

Run `dl status`. Anything showing `ALTERED`, or a report without a cross-check,
is an unfinished protocol violation — not a formatting detail.
