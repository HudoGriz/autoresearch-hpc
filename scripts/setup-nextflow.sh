#!/usr/bin/env bash
# Host controller: the pinned Nextflow with its Java, and the Python arh itself runs on, as a
# locked pixi environment in .arh/envs/nextflow-host (pixi.toml and pixi.lock are the record).
#
#   scripts/setup-nextflow.sh PROJECT
#
# Offline: ARH_PIXI=/path/to/pixi and a filled package cache (PIXI_CACHE_DIR).
set -euo pipefail
[ $# -eq 1 ] || { echo 'usage: scripts/setup-nextflow.sh PROJECT' >&2; exit 2; }
ARH_HOME=${ARH_HOME:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}; export ARH_HOME
state="$(cd "$1" && pwd)/.arh"
[ -d "$state" ] || { echo 'run arh init first' >&2; exit 1; }
# shellcheck source=lib/common.sh
. "$ARH_HOME/lib/common.sh"
version=$(python3 -c 'import json, sys; print(json.load(open(sys.argv[1]))["nextflow"]["version"])' "$ARH_HOME/config/dependencies.json")
dir="$state/envs/nextflow-host"
if grep -q "nextflow-$version-" "$dir/pixi.lock" 2>/dev/null && grep -q '/python-3\.12' "$dir/pixi.lock"; then
  prefix=$(arh_pixi_env "$state" "$dir")
else prefix=$(arh_pixi_env "$state" "$dir" "nextflow==$version" python=3.12); fi
arh_config_set "$state/config/site.md" nextflow_prefix "$prefix" nextflow_version "$version"
printf 'Host Nextflow ready: %s/bin/nextflow\n' "$prefix"
