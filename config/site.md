# Site configuration

Everything about **this machine or cluster**: how jobs are submitted, how tools
are containerised, where images live. Nothing here is scientific — swap this one
file to move a project to a different cluster.

Settings live in the fenced `dl-config` block below as `key = value`. Text
outside the block is documentation and is ignored.

## Scheduler

`scheduler` selects how `dl submit` launches work.

| value | submit | status | notes |
|---|---|---|---|
| `slurm` | `sbatch --parsable` | `squeue` | the usual HPC case |
| `pbs`   | `qsub`              | `qstat` | best-effort |
| `local` | detached `bash`     | `kill -0` | laptops, CI, the test suite |

The `slurm_*` keys become `sbatch` flags. `slurm_extra` is passed through
verbatim, so anything not modelled here (`--gres=gpu:1`, `--qos=...`, a
constraint) still works.

## Containers

`container_runtime` selects how `dl run` executes a pinned tool.

| value | behaviour |
|---|---|
| `apptainer` / `singularity` | `exec --cleanenv --containall`, project bound read-write, immutable inputs bound `:ro` |
| `docker` | `docker run --rm` with the same bind policy |
| `none` | run the command directly on `PATH` — no pinning, use only for smoke tests |

Declare images as `image_<name> = <path or URI>`, then refer to them by
`<name>`. A bare name resolves under `image_dir`.

```dl-config
scheduler         = local
container_runtime = none

# --- SLURM (used when scheduler = slurm) --------------------------------
slurm_partition   =
slurm_account     =
slurm_time        = 01:00:00
slurm_cpus        = 1
slurm_mem         = 4G
slurm_extra       =

# --- PBS (used when scheduler = pbs) ------------------------------------
pbs_queue         =

# --- containers ---------------------------------------------------------
image_dir         = .dl/images
# image_samtools  = /opt/images/samtools_1.21.sif
# image_python    = docker://python:3.11-slim

# Extra bind mounts, space-separated, in the runtime's own syntax
# (apptainer "src:dst[:ro]", docker "src:dst[:ro]").
extra_binds       =
```
