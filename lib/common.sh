#!/usr/bin/env bash
# AutoResearch HPC — shared shell library. Sourced by bin/arh-* commands.
set -euo pipefail

ARH_HOME="${ARH_HOME:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
export ARH_HOME

arh_die()  { printf 'arh: %s\n' "$*" >&2; exit 1; }
arh_warn() { printf 'arh: %s\n' "$*" >&2; }
arh_info() { printf '  %s\n' "$*"; }
arh_ok()   { printf '  OK   %s\n' "$*"; }
arh_fail() { printf '  FAIL %s\n' "$*"; }

# Config files are Markdown. Machine-readable settings live only in
# fenced `arh-config` blocks as `key = value`.
arh_config_get() {
  local file="$1" key="$2" default="${3-}" val
  [ -f "$file" ] || { printf '%s' "$default"; return 0; }
  val=$(awk -v key="$key" '
    /^[ \t]*```[ \t]*arh-config[ \t]*$/ { inb=1; next }
    /^[ \t]*```/    { inb=0; next }
    !inb   { next }
    /^[ \t]*#/       { next }
    {
      n = index($0, "=")
      if (n == 0) next
      k = substr($0, 1, n-1); v = substr($0, n+1)
      gsub(/^[ \t]+|[ \t]+$/, "", k)
      gsub(/^[ \t]+|[ \t]+$/, "", v)
      if (k == key) { print v; exit }
    }' "$file")
  [ -n "$val" ] && printf '%s' "$val" || printf '%s' "$default"
}

arh_config_keys() {
  awk '
    /^[ \t]*```[ \t]*arh-config[ \t]*$/ { inb=1; next }
    /^[ \t]*```/    { inb=0; next }
    !inb || /^[ \t]*#/        { next }
    { n=index($0,"="); if(n){ k=substr($0,1,n-1); gsub(/^[ \t]+|[ \t]+$/,"",k); print k } }' "$1"
}

arh_find_project() {
  local d="${ARH_PROJECT:-$PWD}"
  d=$(cd "$d" 2>/dev/null && pwd) || arh_die "cannot resolve $d"
  while [ "$d" != "/" ]; do
    [ -d "$d/.arh" ] && { printf '%s' "$d"; return 0; }
    d=$(dirname "$d")
  done
  arh_die "not inside an AutoResearch HPC project (no .arh/ found from ${ARH_PROJECT:-$PWD}).
       Run: arh init <dir>, or export ARH_PROJECT=<study> to work from any directory"
}

arh_load_project() {
  ARH_ROOT=$(arh_find_project)
  ARH_STATE="$ARH_ROOT/.arh"
  ARH_CONF="$ARH_STATE/config"
  ARH_SITE="$ARH_CONF/site.md"
  ARH_PROJ="$ARH_CONF/project.md"
  ARH_HARN="$ARH_CONF/harnesses.md"
  ARH_ITERS="$ARH_ROOT/$(arh_config_get "$ARH_PROJ" iterations_dir iterations)"
  ARH_VERIFY="$ARH_ROOT/$(arh_config_get "$ARH_PROJ" verification_dir verification)"
  ARH_LEDGER="$ARH_ROOT/$(arh_config_get "$ARH_PROJ" ledger PROGRESS.md)"
  ARH_REGISTRY="$ARH_STATE/registry.tsv"
  export ARH_ROOT ARH_STATE ARH_CONF ARH_SITE ARH_PROJ ARH_HARN ARH_ITERS ARH_VERIFY ARH_LEDGER ARH_REGISTRY
}

arh_now()   { date -u +%Y-%m-%dT%H:%M:%SZ; }
arh_today() { date -u +%Y-%m-%d; }

arh_abspath() {
  if readlink -m / >/dev/null 2>&1; then
    readlink -m -- "$1"
  else
    python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$1"
  fi
}

arh_sha256() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | awk '{print $1}'
  else arh_die "no sha256sum or shasum available"; fi
}

arh_agent() {
  printf '%s' "${ARH_AGENT:-${CLAUDECODE:+claude}}" 2>/dev/null || true
  :
}

arh_agent_name() {
  if [ -n "${ARH_AGENT:-}" ]; then printf '%s' "$ARH_AGENT"
  elif [ -n "${CLAUDECODE:-}" ]; then printf 'claude'
  elif [ -n "${CODEX_SANDBOX:-}${CODEX_HOME:-}" ]; then printf 'codex'
  elif [ -n "${OPENCODE:-}" ]; then printf 'opencode'
  else printf '%s' "${USER:-unknown}"; fi
}

arh_guard_path() {
  local p abs immutable ip
  immutable=$(arh_config_get "$ARH_PROJ" immutable_inputs "")
  for p in "$@"; do
    abs=$(arh_abspath "$p")
    case "$abs" in "$ARH_ROOT"/*) ;; *) arh_die "refusing write outside project root: $abs" ;; esac
    for ip in $immutable; do
      [ -n "$ip" ] || continue
      case "$ip" in /*) ;; *) ip="$ARH_ROOT/$ip" ;; esac
      ip=$(arh_abspath "$ip")
      case "$abs" in "$ip"/*|"$ip") arh_die "immutable input path: $abs" ;; esac
    done
  done
}

arh_crosschecks() {
  python3 "$ARH_HOME/lib/harness.py" valid "$1" | sed '/^$/d'
}
