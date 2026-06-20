# Configuration

The primary BMAD workspace is `bmad-output/`. Other planning skills read
`bmad-output/config.yaml` to find paths, track, and language preferences.

## Primary Files

```text
bmad-output/
├── config.yaml
├── decision-log.md
├── project-context.md
└── stories/
```

`config.yaml` is the native source of truth for this package. Keep `paths.output_folder`,
`paths.stories_folder`, `paths.decision_log`, and `paths.project_context` current when
you move artifacts.

## Tracks

The `project.track` value must be one of:

- `quick-flow`: small planning scope, tech-spec first.
- `bmad-method`: PRD, architecture, epics, and stories.
- `enterprise`: BMad Method plus security and DevOps planning artifacts.

Tracks are planning scopes, not delivery estimates. This package does not use story
points, velocity, burndown, or coverage metrics.

## Language Rules

Codex should communicate in the user's language during conversation.

Artifact language is controlled separately:

- If `languages.document_output` is set in `config.yaml`, use that language for
  generated planning artifacts.
- If no artifact language is specified, ask once or default to the language of the
  source material.
- Keep filenames, YAML keys, JSON keys, and machine-readable status values stable and
  English.

Example:

```yaml
languages:
  communication: "Chinese"
  document_output: "English"
```

## Optional XMM Compatibility

Users migrating from XMM-style BMAD workflows may expect state under `bmad/`. This
repository supports that as supplemental state only.

When initialized with `--compat-xmm`, the init script creates:

```text
bmad/
├── project.yaml
├── workflow-status.yaml
└── sprint-status.yaml
```

`bmad-output/` remains the primary artifact folder. `bmad-help` reads
`bmad/workflow-status.yaml` as supplemental context when it exists, but normal operation
does not require it.

## Scope Boundary

This repository stays planning-only. It may read existing code for brownfield planning,
but it must not:

- Write application code.
- Run test suites, linters, builds, or coverage tools.
- Review implemented diffs.
- Deploy infrastructure.
- Replace an external implementation agent or development workflow.
