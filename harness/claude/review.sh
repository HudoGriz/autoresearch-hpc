#!/usr/bin/env bash
# Reviewer command for `arh ask` that also records what the review cost.
#
#   harness_claude_cmd = <framework>/harness/claude/review.sh {prompt} {usage} [claude options, e.g. --model M]
#
# Prints the review as `claude -p` would, writes token usage and reported cost to the {usage} path,
# and sends a provider error to stderr, where `arh ask` classifies it.
set -uo pipefail
prompt=$1; shift
usage=""; if [ $# -gt 0 ] && [ "${1#-}" = "$1" ]; then usage=$1; shift; fi
out=$(mktemp); trap 'rm -f "$out"' EXIT
# Headless: no completion notice ever arrives, so work started in the background would be lost.
export CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1
printf '%s' "$prompt" | claude -p --output-format json "$@" > "$out"
rc=$?
python3 - "$out" "$usage" <<'PY'
import json, sys
from pathlib import Path
raw = Path(sys.argv[1]).read_text(errors='replace')
try:
    d = json.loads(raw)
except ValueError:
    sys.stdout.write(raw)
    sys.exit()
(sys.stderr if d.get('is_error') else sys.stdout).write((d.get('result') or '') + '\n')
if sys.argv[2]:
    keys = ('usage', 'modelUsage', 'total_cost_usd', 'duration_ms', 'num_turns', 'session_id')
    Path(sys.argv[2]).write_text(json.dumps({k: d[k] for k in keys if k in d}) + '\n')
PY
exit "$rc"
