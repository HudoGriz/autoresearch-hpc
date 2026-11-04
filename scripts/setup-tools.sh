#!/usr/bin/env bash
# Integrations: install the pinned tools ARH turns on by default, in seconds.
#
# Entire CLI (agent sessions), gitleaks (credential rules) and abtop (live sessions) are release
# binaries checked by sha256; basic-memory (search over knowledge/) is a pixi environment locked in
# .arh/tools-pixi.lock; the research and coding skills (ARIS, Ponytail) are pinned
# source archives extracted under .arh/skills/, where every node and account of the project can read
# them. Pins: config/dependencies.json. What each tool does and how to switch it off:
# docs/integrations.md.
#
# Binaries and the package cache go to tools_dir in site.md (node-local on CephFS or NFS: seconds,
# not minutes), else $ARH_ENV_CACHE/tools, else .arh/envs/tools.
set -euo pipefail
[ $# -eq 1 ] || { echo 'usage: scripts/setup-tools.sh PROJECT' >&2; exit 2; }
ARH_HOME=${ARH_HOME:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}; export ARH_HOME
project=$(cd "$1" && pwd)
state="$project/.arh"
[ -d "$state" ] || { echo 'run arh init first' >&2; exit 1; }
# shellcheck source=lib/common.sh
. "$ARH_HOME/lib/common.sh"

# One line per download (kind name url sha256), then the tool environment's specs.
mapfile -t pins < <(python3 - "$ARH_HOME/config/dependencies.json" <<'PY'
import json, platform, sys
t = json.load(open(sys.argv[1]))['tools']
arch = platform.machine().replace('arm64', 'aarch64')
names = dict(goarch={'x86_64': 'amd64'}.get(arch, 'arm64'), glarch={'x86_64': 'x64'}.get(arch, 'arm64'), arch=arch)
for name in ('entire', 'gitleaks', 'abtop'):
    b = t[name]
    print('bin', name, b['url'].format(version=b['version'], **names), b['sha256'].get(arch, 'none'))
for name, s in t['skills'].items():
    print('skills', name, s['url'].format(version=s['version']), s['sha256'])
print('env', ' '.join(t['env']))
PY
)
dir=$(arh_tools_dir "$state")
prefix="$dir/$(printf '%s\n' "$(uname -m)" "${pins[@]}" | grep -v '^skills ' | sha256sum | cut -c1-16)"  # binaries and env only
fetch() {  # URL SHA256 FILE
  curl -fsSL --retry 3 -o "$3" "$1" && [ "$(arh_sha256 "$3")" = "$2" ] \
    || { echo "download failed or checksum mismatch: $1" >&2; return 1; }
}
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
mkdir -p "$prefix/bin" "$state/skills"
for line in "${pins[@]}"; do
  read -r kind name url sha <<<"$line"
  case "$kind" in
    bin)
      [ -x "$prefix/bin/$name" ] && continue
      fetch "$url" "$sha" "$tmp/$name.tar" && mkdir -p "$tmp/$name" && tar -xf "$tmp/$name.tar" -C "$tmp/$name"
      find "$tmp/$name" -type f -name "$name" -perm -u+x -exec cp {} "$prefix/bin/$name" \;
      [ -x "$prefix/bin/$name" ] || { echo "no $name binary in $url" >&2; exit 1; } ;;
    skills)
      # Only the skill trees and the tools they call; the archive is replaced when its pin changes.
      [ "$(cat "$state/skills/$name/.sha256" 2>/dev/null)" = "$sha" ] && continue
      fetch "$url" "$sha" "$tmp/$name.tgz"
      rm -rf "$state/skills/$name"; mkdir -p "$state/skills/$name"
      tar -xzf "$tmp/$name.tgz" -C "$state/skills/$name" --strip-components=1 --exclude='.*' --wildcards \
        '*/skills/*' '*/workflows/*' '*/tools/*' 2>/dev/null || true
      [ -n "$(find "$state/skills/$name" -name SKILL.md -print -quit)" ] || { echo "no SKILL.md in $url" >&2; exit 1; }
      printf '%s\n' "$sha" > "$state/skills/$name/.sha256" ;;
  esac
done
for d in "$state/skills"/*/; do                    # a source no longer pinned goes with its pin
  if [ -f "$d/.sha256" ] && ! printf '%s\n' "${pins[@]}" | grep -q "^skills $(basename "$d") "; then rm -rf "$d"; fi
done

# basic-memory, replayed exactly from the project's lock once one exists.
read -r _ specs <<<"${pins[-1]}"
if [ ! -x "$prefix/bm/.pixi/envs/default/bin/bm" ]; then
  if [ -s "$state/tools-pixi.lock" ] && [ -f "$state/tools-pixi.toml" ]; then
    mkdir -p "$prefix/bm"; cp "$state/tools-pixi.toml" "$prefix/bm/pixi.toml"; cp "$state/tools-pixi.lock" "$prefix/bm/pixi.lock"
    ARH_CHANNELS=conda-forge arh_pixi_env "$state" "$prefix/bm" >/dev/null
  else
    # shellcheck disable=SC2086
    ARH_CHANNELS=conda-forge arh_pixi_env "$state" "$prefix/bm" $specs >/dev/null
  fi
fi
cp "$prefix/bm/pixi.toml" "$state/tools-pixi.toml"; cp "$prefix/bm/pixi.lock" "$state/tools-pixi.lock"
ln -sf ../bm/.pixi/envs/default/bin/bm "$prefix/bin/bm"
# basic-memory's embedding model, fetched now so that a search never reaches the network (the
# directory enable-record.sh names in basic-memory's configuration).
[ -d "$dir/fastembed" ] || "$prefix/bm/.pixi/envs/default/bin/python" -c 'import sys; from fastembed import TextEmbedding
TextEmbedding("BAAI/bge-small-en-v1.5", cache_dir=sys.argv[1])' "$dir/fastembed" >/dev/null 2>&1 \
  || echo "warning: basic-memory's embedding model was not fetched; the first arh memory search will fetch it" >&2
arh_config_set "$state/config/site.md" tools_prefix "$prefix"
printf 'Tools ready: %s/bin (entire, gitleaks, abtop, bm); skills in .arh/skills/ (%s)\n' "$prefix" \
  "$(cd "$state/skills" && ls | paste -sd' ' -)"
