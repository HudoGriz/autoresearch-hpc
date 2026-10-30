#!/usr/bin/env bash
# Integrations: install the pinned tools ARH turns on by default, in seconds.
#
# Entire CLI (agent sessions, models and tokens), gitleaks (maintained credential rules) and uv are
# single release binaries, checked by sha256; basic-memory (search over knowledge/) goes into a uv
# virtual environment. No conda solve and no Nextflow environment is touched. Pins come from
# config/dependencies.json; the exact Python packages are locked in .arh/tools-pip.lock and
# replayed from it on the next build. docs/integrations.md says what each tool does and how to
# switch it off.
#
# Where: tools_dir in site.md (else $ARH_ENV_CACHE/tools, else .arh/envs/tools). The tools run on
# the host where arh runs, so on a slow shared filesystem (CephFS, NFS) a node-local tools_dir such
# as /var/tmp/arh-tools-$USER builds in ~15 s instead of many minutes.
set -euo pipefail
[ $# -eq 1 ] || { echo 'usage: scripts/setup-tools.sh PROJECT' >&2; exit 2; }
home=${ARH_HOME:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}
project=$(cd "$1" && pwd)
state="$project/.arh"
[ -d "$state" ] || { echo 'run arh init first' >&2; exit 1; }
# shellcheck source=lib/common.sh
. "$home/lib/common.sh"

case "$(uname -s)-$(uname -m)" in
  Linux-x86_64|Linux-amd64) platform=linux-64; triple=x86_64-unknown-linux-gnu; goarch=amd64; glarch=x64 ;;
  Linux-aarch64|Linux-arm64) platform=linux-aarch64; triple=aarch64-unknown-linux-gnu; goarch=arm64; glarch=arm64 ;;
  *) echo "no pinned tool builds for $(uname -s)-$(uname -m): install entire, gitleaks and basic-memory yourself" >&2; exit 1 ;;
esac

# name url sha256 per binary, then the python version and the pip specs
mapfile -t pins < <(python3 - "$home/config/dependencies.json" "$platform" "$triple" "$goarch" "$glarch" <<'PY'
import json, sys
t = json.load(open(sys.argv[1]))['tools']
platform, triple, goarch, glarch = sys.argv[2:6]
for name in ('uv', 'entire', 'gitleaks'):
    b = t[name]
    print(name, b['url'].format(version=b['version'], triple=triple, goarch=goarch, glarch=glarch), b['sha256'][platform])
print(t['python'])
print(' '.join(f'{k}=={v}' for k, v in t['pip'].items()))
PY
)
key=$(printf '%s\n' "$platform" "${pins[@]}" | sha256sum | cut -c1-16)
dir=$(arh_config_get "$state/config/site.md" tools_dir "")
dir=${dir:-${ARH_ENV_CACHE:+$ARH_ENV_CACHE/tools}}
dir=${dir:-$state/envs/tools}
dir=$(eval echo "$dir")           # tools_dir may name $USER
prefix="$dir/$key"

build() {
  mkdir -p "$prefix/bin"
  local tmp name url sha got
  tmp=$(mktemp -d)
  for line in "${pins[@]:0:3}"; do
    read -r name url sha <<<"$line"
    curl -fsSL --retry 3 -o "$tmp/$name.tgz" "$url"
    got=$(sha256sum "$tmp/$name.tgz" | cut -d' ' -f1)
    [ "$got" = "$sha" ] || { echo "$name checksum mismatch: expected $sha, got $got" >&2; rm -rf "$tmp"; return 1; }
    mkdir -p "$tmp/$name"; tar -xzf "$tmp/$name.tgz" -C "$tmp/$name"
    find "$tmp/$name" -type f -name "$name" -perm -u+x -exec cp {} "$prefix/bin/$name" \;
    [ -x "$prefix/bin/$name" ] || { echo "no $name binary in $url" >&2; rm -rf "$tmp"; return 1; }
  done
  rm -rf "$tmp"
  export UV_CACHE_DIR="$dir/uv-cache" UV_PYTHON_INSTALL_DIR="$dir/python"
  "$prefix/bin/uv" venv -q --python "${pins[3]}" "$prefix/venv"
  # basic-memory 0.23.2 pins a pre-release (fastmcp 4.0.0b1). With a lock from an earlier build, its
  # exact versions are installed instead of a fresh resolution.
  if [ -s "$state/tools-pip.lock" ]; then
    VIRTUAL_ENV="$prefix/venv" "$prefix/bin/uv" pip sync -q "$state/tools-pip.lock"
  else
    # shellcheck disable=SC2086
    VIRTUAL_ENV="$prefix/venv" "$prefix/bin/uv" pip install -q --prerelease=allow ${pins[4]}
  fi
  ln -sf ../venv/bin/bm "$prefix/bin/bm"
}
if [ -n "${ARH_ENV_CACHE:-}" ]; then arh_build_once "$prefix" build || { echo "failed to build $prefix" >&2; exit 1; }
elif [ ! -x "$prefix/bin/bm" ]; then build; fi

VIRTUAL_ENV="$prefix/venv" "$prefix/bin/uv" pip freeze -q > "$state/tools-pip.lock"
# basic-memory's embedding model, fetched now so that a search never reaches the network (the
# directory enable-record.sh names in basic-memory's configuration).
[ -d "$dir/fastembed" ] || "$prefix/venv/bin/python" -c 'import sys; from fastembed import TextEmbedding
TextEmbedding("BAAI/bge-small-en-v1.5", cache_dir=sys.argv[1])' "$dir/fastembed" >/dev/null 2>&1 \
  || echo "warning: basic-memory's embedding model was not fetched; the first arh memory search will fetch it" >&2
python3 - "$state/config/site.md" "$prefix" <<'PY'
from pathlib import Path
import re, sys
p = Path(sys.argv[1]); text = p.read_text(); pat = r'(?m)^tools_prefix\s*=.*$'
line = f'tools_prefix = {sys.argv[2]}'
p.write_text(re.sub(pat, line, text) if re.search(pat, text) else text + f'\n```arh-config\n{line}\n```\n')
PY
printf 'Tools ready: %s/bin (entire %s, gitleaks %s, bm)\n' "$prefix" \
  "$("$prefix/bin/entire" version 2>/dev/null | head -1 | awk '{print $NF}')" "$("$prefix/bin/gitleaks" version 2>/dev/null)"
