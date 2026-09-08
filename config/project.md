# Project configuration

Everything about **this study**: what is immutable, where the record lives, and
which standing rules every iteration inherits. Site details belong in
`site.md`; this file survives a move between clusters.

## Paths

`immutable_inputs` is a space-separated list of directories that must never be
written to. `dl guard` aborts on any write path outside the project root or
inside one of these, and `dl run` binds each of them read-only.

## Standing rules

`rules` names the files under `rules/` that every iteration inherits. Each rule
is a Markdown file with a `dl-config` block declaring how it is enforced. Rules
are *conclusion boundaries* — they constrain what an iteration is allowed to
claim, not what it is allowed to compute.

Add project-specific rules by dropping a new file in `rules/` and naming it here.

## Pre-declaration

`required_sections` lists the headings an iteration `README.md` must contain
before any result may be recorded. `dl gate predeclare` enforces this, then
freezes the file's hash; `dl gate results` fails if the README changed after
results appeared. This is preregistration enforced mechanically — it is the
core of the protocol, so shorten this list only deliberately.

```dl-config
ledger            = PROGRESS.md
iterations_dir    = iterations
verification_dir  = verification

# Directories that must never be written to (space-separated, absolute).
immutable_inputs  =

# Standing rules inherited by every iteration.
rules             = association-not-causation null-is-upper-bound negative-controls-required detection-limit-stated

# Headings an iteration README must carry before results are accepted.
required_sections = Question Estimand Instrument Acceptance criteria Negative controls Detection limit Prediction

# Refuse to conclude an iteration whose claims were never cross-checked
# by a harness from a different model family.
require_crosscheck = true
```
