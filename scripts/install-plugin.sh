#!/usr/bin/env sh
set -eu

REPO_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
MARKETPLACE_NAME="codex-bmad-skills"
PLUGIN_NAME="codex-bmad-planning-orchestrator"
REINSTALL=false

for arg in "$@"; do
  case "$arg" in
    --reinstall) REINSTALL=true ;;
    -h|--help)
      cat <<EOF
Usage: ./install.sh [--reinstall]

Registers this repository as a Codex marketplace and installs:
  $PLUGIN_NAME@$MARKETPLACE_NAME
EOF
      exit 0 ;;
    *) echo "Unknown option: $arg" >&2; exit 2 ;;
  esac
done

if ! command -v codex >/dev/null 2>&1; then
  echo "ERROR: codex CLI not found in PATH." >&2
  exit 1
fi

if [ ! -f "$REPO_ROOT/.agents/plugins/marketplace.json" ]; then
  echo "ERROR: marketplace file not found: $REPO_ROOT/.agents/plugins/marketplace.json" >&2
  exit 1
fi

if [ ! -f "$REPO_ROOT/plugins/$PLUGIN_NAME/.codex-plugin/plugin.json" ]; then
  echo "ERROR: plugin manifest not found: $REPO_ROOT/plugins/$PLUGIN_NAME/.codex-plugin/plugin.json" >&2
  exit 1
fi

if codex plugin marketplace list --json 2>/dev/null | grep -q '"name": "'"$MARKETPLACE_NAME"'"'; then
  echo "Marketplace already registered: $MARKETPLACE_NAME"
else
  echo "Registering Codex marketplace: $REPO_ROOT"
  codex plugin marketplace add "$REPO_ROOT"
fi

if [ "$REINSTALL" = true ]; then
  echo "Removing existing plugin before reinstall, if present: $PLUGIN_NAME"
  codex plugin remove "$PLUGIN_NAME" >/dev/null 2>&1 || true
fi

if codex plugin list --json 2>/dev/null | grep -q '"pluginId": "'"$PLUGIN_NAME@$MARKETPLACE_NAME"'"'; then
  echo "Plugin already installed: $PLUGIN_NAME@$MARKETPLACE_NAME"
  echo "Use ./install.sh --reinstall to refresh it."
else
  echo "Installing plugin: $PLUGIN_NAME@$MARKETPLACE_NAME"
  codex plugin add "$PLUGIN_NAME@$MARKETPLACE_NAME"
fi

echo ""
echo "Ready. Try: Use \$bmad-help to inspect my planning state."
