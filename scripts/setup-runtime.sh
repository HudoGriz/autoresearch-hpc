#!/usr/bin/env bash
# Bootstrap TASK dependencies inside Singularity; never launch the Nextflow driver here.
set -euo pipefail
[ $# -eq 2 ] || { echo 'usage: scripts/setup-runtime.sh PROJECT RUNTIME.sif' >&2; exit 2; }
project=$(cd "$1" && pwd)
image=$(cd "$(dirname "$2")" && pwd)/$(basename "$2")
[ -d "$project/.dl" ] || { echo 'run dl init first' >&2; exit 1; }
[ -f "$image" ] || { echo 'runtime SIF is missing' >&2; exit 1; }
version=26.04.6
prefix="$project/.dl/envs/nextflow/$version"
mkdir -p "$project/.dl/mamba" "$project/.dl/home" "$project/.dl/tmp"
export APPTAINER_CACHEDIR="$project/.dl/container-cache"
export APPTAINER_TMPDIR="$project/.dl/tmp"
if [ ! -x "$prefix/bin/nextflow" ]; then
  singularity exec --cleanenv --containall --home "$project/.dl/home" --bind "$project:$project:rw" \
    --env "MAMBA_ROOT_PREFIX=$project/.dl/mamba,CONDA_PKGS_DIRS=$project/.dl/mamba/pkgs,XDG_CACHE_HOME=$project/.dl/mamba/cache" \
    "$image" micromamba create -y -p "$prefix" -c conda-forge -c bioconda \
      "nextflow=$version" 'python=3.12' 'git=2.49' 'bash=5.2' 'procps-ng=4.0.4'
fi
if [ ! -x "$prefix/bin/ps" ]; then
  singularity exec --cleanenv --containall --home "$project/.dl/home" --bind "$project:$project:rw" \
    --env "MAMBA_ROOT_PREFIX=$project/.dl/mamba,CONDA_PKGS_DIRS=$project/.dl/mamba/pkgs,XDG_CACHE_HOME=$project/.dl/mamba/cache" \
    "$image" micromamba install -y -p "$prefix" -c conda-forge 'procps-ng=4.0.4'
fi
# Run the exact environment binary; no activation and no nextflow from host PATH.
singularity exec --cleanenv --containall --home "$project/.dl/home" --bind "$project:$project:rw" \
  --env "MAMBA_ROOT_PREFIX=$project/.dl/mamba,CONDA_PKGS_DIRS=$project/.dl/mamba/pkgs,XDG_CACHE_HOME=$project/.dl/mamba/cache" \
  "$image" micromamba list -p "$prefix" --explicit > "$project/.dl/nextflow-explicit.lock"
digest=$(sha256sum "$image" | awk '{print $1}')
singularity exec --cleanenv --containall --home "$project/.dl/home" --bind "$project:$project:rw" \
  "$image" "$prefix/bin/python3" - "$project" "$image" "$prefix" "$digest" "$version" <<'PY'
from pathlib import Path
import re,sys
project,image,prefix,digest,version=sys.argv[1:]
p=Path(project)/'.dl/config/site.md'; text=p.read_text()
values={'runtime_image':image,'runtime_prefix':prefix,'runtime_sha256':digest,'nextflow_version':version,'container_runtime':'singularity'}
for key,value in values.items():
    pattern=r'(?m)^'+re.escape(key)+r'\s*=.*$'
    if re.search(pattern,text): text=re.sub(pattern,lambda m:key+' = '+value,text)
    else: text+='\n```dl-config\n'+key+' = '+value+'\n```\n'
p.write_text(text)
PY
printf 'Runtime ready: %s\nEnvironment: %s\n' "$image" "$prefix"
