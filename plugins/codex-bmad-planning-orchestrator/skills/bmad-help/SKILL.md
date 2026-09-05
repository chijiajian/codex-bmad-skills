---
name: bmad-help
description: |
  Inspect an active BMAD planning workspace and recommend its next planning skill.
  Use when the user asks for BMAD status, the next BMAD step, $bmad-help,
  bmad:help, bmad:status, or bmad:next. Resolve generic "continue" or "status"
  requests here only when the current task is already BMAD planning.
---

# BMAD Help — Planning Router

## Codex Resource Paths

Resolve bundled resources relative to this skill directory and execute scripts by
absolute path. Shared helpers live in `../../scripts/` and references in
`../../references/`.

This skill reads state and recommends one next step. It produces no planning documents
and does not execute application code or development checks.

## Shared contract

Read [planning-contract.md](../../references/planning-contract.md) for artifact names,
status ownership, config precedence, and reuse of existing authorization.

## Workflow

1. Inspect the current workspace:
   ```sh
   bash ../bmad-help/scripts/detect-state.sh [output-folder]
   ```
2. Obtain the recommendation:
   ```sh
   bash ../bmad-help/scripts/recommend-next.sh [output-folder]
   ```
3. Present the next skill and the evidence for it. If the user already authorized
   continuing the planning workflow, proceed within that scope. Ask only for a missing
   decision that affects the next step; record track/UI decisions in config.yaml.

The scripts use an explicit output argument first, otherwise the output_folder pointer
in bmad-output/config.yaml, otherwise bmad-output. project.track is authoritative;
legacy decision-log and optional bmad/*.yaml values are fallbacks only.

## Routing order

1. Missing project context: migrate existing Claude/BMAD artifacts when detected,
   otherwise initialize. Analysis (brief, research, brainstorming) remains optional.
2. Missing track: establish Quick Flow, BMad Method, or Enterprise once.
3. Requirements: tech-spec.md for Quick Flow; prd.md for BMad Method/Enterprise.
4. UX: record project.has_ui once. If true, require DESIGN.md + EXPERIENCE.md;
   accept a legacy ux-design.md when neither new file exists. If false, skip UX.
5. Architecture: required for BMad Method/Enterprise. Quick Flow uses its tech-spec.
6. Readiness: inspect a current readiness-report*.md with a PASS or CONCERNS verdict.
   A stale/unknown/FAIL verdict returns to bmad-readiness-check. Carry concerns forward.
7. Epics/stories: compile active story documents. Cancelled stories do not block progress.
8. Scheduling: create or refresh sprint-status.yaml from current stories.
9. Handoff: offer bmad-handoff to generate the optional manifest. Report handoff complete
   only when the current manifest validates and matches the ready stories. If the user
   chooses direct story handoff, describe it as planning prepared rather than claiming
   a manifest exists.

Story lifecycle is read from the explicit header, never from lifecycle examples or
words in the body. Once execution has started, report that state; keep planning changes
within the user's requested scope.

See [REFERENCE.md](REFERENCE.md) for compatibility details.

> ---
> Part of the **BMAD Planning & Orchestrator** plugin — a Codex harness for the **BMAD Method** by the **BMAD Code Organization** (https://github.com/bmad-code-org/BMAD-METHOD). Implements the spirit of `bmad-help`. All methodology credit belongs to the BMAD Code Organization.
