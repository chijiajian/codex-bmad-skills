#!/usr/bin/env sh
# BMAD Planning & Orchestrator — Load Project Config
# ---------------------------------------------------
# Reads <output-folder>/config.yaml and emits the project configuration.
# The output folder itself is also surfaced so callers know where artifacts live.
#
# SCOPE: planning and orchestration only. Never runs tests, builds, or lints.
# No numbered project levels — tracks are: quick-flow | bmad-method | enterprise.
# No story points, velocity, or burndown references.
#
# Usage:
#   sh <installed-plugin-root>/scripts/load-config.sh [--output <folder>] [--json] [--export]
#
#   --output <folder>   Override the default output folder (default: bmad-output)
#   --json              Emit a JSON object instead of human-readable text
#   --export            Emit shell export statements (eval-able in the caller)
#
# Exit codes:
#   0  Config found and loaded
#   1  Config not found (project not initialized)
#
# Machine-readable keys emitted on stdout (default mode — one key=value per line):
#   PROJECT_NAME=...
#   PROJECT_TRACK=...     (quick-flow | bmad-method | enterprise)
#   OUTPUT_FOLDER=...
#   STORIES_FOLDER=...
#   DECISION_LOG=...
#   PROJECT_CONTEXT=...
#   SPRINT_STATUS=...
#
# Note: resolve this script from the installed plugin root or use its absolute
# path from the skill instructions. Never hardcode machine-specific paths.

set -eu

OUTPUT_FOLDER="bmad-output"
EMIT_JSON=false
EMIT_EXPORT=false

while [ $# -gt 0 ]; do
  case "$1" in
    --output)   OUTPUT_FOLDER="$2"; shift 2 ;;
    --json)     EMIT_JSON=true;     shift ;;
    --export)   EMIT_EXPORT=true;   shift ;;
    -h|--help)
      grep '^#' "$0" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *) printf 'Unknown option: %s\n' "$1" >&2; exit 1 ;;
  esac
done

CONFIG_FILE="${OUTPUT_FOLDER}/config.yaml"

if [ ! -f "$CONFIG_FILE" ]; then
  printf 'ERROR: BMAD not initialized. No config found at: %s\n' "$CONFIG_FILE" >&2
  printf 'Run $bmad-init to set up the planning workspace.\n' >&2
  exit 1
fi

# --------------------------------------------------------------------------- #
# Portable YAML field extraction (no yq / python required)
# --------------------------------------------------------------------------- #

# extract_field <key> <file>  — first top-level or indented "<key>:" line
extract_field() {
  grep -E "^[[:space:]]*${1}:" "$2" 2>/dev/null | head -1 \
    | sed 's/[^:]*:[[:space:]]*//' | tr -d '"' | tr -d "'" | sed 's/[[:space:]]*$//'
}

# --------------------------------------------------------------------------- #
# Load values
# --------------------------------------------------------------------------- #
PROJECT_NAME=$(extract_field "name" "$CONFIG_FILE")
PROJECT_TRACK=$(extract_field "track" "$CONFIG_FILE")

# paths section: try explicit keys; fall back to derivations from OUTPUT_FOLDER
STORIES_FOLDER=$(extract_field "stories_folder" "$CONFIG_FILE")
DECISION_LOG=$(extract_field "decision_log"     "$CONFIG_FILE")
PROJECT_CONTEXT=$(extract_field "project_context" "$CONFIG_FILE")

# Fill defaults if not present in config
PROJECT_NAME="${PROJECT_NAME:-unknown}"
PROJECT_TRACK="${PROJECT_TRACK:-quick-flow}"
STORIES_FOLDER="${STORIES_FOLDER:-${OUTPUT_FOLDER}/stories}"
DECISION_LOG="${DECISION_LOG:-${OUTPUT_FOLDER}/decision-log.md}"
PROJECT_CONTEXT="${PROJECT_CONTEXT:-${OUTPUT_FOLDER}/project-context.md}"

# sprint-status.yaml is a planning artifact; its location follows output folder
SPRINT_STATUS="${OUTPUT_FOLDER}/sprint-status.yaml"

# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #
if [ "$EMIT_JSON" = true ]; then
  printf '{\n'
  printf '  "project_name": "%s",\n'    "$PROJECT_NAME"
  printf '  "project_track": "%s",\n'   "$PROJECT_TRACK"
  printf '  "output_folder": "%s",\n'   "$OUTPUT_FOLDER"
  printf '  "stories_folder": "%s",\n'  "$STORIES_FOLDER"
  printf '  "decision_log": "%s",\n'    "$DECISION_LOG"
  printf '  "project_context": "%s",\n' "$PROJECT_CONTEXT"
  printf '  "sprint_status": "%s"\n'    "$SPRINT_STATUS"
  printf '}\n'
elif [ "$EMIT_EXPORT" = true ]; then
  printf 'export BMAD_PROJECT_NAME="%s"\n'    "$PROJECT_NAME"
  printf 'export BMAD_PROJECT_TRACK="%s"\n'   "$PROJECT_TRACK"
  printf 'export BMAD_OUTPUT_FOLDER="%s"\n'   "$OUTPUT_FOLDER"
  printf 'export BMAD_STORIES_FOLDER="%s"\n'  "$STORIES_FOLDER"
  printf 'export BMAD_DECISION_LOG="%s"\n'    "$DECISION_LOG"
  printf 'export BMAD_PROJECT_CONTEXT="%s"\n' "$PROJECT_CONTEXT"
  printf 'export BMAD_SPRINT_STATUS="%s"\n'   "$SPRINT_STATUS"
else
  printf 'PROJECT_NAME=%s\n'    "$PROJECT_NAME"
  printf 'PROJECT_TRACK=%s\n'   "$PROJECT_TRACK"
  printf 'OUTPUT_FOLDER=%s\n'   "$OUTPUT_FOLDER"
  printf 'STORIES_FOLDER=%s\n'  "$STORIES_FOLDER"
  printf 'DECISION_LOG=%s\n'    "$DECISION_LOG"
  printf 'PROJECT_CONTEXT=%s\n' "$PROJECT_CONTEXT"
  printf 'SPRINT_STATUS=%s\n'   "$SPRINT_STATUS"
fi
