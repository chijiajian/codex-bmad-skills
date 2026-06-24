# BMAD Planning & Orchestrator — Shared Helpers Reference

Reusable patterns and shared script documentation for all skills in the
**bmad-planning-orchestrator** plugin. Skills reference this file to avoid
repeating boilerplate. Keep SKILL.md instructions short and cite `helpers.md#<anchor>`
instead of embedding full patterns.

**Scope contract:** Every script and pattern documented here is planning-only.
None of these utilities write application code, run tests, lint, build, or review diffs.
The last artifact any helper may produce is a ready-for-dev story file or a handoff manifest.

---

## Shared Scripts

All shared scripts live at `../scripts/` relative to this reference file and
`../../scripts/` relative to an individual skill directory. When running a
bundled script, resolve it to the absolute path in the installed plugin
location; never hardcode machine-specific paths.

---

### load-config.sh

**Path:** `../scripts/load-config.sh`

Reads `<output-folder>/config.yaml` and emits the project configuration.

**Usage:**
```sh
sh "../scripts/load-config.sh" [--output <folder>] [--json] [--export]
```

| Flag | Effect |
|------|--------|
| `--output <folder>` | Override output folder (default: `bmad-output`) |
| `--json` | Emit a JSON object |
| `--export` | Emit `export VAR=value` lines (eval-able in the caller shell) |

**Default output (key=value, one per line):**
```
PROJECT_NAME=my-app
PROJECT_TRACK=bmad-method
OUTPUT_FOLDER=bmad-output
STORIES_FOLDER=bmad-output/stories
DECISION_LOG=bmad-output/decision-log.md
PROJECT_CONTEXT=bmad-output/project-context.md
SPRINT_STATUS=bmad-output/sprint-status.yaml
```

**Exit codes:** `0` = found; `1` = config not found (not initialized).

**Skill usage pattern:**
```
1. Run load-config.sh to discover OUTPUT_FOLDER and PROJECT_TRACK.
2. Branch on TRACK:
     quick-flow   → tech-spec only, skip PRD/architecture
     bmad-method  → PRD + architecture (+ optional UX)
     enterprise   → PRD + architecture + security + DevOps planning
3. Use OUTPUT_FOLDER for all artifact paths; never hardcode paths.
```

---

### check-phase.sh

**Path:** `../scripts/check-phase.sh`

Scans the output folder for planning artifacts and prints the inferred current
phase, project track, and recommended next skill. Read-only; produces no documents.

**Usage:**
```sh
sh "../scripts/check-phase.sh" [--output <folder>]
```

**Output (always on stdout):**
```
PHASE=<phase>
TRACK=<track>
NEXT_SKILL=<bmad-planning-orchestrator:skill-name | none>
REASON=<human-readable rationale>
```

**Phase values:**

| Phase | Meaning |
|-------|---------|
| `uninitialized` | No workspace found (`bmad-output/` absent) |
| `analysis` | Workspace exists; no planning artifacts yet |
| `planning` | Product brief done; PRD / tech-spec in progress |
| `solutioning` | PRD done; architecture in progress |
| `implementation-handoff` | Architecture done; stories being created |
| `handoff-complete` | All stories `ready-for-dev`; external dev tool takes over |

**Skill usage pattern (routing):**
```
1. Run check-phase.sh to get PHASE and NEXT_SKILL.
2. If PHASE=uninitialized → invoke bmad-init first.
3. If PHASE=handoff-complete → inform user; do not plan further.
4. Otherwise → suggest NEXT_SKILL to the user and let them confirm.
```

---

### update-status.sh

**Path:** `../scripts/update-status.sh`

Two sub-commands:

#### Sub-command: story

Updates the `status:` field for a story in `sprint-status.yaml`.

```sh
sh "../scripts/update-status.sh" story \
    --id <story-id> --status <status> [--output <folder>]
```

Valid `--status` values: `backlog` `ready-for-dev` `in-progress` `review` `done`

`--id` accepts the bare form (`2.1`) or the full slug (`2.1.stripe-integration`).
Also updates `last_updated` timestamp in the file.

**Example:**
```sh
sh "../scripts/update-status.sh" story \
    --id 2.1.stripe-integration --status ready-for-dev
```

#### Sub-command: decision

Prepends a new dated entry to `decision-log.md`.

```sh
sh "../scripts/update-status.sh" decision \
    --title "Chose PostgreSQL over SQLite" \
    --body  "SQLite cannot handle concurrent writes at our expected load." \
    --skill "bmad-architecture" \
    [--supersedes "<prior-entry-ref>"] \
    [--output <folder>]
```

Entry format (always newest-first):
```md
### YYYY-MM-DD — <title>
- **Decision:** <body>
- **Rationale:** _(added via update-status.sh — expand as needed)_
- **Made by:** <skill>
- **Supersedes:** <ref | none>
```

