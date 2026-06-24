#!/bin/bash
# BMAD Planning State Detector
# Scans the output folder for planning artifacts, lists which exist, and prints the
# inferred phase + track. ROUTER ONLY — produces no planning documents.
#
# Usage: detect-state.sh [output-folder]   (default: bmad-output)

set -u

OUT="${1:-bmad-output}"
COMPAT_DIR="bmad"
COMPAT_PROJECT="${COMPAT_DIR}/project.yaml"
COMPAT_WORKFLOW="${COMPAT_DIR}/workflow-status.yaml"
COMPAT_SPRINT="${COMPAT_DIR}/sprint-status.yaml"

# Colors (degrade gracefully if not a TTY)
if [ -t 1 ]; then
  RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
  BLUE='\033[0;34m'; GRAY='\033[0;37m'; NC='\033[0m'
else
  RED=''; GREEN=''; YELLOW=''; BLUE=''; GRAY=''; NC=''
fi

mark() { # $1 = path-or-glob, $2 = label
  local found=""
  for f in $1; do
    if [ -e "$f" ]; then found="$f"; break; fi
  done
  if [ -n "$found" ]; then
    printf "  ${GREEN}[x]${NC} %-22s ${GRAY}%s${NC}\n" "$2" "$found"
    return 0
  else
    printf "  ${GRAY}[ ]${NC} %-22s ${GRAY}(missing)${NC}\n" "$2"
    return 1
  fi
}

exists_any() { # returns 0 if any glob matches
  for f in $1; do [ -e "$f" ] && return 0; done
  return 1
}

normalize_track() {
  local raw
  raw="$(echo "${1:-}" | tr '[:upper:]' '[:lower:]' | tr '_' '-')"
  case "$raw" in
    *enterprise*) echo "enterprise" ;;
    *bmad-method*|*bmad\ method*) echo "bmad-method" ;;
    *quick-flow*|*quick\ flow*|*quick*) echo "quick-flow" ;;
    *) echo "unknown" ;;
  esac
}

read_track_from_yaml() {
  local file="$1"
  [ -f "$file" ] || { echo "unknown"; return; }
  local raw
  raw="$(grep -E '^[[:space:]]*track:' "$file" 2>/dev/null | head -1 | sed 's/.*: *//' | tr -d '"' | tr -d "'")"
  normalize_track "$raw"
}

HAS_COMPAT_PROJECT=1
HAS_COMPAT_WORKFLOW=1
HAS_COMPAT_SPRINT=1
[ -f "$COMPAT_PROJECT" ] && HAS_COMPAT_PROJECT=0
[ -f "$COMPAT_WORKFLOW" ] && HAS_COMPAT_WORKFLOW=0
[ -f "$COMPAT_SPRINT" ] && HAS_COMPAT_SPRINT=0
COMPAT_TRACK="unknown"
if [ "$HAS_COMPAT_WORKFLOW" -eq 0 ]; then
  COMPAT_TRACK="$(read_track_from_yaml "$COMPAT_WORKFLOW")"
elif [ "$HAS_COMPAT_PROJECT" -eq 0 ]; then
  COMPAT_TRACK="$(read_track_from_yaml "$COMPAT_PROJECT")"
fi

HAS_MIGRATION_SOURCE=0
MIGRATION_HINTS=""
for p in \
  ".claude" \
  ".bmad-core" \
  "docs/prd.md" \
  "docs/architecture.md" \
  "docs/epics.md" \
  "docs/stories" \
  "bmad-output"
do
  if [ -e "$p" ] && [ "$p" != "$OUT" ]; then
    HAS_MIGRATION_SOURCE=1
    MIGRATION_HINTS="${MIGRATION_HINTS}${MIGRATION_HINTS:+, }${p}"
  fi
done

echo ""
echo -e "${BLUE}== BMAD Planning State ==${NC}"
echo -e "${BLUE}Output folder:${NC} ${OUT}"
echo ""

