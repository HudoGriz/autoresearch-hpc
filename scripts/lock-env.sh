#!/usr/bin/env bash
# Export an existing conda/micromamba environment as a lock that `micromamba create --file`
# accepts, and optionally recreate it — for adopting a project whose results were produced
# in a pre-existing environment and must be reproduced bit for bit.
#
#   scripts/lock-env.sh MICROMAMBA SRC_PREFIX OUT.lock                write the lock
#   scripts/lock-env.sh MICROMAMBA SRC_PREFIX OUT.lock DEST_PREFIX    ... and create DEST from it
#
# Why this exists: `micromamba list --explicit` prints a "List of packages in environment"
# header and no @EXPLICIT marker, so its output is not a valid --file input. micromamba then
# parses the URLs as specs and fails to solve. This writes @EXPLICIT plus the URL#md5 lines,
# warns about distributions a conda lock cannot pin, and verifies that a recreated environment
# lists exactly the locked packages.
set -euo pipefail
[ $# -ge 3 ] || { echo 'usage: scripts/lock-env.sh MICROMAMBA SRC_PREFIX OUT.lock [DEST_PREFIX]' >&2; exit 2; }
mm=$1; src=$2; lock=$3; dest=${4-}
[ -x "$mm" ] || { echo "micromamba not executable: $mm" >&2; exit 1; }
[ -d "$src/conda-meta" ] || { echo "not a conda environment: $src" >&2; exit 1; }

urls() { "$mm" list -p "$1" --explicit --md5 | grep -E '^https?://' | LC_ALL=C sort; }

tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT
urls "$src" > "$tmp"
[ -s "$tmp" ] || { echo "no package URLs exported from $src" >&2; exit 1; }
{ echo '@EXPLICIT'; cat "$tmp"; } > "$lock"
printf 'locked %s packages from %s -> %s (sha256 %s)\n' \
  "$(wc -l < "$tmp" | tr -d ' ')" "$src" "$lock" "$(sha256sum "$lock" | cut -d' ' -f1)"

# Distributions installed by pip are invisible to a conda lock. Name them; do not guess.
find "$src" -path '*site-packages/*.dist-info/INSTALLER' 2>/dev/null | while IFS= read -r f; do
  [ "$(cat "$f")" = conda ] || printf 'WARNING: not conda-installed, not in the lock: %s\n' \
    "$(basename "$(dirname "$f")")" >&2
done

[ -n "$dest" ] || exit 0
[ ! -e "$dest" ] || { echo "refusing to overwrite existing $dest" >&2; exit 1; }
"$mm" create -y -p "$dest" --file "$lock" >/dev/null
if ! urls "$dest" | cmp -s - "$tmp"; then
  echo "FATAL: $dest does not list exactly the locked packages" >&2; exit 1
fi
printf 'created %s from %s; package list verified identical\n' "$dest" "$lock"
