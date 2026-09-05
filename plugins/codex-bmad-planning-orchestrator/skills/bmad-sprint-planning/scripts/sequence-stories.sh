#!/usr/bin/env sh
# Assign waves portably on macOS and Linux. Requires Python 3.9+ and PyYAML.
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 "$SCRIPT_DIR/../../../scripts/sequence_sprint.py" "$@"