if [ ! -d "$OUT" ]; then
  echo -e "${YELLOW}Output folder '${OUT}' does not exist — project not initialized.${NC}"
  if [ "$HAS_MIGRATION_SOURCE" -eq 1 ]; then
    echo -e "${YELLOW}Possible Claude BMAD migration source detected: ${MIGRATION_HINTS}${NC}"
  fi
  if [ "$HAS_COMPAT_PROJECT" -eq 0 ] || [ "$HAS_COMPAT_WORKFLOW" -eq 0 ] || [ "$HAS_COMPAT_SPRINT" -eq 0 ]; then
    echo ""
    echo -e "${BLUE}Compatibility (optional):${NC}"
    mark "$COMPAT_PROJECT"  "bmad/project"; HAS_COMPAT_PROJECT=$?
    mark "$COMPAT_WORKFLOW" "workflow-status"; HAS_COMPAT_WORKFLOW=$?
    mark "$COMPAT_SPRINT"   "sprint-status"; HAS_COMPAT_SPRINT=$?
  fi
  echo -e "Inferred phase: ${YELLOW}uninitialized${NC}"
  echo -e "Track: ${GRAY}${COMPAT_TRACK}${NC}"
  echo ""
  echo "PHASE=uninitialized"
  echo "TRACK=${COMPAT_TRACK}"
  echo "HAS_COMPAT_WORKFLOW=$([ "$HAS_COMPAT_WORKFLOW" -eq 0 ] && echo 1 || echo 0)"
  echo "COMPAT_TRACK=${COMPAT_TRACK}"
  echo "HAS_MIGRATION_SOURCE=${HAS_MIGRATION_SOURCE}"
  echo "MIGRATION_HINTS=${MIGRATION_HINTS}"
  exit 0
fi

# --- Threaded artifacts ---
echo -e "${BLUE}Threaded:${NC}"
mark "$OUT/project-context.md"            "project-context"; HAS_CTX=$?
mark "$OUT/decision-log.md"               "decision-log";    HAS_LOG=$?
echo ""

# --- Phase artifacts ---
echo -e "${BLUE}Analysis (optional):${NC}"
mark "$OUT/product-brief*.md $OUT/analysis/product-brief*.md" "product-brief"; HAS_BRIEF=$?
echo ""

echo -e "${BLUE}Planning:${NC}"
mark "$OUT/prd*.md $OUT/planning/prd*.md"             "prd";        HAS_PRD=$?
mark "$OUT/tech-spec*.md $OUT/planning/tech-spec*.md" "tech-spec";  HAS_SPEC=$?
mark "$OUT/epics*.md $OUT/planning/epics*.md"         "epics";      HAS_EPICS=$?
mark "$OUT/ux-design*.md $OUT/ux/ux-design*.md"       "ux-design";  HAS_UX=$?
echo ""

echo -e "${BLUE}Solutioning:${NC}"
mark "$OUT/architecture*.md $OUT/solutioning/architecture*.md" "architecture"; HAS_ARCH=$?
echo ""

echo -e "${BLUE}Implementation-handoff:${NC}"
STORY_DIR=""
for d in "$OUT/stories" "$OUT/implementation/stories" "$OUT"; do
  if exists_any "$d/*.story.md"; then STORY_DIR="$d"; break; fi
