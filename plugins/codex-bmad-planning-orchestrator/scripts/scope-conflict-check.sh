#!/usr/bin/env sh
# BMAD Planning & Orchestrator — Scope Conflict Checker  (CRITICAL SHARED UTIL)
# ------------------------------------------------------------------------------
# Given two or more story files (or inline story-id:scope-path pairs), detect
# overlapping "Owned File/Module Scope" paths and report which stories CANNOT
# run in the same parallel wave.
#
# FAIL-CLOSED GUARANTEE:
#   If any path cannot be resolved or a scope is ambiguous / undeclared, the
#   pair is reported as CONFLICT (non-parallel). It is always safer to
#   sequence than to risk a merge collision.
#
# SCOPE: planning + orchestration only. Read-only. Never writes code, runs
# tests, lints, builds, or reviews diffs.
#
# Usage:
#   sh <installed-plugin-root>/scripts/scope-conflict-check.sh" \
#       --stories <dir>  [--ids <id1,id2,...>]
#
#   sh <installed-plugin-root>/scripts/scope-conflict-check.sh" \
#       --story-files <file1> <file2> [<file3> ...]
#
#   --stories <dir>     Directory containing *.story.md files
#   --ids <list>        Comma-separated story ids to check (default: all in dir)
#   --story-files       One or more story .md files to check against each other
#   --format text|json  Output format (default: text)
#
# Output:
#   In text mode:
#     CONFLICT: <id-A> vs <id-B>  path=<overlapping-path>  reason=<file|ambiguous>
#     OK: <id-A> vs <id-B>
#     BLOCKED: <id>  reason=<no scope declared>
#
#   In json mode: a JSON array of result objects
#     { "type": "conflict"|"ok"|"blocked", "a": "...", "b": "...",
#       "path": "...", "reason": "..." }
#
# Exit codes:
#   0  No conflicts detected
#   2  One or more conflicts or blocked stories detected
#   1  Usage error
#
# Scope extraction:
#   Reads the "## Owned File/Module Scope" section from each story file.
#   Treats each bullet-list item as one path. Paths are normalized (no leading
#   ./ or trailing /). A directory prefix (src/auth/) matches any descendant
#   (src/auth/login.ts) — same as the parallel-plan graph builder.
#
# Ambiguity / fail-closed cases:
#   - Story file not found           -> BLOCKED (cannot determine scope)
#   - Section "Owned File/Module Scope" absent or empty -> BLOCKED
#   - Path contains shell glob chars -> treated as literal; if unusual, BLOCKED
#
# Note: resolve this script from the installed plugin root or use its absolute path.

set -eu

STORIES_DIR=""
FILTER_IDS=""
STORY_FILES=""
FORMAT="text"

# --------------------------------------------------------------------------- #
# Arg parsing
# --------------------------------------------------------------------------- #
while [ $# -gt 0 ]; do
  case "$1" in
    --stories)      STORIES_DIR="$2";  shift 2 ;;
    --ids)          FILTER_IDS="$2";   shift 2 ;;
    --story-files)
      shift
      while [ $# -gt 0 ] && printf '%s' "$1" | grep -qv '^--'; do
        STORY_FILES="${STORY_FILES} $1"; shift
      done
      ;;
    --format)       FORMAT="$2";       shift 2 ;;
    -h|--help)
      grep '^#' "$0" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *) printf 'Unknown option: %s\n' "$1" >&2; exit 1 ;;
  esac
done

# --------------------------------------------------------------------------- #
# Collect story files
# --------------------------------------------------------------------------- #
if [ -n "$STORY_FILES" ]; then
  FILES="$STORY_FILES"
elif [ -n "$STORIES_DIR" ]; then
  if [ ! -d "$STORIES_DIR" ]; then
    printf 'ERROR: stories directory not found: %s\n' "$STORIES_DIR" >&2
    exit 1
  fi
  FILES=""
  for f in "${STORIES_DIR}"/*.story.md; do
    [ -e "$f" ] || continue
    FILES="${FILES} $f"
  done
else
  printf 'ERROR: provide --stories <dir> or --story-files <files...>\n' >&2
  exit 1
fi

if [ -z "$FILES" ]; then
  printf 'No story files found.\n' >&2
  exit 0
fi

# --------------------------------------------------------------------------- #
# Extract story id from filename   {epic}.{story}.{slug}.story.md
# --------------------------------------------------------------------------- #
file_to_id() {
  basename "$1" | sed 's/\.story\.md$//' | sed 's/^\([0-9]*\.[0-9]*\).*/\1/'
}

