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
├── install.sh
├── uninstall.sh
└── scripts/
```

## Install

Recommended install, as a Codex plugin bundle:

```sh
./install.sh
```

Equivalent manual commands:

```sh
codex plugin marketplace add "$PWD"
codex plugin add codex-bmad-planning-orchestrator@codex-bmad-skills
```

After installation, start Codex and use the skills by name, for example:

```text
Use $bmad-help to inspect my planning state and recommend the next BMAD step.
Use $bmad-init to start a BMAD planning workspace.
Use $bmad-prd to draft a PRD from my product brief.
```

You can also use `bmad:*` intent phrases in normal chat, such as `bmad:status`,
`bmad:init`, or `bmad:prd`. These are skill-discovery phrases, not slash commands.
This package does not create `/bmad`.

## Documentation

- [Getting started](docs/getting-started.md)
- [Commands and intents](docs/commands.md)
- [Configuration](docs/configuration.md)

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
- `bmad-brainstorm`, `bmad-research`, `bmad-product-brief`, `bmad-prfaq`, `bmad-spec`
- `bmad-prd`, `bmad-tech-spec`
- `bmad-ux`, `bmad-architecture`, `bmad-epics-and-stories`, `bmad-readiness-check`
- `bmad-sprint-planning`, `bmad-parallel-plan`, `bmad-handoff`
- `bmad-correct-course`, `bmad-investigate`, `bmad-document-project`, `bmad-builder`

## Scope

This package plans and orchestrates only. It does not write application code, run test suites, lint, build, check coverage, or review implemented diffs. The final artifacts are ready-for-dev story files and handoff manifests for external dev tools.

## Attribution

The BMAD Method is created and maintained by the BMAD Code Organization. This repository is an independent Codex integration and does not imply endorsement. See [ATTRIBUTION.md](ATTRIBUTION.md).
