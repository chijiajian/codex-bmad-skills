#!/usr/bin/env sh
# BMAD Planning & Orchestrator — Check Current Phase
# ---------------------------------------------------
# Reads the planning workspace and prints the inferred current phase,
# the project track, and a next-step recommendation.
#
# SCOPE: planning and orchestration only. Produces no planning documents;
# this is a read-only diagnostic router.
# Tracks: quick-flow | bmad-method | enterprise  (never numbered levels).
# No story points, velocity, or burndown.
#
# Usage:
#   sh <installed-plugin-root>/scripts/check-phase.sh" [--output <folder>]
#
#   --output <folder>   Override the default output folder (default: bmad-output)
#
# Exit codes:
#   0  Always (outputs phase info regardless of initialization state)
#
# Printed lines (always on stdout):
#   PHASE=<phase>
#   TRACK=<track>
#   NEXT_SKILL=<bmad-planning-orchestrator:skill-name | none>
#   REASON=<human-readable reason for the recommendation>
#
# Phase values:
#   uninitialized         — no workspace found
#   analysis              — workspace exists; no planning artifacts yet
#   planning              — product-brief (or similar) done; PRD / tech-spec in progress
#   solutioning           — PRD done; architecture in progress
#   implementation-handoff — architecture done; stories being created / handed off
#   handoff-complete      — all stories are ready-for-dev (external dev tool takes over)
#
# Note: resolve this script from the installed plugin root or use its absolute path.

set -eu

OUTPUT_FOLDER="bmad-output"

while [ $# -gt 0 ]; do
  case "$1" in
    --output) OUTPUT_FOLDER="$2"; shift 2 ;;
    -h|--help)
      grep '^#' "$0" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *) printf 'Unknown option: %s\n' "$1" >&2; exit 1 ;;
  esac
done

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

# exists_any <glob-pattern>  — 0 if any matching file exists, 1 otherwise
exists_any() {
  for f in $1; do
    [ -e "$f" ] && return 0
  done
  return 1
}

# --------------------------------------------------------------------------- #
# Detect artifacts
# --------------------------------------------------------------------------- #

if [ ! -d "$OUTPUT_FOLDER" ]; then
  printf 'PHASE=uninitialized\n'
  printf 'TRACK=unknown\n'
  printf 'NEXT_SKILL=bmad-planning-orchestrator:bmad-init\n'
  printf 'REASON=Output folder %s not found. Initialize the planning workspace first.\n' "$OUTPUT_FOLDER"
  exit 0
fi

# Threaded artifacts
HAS_CTX=0; [ -f "${OUTPUT_FOLDER}/project-context.md" ]   && HAS_CTX=1
HAS_LOG=0; [ -f "${OUTPUT_FOLDER}/decision-log.md" ]       && HAS_LOG=1

# Phase artifacts (flexible naming — allow date suffixes etc.)
HAS_BRIEF=0; exists_any "${OUTPUT_FOLDER}/product-brief*.md"  && HAS_BRIEF=1
HAS_PRD=0;   exists_any "${OUTPUT_FOLDER}/prd*.md"            && HAS_PRD=1
HAS_SPEC=0;  exists_any "${OUTPUT_FOLDER}/tech-spec*.md"      && HAS_SPEC=1
HAS_EPICS=0; exists_any "${OUTPUT_FOLDER}/epics*.md"          && HAS_EPICS=1
HAS_ARCH=0;  exists_any "${OUTPUT_FOLDER}/architecture*.md"   && HAS_ARCH=1

# Stories: count total vs. ready-for-dev
STORY_COUNT=0; READY_COUNT=0
if exists_any "${OUTPUT_FOLDER}/stories/*.story.md"; then
  for sf in "${OUTPUT_FOLDER}/stories/"*.story.md; do
    [ -e "$sf" ] || continue
    STORY_COUNT=$((STORY_COUNT + 1))
    if grep -qiE 'ready-for-dev' "$sf" 2>/dev/null; then
      READY_COUNT=$((READY_COUNT + 1))
    fi
  done
fi

