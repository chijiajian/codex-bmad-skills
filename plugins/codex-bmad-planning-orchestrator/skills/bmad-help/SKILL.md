---
name: bmad-help
description: |
  Routes BMAD planning sessions by scanning bmad-output state plus optional
  bmad/workflow-status.yaml compatibility state, and Claude BMAD migration hints,
  then recommending the next single BMAD skill. Use when the user asks "what's
  next", "where am I", "what's my status", "continue", "resume planning",
  "which skill should I run", "what BMAD step is next", or types "$bmad-help",
  "bmad:help", "bmad:status", "bmad:next", "bmad status", or "status". Routes
  only; never writes planning documents.
---

# BMAD Help — Orchestration Spine

## Codex Resource Paths

Resolve bundled resources relative to this skill directory. When running a bundled script, use the absolute path to that script from the installed plugin location; relative examples are shown from this `SKILL.md` directory. Shared BMAD helper scripts live under `../../scripts/`, and shared references live under `../../references/`.

A lean router. It answers one question: **what do I run next?** It detects planning
state, infers the phase and track, and points to the next skill. It is auto-invoked to
orient a session and replaces a heavyweight master/orchestrator agent.

**This skill produces NO planning documents.** It reads state and recommends. All
artifacts are produced by the specialized planning skills it routes to.

## Phase Map

```
Analysis  ──►  Planning  ──►  Solutioning  ──►  Implementation-handoff
(optional)     (required)     (conditional)     (required: ready-for-dev stories)
```

| Phase | Artifact(s) | Skill |
|-------|-------------|-------|
| Analysis (optional) | product-brief, research, brainstorm | `bmad-product-brief` / `bmad-research` / `bmad-brainstorm` |
| Planning (required) | prd.md OR tech-spec.md, epics.md | `bmad-prd` / `bmad-tech-spec` / `bmad-epics-and-stories` |
| Planning — UX (only if UI) | ux-design.md | `bmad-ux` |
| Solutioning (track-dependent) | architecture.md | `bmad-architecture` |
| Implementation-handoff (required) | {epic}.{story}.{slug}.story.md (ready-for-dev) | `bmad-epics-and-stories` → `bmad-sprint-planning` |

Threaded across every phase: **project-context.md** (the project "constitution") and
**decision-log.md** (decisions carried between workflows). If these are missing, the
first recommendation is always to establish them.

When `bmad/workflow-status.yaml` exists, treat it as optional compatibility state
for users coming from XMM-style workflows. Native `bmad-output/` artifacts remain
authoritative; compatibility state can fill gaps such as an otherwise missing track.

When no native workspace exists but `.claude/`, `.bmad-core/`, `docs/prd.md`,
`docs/architecture.md`, `docs/stories/`, or a non-target `bmad-output/` is detected,
recommend `bmad-migrate` before `bmad-init`.

> Implementation itself (writing code, running tests) is OUT OF SCOPE. The last artifact
> this plugin produces is a ready-for-dev story file or handoff manifest, passed to an
> external dev tool.

## Tracks (scale-adaptive — never numbered levels)

A heuristic may suggest a track from story count; **the user confirms**.

| Track | Scope | Required planning | Optional |
|-------|-------|-------------------|----------|
| **Quick Flow** | 1–15 stories | tech-spec + stories | analysis, ux |
| **BMad Method** | 10–50+ stories | prd + architecture + epics + stories | analysis; ux (if UI) |
| **Enterprise** | 30+ stories | prd + architecture + security + devops + epics + stories | analysis |

Per-track required vs optional steps in detail: see
[REFERENCE.md](../bmad-help/REFERENCE.md).

## How it works

1. **Detect state.** Run the detector to list which artifacts exist and the inferred
   phase:
   ```bash
   bash ../bmad-help/scripts/detect-state.sh [output-folder]
   ```
   Default output folder is `bmad-output/`. It prints a checklist of artifacts (present
   or missing), the detected track (from decision-log first, then optional
   `bmad/workflow-status.yaml`), the inferred phase, and any compatibility files.

2. **Recommend next.** Map the detected state to the next skill:
   ```bash
   bash ../bmad-help/scripts/recommend-next.sh [output-folder]
   ```
   It prints the single next skill to run, plus why, plus any skipped optional phases.

3. **Present** the recommendation to the user in plain prose. Offer to invoke the
   recommended skill. Do not auto-run planning skills without confirmation when the
   track is still ambiguous.

If `project-context.md` does not exist yet, treat the project as un-initialized: the
recommendation is to start with `bmad-init` (or `bmad-product-brief` if the user wants the
optional Analysis phase first) to establish project context and choose a track.

## Routing logic (summary)

Evaluate in order; recommend the first unmet step for the active track.

1. No `project-context.md` → establish project context (run `bmad-init`, or
   `bmad-product-brief` if the user opts into Analysis). Confirm the track.
   If Claude BMAD artifacts are detected, recommend `bmad-migrate` first.
2. No `prd.md` and no `tech-spec.md` →
   - Quick Flow → `bmad-tech-spec` (tech-spec).
   - BMad Method / Enterprise → `bmad-prd` (PRD).
3. Project has a UI and no `ux-design.md` (BMad/Enterprise) → `bmad-ux`.
4. Track needs architecture and no `architecture.md` (BMad/Enterprise) →
   `bmad-architecture`. (Quick Flow skips architecture.)
5. Enterprise and no security/devops planning → `bmad-architecture` (security + devops
   sections / handoff).
6. No `epics.md` (BMad/Enterprise) → `bmad-epics-and-stories` (epic breakdown).
7. No story files under `stories/` → `bmad-epics-and-stories` (create ready-for-dev stories).
8. Stories exist but some are still `backlog`/not `ready-for-dev` → `bmad-epics-and-stories`
   (finish compiling story context objects); then `bmad-sprint-planning` to sequence waves.
9. All required artifacts present and stories are `ready-for-dev` → **handoff
   complete.** Recommend handing the stories to the external dev tool. Nothing left to
   plan.

**Skipping rules:** Analysis is always optional — never block on it. UX is recommended
only when the project has a UI. Architecture is skipped for Quick Flow.

Full decision table with edge cases: [REFERENCE.md](../bmad-help/REFERENCE.md).

## Notes for Codex

- This is the entry point. Always detect state before recommending.
- Recommend exactly ONE next skill. Keep it actionable.
- Never produce planning documents here — route to the owning skill.
- Never recommend running tests, builds, linters, or writing code — that is out of
  scope for this plugin entirely.
- Respect locked sections: Acceptance Criteria, Dev Notes, and Testing in story files
  are owned by planning skills and must not be edited downstream.
- Use `decision-log.md` to read the confirmed track; if absent, ask the user to confirm
  the track before recommending track-specific steps.

> ---
> Part of the **BMAD Planning & Orchestrator** plugin — a Codex harness for the **BMAD Method** by the **BMAD Code Organization** (https://github.com/bmad-code-org/BMAD-METHOD). Implements the spirit of `bmad-help`. All methodology credit belongs to the BMAD Code Organization.
