#!/usr/bin/env bash
set -euo pipefail

here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT

python3 "$here/analysis.py" "$here/data.tsv" > "$tmp"
python3 - "$here/expected.json" "$tmp" <<'PY'
import json, sys
expected = json.load(open(sys.argv[1]))
observed = json.load(open(sys.argv[2]))
if observed != expected:
    print("publication example mismatch", file=sys.stderr)
    print("expected:", json.dumps(expected, sort_keys=True), file=sys.stderr)
    print("observed:", json.dumps(observed, sort_keys=True), file=sys.stderr)
    raise SystemExit(1)
print("publication example: OK")
PY
