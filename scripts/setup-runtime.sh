#!/usr/bin/env bash
# Bootstrap task dependencies inside Singularity/Apptainer.
set -euo pipefail
[ $# -eq 2 ] || { echo 'usage: scripts/setup-runtime.sh PROJECT RUNTIME.sif' >&2; exit 2; }
project=$(cd "$1" && pwd)
image=$(cd "$(dirname "$2")" && pwd)/$(basename "$2")
state="$project/.arh"
[ -d "$state" ] || { echo 'run arh init first' >&2; exit 1; }
[ -f "$image" ] || { echo 'runtime SIF is missing' >&2; exit 1; }
if command -v singularity >/dev/null 2>&1; then runtime=singularity
elif command -v apptainer >/dev/null 2>&1; then runtime=apptainer
else echo 'singularity/apptainer is missing' >&2; exit 1; fi
version=26.04.6
packages=("nextflow=$version" 'python=3.12' 'git=2.49' 'bash=5.2' 'procps-ng=4.0.4')
if command -v sha256sum >/dev/null 2>&1; then digest=$(sha256sum "$image" | awk '{print $1}'); else digest=$(shasum -a 256 "$image" | awk '{print $1}'); fi
mkdir -p "$state/home" "$state/tmp"
export APPTAINER_CACHEDIR="$state/container-cache"
export APPTAINER_TMPDIR="$state/tmp"
binds=(--bind "$project:$project:rw")
if [ -n "${ARH_ENV_CACHE:-}" ]; then
  # Shared and content-addressed by image digest and package pins, as in setup-nextflow.sh.
  mkdir -p "$ARH_ENV_CACHE"; cache=$(cd "$ARH_ENV_CACHE" && pwd)
  if command -v sha256sum >/dev/null 2>&1; then key=$(printf '%s\n' "$digest" "${packages[@]}" | sha256sum | cut -c1-16)
  else key=$(printf '%s\n' "$digest" "${packages[@]}" | shasum -a 256 | cut -c1-16); fi
  prefix="$cache/runtime/$version-$key"; mamba="$cache/mamba"
  binds+=(--bind "$cache:$cache:rw")
else
  prefix="$state/envs/nextflow/$version"; mamba="$state/mamba"
fi
mkdir -p "$mamba"
in_image() {
  "$runtime" exec --cleanenv --containall --home "$state/home" "${binds[@]}" \
    --env "MAMBA_ROOT_PREFIX=$mamba,CONDA_PKGS_DIRS=$mamba/pkgs,XDG_CACHE_HOME=$mamba/cache" \
    "$image" micromamba "$@"
}
create_env() { in_image create -y -p "$prefix" -c conda-forge -c bioconda "${packages[@]}"; }
if [ -n "${ARH_ENV_CACHE:-}" ]; then
  # shellcheck source=lib/common.sh
  . "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib/common.sh"
  arh_build_once "$prefix" create_env || { echo "failed to build $prefix" >&2; exit 1; }
elif [ ! -x "$prefix/bin/nextflow" ]; then
  create_env
fi
# Replayable lock (@EXPLICIT plus URL#md5 lines), as in setup-nextflow.sh.
{ echo '@EXPLICIT'; in_image list -p "$prefix" --explicit --md5 | grep -E '^https?://'; } > "$state/nextflow-explicit.lock"
# setup-nextflow.sh rewrites the same file; serialise so concurrent setups cannot drop keys.
lock="$state/config/.site.lock"; i=0
until mkdir "$lock" 2>/dev/null; do
  i=$((i+1)); [ "$i" -lt 120 ] || { echo "site.md locked by another setup: $lock (remove if stale)" >&2; exit 1; }
  sleep 1
done
trap 'rmdir "$lock" 2>/dev/null || true' EXIT
python3 - "$state/config/site.md" "$image" "$prefix" "$digest" "$version" "$runtime" <<'PY'
from pathlib import Path
import re,sys
p=Path(sys.argv[1]); text=p.read_text()
values={'runtime_image':sys.argv[2],'runtime_prefix':sys.argv[3],'runtime_sha256':sys.argv[4],
        'nextflow_version':sys.argv[5],'container_runtime':sys.argv[6]}
for key,value in values.items():
    pat=r'(?m)^'+re.escape(key)+r'\s*=.*$'
    text=re.sub(pat, f'{key} = {value}', text) if re.search(pat,text) else text+f'\n```arh-config\n{key} = {value}\n```\n'
p.write_text(text)
PY
printf 'Runtime ready: %s\nEnvironment: %s\n' "$image" "$prefix"
