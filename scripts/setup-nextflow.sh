#!/usr/bin/env bash
# Host controller: bootstrap a pinned micromamba binary and Nextflow environment.
set -euo pipefail

usage() {
  cat >&2 <<'USAGE'
usage: scripts/setup-nextflow.sh PROJECT [MICROMAMBA_BINARY]

Without MICROMAMBA_BINARY, this script reuses the pinned project-local binary,
uses the checksum-matching pinned micromamba already on PATH, or downloads and
checksum-verifies the pinned standalone binary into .arh/tools/.
USAGE
}
[ $# -ge 1 ] && [ $# -le 2 ] || { usage; exit 2; }

home=${ARH_HOME:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}
project=$(cd "$1" && pwd)
provided=${2-}
[ -d "$project/.arh" ] || { echo 'run arh init first' >&2; exit 1; }
state="$project/.arh"

deps="$home/config/dependencies.json"
[ -f "$deps" ] || { echo "dependency manifest missing: $deps" >&2; exit 1; }

case "$(uname -s)-$(uname -m)" in
  Linux-x86_64|Linux-amd64) platform=linux-64 ;;
  Linux-aarch64|Linux-arm64) platform=linux-aarch64 ;;
  Linux-ppc64le) platform=linux-ppc64le ;;
  *) echo "unsupported host platform for automatic micromamba bootstrap: $(uname -s)-$(uname -m)" >&2; exit 1 ;;
esac

read -r mm_version mm_release mm_sha nextflow_version python_version <<EOF_DEPS
$(python3 - "$deps" "$platform" <<'PY'
import json, sys
with open(sys.argv[1]) as fh:
    d = json.load(fh)
mm = d['micromamba']
print(mm['version'], mm['release'], mm['sha256'][sys.argv[2]], d['nextflow']['version'], d['python']['version'])
PY
)
EOF_DEPS
mm_url="https://github.com/mamba-org/micromamba-releases/releases/download/${mm_release}/micromamba-${platform}"

sha256_file() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | awk '{print $1}'
  else echo 'need sha256sum or shasum to verify micromamba' >&2; return 1
  fi
}

sha256_stdin() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum | awk '{print $1}'
  else shasum -a 256 | awk '{print $1}'; fi
}

download_file() {
  if command -v curl >/dev/null 2>&1; then
    curl -fL --retry 3 --connect-timeout 15 -o "$2" "$1"
  elif command -v wget >/dev/null 2>&1; then
    wget -O "$2" "$1"
  else
    echo 'automatic micromamba bootstrap needs curl or wget' >&2
    return 1
  fi
}

micromamba=""
source_kind=""
if [ -n "$provided" ]; then
  micromamba=$(cd "$(dirname "$provided")" && pwd)/$(basename "$provided")
  [ -x "$micromamba" ] || { echo "micromamba binary missing or not executable: $micromamba" >&2; exit 1; }
  source_kind=provided
else
  cached="$state/tools/micromamba/$mm_release/$platform/micromamba"
  if [ -x "$cached" ]; then
    got=$(sha256_file "$cached") || exit 1
    if [ "$got" = "$mm_sha" ]; then
      micromamba="$cached"
      source_kind='project-cache'
    else
      echo "discarding cached micromamba with wrong checksum: $cached" >&2
      rm -f "$cached"
    fi
  fi

  if [ -z "$micromamba" ] && command -v micromamba >/dev/null 2>&1; then
    candidate=$(command -v micromamba)
    candidate_version=$("$candidate" --version 2>/dev/null | head -1 || true)
    candidate_sha=$(sha256_file "$candidate" 2>/dev/null || true)
    if [ "$candidate_version" = "$mm_version" ] && [ "$candidate_sha" = "$mm_sha" ]; then
      micromamba="$candidate"
      source_kind=path
    else
      printf 'Ignoring micromamba on PATH: it is not the pinned %s build.\n' "$mm_release" >&2
    fi
  fi

  if [ -z "$micromamba" ]; then
    mkdir -p "$(dirname "$cached")"
    tmp=$(mktemp "${cached}.tmp.XXXXXX")
    trap 'rm -f "${tmp:-}"' EXIT
    printf 'Downloading pinned micromamba %s for %s...\n' "$mm_release" "$platform"
    if ! download_file "$mm_url" "$tmp"; then
      echo "failed to download pinned micromamba from: $mm_url" >&2
      echo "offline setup: stage a micromamba binary and rerun: $0 $project /path/to/micromamba" >&2
      exit 1
    fi
    got=$(sha256_file "$tmp") || exit 1
    if [ "$got" != "$mm_sha" ]; then
      echo "micromamba checksum mismatch: expected $mm_sha, got $got" >&2
      exit 1
    fi
    chmod 0755 "$tmp"
    mv "$tmp" "$cached"
    trap - EXIT
    micromamba="$cached"
    source_kind=downloaded
  fi
