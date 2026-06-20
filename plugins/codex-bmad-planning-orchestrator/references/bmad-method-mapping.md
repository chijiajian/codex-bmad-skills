# BMAD Method Mapping — Plugin Skills to Upstream BMAD Counterparts

**For the BMAD Planning & Orchestrator plugin**
Upstream BMAD Method v6.x | BMAD Code Organization (https://github.com/bmad-code-org/BMAD-METHOD)

---

## About This Document

This file maps every skill in the BMAD Planning & Orchestrator plugin to its upstream counterpart in the BMAD Method v6.x implementation by the **BMAD Code Organization**. The plugin is a Codex harness that implements the spirit of that method — adapting it for AI-agent planning workflows, scale-adaptive tracks, and parallel dev handoff. All methodology credit belongs to the BMAD Code Organization.

**Upstream version tracked:** v6.x

---

## Skill-to-Upstream Mapping

| Plugin skill (namespace: `bmad-planning-orchestrator:`) | Upstream BMAD counterpart | Phase / Role | Notes |
|----------------------------------------------------------|--------------------------|--------------|-------|
| `bmad-init` | `bmad-init` | Cross-phase scaffolder | Workspace initialization, track selection (Quick Flow / BMad Method / Enterprise), `config.yaml`, `decision-log.md`, `project-context.md` |
| `bmad-help` | `bmad-help` | Cross-phase router | Orchestration spine; detects planning state from artifacts present; routes to next skill; replaces a heavyweight orchestrator persona |
| `bmad-spec` | `bmad-spec` | Pre-planning kernel | Five-field distiller (Problem, Capabilities, Constraints, Non-Goals, Success Metrics); accepts any messy input; feeds PRD or tech-spec |
| `bmad-prfaq` | `bmad-prfaq` | Pre-planning / Analysis | Amazon Working-Backwards press release + internal and external FAQs; stress-tests concept before PRD |
| `bmad-product-brief` | `bmad-business-analyst` | Phase 1: Analysis | Guided discovery conversation; produces `product-brief.md`; persona Mary (Business Analyst) |
| `bmad-research` | `bmad-market/domain/technical-research` | Phase 1: Analysis | Live web research (market, competitive, technical, domain); cited `research-report.md` |
| `bmad-brainstorm` | `bmad-brainstorming` | Phase 1: Analysis | Structured ideation (SCAMPER, SWOT, 5 Whys, Six Thinking Hats, etc.); `brainstorming-report.md` |
| `bmad-document-project` | `bmad-document-project` | Phase 1: Analysis (brownfield) | READ-ONLY codebase scan; produces `project-documentation.md` as brownfield planning ground truth |
| `bmad-prd` | `bmad-prd` | Phase 2: Planning | PRD facilitator (John the PM); FR-###, NFR-###, MoSCoW, RICE, epics outline; `prd.md` |
| `bmad-tech-spec` | `bmad-tech-spec` | Phase 2: Planning (Quick Flow) | Lightweight planning doc for 1–15 story scope; replaces PRD + architecture for Quick Flow track |
| `bmad-architecture` | `bmad-create-architecture` | Phase 3: Solutioning | System design, ADRs, FR/NFR coverage matrix; semantic conflict prevention; persona Winston (Architect) |
| `bmad-ux` | `bmad-ux-designer` | Phase 3: Solutioning (optional) | Visual system (`DESIGN.md`) + user journeys (`EXPERIENCE.md`); WCAG 2.1 AA contract; persona Sally (UX) |
| `bmad-readiness-check` | `bmad-check-implementation-readiness` | Phase 3: Solutioning gate | Cross-references PRD, architecture, and epics for coverage; PASS / CONCERNS / FAIL verdict before stories begin |
| `bmad-epics-and-stories` | `bmad-create-epics-and-stories` | Phase 4: Implementation handoff | Shards PRD + architecture into `epics.md` + per-story context objects; compiled self-contained ~8K-token story files; the last planning artifact |
| `bmad-sprint-planning` | `bmad-sprint-planning` | Phase 4: Orchestration handoff | Sequences stories by dependency; assigns parallel waves; emits `sprint-status.yaml`; no velocity, no points |
| `bmad-parallel-plan` | `bmad-parallel-plan` | Phase 4: Orchestration handoff | Builds dependency DAG; topologically sorts into conflict-free concurrent waves; emits `parallelization-plan.md` with worktree branch names and merge order |
| `bmad-handoff` | `bmad-handoff` | Phase 4: Implementation handoff | Emits `handoff-manifest.json` for dev-tool-agnostic consumption; the final plugin artifact |
| `bmad-correct-course` | `bmad-correct-course` | Cross-phase correction | Mid-stream scope / architecture change handler; minimum-blast-radius re-shard; routes to epics-and-stories, sprint-planning, or parallel-plan as needed |
| `bmad-investigate` | `bmad-investigate` | Cross-phase triage | Forensic bug triage; graded evidence (A/B/C); hypothesis ranking; produces investigation case file + optional fix story |
| `bmad-builder` | `bmad-bmb-builder` | Meta / tooling | Scaffolds and validates new planning/orchestration skills for this plugin; enforces scope law |

---

## Phase Summary

```
Phase 1: Analysis (optional)
  bmad-product-brief, bmad-research, bmad-brainstorm,
  bmad-document-project, bmad-prfaq, bmad-spec

Phase 2: Planning (required)
  Quick Flow:     bmad-tech-spec
  BMad / Enterprise: bmad-prd

Phase 3: Solutioning (track-dependent)
  bmad-architecture, bmad-ux (optional), bmad-readiness-check

Phase 4: Implementation handoff (required)
  bmad-epics-and-stories → bmad-sprint-planning
                         → bmad-parallel-plan (optional)
                         → bmad-handoff

Cross-phase (any point):
  bmad-init, bmad-help, bmad-correct-course,
  bmad-investigate, bmad-builder
```

---

## What This Plugin Adapts from the Upstream Method

The plugin faithfully implements the BMAD Method's structure. Where it adapts:

| Upstream concept | Plugin adaptation | Reason |
|-----------------|-------------------|--------|
| Numbered Levels (1, 2, 3 …) | Named Tracks (Quick Flow, BMad Method, Enterprise) | Levels implied fixed scope; tracks are planning-need decisions chosen interactively |
| Story points / Fibonacci | Removed entirely | No estimation currency needed when sizing rule is "one dev-day"; progress tracked by count |
| Velocity and burndown | Removed entirely | Trailing averages are stable only after many sprints; count-based reporting is simpler and equally informative |
| Sprint planning with capacity | Wave planning with `maxParallel` | AI-agent delivery constraint is concurrent session count, not team member capacity |
| Persona-driven agent characters | Persona flavor only (not heavy overhead) | Skills are workflows; personas are flavor to signal intent, not full character simulation |

---

## Attribution

All BMAD Method concepts, structures, and practices implemented here originate from the **BMAD Code Organization**. The BMAD Planning & Orchestrator plugin is a Codex harness for that method. This plugin does not claim authorship of the BMAD Method.

Upstream repository: https://github.com/bmad-code-org/BMAD-METHOD
Upstream version tracked: **v6.x**

---

> Part of the **BMAD Planning & Orchestrator** plugin — a Codex harness for the **BMAD Method** by the **BMAD Code Organization** (https://github.com/bmad-code-org/BMAD-METHOD). All methodology credit belongs to the BMAD Code Organization.
