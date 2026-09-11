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

If micromamba and the task SIF are already staged, initialization can configure
the runtime in one step:

```bash
arh init /shared/study --bootstrap \
  --micromamba "$(command -v micromamba)" \
  --runtime /shared/images/runtime.sif
```

The setup helpers remain available independently:

```bash
scripts/setup-nextflow.sh /shared/study /absolute/path/to/micromamba
scripts/setup-runtime.sh /shared/study /shared/images/runtime.sif
```

`nextflow_prefix` is the host controller environment. `runtime_image` plus
`runtime_sha256` identify the task SIF. The optional `runtime_prefix` is a task
environment mounted read-only inside that image. Explicit package lists are
recorded under `.arh/`.

Set `scheduler = slurm` in `.arh/config/site.md` and configure partition,
account, time, CPUs and memory there. Additional Nextflow configuration belongs
in `.arh/config/nextflow.config`. The project and task runtime must be accessible
at consistent paths from compute nodes.

`arh submit iterations/iterationN/scripts/workflow.nf -n experiment` checks the
frozen plan, runs Nextflow and records trace, report, timeline and a run receipt.
Use `--resume` for native workflows with declared inputs. Legacy `.sh` submission
is a migration adapter and deliberately cannot resume.

Immutable inputs are bound read-only; the task environment is also read-only.
This is a cooperative research protocol, not a sandbox for hostile Nextflow code.
Workflow authors must preserve the container policy and declare scientific
dependencies and inputs. The host controller, scheduler clients and container
runtime are infrastructure prerequisites.
