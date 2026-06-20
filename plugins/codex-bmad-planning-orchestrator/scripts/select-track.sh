#!/usr/bin/env sh
# BMAD Planning & Orchestrator — Track Selector
# ----------------------------------------------
# Prints the three scale-adaptive BMAD tracks with descriptions and a
# heuristic-suggested default. The user ALWAYS confirms; this script
# only makes a suggestion.
#
# Tracks (never numbered levels; no story points, velocity, or burndown):
#
#   quick-flow   — 1-15 stories; tech-spec only; single builder
#   bmad-method  — 10-50+ stories; PRD + Architecture (+ optional UX)
#   enterprise   — 30+ stories; PRD + Architecture + Security + DevOps planning
#
# Usage:
#   sh <installed-plugin-root>/scripts/select-track.sh" \
#       [--stories <N>] [--teams one|many] [--compliance yes|no]
#
#   --stories <N>       Approximate story count (optional heuristic signal)
#   --teams one|many    Team size signal
#   --compliance yes|no Regulatory / compliance / security-planning requirement
#
# Exit codes:
#   0  Always (informational; user decides)
#
# Machine-readable tail (always the last 2 lines):
#   SUGGESTED_TRACK=<quick-flow|bmad-method|enterprise>
#   SUGGESTION_REASON=<human-readable rationale>
#
# Note: resolve this script from the installed plugin root or use its absolute path.

set -eu

STORIES=""
TEAMS=""
COMPLIANCE=""

while [ $# -gt 0 ]; do
  case "$1" in
    --stories)    STORIES="$2";    shift 2 ;;
    --teams)      TEAMS="$2";      shift 2 ;;
    --compliance) COMPLIANCE="$2"; shift 2 ;;
    -h|--help)
      grep '^#' "$0" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *) printf 'Unknown option: %s\n' "$1" >&2; exit 1 ;;
  esac
done

# --------------------------------------------------------------------------- #
# Track descriptions
# --------------------------------------------------------------------------- #
printf '\n'
printf 'BMAD scale-adaptive TRACKS  (choose by planning need; story count is a soft signal)\n'
printf '\n'

printf 'quick-flow    1-15 stories\n'
printf '   Artifacts : tech-spec only\n'
printf '   Best for  : a focused feature or fix, one builder, low coordination overhead.\n'
printf '\n'

printf 'bmad-method   10-50+ stories\n'
printf '   Artifacts : PRD + Architecture (+ optional UX design)\n'
printf '   Best for  : a real product slice; multiple epics; decisions worth writing down.\n'
printf '\n'

printf 'enterprise    30+ stories\n'
printf '   Artifacts : PRD + Architecture + Security planning + DevOps planning\n'
printf '   Best for  : compliance/regulatory scope, multiple teams, infra concerns to\n'
printf '               plan up-front; governance artefacts required.\n'
printf '\n'

# --------------------------------------------------------------------------- #
# Heuristic suggestion
# --------------------------------------------------------------------------- #
SUGGESTION="quick-flow"
REASON="default for small, focused, single-builder work"

# is_num: true if arg is a non-empty string of digits
is_num() { printf '%s' "$1" | grep -qE '^[0-9]+$'; }

if [ "$COMPLIANCE" = "yes" ] || [ "$TEAMS" = "many" ]; then
  SUGGESTION="enterprise"
  REASON="compliance/regulatory requirement or multiple teams need security + DevOps planning"
elif is_num "$STORIES" && [ "$STORIES" -ge 30 ]; then
  SUGGESTION="enterprise"
  REASON="approx. ${STORIES} stories — enterprise-scale coordination"
elif is_num "$STORIES" && [ "$STORIES" -ge 10 ]; then
  SUGGESTION="bmad-method"
  REASON="approx. ${STORIES} stories — warrants a PRD + Architecture"
elif is_num "$STORIES" && [ "$STORIES" -ge 1 ]; then
  SUGGESTION="quick-flow"
  REASON="approx. ${STORIES} stories — a tech-spec is sufficient"
fi

printf 'Suggested default: %s\n' "$SUGGESTION"
printf '   Why: %s\n'            "$REASON"
printf '\n'
printf 'This is a suggestion only. Confirm with the user — they may override.\n'
printf 'When unsure between two tracks, prefer the lighter one (promote later if needed).\n'
printf '\n'

# Machine-readable summary (always the last two lines for easy parsing)
printf 'SUGGESTED_TRACK=%s\n'  "$SUGGESTION"
printf 'SUGGESTION_REASON=%s\n' "$REASON"
