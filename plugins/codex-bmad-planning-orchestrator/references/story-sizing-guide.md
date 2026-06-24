# Story Sizing Guide — Count-Based Delivery

**For the BMAD Planning & Orchestrator plugin**
Upstream BMAD Method v6.x reference | BMAD Code Organization

---

## The Core Rule

A story must be **small enough for one agent session: roughly 2–8 hours, one dev-day maximum.**

That is the only sizing metric. If a story exceeds one dev-day, split it into two or more stories before it leaves the planning phase.

---

## What "One Agent Session" Means in Practice

An agent session is a single focused context window of work for an external dev tool. A well-sized story:

- Touches a bounded set of files (declared in the Owned File/Module Scope section)
- Has 3–7 numbered Acceptance Criteria, each individually testable
- Fits in roughly 8K tokens as a self-contained context object
- Covers ONE layer or ONE capability slice — not both simultaneously

If your Dev Notes cannot be written in 8K tokens without hand-waving, the story is too large.

---

## Delivery Tracking: Count-Based Only

Progress is tracked by **story count**, not by estimation-unit calculations.

```
Stories remaining = count of stories with status in
  { backlog | ready-for-dev | in-progress | review }

Stories done = count of stories with status: done

Completion rate = done / total   (a simple ratio)
```

Report progress as: "7 of 20 stories done (35%). Wave 1 complete; Wave 2 has 4 stories in progress."

That is the complete progress model. Nothing else is needed.

---

## What Is Explicitly NOT Used and Why

### No Fibonacci Story Points

Fibonacci story points (1, 2, 3, 5, 8, 13 …) assign a relative effort number to each story. The BMAD Method removes them entirely because:

- They create the illusion of precision on inherently uncertain work.
- They require a calibration ceremony (pointing meetings) that produces no planning artifact.
- The resulting "point totals" do not translate to calendar time without velocity history — which new projects and new agent sessions do not have.
- In an AI-agent delivery context, the meaningful constraint is context-window capacity per session, not relative effort across humans. The sizing rule ("one dev-day") captures that constraint directly.

### No Velocity

Velocity (story points completed per sprint) is derived from points. If there are no points, there is no velocity. More fundamentally, velocity is a backward-looking trailing average that is only stable once a team has completed 5–10 sprints. For AI-agent delivery, where session throughput can change significantly as models improve, a trailing average becomes misleading rather than useful.

### No Burndown Charts

Burndown charts plot remaining effort (in points or hours) against calendar time. Without points, there is nothing to burn down. The count-based model replaces burndown with a simpler instrument: the fraction of stories done is visible at a glance from any story list filtered by status. A bar chart of stories-remaining-by-wave conveys the same information as a burndown and requires no estimation data to construct.

---

## Split Heuristics — When to Split a Story

Split a story when ANY of the following is true:

| Signal | Split action |
|--------|-------------|
| Touches more than ~3–5 files of genuinely new logic | Split by file cluster or layer |
| Has more than ~7 Acceptance Criteria | Split by capability or path |
| Spans two layers that could ship independently (e.g., API endpoint AND its UI screen) | Split by layer (API first, UI second) |
| Bundles a schema migration with feature logic | Extract the migration as its own prior story |
| Mixes the happy path with a large error/edge-case surface | Happy path first; hardening follow-up story |
| Dev Notes cannot be written in ~8K tokens without hand-waving | Story is too large; find the seam |

### How to Split

| Pattern | When |
|---------|------|
| **By layer** | `data model → API → UI` as three stories with explicit Blocked-by links |
| **By CRUD operation** | Create / Read / Update / Delete as separate stories |
| **By path** | Happy path first; validation and edge cases in a follow-up |
| **By integration** | Stub or contract first; real integration second |

After splitting, renumber stories within the epic, update Dependency Maps, and update `epics.md`.

---

## Count-Based Reporting in Practice

When a stakeholder asks "how are we doing?", the answer follows this pattern:

> "We have 20 stories total across 4 epics. 7 are done, 4 are in progress (Wave 2), 9 are backlog. At current completion pace (7 done in 3 days = 2.3/day), the remaining 13 stories take roughly 6 more working days."

No points. No velocity. No burndown required. The count and the dates tell the story.

---

## Story Status Lifecycle

```
backlog → ready-for-dev → in-progress → review → done
                                                    ↑
cancelled  (set here on drop; never deleted)    ────
```

Status transitions past `ready-for-dev` are owned by external dev tooling. This plugin owns `backlog` and `ready-for-dev` only.

---

## Reference Connections

- Story context-object contract: `skills/bmad-epics-and-stories/REFERENCE.md`
- Split heuristics in depth: `skills/bmad-epics-and-stories/REFERENCE.md §2`
- Scope-conflict checker: `../scripts/scope-conflict-check.sh`
- Sprint sequencing (wave assignment): `skills/bmad-sprint-planning/SKILL.md`

---

> Part of the **BMAD Planning & Orchestrator** plugin — a Codex harness for the **BMAD Method** by the **BMAD Code Organization** (https://github.com/bmad-code-org/BMAD-METHOD). All methodology credit belongs to the BMAD Code Organization.
