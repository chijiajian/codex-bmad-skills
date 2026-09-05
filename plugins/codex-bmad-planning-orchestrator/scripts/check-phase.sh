#!/usr/bin/env sh
# Shared read-only router. Preserve the --output and key/value CLI interface.
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 "$SCRIPT_DIR/planning_state.py" --phase "$@"
