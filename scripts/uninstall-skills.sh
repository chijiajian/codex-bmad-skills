#!/usr/bin/env sh
set -eu

CODEX_HOME_DIR="${CODEX_HOME:-$HOME/.codex}"
SKILLS_DEST="$CODEX_HOME_DIR/skills"

if [ "${1:-}" != "--yes" ]; then
  echo "This removes bmad-* skills and _bmad-shared from: $SKILLS_DEST"
  echo "Run again with --yes to confirm."
  exit 2
fi

for skill_dir in "$SKILLS_DEST"/bmad-*; do
  [ -d "$skill_dir" ] || continue
  rm -rf "$skill_dir"
done
rm -rf "$SKILLS_DEST/_bmad-shared"

echo "Removed BMAD skills from: $SKILLS_DEST"
