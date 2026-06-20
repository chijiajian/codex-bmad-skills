#!/usr/bin/env sh
# BMAD Planning & Orchestrator — Update Sprint Status / Decision Log
# ------------------------------------------------------------------
# Two sub-commands:
#
#   story   — update a story's status field in sprint-status.yaml
#   decision — append a new entry to decision-log.md
#
# SCOPE: planning and orchestration only. Never writes application code,
# runs tests, lints, or builds. No story points, velocity, or burndown.
#
# Usage:
#   sh <installed-plugin-root>/scripts/update-status.sh" story \
#       --id <story-id> --status <status> [--output <folder>]
#
#   sh <installed-plugin-root>/scripts/update-status.sh" decision \
#       --title <title> --body <text> --skill <skill-name> \
#       [--supersedes <ref>] [--output <folder>]
#
# story --status values:
#   backlog | ready-for-dev | in-progress | review | done
#
# story --id format:
#   {epic}.{story}  e.g. 2.1
#   or the full slug   e.g. 2.1.stripe-integration
#
# Exit codes:
#   0  Success
#   1  Usage error or file not found
#
# Implementation note:
#   sprint-status.yaml is YAML but we edit it with portable sed/awk (no yq).
#   The story entry format produced by bmad-sprint-planning always puts status
#   on its own indented line directly following the `- id:` block. We locate
#   the id and update the next `status:` occurrence in that block.
#
# Note: resolve this script from the installed plugin root or use its absolute path.

set -eu

SUBCOMMAND=""
STORY_ID=""
NEW_STATUS=""
DECISION_TITLE=""
DECISION_BODY=""
DECISION_SKILL=""
DECISION_SUPERSEDES="none"
OUTPUT_FOLDER="bmad-output"

# --------------------------------------------------------------------------- #
# Arg parsing
# --------------------------------------------------------------------------- #
if [ $# -gt 0 ]; then
  SUBCOMMAND="$1"
  shift
fi

while [ $# -gt 0 ]; do
  case "$1" in
    --id)          STORY_ID="$2";              shift 2 ;;
    --status)      NEW_STATUS="$2";            shift 2 ;;
    --title)       DECISION_TITLE="$2";        shift 2 ;;
    --body)        DECISION_BODY="$2";         shift 2 ;;
    --skill)       DECISION_SKILL="$2";        shift 2 ;;
    --supersedes)  DECISION_SUPERSEDES="$2";   shift 2 ;;
    --output)      OUTPUT_FOLDER="$2";         shift 2 ;;
    -h|--help)
      grep '^#' "$0" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *) printf 'Unknown option: %s\n' "$1" >&2; exit 1 ;;
  esac
done

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

# --------------------------------------------------------------------------- #
# Sub-command: story
# --------------------------------------------------------------------------- #
if [ "$SUBCOMMAND" = "story" ]; then
  [ -n "$STORY_ID" ]   || die "--id is required for the 'story' sub-command."
  [ -n "$NEW_STATUS" ] || die "--status is required for the 'story' sub-command."

  # Validate status value
  case "$NEW_STATUS" in
    backlog|ready-for-dev|in-progress|review|done) ;;
    *) die "Invalid status '$NEW_STATUS'. Valid values: backlog ready-for-dev in-progress review done" ;;
  esac

  SPRINT_STATUS="${OUTPUT_FOLDER}/sprint-status.yaml"
  [ -f "$SPRINT_STATUS" ] || die "sprint-status.yaml not found at: $SPRINT_STATUS"

  # Strip optional slug suffix from id (2.1.some-slug -> 2.1)
  BARE_ID=$(printf '%s' "$STORY_ID" | sed 's/^\([0-9]*\.[0-9]*\).*/\1/')

  # We locate the block that contains the target id and replace the first
  # status: line within it. awk handles multi-line context portably.
  TMPFILE="${SPRINT_STATUS}.tmp.$$"
  UPDATED=0

  awk -v id="$BARE_ID" -v full_id="$STORY_ID" -v new_status="$NEW_STATUS" '
  BEGIN { in_block = 0; done = 0 }
  {
    # Detect a story list entry line (  - id: "2.1" or  - id: "2.1.slug")
    if (!done && match($0, /^[[:space:]]*-[[:space:]]*id:[[:space:]]*/)) {
      # Extract the id value
      rest = substr($0, RSTART + RLENGTH)
      gsub(/^["'"'"']|["'"'"'][[:space:]]*$/, "", rest)
      # Match bare id OR full slug
      if (rest == id || rest == full_id || index(rest, id ".") == 1) {
        in_block = 1
      } else {
        in_block = 0
      }
    }
    # Detect start of next entry (resets block)
    if (in_block && NR > 1 && match($0, /^[[:space:]]*-[[:space:]]*id:/) && !match($0, id)) {
      in_block = 0
    }
    # Replace status in the current block (first occurrence only)
    if (in_block && !done && match($0, /^[[:space:]]*status:[[:space:]]*/)) {
      indent = substr($0, 1, RSTART - 1)
      print indent "status: " new_status
      done = 1
      next
    }
    print
  }
  END { if (!done) { print "WARNING: story id not found: " id > "/dev/stderr" } }
  ' "$SPRINT_STATUS" > "$TMPFILE"

  mv "$TMPFILE" "$SPRINT_STATUS"

  # Also update last_updated timestamp
  TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  TMPFILE2="${SPRINT_STATUS}.tmp2.$$"
  sed "s/^last_updated:.*/last_updated: \"${TIMESTAMP}\"/" "$SPRINT_STATUS" > "$TMPFILE2"
  mv "$TMPFILE2" "$SPRINT_STATUS"

  printf '[update-status] story %s -> %s  (%s)\n' "$STORY_ID" "$NEW_STATUS" "$SPRINT_STATUS"
  exit 0
