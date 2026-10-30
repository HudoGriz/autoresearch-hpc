#!/usr/bin/env bash
# Make a project a git repository of its record and let Entire CLI record the agent sessions.
#
# Run by `arh init` and, for an existing study, by hand: scripts/enable-record.sh PROJECT.
# Idempotent. git_record = off or entire = off in harnesses.md skips the matching part.
set -euo pipefail
[ $# -eq 1 ] || { echo 'usage: scripts/enable-record.sh PROJECT' >&2; exit 2; }
ARH_HOME=${ARH_HOME:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}; export ARH_HOME
export ARH_PROJECT
ARH_PROJECT=$(cd "$1" && pwd)
# shellcheck source=lib/common.sh
. "$ARH_HOME/lib/common.sh"
arh_load_project
tools=$(arh_config_get "$ARH_SITE" tools_prefix "")
[ -z "$tools" ] || PATH="$PATH:$tools/bin"

[ "$(arh_config_get "$ARH_HARN" git_record on)" = on ] || { echo 'git_record = off: nothing to do'; exit 0; }
command -v git >/dev/null 2>&1 || arh_die 'git_record = on needs git on PATH'
cd "$ARH_ROOT"
[ -d .git ] || git init -q
# A study shared with a group (another account, an agent persona) commits from every member's arh.
git config core.sharedRepository group
if [ ! -f .gitignore ]; then
  iters=$(arh_config_get "$ARH_PROJ" iterations_dir iterations)
  verif=$(arh_config_get "$ARH_PROJ" verification_dir verification)
  sed -e "s|/iterations/|/$iters/|g" -e "s|/verification/|/$verif/|g" "$ARH_HOME/templates/gitignore" > .gitignore
fi

entire=$(command -v entire || true)
if [ "$(arh_config_get "$ARH_HARN" entire on)" = on ] && [ -z "$entire" ]; then
  arh_warn 'entire = on, but Entire CLI is not installed yet: run scripts/setup-tools.sh, then this script again'
elif [ "$(arh_config_get "$ARH_HARN" entire on)" = on ]; then
  # The Entire agent of each configured harness: harness_<h>_entire_agent, else the one for the
  # program its command runs (claude_ana runs claude). ARH_ENTIRE_AGENTS names them instead.
  entire_agent() {
    local a prog
    a=$(arh_config_get "$ARH_HARN" "harness_${1}_entire_agent" "")
    [ -n "$a" ] && { echo "$a"; return; }
    prog=$(arh_config_get "$ARH_HARN" "harness_${1}_cmd" "$1" | tr ' ' '\n' | grep -v -e '^env$' -e = | head -1)
    case "${prog##*/}" in claude) echo claude-code ;; codex) echo codex ;; opencode) echo opencode ;; esac
  }
  agents=${ARH_ENTIRE_AGENTS:-$(for h in $(arh_config_get "$ARH_HARN" harnesses ""); do entire_agent "$h"; done | sort -u | xargs)}
  # Entire is a convenience: when it cannot enable (no git identity, no login on a CI runner), the
  # record goes on without it.
  first=1
  for a in $agents; do
    if [ "$first" = 1 ]; then
      "$entire" enable --agent "$a" --telemetry=false --skip-push-sessions --absolute-git-hook-path >/dev/null 2>&1 \
        || { arh_warn "Entire could not be enabled (it needs a git identity: git config user.email); the record goes on without session records"; agents=""; break; }
      first=0
    else
      "$entire" agent add "$a" >/dev/null 2>&1 || arh_warn "Entire could not add agent $a"
    fi
  done
  # Agent hooks call `entire` by name, and an agent's PATH need not hold the pinned tools
  # environment: name the binary in full, or every hook silently does nothing.
  for f in .claude/settings.json .codex/hooks.json .opencode/plugins/entire.ts; do
    [ -f "$f" ] && sed -i -e "s|command -v entire |command -v $entire |g" -e "s|exec entire |exec $entire |g" "$f"
  done
  # Entire may have just created a harness's project configuration: give it arh's access entries
  # (sealed-input denials, declared inputs, web tools), as harness/install.sh would, and let the
  # project's group read it. Entire writes it owner-only, so another member's sessions would run
  # without the sealed-input denials and their hooks would fail.
  reach=$(arh_config_get "$ARH_PROJ" immutable_inputs "")
  gotchas=$(arh_config_get "$ARH_SITE" site_gotchas "")
  [ -z "$gotchas" ] || reach="$reach $(dirname "$gotchas")"
  web=$(arh_config_get "$ARH_HARN" web_access allow)
  # shellcheck disable=SC2086
  [ ! -d .claude ] || python3 "$ARH_HOME/lib/harness_access.py" write "$ARH_ROOT" claude "$web" $reach
  # shellcheck disable=SC2086
  [ ! -f opencode.json ] || python3 "$ARH_HOME/lib/harness_access.py" write "$ARH_ROOT" opencode "$web" $reach
  chmod -R g+rX .claude .codex .opencode .entire 2>/dev/null || true
fi
# basic-memory, the default memory search: its configuration and index stay in the project, and it
# must never rewrite a finding's front matter.
if [ "$(arh_config_get "$ARH_HARN" memory_search_cmd basic-memory)" = basic-memory ] && command -v bm >/dev/null 2>&1; then
  export BASIC_MEMORY_CONFIG_DIR="$ARH_STATE/basic-memory"
  mkdir -p "$BASIC_MEMORY_CONFIG_DIR" "$ARH_ROOT/knowledge"
  [ -f "$BASIC_MEMORY_CONFIG_DIR/config.json" ] \
    || printf '{"disable_permalinks": true, "ensure_frontmatter_on_sync": false}\n' > "$BASIC_MEMORY_CONFIG_DIR/config.json"
  # The embedding model (~70 MB) sits beside the tools, shared and on their disk, not in each project.
  [ -z "$tools" ] || python3 - "$BASIC_MEMORY_CONFIG_DIR/config.json" "$(dirname "$tools")/fastembed" <<'PY'
import json, sys
c = json.load(open(sys.argv[1])); c['semantic_embedding_cache_dir'] = sys.argv[2]
json.dump(c, open(sys.argv[1], 'w'), indent=2)
PY
  bm project list 2>/dev/null | grep -q arh-knowledge || bm project add arh-knowledge "$ARH_ROOT/knowledge" >/dev/null
  timeout 600 bm reindex --project arh-knowledge >/dev/null 2>&1 || arh_warn 'basic-memory reindex failed'
fi
arh_git_record 'arh: record enabled (git, Entire)'
echo "record: $(git rev-parse --short HEAD 2>/dev/null || echo 'no commit yet') in $ARH_ROOT${agents:+; Entire records: $agents}"