**Skill usage pattern:**
```
After producing a planning artifact:
  1. Call update-status.sh story --id <id> --status ready-for-dev
     for each story that is now complete and ready.
  2. For architecture / track / major scope decisions, call
     update-status.sh decision to keep the decision-log threaded.
```

---

### select-track.sh

**Path:** `../scripts/select-track.sh`

Prints the three BMAD scale-adaptive tracks with descriptions and a
heuristic-suggested default. Always defers final choice to the user.

```sh
sh "../scripts/select-track.sh" \
    [--stories <N>] [--teams one|many] [--compliance yes|no]
```

| Flag | Heuristic signal |
|------|-----------------|
| `--stories <N>` | Approximate story count |
| `--teams one\|many` | Single builder vs. multiple teams |
| `--compliance yes\|no` | Regulatory / security-governance requirement |

**Machine-readable tail (last 2 lines):**
```
SUGGESTED_TRACK=<quick-flow|bmad-method|enterprise>
SUGGESTION_REASON=<rationale>
```

**Track summary:**

| Track | Story count signal | Artifacts |
|-------|-------------------|-----------|
| `quick-flow` | 1–15 | tech-spec only |
| `bmad-method` | 10–50+ | PRD + Architecture (+ optional UX) |
| `enterprise` | 30+ | PRD + Architecture + Security planning + DevOps planning |

**Promotion rule:** when unsure between two tracks, prefer the lighter one.
Promote later if scope grows. This avoids over-engineering.

**Skill usage pattern (bmad-init):**
```
1. Gather signals from the user: rough story estimate, team size, compliance needs.
2. Run select-track.sh with those signals to get SUGGESTED_TRACK.
3. Present the suggestion and all three options to the user.
4. User confirms or overrides.
5. Store the confirmed track in config.yaml and log it in decision-log.md.
```

---

### scope-conflict-check.sh  (CRITICAL)

**Path:** `../scripts/scope-conflict-check.sh`

Given two or more story files, detect overlapping `Owned File/Module Scope` paths
and report which pairs **cannot run in the same parallel wave**.

**Fail-closed guarantee:** if scope is missing or ambiguous for any story, that
story is reported as `BLOCKED` and treated as non-parallel. It is always safer to
sequence than to risk a merge collision.

```sh
# Check all stories in a directory
sh "../scripts/scope-conflict-check.sh" \
    --stories bmad-output/stories [--ids 1.1,1.2,2.1] [--format text|json]

# Check specific files
sh "../scripts/scope-conflict-check.sh" \
    --story-files story1.story.md story2.story.md story3.story.md \
    [--format text|json]
```

**Text output:**
```
CONFLICT: 1.1 vs 2.3  path=src/auth/ overlaps src/auth/login.ts  reason=file-scope-overlap
OK: 1.1 vs 1.2
BLOCKED: 3.2  reason=no Owned File/Module Scope declared

[scope-conflict-check] 1 conflict(s), 1 blocked (no scope)
Stories with conflicts or missing scope MUST NOT share a parallel wave.
```

**JSON output (`--format json`):**
```json
[
  {"type": "conflict", "a": "1.1", "b": "2.3",
   "path": "src/auth/ overlaps src/auth/login.ts", "reason": "file-scope-overlap"},
  {"type": "ok", "a": "1.1", "b": "1.2", "path": "", "reason": ""},
  {"type": "blocked", "a": "3.2", "b": "", "path": "", "reason": "no Owned File/Module Scope declared"}
]
```

**Exit codes:** `0` = no conflicts; `2` = one or more conflicts or blocked stories.

**Path overlap rules (same as the parallel-plan graph builder):**
- Exact match: `src/payments/stripe.ts` == `src/payments/stripe.ts`
- Directory prefix: `src/auth/` matches any descendant `src/auth/login.ts`
- Normalization: leading `./` and trailing `/` are stripped before comparison

**Skill usage pattern (bmad-parallel-plan and bmad-sprint-planning):**
```
Before assigning stories to the same parallel wave:
  1. Run scope-conflict-check.sh on the candidate set.
  2. Any CONFLICT pair → must be placed in different waves (sequence them).
  3. Any BLOCKED story → return it to the scrum-master for scope declaration
     before re-running the wave assignment.
  4. Only OK pairs may share a wave.
  5. Record wave assignments in sprint-status.yaml (parallel_set field).
```

---

## Reusable Patterns

### Pattern: Load Config + Route by Track

Referenced by most skills at startup.

```
1. sh "../scripts/load-config.sh" --export
   → eval the output to get BMAD_PROJECT_TRACK, BMAD_OUTPUT_FOLDER, etc.
2. Branch on BMAD_PROJECT_TRACK:
     quick-flow  → short artifact set; skip sections marked [bmad-method+]
     bmad-method → standard artifact set
     enterprise  → standard + security/devops planning sections
3. Use BMAD_OUTPUT_FOLDER as the base for all artifact reads/writes.
```

