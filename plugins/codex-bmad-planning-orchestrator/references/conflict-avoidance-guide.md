# Conflict Avoidance Guide — Semantic and File/Merge Layers

**For the BMAD Planning & Orchestrator plugin**
Upstream BMAD Method v6.x reference | BMAD Code Organization

---

## The Two Conflict Layers

When multiple dev agents work in parallel, two distinct classes of collision can occur. Each is prevented at a different stage of the planning process.

| Layer | What collides | When it surfaces | How it is detected | Where it is prevented |
|-------|--------------|------------------|--------------------|-----------------------|
| **Semantic** | Behavior, contracts, invariants | Integration testing (or production) | Not by git | Architecture / Solutioning phase |
| **File/Merge** | Source file bytes | `git merge` | git conflict markers | Story Owned Scope scoping + worktrees + ordered merges |

Preventing both layers in planning is fundamentally cheaper than resolving them in implementation. A decision changed in an architecture document edits one file; the same decision changed mid-build requires editing many story files, invalidating implemented code, and potentially re-merging completed work. **Catching alignment in solutioning is approximately 10x cheaper than catching it during implementation.** Spend the judgment now.

---

## Layer 1: Semantic Conflicts — Prevented in Architecture / Solutioning

### What a Semantic Conflict Is

Two dev agents edit different source files but change the same behavior, contract, or shared invariant. Git sees no conflict; the source trees merge cleanly. But the integrated system is broken:

- Agent A defines `POST /payments` returning `{ status: "ok" }`.
- Agent B writes the payments UI expecting `{ result: "success" }`.
- Both stories merge without a git conflict. The UI is broken.

Or more subtly:

- Agent A chooses JWT tokens with 15-minute expiry.
- Agent B writes a background job that assumes sessions last 24 hours.
- Both merge. The job silently fails for 23.75 hours out of every 24.

These are semantic conflicts: invisible to version control, expensive to diagnose, and easy to introduce when parallel agents invent their own interpretations of unstated decisions.

### How Architecture Prevents Semantic Conflicts

The `bmad-architecture` skill locks every shared decision into a single document — `architecture.md` — before any story is written. The minimum required Architecture Decision Records (ADRs) for a BMad Method project are:

| Cross-cutting decision | If left unstated, parallel agents will… |
|------------------------|------------------------------------------|
| API style (REST / GraphQL / gRPC) and response envelope | Invent incompatible endpoint shapes |
| Data model (entities, relationships, ownership) | Create divergent schemas that cannot be joined |
| State management strategy (server-side / client-side / cache) | Build inconsistent assumptions into every screen |
| Naming conventions (casing, resource names, error codes) | Produce unmergeable identifier namespaces |
| AuthN/AuthZ model (JWT / session / API key, scopes) | Implement mismatched auth that breaks cross-service calls |
| Error / response convention (shape, HTTP status codes) | Write clients and servers that cannot understand each other |

Each ADR is stated so that a downstream dev agent can follow it mechanically, without judgment. The ADR's `Decision` field is the directive; the `Consequences` field marks what is now LOCKED for all stories.

### The 10x Principle

> **Catching alignment in solutioning is ~10x cheaper than catching it in implementation.**

A semantic conflict caught in `architecture.md` review costs one editing pass on one document. The same conflict caught after three stories have been implemented costs: reverting and re-implementing story N, updating story N+1's Dev Notes (which are LOCKED and require explicit user authorization to change), and re-running the conflict checker across the backlog. The later the catch, the higher the cost multiplier.

### Shared / Cross-Cutting Modules

The architecture document enumerates modules that are inherently shared: auth middleware, database schema files, shared type definitions, dependency injection containers, global configuration, event bus definitions. Any two stories that both touch a shared module are flagged as semantically conflicting even if their file scopes are otherwise disjoint — they cannot safely run in the same parallel wave.

---

## Layer 2: File/Merge Conflicts — Prevented by Owned Scope + Worktrees + Ordered Merges

### What a File/Merge Conflict Is

Two dev agents edit the same source file. When their branches are merged, git produces conflict markers. Resolution requires a human (or another agent) to manually reconcile the two edits. This is:

- Cheap to detect (compare file paths across stories before they run)
- Expensive to resolve after the fact (especially in auto-merged worktrees)
- Completely avoidable with precise scope declaration

### Prevention Step 1: Owned File/Module Scope

Every story compiled by `bmad-epics-and-stories` must declare an explicit `Owned File/Module Scope` section — an enumerated list of every source file or tight directory glob the story is permitted to create or modify:

```
## Owned File/Module Scope

- src/payments/stripe_client.py
- src/payments/__init__.py
- tests/payments/test_stripe_client.py
```

