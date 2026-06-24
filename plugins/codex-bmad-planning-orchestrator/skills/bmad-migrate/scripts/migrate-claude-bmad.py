#!/usr/bin/env python3
"""Migrate Claude BMAD planning artifacts into the Codex BMAD layout.

Default mode is a dry run that prints a Markdown migration report. --apply copies
missing planning artifacts and writes bmad-output/migration-report.md. Existing
target files are never overwritten.
"""

from __future__ import annotations

import argparse
import filecmp
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


ROOT_ARTIFACTS = [
    "config.yaml",
    "project-context.md",
    "decision-log.md",
    "product-brief.md",
    "brainstorming-report.md",
    "research-report.md",
    "prfaq.md",
    "SPEC.md",
    "spec.md",
    "prd.md",
    "addendum.md",
    "tech-spec.md",
    "ux-design.md",
    "DESIGN.md",
    "design.md",
    "EXPERIENCE.md",
    "experience.md",
    "architecture.md",
    "epics.md",
    "readiness-report.md",
    "sprint-status.yaml",
    "parallelization-plan.md",
    "handoff-manifest.json",
    "project-documentation.md",
]

SUPPLEMENTAL_BMAD = [
    "project.yaml",
    "workflow-status.yaml",
    "sprint-status.yaml",
]

REMOVED_CAPABILITY_PATTERNS = [
    ".claude/commands/bmad/dev-story",
    ".claude/skills/bmad/developer",
    "dev-story",
    "developer",
    "coverage",
    "lint",
]


@dataclass(frozen=True)
class Candidate:
    source: Path
    target: Path
    kind: str
    note: str = ""


def rel(path: Path, base: Path) -> str:
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return path.as_posix()


def normalize_track(raw: str) -> str:
    value = raw.strip().strip('"').strip("'").lower().replace("_", "-")
    if "enterprise" in value:
        return "enterprise"
    if "bmad-method" in value or "bmad method" in value:
        return "bmad-method"
    if "quick-flow" in value or "quick flow" in value or "quick" in value:
        return "quick-flow"
    return "unknown"


def read_text(path: Path, limit: int = 200_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:limit]
    except OSError:
        return ""


def infer_track(source: Path, candidates: list[Candidate]) -> str:
    for path in [
        source / "bmad-output" / "config.yaml",
        source / "bmad" / "workflow-status.yaml",
        source / "bmad" / "project.yaml",
    ]:
        text = read_text(path)
        match = re.search(r"(?im)^\s*track\s*:\s*(.+?)\s*$", text)
        if match:
            track = normalize_track(match.group(1))
            if track != "unknown":
                return track

    decision_log = source / "bmad-output" / "decision-log.md"
    text = read_text(decision_log)
    match = re.search(r"(?i)track[:=\s].*(quick[- ]?flow|bmad[- ]?method|enterprise)", text)
    if match:
        return normalize_track(match.group(1))

    candidate_targets = {c.target.name.lower() for c in candidates}
    story_count = sum(1 for c in candidates if c.kind == "story")
    if story_count >= 30:
        return "enterprise"
    if "prd.md" in candidate_targets or "architecture.md" in candidate_targets:
        return "bmad-method"
    if story_count >= 10:
        return "bmad-method"
    return "quick-flow"


def infer_project_name(source: Path) -> str:
    config = source / "bmad-output" / "config.yaml"
    text = read_text(config)
    match = re.search(r"(?im)^\s*name\s*:\s*(.+?)\s*$", text)
    if match:
        return match.group(1).strip().strip('"').strip("'")
    return source.resolve().name or "Migrated BMAD Project"


def first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.is_file():
            return path
    return None


def add_candidate(candidates: list[Candidate], source: Path | None, target: Path, kind: str, note: str = "") -> None:
    if source is None:
        return
    resolved = source.resolve()
    if any(c.source.resolve() == resolved and c.target == target for c in candidates):
        return
    candidates.append(Candidate(source=source, target=target, kind=kind, note=note))