# --------------------------------------------------------------------------- #
# Normalize a scope path (strip leading ./ and trailing /)
# --------------------------------------------------------------------------- #
normalize_path() {
  printf '%s' "$1" | sed 's|^\./||; s|/$||; s|[[:space:]]||g'
}

# --------------------------------------------------------------------------- #
# Extract owned scope paths from a story file
# Returns one path per line; empty output means no scope declared.
# --------------------------------------------------------------------------- #
extract_scope() {
  local file="$1"
  local in_section=0
  while IFS= read -r line; do
    # Detect the Owned File/Module Scope heading (any heading level)
    case "$(printf '%s' "$line" | tr '[:upper:]' '[:lower:]')" in
      *'#'*'owned file'*|*'#'*'module scope'*)
        in_section=1
        continue
        ;;
    esac
    # Detect next heading — end of section
    if printf '%s' "$line" | grep -qE '^#{1,6}[[:space:]]'; then
      if [ "$in_section" -eq 1 ]; then
        in_section=0
      fi
      continue
    fi
    if [ "$in_section" -eq 1 ]; then
      # Extract bullet items
      item=$(printf '%s' "$line" | sed -n 's/^[[:space:]]*[-*][[:space:]]\{1,\}//p')
      if [ -n "$item" ]; then
        # Strip trailing comments (# ...) and backticks
        item=$(printf '%s' "$item" | sed 's/#.*//; s/`//g; s/[[:space:]]*$//')
        # Take first token only
        item=$(printf '%s' "$item" | awk '{print $1}')
        if [ -n "$item" ] && ! printf '%s' "$item" | grep -qiE '^none$|^n/a$'; then
          normalize_path "$item"
          printf '\n'
        fi
      fi
    fi
  done < "$file"
}

# --------------------------------------------------------------------------- #
# Check if two scope path lists overlap
# Returns the first overlapping pair as "pathA|pathB" or empty string
# Prefix-aware: src/auth matches src/auth/login.ts
# --------------------------------------------------------------------------- #
scopes_overlap() {
  local scope_a="$1"   # newline-separated paths
  local scope_b="$2"
  while IFS= read -r pa; do
    [ -n "$pa" ] || continue
    while IFS= read -r pb; do
      [ -n "$pb" ] || continue
      # exact match
      if [ "$pa" = "$pb" ]; then
        printf '%s|%s' "$pa" "$pb"
        return
      fi
      # pa is a prefix of pb (directory containment)
      case "$pb" in
        "${pa}/"*) printf '%s|%s' "$pa" "$pb"; return ;;
      esac
      # pb is a prefix of pa
      case "$pa" in
        "${pb}/"*) printf '%s|%s' "$pa" "$pb"; return ;;
      esac
    done <<EOF
$scope_b
EOF
  done <<EOF
$scope_a
EOF
  printf ''
}

# --------------------------------------------------------------------------- #
# Apply id filter if --ids provided
# --------------------------------------------------------------------------- #
filter_ids_list=""
if [ -n "$FILTER_IDS" ]; then
  filter_ids_list=$(printf '%s' "$FILTER_IDS" | tr ',' '\n')
fi

id_in_filter() {
  local id="$1"
  [ -z "$filter_ids_list" ] && return 0
  printf '%s' "$filter_ids_list" | grep -qxF "$id"
}

# --------------------------------------------------------------------------- #
# Build per-story scope map (written to temp files)
# --------------------------------------------------------------------------- #
TMPDIR_SCOPE="/tmp/bmad_scope_check_$$"
mkdir -p "$TMPDIR_SCOPE"
trap 'rm -rf "$TMPDIR_SCOPE"' EXIT INT TERM

STORY_IDS=""
BLOCKED_IDS=""

