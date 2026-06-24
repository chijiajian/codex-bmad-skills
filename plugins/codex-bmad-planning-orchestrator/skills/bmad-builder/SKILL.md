---
name: bmad-builder
description: |
  Scaffolds and validates custom planning/orchestration skills inside the BMAD
  Planning & Orchestrator plugin. Use for "$bmad-builder", "bmad:builder", or
  when the user says "create a skill", "scaffold a skill", "build a new planning
  skill", "add a skill to the orchestrator", "extend BMAD planning", "validate
  this skill", "check this skill for scope violations", or "bmad-builder".
  Supports Create, Validate, and Scaffold. Plans and scaffolds only; never writes
  application code, runs tests, lints, or builds.
---

# BMAD Builder

## Codex Resource Paths

Resolve bundled resources relative to this skill directory. When running a bundled script, use the absolute path to that script from the installed plugin location; relative examples are shown from this `SKILL.md` directory. Shared BMAD helper scripts live under `../../scripts/`, and shared references live under `../../references/`.

**Function:** Scaffold and validate custom planning/orchestration skills for the BMAD Planning & Orchestrator plugin. Produces compliant SKILL.md files, shell scripts, and templates — pre-wired to this plugin's path conventions — and runs scope-violation checks to keep new skills inside the PLAN/ORCHESTRATE boundary.

## Scope (PLAN, never build)

This skill produces planning artifacts and skill skeleton files. It does NOT write application code, run tests, lint, check coverage, or execute builds. If a skill being designed is tempted to "implement", "fix the code", "run the suite", or "review the diff" — that is a scope violation. Plan and hand off instead.

## Three intents

Always clarify which intent applies before starting.

### Create — new planning skill from scratch

1. Gather requirements (use TodoWrite to track):
   - Skill name (lowercase-hyphen, prefixed `bmad-`; e.g. `bmad-example`)
   - What planning/orchestration problem it solves
   - Trigger phrases users will say
   - Which BMAD track(s) it applies to (Quick Flow / BMad Method / Enterprise)
   - Upstream BMAD counterpart (e.g. `bmad-risk-assessment`)

2. Run the scaffold script to create the directory:
   ```bash
   bash ../bmad-builder/scripts/scaffold-skill.sh <skill-name>
   ```
   This creates `skills/<skill-name>/` with `scripts/` and `templates/` subdirectories and a starter SKILL.md.

3. Fill the SKILL.md using the skill template:
   - Reference: `../bmad-builder/templates/skill.template.md`
   - Keep body under 5K tokens; push long reference detail to a sibling `REFERENCE.md` in the new skill's own folder
   - Resolve bundled paths relative to the installed skill directory
   - Artifacts go to `bmad-output/` (honor user-configured folder)
   - End with the mandatory attribution footer (see template)

4. Validate the new skill:
   ```bash
   bash ../bmad-builder/scripts/validate-skill.sh \
     ../<skill-name>/SKILL.md
   ```
   Fix all errors; review all warnings before declaring done.

### Validate — check an existing SKILL.md

Run the validator directly against any SKILL.md path:
```bash
bash ../bmad-builder/scripts/validate-skill.sh <path-to-SKILL.md>
```

The validator checks:
- `name` field present and lowercase-hyphen
- `description` field present with trigger phrases
- `agents/openai.yaml` present for Codex UI metadata (warns if missing)
- No dev/lint/build/coverage scope violations in frontmatter or body
- File size within the ~5K token target (~20KB)
- Attribution footer present

### Scaffold — directory structure only

Use when you want an empty directory skeleton without generating content:
```bash
bash ../bmad-builder/scripts/scaffold-skill.sh <skill-name>
```
Then fill SKILL.md manually using the template as a guide.

## Scope law for new skills

Every skill created by this builder MUST comply with the Scope Law:

- The plugin PLANS and ORCHESTRATES. It NEVER writes application code, runs tests, lints, checks coverage, builds, or reviews implemented code.
- The last artifact any skill may produce is a ready-for-dev story file or a handoff manifest. Implementation is handed to EXTERNAL dev tools/plugins.
- Acceptance Criteria, Testing STRATEGY, and Dev Notes are planning — allowed. Executing tests or writing implementation code is out of scope.

The `validate-skill.sh` script enforces this automatically by flagging forbidden terms.

## BMAD fidelity reminders

When designing skills, track the BMAD Method conventions:

| Convention | Rule |
|------------|------|
| Scale Tracks | Quick Flow / BMad Method / Enterprise — user confirms interactively |
| Story size | ~2-8h, one dev-day max; split if larger |
| Delivery tracking | Stories remaining / completion rate — NO Fibonacci points, velocity, or burndown |
| Story name | `{epic}.{story}.{slug}.story.md` |
| Story status | backlog → ready-for-dev → in-progress → review → done |
| Decision log | Decisions thread through `decision-log.md` |
| Project constitution | `project-context.md` loaded across skills |
| Three intents | Create / Update / Validate where applicable |

## Available scripts

| Script | Purpose |
|--------|---------|
| `scripts/scaffold-skill.sh <name>` | Creates `skills/<name>/` with subdirs and starter SKILL.md |
| `scripts/validate-skill.sh <SKILL.md>` | Validates frontmatter, scope, size, and attribution footer |

Resolve the referenced script paths from the installed skill directory before running
them. You may run them via `bash` even if executable bits are not preserved.

## Templates

| Template | Use for |
|----------|---------|
| `templates/skill.template.md` | Skeleton for a new planning/orchestration SKILL.md |
| `templates/document.template.md` | Generic planning document (PRD section, brief, spec section, etc.) |

## Subagent strategy

Subagents, when the capability is available, are an important part of this
workflow. Use them as directed by this section.

If the current Codex runtime requires explicit user authorization for subagents,
ask once before launching any subagent and apply that answer to the whole
workflow run. If authorization is denied, or subagent tooling is unavailable,
execute the listed slices sequentially in the main context and keep the same
outputs.

For creating a full skill package in parallel:

| Agent | Task | Output |
|-------|------|--------|
| Agent 1 | Draft SKILL.md body from gathered requirements | `skills/<name>/SKILL.md` |
| Agent 2 | Write domain scripts (validators, checklists) | `skills/<name>/scripts/` |
| Agent 3 | Write domain templates | `skills/<name>/templates/` |
| Agent 4 | Write REFERENCE.md if body exceeds 5K tokens | `skills/<name>/REFERENCE.md` |

Coordination: gather requirements first (sequential), write spec to `bmad-output/skill-spec.md`, then fan out. Main context validates all outputs with `validate-skill.sh` and assembles the final package.

## Notes for LLMs

- Use TodoWrite to track which components have been created.
- Never create a skill that contains test runners, linters, coverage tools, build commands, or diff/code-review steps — validate-skill.sh will flag these.
- Always end SKILL.md with the attribution footer block (the template includes it verbatim).
- Keep SKILL.md under 5K tokens; use REFERENCE.md for lengthy patterns.
- Resolve internal paths relative to the installed skill directory; never hardcode home-directory or machine-specific paths.
- Output artifacts (non-skill files) go under `bmad-output/` by default.

> ---
> Part of the **BMAD Planning & Orchestrator** plugin — a Codex harness for the **BMAD Method** by the **BMAD Code Organization** (https://github.com/bmad-code-org/BMAD-METHOD). Implements the spirit of `bmad-bmb-builder`. All methodology credit belongs to the BMAD Code Organization.
