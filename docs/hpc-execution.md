# HPC execution boundary

Nextflow runs on the host from a versioned micromamba environment. It inherits
the site's scheduler configuration and uses the native Slurm/PBS client tools.
Singularity/Apptainer runs scientific tasks on local or cluster executors. Do not
wrap the Nextflow controller itself in the task container.

```text
Host: arh → <nextflow_prefix>/bin/nextflow → Slurm/PBS
                                               ↓
Compute node:                         Singularity/Apptainer → task
```

## Fast setup

`arh init` discovers basic site capabilities and `arh doctor` tells you what is
still missing:

```bash
arh init /shared/study
cd /shared/study
arh doctor
```

The task runtime is a micromamba image. Pull it once; point `APPTAINER_CACHEDIR`
somewhere with space so the layer cache does not land in your home quota:

```bash
export APPTAINER_CACHEDIR=/shared/images/.cache
singularity pull /shared/images/runtime.sif docker://mambaorg/micromamba:2.8.1
```

If micromamba and the task SIF are already staged, initialization can configure
the runtime in one step:

```bash
arh init /shared/study --bootstrap \
  --micromamba "$(command -v micromamba)" \
  --runtime /shared/images/runtime.sif
```

The setup helpers remain available independently. They serialise their edits to
`site.md`, so they are safe to run concurrently:

```bash
scripts/setup-nextflow.sh /shared/study /absolute/path/to/micromamba
scripts/setup-runtime.sh /shared/study /shared/images/runtime.sif
```

`nextflow_prefix` is the host controller environment. `runtime_image` plus
`runtime_sha256` identify the task SIF. The optional `runtime_prefix` is a task
environment mounted read-only inside that image. Replayable `@EXPLICIT` package
locks are recorded under `.arh/`; `scripts/lock-env.sh` writes the same kind of
lock for any existing environment and can recreate it with a verified identical
package list.

Set `scheduler = slurm` in `.arh/config/site.md` and configure partition,
account, time, CPUs and memory there. Additional Nextflow configuration belongs
in `.arh/config/nextflow.config`. The project and task runtime must be accessible
at consistent paths from compute nodes.

## Submitting a workflow

`arh submit iterations/iterationN/scripts/workflow.nf -n experiment` checks the
frozen plan, runs Nextflow and records trace, report, timeline and a run receipt.
Use `--resume` for native workflows with declared inputs. Legacy `.sh` submission
is a migration adapter and deliberately cannot resume.

Submission blocks until Nextflow exits. Progress is visible in
`logs/nextflow/<name>/attempt-*/console.log` and `trace.tsv`.

### Run receipts and caching

The run receipt (`logs/nextflow/<name>/attempt-*/run.json`) hashes the workflow,
its configs and the task image. Workflows usually call the iteration's scripts
by path, and those are not Nextflow inputs, so the receipt also hashes every file
under `iterations/iterationN/scripts/` (`script_sha256`). `--resume` still
decides caching from each task's command string and declared inputs only. If
changing a script should invalidate the cache, declare it as a `path` input.

### Stopping a submission

Send SIGTERM to the wrapper; its PID is in
`metadata/nextflow/<name>/.launch-lock/owner.json`. The wrapper forwards the
signal to Nextflow, which cancels its jobs; a second signal escalates to SIGKILL.
The receipt records the signal and the lock is released. The next submit reclaims
a lock left by a process that no longer exists on the same host. A lock with no
owner record, or owned by a live or remote process, still refuses.

### Strict Nextflow syntax

The pinned Nextflow (26.04) runs workflows in strict syntax. Among other
things, a Groovy `import` statement is a compile error — write the
fully-qualified class inline instead (`new groovy.json.JsonSlurper()`). The
failure appears only after `arh submit` has created its attempt directory, so
check new workflows with `nextflow lint` from the host environment first.

## Isolation boundary

Immutable inputs are bound read-only; the task environment is also read-only.
This is a cooperative research protocol, not a sandbox for hostile Nextflow code.
Workflow authors must preserve the container policy and declare scientific
dependencies and inputs. The host controller, scheduler clients and container
runtime are infrastructure prerequisites.
