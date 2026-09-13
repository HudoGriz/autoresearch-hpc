# Independent reproduction record

Use this form for the publication-readiness usability test. The tester should be
someone who did not develop AutoResearch HPC and should receive only the
repository URL plus a request to install the software and reproduce the public
example.

Do not coach the tester unless they are blocked. Every intervention is data about
the setup experience and should be recorded.

## Tester and environment

- Date:
- Tester role/background:
- Operating system:
- Architecture:
- Scheduler: local / Slurm / PBS / other
- Scheduler version:
- Container runtime: Singularity / Apptainer / Docker / none
- Container runtime version:
- Shell:
- AutoResearch HPC commit/tag:
- `arh --version`:
- Nextflow version:

Do not record usernames, hostnames, internal IP addresses, credentials or paths
that identify private infrastructure. Generalize those before committing this
form to the public repository.

## Task given to the tester

Provide exactly this unless there is a documented reason to change it:

> Install AutoResearch HPC from this repository using the public documentation,
> run `arh doctor`, and reproduce the synthetic mean-shift example. Please note
> anything unclear, missing, surprising or broken. Do not ask the maintainer for
> help unless you are blocked.

## Outcomes

- Clone succeeded: yes / no
- Automatic bootstrap succeeded: yes / no
- `arh doctor` passed: yes / no
- Time from clone to first passing `arh doctor`:
- Synthetic example reproduced: yes / no
- Full ARH iteration completed: yes / no
- Foreign-family review completed: yes / no / not attempted
- Number of maintainer interventions:
- Setup difficulty (1 very easy — 5 very difficult):

## Expected synthetic result

The direct fixture should reproduce:

```json
{
  "estimand": "mean(after - before)",
  "mean_difference": 1.833333333333,
  "n": 12,
  "sign_flip_p_value": 0.00048828125
}
```

Record the observed output hash and compare it with the release artifact rather
than manually retyping values into the paper.

- Expected-result hash:
- Observed-result hash:
- Match: yes / no

## Problems encountered

For every problem, record the stage, exact error, what the tester tried, and
whether the documentation or diagnostics were sufficient.

| # | Stage | Problem | Could tester resolve unaided? | Repository change needed? |
|---|---|---|---|---|
| 1 | | | | |

## Maintainer interventions

Every intervention counts, including a one-line clarification.

| # | When | What the tester was told | Why docs/diagnostics were insufficient |
|---|---|---|---|
| 1 | | | |

## Final free-text feedback

- What was easiest?
- What was most confusing?
- What did you expect the software to do that it did not do?
- What did it do that you did not expect?
- Would you use this in a real computational project? Why or why not?

## Maintainer disposition

After the test, convert each needed intervention into one of:

- documentation fix;
- diagnostic improvement;
- setup/bootstrap bug;
- unsupported environment;
- no change, with reason.

Link the resulting issues/commits here. Preserve unsuccessful reproduction
attempts in the publication evidence rather than reporting only the final
successful rerun.
