---
name: bmad-sprint-planning
description: |
  For BMAD planning requests or an established BMAD planning workflow.
  Creates or maintains bmad-output/sprint-status.yaml as the story sequencing and
  scheduling view, mirroring lifecycle from story headers. Use for "$bmad-sprint-planning", "bmad:sprint-plan", or
  when the user says "sequence the stories", "build the sprint status", "create
  sprint-status.yaml", "assign parallel sets", "order stories by dependency", "set
  up story sequencing", "initialize sprint tracking", "ready the backlog", or
  "prepare for dev handoff". Sequencing only: no velocity, burndown, points,
  coverage metrics, implementation, tests, lints, or builds.
---

# BMAD Sprint Planning

## Codex Resource Paths

Resolve bundled resources relative to this skill directory. When running a bundled script, use the absolute path to that script from the installed plugin location; relative examples are shown from this `SKILL.md` directory. Shared BMAD helper scripts live under `../../scripts/`, and shared references live under `../../references/`.

Use the [shared planning contract](../../references/planning-contract.md) for artifact names, status ownership, existing authorization, and runtime tool adaptation.

**Role:** Sequencing & Handoff Bridge — Phase 4 orchestration
**Scheduling view:** `bmad-output/sprint-status.yaml`

---

## What This Skill Does

1. Reads planning artifacts (PRD, architecture, epics, stories) from `bmad-output/`.
2. Derives a dependency graph across all stories.
3. Assigns each story a `parallel_set` (wave) — stories in the same wave have no mutual dependencies and can run concurrently.
4. Emits `bmad-output/sprint-status.yaml` using the canonical template.
5. Mirrors lifecycle from story headers; complete documents remain `ready-for-dev` in every wave. Dependency satisfaction determines when execution may start.
6. Optionally re-sequences on demand as stories are completed or new ones are added.

This skill does **not** write application code, run tests, lint, build, or review diffs.

---

## Three-Intent Operation

| Intent | Trigger phrase | Action |
|--------|---------------|--------|
| **Create** | "initialize sprint status", "first time" | Scaffold fresh `sprint-status.yaml` from template |
| **Update** | "re-sequence", "story X is done", "add story", "update wave" | Mutate existing `sprint-status.yaml` in-place |
| **Validate** | "check sequencing", "are dependencies correct", "show wave plan" | Read and report without writing |

---

## Workflow — Create

1. **Load planning artifacts**
   ```
   Glob: bmad-output/**/*.md, bmad-output/**/*.yaml
   ```
   Priority order: `epics.md` → `prd.md` → `architecture.md` → individual story files.

2. **Extract epics and stories**
   - Parse all story IDs: format `{epic}.{story}.{slug}.story.md` (e.g., `2.1.stripe-integration.story.md`)
   - Derive epic ordering from the epic list in `epics.md` or `prd.md`

3. **Build dependency graph**
   - Read `**Blocked by:**` from each story's Dependency Maps section; normalize legacy slug-bearing IDs
   - Topological sort: stories with no unmet dependencies → wave 1; stories unblocked after wave 1 → wave 2; etc.

4. **Initialize sprint-status.yaml**
   ```bash
   bash ../bmad-sprint-planning/scripts/init-sprint-status.sh
   ```
   Then populate with sequenced data (see template).

5. **Sequence stories**
   ```bash
   bash ../bmad-sprint-planning/scripts/sequence-stories.sh
   ```

6. **Mirror lifecycle without downgrading later waves**
   - Read each story's explicit status header into the scheduling view.
   - Keep complete documents `ready-for-dev` in every wave.
   - Preserve `done` and `cancelled`; neither is wave-eligible.
   - Mark actual execution state only from user/dev-tool signals.

7. **Emit handoff summary** — list wave 1 stories by `owned_scope` for conflict-free parallel dispatch

---

## Workflow — Update

When a story moves to `done`:
1. Mirror its `done` status from the story header; retain all dependency declarations
2. Identify newly unblocked stories (dependencies now fully satisfied)
3. List the now-executable stories; document readiness and execution eligibility are separate
4. Re-evaluate parent epic status
5. Write updated `sprint-status.yaml`

---

## Parallel Set Assignment

Wave width (how many stories can run at once) is not a fixed number — it is the size of the dependency-free frontier at each topological level. There is no points budget or velocity ceiling.

