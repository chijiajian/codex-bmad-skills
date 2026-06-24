#!/usr/bin/env sh
set -eu

PLUGIN_NAME="codex-bmad-planning-orchestrator"
MARKETPLACE_NAME="codex-bmad-skills"

if ! command -v codex >/dev/null 2>&1; then
  echo "ERROR: codex CLI not found in PATH." >&2
  exit 1
fi

echo "Removing plugin: $PLUGIN_NAME"
codex plugin remove "$PLUGIN_NAME" || true

echo "Removing marketplace: $MARKETPLACE_NAME"
codex plugin marketplace remove "$MARKETPLACE_NAME" || true

echo "Uninstall complete."
