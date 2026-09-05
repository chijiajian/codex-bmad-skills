#!/usr/bin/env python3
"""Inspect native/legacy BMAD state and recommend the next planning step."""

import argparse
import json
from pathlib import Path

from planning_contract import field_value, scalar, story_id, story_parts, story_status, text, track_for
from validate_handoff import validate as validate_manifest
from sequence_sprint import validate_schedule


def artifacts(output, *patterns):
    return sorted({path for pattern in patterns for path in output.glob(pattern)
                   if path.is_file() and path.stat().st_size})


def detect(output, project_root=None):
    project_root = Path(project_root or Path.cwd())
    compatibility = Path("bmad")
    native_default = Path("bmad-output").resolve()
    migration = [str(path) for path in map(Path, (
        ".claude", ".bmad-core", "docs/prd.md", "docs/architecture.md",
        "docs/epics.md", "docs/stories", "bmad-output",
    )) if path.exists() and path.resolve() != output.resolve()]
    # A custom native output is not a migration merely because a config pointer exists.
    if output.resolve() != native_default and scalar(Path("bmad-output/config.yaml"), "output_folder"):
        migration = [name for name in migration if name != "bmad-output"]
    groups = {
        "CTX": artifacts(output, "project-context.md"),
        "LOG": artifacts(output, "decision-log.md"),
        "BRIEF": artifacts(output, "product-brief*.md", "analysis/product-brief*.md"),
        "PRD": artifacts(output, "prd.md", "planning/prd.md"),
        "SPEC": artifacts(output, "tech-spec.md", "planning/tech-spec.md"),
        "EPICS": artifacts(output, "epics.md", "planning/epics.md"),
        "ARCH": artifacts(output, "architecture.md", "solutioning/architecture.md"),
        "UX": artifacts(output, "ux-design*.md", "ux/ux-design*.md"),
        "SPRINT": artifacts(output, "sprint-status.yaml"),
        "MANIFEST": artifacts(output, "handoff-manifest.json"),
    }
    design, experience = artifacts(output, "DESIGN.md"), artifacts(output, "EXPERIENCE.md")
    if design or experience:
        groups["UX"] = design + experience if design and experience else []
    state = {"HAS_" + key: int(bool(value)) for key, value in groups.items()}
    configured_stories = scalar(output / "config.yaml", "stories_folder")
    stories = sorted(Path(configured_stories).glob("*.story.md")) if configured_stories else artifacts(
        output, "stories/*.story.md", "implementation/stories/*.story.md", "*.story.md")
    statuses = [story_status(path) for path in stories]
    active = [value for value in statuses if value != "cancelled"]
    state.update(
        TRACK=track_for(output, compatibility),
        HAS_STORIES=int(bool(stories)), STORY_COUNT=len(active),
        READY_COUNT=sum(value in {"ready-for-dev", "in-progress", "review", "done"} for value in active),
        BEYOND_COUNT=sum(value in {"in-progress", "review", "done"} for value in active),
        CANCELLED_COUNT=statuses.count("cancelled"),
        HAS_COMPAT_WORKFLOW=int((compatibility / "workflow-status.yaml").is_file()),
        COMPAT_TRACK=track_for(Path("__no_native_bmad__"), compatibility),
        HAS_MIGRATION_SOURCE=int(bool(migration)), MIGRATION_HINTS=", ".join(migration),
    )
    ui = scalar(output / "config.yaml", "has_ui").lower()
    state["HAS_UI"] = "1" if ui == "true" else "0" if ui == "false" else "1" if state["HAS_UX"] else "unknown"
    reports = artifacts(output, "readiness-report*.md")
    state["READINESS"] = "missing"
    if reports:
        report = max(reports, key=lambda path: path.stat().st_mtime_ns)
        inputs = sum((groups[key] for key in ("CTX", "PRD", "SPEC", "ARCH", "UX")), [])
        inputs += artifacts(output, "config.yaml")
        stale = any(path.stat().st_mtime_ns > report.stat().st_mtime_ns for path in inputs)
        state["READINESS"] = "stale" if stale else field_value(text(report), "verdict", {"pass", "concerns", "fail"})
    schedule = {}
    if state["HAS_SPRINT"]:
        try:
            import yaml
            schedule_data = yaml.safe_load(text(groups["SPRINT"][0]))
            validate_schedule(schedule_data, stories)
            schedule = {story_id(row["id"]): row for row in schedule_data["stories"]}
        except ImportError:
            state["HAS_SPRINT"] = 0
            state["SCHEDULE_ERROR"] = "Install PyYAML for the helper interpreter."
        except (ValueError, TypeError, AttributeError, yaml.YAMLError) as error:
            state["HAS_SPRINT"] = 0
            state["SCHEDULE_ERROR"] = str(error)
        scheduling_inputs = stories + groups["EPICS"]
        if any(path.stat().st_mtime_ns > groups["SPRINT"][0].stat().st_mtime_ns for path in scheduling_inputs):
            state["HAS_SPRINT"] = 0
            state["SCHEDULE_ERROR"] = "Story or epic inputs changed after scheduling."
    if state["HAS_MANIFEST"]:
        path = groups["MANIFEST"][0]
        try:
            manifest = json.loads(text(path))
            validate_manifest(manifest)
            expected = {story_id(path.name.removesuffix(".story.md")): path for path in stories
                        if story_status(path) == "ready-for-dev"}
            actual = {story_id(row["id"]) for row in manifest["stories"]}
            inputs = stories + groups["SPRINT"] + reports
            if actual != set(expected) or not state["HAS_SPRINT"]:
                raise ValueError("manifest stories or scheduling inputs do not match")
            for row in manifest["stories"]:
                sid = story_id(row["id"])
                scope, dependencies = story_parts(expected[sid])
                if (row["ownedScope"] != scope or
                        {story_id(dep) for dep in row["dependencies"]} != set(dependencies) or
                        row["wave"] != schedule[sid]["parallel_set"] or
                        (project_root / row["storyFilePath"]).resolve() != expected[sid].resolve()):
                    raise ValueError("manifest metadata differs from source story or schedule: " + sid)
            if any(item.stat().st_mtime_ns > path.stat().st_mtime_ns for item in inputs):
                state["HAS_MANIFEST"] = 0
        except (OSError, ValueError, TypeError, KeyError):
            state["HAS_MANIFEST"] = 0
    state["PHASE"] = ("uninitialized" if not state["HAS_CTX"] else
                      "implementation-external" if state["BEYOND_COUNT"] else
                      "implementation-handoff" if state["HAS_STORIES"] else
                      "solutioning" if state["HAS_ARCH"] else "planning")
    if recommend(state)[0] == "(none — handoff complete)":
        state["PHASE"] = "handoff-complete"
    return state


