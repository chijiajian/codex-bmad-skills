# BMAD Help Reference

The shared [planning contract](../../references/planning-contract.md) is the source of
truth for artifact names and lifecycle ownership. The router's order is documented in
SKILL.md and implemented in the shared planning_state.py helper.

## Compatibility

- Native config.yaml takes precedence over decision-log.md and bmad/*.yaml.
- Legacy decision logs may provide a Track: entry when native config has no track.
- bmad/workflow-status.yaml and bmad/project.yaml are optional migration fallbacks.
- project.has_ui records a boolean; absence is an open decision. Existing complete UX
  artifacts imply UI work. A false value avoids recurring UX recommendations for CLI/API work.
- Both native story headers (**Status:** ready-for-dev) and legacy status: / ## Status
  forms are accepted. HTML comments and fenced examples do not supply lifecycle state.
- A legacy ux-design.md is accepted only when neither DESIGN.md nor EXPERIENCE.md
  exists; a partially migrated pair must be completed.
- Current readiness and scheduling are checked by modification time of their inputs.
  This is a conservative freshness hint. Agents still review semantic consistency.

## Migration discovery

When native project-context.md is missing, .claude/, .bmad-core/, docs/prd.md,
docs/architecture.md, docs/epics.md, docs/stories/, or a non-target bmad-output/
may indicate a migration source. Inspect it before initializing. Do not require these
compatibility paths for new projects.

## Tracks

Quick Flow uses tech-spec + applicable UX + readiness + stories + scheduling.
BMad Method adds a separate PRD, architecture and epic map. Enterprise adds security
and operations planning inside those artifacts. Analysis and the final JSON manifest
are optional; story readiness and dependency-safe scheduling are separate checks.
