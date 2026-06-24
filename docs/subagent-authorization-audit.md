# Codex Subagent Authorization Audit

Date: 2026-06-25

This audit records how this Codex BMAD Planning & Orchestrator plugin addresses
the Codex subagent authorization ambiguity described in
[`bmad-code-org/BMAD-METHOD#2451`](https://github.com/bmad-code-org/BMAD-METHOD/issues/2451).

## Scope

The upstream issue asks BMAD skills that rely on subagents, subprocesses, or
parallel agent work to avoid confusing "subagent authorization was not granted"
with "subagent tooling is unavailable." The requested mitigation is an
ask-once guardrail for the whole workflow run.

This plugin is not the upstream BMAD-METHOD repository. It is a planning-only
Codex plugin. The audit below applies only to the skills shipped in this
repository.

## Mitigation Applied

Every shipped skill that contains a `Subagent Strategy` section now includes the
same runtime guardrail:

```text
Subagents, when the capability is available, are an important part of this
workflow. Use them as directed by this section.

If the current Codex runtime requires explicit user authorization for subagents,
ask once before launching any subagent and apply that answer to the whole
workflow run. If authorization is denied, or subagent tooling is unavailable,
execute the listed slices sequentially in the main context and keep the same
outputs.
```

This preserves the previous inline fallback behavior while making the
authorization branch explicit.

## Mitigated Skills

These skills include subagent, fan-out, or parallel-agent workflow guidance and
now include the authorization guardrail:

| Skill | Reason |
| --- | --- |
| `bmad-brainstorm` | May fan out one agent per brainstorming technique. |
| `bmad-builder` | May fan out scaffold, reference, and validation work. |
| `bmad-correct-course` | May fan out large backlog or epic impact analysis. |
| `bmad-epics-and-stories` | May fan out one agent per epic for story drafting. |
| `bmad-handoff` | May fan out story extraction for large backlogs. |
| `bmad-investigate` | May fan out suspected component investigation. |
| `bmad-prfaq` | May fan out customer, internal FAQ, and risk perspectives. |
| `bmad-product-brief` | May launch optional competitive and persona research agents. |
| `bmad-research` | May fan out market, competitive, technical, and domain research. |
| `bmad-sprint-planning` | May use subagent analysis for backlog sequencing. |
| `bmad-tech-spec` | Contains subagent strategy plus a no-parallel-writing rule. |
| `bmad-ux` | May fan out journey-specific UX analysis. |

`bmad-research` maps to the upstream market, domain, and technical research
candidate family.

## No Mitigation Needed

| Skill | Reason |
| --- | --- |
| `bmad-prd` | No subagent, delegation, fan-out, or parallel-agent instructions are present in this plugin's PRD skill. |
| `bmad-architecture` | Discusses downstream parallel agents only as a planning risk; it does not instruct Codex to launch subagents. |

## Not Applicable

The following upstream candidates are not shipped by this plugin:

| Upstream candidate | Local status |
| --- | --- |
| `bmad-agent-tech-writer` | Not present. |
| `bmad-party-mode` | Not present. |

## Future Skill Guardrail

`bmad-builder` was also updated so newly scaffolded skills inherit the same
guardrail:

- `plugins/codex-bmad-planning-orchestrator/skills/bmad-builder/templates/skill.template.md`
- `plugins/codex-bmad-planning-orchestrator/skills/bmad-builder/scripts/scaffold-skill.sh`
- `plugins/codex-bmad-planning-orchestrator/skills/bmad-builder/scripts/validate-skill.sh`

The validator now warns when a skill has a `Subagent` section but lacks either:

- a fallback for unavailable subagent tooling
- an explicit user authorization guardrail

## Validation

Checks run for this repository:

```sh
./scripts/validate.sh
git diff --check
```

Both passed locally.

The upstream BMAD-METHOD quality gate (`npm ci && npm run quality`) was not run
here because this repository is a separate Codex plugin and has no `package.json`.

## Conclusion

This repository has resolved the Codex subagent authorization ambiguity for the
skills it ships. Closing the upstream issue still requires applying or auditing
the equivalent mitigation in `bmad-code-org/BMAD-METHOD` itself and running that
repository's quality gate.