fi

# --------------------------------------------------------------------------- #
# Sub-command: decision
# --------------------------------------------------------------------------- #
if [ "$SUBCOMMAND" = "decision" ]; then
  [ -n "$DECISION_TITLE" ] || die "--title is required for the 'decision' sub-command."
  [ -n "$DECISION_BODY" ]  || die "--body is required for the 'decision' sub-command."
  [ -n "$DECISION_SKILL" ] || die "--skill is required for the 'decision' sub-command."

  DECISION_LOG="${OUTPUT_FOLDER}/decision-log.md"
  [ -f "$DECISION_LOG" ] || die "decision-log.md not found at: $DECISION_LOG"

  DATE_STR=$(date -u +"%Y-%m-%d")

  NEW_ENTRY="### ${DATE_STR} — ${DECISION_TITLE}
- **Decision:** ${DECISION_BODY}
- **Rationale:** _(added via update-status.sh — expand as needed)_
- **Made by:** ${DECISION_SKILL}
- **Supersedes:** ${DECISION_SUPERSEDES}

---"

  # Insert the entry just before the first "### YYYY-MM-DD" line (newest-first order),
  # or just after the first "---" separator if no prior entry exists yet,
  # or append at end as a final fallback.
  # We write to a temp file to avoid awk multiline -v portability issues.
  TMPFILE="${DECISION_LOG}.tmp.$$"

  INJECTED=0
  LINENUM=0
  while IFS= read -r dline; do
    LINENUM=$((LINENUM + 1))
    # Inject before the first existing dated entry (### YYYY-MM-DD)
    if [ "$INJECTED" -eq 0 ] && printf '%s' "$dline" | grep -qE '^###[[:space:]][0-9]{4}-[0-9]{2}-[0-9]{2}'; then
      printf '%s\n' "$NEW_ENTRY" >> "$TMPFILE"
      printf '\n' >> "$TMPFILE"
      INJECTED=1
    fi
    printf '%s\n' "$dline" >> "$TMPFILE"
    # If we hit the first "---" separator and still not injected, mark that position
    # and inject right after it (no prior entries yet)
    if [ "$INJECTED" -eq 0 ] && [ "$dline" = "---" ]; then
      printf '\n' >> "$TMPFILE"
      printf '%s\n' "$NEW_ENTRY" >> "$TMPFILE"
      INJECTED=1
    fi
  done < "$DECISION_LOG"

  # Fallback: append at end
  if [ "$INJECTED" -eq 0 ]; then
    printf '\n' >> "$TMPFILE"
    printf '%s\n' "$NEW_ENTRY" >> "$TMPFILE"
  fi

  mv "$TMPFILE" "$DECISION_LOG"
  printf '[update-status] decision logged: "%s"  (%s)\n' "$DECISION_TITLE" "$DECISION_LOG"
  exit 0
fi

# --------------------------------------------------------------------------- #
# No valid sub-command
# --------------------------------------------------------------------------- #
printf 'Usage: %s <story|decision> [options]\n' "$(basename "$0")" >&2
printf '  story:    --id <id> --status <status> [--output <folder>]\n' >&2
printf '  decision: --title <t> --body <b> --skill <s> [--supersedes <r>] [--output <folder>]\n' >&2
exit 1
