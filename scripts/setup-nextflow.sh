#!/usr/bin/env bash
# Host controller: exact micromamba prefix, preserving scheduler access.
set -euo pipefail
[ $# -eq 2 ] || { echo 'usage: scripts/setup-nextflow.sh PROJECT MICROMAMBA_BINARY' >&2; exit 2; }
project=$(cd "$1" && pwd)
micromamba=$(realpath "$2")
[ -x "$micromamba" ] || { echo 'micromamba binary missing' >&2; exit 1; }
[ -d "$project/.dl" ] || { echo 'run dl init first' >&2; exit 1; }
prefix="$project/.dl/envs/nextflow-host/26.04.6"
export MAMBA_ROOT_PREFIX="$project/.dl/mamba-host"
mkdir -p "$MAMBA_ROOT_PREFIX"
if [ ! -x "$prefix/bin/nextflow" ]; then
  "$micromamba" create -y -p "$prefix" -c conda-forge -c bioconda 'nextflow=26.04.6' 'python=3.12'
fi
"$micromamba" list -p "$prefix" --explicit > "$project/.dl/nextflow-host-explicit.lock"
"$prefix/bin/python3" - "$project" "$prefix" <<'PY'
from pathlib import Path
import re,sys
project,prefix=sys.argv[1:]
p=Path(project)/'.dl/config/site.md'; text=p.read_text()
for key,value in {'nextflow_prefix':prefix,'nextflow_version':'26.04.6'}.items():
    pattern=r'(?m)^'+re.escape(key)+r'\s*=.*$'
    if re.search(pattern,text): text=re.sub(pattern,lambda m:key+' = '+value,text)
    else: text+='\n```dl-config\n'+key+' = '+value+'\n```\n'
p.write_text(text)
PY
printf 'Host Nextflow ready: %s/bin/nextflow\n' "$prefix"
