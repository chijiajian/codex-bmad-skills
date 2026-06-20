# Contributing

Keep this package planning-only.

In scope:

- Planning and orchestration skills
- Product, requirements, UX, architecture, story, sequencing, and handoff artifacts
- Validators that check planning documents
- Installation, packaging, and documentation improvements

Out of scope:

- Writing application code
- Running application test suites, linters, builds, or coverage tools
- Reviewing implemented diffs
- Deploying infrastructure

Before submitting changes, run:

```sh
./scripts/validate.sh
```

Skills live under `plugins/codex-bmad-planning-orchestrator/skills/<skill-name>/`.
Each skill must keep valid Codex frontmatter (`name`, `description`) and `agents/openai.yaml` UI metadata.
