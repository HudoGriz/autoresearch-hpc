# HPC execution boundary

Nextflow runs on the host from a locked pixi environment. It inherits the site's
scheduler configuration and uses the native Slurm/PBS client tools.
Singularity/Apptainer runs scientific tasks on local or cluster executors. Do not
wrap the Nextflow controller itself in the task container.

```text
Host: arh → <nextflow_prefix>/bin/nextflow → Slurm/PBS
                                               ↓
Compute node:                         Singularity/Apptainer → task
```

## Fast setup

`arh init` discovers basic site capabilities and `arh doctor` tells you what is
still missing. Any digest-pinned image with a shell is a task image; ARH installs
nothing into it:

```bash
export APPTAINER_CACHEDIR=/shared/images/.cache        # not your home quota
singularity pull /shared/images/runtime.sif docker://debian:bookworm-slim
arh init /shared/study --bootstrap --runtime /shared/images/runtime.sif
cd /shared/study && arh doctor
```

Every environment ARH builds is a [pixi](https://pixi.sh) environment: the host
Nextflow with its Java (`.arh/envs/nextflow-host`), the task runtime that is bound
read-only into every task (`.arh/envs/runtime`: bash, `ps` for Nextflow's task
metrics, python, git), each `arh env create` environment and the tools. Each
directory's `pixi.toml` and `pixi.lock` are the record; a fresh clone rebuilds them
exactly. The pinned pixi binary and its package cache go to `tools_dir` (node-local
on a shared filesystem: a CUDA PyTorch environment builds in about 2 min on CephFS).
`--env-cache DIR` (or `ARH_ENV_CACHE`) shares both between projects. Offline, stage
pixi yourself and set `ARH_PIXI=/path/to/pixi`. The setup helpers run on their own
too: `scripts/setup-nextflow.sh PROJECT`, `scripts/setup-runtime.sh PROJECT IMAGE`.

`nextflow_prefix` is the host controller environment, `runtime_image` plus
`runtime_sha256` identify the task image and `runtime_prefix` the task runtime.
Environments built by an earlier arh with micromamba keep working.

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
`logs/nextflow/<name>/attempt-*/console.log` and `trace.tsv`. Another process can
block until an iteration's submissions and reviews have finished with
`arh wait -n N`; it reads the launch and review locks and calls neither a model
nor the scheduler.

Nextflow writes an HTML report and timeline for every submission, about 1.9 MB,
which is nearly all of a run's evidence bytes. Set `nextflow_reports = gzip` in
`site.md` to compress them after the run, or `none` to skip them; `trace.tsv` and
the run receipt are always kept.

### Scientific environments

`arh env create NAME pkg=version ...` (`pypi:pkg==version` for PyPI) solves a
package set once with pixi and locks it in `.arh/envs/NAME/pixi.lock`; it prints the
prefix a process calls (`<prefix>/bin/python`). `arh env create NAME` without
packages rebuilds it exactly from its lock. A built environment does not change: a
different package set is a new name. Run receipts hash every lock. A CUDA package set
(`pytorch-gpu`, ...) takes `--cuda 12`: it is recorded in `pixi.toml`, so the set solves and
rebuilds on a node without a GPU.

### Provenance from Nextflow itself

`.arh/config/nextflow.config` is passed to every run, so Nextflow's own provenance
needs no ARH code. Its data lineage records every task's code, inputs, outputs and
container with checksums (`nextflow lineage view`), and the nf-prov plugin writes a
Workflow Run RO-Crate next to the results, where the review binds it:

```groovy
lineage.enabled = true      // in the run directory, iterationN/metadata/nextflow/NAME/.lineage
plugins { id 'nf-prov@1.8.0' }
prov { formats { wrroc { file = "${params.outdir}/ro-crate-metadata.json"; overwrite = true } } }
```

Runs are offline, so install the plugin once:
`NXF_HOME=.arh/nextflow .arh/envs/nextflow-host/.pixi/envs/default/bin/nextflow plugin install nf-prov@1.8.0`.
Lineage is experimental in Nextflow and checksums every output, which costs time
on large results; ARH's own run receipt is kept either way, because Nextflow does
not see the plan, the frozen scripts a workflow calls by path, or the image digest.

### GPUs

A process that carries `label 'gpu'` (nf-core's `process_gpu` works too) or an
`accelerator N` directive runs with Singularity's `--nv`. On Slurm it goes to
`gpu_partition` (default `slurm_partition`) with `--gres=gpu[:gpu_type]:N`, plus
`--constraint=gpu_constraint` and `gpu_extra` when set; other processes keep the
ordinary partition. The settings are written as label-aware closures in the
generated `execution.config`, because when a process has two labels the last
`withLabel` selector would otherwise win. The receipt records the GPU settings.
A process that sets its own `containerOptions`, `queue` or `clusterOptions`
replaces these.

### A second tool image

`label 'image_<name>'` runs a process in the image declared as `image_<name>`
in `site.md` instead of the task image. The image must be a local file whose
digest matches `image_<name>_sha256`, checked at every submit. The process gets
the image's own `PATH` (read from the image, or `image_<name>_path`), followed
by the task environment's `bin/`: the image's tools win, and Nextflow still finds
the `ps` it needs in every container, which many tool images lack. The receipt records
`images` (path, digest, `PATH`), and `trace.tsv` gains a `container` column naming
the image each task ran in.

### Imports from other iterations

A plan declares code it takes from another iteration's `scripts/` in an
`arh-config` block (`imports = iterations/iteration1/scripts/it1_00_lib.py`).
`arh gate predeclare` appends each file's hash to `PREDECLARATION.sha256`, and
`arh submit` refuses a run in which one changed. Other iterations' scripts that
the workflow or its scripts name without declaring them are hashed too
(`referenced_sha256`), with a warning.

### Verifications and work outside the receipt

`arh verify run OBJECT WORKFLOW` submits a verification's workflow exactly as
`arh submit` submits an iteration's, with its evidence under
`verification/OBJECT/`. `arh verify conclude OBJECT` requires a successful receipt
of the frozen plan unless given `--without-run REASON`.

Work that cannot go through `arh submit` is recorded with
`arh note -n N --job JOBID TEXT`. `arh status` counts notes, `arh context` shows
the latest, and `arh gate results` warns about them, and about results that no
receipt accounts for.

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
check new workflows first with `arh submit WORKFLOW.nf --lint`, which runs
`nextflow lint` with the pinned controller and submits nothing.

### Sealed inputs and freezes

`sealed_inputs` in `project.md` names held-out data. For a run that may not read
them, `arh submit` adds an empty read-only bind over each sealed path (after the
immutable inputs, so a sealed directory inside a broader input is covered too)
and sets `singularity.autoMounts = false`: Nextflow's automounts bind a staged
input's directory before ARH's options, and Singularity keeps the first bind of
a target, so an automount would otherwise expose it. It also refuses a workflow,
params file or iteration script whose text names a sealed path. `arh run` always
covers them.

A run of an iteration with a valid `FREEZE.json` (`arh freeze -n N PATH...`)
binds the sealed paths read-only instead. Its receipt records `freeze_sha256`
and `sealed_inputs.read`, and `.arh/unseals.tsv` gets one row per sealed path and
run. `arh submit` refuses the run if any file named in `FREEZE.json` has changed.

## Isolation boundary

Immutable inputs are bound read-only; the task environment is also read-only.
Sealed inputs are hidden from every container that is not a frozen confirmation,
but the agent's own shell can still read whatever the operating system lets it;
`harness/install.sh` adds deny rules where a harness supports them.
This is a cooperative research protocol, not a sandbox for hostile Nextflow code.
Workflow authors must preserve the container policy and declare scientific
dependencies and inputs. The host controller, scheduler clients and container
runtime are infrastructure prerequisites.
