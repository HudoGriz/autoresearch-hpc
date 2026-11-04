#!/usr/bin/env bash
# AutoResearch HPC — shared shell library. Sourced by bin/arh-* commands.
set -euo pipefail

ARH_HOME="${ARH_HOME:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
export ARH_HOME

arh_die()  { printf 'arh: %s\n' "$*" >&2; exit 1; }
arh_warn() { printf 'arh: %s\n' "$*" >&2; }
arh_info() { printf '  %s\n' "$*"; }
# Gates and doctor list only what needs attention unless asked (-v or ARH_VERBOSE=1): their passing
# checks were most of what an agent read from them, every time it ran them. They count instead.
arh_ok()   { if [ "${ARH_QUIET_OK:-0}" = 1 ]; then ARH_OK_COUNT=$(( ${ARH_OK_COUNT:-0} + 1 )); else printf '  OK   %s\n' "$*"; fi; }
arh_ok_summary() { [ "${ARH_OK_COUNT:-0}" = 0 ] || printf '  OK   %s check(s) passed (-v lists them)\n' "$ARH_OK_COUNT"; }
arh_fail() { printf '  FAIL %s\n' "$*"; }

# arh_config_set FILE KEY VALUE...: set each KEY = VALUE in place, or append it in its own block.
# Serialised, so setups running at once cannot drop each other's keys.
arh_config_set() {
  local file="$1"; shift
  ( flock 9; python3 -c 'import re, sys
from pathlib import Path
p = Path(sys.argv[1]); text = p.read_text(); kv = sys.argv[2:]
for key, value in zip(kv[::2], kv[1::2]):
    pat = r"(?m)^" + re.escape(key) + r"\s*=.*$"
    text = re.sub(pat, lambda m: f"{key} = {value}", text) if re.search(pat, text) else text + f"\n```arh-config\n{key} = {value}\n```\n"
p.write_text(text)' "$file" "$@" ) 9<"$file"
}

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

# An iteration's own harnesses.md (arh claim --worker/--reviewer/..., arh roles) overrides the project's
# for that iteration only. Its keys come first in a generated effective file, and the first value wins.
# Without one, the project's file is the iteration's, so older claims keep their terms hash.
arh_iter_harn() {
  local dir="$1" eff="$1/metadata/harnesses.effective.md" project="${ARH_HARN_PROJECT:-$ARH_HARN}"
  [ -f "$dir/harnesses.md" ] || { printf '%s' "$project"; return 0; }
  mkdir -p "$dir/metadata"
  { printf '# Generated: %s/harnesses.md first, then the project'"'"'s harnesses.md. Edit those, not this.\n\n' "${dir##*/}"
    cat "$dir/harnesses.md"; printf '\n'; cat "$project" 2>/dev/null; } > "$eff.tmp" && mv "$eff.tmp" "$eff"
  printf '%s' "$eff"
}

# Set KEY=VALUE pairs in iteration DIR's own harnesses.md (created on first use). The role names map to
# the project keys they override: worker = iteration_controller, reviewer = verifier,
# orchestrator = orchestrator, on-limit = dispatch_on_limit; any other KEY is used as written.
arh_set_iter_harn() {
  local dir="$1"; shift
  python3 - "$dir/harnesses.md" "${ARH_HARN_PROJECT:-$ARH_HARN}" "$@" <<'PY' || return 1
import re, sys
from pathlib import Path
own, project, pairs = Path(sys.argv[1]), sys.argv[2], sys.argv[3:]
sys.path.insert(0, __import__('os').environ['ARH_HOME'] + '/lib')
from project import config
alias = {'worker': 'iteration_controller', 'worker-fallback': 'iteration_controller_fallback', 'reviewer': 'verifier',
         'reviewer-fallback': 'verifier_fallback', 'orchestrator': 'orchestrator', 'on-limit': 'dispatch_on_limit'}
roles = {'iteration_controller', 'iteration_controller_fallback', 'verifier', 'verifier_fallback', 'orchestrator'}
values, known = config(own), config(project)
for pair in pairs:
    key, sep, value = pair.partition('=')
    key = alias.get(key, key)
    if not sep or not re.fullmatch(r'[a-z][a-z0-9_]*', key):
        sys.exit(f"arh: expected KEY=VALUE, not '{pair}'")
    if key in roles:
        for h in value.split():
            if not known.get(f'harness_{h}_cmd'):
                sys.exit(f"arh: no harness '{h}' in {project} (harness_{h}_cmd); define it there first")
    if key == 'dispatch_on_limit' and value not in ('fallback', 'wait', 'stop'):
        sys.exit("arh: on-limit must be fallback, wait or stop")
    values[key] = value
body = ''.join(f'{k} = {v}\n' for k, v in values.items())
own.write_text('# This iteration\'s own harness settings; they override .arh/config/harnesses.md for it only.\n\n'
               f'```arh-config\n{body}```\n')
PY
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
  ARH_HARN="$ARH_CONF/harnesses.md"; ARH_HARN_PROJECT="$ARH_HARN"
  ARH_ITERS="$ARH_ROOT/$(arh_config_get "$ARH_PROJ" iterations_dir iterations)"
  ARH_VERIFY="$ARH_ROOT/$(arh_config_get "$ARH_PROJ" verification_dir verification)"
  ARH_LEDGER="$ARH_ROOT/$(arh_config_get "$ARH_PROJ" ledger PROGRESS.md)"
  ARH_REGISTRY="$ARH_STATE/registry.tsv"
  # The operator's directives file; a study that kept them in VALIDATION_PROTOCOL.md names it (#47).
  ARH_DIRECTIVES="$ARH_ROOT/$(arh_config_get "$ARH_PROJ" directives DIRECTIVES.md)"
  # Which environment variables carry the harness's own session id (harnesses.md session_env).
  # Unset, the variables Claude Code and Codex set (feedback #129); every harness is also identified
  # by its process (agent_process), so a harness without such a variable is still linked.
  ARH_SESSION_ENV=$(arh_config_get "$ARH_HARN" session_env "CLAUDE_CODE_SESSION_ID CODEX_SESSION_ID")
  # auto: gitleaks's maintained rules on top of the built-in patterns when gitleaks is installed.
  ARH_SECRET_SCANNER=$(arh_config_get "$ARH_HARN" secret_scanner auto)
  export ARH_ROOT ARH_STATE ARH_CONF ARH_SITE ARH_PROJ ARH_HARN ARH_HARN_PROJECT ARH_ITERS ARH_VERIFY ARH_LEDGER ARH_REGISTRY ARH_DIRECTIVES \
    ARH_SESSION_ENV ARH_SECRET_SCANNER
}

# mktemp makes files 0600 and directories 0700. Anything arh keeps in the project gets the mode the
# umask gives other files (a directory keeps its setgid bit), or a project shared between accounts
# through a group hides its records from the other account (field feedback #88).
arh_share_mode() {
  local p m
  m=$(umask)
  for p in "$@"; do
    if [ -d "$p" ]; then chmod "$(printf '%o' $(( 0777 & ~m )))" "$p"
    elif [ -e "$p" ]; then chmod "$(printf '%o' $(( 0666 & ~m )))" "$p"; fi
  done
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

# What decided arh_agent_name. Harness markers are inherited by child processes, so a
# Codex session started from inside Claude Code still carries CLAUDECODE; claims record
# the source so a wrong inference is visible in the record.
arh_agent_source() {
  if [ -n "${ARH_AGENT:-}" ]; then printf 'ARH_AGENT'
  elif [ -n "${CLAUDECODE:-}" ]; then printf 'CLAUDECODE'
  elif [ -n "${CODEX_SANDBOX:-}${CODEX_HOME:-}" ]; then printf 'CODEX_SANDBOX/CODEX_HOME'
  elif [ -n "${OPENCODE:-}" ]; then printf 'OPENCODE'
  else printf 'USER'; fi
}

# Warn when the session's idea of the agent differs from the configured producer.
# ARH_AGENT is deliberately NOT exempt: the agent contract tells a session to set it to
# its own harness name ("claude", "codex", ...), which silently discards the model and
# account a lane pinned into the producer name. That override is exactly what needs
# reporting, so only a plain USER fallback (a human at a shell) is exempt.
arh_warn_agent_mismatch() {
  local name source producer
  name=$(arh_agent_name); source=$(arh_agent_source)
  producer=$(arh_config_get "$ARH_HARN" producer "")
  case "$source" in USER) return 0 ;; esac
  [ -n "$producer" ] && [ "$name" != "$producer" ] || return 0
  arh_warn "agent '$name' came from $source, but the configured producer is '$producer'."
  arh_warn "the configured producer is authoritative; pass 'arh claim -a NAME' to record a different agent"
}

arh_guard_path() {
  local p abs immutable ip
  immutable="$(arh_config_get "$ARH_PROJ" immutable_inputs "") $(! arh_has_sealed || python3 "$ARH_HOME/lib/freeze.py" sealed "$ARH_ROOT" | tr '\n' ' ')"
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

# The frozen pre-declaration fixes the science; the review terms (verifier, fallbacks, family rule,
# bounds) live in harnesses.md, which a producing agent could once edit without a trace (2026-09-16).
# arh claim now binds them to the iteration. Prints changed, unchanged, or unrecorded for claims
# older than the hash.
arh_harness_config_state() {
  local claimed
  claimed=$(sed -n 's/.*"harness_config_sha256"[ ]*:[ ]*"\([0-9a-f]\{64\}\)".*/\1/p' "$1/CLAIM.json" 2>/dev/null | head -1)
  if [ -z "$claimed" ]; then echo unrecorded
  elif [ "$claimed" = "$(arh_sha256 "$(arh_iter_harn "$1")" 2>/dev/null)" ]; then echo unchanged
  else echo changed; fi
}

# The value of a review-policy key (require_crosscheck, review_response, unsound_review) that iteration
# DIR is judged by: the one recorded when it was claimed, else project.md's (claims older than the
# record). A later edit of project.md is named on stderr and does not apply.
# arh_tier DIR — exploratory or confirmatory (the default, and every iteration claimed before tiers).
arh_tier() {
  if grep -q '"tier": *"exploratory"' "$1/CLAIM.json" 2>/dev/null; then echo exploratory; else echo confirmatory; fi
}

arh_review_policy() {
  local dir="$1" key="$2" default="$3" current claimed
  current=$(arh_config_get "$ARH_PROJ" "$key" "$default")
  claimed=$(python3 -c 'import json, sys
try:
    print(json.load(open(sys.argv[1])).get("review_policy", {}).get(sys.argv[2], ""))
except (OSError, ValueError, AttributeError):
    print("")' "$dir/CLAIM.json" "$key")
  if [ -n "$claimed" ]; then
    [ "$claimed" = "$current" ] || printf '  NOTE %s = %s in project.md, but %s when iteration %s was claimed: the claimed value applies\n' \
      "$key" "$current" "$claimed" "${dir##*iteration}" >&2
    printf '%s\n' "$claimed"
  else
    printf '%s\n' "$current"
  fi
}

# Where the tools and the package cache go: tools_dir in site.md (may name $USER), else
# $ARH_ENV_CACHE/tools, else .arh/envs/tools. Node-local on a slow shared filesystem.
arh_tools_dir() {
  local d; d=$(arh_config_get "$1/config/site.md" tools_dir "")
  d=${d:-${ARH_ENV_CACHE:+$ARH_ENV_CACHE/tools}}; d=${d:-$1/envs/tools}
  eval echo "$d"
}

# arh_pixi STATE: the pixi binary pinned in config/dependencies.json, fetched once (ARH_PIXI overrides).
arh_pixi() {
  [ -z "${ARH_PIXI:-}" ] || { printf '%s\n' "$ARH_PIXI"; return 0; }
  local url sha bin tmp
  read -r url sha < <(python3 -c 'import json, platform, sys
p = json.load(open(sys.argv[1]))["tools"]["pixi"]; a = platform.machine().replace("arm64", "aarch64")
print(p["url"].format(version=p["version"], arch=a), p["sha256"].get(a, "none"))' "$ARH_HOME/config/dependencies.json")
  bin="$(arh_tools_dir "$1")/pixi-${sha:0:12}/pixi"
  if [ ! -x "$bin" ]; then
    mkdir -p "${bin%/*}"; tmp=$(mktemp "${bin%/*}/download.XXXXXX")
    if ! curl -fsSL --retry 3 -o "$tmp" "$url" || [ "$(arh_sha256 "$tmp")" != "$sha" ] \
       || ! tar -xzf "$tmp" -C "${bin%/*}" pixi; then
      rm -f "$tmp"; arh_warn "could not fetch the pinned pixi ($url); offline, set ARH_PIXI=/path/to/pixi"; return 1
    fi
    rm -f "$tmp"
  fi
  printf '%s\n' "$bin"
}

# arh_pixi_env STATE DIR [SPEC...]: a locked environment in DIR (pixi.toml and pixi.lock are the record,
# .pixi/ holds the files). With SPECs (conda specs; pypi:NAME==V for PyPI) it is solved and locked;
# without, rebuilt exactly from DIR/pixi.lock. pixi locks and resumes its own installs. Prints the
# prefix. Channels: ARH_CHANNELS (default conda-forge bioconda). A GPU solve on a node without a GPU
# needs CONDA_OVERRIDE_CUDA=12, which pixi reads from the environment.
arh_pixi_env() {
  local state="$1" dir="$2" pixi c spec conda=() pypi=(); shift 2
  pixi=$(arh_pixi "$state") || return 1
  export PIXI_CACHE_DIR="${PIXI_CACHE_DIR:-$(arh_tools_dir "$state")/pixi-cache}"
  mkdir -p "$dir"
  if [ $# -gt 0 ]; then
    { printf '[workspace]\nname = "%s"\nchannels = [' "$(basename "$dir")"
      for c in ${ARH_CHANNELS:-conda-forge bioconda}; do printf '"%s", ' "$c"; done
      printf ']\nplatforms = ["linux-%s"]\n\n[dependencies]\n' "$(uname -m | sed 's/x86_64/64/; s/arm64/aarch64/')"
    } > "$dir/pixi.toml"
    rm -f "$dir/pixi.lock"
    for spec in "$@"; do case "$spec" in pypi:*) pypi+=("${spec#pypi:}") ;; *) conda+=("$spec") ;; esac; done
    [ ${#conda[@]} -eq 0 ] || "$pixi" add -q --manifest-path "$dir/pixi.toml" "${conda[@]}" >&2 || return 1
    [ ${#pypi[@]} -eq 0 ] || "$pixi" add -q --manifest-path "$dir/pixi.toml" --pypi "${pypi[@]}" >&2 || return 1
  else
    [ -f "$dir/pixi.lock" ] || { arh_warn "no lock to rebuild from: $dir/pixi.lock"; return 1; }
    "$pixi" install -q --frozen --manifest-path "$dir/pixi.toml" >&2 || return 1
  fi
  printf '%s\n' "$dir/.pixi/envs/default"
}

# SOURCE:TARGET binds that cover every existing sealed input with an empty mount. `arh run` has no
# iteration and so no freeze: it never reads a sealed input, even one inside a broader immutable input.
arh_sealed_masks() {
  arh_has_sealed || return 0
  python3 "$ARH_HOME/lib/freeze.py" masks "$ARH_ROOT"
}

# Any sealed group declared: sealed_inputs, sealed_inputs_<group>, or either with _file.
arh_has_sealed() {
  [ -f "$ARH_PROJ" ] && arh_config_keys "$ARH_PROJ" | while read -r k; do
    case "$k" in sealed_inputs|sealed_inputs_*) [ -n "$(arh_config_get "$ARH_PROJ" "$k" "")" ] && echo y ;; esac
  done | grep -q y
}

# arh_secret_scan NOTE FILE...: succeed unless the files, or the note text, carry something shaped like
# a credential; the findings go to stderr, redacted. Run on what arh ask and arh delegate
# are about to send to an outside model service. `secret_scan = off` in harnesses.md disables it.
arh_secret_scan() {
  local note="$1" tmp="" rc=0 hits; shift
  [ "$(arh_config_get "$ARH_HARN" secret_scan on)" != off ] || return 0
  if [ -n "$note" ]; then tmp=$(mktemp); printf '%s\n' "$note" > "$tmp"; set -- "$@" "$tmp"; fi
  hits=$(python3 "$ARH_HOME/lib/secret_scan.py" scan "$@") || rc=$?
  [ "$rc" != 2 ] || { [ -z "$tmp" ] || rm -f "$tmp"; arh_die "the secret scanner could not run (above); nothing was sent"; }
  [ "$rc" = 0 ] || printf '%s\n' "${hits//"$tmp"/--note}" >&2
  [ -z "$tmp" ] || rm -f "$tmp"
  return "$rc"
}

# arh_owner_dir N|OBJECT: the iteration directory for a number, or the verification directory for a
# verification object's name. note, lease and wait worked on iterations only, so a verification could
# record no out-of-band work, no takeover and no wait (field feedback #56, #59, #67).
arh_owner_dir() {
  case "$1" in
    "") return 1 ;;
    *[!0-9]*) [ -f "$ARH_VERIFY/$1/PREDECLARATION.md" ] && case "$1" in */*|..*) return 1 ;; *) printf '%s' "$ARH_VERIFY/$1" ;; esac ;;
    *) printf '%s' "$ARH_ITERS/iteration$1" ;;
  esac
}

# arh_lease_touch DIR COMMAND: record that COMMAND acted on the iteration in DIR, warning when another
# session holds it. Never fails the command that calls it.
arh_lease_touch() {
  [ -f "$1/CLAIM.json" ] || [ -f "$1/PREDECLARATION.md" ] || return 0
  local rc=0
  python3 "$ARH_HOME/lib/lease.py" touch "$1" "$2" "$(arh_agent_name)" "${USER:-unknown}" "$(uname -n)" \
    "${ARH_SESSION:-}" || rc=$?
  # 3: a dispatched controller holds the iteration (lease.py said so); any other failure only warns.
  [ "$rc" -ne 3 ] || exit 3
}

# git_record = on (the default): the project is a git repository holding the record, not the data
# (templates/gitignore), and each successful command that changes the record is committed. The
# history is a second, independent trail of who changed what and when, and it is what Entire CLI
# hangs agent sessions on (Entire-Checkpoint trailers; docs/integrations.md). Never fatal: a failed
# commit warns and leaves the change in the working tree for the next one.
# arh_git_record MESSAGE [N[,N...]]: commit the files outside the iteration and verification
# directories, those of each N named, and any iteration or verification not yet in the record (a claim).
arh_git_record() {
  local msg=$1 scope=${2-} max big sealed iters verif s
  local -a paths
  [ "$(arh_config_get "$ARH_HARN" git_record on)" = on ] || return 0
  [ -d "$ARH_ROOT/.git" ] || return 0
  command -v git >/dev/null 2>&1 || return 0
  max=$(arh_config_get "$ARH_HARN" git_max_file_bytes 2000000)
  mkdir -p "$ARH_STATE/tmp"
  (
    flock -w 300 9 || { arh_warn "git record: lock busy; left for the next commit"; exit 0; }
    cd "$ARH_ROOT" || exit 0
    # Sealed inputs inside the project never enter the history: a commit would be a readable copy.
    sealed=$(python3 "$ARH_HOME/lib/freeze.py" git-exclude "$ARH_ROOT") || { arh_warn "git record: sealed inputs unknown; skipped"; exit 0; }
    { sed '/^# arh sealed inputs >>>$/,/^# <<< arh sealed inputs$/d' .git/info/exclude 2>/dev/null
      printf '# arh sealed inputs >>>\n%s\n# <<< arh sealed inputs\n' "$sealed"; } > .git/info/exclude.new \
      && mv .git/info/exclude.new .git/info/exclude
    iters=$(arh_config_get "$ARH_PROJ" iterations_dir iterations)
    verif=$(arh_config_get "$ARH_PROJ" verification_dir verification)
    paths=()
    for s in ${scope//,/ }; do
      case "$s" in
        *[!0-9]*) [ -d "$verif/$s" ] && paths+=("$verif/$s") ;;
        *) [ -d "$iters/iteration$s" ] && paths+=("$iters/iteration$s") ;;
      esac
    done
    while IFS= read -r -d '' s; do
      case "$s" in "$iters"/*/*/|"$verif"/*/*/) ;; "$iters"/|"$verif"/|"$iters"/*/|"$verif"/*/) paths+=("$s") ;; esac
    done < <(git ls-files -z -o --directory --exclude-standard -- "$iters" "$verif" 2>/dev/null)
    # Data never enters the history, even when .gitignore misses it. Checked before `git add`, which
    # would otherwise compress every large file into .git/objects first (minutes on a shared filesystem).
    big=$(git ls-files -z -o -m --exclude-standard | xargs -0 -r stat -c '%s %n' 2>/dev/null \
          | awk -v m="$max" '$1 > m {sub(/^[0-9]+ /, ""); print}' || true)
    if [ -n "$big" ]; then
      printf '%s\n' "$big" | while IFS= read -r f; do git rm -q --cached --ignore-unmatch -- "$f"; printf '/%s\n' "$f" >> .git/info/exclude; done
      arh_warn "git record: left out files over $max bytes (added to .git/info/exclude): $(printf '%s ' $big)"
    fi
    # Everything outside the iterations, then only the iterations named or new: another session's
    # work in progress stays in the working tree for its own commit.
    git add -A . 2>/dev/null || { arh_warn "git record: git add failed"; exit 0; }
    git reset -q -- "$iters" "$verif" 2>/dev/null || true
    [ ${#paths[@]} -eq 0 ] || git add -A -- "${paths[@]}" 2>/dev/null || { arh_warn "git record: git add failed"; exit 0; }
    # A path sealed after it was committed leaves the index (its old commits stay: see docs/integrations.md).
    git ls-files -z -c -i --exclude-standard | xargs -0 -r git rm -q --cached -- 2>/dev/null || true
    git diff --cached --quiet && exit 0
    if git config user.email >/dev/null 2>&1; then git commit -q -m "$msg" >/dev/null 2>&1
    else git -c user.name="${USER:-arh}" -c user.email="${USER:-arh}@$(hostname)" commit -q -m "$msg" >/dev/null 2>&1; fi \
      || arh_warn "git record: commit failed; the change stays in the working tree"
  ) 9>"$ARH_STATE/tmp/git.lock" || arh_warn "git record: skipped ($msg)"
  return 0
}