def recommend(state):
    if not state["HAS_CTX"]:
        if state["HAS_MIGRATION_SOURCE"]:
            return "bmad-migrate", "Existing planning artifacts detected; inspect migration before initializing."
        return "bmad-init", "Establish project context and record the chosen track."
    if state["TRACK"] == "unknown":
        return "(confirm track with the user)", "Record a valid project.track in config.yaml; reuse existing authorization."
    quick = state["TRACK"] == "quick-flow"
    if quick and not state["HAS_SPEC"]:
        return "bmad-tech-spec", "Quick Flow needs tech-spec.md."
    if not quick and not state["HAS_PRD"]:
        return "bmad-prd", "This track needs prd.md; a tech-spec alone does not replace it."
    if state["HAS_UI"] == "unknown":
        return "(confirm UI scope with the user)", "Record project.has_ui: true or false once in config.yaml."
    if state["HAS_UI"] == "1" and not state["HAS_UX"]:
        return "bmad-ux", "Complete DESIGN.md and EXPERIENCE.md (legacy ux-design.md is accepted)."
    if not quick and not state["HAS_ARCH"]:
        return "bmad-architecture", "Complete architecture.md, including Enterprise security/operations when applicable."
    if state["READINESS"] not in {"pass", "concerns"}:
        return "bmad-readiness-check", "Readiness verdict is " + state["READINESS"] + "; inspect the current planning inputs."
    if (not quick and not state["HAS_EPICS"]) or not state["HAS_STORIES"]:
        return "bmad-epics-and-stories", "Compile the story context objects; carry forward any readiness concerns."
    if state["STORY_COUNT"] == 0:
        return "(none — no active stories)", "All stories are cancelled; no work is eligible for handoff."
    if state["READY_COUNT"] < state["STORY_COUNT"]:
        return "bmad-epics-and-stories", "Some active story documents remain backlog or have an invalid/missing status."
    if not state["HAS_SPRINT"]:
        return "bmad-sprint-planning", "Create or refresh sprint-status.yaml. " + state.get("SCHEDULE_ERROR", "Mirror current stories and dependencies.")
    if state["BEYOND_COUNT"]:
        return "(none — implementation underway externally)", "Execution has started; keep story status and the scheduling view synchronized."
    if state["HAS_MANIFEST"]:
        return "(none — handoff complete)", "Current readiness, scheduling and validated story manifest are present."
    return "bmad-handoff", "Planning and scheduling are prepared. Generate or refresh the optional validated handoff manifest."


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", nargs="?")
    parser.add_argument("--output", dest="output_option")
    parser.add_argument("--recommend", action="store_true")
    parser.add_argument("--phase", action="store_true", help="Print the shared check-phase.sh key/value interface")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    output = Path(args.output_option or args.output or scalar(Path("bmad-output/config.yaml"), "output_folder") or "bmad-output")
    state = detect(output)
    if args.json:
        print(json.dumps(state))
        return
    if args.phase:
        skill, why = recommend(state)
        print(f"PHASE={state['PHASE']}\nTRACK={state['TRACK']}\nNEXT_SKILL={skill if skill.startswith('bmad-') else 'none'}\nREASON={why}")
    elif args.recommend:
        skill, why = recommend(state)
        print(f"Phase: {state['PHASE']}    Track: {state['TRACK']}\nRun: {skill}\nWhy: {why}")
        if state["HAS_COMPAT_WORKFLOW"]:
            print("Compatibility state is advisory; native config.yaml takes precedence.")
        print("NEXT_SKILL=" + skill)
    else:
        print(f"BMAD planning state: {output}")
        for key, value in state.items():
            print(f"{key}={value}")


if __name__ == "__main__":
    main()
