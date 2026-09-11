# Security

## Scope

AutoResearch HPC runs commands you write, submits jobs to your scheduler, and
dispatches prompts to agent CLIs you configure. It grants no privilege of its
own.

**`arh guard` and the container bind policy are safety rails, not a sandbox.**
They protect normal workflows from writing outside the project root or into
declared immutable inputs. They do not contain deliberately hostile code.

**Cross-check prompts can carry project contents** to the configured external
agent CLI. That CLI/provider decides where the supplied context is processed.
Do not configure a harness you would not send that material to.

**Agent output is untrusted input.** A cross-check record is model-generated
text. Never execute it; treat `VERDICT:` as evidence rather than a ruling.

Local hashes detect later changes but are not trusted timestamps. A container
digest identifies bytes but does not prove deterministic execution or scientific
validity. Blind-replication directories are cooperative unless the operating
system separately enforces access restrictions.

## Reporting

Report suspected vulnerabilities through GitHub's private advisory form rather
than a public issue. Include `arh --version` and a minimal reproduction.

A wrong scientific conclusion, a gate satisfied with bad-faith prose, or
`container_runtime = none` being unreproducible are limitations of the research
protocol rather than privilege-escalation vulnerabilities; they should still be
reported when they expose a protocol defect.
