# Harness configuration

Which agent CLIs are available, how to invoke each non-interactively, and which
model family each belongs to.

The model family matters. A model reviewing its own output can reproduce the
same reasoning errors, so `arh ask` refuses a verification role from the same
configured family unless `--same-family` explicitly records a weaker check.

## Invocation

Each harness declares a command template. `{prompt}` is substituted with the
composed prompt; `{cwd}` with the working directory.

| harness | non-interactive form |
|---|---|
| `claude` | `claude -p "…"` |
| `codex` | `codex exec --skip-git-repo-check "…"` |
| `opencode` | `opencode run "…"` |
| `gemini` | `gemini -p "…"` |

## Roles

`arh ask --role <role>` composes a prompt from
`skills/cross-check/roles/<role>.md`. Shipped roles are `adversary`,
`reimplementer`, `estimand-auditor` and `gotcha-scanner`.

```arh-config
harnesses = claude codex opencode

harness_claude_cmd      = claude -p {prompt}
harness_claude_family   = anthropic

harness_codex_cmd       = codex exec --skip-git-repo-check {prompt}
harness_codex_family    = openai

harness_opencode_cmd    = opencode run {prompt}
harness_opencode_family = mixed

harness_gemini_cmd      = gemini -p {prompt}
harness_gemini_family   = google

producer   = claude
verifier   = codex

ask_timeout = 180
ask_max_input_bytes = 24000
ask_max_output_bytes = 8000
ask_output_words = 500
ask_max_rounds = 2
```

Command templates are parsed as quoted arguments without shell evaluation; use
a wrapper script for pipelines or environment setup. Reviews from `mixed` or
`unknown` families cannot satisfy the required foreign-family gate. An unchanged
eligible review is reused without a model call. Deterministic execution, status
and context assembly do not call a model.
