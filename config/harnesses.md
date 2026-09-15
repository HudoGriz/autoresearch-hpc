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
harness_claude_version_cmd = claude --version

harness_codex_cmd       = codex exec --skip-git-repo-check {prompt}
harness_codex_family    = openai
harness_codex_version_cmd = codex --version

harness_opencode_cmd    = opencode run {prompt}
harness_opencode_family = mixed
harness_opencode_version_cmd = opencode --version

harness_gemini_cmd      = gemini -p {prompt}
harness_gemini_family   = google
harness_gemini_version_cmd = gemini --version

producer   = claude
verifier   = codex
# Tried in order only after the verifier refuses the content (arh ask exit 77). Each needs a
# concrete model family other than the producer's, e.g.: verifier_fallback = gemini
verifier_fallback =

ask_timeout = 900
ask_max_input_bytes = 24000
ask_max_output_bytes = 8000
ask_output_words = 500
ask_max_rounds = 2
```

## Refusals, fallbacks and token usage

`arh ask` exits 75 when the provider refuses the call on a usage or rate limit, or on
authentication, and prints the provider's own line with any reset time it states. It
exits 77 when the provider refuses the content itself (a safety classifier). Neither
consumes a review round. After a content refusal, each harness in `verifier_fallback`
is tried in turn.

A command template may contain `{usage}`, a file path the command can write a JSON
object of token counts or cost to; `arh ask` stores it in the review record as `usage`.
The framework's `harness/claude/review.sh` and `harness/codex/review.sh` do this. The
prompt stays the first argument, `{usage}` the second, CLI options follow:

    harness_claude_cmd = /path/to/autoresearch-hpc/harness/claude/review.sh {prompt} {usage} --model <model>
    harness_codex_cmd  = /path/to/autoresearch-hpc/harness/codex/review.sh {prompt} {usage} -m <model>

Command templates are parsed as quoted arguments without shell evaluation; use
a wrapper script for pipelines or environment setup. Reviews from `mixed` or
`unknown` families cannot satisfy the required foreign-family gate. An unchanged
eligible review is reused without a model call. Deterministic execution, status
and context assembly do not call a model.

`harness_<name>_version_cmd` (optional) runs once before each review. Its first
output line is stored in the review record as `verifier_version`, so a verdict
can be traced to the CLI build that produced it. The family alone does not
identify the model. When the provider's default model must not drift between
reviews, pin it in the command template itself (for example
`codex exec -m <model> --skip-git-repo-check {prompt}`).
