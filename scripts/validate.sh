#!/usr/bin/env sh
set -eu

REPO_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
PLUGIN_ROOT="$REPO_ROOT/plugins/codex-bmad-planning-orchestrator"
CODEX_HOME_DIR="${CODEX_HOME:-$HOME/.codex}"
PLUGIN_VALIDATOR="$CODEX_HOME_DIR/skills/.system/plugin-creator/scripts/validate_plugin.py"
SKILL_VALIDATOR="$CODEX_HOME_DIR/skills/.system/skill-creator/scripts/quick_validate.py"
BMAD_VALIDATOR="$PLUGIN_ROOT/skills/bmad-builder/scripts/validate-skill.sh"

python3 -m json.tool "$REPO_ROOT/.agents/plugins/marketplace.json" >/dev/null
python3 -m json.tool "$PLUGIN_ROOT/.codex-plugin/plugin.json" >/dev/null

echo "JSON manifests parse"

if command -v ruby >/dev/null 2>&1; then
  find "$PLUGIN_ROOT" \( -name '*.yaml' -o -name '*.yml' \) -exec ruby -e 'require "yaml"; ARGV.each { |f| YAML.load_file(f) }' {} +
  echo "YAML files parse"
else
  echo "Ruby not found; skipping YAML parse check"
fi

if [ -f "$PLUGIN_VALIDATOR" ]; then
  python3 "$PLUGIN_VALIDATOR" "$PLUGIN_ROOT"
else
  echo "Codex plugin validator not found at $PLUGIN_VALIDATOR; running built-in manifest checks"
  python3 - "$PLUGIN_ROOT" <<'PYVALIDATEPLUGIN'
import json
import re
import sys
from pathlib import Path
root = Path(sys.argv[1])
manifest = json.loads((root / '.codex-plugin' / 'plugin.json').read_text())
required = ['name', 'version', 'description', 'author', 'skills', 'interface']
missing = [key for key in required if key not in manifest]
if missing:
    raise SystemExit(f'missing plugin fields: {missing}')
if not re.fullmatch(r'[a-z0-9-]+', manifest['name']):
    raise SystemExit('plugin name must be lowercase hyphen-case')
if not (root / 'skills').is_dir():
    raise SystemExit('plugin skills directory missing')
interface = manifest.get('interface') or {}
for key in ['displayName', 'shortDescription', 'longDescription', 'developerName', 'category', 'defaultPrompt']:
    if key not in interface:
        raise SystemExit(f'missing interface.{key}')
print('Built-in plugin manifest checks passed')
PYVALIDATEPLUGIN
fi

if [ -f "$SKILL_VALIDATOR" ]; then
  for d in "$PLUGIN_ROOT"/skills/*; do
    [ -d "$d" ] || continue
    python3 "$SKILL_VALIDATOR" "$d" >/dev/null
  done
  echo "All Codex skills passed quick_validate"
else
  echo "Codex skill validator not found at $SKILL_VALIDATOR; running built-in skill checks"
  python3 - "$PLUGIN_ROOT" <<'PYVALIDATESKILLS'
import re
import sys
from pathlib import Path
root = Path(sys.argv[1])
errors = []
for skill in sorted((root / 'skills').iterdir()):
    if not skill.is_dir() or skill.name.startswith('.'):
        continue
    skill_md = skill / 'SKILL.md'
    if not skill_md.is_file():
        errors.append(f'{skill.name}: missing SKILL.md')
        continue
    text = skill_md.read_text()
    match = re.match(r'^---\n(.*?)\n---', text, re.S)
    if not match:
        errors.append(f'{skill.name}: invalid frontmatter')
        continue
    fm = match.group(1)
    name_match = re.search(r'^name:\s*([a-z0-9-]+)\s*$', fm, re.M)
    if not name_match:
        errors.append(f'{skill.name}: missing or invalid name')
    elif name_match.group(1) != skill.name:
        errors.append(f'{skill.name}: frontmatter name mismatch')
    if not re.search(r'^description:\s*(\||>|[^\n]+)', fm, re.M):
        errors.append(f'{skill.name}: missing description')
    agent_yaml = skill / 'agents' / 'openai.yaml'
    if not agent_yaml.is_file():
        errors.append(f'{skill.name}: missing agents/openai.yaml')
if errors:
    raise SystemExit('\n'.join(errors))
print('Built-in skill checks passed')
PYVALIDATESKILLS
fi

for f in "$PLUGIN_ROOT"/skills/*/SKILL.md; do
  bash "$BMAD_VALIDATOR" "$f" >/tmp/codex-bmad-skill-validate.log || {
    cat /tmp/codex-bmad-skill-validate.log
    exit 1
  }
done

echo "All BMAD skill scope validations passed"
echo "Validation complete."
