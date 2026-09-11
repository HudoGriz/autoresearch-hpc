#!/usr/bin/env bash
# Install harness-native wiring into an AutoResearch HPC project.
set -euo pipefail
here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
root=$(cd "$here/.." && pwd)
target="${1:?usage: harness/install.sh <project-dir> [claude codex opencode]}"; shift || true
[ -d "$target/.arh" ] || { echo "not an AutoResearch HPC project (.arh missing): $target" >&2; exit 1; }
target=$(cd "$target" && pwd)
harnesses=("$@"); [ ${#harnesses[@]} -eq 0 ] && harnesses=(claude codex opencode)

mkdir -p "$target/skills"
cp -r "$root/skills/." "$target/skills/"
if ! grep -q '^## Default coding skill — Ponytail' "$target/AGENTS.md"; then
  sed -n '/^## Default coding skill — Ponytail/,$p' "$root/AGENTS.md" >> "$target/AGENTS.md"
fi

for h in "${harnesses[@]}"; do
  case "$h" in
    claude)
      mkdir -p "$target/.claude/skills"
      cp -r "$root/skills/." "$target/.claude/skills/"
      ln -sf AGENTS.md "$target/CLAUDE.md"
      echo "claude   -> .claude/skills/, CLAUDE.md"
      ;;
    codex)
      mkdir -p "$target/.codex"
      cp "$here/codex/config.toml" "$target/.codex/config.toml"
      echo "codex    -> .codex/config.toml (reads AGENTS.md natively)"
      ;;
    opencode)
      cp "$here/opencode/opencode.json" "$target/opencode.json"
      echo "opencode -> opencode.json (reads AGENTS.md natively)"
      ;;
    *) echo "unknown harness: $h" >&2; exit 1 ;;
  esac
done
printf '\nPATH: export PATH="%s/bin:$PATH"\n' "$root"
printf 'Check: arh doctor\n'
