# External research generators

AutoResearch HPC can now **evoke** a specialist research system without copying
that system into this repository or letting it bypass the protocol. The
integration surface is deliberately small:

```text
iteration context -> request.md -> external command -> response + artifacts + run.json
```

The external installation, environment, models and credentials remain
operator-owned. Its output is advisory and lands under
`metadata/evocations/`, outside `results/`.

## Selected integrations

| Generator | Why it is first-class | Best phase | Important boundary |
|---|---|---|---|
| [Biomni](https://github.com/snap-stanford/Biomni) | The strongest domain fit for biomedical hypotheses, analysis planning and interpretation | ideate, plan, interpret | Large environment and data lake; generated code currently has full process privileges |
| [AI Scientist v2](https://github.com/SakanaAI/AI-Scientist-v2) | A concrete local pipeline for ML ideation and experiment-tree search | ideate, plan, implement | ML-focused, GPU-oriented and explicitly intended for a controlled sandbox |
| [Agent Laboratory](https://github.com/SamuelSchmidgall/AgentLaboratory) | A broad local literature-review, experimentation and report workflow | plan, implement, write | Its end-to-end outputs still need ARH pre-declaration and execution provenance |

These were selected because each has an official open repository and a local
invocation boundary that an operator can pin and wrap.

[AgentRxiv](https://github.com/AgentRxiv/AgentRxiv.github.io) is a collaborative
publication/exchange layer rather than a bounded local worker. Robin and Kosmos
are hosted research services. They remain valid composition targets, but they
are not enabled as built-in command adapters: publication and hosted-service
data egress require a separate policy decision. A site can still add any of
them as a custom entry in `generators.md`.

## Configure, do not install

`arh init` writes `.arh/config/generators.md` with all three integrations
disabled. Install the chosen upstream project independently, pin it there, and
provide a small site-owned wrapper with this contract:

1. argument 1 is the path to the generated Markdown request;
2. argument 2 is a newly created output directory;
3. the final human-readable response is written to stdout;
4. diagnostics go to stderr and failure returns non-zero.

Then configure its command. For example:

```arh-config
generator_biomni_enabled = true
generator_biomni_cmd = /shared/agents/biomni/bin/arh-biomni {request} {output}
generator_biomni_version_cmd = /shared/agents/biomni/bin/python -m pip show biomni
generator_biomni_cwd = /shared/agents/biomni
```

The wrapper is intentionally site-owned. Upstream interfaces differ: Biomni is
primarily a Python API, AI Scientist v2 uses ideation and launch scripts, and
Agent Laboratory consumes experiment YAML. Keeping that translation beside the
pinned external installation prevents this repository from carrying stale
copies of their code or pretending their environments are interchangeable.

Command templates are split into arguments without a shell. They support
`{request}`, `{output}`, `{project}`, `{iteration}` and `{phase}`.
Do not put an API key in the command: the template is retained in `run.json`.

## Use

List the registry and inspect the exact request before any external call:

```bash
arh evoke list
arh evoke show biomni
arh evoke biomni -n 4 --phase plan --prompt request.md --dry-run
```

A real invocation requires both the configuration switch and an explicit
per-run acknowledgement:

```bash
arh evoke biomni -n 4 --phase plan --prompt request.md --allow-external
```

A successful record contains:

```text
iterations/iteration4/metadata/evocations/<timestamp>-biomni.<id>/
├── request.md
├── response.md
├── stderr.log          # removed when empty
├── run.json
└── artifacts/          # files written by the external wrapper
```

`run.json` records the request and configuration hashes, source URL, command
template, external version when available, working directory, timestamps and
exit status. Timeout and combined stdout/stderr limits are set globally or per
generator in `generators.md`.

## Trust and scientific boundary

`--allow-external` is not a sandbox. Use a container, disposable VM or batch
wrapper when the upstream system executes generated code. Restrict filesystem
mounts and network access at that boundary. Send the minimum context; do not
include patient identifiers, credentials or raw confidential data merely
because the study itself lives on local HPC.

Generator output does not become evidence by being recorded. If a proposal is
adopted, cite its evocation directory in the iteration, move only the selected
implementation into `scripts/`, and run it through pinned ARH execution.
Required foreign-family review still uses `arh ask`.

