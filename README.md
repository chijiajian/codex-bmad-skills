# Codex BMAD Skills

A Codex port of **BMAD Planning & Orchestrator**: a planning-only harness for the BMAD Method. It helps Codex create product briefs, SPECs, PRDs, UX docs, architecture, epics, ready-for-dev stories, conflict-free parallel wave plans, and handoff manifests.

This repository is structured like a Codex marketplace repo:

```text
codex-bmad-skills/
├── .agents/plugins/marketplace.json
├── plugins/codex-bmad-planning-orchestrator/
│   ├── .codex-plugin/plugin.json
│   ├── skills/
│   ├── scripts/
│   └── references/
├── examples/
├── install.sh
├── uninstall.sh
└── scripts/
```

## Install

Clone the GitHub repository, then install the Codex plugin bundle:

```sh
git clone git@github.com:chijiajian/codex-bmad-skills.git
cd codex-bmad-skills
./install.sh
```

Equivalent manual commands:

```sh
codex plugin marketplace add "$PWD"
codex plugin add codex-bmad-planning-orchestrator@codex-bmad-skills
```

After installation, start a new Codex session or restart Codex so the plugin
metadata is loaded.

## Usage

Use any skill from the catalog by name. These are common examples, not the
complete list:

```text
Use $bmad-help to inspect my planning state.
Use $bmad-init to start a BMAD planning workspace.
Use $bmad-migrate to scan an existing Claude BMAD project.
Use $bmad-parallel-plan to build a conflict-free wave plan.
Use $bmad-architecture to draft the system architecture.
Use $bmad-handoff to emit a handoff manifest for implementation tools.
```

Or use `bmad:*` intent phrases in normal chat. These cover the main BMAD
workflow stages:

```text
bmad:status
bmad:init
bmad:migrate
bmad:product-brief
bmad:prd
bmad:architecture
bmad:stories
bmad:sprint-plan
bmad:parallel-plan
bmad:handoff
```

These are skill-discovery phrases, not slash commands. This package does not
create `/bmad`. See [Commands and intents](docs/commands.md) for the complete
intent mapping, and see [Skill Catalog](#skill-catalog) for every installed skill
name you can invoke directly.

Recommended entry points:

- New project: `bmad:status` -> `bmad:init`
- Claude BMAD project: `bmad:migrate` -> `bmad:status`
- Existing BMAD workspace: `bmad:status`
- Ready-for-dev story backlog: `bmad:sprint-plan` -> `bmad:parallel-plan` -> `bmad:handoff`

## Documentation

- [Getting started](docs/getting-started.md)
- [Commands and intents](docs/commands.md)
- [Configuration](docs/configuration.md)

## Examples

- [Parallelization plan example](examples/parallelization-plan.example.md)

## Skills-only install

If you do not want to install the plugin marketplace entry, install just the skill folders into Codex's skill directory:

```sh
./scripts/install-skills.sh
```

This copies the BMAD skills to `${CODEX_HOME:-$HOME/.codex}/skills` and installs shared BMAD scripts/references under `_bmad-shared`.

Remove the skills-only install with:

```sh
./scripts/uninstall-skills.sh --yes
```

## Validate

```sh
./scripts/validate.sh
```

The validator checks the Codex plugin manifest, all skill frontmatter, and BMAD's planning-only scope rules.

## Roadmap

- [XMM BMAD compatibility plan](docs/xmm-compatibility-plan.md)

## Skill Catalog

- `bmad-help` — next-step router
- `bmad-init` — initialize a BMAD planning workspace
- `bmad-migrate` — migrate Claude BMAD planning artifacts into Codex BMAD layout
- `bmad-brainstorm`, `bmad-research`, `bmad-product-brief`, `bmad-prfaq`, `bmad-spec`
- `bmad-prd`, `bmad-tech-spec`
- `bmad-ux`, `bmad-architecture`, `bmad-epics-and-stories`, `bmad-readiness-check`
- `bmad-sprint-planning`, `bmad-parallel-plan`, `bmad-handoff`
- `bmad-correct-course`, `bmad-investigate`, `bmad-document-project`, `bmad-builder`

## Scope

This package plans and orchestrates only. It does not write application code, run test suites, lint, build, check coverage, or review implemented diffs. The final artifacts are ready-for-dev story files and handoff manifests for external dev tools.

## Attribution

The BMAD Method is created and maintained by the BMAD Code Organization. This
repository is an independent Codex integration and does not imply endorsement.
This package also adapts ideas and artifact shapes from AJ Geddes'
MIT-licensed Claude Code BMAD plugin. See [ATTRIBUTION.md](ATTRIBUTION.md).
