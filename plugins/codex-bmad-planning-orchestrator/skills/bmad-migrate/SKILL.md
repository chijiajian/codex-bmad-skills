---
name: bmad-migrate
description: |
  Discovers and migrates existing BMAD planning artifacts from Claude Code BMAD
  plugin or older Claude BMAD skills into this Codex BMAD workspace. Use when the
  user says "$bmad-migrate", "bmad:migrate", "migrate from Claude BMAD",
  "import Claude BMAD artifacts", "convert my Claude Code BMAD project",
  "adopt existing bmad-output", "scan old BMAD docs", or asks how to move from
  git@github.com:aj-geddes/claude-code-bmad-skills.git. Planning artifacts only;
  never writes application code, runs tests, lints, reviews diffs, or deploys.
---

# BMAD Migrate — Claude BMAD Importer

## Codex Resource Paths

Resolve bundled resources relative to this skill directory. When running a bundled
script, use the absolute path to that script from the installed plugin location;
relative examples are shown from this `SKILL.md` directory. Shared BMAD helper
scripts live under `../../scripts/`, and shared references live under
`../../references/`.

Import planning state from Claude BMAD installations into the Codex BMAD Planning &
Orchestrator layout. This is a **planning artifact migration** skill. It never
changes application source files and never executes build, test, lint, coverage, or
deployment commands.

## What It Supports

- Claude Code BMAD plugin projects from
  `git@github.com:aj-geddes/claude-code-bmad-skills.git`, which usually already use
  `bmad-output/`.
- Older Claude BMAD skill projects that left planning files in `docs/`,
  `docs/stories/`, `bmad/`, or `.claude/` support folders.
- Existing `bmad-output/` workspaces that should be adopted rather than rewritten.

## What It Produces

In dry-run mode, it prints a Markdown migration report to stdout and writes nothing.

With `--apply`, it creates or updates only planning artifacts:

```
bmad-output/
├── config.yaml
├── migration-report.md
├── project-context.md
├── decision-log.md
├── prd.md / tech-spec.md / architecture.md / epics.md / ...
└── stories/*.story.md
```

It may also preserve supplemental compatibility files under `bmad/` when found.

## Workflow

1. **Start with discovery.** Ask for the source project path if the user has not
   provided one. Default to the current workspace (`.`). Run:

   ```bash
   python3 "../bmad-migrate/scripts/migrate-claude-bmad.py" \
     --source "." \
     --output "bmad-output"
   ```

   This is dry-run mode. It must not mutate files.

2. **Explain the migration report.** Identify:
   - Detected source family: Claude plugin `bmad-output/`, old `docs/` artifacts,
     optional `bmad/*.yaml`, or `.claude/` installation remnants.
   - Files that can be adopted in place.
   - Files that can be copied into `bmad-output/`.
   - Missing required BMAD state (`config.yaml`, `project-context.md`,
     `decision-log.md`).
   - Conflicts where target files already exist.
   - Removed capabilities that cannot migrate: developer skill, `/dev-story`, test,
     lint, coverage, implementation review, and deployment workflows.

3. **Ask before applying.** If the report is acceptable, run the same script with
   `--apply`:

   ```bash
   python3 "../bmad-migrate/scripts/migrate-claude-bmad.py" \
     --source "." \
     --output "bmad-output" \
     --apply
   ```

   The script creates missing directories and copies missing planning files. It
   never overwrites existing files unless the user explicitly asks for overwrite and
   you have inspected the conflict.

4. **Validate the migrated workspace.**

   ```bash
   bash "../bmad-init/scripts/init-project.sh" --validate --output "bmad-output"
   bash "../bmad-help/scripts/detect-state.sh" "bmad-output"
   bash "../bmad-help/scripts/recommend-next.sh" "bmad-output"
   ```

5. **Hand off to the router.** Recommend `bmad:status` / `$bmad-help` next so the
   user can continue from the migrated planning state.

## Artifact Mapping

| Claude / old BMAD location | Codex BMAD location |
| --- | --- |
| `bmad-output/config.yaml` | `bmad-output/config.yaml` |
| `bmad-output/project-context.md` | `bmad-output/project-context.md` |
| `bmad-output/decision-log.md` | `bmad-output/decision-log.md` |
| `docs/prd.md` or `bmad-output/prd.md` | `bmad-output/prd.md` |
| `docs/tech-spec.md` or `bmad-output/tech-spec.md` | `bmad-output/tech-spec.md` |
| `docs/architecture.md` or `bmad-output/architecture.md` | `bmad-output/architecture.md` |
| `docs/epics.md` or `bmad-output/epics.md` | `bmad-output/epics.md` |
| `docs/stories/*.story.md` | `bmad-output/stories/*.story.md` |
| `bmad/project.yaml` | `bmad/project.yaml` (supplemental) |
| `bmad/workflow-status.yaml` | `bmad/workflow-status.yaml` (supplemental) |
| `bmad/sprint-status.yaml` | `bmad/sprint-status.yaml` (supplemental) |

## Notes for LLMs

- Prefer dry-run first; do not apply until the user agrees.
- Treat `bmad-output/` from the Claude plugin as mostly compatible. If source and
  target are the same directory, adopt in place and write only a migration report
  when applying.
- If required context files are missing, generate minimal migration stubs only in
  `--apply` mode and clearly mark them for user review.
- Preserve user-authored planning documents. Do not rewrite content just to match
  tone or template.
- Use `bmad-help` after migration to determine the next planning step.

> ---
> Part of the **BMAD Planning & Orchestrator** plugin — a Codex harness for the **BMAD Method** by the **BMAD Code Organization** (https://github.com/bmad-code-org/BMAD-METHOD). Implements a Codex migration path for Claude BMAD planning artifacts, including projects created with `aj-geddes/claude-code-bmad-skills`. All methodology credit belongs to the BMAD Code Organization.