# Track detection from config.yaml (most reliable), then decision-log fallback
TRACK="unknown"
CONFIG_FILE="${OUTPUT_FOLDER}/config.yaml"
if [ -f "$CONFIG_FILE" ]; then
  RAW=$(grep -iE '^[[:space:]]*track:' "$CONFIG_FILE" 2>/dev/null | head -1 || true)
  case "$(printf '%s' "$RAW" | tr '[:upper:]' '[:lower:]')" in
    *enterprise*)                        TRACK="enterprise" ;;
    *bmad-method*|*bmad_method*)         TRACK="bmad-method" ;;
    *quick-flow*|*quick_flow*)           TRACK="quick-flow" ;;
  esac
fi
if [ "$TRACK" = "unknown" ] && [ "$HAS_LOG" -eq 1 ]; then
  RAW=$(grep -iE 'track[:= ].*(quick[- ]?flow|bmad[- ]?method|enterprise)' \
        "${OUTPUT_FOLDER}/decision-log.md" 2>/dev/null | tail -1 || true)
  case "$(printf '%s' "$RAW" | tr '[:upper:]' '[:lower:]')" in
    *enterprise*)                        TRACK="enterprise" ;;
    *bmad?method*|*bmad-method*)         TRACK="bmad-method" ;;
    *quick*)                             TRACK="quick-flow" ;;
  esac
fi

# --------------------------------------------------------------------------- #
# Phase inference
# --------------------------------------------------------------------------- #
PHASE="uninitialized"
NEXT_SKILL="bmad-planning-orchestrator:bmad-init"
REASON="No planning workspace found. Run bmad-init to create one."

if [ "$HAS_CTX" -eq 1 ]; then
  PHASE="analysis"
  NEXT_SKILL="bmad-planning-orchestrator:bmad-product-brief"
  REASON="Workspace initialized. Create a product brief to begin analysis."

  # Quick-flow: skip brief/PRD → need tech-spec first
  if [ "$TRACK" = "quick-flow" ]; then
    NEXT_SKILL="bmad-planning-orchestrator:bmad-tech-spec"
    REASON="Quick Flow track: write a tech-spec (no PRD required)."
    if [ "$HAS_SPEC" -eq 1 ]; then
      PHASE="planning"
      NEXT_SKILL="bmad-planning-orchestrator:bmad-epics-and-stories"
      REASON="Tech-spec complete. Break work into epics and stories."
    fi
  else
    # bmad-method / enterprise: brief → PRD → arch (→ security/devops for enterprise)
    if [ "$HAS_BRIEF" -eq 1 ]; then
      PHASE="planning"
      NEXT_SKILL="bmad-planning-orchestrator:bmad-prd"
      REASON="Product brief complete. Create the PRD."

      if [ "$HAS_PRD" -eq 1 ]; then
        NEXT_SKILL="bmad-planning-orchestrator:bmad-architecture"
        REASON="PRD complete. Design the system architecture."

        if [ "$HAS_ARCH" -eq 1 ] || [ "$HAS_EPICS" -eq 1 ]; then
          PHASE="solutioning"
          NEXT_SKILL="bmad-planning-orchestrator:bmad-epics-and-stories"
          REASON="Architecture done. Decompose into epics and stories."

          if [ "$STORY_COUNT" -gt 0 ]; then
            PHASE="implementation-handoff"
            NEXT_SKILL="bmad-planning-orchestrator:bmad-sprint-planning"
            REASON="Stories exist. Run sprint-planning to sequence waves and hand off."

            if [ "$READY_COUNT" -eq "$STORY_COUNT" ] && [ "$STORY_COUNT" -gt 0 ]; then
              PHASE="handoff-complete"
              NEXT_SKILL="none"
              REASON="All stories are ready-for-dev. Hand off to the external dev tool."
            fi
          fi
        fi
      fi
    fi
  fi
fi

# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #
printf 'PHASE=%s\n'      "$PHASE"
printf 'TRACK=%s\n'      "$TRACK"
printf 'NEXT_SKILL=%s\n' "$NEXT_SKILL"
printf 'REASON=%s\n'     "$REASON"
