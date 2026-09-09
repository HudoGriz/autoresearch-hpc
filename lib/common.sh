#!/usr/bin/env bash
# discovery-loop — shared shell library. Sourced by every bin/dl-* command.
set -euo pipefail

DL_HOME="${DL_HOME:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
export DL_HOME

dl_die()  { printf 'dl: %s\n' "$*" >&2; exit 1; }
dl_warn() { printf 'dl: %s\n' "$*" >&2; }
dl_info() { printf '  %s\n' "$*"; }
dl_ok()   { printf '  OK   %s\n' "$*"; }
dl_fail() { printf '  FAIL %s\n' "$*"; }

# ---------------------------------------------------------------------------
# Config files are Markdown. Machine-readable settings live in fenced blocks
# tagged `dl-config`, as `key = value`. Everything outside those blocks is
# documentation for the human and is ignored by the parser.
# ---------------------------------------------------------------------------
dl_config_get() {   # <file> <key> [default]
  local file="$1" key="$2" default="${3-}" val
  [ -f "$file" ] || { printf '%s' "$default"; return 0; }
  val=$(awk -v key="$key" '
    /^[ \t]*```[ \t]*dl-config[ \t]*$/ { inb=1; next }
    /^[ \t]*```/                       { inb=0; next }
    !inb                               { next }
    /^[ \t]*#/                         { next }
    {
      n = index($0, "=")
      if (n == 0) next
      k = substr($0, 1, n-1); v = substr($0, n+1)
      gsub(/^[ \t]+|[ \t]+$/, "", k)
      gsub(/^[ \t]+|[ \t]+$/, "", v)
      if (k == key) { print v; found=1; exit }
    }' "$file")
  [ -n "$val" ] && printf '%s' "$val" || printf '%s' "$default"
}

dl_config_keys() {  # <file>  -> list all keys
  awk '
    /^[ \t]*```[ \t]*dl-config[ \t]*$/ { inb=1; next }
    /^[ \t]*```/                       { inb=0; next }
    !inb || /^[ \t]*#/                 { next }
    { n = index($0, "="); if (n) { k=substr($0,1,n-1); gsub(/^[ \t]+|[ \t]+$/,"",k); print k } }' "$1"
}

# ---------------------------------------------------------------------------
# Project discovery: walk up from $PWD looking for the .dl/ marker directory.
# ---------------------------------------------------------------------------
dl_find_project() {
  local d="${DL_PROJECT:-$PWD}"
  d=$(cd "$d" 2>/dev/null && pwd) || dl_die "cannot resolve $d"
  while [ "$d" != "/" ]; do
    [ -d "$d/.dl" ] && { printf '%s' "$d"; return 0; }
    d=$(dirname "$d")
  done
  dl_die "not inside a discovery-loop project (no .dl/ found). Run: dl init <dir>"
}

dl_load_project() {
  DL_ROOT=$(dl_find_project)
  DL_CONF="$DL_ROOT/.dl/config"
  DL_SITE="$DL_CONF/site.md"
  DL_PROJ="$DL_CONF/project.md"
  DL_HARN="$DL_CONF/harnesses.md"
  DL_ITERS="$DL_ROOT/$(dl_config_get "$DL_PROJ" iterations_dir iterations)"
  DL_VERIFY="$DL_ROOT/$(dl_config_get "$DL_PROJ" verification_dir verification)"
  DL_LEDGER="$DL_ROOT/$(dl_config_get "$DL_PROJ" ledger PROGRESS.md)"
  DL_REGISTRY="$DL_ROOT/.dl/registry.tsv"
  export DL_ROOT DL_CONF DL_SITE DL_PROJ DL_HARN DL_ITERS DL_VERIFY DL_LEDGER DL_REGISTRY
}

dl_now()   { date -u +%Y-%m-%dT%H:%M:%SZ; }
dl_today() { date -u +%Y-%m-%d; }

# Portable `readlink -m`: absolutise and normalise a path that need not exist.
# BSD/macOS readlink has no -m, so fall back to python3 (already a dependency).
dl_abspath() {
  if readlink -m / >/dev/null 2>&1; then
    readlink -m -- "$1"
  else
    python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$1"
  fi
}

dl_sha256() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | awk '{print $1}'
  elif command -v shasum   >/dev/null 2>&1; then shasum -a 256 "$1" | awk '{print $1}'
  else dl_die "no sha256sum or shasum available"; fi
}

# Identity of the agent doing the work, for claim records.
dl_agent() {
  printf '%s' "${DL_AGENT:-${CLAUDECODE:+claude}${DL_AGENT:-}}" 2>/dev/null || true
  :
}
dl_agent_name() {
  if [ -n "${DL_AGENT:-}" ]; then printf '%s' "$DL_AGENT"
  elif [ -n "${CLAUDECODE:-}" ]; then printf 'claude'
  elif [ -n "${CODEX_SANDBOX:-}${CODEX_HOME:-}" ]; then printf 'codex'
  elif [ -n "${OPENCODE:-}" ]; then printf 'opencode'
  else printf '%s' "${USER:-unknown}"; fi
}

# Immutable-input guard. Refuses any write path outside the project root, or
# inside a path listed as immutable in project.md.
dl_guard_path() {   # <path...>
  local p abs immutable
  immutable=$(dl_config_get "$DL_PROJ" immutable_inputs "")
  for p in "$@"; do
    abs=$(dl_abspath "$p")
    case "$abs" in
      "$DL_ROOT"/*) ;;
      *) dl_die "refusing write outside project root: $abs" ;;
    esac
    local ip
    for ip in $immutable; do
      [ -n "$ip" ] || continue
      case "$abs" in "$ip"/*|"$ip") dl_die "immutable input path: $abs" ;; esac
    done
  done
}