done
STORY_COUNT=0
READY_COUNT=0
BEYOND_COUNT=0
if [ -n "$STORY_DIR" ]; then
  for sf in "$STORY_DIR"/*.story.md; do
    [ -e "$sf" ] || continue
    STORY_COUNT=$((STORY_COUNT+1))
    # Read the Status line (first match of "ready-for-dev" / status field)
    if grep -qiE '^(status:|## *status)' "$sf" 2>/dev/null; then
      st=$(grep -iE 'ready-for-dev|in-progress|review|done|backlog' "$sf" 2>/dev/null | head -1 | tr '[:upper:]' '[:lower:]')
    else
      st=""
    fi
    case "$st" in
      *in-progress*|*review*|*done*) BEYOND_COUNT=$((BEYOND_COUNT+1)); READY_COUNT=$((READY_COUNT+1)) ;;
      *ready-for-dev*)               READY_COUNT=$((READY_COUNT+1)) ;;
    esac
  done
  printf "  ${GREEN}[x]${NC} %-22s ${GRAY}%s (%d stories, %d ready-for-dev)${NC}\n" \
    "stories" "$STORY_DIR" "$STORY_COUNT" "$READY_COUNT"
  HAS_STORIES=0
else
  printf "  ${GRAY}[ ]${NC} %-22s ${GRAY}(no *.story.md found)${NC}\n" "stories"
  HAS_STORIES=1
fi
echo ""

if [ "$HAS_COMPAT_PROJECT" -eq 0 ] || [ "$HAS_COMPAT_WORKFLOW" -eq 0 ] || [ "$HAS_COMPAT_SPRINT" -eq 0 ]; then
  echo -e "${BLUE}Compatibility (optional):${NC}"
  mark "$COMPAT_PROJECT"  "bmad/project"; HAS_COMPAT_PROJECT=$?
  mark "$COMPAT_WORKFLOW" "workflow-status"; HAS_COMPAT_WORKFLOW=$?
  mark "$COMPAT_SPRINT"   "sprint-status"; HAS_COMPAT_SPRINT=$?
  if [ "$COMPAT_TRACK" != "unknown" ]; then
    printf "  ${GRAY}compat track:${NC} %s\n" "$COMPAT_TRACK"
  fi
  echo ""
fi

# --- Track detection (from decision-log) ---
TRACK="unknown"
if [ "$HAS_LOG" -eq 0 ]; then
  raw=$(grep -iE 'track[:= ].*(quick[- ]?flow|bmad[- ]?method|enterprise)' "$OUT/decision-log.md" 2>/dev/null | tail -1)
  case "$(echo "$raw" | tr '[:upper:]' '[:lower:]')" in
    *enterprise*)            TRACK="enterprise" ;;
    *bmad?method*|*bmad-method*|*bmad_method*) TRACK="bmad-method" ;;
    *quick*)                 TRACK="quick-flow" ;;
  esac
fi
if [ "$TRACK" = "unknown" ] && [ "$COMPAT_TRACK" != "unknown" ]; then
  TRACK="$COMPAT_TRACK"
fi

# --- Phase inference ---
PHASE="planning"
if [ "$HAS_CTX" -ne 0 ]; then
  PHASE="uninitialized"
elif [ "$HAS_STORIES" -eq 0 ] && [ "$STORY_COUNT" -gt 0 ] && [ "$READY_COUNT" -eq "$STORY_COUNT" ]; then
  if [ "$BEYOND_COUNT" -gt 0 ]; then
    PHASE="implementation-external"   # dev tool has taken over
  else
    PHASE="handoff-complete"
  fi
elif [ "$HAS_STORIES" -eq 0 ]; then
  PHASE="implementation-handoff"
elif [ "$HAS_ARCH" -eq 0 ] || [ "$HAS_EPICS" -eq 0 ]; then
  PHASE="solutioning"
elif [ "$HAS_PRD" -eq 0 ] || [ "$HAS_SPEC" -eq 0 ]; then
  PHASE="planning"
else
  PHASE="planning"
fi

echo -e "${BLUE}Inferred phase:${NC} ${YELLOW}${PHASE}${NC}"
echo -e "${BLUE}Track:${NC} ${YELLOW}${TRACK}${NC}"
echo ""

# Machine-readable tail (consumed by recommend-next.sh)
echo "PHASE=${PHASE}"
echo "TRACK=${TRACK}"
echo "HAS_CTX=$([ $HAS_CTX -eq 0 ] && echo 1 || echo 0)"
echo "HAS_LOG=$([ $HAS_LOG -eq 0 ] && echo 1 || echo 0)"
echo "HAS_BRIEF=$([ $HAS_BRIEF -eq 0 ] && echo 1 || echo 0)"
echo "HAS_PRD=$([ $HAS_PRD -eq 0 ] && echo 1 || echo 0)"
echo "HAS_SPEC=$([ $HAS_SPEC -eq 0 ] && echo 1 || echo 0)"
echo "HAS_EPICS=$([ $HAS_EPICS -eq 0 ] && echo 1 || echo 0)"
echo "HAS_UX=$([ $HAS_UX -eq 0 ] && echo 1 || echo 0)"
echo "HAS_ARCH=$([ $HAS_ARCH -eq 0 ] && echo 1 || echo 0)"
echo "HAS_STORIES=$([ $HAS_STORIES -eq 0 ] && echo 1 || echo 0)"
echo "STORY_COUNT=${STORY_COUNT}"
echo "READY_COUNT=${READY_COUNT}"
echo "BEYOND_COUNT=${BEYOND_COUNT}"
echo "HAS_COMPAT_WORKFLOW=$([ $HAS_COMPAT_WORKFLOW -eq 0 ] && echo 1 || echo 0)"
echo "COMPAT_TRACK=${COMPAT_TRACK}"
echo "HAS_MIGRATION_SOURCE=${HAS_MIGRATION_SOURCE}"
echo "MIGRATION_HINTS=${MIGRATION_HINTS}"
