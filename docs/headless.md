# Running agents unattended

`arh` is usually driven by an agent in an interactive session. A batch driver that
starts producer sessions itself (one per round, per study, overnight) meets failure
modes that interactive use hides. These notes come from running twelve replication
studies this way on a Slurm cluster, with Claude Code and Codex CLI producers and
reviewers.

## The session must wait in the foreground

A headless session (`claude -p`, `codex exec`) gets no notice when background work
finishes, and it ends as soon as its reply ends. Claude Code producers started Slurm
fits, smoke tests and even the review in the background, then ended the reply to
"wait for a notification". The session exited and the work was orphaned; two studies
lost two rounds each before this was found. Codex sessions block and were unaffected.

- Tell the producer the session is non-interactive and that all waiting happens in
  the foreground. `AGENTS.md` says so; a driver prompt should repeat it.
- For Claude Code, set `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1`.
- `arh submit`, `arh ask` and `arh env create` block until done. `arh wait -n N`
  blocks until the iteration's running submissions and reviews finish, for work
  started by an earlier session.

## Runs longer than a session, and sessions that end mid-iteration

`arh submit` blocks and forwards a stop signal to Nextflow, so a harness that caps
how long a command may live (Claude Code: two hours for a background task) stopped
long runs when the cap hit. A field study restarted one under `setsid nohup` and
watched `trace.tsv` with a separate monitor.

- `arh submit WORKFLOW.nf -n NAME --detach` starts the run in its own session and
  returns once it holds its launch lock. `arh wait -n N` blocks on it;
  `arh status --running` shows each live submission with its trace counts, running
  reviews, and the scheduler state of job ids recorded with `arh note --job`.
- Two sessions on two accounts once drove one study. The second learned what the
  first had left running only from its transcript. Every `arh` command on an
  iteration now records itself in the iteration's lease, `arh status` lists open
  iterations with their holder and idle time (flagged `STALE` after
  `lease_stale_hours`, 24 by default), and a command from a different agent, user,
  host or `ARH_SESSION` warns. A takeover is `arh lease take -n N --reason TEXT`.
  Set `ARH_SESSION` in a driver to tell apart two sessions of one harness on one
  host.
- Work that cannot go through `arh submit` is recorded as it starts:
  `arh note -n N --job JOBID TEXT`.

## Check the site and the data before the first iteration

`arh doctor` checks that binaries and settings exist. `arh doctor --smoke` also runs
one task through the configured scheduler and task image and reports what the task
sees: the task environment, a writable project, read-only immutable inputs, hidden
sealed inputs, and with `--smoke gpu` a GPU in a task labelled `gpu`. Evidence goes
to `.arh/smoke/`.

`arh inputs check` reads the end-of-file marker of every CRAM 3 and BGZF file (BAM,
BCF, `.vcf.gz`, indices) under the declared inputs; `--deep` decompresses gzip files.
A truncated CRAM once made a caller exit 0 with calls for chr1-10 only. Results
go to `.arh/inputs/checks.jsonl`; every run receipt records them and `arh submit`
warns when a declared input failed.

## Do not inherit the operator's session

A driver started from inside an agent session passes that session's variables to
every child. `CLAUDECODE` made `arh claim` record a Codex producer as `claude`, and
the inherited `CLAUDE_CODE_*` variables exposed a session token to the producer.

- Clear harness variables (`CLAUDE*`, `CODEX*`) before starting a producer.
- Name the producer in `.arh/config/harnesses.md` rather than relying on `ARH_AGENT`.
  A driver's exported `ARH_AGENT` does not survive a producer that exports its own, and
  the agent contract used to invite exactly that, so a lane whose producer name pinned a
  model and account recorded itself under the bare harness name. `arh claim` now takes the
  configured producer over both `ARH_AGENT` and the harness markers, keeps what the session
  reported in `inferred_agent`/`inferred_from`, and warns; `arh doctor` warns too. `-a NAME`
  overrides deliberately.

## Close stdin for Codex

`codex exec` with a prompt argument still reads stdin when it is not a terminal and
waits forever ("Reading additional input from stdin…"). Start it with
`< /dev/null`. `arh ask` already does.

## Provider limits and refusals

Subscription limits, not compute, set the pace: Codex (`xhigh` reasoning) and
Claude Opus limits were reached within minutes to an hour, and one family's limit
also stops the other family's reviews. Plan one study at a time, or budget API keys.

- Detect limits from structured events, not by searching the log: the prompt itself
  may mention "rate limit". Claude reports a `result` event with `is_error` and a
  text such as "You've hit your session limit · resets 2:20pm". Codex emits `error`
  and `turn.failed` events ("try again at 5:05 PM"). Parse the reset time, but treat it
  as an upper bound: Codex once stated a reset five days out, and a probe 44 minutes
  later succeeded. Re-probe on a bounded interval and sleep to the stated time only
  when it is sooner.
- `arh ask` exits 75 on a limit and prints the provider's line with its reset time;
  the attempt spends no review round, and each harness in `verifier_fallback` is tried
  first, so a limit on one family need not stop the review.
- A provider can refuse a whole study on topic grounds. Codex refused a SARS-CoV-2
  host-transcriptomics replication as "flagged for possible biological risk", although
  the input was a public table of host gene counts. The same question asked briefly
  outside the working session was answered, so the refusal depends on accumulated
  context and cannot be predicted from the topic. `arh ask` exits 77 on such a
  refusal and tries each harness in `verifier_fallback`; a driver should record the
  refusal as its own outcome, not as a failed analysis.

## Accounting

Only reviews are bounded by `arh` ([details](skills-and-token-budget.md#what-the-bounds-do-not-cover)).

- Claude Code reports usage and cost in its final `result` event
  (`--output-format json` or `stream-json`).
- Codex reports usage per turn in `turn.completed` events of `--json` output, and in
  its session rollout file under `~/.codex/sessions/`.
- For reviews, `harness/claude/review.sh` and `harness/codex/review.sh` write these
  numbers to `{usage}`, and `arh ask` stores them in the review record.

## Blinding is cooperative

A producer that submits to Slurm usually runs with permission prompts bypassed, so
it can read any file the operator can. Anything it must not see (graders' targets,
published values, another study) is protected only by instruction. Run producers
under a separate Unix user, or in a filesystem sandbox that still reaches the
scheduler, when blinding has to be enforced.

## A failed criterion is not a blocker

A producer told only "stop if you are blocked" stopped entirely when an acceptance
criterion failed (a primary-outcome code missing from the data dictionary). The
protocol's answer is to report the failure, conclude the iteration and pre-declare
the handling in a new one; `AGENTS.md` and `arh next` now say so. Reserve "blocked"
for when no iteration can proceed at all.