fi

actual_version=$("$micromamba" --version 2>/dev/null | head -1 || true)
[ -n "$actual_version" ] || { echo "cannot execute micromamba: $micromamba" >&2; exit 1; }
if [ "$source_kind" != provided ] && [ "$actual_version" != "$mm_version" ]; then
  echo "pinned micromamba version mismatch: expected $mm_version, got $actual_version" >&2
  exit 1
fi

create_env() {
  "$micromamba" create -y -p "$prefix" -c conda-forge -c bioconda \
    "nextflow=$nextflow_version" "python=$python_version"
}
if [ -n "${ARH_ENV_CACHE:-}" ]; then
  # Shared and content-addressed: every project asking for the same pinned environment reuses one
  # build (~0.7 GB) instead of making its own. Each project still records its own explicit lock.
  mkdir -p "$ARH_ENV_CACHE"; cache=$(cd "$ARH_ENV_CACHE" && pwd)
  key=$(printf '%s\n' "$platform" "nextflow=$nextflow_version" "python=$python_version" conda-forge bioconda | sha256_stdin | cut -c1-16)
  prefix="$cache/nextflow-host/$nextflow_version-$key"
  export MAMBA_ROOT_PREFIX="$cache/mamba-host"
  mkdir -p "$MAMBA_ROOT_PREFIX"
  # shellcheck source=lib/common.sh
  . "$home/lib/common.sh"
  arh_build_once "$prefix" create_env || { echo "failed to build $prefix" >&2; exit 1; }
else
  prefix="$state/envs/nextflow-host/$nextflow_version"
  export MAMBA_ROOT_PREFIX="$state/mamba-host"
  mkdir -p "$MAMBA_ROOT_PREFIX"
  [ -x "$prefix/bin/nextflow" ] || create_env
fi
# A lock `micromamba create --file` accepts: @EXPLICIT plus URL#md5 lines. Plain
# `list --explicit` output starts with a header and cannot be replayed.
{ echo '@EXPLICIT'; "$micromamba" list -p "$prefix" --explicit --md5 | grep -E '^https?://'; } \
  > "$state/nextflow-host-explicit.lock"
mm_digest=$(sha256_file "$micromamba") || exit 1
cat > "$state/micromamba.lock" <<EOF_LOCK
version=$actual_version
expected_release=$mm_release
platform=$platform
sha256=$mm_digest
source=$source_kind
binary=$micromamba
EOF_LOCK

# setup-runtime.sh rewrites the same file; serialise so concurrent setups cannot drop keys.
lock="$state/config/.site.lock"; i=0
until mkdir "$lock" 2>/dev/null; do
  i=$((i+1)); [ "$i" -lt 120 ] || { echo "site.md locked by another setup: $lock (remove if stale)" >&2; exit 1; }
  sleep 1
done
trap 'rmdir "$lock" 2>/dev/null || true' EXIT
"$prefix/bin/python3" - "$state/config/site.md" "$prefix" "$nextflow_version" <<'PY'
from pathlib import Path
import re,sys
p=Path(sys.argv[1]); text=p.read_text(); prefix=sys.argv[2]; version=sys.argv[3]
for key,value in {'nextflow_prefix':prefix,'nextflow_version':version}.items():
    pat=r'(?m)^'+re.escape(key)+r'\s*=.*$'
    text=re.sub(pat, f'{key} = {value}', text) if re.search(pat,text) else text+f'\n```arh-config\n{key} = {value}\n```\n'
p.write_text(text)
PY
printf 'Micromamba: %s (%s)\n' "$micromamba" "$source_kind"
printf 'Host Nextflow ready: %s/bin/nextflow\n' "$prefix"
