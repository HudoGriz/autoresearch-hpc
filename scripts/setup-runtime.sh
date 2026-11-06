#!/usr/bin/env bash
# Task runtime: a digest-pinned image, which needs nothing installed in it, and the environment every
# task needs (bash, ps for Nextflow's task metrics, python, git), locked with pixi in
# .arh/envs/runtime and bound read-only into each task.
#
#   scripts/setup-runtime.sh PROJECT RUNTIME.sif
set -euo pipefail
[ $# -eq 2 ] || { echo 'usage: scripts/setup-runtime.sh PROJECT RUNTIME.sif' >&2; exit 2; }
ARH_HOME=${ARH_HOME:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}; export ARH_HOME
state="$(cd "$1" && pwd)/.arh"
image=$(cd "$(dirname "$2")" && pwd)/$(basename "$2")
[ -d "$state" ] || { echo 'run arh init first' >&2; exit 1; }
[ -f "$image" ] || { echo 'runtime SIF is missing' >&2; exit 1; }
# shellcheck source=lib/common.sh
. "$ARH_HOME/lib/common.sh"
runtime=$(command -v singularity >/dev/null 2>&1 && echo singularity || echo apptainer)
dir="$state/envs/runtime"
if [ -f "$dir/pixi.lock" ]; then prefix=$(arh_pixi_env "$state" "$dir")
else prefix=$(arh_pixi_env "$state" "$dir" 'python=3.12' bash procps-ng git); fi
arh_config_set "$state/config/site.md" runtime_image "$image" runtime_prefix "$prefix" \
  runtime_sha256 "$(arh_sha256 "$image")" container_runtime "$runtime"
printf 'Runtime ready: %s\nEnvironment: %s\n' "$image" "$prefix"
