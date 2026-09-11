#!/usr/bin/env bash
# Host controller: exact micromamba prefix, preserving scheduler access.
set -euo pipefail
[ $# -eq 2 ] || { echo 'usage: scripts/setup-nextflow.sh PROJECT MICROMAMBA_BINARY' >&2; exit 2; }
project=$(cd "$1" && pwd)
micromamba=$(realpath "$2")
[ -x "$micromamba" ] || { echo 'micromamba binary missing' >&2; exit 1; }
if [ -d "$project/.arh" ]; then state="$project/.arh"; elif [ -d "$project/.arh" ]; then state="$project/.arh"; else echo 'run arh init first' >&2; exit 1; fi
prefix="$state/envs/nextflow-host/26.04.6"
export MAMBA_ROOT_PREFIX="$state/mamba-host"
mkdir -p "$MAMBA_ROOT_PREFIX"
if [ ! -x "$prefix/bin/nextflow" ]; then
  "$micromamba" create -y -p "$prefix" -c conda-forge -c bioconda 'nextflow=26.04.6' 'python=3.12'
fi
"$micromamba" list -p "$prefix" --explicit > "$state/nextflow-host-explicit.lock"
"$prefix/bin/python3" - "$state/config/site.md" "$prefix" <<'PY'
from pathlib import Path
import re,sys
p=Path(sys.argv[1]); text=p.read_text(); prefix=sys.argv[2]
for key,value in {'nextflow_prefix':prefix,'nextflow_version':'26.04.6'}.items():
    pat=r'(?m)^'+re.escape(key)+r'\s*=.*$'
    text=re.sub(pat, f'{key} = {value}', text) if re.search(pat,text) else text+f'\n```arh-config\n{key} = {value}\n```\n'
p.write_text(text)
PY
printf 'Host Nextflow ready: %s/bin/nextflow\n' "$prefix"