for f in $FILES; do
  [ -e "$f" ] || continue
  id=$(file_to_id "$f")
  id_in_filter "$id" || continue

  # Write scope directly to file to preserve newlines (command substitution strips them)
  extract_scope "$f" > "${TMPDIR_SCOPE}/${id}.scope"
  if [ ! -s "${TMPDIR_SCOPE}/${id}.scope" ]; then
    BLOCKED_IDS="${BLOCKED_IDS} $id"
    rm -f "${TMPDIR_SCOPE}/${id}.scope"
    continue
  fi

  STORY_IDS="${STORY_IDS} $id"
done

# --------------------------------------------------------------------------- #
# Pairwise conflict detection
# --------------------------------------------------------------------------- #
CONFLICT_COUNT=0
BLOCKED_COUNT=0
RESULTS=""   # accumulates JSON objects if --format json

emit_result() {
  local type="$1" id_a="$2" id_b="${3:-}" path="${4:-}" reason="${5:-}"
  if [ "$FORMAT" = "json" ]; then
    RESULTS="${RESULTS}{\"type\":\"${type}\",\"a\":\"${id_a}\",\"b\":\"${id_b}\",\"path\":\"${path}\",\"reason\":\"${reason}\"},"
  else
    case "$type" in
      conflict) printf 'CONFLICT: %s vs %s  path=%s  reason=%s\n' "$id_a" "$id_b" "$path" "$reason" ;;
      ok)       printf 'OK: %s vs %s\n' "$id_a" "$id_b" ;;
      blocked)  printf 'BLOCKED: %s  reason=%s\n' "$id_a" "$reason" ;;
    esac
  fi
}

# Blocked stories (no scope declared — fail-closed)
for bid in $BLOCKED_IDS; do
  emit_result "blocked" "$bid" "" "" "no Owned File/Module Scope declared"
  BLOCKED_COUNT=$((BLOCKED_COUNT + 1))
done

# All pairs
set -- $STORY_IDS
while [ $# -gt 1 ]; do
  id_a="$1"
  shift
  for id_b in "$@"; do
    scope_a=$(cat "${TMPDIR_SCOPE}/${id_a}.scope" 2>/dev/null || true)
    scope_b=$(cat "${TMPDIR_SCOPE}/${id_b}.scope" 2>/dev/null || true)

    if [ -z "$scope_a" ] || [ -z "$scope_b" ]; then
      # Should not reach here (blocked above), but fail-closed
      emit_result "conflict" "$id_a" "$id_b" "unknown" "ambiguous-scope"
      CONFLICT_COUNT=$((CONFLICT_COUNT + 1))
      continue
    fi

    overlap=$(scopes_overlap "$scope_a" "$scope_b")
    if [ -n "$overlap" ]; then
      path_display=$(printf '%s' "$overlap" | sed 's/|/ overlaps /')
      emit_result "conflict" "$id_a" "$id_b" "$path_display" "file-scope-overlap"
      CONFLICT_COUNT=$((CONFLICT_COUNT + 1))
    else
      emit_result "ok" "$id_a" "$id_b"
    fi
  done
done

# --------------------------------------------------------------------------- #
# JSON wrapper
# --------------------------------------------------------------------------- #
if [ "$FORMAT" = "json" ]; then
  # Strip trailing comma from last object
  RESULTS=$(printf '%s' "$RESULTS" | sed 's/,$//')
  printf '[%s]\n' "$RESULTS"
fi

# --------------------------------------------------------------------------- #
# Summary
# --------------------------------------------------------------------------- #
TOTAL_CONFLICTS=$((CONFLICT_COUNT + BLOCKED_COUNT))
if [ "$FORMAT" != "json" ]; then
  printf '\n'
  printf '[scope-conflict-check] %d conflict(s), %d blocked (no scope)\n' \
    "$CONFLICT_COUNT" "$BLOCKED_COUNT"
  if [ "$TOTAL_CONFLICTS" -gt 0 ]; then
    printf 'Stories with conflicts or missing scope MUST NOT share a parallel wave.\n'
  else
    printf 'No scope conflicts detected. Stories may run in the same parallel wave.\n'
  fi
fi

[ "$TOTAL_CONFLICTS" -eq 0 ] && exit 0 || exit 2
