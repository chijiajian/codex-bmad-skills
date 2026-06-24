# Track Selection Guide — Quick Flow vs. BMad Method vs. Enterprise

**For the BMAD Planning & Orchestrator plugin**
Upstream BMAD Method v6.x reference | BMAD Code Organization

---

## Overview

BMAD uses three scale-adaptive **tracks** — never numbered levels, phases, or tiers. A track is a planning-need decision that determines which planning artifacts are required before implementation begins. The heuristics in this guide suggest a track; the user always confirms or overrides.

---

## The Three Tracks at a Glance

| Track | Typical story count | Required planning artifacts | Optional |
|-------|--------------------|-----------------------------|----------|
| **Quick Flow** | 1–15 stories | tech-spec only | analysis, UX |
| **BMad Method** | 10–50+ stories | PRD + Architecture (+ optional UX) | analysis, UX |
| **Enterprise** | 30+ stories | PRD + Architecture + Security plan + DevOps plan | analysis |

Story count is a **soft signal only**. The real driver is how much up-front structure the work demands to stay coordinated and de-risked.

---

## Quick Flow

### When It Applies

Quick Flow is the right track when:

- The feature or change is well-bounded and understood by one builder
- Total backlog is roughly 1–15 stories
- No formal cross-team coordination is needed
- Requirements are clear enough to write directly as a technical specification
- Architecture decisions are either trivial (existing stack) or already made
- Compliance, security, or regulatory planning is not required

### What It Requires

| Artifact | Purpose |
|----------|---------|
| `tech-spec.md` | Single planning document: problem, requirements, technical approach, story list |
| `bmad-output/stories/*.story.md` | Story context objects for dev handoff |

PRD and `architecture.md` are NOT required. Stories are compiled directly from the tech-spec.

### Planning Flow

```
bmad-init (Quick Flow)
  → bmad-spec (optional kernel)
    → bmad-tech-spec
      → bmad-epics-and-stories
        → bmad-handoff
```

### Heuristic Signals Pointing to Quick Flow

- "I just need a spec for this feature"
- "It's a focused change, single endpoint or single screen"
- "I'm the only developer"
- "We already know the stack; I just need the stories"
- Story list fits on one page without grouping into epics

---

## BMad Method

### When It Applies

BMad Method is the right track when:

- The backlog is in the range of 10–50+ stories
- Multiple distinct capabilities or features need to be coordinated
- Requirements benefit from structured writing (PRD with MoSCoW prioritization)
- Architecture decisions will affect how multiple parallel agents build concurrently
- There is meaningful UI work that benefits from a UX planning pass
- Cross-epic dependencies and ordering matter

### What It Requires

| Artifact | Purpose |
|----------|---------|
| `prd.md` | Functional requirements (FR-###), NFRs, epic outline, acceptance criteria |
| `architecture.md` | System design, ADRs, FR/NFR coverage matrix, component boundaries |
| `epics.md` | Ordered epic map with story lists |
| `bmad-output/stories/*.story.md` | Compiled story context objects |
| `ux-design.md` *(optional)* | Visual system + experience plan (only if the project has a UI) |

### Planning Flow

```
bmad-init (BMad Method)
  → bmad-product-brief (optional analysis)
    → bmad-prd
      → bmad-architecture
        → bmad-ux (optional — only if UI exists)
          → bmad-readiness-check (gate)
            → bmad-epics-and-stories
              → bmad-sprint-planning
                → bmad-parallel-plan (optional)
                  → bmad-handoff
```

### Heuristic Signals Pointing to BMad Method

- "We need a PRD before we can start"
- "There are multiple teams or workstreams"
- "The architecture decision will affect how stories are split"
- "We have 10 or more distinct features to plan"
- "We need formal requirements traceability"
- "There are significant UX decisions to make before coding"

---

## Enterprise

### When It Applies

Enterprise is the right track when ANY of these is true:

- Compliance, regulatory, or audit requirements are non-negotiable (SOC 2, HIPAA, GDPR, PCI, FedRAMP, etc.)
- Security must be planned up front (threat model, auth/authz strategy, secrets management)
- DevOps/infrastructure planning must happen before implementation (CI/CD strategy, deployment environments, IaC design, on-call and incident response plan)
- Multiple teams are involved and coordination overhead is significant
- Backlog is 30+ stories with complex interdependencies

### What It Requires

Everything BMad Method requires, plus:

| Additional Artifact | Purpose |
|---------------------|---------|
| Security planning addendum | Threat model, authn/authz design, encryption strategy, compliance mapping |
| DevOps planning addendum | CI/CD pipeline design, environment strategy, IaC plan, monitoring and alerting strategy |

**Important:** "Security planning" and "DevOps planning" here are **planning artifacts** — documents that define strategy, requirements, and acceptance criteria. This plugin never executes security scans, provisions infrastructure, or deploys pipelines.

### Planning Flow

```
bmad-init (Enterprise)
  → bmad-product-brief / bmad-prfaq (optional)
    → bmad-prd (with Security and DevOps NFR sections)
      → bmad-architecture (with security/infra ADRs)
        → bmad-ux (optional)
          → security planning addendum
            → DevOps planning addendum
              → bmad-readiness-check (gate)
                → bmad-epics-and-stories (includes Security and DevOps story streams)
                  → bmad-sprint-planning
                    → bmad-parallel-plan
                      → bmad-handoff
```

### Heuristic Signals Pointing to Enterprise

- "We need SOC 2 / HIPAA / PCI compliance"
- "Security has to be designed before we build anything"
- "We need a DevOps strategy before stories go to dev"
- "Multiple teams will be building concurrently across 30+ stories"
- "We have infrastructure and deployment planning to do first"
- "There will be an audit"

---

## Track Selection Heuristic (Machine-Readable Form)

This is the logic `scripts/select-track.sh` in the `bmad-init` skill applies:

```
if compliance/security/infra required OR ~30+ stories:
  suggest Enterprise
elif ~10+ stories OR PRD/architecture clearly needed:
  suggest BMad Method
else:
  suggest Quick Flow
```

The heuristic produces a **suggestion**. Surface it with the reasoning, then ask the user to confirm or override.

When unsure between two tracks, prefer the lighter one — you can always promote later via the `bmad-init` Update intent. Going lighter is cheaper to correct than over-engineering the planning phase.

---

## Promoting Between Tracks

Tracks are not locked at init. If scope grows during planning, promote:

- Quick Flow → BMad Method: run `bmad-prd` and `bmad-architecture` before continuing to stories.
- BMad Method → Enterprise: add security and DevOps planning passes before the readiness gate.

Record the track change in `decision-log.md` with a date and rationale. Update `config.yaml` via `bmad-init` (Update intent).

---

## Reference Connections

- Workspace initialization: `skills/bmad-init/SKILL.md`
- Track decision detail: `skills/bmad-init/REFERENCE.md §Tracks in depth`
- Track selection script: `../skills/bmad-init/scripts/select-track.sh`
- Quick Flow spec skill: `skills/bmad-tech-spec/SKILL.md`
- BMad Method PRD skill: `skills/bmad-prd/SKILL.md`
- BMad Method architecture skill: `skills/bmad-architecture/SKILL.md`

---

> Part of the **BMAD Planning & Orchestrator** plugin — a Codex harness for the **BMAD Method** by the **BMAD Code Organization** (https://github.com/bmad-code-org/BMAD-METHOD). All methodology credit belongs to the BMAD Code Organization.