Rules for declaring scope:

- **Be explicit and path-based.** List files or tight globs, not broad directories.
- **Prefer files over directories.** `src/api/routes/checkout.ts` beats `src/api/**`. Broad globs manufacture false conflicts and kill parallelism.
- **Include test paths.** Test files are real files that can collide.
- **Call out shared/contended files.** If two stories must both edit a shared file (e.g., `routes.ts`, `schema.prisma`, a DI container), that is a conflict: either make one `Blocked-by` the other, or extract the shared edit into its own enabling story.
- **No wildcards over the whole repo.** A story claiming `src/**` can never run in parallel.

A story with no declared scope is a **planning blocker**. The `bmad-parallel-plan` skill will not schedule it; the `bmad-sprint-planning` skill will flag it. Fix the scope declaration; never invent paths.

### Prevention Step 2: Scope-Conflict Check

Before any story is marked `ready-for-dev`, run the shared conflict checker:

```bash
bash ../scripts/scope-conflict-check.sh bmad-output/stories/
```

The checker reads the Owned Scope block from each `*.story.md`, computes pairwise path intersections, and reports any pair that shares a path. For each conflict:

- Add a `Dependency Maps / Blocked-by` link to serialize the pair, OR
- Re-slice the stories so their scopes are disjoint, OR
- Extract the shared file into a small enabling story that both depend on.

Re-run until clean. A story is only truly `ready-for-dev` when the checker reports no overlaps with any other `ready-for-dev` story in the same wave.

### Prevention Step 3: Git Worktrees

Each parallel story runs in its own isolated git worktree:

```
story/{epic}.{story}-{slug}   (e.g., story/2.1-stripe-integration)
```

One worktree per story guarantees that the working tree on disk is not shared between concurrent dev agents. Even if two story branches were to share a file (a scope-declaration error), the physical working trees remain separate until the merge step. This provides a second layer of isolation after scope checking.

The `bmad-parallel-plan` skill emits the branch naming and worktree recommendations. Creating and managing actual worktrees is the external dev tool's responsibility — this plugin plans, it does not run `git worktree`.

### Prevention Step 4: Ordered Merges

Within a wave, all story branches are file-disjoint (by construction from the scope check). They can merge in any order without textual conflict. BMAD nonetheless imposes a deterministic merge order for predictability:

1. **Merge in ascending story ID order into `integration/wave-{N}`.** Lower story IDs are typically foundational (earlier in the epic, earlier authored), so the integration branch grows from the most foundational change outward.
2. **Integration review checkpoint.** After all branches land on `integration/wave-{N}`, review the combined result. This is where a hidden semantic interaction between same-wave stories might surface — the only place a semantic conflict that architecture review missed could appear.
3. **Single PR `integration/wave-{N}` → `main`.** One reviewed, integrated unit lands on `main` rather than N independent PRs racing each other.
4. **Wave N+1 branches off the merged `main`.** Each wave starts from a known-good base.

---

## How the Two Layers Work Together

```
PLANNING PHASE (this plugin)
  ├── Architecture review locks semantic decisions (ADRs)
  │     → Prevents semantic conflicts before any story is written
  │
  ├── Story Owned Scope declaration + conflict check
  │     → Detects file-level conflicts before dev agents start
  │
  └── Parallel plan with ordered merge sequence
        → Ensures file-disjoint waves and deterministic integration

IMPLEMENTATION PHASE (external dev tools)
  ├── Worktrees enforce runtime isolation
  └── Merge order + integration checkpoint catch anything that slipped through
```

The earlier a conflict class is caught, the cheaper it is to resolve. Architecture catches semantic conflicts at the lowest cost. Scope checking catches file conflicts at low cost. Worktrees and ordered merges are the safety net — they catch what the planning layers miss, but they are significantly more expensive to resolve.

---

## Reference Connections

- Architecture / ADR authoring: `skills/bmad-architecture/SKILL.md`
- NFR and ADR coverage: `skills/bmad-architecture/REFERENCE.md`
- Scope declaration discipline: `skills/bmad-epics-and-stories/REFERENCE.md §4`
- Scope conflict checker: `../scripts/scope-conflict-check.sh`
- Wave algorithm and conflict edge types: `skills/bmad-parallel-plan/REFERENCE.md §2`
- Worktree and branch naming: `skills/bmad-parallel-plan/REFERENCE.md §5`

---

> Part of the **BMAD Planning & Orchestrator** plugin — a Codex harness for the **BMAD Method** by the **BMAD Code Organization** (https://github.com/bmad-code-org/BMAD-METHOD). All methodology credit belongs to the BMAD Code Organization.