```
Wave 1: all stories with no dependencies
Wave 2: all stories whose only dependencies are in wave 1
Wave N: all stories whose dependencies are fully in waves 1…(N-1)
```

Stories within a wave MUST have non-overlapping `owned_scope` to be safe for parallel dispatch. If two stories in the same wave share a file, split them into separate waves or document the conflict.

---

## Status Lifecycle (view, not metric)

```
backlog → ready-for-dev → in-progress → review → done
```

- This is a **view** of sequencing state, not a tracking instrument.
- Transitions are triggered by external signals (dev tool reports, user command).
- This skill never computes velocity, burndown, or completion rates from these statuses.

---

## Scale-Adaptive Track Guidance

| Track | Story count | Sprint-status behavior |
|-------|-------------|----------------------|
| Quick Flow | 1–15 | Single wave pass; minimal epic structure |
| BMAD Method | 10–50+ | Full wave assignment; epic grouping |
| Enterprise | 30+ | Multi-phase wave planning; dependency map documented in REFERENCE |

Reuse project.track from config.yaml. Ask only when it is missing or a requested scope change invalidates it.

---

## Subagent Strategy

Subagents, when the capability is available, are an important part of this
workflow. Use them as directed by this section.

If the current Codex runtime requires explicit user authorization for subagents,
ask once before launching any subagent and apply that answer to the whole
workflow run. If authorization is denied, or subagent tooling is unavailable,
execute the listed slices sequentially in the main context and keep the same
outputs.

**Pattern:** Parallel dependency analysis
**Use when:** 15+ stories across 3+ epics

| Agent | Task | Output |
|-------|------|--------|
| Agent 1 | Parse all story files, extract dependency declarations | `bmad-output/context/dependency-raw.yaml` |
| Agent 2 | Parse epic ordering from PRD/epics.md | `bmad-output/context/epic-order.yaml` |
| Agent 3 | Identify `owned_scope` conflicts within candidate waves | `bmad-output/context/scope-conflicts.md` |

Main context: merge outputs, run topological sort, write `sprint-status.yaml`.

### Example subagent prompt
```
Task: Extract dependencies from all story files
Context: Read all *.story.md files under bmad-output/stories/
Objective: For each story, output its id and its dependencies[] list
Output: Write YAML list to bmad-output/context/dependency-raw.yaml

Format:
- id: "2.1.stripe-integration"
  dependencies: ["1.3.user-auth"]
- id: "2.2.payment-webhook"
  dependencies: ["2.1.stripe-integration"]
```

---

## Scripts

### `init-sprint-status.sh`
Scaffolds `bmad-output/sprint-status.yaml` from the template if it does not exist.

```bash
bash ../bmad-sprint-planning/scripts/init-sprint-status.sh \
  [project-name] [output-dir]
```

### `sequence-stories.sh`
Requires Python 3.9+ and PyYAML (see repository requirements.txt); works with the default macOS shell. The helper validates the whole plan before replacing YAML. Comments in this generated scheduling view may be normalized, while unrelated data fields are retained.

Orders stories across epics by dependency, separates scope conflicts, then assigns
`parallel_set` integers. Story IDs break ties; they do not override explicit dependencies.

```bash
bash ../bmad-sprint-planning/scripts/sequence-stories.sh \
  [sprint-status-file]
```

---

## Template

`../bmad-sprint-planning/templates/sprint-status.template.yaml`

Fields: `epics[]`, `stories[]` (with `id`, `title`, `status`, `dependencies`, `parallel_set`,
`owned_scope`). The template contains **no** velocity, burndown, or points fields.

---

## Key Guidelines

1. **Load context first** — always read existing `sprint-status.yaml` before writing
2. **Use the available progress-tracking tool** to track multi-step sequencing workflows
3. **Respect owned_scope** — flag conflicts before assigning same-wave membership
4. **No metrics** — if a field resembles velocity, points, or burndown, remove it
5. **Handoff clearly** — conclude every Create/Update with the list of `ready-for-dev` stories and their `owned_scope`
6. **Decision log** — append sequencing decisions to `bmad-output/decision-log.md`

---

> ---
> Part of the **BMAD Planning & Orchestrator** plugin — a Codex harness for the **BMAD Method** by the **BMAD Code Organization** (https://github.com/bmad-code-org/BMAD-METHOD). Implements the spirit of `bmad-sprint-planning`. All methodology credit belongs to the BMAD Code Organization.