def discover_candidates(source: Path, output: Path) -> list[Candidate]:
    candidates: list[Candidate] = []
    native = source / "bmad-output"
    docs = source / "docs"

    for name in ROOT_ARTIFACTS:
        canonical_name = "SPEC.md" if name == "spec.md" else name
        target = output / canonical_name
        add_candidate(candidates, native / name if (native / name).is_file() else None, target, "artifact", "native bmad-output")
        add_candidate(candidates, docs / name if (docs / name).is_file() else None, target, "artifact", "docs fallback")

    for story_root in [native / "stories", native / "implementation" / "stories", docs / "stories"]:
        if story_root.is_dir():
            for story in sorted(story_root.glob("*.story.md")):
                add_candidate(candidates, story, output / "stories" / story.name, "story", rel(story_root, source))

    for story in sorted(docs.glob("*.story.md")) if docs.is_dir() else []:
        add_candidate(candidates, story, output / "stories" / story.name, "story", "docs root story")

    bmad = source / "bmad"
    for name in SUPPLEMENTAL_BMAD:
        add_candidate(
            candidates,
            bmad / name if (bmad / name).is_file() else None,
            Path("bmad") / name,
            "compat",
            "supplemental compatibility state",
        )

    return candidates


def detect_source_family(source: Path) -> list[str]:
    family: list[str] = []
    if (source / "bmad-output").is_dir():
        family.append("Claude BMAD plugin/native bmad-output")
    if (source / "docs").is_dir():
        family.append("old/docs-based BMAD artifacts")
    if (source / "bmad").is_dir():
        family.append("XMM-style bmad/*.yaml state")
    if (source / ".claude").exists():
        family.append("old Claude local install remnants")
    if not family:
        family.append("unknown or empty BMAD source")
    return family


def target_status(candidate: Candidate) -> str:
    if candidate.source.resolve() == candidate.target.resolve():
        return "adopt"
    if not candidate.target.exists():
        return "copy"
    try:
        if candidate.source.is_file() and candidate.target.is_file() and filecmp.cmp(candidate.source, candidate.target, shallow=False):
            return "same"
    except OSError:
        pass
    return "conflict"


def removed_capability_hits(source: Path) -> list[str]:
    hits: list[str] = []
    for pattern in REMOVED_CAPABILITY_PATTERNS:
        for path in source.glob(f"**/*{pattern}*"):
            if ".git" in path.parts:
                continue
            hits.append(rel(path, source))
    return sorted(set(hits))


def migration_stub_config(project_name: str, track: str, output: Path) -> str:
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    out = output.as_posix()
    return f'''# BMAD Planning & Orchestrator - Project Configuration
# Generated by bmad-migrate: {timestamp}

bmad_version: "6.x"

project:
  name: "{project_name}"
  track: "{track}"
  created: "{timestamp}"
  migrated_from: "claude-bmad"

paths:
  output_folder: "{out}"
  stories_folder: "{out}/stories"
  decision_log: "{out}/decision-log.md"
  project_context: "{out}/project-context.md"

languages:
  communication: "English"
  document_output: "English"

delivery:
  metric: "count-based"
  story_sizing: "one agent session (~2-8h, one dev-day max); split if larger"
'''


def migration_stub_project_context(project_name: str) -> str:
    timestamp = datetime.now(timezone.utc).date().isoformat()
    return f'''# Project Context - {project_name}

> Generated by `bmad-migrate` on {timestamp}. Review and fill gaps before continuing.

## Project Goal

TODO: Summarize the product or feature goal from the migrated BMAD artifacts.

## Primary Users

TODO: Identify primary users and jobs-to-be-done.

## Core Constraints

TODO: Capture technical, business, timeline, compliance, or operational constraints.

## Non-Goals

TODO: List explicit exclusions to prevent planning drift.

## Migrated Sources

Review `migration-report.md` for the source artifact list and any conflicts.
'''


def migration_stub_decision_log(project_name: str, track: str) -> str:
    timestamp = datetime.now(timezone.utc).date().isoformat()
    return f'''# Decision Log - {project_name}

## {timestamp} - Migrated Claude BMAD planning state

- Decision: Adopt migrated BMAD planning artifacts into Codex BMAD layout.
- Track: {track}
- Rationale: Created by `bmad-migrate`; confirm or update after reviewing migrated artifacts.
'''