### Pattern: Update Status After Artifact Completion

Referenced by every artifact-producing skill.

```
After writing a planning artifact to disk:
  1. If the artifact is a story:
       sh "../scripts/update-status.sh" story \
           --id <id> --status ready-for-dev
  2. If a major architectural/scope decision was made:
       sh "../scripts/update-status.sh" decision \
           --title "<short title>" --body "<decision>" --skill "<skill-name>"
  3. Do NOT update story status to in-progress, review, or done — those
     transitions belong to the external dev tool.
```

### Pattern: Check Phase Before Acting

Referenced by the bmad-help routing skill.

```
1. sh "../scripts/check-phase.sh" --output bmad-output
2. Parse PHASE and NEXT_SKILL from stdout.
3. If PHASE=uninitialized  → tell user to run bmad-init; stop.
4. If PHASE=handoff-complete → tell user all stories are ready-for-dev;
     the external dev tool should take over; stop planning.
5. Otherwise → present NEXT_SKILL suggestion; let user confirm or redirect.
```

### Pattern: Scope Conflict Gate (Parallel Planning)

Referenced by bmad-parallel-plan and bmad-sprint-planning.

```
Before producing a parallelization plan:
  1. sh "../scripts/scope-conflict-check.sh" \
         --stories "${BMAD_OUTPUT_FOLDER}/stories" --format json
  2. Parse JSON result array:
       - "conflict" pairs → MUST be in different waves
       - "blocked" stories → report back to scrum-master (no scope declared);
           do not assign to any wave until fixed
       - "ok" pairs → eligible to share a wave
  3. Feed conflict pairs as undirected conflict edges into the wave algorithm.
  4. Document deferred (blocked) stories in the handoff manifest and decision-log.
```

### Pattern: Story Status Lifecycle

The external dev tool owns transitions after `ready-for-dev`. The planning plugin
only sets `backlog` → `ready-for-dev`. Never write `in-progress`, `review`, or
`done` in planning scripts.

```
planning plugin writes:    backlog  →  ready-for-dev
external dev tool writes:  ready-for-dev  →  in-progress  →  review  →  done
```

### Pattern: Decision Log Threading

Every skill that makes a substantive planning decision appends to `decision-log.md`
so later skills have traceability back to why choices were made.

```
Append after:
  - Track selection (bmad-init)
  - Key architecture decisions (bmad-architecture)
  - Scope changes / course corrections (bmad-correct-course)
  - Epic decomposition rationale (bmad-epics-and-stories)
  - Parallel wave cap or deferred-story decisions (bmad-parallel-plan)

Format (newest first — never rewrite past entries):
  ### YYYY-MM-DD — <short title>
  - **Decision:** <what>
  - **Rationale:** <why; alternatives considered>
  - **Made by:** <skill-name>
  - **Supersedes:** <prior entry ref, or none>
```

---

## Error Handling

### Config-Not-Found

```
If load-config.sh exits 1 (config missing):
  → Inform the user: "No BMAD planning workspace found."
  → Offer: "Run $bmad-init to initialize."
  → Do not proceed with the requested skill.
```

### Sprint-Status-Missing

```
If sprint-status.yaml does not exist when update-status.sh story is called:
  → Run init-sprint-status.sh (bmad-sprint-planning) first to scaffold the file.
  → Then retry the status update.
  → Log the scaffold event in decision-log.md.
```

### Scope-Blocked Stories

```
If scope-conflict-check.sh reports BLOCKED stories:
  → Do not assign them to any wave.
  → Return to bmad-epics-and-stories to declare scope.
  → Re-run scope-conflict-check.sh after scope is declared.
  → The planner must never invent file paths to unblock a story.
```

### Dependency Cycle

```
If plan-parallel-waves.py (or equivalent logic) detects a cycle:
  → Report the cycle to the user with the affected story ids.
  → Do not produce a wave plan.
  → Refer to bmad-correct-course to resolve the cyclic dependency.
```

---

## Token Optimization

Reference this file instead of embedding full instructions in SKILL.md:

```
# Good (SKILL.md stays under ~5K tokens):
  "Load config: follow helpers.md#load-config-sh"
  "Check phase: follow helpers.md#check-phase-sh"
  "Scope gate before wave assignment: helpers.md#pattern-scope-conflict-gate"

# Bad (bloats SKILL.md):
  [Full 50-line config loading instructions repeated inline]
```

Load this file lazily — only when the relevant pattern is actually needed.
Start each skill with SKILL.md only (~2–3K tokens); load helpers.md when
a shared operation is required.
