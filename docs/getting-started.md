# Getting Started

This package installs BMAD planning as a Codex plugin bundle. It contributes
discoverable `$bmad-*` skills. It does not create a `/bmad` slash command.

## Install

From the repository root:

```sh
./install.sh
```

Equivalent manual install:

```sh
codex plugin marketplace add "$PWD"
codex plugin add codex-bmad-planning-orchestrator@codex-bmad-skills
```

After installation, start a new Codex thread or restart Codex so the plugin metadata is
loaded into the session.

## First Use

Use the skill names directly:

```text
Use $bmad-help to inspect my planning state and recommend the next BMAD step.
Use $bmad-init to start a BMAD planning workspace.
Use $bmad-migrate to scan and migrate an existing Claude BMAD project.
Use $bmad-prd to draft a PRD from my product brief.
```

You can also use `bmad:*` intent phrases in plain text:

```text
bmad:status
bmad:init
bmad:migrate
bmad:prd
```

These are routing phrases for Codex skill discovery. They are not slash commands.

## Recommended Flow

1. Run `$bmad-help` or say `bmad:status` to inspect current planning state.
2. If Claude BMAD artifacts already exist, run `$bmad-migrate` or say
   `bmad:migrate`.
3. If no workspace exists, run `$bmad-init` or say `bmad:init`.
4. Fill the first sections of `bmad-output/project-context.md`.
5. Continue with the next recommended planning skill.

For a new project:

- Quick Flow: `bmad:init` -> `bmad:tech-spec` -> `bmad:stories`
- BMad Method: `bmad:init` -> `bmad:product-brief` -> `bmad:prd` ->
  `bmad:architecture` -> `bmad:stories`
- Enterprise: same as BMad Method, with security and DevOps planning captured in
  architecture and handoff artifacts.

## Optional XMM Compatibility

The primary artifact folder is still `bmad-output/`. For users migrating from
XMM-style workflows, initialization can optionally create supplemental state files
under `bmad/`:

```sh
bash plugins/codex-bmad-planning-orchestrator/skills/bmad-init/scripts/init-project.sh \
  --name "My Project" \
  --track bmad-method \
  --output bmad-output \
  --compat-xmm
```

This creates `bmad/project.yaml`, `bmad/workflow-status.yaml`, and
`bmad/sprint-status.yaml`. Normal operation does not require these files.

## Claude BMAD Migration

For projects previously planned with
`git@github.com:aj-geddes/claude-code-bmad-skills.git` or older Claude BMAD
skills, start with a dry-run migration:

```text
bmad:migrate
```

The migration skill scans `bmad-output/`, `docs/`, `docs/stories/`, `bmad/`,
`.claude/`, and `.bmad-core/`. It writes nothing until you approve the `--apply`
step.

## Boundary

This package plans and orchestrates only. It does not write application code, run test
suites, lint, build, review implementation diffs, or deploy infrastructure.
