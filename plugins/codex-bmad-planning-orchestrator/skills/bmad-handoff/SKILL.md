---
name: bmad-handoff
description: |
  For BMAD planning requests or an established BMAD planning workflow.
  Emits bmad-output/handoff-manifest.json from ready-for-dev stories for external
  dev tools or orchestrators. Use when the user says "$bmad-handoff",
  "bmad:handoff", "generate a handoff", "create handoff manifest", "export stories for
  dev", "hand off to dev tool", "ready to hand off", "prepare handoff for
  external tool", "export ready-for-dev stories", or asks for an exportable
  artifact of stories ready for dev. Read-only with respect to story files.
---

# BMAD Handoff

## Codex Resource Paths

Resolve bundled resources relative to this skill directory. When running a bundled script, use the absolute path to that script from the installed plugin location; relative examples are shown from this `SKILL.md` directory. Shared BMAD helper scripts live under `../../scripts/`, and shared references live under `../../references/`.

Use the [shared planning contract](../../references/planning-contract.md) for artifact names, status ownership, existing authorization, and runtime tool adaptation.

**Purpose:** Scan the planning output folder for all stories at status `ready-for-dev`,
compile them into a single `handoff-manifest.json`, and leave it where any downstream
dev tool can read it — without coupling to any specific runner.

This is the last artifact the planning plugin produces. What happens next is owned by
the external dev tool, not by this skill.

## Preconditions

Run this skill after the story-writing phase is complete and you (or the user) have
confirmed that at least one story carries status `ready-for-dev`. The manifest is a
point-in-time snapshot; re-run the skill to refresh it.

## Workflow

Use the available progress-tracking tool to track progress through these steps.

### 1. Locate the output folder

Look for `bmad-output/project-context.md` (the default output folder) or ask the
user for the output folder. Default: `bmad-output/`.

### 2. Discover story files

Glob for `**/{epic}.{story}.*.story.md` under the output folder.
Accept alternative flat layouts (`stories/*.story.md`) if the glob turns up nothing.

### 3. Filter to ready-for-dev

Read the `**Status:**` header field of each story file (in the story header block, not a
`## Status` heading). Include only stories whose status value is exactly `ready-for-dev`.

If none are found, report which statuses were seen and stop — do not produce an
empty manifest.

### 4. Extract per-story fields

For each qualifying story file, extract:

| Field | Source in story file |
|---|---|
| `id` | `**Story ID:**` (epic.story); normalize legacy filename/slug IDs |
| `storyFilePath` | Relative path from project root |
| `status` | `**Status:**` header field value |
| `epic` | First segment of filename, e.g. `"2"` in `2.1.stripe.story.md` |
| `storyNumber` | Second segment, e.g. `"1"` |
| `title` | First H1 or `## Story` heading text |
| `ownedScope` | `## Owned File/Module Scope` — list every path verbatim |
| `wave` | Matching sprint-status.yaml row → parallel_set; story annotation only as a fallback |
| `parallelSet` | Same section — parallel set label if present (string or null) |
| `dependencies` | `## Dependency Maps` → blocked-by story IDs (array, may be empty) |
| `acceptanceCriteriaSummary` | First 3 AC items from `## Acceptance Criteria`, each ≤120 chars |
| `lockedSectionsNote` | Static string — see schema |
| `devAgentRecord` | Static null — placeholder for the dev tool to populate |

### 5. Compute wave order

Reuse current sprint-status.yaml wave annotations first. Validate dependencies and Owned Scope before export. If no scheduling view exists, route to bmad-sprint-planning. For a direct manual export with known dependencies:
- Stories with empty `dependencies` arrays are wave 1.
- A story whose every dependency is in wave N or lower is wave N+1.
- Serialize intersecting scopes, even without an explicit dependency. Reject cycles and unresolved ordering instead of inventing a wave; only `parallelSet` may be null when not annotated.

### 6. Write the manifest

Write to `{outputFolder}/handoff-manifest.json`.

Use the schema from
`../bmad-handoff/templates/handoff-manifest.schema.json`
as the structural contract. Populate `schemaVersion: "1.0"`.

Sort stories by `wave` ascending, then by `id` ascending within each wave.
Prepare the candidate in a temporary file and validate it before replacing the manifest:

```sh
python3 ../../scripts/validate_handoff.py <candidate-manifest.json>
```

