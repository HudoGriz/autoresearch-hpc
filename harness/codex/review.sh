#!/usr/bin/env bash
# Reviewer command for `arh ask` that also records what the review cost.
#
#   harness_codex_cmd = <framework>/harness/codex/review.sh {prompt} {usage} [codex exec options, e.g. -m M]
#
# Prints the final message as `codex exec` would, writes the summed token counts to the {usage}
# path, and sends provider errors to stderr, where `arh ask` classifies them.
set -uo pipefail
prompt=$1; shift
usage=""; if [ $# -gt 0 ] && [ "${1#-}" = "$1" ]; then usage=$1; shift; fi
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
# `codex exec` reads stdin whenever it is not a terminal, and waits forever unless stdin is closed.
codex exec --skip-git-repo-check --json -o "$d/last.md" "$@" "$prompt" < /dev/null > "$d/events.jsonl" 2> "$d/stderr"
rc=$?
cat "$d/last.md" 2>/dev/null
python3 - "$d/events.jsonl" "$d/stderr" "$rc" "$usage" <<'PY'
import json, sys
from pathlib import Path
usage, errors, thread = {}, [], None
for line in Path(sys.argv[1]).read_text(errors='replace').splitlines():
    try:
        e = json.loads(line)
    except ValueError:
        continue
    if e.get('type') == 'thread.started':
        thread = e.get('thread_id')
    elif e.get('type') == 'turn.completed' and isinstance(e.get('usage'), dict):
        for k, v in e['usage'].items():
            if isinstance(v, (int, float)):
                usage[k] = usage.get(k, 0) + v
    elif e.get('type') in ('error', 'turn.failed'):
        errors.append(e.get('message') or (e.get('error') or {}).get('message') or '')
for message in dict.fromkeys(m for m in errors if m):
    print(message, file=sys.stderr)
if not errors and sys.argv[3] != '0':      # failures outside the event stream: options, authentication
    sys.stderr.write(Path(sys.argv[2]).read_text(errors='replace')[-4000:])
if sys.argv[4]:
    Path(sys.argv[4]).write_text(json.dumps({'usage': usage or None, 'thread_id': thread}) + '\n')
PY
exit "$rc"
