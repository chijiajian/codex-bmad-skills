# Commands and Intents

Codex plugins expose skills, not slash commands. Use `$bmad-*` skill names directly, or
write `bmad:*` intent phrases in normal chat. `/bmad` is not created by this package.

| Intent phrase | Skill | Typical output |
| --- | --- | --- |
| `bmad:help`, `bmad:status`, `bmad:next` | `$bmad-help` | Next recommended planning skill |
| `bmad:init` | `$bmad-init` | `bmad-output/config.yaml`, `decision-log.md`, `project-context.md` |
| `bmad:migrate` | `$bmad-migrate` | Claude BMAD migration report and optional migrated artifacts |
| `bmad:brainstorm` | `$bmad-brainstorm` | `brainstorming-report.md` |
| `bmad:research` | `$bmad-research` | `research-report.md` |
| `bmad:product-brief`, `bmad:brief` | `$bmad-product-brief` | `product-brief.md` |
| `bmad:prfaq` | `$bmad-prfaq` | `prfaq.md` |
| `bmad:spec` | `$bmad-spec` | `SPEC.md` |
| `bmad:prd` | `$bmad-prd` | `prd.md` |
| `bmad:tech-spec` | `$bmad-tech-spec` | `tech-spec.md` |
| `bmad:ux` | `$bmad-ux` | UX planning documents |
| `bmad:architecture`, `bmad:arch` | `$bmad-architecture` | `architecture.md`, ADRs |
| `bmad:stories`, `bmad:story-draft` | `$bmad-epics-and-stories` | `epics.md`, ready-for-dev story files |
| `bmad:readiness-check` | `$bmad-readiness-check` | Readiness report |
| `bmad:sprint-plan` | `$bmad-sprint-planning` | `sprint-status.yaml` |
| `bmad:parallel-plan` | `$bmad-parallel-plan` | `parallelization-plan.md` |
| `bmad:handoff` | `$bmad-handoff` | `handoff-manifest.json` |
| `bmad:correct-course` | `$bmad-correct-course` | Updated planning artifacts and decision log entries |
| `bmad:investigate` | `$bmad-investigate` | Investigation case file |
| `bmad:document-project` | `$bmad-document-project` | Brownfield project documentation |
| `bmad:builder` | `$bmad-builder` | Custom planning skill scaffold or validation report |

## Usage Notes

- Use `$bmad-help` when you are unsure which planning skill should run next.
- Use `$bmad-init` before downstream planning if no `bmad-output/config.yaml` exists.
- Use `$bmad-migrate` before `$bmad-init` when a project already has Claude BMAD
  artifacts from `aj-geddes/claude-code-bmad-skills` or older Claude BMAD skills.
- Use `bmad:*` phrases when coming from another BMAD workflow; Codex treats them as
  natural language triggers.
- Implementation, code review, test execution, and deployment stay outside this package.
