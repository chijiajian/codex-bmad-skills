# Codex BMAD Skills

[![CI](https://github.com/chijiajian/codex-bmad-skills/actions/workflows/ci.yml/badge.svg)](https://github.com/chijiajian/codex-bmad-skills/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/chijiajian/codex-bmad-skills?sort=semver)](https://github.com/chijiajian/codex-bmad-skills/releases)
[![License](https://img.shields.io/github/license/chijiajian/codex-bmad-skills)](LICENSE)

**Codex BMAD Skills is a Codex-native port of BMAD Planning & Orchestrator:
a planning-only plugin that turns BMAD Method workflows into discoverable Codex
skills for product discovery, PRDs, architecture, UX, story sharding, parallel
planning, and implementation handoff.**

Use it when you want Codex to structure product and engineering planning work
without writing application code. The plugin produces durable BMAD artifacts,
keeps planning boundaries explicit, and prepares ready-for-dev stories or
handoff manifests for implementation tools.

## Why This Exists

- **Codex-native BMAD workflows:** BMAD planning stages are exposed as
  `$bmad-*` skills and `bmad:*` intent phrases.
- **Planning-only by design:** the plugin creates planning artifacts, not
  application code, builds, tests, deployments, or implementation reviews.
- **Ready handoff artifacts:** output includes PRDs, architecture, UX docs,
  epics, ready-for-dev stories, parallel wave plans, and handoff manifests.
- **Brownfield-friendly:** migration support helps move older Claude BMAD
  planning artifacts into the Codex BMAD layout.
- **Codex runtime guardrails:** subagent workflows include an ask-once
  authorization guardrail and a sequential fallback when subagents are denied or
  unavailable.

Latest release: **v1.0.1**. See [Release Notes](CHANGELOG.md).

## 60-Second Start

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

Then ask Codex:

```text
bmad:status
bmad:init
bmad:product-brief
bmad:prd
bmad:architecture
bmad:stories
bmad:parallel-plan
bmad:handoff
```

These are skill-discovery phrases, not slash commands. This package does not
create `/bmad`.

## Common Workflows

| Scenario | Start with | Continue with |
| --- | --- | --- |
| New project | `bmad:status` -> `bmad:init` | `bmad:product-brief` -> `bmad:prd` -> `bmad:architecture` -> `bmad:stories` |
| Small feature | `bmad:init` | `bmad:tech-spec` -> `bmad:stories` |
| Claude BMAD project | `bmad:migrate` -> `bmad:status` | Next recommended BMAD skill |
| Brownfield planning | `bmad:document-project` | `bmad:prd` or `bmad:tech-spec` |
| Parallel implementation prep | `bmad:sprint-plan` | `bmad:parallel-plan` -> `bmad:handoff` |

## Usage Details

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

See [Commands and intents](docs/commands.md) for the complete intent mapping,
and see [Skill Catalog](#skill-catalog) for every installed skill name you can
invoke directly.

## Documentation

- [Getting started](docs/getting-started.md)
- [Commands and intents](docs/commands.md)
- [Configuration](docs/configuration.md)
- [Codex subagent authorization audit](docs/subagent-authorization-audit.md)
- [Release notes](CHANGELOG.md)

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

## Repository Layout

This repository is structured like a Codex marketplace repo:

```text
codex-bmad-skills/
├── .github/workflows/ci.yml
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
