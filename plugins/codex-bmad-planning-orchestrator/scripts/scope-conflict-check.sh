#!/usr/bin/env sh
# Read-only check of planned story scopes. See --help for the public CLI.
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 "$SCRIPT_DIR/check_scopes.py" "$@"
