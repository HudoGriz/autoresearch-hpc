#!/usr/bin/env bash
# Integrations: build the pinned tools environment ARH turns on by default.
#
# Entire CLI (agent sessions, models and tokens), gitleaks (maintained credential rules) and
# basic-memory (search over knowledge/) live in their own environment, apart from the host
# Nextflow one, so adding or upgrading a tool never touches the environment running workflows.
# Versions and checksums come from config/dependencies.json; docs/integrations.md says what each
# tool does and how to switch it off.
set -euo pipefail
[ $# -eq 1 ] || { echo 'usage: scripts/setup-tools.sh PROJECT   (after scripts/setup-nextflow.sh)' >&2; exit 2; }
home=${ARH_HOME:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}
project=$(cd "$1" && pwd)
state="$project/.arh"
[ -d "$state" ] || { echo 'run arh init first' >&2; exit 1; }
micromamba=$(sed -n 's/^binary=//p' "$state/micromamba.lock" 2>/dev/null || true)
[ -x "$micromamba" ] || { echo "no pinned micromamba: run scripts/setup-nextflow.sh $project first" >&2; exit 1; }

case "$(uname -s)-$(uname -m)" in
  Linux-x86_64|Linux-amd64) platform=linux-64; gl_arch=linux_x64 ;;
  Linux-aarch64|Linux-arm64) platform=linux-aarch64; gl_arch=linux_arm64 ;;
  *) platform=other; gl_arch='' ;;
esac

# conda specs, pip specs, gitleaks version and checksum, one per line
mapfile -t pins < <(python3 - "$home/config/dependencies.json" "$platform" <<'PY'
import json, sys
t = json.load(open(sys.argv[1]))['tools']
print(' '.join(f'{k}={v}' for k, v in t['conda'].items()))
print(' '.join(f'{k}=={v}' for k, v in t['pip'].items()))
print(t['gitleaks']['version'])
print(t['gitleaks']['sha256'].get(sys.argv[2], ''))
PY
)
read -r -a conda_specs <<<"${pins[0]}"
read -r -a pip_specs <<<"${pins[1]}"
gl_version=${pins[2]}; gl_sha=${pins[3]}

key=$(printf '%s\n' "$platform" "${conda_specs[@]}" "${pip_specs[@]}" "gitleaks=$gl_version" | sha256sum | cut -c1-16)
if [ -n "${ARH_ENV_CACHE:-}" ]; then
  # Shared and content-addressed, as in setup-nextflow.sh.
  mkdir -p "$ARH_ENV_CACHE"; cache=$(cd "$ARH_ENV_CACHE" && pwd)
  prefix="$cache/tools/$key"; export MAMBA_ROOT_PREFIX="$cache/mamba-host"
else
  prefix="$state/envs/tools/$key"; export MAMBA_ROOT_PREFIX="$state/mamba-host"
fi
mkdir -p "$MAMBA_ROOT_PREFIX"

build() {
  "$micromamba" create -y -p "$prefix" -c conda-forge "${conda_specs[@]}"
  "$prefix/bin/python3" -m pip install --no-input --disable-pip-version-check "${pip_specs[@]}"
  if [ -n "$gl_sha" ]; then
    tmp=$(mktemp -d); url="https://github.com/gitleaks/gitleaks/releases/download/v$gl_version/gitleaks_${gl_version}_${gl_arch}.tar.gz"
    curl -fsSL --retry 3 -o "$tmp/gl.tgz" "$url"
    got=$(sha256sum "$tmp/gl.tgz" | cut -d' ' -f1)
    [ "$got" = "$gl_sha" ] || { echo "gitleaks checksum mismatch: expected $gl_sha, got $got" >&2; rm -rf "$tmp"; return 1; }
    tar -xzf "$tmp/gl.tgz" -C "$prefix/bin" gitleaks; rm -rf "$tmp"
  else
    echo "no pinned gitleaks build for $platform: install it on PATH or set secret_scanner = builtin" >&2
  fi
}
# shellcheck source=lib/common.sh
. "$home/lib/common.sh"
if [ -n "${ARH_ENV_CACHE:-}" ]; then arh_build_once "$prefix" build || { echo "failed to build $prefix" >&2; exit 1; }
elif [ ! -x "$prefix/bin/entire" ]; then build; fi

# Replayable locks, as for the Nextflow environments.
{ echo '@EXPLICIT'; "$micromamba" list -p "$prefix" --explicit --md5 | grep -E '^https?://'; } > "$state/tools-explicit.lock"
"$prefix/bin/python3" -m pip freeze --disable-pip-version-check > "$state/tools-pip.lock"

lock="$state/config/.site.lock"; i=0
until mkdir "$lock" 2>/dev/null; do
  i=$((i+1)); [ "$i" -lt 120 ] || { echo "site.md locked by another setup: $lock (remove if stale)" >&2; exit 1; }
  sleep 1
done
trap 'rmdir "$lock" 2>/dev/null || true' EXIT
python3 - "$state/config/site.md" "$prefix" <<'PY'
from pathlib import Path
import re, sys
p = Path(sys.argv[1]); text = p.read_text(); pat = r'(?m)^tools_prefix\s*=.*$'
line = f'tools_prefix = {sys.argv[2]}'
p.write_text(re.sub(pat, line, text) if re.search(pat, text) else text + f'\n```arh-config\n{line}\n```\n')
PY
printf 'Tools ready: %s/bin (entire, gitleaks, bm)\n' "$prefix"
