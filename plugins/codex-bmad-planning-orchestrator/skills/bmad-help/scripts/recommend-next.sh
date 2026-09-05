#!/usr/bin/env sh
# Read-only BMAD planning state; shared contract supports plugin/skills installs.
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 "$SCRIPT_DIR/../../../scripts/planning_state.py" --recommend "$@"
