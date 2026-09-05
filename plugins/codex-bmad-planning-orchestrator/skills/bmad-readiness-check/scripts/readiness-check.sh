#!/usr/bin/env sh
# Advisory planning pre-flight, including Quick Flow; no application execution.
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 "$SCRIPT_DIR/../../../scripts/readiness_preflight.py" "$@"
