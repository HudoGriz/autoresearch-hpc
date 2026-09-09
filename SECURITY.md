# Security

## Scope

`discovery-loop` runs commands you write, submits jobs to your scheduler, and
dispatches prompts to agent CLIs you have configured. It grants no privilege of
its own. The security-relevant surface is small and worth stating plainly.

**`dl guard` and the container bind policy are safety rails, not a sandbox.**
They stop an agent writing outside the project root or into declared immutable
inputs. They do not contain a deliberately hostile process, and are not intended
to.

**Cross-check prompts carry your project's contents** — the pre-declaration and
report — to whichever CLI you configured. That CLI decides where it sends them.
Do not configure a harness you would not send the project to.

**Agent output is untrusted input.** A cross-check record is text written by a
model. Never execute it, and read `VERDICT:` as evidence rather than as a ruling.

## Reporting

Report suspected vulnerabilities through GitHub's private advisory form
("Security" → "Report a vulnerability") rather than a public issue. Please
include the version (`dl --version`) and a minimal reproduction.

Things that are **not** vulnerabilities: an agent producing a wrong scientific
conclusion, a gate that a determined author can satisfy with bad-faith prose, or
`container_runtime = none` being unreproducible. The first two are what the
cross-check roles and human review are for; the third is documented.
