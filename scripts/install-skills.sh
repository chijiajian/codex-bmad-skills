#!/usr/bin/env sh
set -eu

REPO_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
PLUGIN_ROOT="$REPO_ROOT/plugins/codex-bmad-planning-orchestrator"
CODEX_HOME_DIR="${CODEX_HOME:-$HOME/.codex}"
SKILLS_DEST="$CODEX_HOME_DIR/skills"
SHARED_DEST="$SKILLS_DEST/_bmad-shared"

if [ ! -d "$PLUGIN_ROOT/skills" ]; then
  echo "ERROR: skills directory not found: $PLUGIN_ROOT/skills" >&2
  exit 1
fi

mkdir -p "$SKILLS_DEST" "$SHARED_DEST"
rm -rf "$SHARED_DEST/scripts" "$SHARED_DEST/references"
cp -R "$PLUGIN_ROOT/scripts" "$SHARED_DEST/scripts"
cp -R "$PLUGIN_ROOT/references" "$SHARED_DEST/references"

for skill_dir in "$PLUGIN_ROOT"/skills/bmad-*; do
  [ -d "$skill_dir" ] || continue
  name=$(basename "$skill_dir")
  rm -rf "$SKILLS_DEST/$name"
  cp -R "$skill_dir" "$SKILLS_DEST/$name"
  find "$SKILLS_DEST/$name" -type f \( -name '*.md' -o -name '*.sh' -o -name '*.py' -o -name '*.yaml' -o -name '*.json' \) -exec perl -0pi -e 's#\.\./\.\./scripts/#../_bmad-shared/scripts/#g; s#\.\./\.\./references/#../_bmad-shared/references/#g' {} \;
done

chmod +x "$SHARED_DEST/scripts"/*.sh 2>/dev/null || true
find "$SKILLS_DEST" -path '*/scripts/*.sh' -exec chmod +x {} \; 2>/dev/null || true

echo "Installed BMAD skills to: $SKILLS_DEST"
echo "Shared resources installed to: $SHARED_DEST"
echo "Restart Codex or reload skills if needed."
