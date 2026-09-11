# Site configuration

Everything about **this machine or cluster**: how jobs are submitted, how tools
are containerised, where images live. Nothing here is scientific — swap this one
file to move a project to a different cluster.

Settings live in the fenced `arh-config` block below as `key = value`. Text
outside the block is documentation and is ignored.

## Scheduler

`scheduler` selects how `arh submit` launches work.

| value | submit | status | notes |
|---|---|---|---|
| `slurm` | Nextflow → Slurm | `squeue` | the usual HPC case |
| `pbs`   | Nextflow → PBS | `qstat` | best-effort |
| `local` | Nextflow local | Nextflow trace | laptops, CI, the test suite |

`arh init` detects Slurm/PBS when their client commands are present; override it
with `--scheduler` or edit this file. Slurm resource keys become Nextflow process
settings or cluster options.

## Containers

`container_runtime` records the site command available for container execution.
`arh init` detects `singularity` or `apptainer` when present. Scientific tasks
must still use the configured digest-pinned runtime image.

| value | behaviour |
|---|---|
| `apptainer` / `singularity` | clean task execution with project RW and immutable inputs RO |
| `docker` | local/container development with the same bind policy |
| `none` | direct host execution — smoke tests only, not reproducible research |

Declare auxiliary images as `image_<name> = <path or URI>`, then refer to them
by `<name>`. A bare name resolves under `image_dir`.

```arh-config
scheduler         = local
container_runtime = singularity

# Host controller. `arh init --bootstrap` can populate this automatically.
nextflow_prefix =
# Task container. scripts/setup-runtime.sh records its digest.
runtime_image =
runtime_sha256 =
runtime_prefix =
nextflow_version = 26.04.6

# --- SLURM ---------------------------------------------------------------
slurm_partition   =
slurm_account     =
slurm_time        = 01:00:00
slurm_cpus        = 1
slurm_mem         = 4G
slurm_extra       =

# --- PBS -----------------------------------------------------------------
pbs_queue         =

# --- containers ----------------------------------------------------------
image_dir         = .arh/images
# image_samtools  = /opt/images/samtools_1.21.sif
# image_samtools_sha256 = <sha256 of that file>
# image_python    = docker://python@sha256:<64 lowercase hexadecimal digits>

extra_binds       =
```

Non-smoke runs require declared content identity. Local image files use
`image_<name>_sha256`; remote references require `@sha256:...`. Changing a local
image without changing its declared digest fails before execution.
