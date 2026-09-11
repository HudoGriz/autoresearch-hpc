#!/usr/bin/env bash
# Host controller: exact micromamba prefix, preserving scheduler access.
set -euo pipefail
[ $# -eq 2 ] || { echo 'usage: scripts/setup-nextflow.sh PROJECT MICROMAMBA_BINARY' >&2; exit 2; }
project=$(cd "$1" && pwd)
micromamba=$(realpath "$2")
[ -x "$micromamba" ] || { echo 'micromamba binary missing' >&2; exit 1; }
state="$project/.arh"
[ -d "$state" ] || { echo 'run arh init first' >&2; exit 1; }
prefix="$state/envs/nextflow-host/26.04.6"
export MAMBA_ROOT_PREFIX="$state/mamba-host"
mkdir -p "$MAMBA_ROOT_PREFIX"
if [ ! -x "$prefix/bin/nextflow" ]; then
  "$micromamba" create -y -p "$prefix" -c conda-forge -c bioconda 'nextflow=26.04.6' 'python=3.12'
fi
# A lock `micromamba create --file` accepts: @EXPLICIT plus URL#md5 lines. Plain
# `list --explicit` output starts with a header and cannot be replayed.
{ echo '@EXPLICIT'; "$micromamba" list -p "$prefix" --explicit --md5 | grep -E '^https?://'; } \
  > "$state/nextflow-host-explicit.lock"
# setup-runtime.sh rewrites the same file; serialise so concurrent setups cannot drop keys.
lock="$state/config/.site.lock"; i=0
until mkdir "$lock" 2>/dev/null; do
  i=$((i+1)); [ "$i" -lt 120 ] || { echo "site.md locked by another setup: $lock (remove if stale)" >&2; exit 1; }
  sleep 1
done
trap 'rmdir "$lock" 2>/dev/null || true' EXIT
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
