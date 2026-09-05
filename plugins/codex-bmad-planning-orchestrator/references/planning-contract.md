# Shared BMAD Planning Contract

## Activation and authorization

Apply these workflows to a BMAD planning request or an established BMAD planning session.
Generic requests to continue, investigate, write a skill, or summarize notes do not by
themselves require a BMAD workspace. Keep normal implicit skill discovery enabled.

Reuse decisions and explicit authorization already present in the conversation and
project config. Ask only when missing information materially changes scope or the next
step. A request to perform an identified change is authorization for that change; do
not demand a second confirmation for the same edit. Materially different actions require
a new decision. Existing runtime restrictions and subagent authorization remain in force.

Planning-only restrictions apply to this plugin's planning work. They do not prohibit
writing a downstream verification strategy or specifying concrete development checks.
When the user also explicitly requests implementation, finish the planning portion and
continue through the normal implementation workflow outside this skill's scope.

Use the current environment's file, search, progress and shell capabilities; historical
names such as TodoWrite, Read, Write, Edit or Glob are not required tool identifiers.
If subagents are permitted but restricted to read-only access, request returned drafts
and let the main agent save them; do not relax their permissions.

## Helper dependencies

Use Python 3.9+ for the bundled helpers. Sequencing needs PyYAML and schema validation
needs jsonschema. The dependency file is bundled in ../scripts/requirements.txt;
install it for the same Python interpreter that runs the helpers. A missing dependency
is a setup error, not proof that planning is complete.

## Artifact and configuration ownership

- config.yaml owns current project.track and project.has_ui. Resolve native values
  before legacy decision-log or bmad/*.yaml fallbacks. decision-log records rationale
  and history; do not infer current settings from arbitrary prose when config exists.
- Explicit output-folder arguments override defaults. Without one, use the
  paths.output_folder pointer in bmad-output/config.yaml, then bmad-output.
- Quick Flow: tech-spec.md contains requirements and technical approach.
- BMad Method/Enterprise: prd.md + architecture.md; Enterprise includes security/operations.
- UI work: DESIGN.md describes the visual system; EXPERIENCE.md describes journeys/states.
  A legacy ux-design.md can be read while migrating, but new consumers use the pair.
- A readiness report records **Verdict:** PASS, CONCERNS or FAIL after semantic review.
  Script pre-flight results are advisory and do not replace that report.

## Story lifecycle and scheduling

- Canonical story ID is epic.story (for example 2.1); the slug belongs in its filename.
  Legacy epic.story.slug IDs are normalized when resolving dependencies.
- The story header **Status:** owns lifecycle: backlog, ready-for-dev, in-progress,
  review, done, cancelled. ready-for-dev means the document is complete; it does not
  mean all its prerequisites are already done.
- sprint-status.yaml is the scheduling view: mirror lifecycle from referenced story
  files and assign parallel_set waves. Do not downgrade complete later-wave stories
  to backlog, or delete dependency history after a prerequisite completes.
- Keep dependencies under **Blocked by:** in Dependency Maps. A missing, cancelled,
  backlog, or otherwise unresolved prerequisite blocks execution; never assume it done.
- A completed prerequisite satisfies its dependency. Cancelled stories are excluded
  from active-work counts, but cancelling a prerequisite does not satisfy it.
- Scope checks can report overlap across different waves; serialize those stories.
  Only stories within the same wave must have disjoint scopes. Overlap alone does not
  make a fully specified story document incomplete.

## Scope and handoff checks

Use repository-relative file or directory paths in scope bullets; backticks preserve
spaces. Shared/contended bullets must put the actual path in backticks. Parent traversal,
absolute paths and unresolved placeholders are invalid. Planned files need not exist.

Globs reserve their fixed directory prefix: src/auth/** reserves src/auth. This may
serialize more work than exact glob intersection would, but cannot declare that scope
safe alongside src/auth/login.ts. A root glob reserves the entire repository.

Run scope-conflict-check.sh with --stories <directory> or --story-files <files...>.
Resolve missing/invalid scopes; carry valid overlapping scopes into separate waves.

Handoff exports all ready-for-dev documents, including later waves. Reuse scheduling
annotations, preserve dependencies, and validate the result with validate_handoff.py.
Only schema-nullable fields may contain null. If required data or dependency ordering
cannot be established, report the gap and leave the prior manifest intact. Never
claim an invalid or stale manifest is a completed handoff.
