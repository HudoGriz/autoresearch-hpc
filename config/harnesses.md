# Harness configuration

Which agent CLIs are available, how to invoke each non-interactively, and which
model family each belongs to.

The model family matters. A model reviewing its own output checks whether the
work *looks* correctly generated, not whether it is correct — it reproduces the
reasoning errors it made while generating. So `dl ask` refuses to run a
verification role on the same family that produced the work, unless you pass
`--same-family` and accept that the check is weaker.

## Invocation

Each harness declares a command template. `{prompt}` is substituted with the
composed prompt; `{cwd}` with the working directory.

| harness | non-interactive form |
|---|---|
| `claude`   | `claude -p "…"` |
| `codex`    | `codex exec --skip-git-repo-check "…"` |
| `opencode` | `opencode run "…"` |
| `gemini`   | `gemini -p "…"` |

Add a harness by adding three keys: `harness_<name>_cmd`, `harness_<name>_family`,
and listing it in `harnesses`.

## Roles

`dl ask --role <role>` composes a prompt from `skills/cross-check/roles/<role>.md`.
Shipped roles:

- **`adversary`** — try to break the claim. Assume it is wrong; find the reason.
- **`reimplementer`** — implement the analysis from the written specification
  alone, never reading the original code, then compare results.
- **`estimand-auditor`** — does the test measure the quantity the question asks
  about? Catches the class of error where a technically correct computation
  answers the wrong question.
- **`gotcha-scanner`** — check the run against the project's recorded silent
  failure modes in `GOTCHAS.md`.

```dl-config
harnesses = claude codex opencode

harness_claude_cmd      = claude -p {prompt}
harness_claude_family   = anthropic

harness_codex_cmd       = codex exec --skip-git-repo-check {prompt}
harness_codex_family    = openai

harness_opencode_cmd    = opencode run {prompt}
harness_opencode_family = mixed

harness_gemini_cmd      = gemini -p {prompt}
harness_gemini_family   = google

# Harness that produces work by default; verification must differ in family.
producer   = claude
verifier   = codex

# Seconds before a cross-check invocation is abandoned.
ask_timeout = 180
ask_max_input_bytes = 24000
ask_max_output_bytes = 8000
ask_output_words = 500
ask_max_rounds = 2
```

Command templates are parsed as quoted arguments without shell evaluation; use a
wrapper script for pipelines or environment setup. `{cwd}` resolves to the project
root and invocation also uses that working directory. Reviews from `mixed` or
`unknown` model families are refused. Select the actual provider family used by
each configurable harness before review. `--same-family` records a weaker review
that does not satisfy a required foreign-family cross-check.

Budget scope: byte limits cover the supplied prompt and captured CLI response;
they are not provider token/billing caps and cannot bound hidden harness context.
An unchanged eligible review is reused without a model call. Further reviews need
--note with a concrete issue and consume the iteration-wide round budget. Failed
attempts consume a round. Deterministic execution/status never calls a model.
