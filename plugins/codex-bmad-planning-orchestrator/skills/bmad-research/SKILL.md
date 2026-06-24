---
name: bmad-research
description: |
  Conducts market, competitive, domain, or technical research with citations and
  writes research-report.md for BMAD planning. Use for "$bmad-research",
  "bmad:research", or when the user says "research this topic", "competitive
  analysis", "who are the competitors", "market size", "market landscape",
  "technical research", "evaluate this technology", "domain research", "industry
  analysis", "find out about this space", "research before we plan", or "gather
  information". Supports Create, Update, and Validate.
---

# BMAD Research

## Codex Resource Paths

Resolve bundled resources relative to this skill directory. When running a bundled script, use the absolute path to that script from the installed plugin location; relative examples are shown from this `SKILL.md` directory. Shared BMAD helper scripts live under `../../scripts/`, and shared references live under `../../references/`.

Conducts structured, cited research across three modes to feed BMAD planning workflows.
Output is a research-report.md in bmad-output/, ready for handoff to planning skills.

---

## Step 0 — Clarify Intent

Before searching, confirm:

1. **Mode** — Create / Update / Validate (default: Create)
2. **Research type** — Market | Competitive | Technical | Domain (may combine)
3. **Topic** — What is being researched?
4. **Output destination** — Default: `bmad-output/research-report.md`

If project-context.md exists, read it first (`bmad-output/project-context.md`) for
scope constraints.

---

## Step 1 — Plan the Research

Use the source-type strategy guide to pick sources by research type:

```
../bmad-research/scripts/research-sources.sh
```

Run it (Bash) to print the guide, then sketch a query plan:
- 3–5 targeted WebSearch queries per research type
- Specific URLs to WebFetch (industry reports, competitor sites, docs)
- Triangulation goal: each key claim backed by 2+ independent sources

Track progress with TodoWrite.

---

## Step 2 — Execute Research

### Market Research
- Search: market size, TAM/SAM/SOM, growth CAGR, key trends, growth drivers
- Sources: Statista, Grand View Research, CB Insights, SEC filings, industry reports
- Quantify everything possible: dollar values, percentages, time frames

### Competitive Research
- Search: top competitors, feature comparisons, pricing, user reviews, funding
- Sources: G2/Capterra (reviews), Crunchbase (funding/size), company IR pages,
  product documentation, Reddit/HN community sentiment
- Build a feature comparison matrix

### Technical Research
- Search: framework benchmarks, adoption rates, community health, known trade-offs
- Sources: Official docs, GitHub stars/issues, npm/PyPI stats, State of JS/CSS,
  ThoughtWorks Radar, Stack Overflow surveys
- Evaluate: maturity, ecosystem, licensing, long-term viability

### Domain Research
- Search: regulatory landscape, industry standards, key players, domain glossary
- Sources: Government databases, standards bodies, academic papers (Google Scholar,
  arXiv), trade publications

**Citation discipline**: for every factual claim, record source URL + access date.
When a claim cannot be verified across 2+ sources, mark it `[UNVERIFIED]`.

---

## Step 3 — Update Mode

If mode is Update, read the existing report first. Then:
1. Identify sections with stale data (>6 months old, or marked `[UNVERIFIED]`)
2. Re-run targeted searches for those sections only
3. Append a "Last Updated" entry per section
4. Increment the report version

---

## Step 4 — Validate Mode

If mode is Validate:
1. Extract all quantitative claims from the existing report
2. Spot-check each claim with a fresh WebSearch
3. Mark each claim: `[VERIFIED]`, `[CONTRADICTED source: …]`, or `[UNVERIFIED]`
4. Append a "Validation Summary" section noting overall confidence

---

## Step 5 — Write the Report

Use the template:

```
../bmad-research/templates/research-report.template.md
```

Fill all sections. Sections irrelevant to the research type may be omitted (mark as
N/A). Write the completed report to:

```
bmad-output/research-report.md   # or a user-specified path
```

**Required sections regardless of mode:**
- Executive Summary with key findings and bottom line
- Research Scope (in/out of scope, time frame)
- Methodology (sources used, tools, limitations)
- Gaps & Opportunities
- Recommendations (planning actions, not implementation actions)
- Full source bibliography (Appendix B) with URLs and access dates

---

## Step 6 — Handoff

After writing the report, tell the user:
- The output path
- The 3 most important findings in plain language
- Which BMAD planning skill should consume this report next:
  - Market/Competitive → business-analyst or product-manager
  - Technical → system-architect
  - Domain → business-analyst

Record the research decision in `bmad-output/decision-log.md`:
```
## Research: [Topic] — [Date]
- Mode: [Create/Update/Validate]
- Types: [Market/Competitive/Technical/Domain]
- Key finding: [one sentence]
- Report: bmad-output/research-report.md
- Next skill: [skill name]
```

---

## Subagent Strategy

Subagents, when the capability is available, are an important part of this
workflow. Use them as directed by this section.

If the current Codex runtime requires explicit user authorization for subagents,
ask once before launching any subagent and apply that answer to the whole
workflow run. If authorization is denied, or subagent tooling is unavailable,
execute the listed slices sequentially in the main context and keep the same
outputs.

For broad research covering multiple types simultaneously, fan out parallel agents:

**Agent 1 — Market Agent**
```
Read project-context.md, then conduct market research on [topic]:
TAM/SAM/SOM, growth rates, key trends. Write findings to
bmad-output/research-scratch/market.md with full citations.
```

**Agent 2 — Competitive Agent**
```
Read project-context.md, then research top 3-5 competitors for [topic]:
features, pricing, strengths/weaknesses, user sentiment. Write findings to
bmad-output/research-scratch/competitive.md with full citations.
```

**Agent 3 — Technical/Domain Agent**
```
Read project-context.md, then research technical landscape for [topic]:
technology options, ecosystem health, standards. Write findings to
bmad-output/research-scratch/technical.md with full citations.
```

After all agents complete, synthesize scratch files into the final report using the
template. Delete scratch files after synthesis.

---

> ---
> Part of the **BMAD Planning & Orchestrator** plugin — a Codex harness for the **BMAD Method** by the **BMAD Code Organization** (https://github.com/bmad-code-org/BMAD-METHOD). Implements the spirit of `bmad-market/domain/technical-research`. All methodology credit belongs to the BMAD Code Organization.
