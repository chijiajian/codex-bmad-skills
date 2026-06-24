# XMM BMAD Compatibility Plan

This plan captures the practical improvements identified from comparing this repository with
`xmm/codex-bmad-skills`.

The goal is to improve discoverability and workflow compatibility without changing this package's
planning-only boundary.

## Current Position

This repository packages BMAD planning as a Codex plugin marketplace bundle with `$bmad-*` skills.
It focuses on planning artifacts under `bmad-output/` and stops at ready-for-dev stories, parallel
planning, readiness checks, and handoff manifests.

The `xmm/codex-bmad-skills` project is a skill pack that exposes `bmad:*` intent phrases, initializes
project state under `bmad/*.yaml`, and includes developer and review flows. It is closer to an
end-to-end BMAD operating workspace, while this repository is intentionally planning-only.

## Objectives

- Make common `bmad:*` intent phrases discoverable by Codex users.
- Add usage documentation that explains the difference between Codex skills, plugin installation,
  and non-existent slash commands.
- Optionally support a lightweight `bmad/workflow-status.yaml` compatibility layer for users coming
  from the XMM workflow.
- Preserve the planning-only scope: no application code generation, test execution, implementation
  review, or deployment behavior.

## Non-Goals

- Do not add real slash commands unless Codex plugin manifests gain validated command support.
- Do not import developer or code-review workflows into this package.
- Do not move the primary artifact model away from `bmad-output/`.
- Do not replace existing `$bmad-*` skills with `bmad:*` names; treat `bmad:*` as user-facing intent
  language only.

## Phase 1: Intent Alias Compatibility

Add `bmad:*` phrases to relevant skill descriptions and usage guidance so Codex can route common
requests more naturally.

Suggested mappings:

| Intent phrase | Existing skill |
| --- | --- |
| `bmad:init` | `bmad-init` |
| `bmad:help`, `bmad:status`, `bmad:next` | `bmad-help` |
| `bmad:brainstorm` | `bmad-brainstorm` |
| `bmad:research` | `bmad-research` |
| `bmad:product-brief`, `bmad:brief` | `bmad-product-brief` |
| `bmad:spec` | `bmad-spec` |
| `bmad:prd` | `bmad-prd` |
| `bmad:ux` | `bmad-ux` |
| `bmad:architecture`, `bmad:arch` | `bmad-architecture` |
| `bmad:stories`, `bmad:story-draft` | `bmad-epics-and-stories` |
| `bmad:sprint-plan` | `bmad-sprint-planning` |
| `bmad:parallel-plan` | `bmad-parallel-plan` |
| `bmad:handoff` | `bmad-handoff` |
| `bmad:correct-course` | `bmad-correct-course` |
| `bmad:investigate` | `bmad-investigate` |
| `bmad:document-project` | `bmad-document-project` |

Acceptance criteria:

- All updated skill frontmatter remains valid.
- Descriptions stay concise enough for Codex skill discovery.
- `./scripts/validate.sh` passes without warnings or errors.
- README includes at least one `bmad:*` example and explains that these are intent phrases, not slash
  commands.

## Phase 2: Usage Documentation

Add focused user documentation for installation and day-to-day operation.

Proposed files:

- `docs/getting-started.md`: first-run flow, plugin installation, restart/new-thread requirement, and
  the recommended first commands.
- `docs/commands.md`: `$bmad-*` skill names, matching `bmad:*` intent phrases, and expected outputs.
- `docs/configuration.md`: artifact locations, optional compatibility settings, and planning-only
  boundaries.

Acceptance criteria:

- README links to the new docs.
- The docs explicitly state that `/bmad` is not created by this package.
- The docs explain when to use `$bmad-help`, `$bmad-init`, and the main planning skills.
- The docs keep implementation and review workflows out of scope.

## Phase 3: Workflow Status Compatibility

Add an optional compatibility layer for users who expect XMM-style status files under `bmad/`.

Recommended behavior:

- Keep `bmad-output/` as the primary artifact location.
- If `bmad/workflow-status.yaml` exists, read it as supplemental context.
- If compatibility mode is enabled during initialization, create:
  - `bmad/project.yaml`
  - `bmad/workflow-status.yaml`
  - `bmad/sprint-status.yaml`
- Do not require the compatibility files for normal operation.

Acceptance criteria:

- Existing users can keep using `bmad-output/` only.
- `bmad-help` can summarize both native planning state and optional compatibility state.
- Initialization docs describe the compatibility mode clearly.
- Validators reject malformed compatibility YAML if the repository ships templates for it.

## Phase 4: Language Guardrails

Add guidance for multilingual use so Codex can communicate in the user's language while keeping
artifacts predictable.

Recommended behavior:

- Conversational responses should follow the user's language.
- Artifact language should be explicit in the planning brief or initialization context.
- If artifact language is not specified, ask once or default to the language of the source material.
- Generated filenames and machine-readable YAML keys should remain stable and English.

Acceptance criteria:

- The rule is documented in `docs/configuration.md`.
- Relevant planning skills mention the language rule only where it changes artifact behavior.
- Validators are unaffected unless new templates are added.

## Phase 5: Validation and Release

Run the existing validation suite after each phase and before release.

Required checks:

```sh
./scripts/validate.sh
find . -name '*.sh' -print0 | xargs -0 -n1 bash -n
find . -name '*.json' -print0 | xargs -0 -n1 python3 -m json.tool >/dev/null
ruby -e 'require "yaml"; Dir["plugins/codex-bmad-planning-orchestrator/skills/*/agents/openai.yaml"].each { |f| YAML.load_file(f) }'
find . -name '*.py' -print0 | xargs -0 env PYTHONPYCACHEPREFIX=/private/tmp/codex-bmad-pycache python3 -m py_compile
git diff --check
```

Release criteria:

- Existing plugin install flow still works with `./install.sh --reinstall`.
- `codex plugin list` shows the plugin installed and enabled after reinstall.
- A new Codex thread can discover the updated `$bmad-*` skills.
- Documentation sets the correct expectation that there is no `/bmad` command.

## Recommended Sequence

1. Implement Phase 1 and Phase 2 together because alias discovery and documentation reinforce each
   other.
2. Ship Phase 3 only after confirming the expected compatibility file schema.
3. Add Phase 4 as documentation first, then update individual skills only where necessary.
4. Keep developer and code-review capabilities out of this repository unless the scope is explicitly
   changed from planning-only to end-to-end BMAD execution.