def build_report(
    source: Path,
    output: Path,
    candidates: list[Candidate],
    family: list[str],
    apply: bool,
    project_name: str,
    track: str,
    removed_hits: list[str],
) -> str:
    groups: dict[str, list[Candidate]] = {"adopt": [], "copy": [], "same": [], "conflict": []}
    for candidate in candidates:
        groups[target_status(candidate)].append(candidate)

    missing_required = []
    for name in ["config.yaml", "project-context.md", "decision-log.md"]:
        if not (output / name).exists() and not any(c.target == output / name for c in candidates):
            missing_required.append(name)

    lines = [
        "# BMAD Migration Report",
        "",
        f"- Source: `{source}`",
        f"- Target: `{output}`",
        f"- Mode: `{'apply' if apply else 'dry-run'}`",
        f"- Source family: {', '.join(family)}",
        f"- Inferred project: `{project_name}`",
        f"- Inferred track: `{track}`",
        "",
        "## Planned Actions",
        "",
        f"- Adopt in place: {len(groups['adopt'])}",
        f"- Copy missing artifacts: {len(groups['copy'])}",
        f"- Already present and identical: {len(groups['same'])}",
        f"- Conflicts requiring review: {len(groups['conflict'])}",
        f"- Create migration stubs: {len(missing_required)}",
        "",
    ]

    for title, key in [
        ("Adopt Existing Compatible Artifacts", "adopt"),
        ("Copy Missing Planning Artifacts", "copy"),
        ("Already Present", "same"),
        ("Conflicts", "conflict"),
    ]:
        lines.extend([f"## {title}", ""])
        items = groups[key]
        if not items:
            lines.extend(["- None.", ""])
            continue
        for item in items:
            note = f" ({item.note})" if item.note else ""
            lines.append(f"- `{item.source}` -> `{item.target}`{note}")
        lines.append("")

    lines.extend(["## Migration Stubs", ""])
    if missing_required:
        for name in missing_required:
            lines.append(f"- `{output / name}`")
    else:
        lines.append("- None.")
    lines.append("")

    lines.extend(["## Removed Claude BMAD Capabilities", ""])
    lines.append("These do not migrate into this planning-only Codex plugin: developer skill, `/dev-story`, implementation review, test execution, lint, coverage, build, and deployment workflows.")
    if removed_hits:
        lines.append("")
        lines.append("Detected possible removed-capability remnants:")
        for hit in removed_hits:
            lines.append(f"- `{hit}`")
    lines.append("")

    lines.extend([
        "## Next Step",
        "",
        "1. Review this report.",
        "2. If acceptable, rerun with `--apply`.",
        "3. Run `bmad:status` / `$bmad-help` after migration.",
        "",
    ])
    return "\n".join(lines)


def apply_migration(
    output: Path,
    candidates: list[Candidate],
    report: str,
    project_name: str,
    track: str,
) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / "stories").mkdir(parents=True, exist_ok=True)

    for candidate in candidates:
        status = target_status(candidate)
        if status not in {"copy", "adopt"}:
            continue
        if status == "adopt":
            continue
        candidate.target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(candidate.source, candidate.target)

    stubs = {
        output / "config.yaml": migration_stub_config(project_name, track, output),
        output / "project-context.md": migration_stub_project_context(project_name),
        output / "decision-log.md": migration_stub_decision_log(project_name, track),
    }
    for path, content in stubs.items():
        if not path.exists():
            path.write_text(content, encoding="utf-8")

    (output / "migration-report.md").write_text(report, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate Claude BMAD artifacts into Codex BMAD layout.")
    parser.add_argument("--source", default=".", help="Source project directory (default: current directory)")
    parser.add_argument("--output", default="bmad-output", help="Target BMAD output directory")
    parser.add_argument("--apply", action="store_true", help="Apply the migration; default is dry-run")
    args = parser.parse_args()

    source = Path(args.source).expanduser().resolve()
    if not source.is_dir():
        raise SystemExit(f"source directory not found: {source}")

    output_arg = Path(args.output).expanduser()
    output = output_arg if output_arg.is_absolute() else (Path.cwd() / output_arg)
    output = output.resolve()

    candidates = discover_candidates(source, output)
    family = detect_source_family(source)
    project_name = infer_project_name(source)
    track = infer_track(source, candidates)
    removed_hits = removed_capability_hits(source)

    report = build_report(source, output, candidates, family, args.apply, project_name, track, removed_hits)
    if args.apply:
        apply_migration(output, candidates, report, project_name, track)
        report = build_report(source, output, candidates, family, args.apply, project_name, track, removed_hits)
        (output / "migration-report.md").write_text(report, encoding="utf-8")

    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