This needs jsonschema from the repository requirements.txt. Keep the previous manifest
if schema, dependency or same-wave scope checks fail.

### 7. Report to the user

Print a compact summary:

```
Handoff manifest written → bmad-output/handoff-manifest.json
  schemaVersion : 1.0
  stories       : <N> ready-for-dev
  waves         : <W>  (wave 1 has <X> stories; verify external prerequisites before execution)
  output path   : bmad-output/handoff-manifest.json
```

If any story was missing required sections (e.g. no `## Owned File/Module Scope`),
report them as export blockers and preserve the prior manifest. Do not omit or fabricate required data.

## Manifest Field Definitions (Quick Reference)

See REFERENCE.md for the full schema narrative and adapter notes.

| Field | Type | Required | Notes |
|---|---|---|---|
| `schemaVersion` | string | yes | Semver string; current = `"1.0"` |
| `generatedAt` | string | yes | ISO-8601 UTC timestamp |
| `projectName` | string | yes | From project-context.md or user input |
| `outputFolder` | string | yes | Relative path used to find stories |
| `stories` | array | yes | One object per ready-for-dev story |
| `stories[].id` | string | yes | Unique story identifier |
| `stories[].storyFilePath` | string | yes | Relative path to the .story.md file |
| `stories[].status` | string | yes | Always `"ready-for-dev"` in this manifest |
| `stories[].epic` | string | yes | Epic identifier |
| `stories[].storyNumber` | string | yes | Story number within epic |
| `stories[].title` | string | yes | Human-readable story title |
| `stories[].ownedScope` | array | yes | File/module paths this story may modify |
| `stories[].wave` | integer | yes | Execution wave (1 = no dependencies) |
| `stories[].parallelSet` | string\|null | no | Label if explicitly grouped |
| `stories[].dependencies` | array | yes | Story IDs that must complete first |
| `stories[].acceptanceCriteriaSummary` | array | yes | First 3 AC items, ≤120 chars each |
| `stories[].lockedSectionsNote` | string | yes | Instruction to dev tools |
| `stories[].devAgentRecord` | null | yes | Dev tool populates; always null at emit time |

`lockedSectionsNote` is always the string:
> "Sections Acceptance Criteria, Dev Notes, and Testing are LOCKED. External dev tools
> must not edit them. Populate only the Dev Agent Record section."

## Subagent Strategy

Subagents, when the capability is available, are an important part of this
workflow. Use them as directed by this section.

If the current Codex runtime requires explicit user authorization for subagents,
ask once before launching any subagent and apply that answer to the whole
workflow run. If authorization is denied, or subagent tooling is unavailable,
execute the listed slices sequentially in the main context and keep the same
outputs.

For small backlogs (≤15 stories), this skill runs single-threaded — the extraction
loop is fast and context fits in one session.

For large backlogs (16+ stories), fan out story extraction in parallel:

| Agent | Task |
|---|---|
| Agent 1…N | Read story files in their assigned slice; extract fields; return JSON fragment |
| Coordinator | Merge fragments; compute wave order; write manifest |

Each agent receives the list of file paths for its slice plus the field extraction
table above. It returns a JSON array of story objects (no wave field yet).
The coordinator merges, computes waves, sorts, and writes the manifest.

## Key Guidelines

1. Never fabricate field values. Emit null only for schema-nullable fields.
   If required metadata is missing, report the gap and leave the previous manifest intact.
2. Do not modify story files — this skill is read-only with respect to story content.
3. `ownedScope` is critical for parallel-conflict safety; never collapse or summarize it.
4. This manifest is a STABLE versioned interface. Increment `schemaVersion` (as a
   separate schema revision, not within this run) before adding or removing fields.
5. Include all ready-for-dev documents, including later waves. Preserve dependencies
   on completed/external stories; verify their completion from source artifacts before
   claiming any story can start. Validate internal ordering and same-wave scope safety.
6. If the user asks to "re-run" or "refresh" the manifest, overwrite the existing file.

---

> ---
> Part of the **BMAD Planning & Orchestrator** plugin — a Codex harness for the **BMAD Method** by the **BMAD Code Organization** (https://github.com/bmad-code-org/BMAD-METHOD). Implements the spirit of `bmad-handoff`. All methodology credit belongs to the BMAD Code Organization.
