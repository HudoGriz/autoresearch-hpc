# AutoResearch HPC — agent contract

You are working inside an **AutoResearch HPC** project. This file is the
harness-agnostic contract. Codex, OpenCode, Cursor and Copilot can read it
directly; Claude Code reads it through `CLAUDE.md`, which symlinks here.

**Read `PROGRESS.md` first.** It is the authoritative project state and resume
point. Never reconstruct state from conversation history.

## The shape of the work

Work happens in numbered, **append-only** iterations under `iterations/`. One
iteration answers one question. A complete iteration contains:

```text
iterations/iterationN/
  CLAIM.json
  README.md                     pre-declaration, written BEFORE results
  PREDECLARATION.sha256         frozen declaration hash
  scripts/  resources/  metadata/
  results/report/iterationN_report.md
  logs/
  CROSSCHECK_<role>_<harness>_<ts>.md
  REVIEW_RESPONSE.md            your evaluation of each review finding
```

Project/runtime configuration lives under `.arh/config/`.

## The loop

```bash
arh claim -t "the question"          # atomic; returns N
arh new -n N                         # scaffold the pre-declaration
# complete every section first
arh gate predeclare -n N             # freezes the declaration hash
# write/run the workflow
arh submit iterations/iterationN/scripts/experiment.nf -n itN_01
arh ask --role adversary -n N        # foreign-family cross-check
arh gate results -n N                # verifies the declaration stayed frozen
arh ledger render && arh ledger check
```

`arh` finds the project by walking up from the working directory. If your
harness resets the shell's directory between commands, `export ARH_PROJECT=<study>`
so every command resolves the project from anywhere.

A review is bound to the report's sha256 and to every file under `results/`.
Write the report's *Cross-check* section as a pointer before `arh ask`, and put
your evaluation of the findings in `REVIEW_RESPONSE.md` at the iteration root.

To re-examine a result an iteration already produced, use the verification
track instead of silently revising the original:

```bash
arh verify new <object> -m re-implementation
arh verify gate <object>
```

## Rules that are not negotiable

1. **Claim before you create.** `arh claim` is the only way to take an iteration
   number. The directory creation is the concurrency lock. Never `mkdir -p` an
   iteration by hand.

2. **Pre-declare before you run.** Complete the iteration README before any
   result exists; `arh gate predeclare` freezes its hash. If the design changes,
   create a **new iteration**.

3. **Append-only. Never rewrite an earlier conclusion.** A correction is a new
   iteration that records what the earlier one got wrong. Superseded evidence
   remains intact.

4. **Immutable inputs are immutable.** Bind them read-only in containers. All
   output stays under the project root. Use `arh guard` before writing.

5. **Pin every scientific tool.** Use the declared task image / `arh run` path.
   A tool that can silently change underneath a run is not reproducibly pinned.

6. **Required review comes from a different configured model family.** `arh ask`
   enforces this. Cross-family review reduces one source of correlated error; it
   is evidence, not proof or independent scientific validation.

7. **Standing rules bind every conclusion.** They live in `rules/` and are
   enforced by `arh gate`.

8. **Record predictions, including wrong ones.** Do not revise a missed
   prediction after seeing the result.

## Reporting

- Report the quantity that was pre-declared, even if another number looks nicer.
- A null result is an **upper bound** with its detection basis, not an absence.
- Anything without appropriate orthogonal validation is a **candidate**.
- Use causal language only when the design supports it.
- State the detection limit in the units of the estimand.
- Report negative-control behaviour and failed arms.

## When the operator challenges a result

Treat the challenge as the trigger for a **new iteration**, not an instruction
to edit the old one. Record the challenge as motivation. The operator is an
adversary in this protocol by design.

## Style

- Shell: `set -euo pipefail`, quote expansions, explicit paths.
- Scripts: `itN_NN_description.{sh,py}`, deterministic seeds, sorted inputs.
- Tabular data is real TSV; parse deliberately.
- Write outputs only under the iteration that produced them.

## Before you finish

Run `arh status`. Anything showing `ALTERED`, or a required review that is
missing/ineligible, is an unfinished protocol violation rather than a formatting
detail.

## Default coding skill — Ponytail

For coding, debugging, refactoring and dependency decisions, use Ponytail in
full mode by default. Read `skills/ponytail/SKILL.md` once when starting coding
work; reuse that context rather than reloading it every turn. Prefer existing
code, standard libraries and installed tools before adding implementation.

Explicit user requirements, validation, immutable-input protection and every
research gate above take precedence over brevity. “Stop ponytail” or “normal
mode” disables this coding preference for the session; it does not change the
research protocol.
