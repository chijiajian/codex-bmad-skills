# Changelog

## [1.0.1] - 2026-06-25

Codex subagent authorization guardrail release.

### Added

- Added an ask-once Codex subagent authorization guardrail to every shipped
  skill with a `Subagent Strategy` section.
- Added `docs/subagent-authorization-audit.md` to document how this repository
  addresses the ambiguity raised in `bmad-code-org/BMAD-METHOD#2451`.

### Changed

- Updated `bmad-builder` templates and scaffolding so newly generated planning
  skills inherit the same subagent authorization guardrail.
- Updated BMAD skill validation to warn when a skill has a `Subagent` section
  but lacks explicit authorization guidance or an unavailable-tooling fallback.

### Validation

- `./scripts/validate.sh`
- `git diff --check`

## [1.0.0] - 2026-06-24

First stable GitHub release.

### Added

- Documented the GitHub install flow for the Codex plugin bundle.
- Added attribution and examples for the independent Codex integration.
- Added GitHub Actions CI for repository validation.

### Changed

- Promoted the plugin repository to a stable `v1.0.0` release baseline.

## [0.5.0] - 2026-06-20

Initial Codex port of BMAD Planning & Orchestrator.

### Added
- Codex marketplace layout under `.agents/plugins/marketplace.json`.
- Codex plugin bundle under `plugins/codex-bmad-planning-orchestrator/`.
- 20 BMAD planning/orchestration skills with `agents/openai.yaml` metadata.
- Plugin install/uninstall scripts.
- Skills-only install/uninstall scripts.
- Validation script for plugin and skill manifests.

### Changed
- Converted Claude plugin-specific paths and slash commands to Codex-compatible `$bmad-*` skill usage.
- Removed Claude-specific `allowed-tools` frontmatter from skill manifests.
