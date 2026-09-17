# External research generators

Optional research agents that AutoResearch HPC may invoke as proposal engines.
Their source code and environments stay outside this repository. A configured
command receives a generated request file and an empty output directory through
the `{request}` and `{output}` placeholders.

Nothing is enabled by default. Enabling a generator is an operator decision:
these systems may call remote models, search the web and execute generated code.
Use environment variables or the external tool's own credential store for API
keys; never put secrets in a command template, which is retained in `run.json`.

```arh-config
generators = biomni ai-scientist-v2 agent-laboratory

evoke_timeout = 7200
evoke_max_output_bytes = 1048576

# Biomedical reasoning, analysis planning and hypothesis generation.
generator_biomni_enabled = false
generator_biomni_capabilities = biomedical-ideation biomedical-planning biomedical-interpretation
generator_biomni_source = https://github.com/snap-stanford/Biomni
generator_biomni_cmd =
generator_biomni_version_cmd =
generator_biomni_cwd =

# Open-ended machine-learning ideation and experiment-tree proposals.
generator_ai-scientist-v2_enabled = false
generator_ai-scientist-v2_capabilities = ml-ideation ml-experiment-design ml-tree-search
generator_ai-scientist-v2_source = https://github.com/SakanaAI/AI-Scientist-v2
generator_ai-scientist-v2_cmd =
generator_ai-scientist-v2_version_cmd =
generator_ai-scientist-v2_cwd =

# General literature review, planning, implementation and report drafting.
generator_agent-laboratory_enabled = false
generator_agent-laboratory_capabilities = literature-review research-planning report-drafting
generator_agent-laboratory_source = https://github.com/SamuelSchmidgall/AgentLaboratory
generator_agent-laboratory_cmd =
generator_agent-laboratory_version_cmd =
generator_agent-laboratory_cwd =
```

Command templates are parsed as arguments without shell evaluation. Supported
placeholders are `{request}`, `{output}`, `{project}`, `{iteration}` and
`{phase}`. Use a wrapper in the external installation when an upstream project
does not expose a one-request CLI. The wrapper is also where site-specific
container, Slurm and credential policy belongs.

