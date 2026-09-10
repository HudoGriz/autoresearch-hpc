# HPC execution boundary

Nextflow runs on the host from a versioned micromamba environment. It inherits
the site's PATH and Slurm configuration, and uses the host `sbatch`, `squeue`
and `scancel`. Singularity runs each workflow task, on both local and Slurm
executors. Do not wrap the Nextflow controller in Singularity.

```text
Host: dl → <nextflow_prefix>/bin/nextflow → Slurm
                                            ↓
Compute node:                         Singularity → task
```

Initialize a study, stage a SIF, and configure the two environments:

```bash
bin/dl init /shared/study
scripts/setup-nextflow.sh /shared/study /absolute/path/to/micromamba
scripts/setup-runtime.sh /shared/study /shared/images/runtime.sif
```

`nextflow_prefix` is the host controller environment. `runtime_image` and its
`runtime_sha256` select the task SIF. The optional `runtime_prefix` is a
micromamba task environment mounted read-only inside that SIF. The current
bootstrap provides a general Python task environment; domain workflows need
their own pinned scientific packages. Explicit package lists are recorded in
`.dl/nextflow-host-explicit.lock` and `.dl/nextflow-explicit.lock`.

Set `scheduler = slurm` in `.dl/config/site.md` and configure partition, account,
time, CPUs and memory there. Additional Nextflow configuration belongs in
`.dl/config/nextflow.config`. The project, task image and environment must be
accessible at the same paths on compute nodes, where Singularity must be on
PATH. Follow site policy for running the controller on a login or allocated node.

`dl submit iterations/iterationN/scripts/workflow.nf -n experiment` checks the
frozen plan, runs Nextflow and records trace, report, timeline and a run receipt.
Use `--resume` for native workflows with declared inputs. Legacy `.sh` submission
is a migration adapter and deliberately cannot resume: arbitrary shell scripts
do not declare their dependencies. Submission waits for Nextflow to finish.

Immutable inputs are explicitly bound read-only; the task environment is also
read-only. This is a cooperative workflow protocol, not a sandbox for hostile
Nextflow code. Workflow authors must preserve the container policy and declare
all scientific dependencies and inputs. The host controller, scheduler clients
and Singularity itself are infrastructure prerequisites.

This follows Nextflow's documented [Slurm executor](https://github.com/nextflow-io/nextflow/blob/master/docs/executor.md)
and [cluster configuration pattern](https://training.nextflow.io/latest/nf4_science/imaging/04_config/).
