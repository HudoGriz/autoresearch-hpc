# discovery-loop

[![test](https://github.com/<you>/discovery-loop/actions/workflows/test.yml/badge.svg)](https://github.com/<you>/discovery-loop/actions/workflows/test.yml)
[![protocol 0.1.0](https://img.shields.io/badge/protocol-0.1.0-blue)](PROTOCOL.md)
[![licence MIT](https://img.shields.io/badge/licence-MIT-green)](LICENSE)

A framework for running **automated research on HPC** as an auditable,
self-correcting loop — a set of skills and instructions that any agent harness
(Claude Code, Codex, OpenCode, Cursor, Copilot) can execute against the same
project, plus the tooling that enforces the rules.

It is domain-agnostic. Nothing here knows what you are studying. Scheduler,
container runtime, tool images, immutable inputs and standing rules are all
configured per project, in Markdown you edit.

## Why this exists

Autonomous discovery systems are good at generating results and bad at knowing
when they are wrong. The documented failure modes are consistent: agents pick
the analysis after seeing the answer, report a null as an absence, defend a
conclusion their own data contradicts, and pass their own review because a model
checking its own output verifies that the work *looks* correctly generated
rather than that it is correct.

None of those are fixed by a better model. They are fixed by a protocol:

| Mechanism | What it blocks |
|---|---|
| Claim before create | two agents silently occupying the same iteration |
| Pre-declaration, hash-frozen | choosing the analysis after seeing the answer |
| Append-only iterations | quietly rewriting history to look right |
| Standing rules as gates | causal language, bare nulls, missing controls |
| Cross-harness verification | a model passing its own reasoning errors |
| Gotchas as assertions | silent failures that exit zero |
| Detection limit required | thresholds discarding the events you seek |

## Install

```bash
git clone https://github.com/<you>/discovery-loop.git
cd discovery-loop
export PATH="$PWD/discovery-loop/bin:$PATH"
dl doctor
```

Requires bash, `awk`, `sed`, `python3` and `sha256sum`. Everything else —
SLURM, Apptainer, agent CLIs — is optional and configured per project.

## Quick start

```bash
dl init my-study && cd my-study
$EDITOR .dl/config/site.md        # scheduler, containers, images
$EDITOR .dl/config/project.md     # immutable inputs, standing rules
dl doctor

N=$(dl claim -t "Does X differ between A and B?")
dl new -n $N                      # scaffold the pre-declaration
$EDITOR iterations/iteration$N/README.md
dl gate predeclare -n $N          # freezes the hash — results now permitted

# ... write scripts/, then ...
dl submit iterations/iteration$N/scripts/it${N}_01_run.sh -n it${N}_01 -w
dl ask --role adversary -n $N     # cross-check with a foreign harness
dl gate results -n $N             # fails if the pre-declaration changed
dl ledger render && dl ledger check
```

Install harness-native wiring:

```bash
../discovery-loop/harness/install.sh . claude codex opencode
```

## What a project looks like

```
my-study/
  PROGRESS.md              the record — every agent reads this first
  AGENTS.md                the contract  (CLAUDE.md -> AGENTS.md)
  GOTCHAS.md               silent failure modes, each with an assertion
  rules/                   standing rules every iteration inherits
  .dl/config/              site.md · project.md · harnesses.md
  iterations/iterationN/
    CLAIM.json             who holds this number
    README.md              the pre-declaration
    PREDECLARATION.sha256  proof it predates the results
    scripts/ results/ logs/ resources/ metadata/
    CROSSCHECK_*.md        foreign-harness reviews
  verification/            independent re-examination of existing results
```

## Configuration

Config files are Markdown. Machine-readable settings live in fenced
` ```dl-config ` blocks as `key = value`; everything else on the page is
documentation for whoever reads it next.

**`.dl/config/site.md`** — this machine. `scheduler` is `slurm`, `pbs` or
`local`; `container_runtime` is `apptainer`, `singularity`, `docker` or `none`.
Declare images as `image_<name> = <path or docker:// URI>`. Moving a project to
a different cluster means editing this one file.

**`.dl/config/project.md`** — this study. Immutable input paths, which standing
rules apply, which sections a pre-declaration must carry.

**`.dl/config/harnesses.md`** — which agent CLIs exist, how to invoke each
non-interactively, and which **model family** each belongs to. Cross-checks are
refused between harnesses of the same family.

## Commands

| command | does |
|---|---|
| `dl init [dir]` | create a project |
| `dl claim -t TITLE` | atomically take the next iteration number |
| `dl new -n N` | scaffold the pre-declaration |
| `dl arm {new\|gate\|fate\|list}` | parallel sub-analyses that fail independently |
| `dl gate predeclare -n N` | check it, then freeze its hash |
| `dl gate results -n N` | verify the pre-declaration never changed |
| `dl gate rules FILE` | check a document against the standing rules |
| `dl ask --role R -n N` | cross-check with a foreign harness |
| `dl verify {new\|gate\|list}` | re-examine an object an iteration produced |
| `dl dag {init\|check\|freeze}` | reconstruct the path a result took |
| `dl replicate [run\|report]` | N agents re-implement from the DAG, blind to the code |
| `dl run IMAGE -- CMD` | run inside the configured container runtime |
| `dl submit SCRIPT` | submit through the configured scheduler |
| `dl guard PATH...` | assert paths are writable under the project |
| `dl ledger render \| check` | maintain the record |
| `dl status` | iterations, claims, gate state |
| `dl doctor` | check the environment against the config |
| `dl next` | what to do next, and why |
| `dl status --json` | machine-readable state, for calling `dl` from code |

## Blind replication from a DAG

The strongest check the framework offers. Reconstruct the path a result took,
freeze it, then have several agents re-implement it from that specification
alone:

```bash
dl dag init -n N && dl dag freeze -n N
dl replicate -n N --agents 3 --harnesses codex,opencode,claude
dl replicate report -n N
```

Each agent gets a sandbox holding the frozen DAG and the pre-declaration, and
**nothing else** — the original scripts are absent by construction, because an
agent that reads them reproduces their choices including their mistakes.

`dl dag check` fails on a node declared in the tables but absent from the graph:
an adjacency the argument assumes and the topology does not contain. It also
requires §4 to state how many paths exist versus how many were reported — the
multiple-testing denominator.

The report surfaces **disagreement**, which is the evidence: divergent values
mark decisions the DAG left open, contested set membership is named element by
element, and the ambiguity count measures the specification rather than the
result. Agreement is not treated as confirmation — models fail in correlated
ways, and a unanimous answer can be unanimously wrong.

## Cross-check roles

`dl ask --role <role> -n N` composes a prompt from the role, the frozen
pre-declaration and the report, then dispatches it to a foreign harness.

- **`adversary`** — assume the conclusion is wrong; find out why.
- **`reimplementer`** — build it from the written spec alone, never reading the
  original code. Every ambiguity it had to resolve is a finding.
- **`estimand-auditor`** — does the test measure the quantity the question asks
  about? Catches the error class where every step is correct and the number
  answers a different question.
- **`gotcha-scanner`** — check the run against recorded silent failure modes.

A verdict is evidence, not a ruling. Evaluate each finding on its merits and
record the rejections with reasons.

## Skills

`skills/` holds portable skill definitions — `iterate`, `arms`, `verify`,
`cross-check`, `replicate`, `ledger` — installed into `.claude/skills/` for Claude Code and referenced by
`opencode.json` for OpenCode. Codex and Cursor read `AGENTS.md` directly.

## Tests

```bash
test/run_tests.sh          # 136 checks, no cluster or network needed
KEEP=1 test/run_tests.sh   # keep the scratch project for inspection
```

The suite builds a real project, runs a generic toy analysis through the whole
loop, and asserts the protocol actually bites: concurrent claims never collide,
an unfilled pre-declaration is rejected, results before pre-declaration are
rejected, a README edited after freezing is caught, causal language and bare
nulls are refused, and same-family cross-checks are blocked.

## Extending

**A new standing rule** — drop a file in `rules/`, declare `id`, `severity`,
`applies` (`predeclaration` and/or `report`), and `forbid`/`requires` regexes in
its `dl-config` block. Name it in `project.md`.

**A new harness** — three keys in `harnesses.md` (`harness_<n>_cmd`,
`harness_<n>_family`, and the name in `harnesses`), plus native config under
`harness/` if it needs any.

**A new scheduler or container runtime** — add a case to `lib/scheduler.sh` or
`lib/container.sh`. Both are small and have one job each.

## Status

Working, tested, and pre-1.0: the protocol version is `0.1.0` and the config
format may still change. `schema/` types claims, findings and cross-checks —
generating the ledger from typed findings rather than maintaining it by hand is
the next step.

## Documentation

| file | what it is |
|---|---|
| [`PROTOCOL.md`](PROTOCOL.md) | the normative spec — what conformance means |
| [`AGENTS.md`](AGENTS.md) | the contract an agent reads on entering a project |
| [`docs/related-work.md`](docs/related-work.md) | what this is not, and where the design came from |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | the bar for a change, and shell style |
| [`CHANGELOG.md`](CHANGELOG.md) | versioned protocol changes |

## Citing

`CITATION.cff` — GitHub renders a "Cite this repository" button from it.

## Licence

MIT — see [`LICENSE`](LICENSE).
