# Changelog

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
