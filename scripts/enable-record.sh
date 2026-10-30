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
if [ ! -f .gitignore ]; then
  iters=$(arh_config_get "$ARH_PROJ" iterations_dir iterations)
  verif=$(arh_config_get "$ARH_PROJ" verification_dir verification)
  sed -e "s|/iterations/|/$iters/|g" -e "s|/verification/|/$verif/|g" "$ARH_HOME/templates/gitignore" > .gitignore
fi

entire=$(command -v entire || true)
if [ "$(arh_config_get "$ARH_HARN" entire on)" = on ] && [ -z "$entire" ]; then
  arh_warn 'entire = on, but Entire CLI is not installed yet: run scripts/setup-tools.sh, then this script again'
elif [ "$(arh_config_get "$ARH_HARN" entire on)" = on ]; then
  # Every configured harness that Entire knows (harness_<h>_entire_agent in harnesses.md).
  # ARH_ENTIRE_AGENTS names them instead, e.g. for a study whose harnesses.md predates the key and
  # must not change under open iterations (its hash binds their review terms).
  agents=${ARH_ENTIRE_AGENTS:-$(for h in $(arh_config_get "$ARH_HARN" harnesses ""); do arh_config_get "$ARH_HARN" "harness_${h}_entire_agent" ""; echo; done | sort -u | xargs)}
  first=1
  for a in $agents; do
    if [ "$first" = 1 ]; then
      "$entire" enable --agent "$a" --telemetry=false --skip-push-sessions --absolute-git-hook-path >/dev/null
      first=0
    else
      "$entire" agent add "$a" >/dev/null
    fi
  done
  # Agent hooks call `entire` by name, and an agent's PATH need not hold the pinned tools
  # environment: name the binary in full, or every hook silently does nothing.
  for f in .claude/settings.json .codex/hooks.json .opencode/plugins/entire.ts; do
    [ -f "$f" ] && sed -i -e "s|command -v entire |command -v $entire |g" -e "s|exec entire |exec $entire |g" "$f"
  done
fi
# basic-memory, the default memory search: its configuration and index stay in the project, and it
# must never rewrite a finding's front matter.
if [ "$(arh_config_get "$ARH_HARN" memory_search_cmd basic-memory)" = basic-memory ] && command -v bm >/dev/null 2>&1; then
  export BASIC_MEMORY_CONFIG_DIR="$ARH_STATE/basic-memory"
  mkdir -p "$BASIC_MEMORY_CONFIG_DIR" "$ARH_ROOT/knowledge"
  [ -f "$BASIC_MEMORY_CONFIG_DIR/config.json" ] \
    || printf '{"disable_permalinks": true, "ensure_frontmatter_on_sync": false}\n' > "$BASIC_MEMORY_CONFIG_DIR/config.json"
  bm project list 2>/dev/null | grep -q arh-knowledge || bm project add arh-knowledge "$ARH_ROOT/knowledge" >/dev/null
  timeout 600 bm reindex --project arh-knowledge >/dev/null 2>&1 || arh_warn 'basic-memory reindex failed'
fi
arh_git_record 'arh: record enabled (git, Entire)'
echo "record: $(git rev-parse --short HEAD 2>/dev/null || echo 'no commit yet') in $ARH_ROOT${agents:+; Entire records: $agents}"
