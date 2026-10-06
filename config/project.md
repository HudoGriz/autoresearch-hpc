# Project configuration

Everything about **this study**: what is immutable, where the record lives, and
which standing rules every iteration inherits. Site details belong in
`site.md`; this file survives a move between clusters.

## Paths

`immutable_inputs` is a space-separated list of directories that must never be
written to. `arh guard` aborts on any write path outside the project root or
inside one of these, and `arh run` binds each of them read-only.

## Sealed inputs

`sealed_inputs` lists held-out data that only a frozen confirmation may read:
an external validation sample, a test split, a truth set kept for the end.
`arh submit` covers each sealed path with an empty read-only mount, and refuses a
workflow, params file or iteration script that names one, unless the iteration
has a valid `FREEZE.json` (`arh freeze -n N MODEL THRESHOLDS ...`). A run of
such an iteration reads them read-only and appends the read to
`.arh/unseals.tsv`, so every use of the held-out data is on record. `arh run`
never reads them, and `arh guard` refuses writes to them. Do not put an
immutable input inside a sealed one; a sealed path inside a broader immutable
input is covered as well.

## Standing rules

`rules` names files under `rules/` that every iteration inherits. Each rule is a
Markdown file with an `arh-config` block declaring how it is enforced. Rules are
conclusion boundaries — they constrain what an iteration may claim, not what it
may compute.

## Pre-declaration

`required_sections` is a comma-separated list of headings an iteration README
must contain before any result may be recorded. `arh gate predeclare` enforces
this, then freezes the file hash; `arh gate results` fails if it changed after
results appeared.

```arh-config
ledger            = PROGRESS.md
iterations_dir    = iterations
verification_dir  = verification

immutable_inputs  =
sealed_inputs     =
rules             = association-not-causation null-is-upper-bound negative-controls-required detection-limit-stated
required_sections = Question, Estimand, Instrument, Acceptance criteria, Negative controls, Detection limit, Prediction
require_crosscheck = true
```
