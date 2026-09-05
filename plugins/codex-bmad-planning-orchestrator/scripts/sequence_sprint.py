#!/usr/bin/env python3
"""Assign dependency-ordered, scope-disjoint waves to a sprint scheduling view."""

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import sys
import tempfile

from planning_contract import scope_prefix, scopes_intersect, story_id, story_parts, story_status


def validate_schedule(data, story_paths):
    """Reject stale/incomplete scheduling rows and unsafe existing wave assignments."""
    if not isinstance(data, dict) or not isinstance(data.get("stories"), list):
        raise ValueError("sprint status must contain a stories list")
    rows = data["stories"]
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError("each scheduling row must be a mapping")
    by_id = {story_id(row.get("id", "")): row for row in rows}
    if len(by_id) != len(rows):
        raise ValueError("duplicate scheduling ids")
    expected = {story_id(path.name.removesuffix(".story.md")): path for path in story_paths}
    if len(expected) != len(story_paths):
        raise ValueError("duplicate story file ids")
    if set(by_id) != set(expected):
        raise ValueError("scheduling rows do not match story files")
    active = {}
    for sid, path in expected.items():
        row, status = by_id[sid], story_status(path)
        if status == "unknown":
            raise ValueError("missing or invalid story status: " + sid)
        if row.get("status") != status:
            raise ValueError("stale lifecycle mirror: " + sid)
        if status in {"done", "cancelled", "backlog"}:
            continue
        scope, dependencies = story_parts(path)
        if not scope or row.get("owned_scope") != scope:
            raise ValueError("missing or stale scope: " + sid)
        row_deps = row.get("dependencies")
        if not isinstance(row_deps, list) or {story_id(dep) for dep in row_deps} != set(dependencies):
            raise ValueError("missing or stale dependencies: " + sid)
        for value in scope:
            scope_prefix(value)
        if type(row.get("parallel_set")) is not int or row["parallel_set"] < 1:
            raise ValueError("missing wave: " + sid)
        active[sid] = row
    for sid, row in active.items():
        for dep in row["dependencies"]:
            dep = story_id(dep)
            if dep not in by_id:
                raise ValueError("unknown prerequisite: " + dep)
            if by_id[dep]["status"] == "done":
                continue
            if dep not in active or active[dep]["parallel_set"] >= row["parallel_set"]:
                raise ValueError("unsatisfied prerequisite ordering: " + sid)
    ids = list(active)
    for i, sid in enumerate(ids):
        for other in ids[i + 1:]:
            left, right = active[sid], active[other]
            if left["parallel_set"] == right["parallel_set"] and scopes_intersect(left["owned_scope"], right["owned_scope"]):
                raise ValueError("same-wave scope overlap: " + sid + ", " + other)


def sequence(data):
    rows = data.get("stories", [])
    if not isinstance(rows, list) or not rows:
        raise ValueError("stories must be a nonempty list")
    by_id = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("each scheduling row must be a mapping")
        sid = story_id(row.get("id", ""))
        if not sid or sid in by_id:
            raise ValueError("missing or duplicate story id: " + sid)
        by_id[sid] = row
        if row.get("file"):
            path = Path(row["file"])
            if not path.is_file():
                raise ValueError("story file not found: " + str(path))
            if sid != story_id(path.name.removesuffix(".story.md")):
                raise ValueError("story id does not match its file: " + sid)
            row["status"] = story_status(path)
            row["owned_scope"], row["dependencies"] = story_parts(path)
        if row.get("status") not in {"backlog", "ready-for-dev", "in-progress", "review", "done", "cancelled"}:
            raise ValueError("missing or invalid status: " + sid)
    active = {sid for sid, row in by_id.items() if row["status"] in {"ready-for-dev", "in-progress", "review"}}
    dependencies = {}
    for sid in active:
        row = by_id[sid]
        scope = row.get("owned_scope")
        if not isinstance(scope, list) or not scope or not all(isinstance(item, str) for item in scope):
            raise ValueError("missing or invalid owned_scope: " + sid)
        for item in scope:
            scope_prefix(item)
        deps = row.get("dependencies", [])
        if not isinstance(deps, list):
            raise ValueError("dependencies must be a list: " + sid)
        dependencies[sid] = {story_id(dep) for dep in deps}
        for dep in dependencies[sid]:
            if dep not in by_id or (dep not in active and by_id[dep]["status"] != "done"):
                raise ValueError(f"{sid}: dependency {dep} is missing or not ready")

    waves = {}
    remaining = set(active)
    while remaining:
        available = sorted(sid for sid in remaining if not ((dependencies[sid] & active) - waves.keys()))
        if not available:
            raise ValueError("dependency cycle: " + ", ".join(sorted(remaining)))
        for sid in available:
            wave = 1 + max((waves[dep] for dep in dependencies[sid] if dep in waves), default=0)
            while any(other_wave == wave and scopes_intersect(by_id[sid]["owned_scope"], by_id[other]["owned_scope"])
                      for other, other_wave in waves.items()):
                wave += 1
            waves[sid] = wave
            remaining.remove(sid)
    for sid, row in by_id.items():
        row["parallel_set"] = waves.get(sid)
    data["last_updated"] = datetime.now(timezone.utc).isoformat()
    return waves


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("status_file", nargs="?", type=Path, default=Path("bmad-output/sprint-status.yaml"))
    args = parser.parse_args()
    try:
        import yaml
    except ImportError:
        parser.exit(1, "Install PyYAML for this Python interpreter (see repository requirements.txt).\n")
    try:
        data = yaml.safe_load(args.status_file.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("sprint status must be a YAML mapping")
        waves = sequence(data)
        output = yaml.safe_dump(data, allow_unicode=True, sort_keys=False)
        # Validate the complete plan before replacing the generated scheduling view.
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=args.status_file.parent, delete=False) as file:
                temporary = Path(file.name)
                file.write(output)
            temporary.chmod(args.status_file.stat().st_mode)
            os.replace(temporary, args.status_file)
        finally:
            if temporary and temporary.exists():
                temporary.unlink()
        for wave in sorted(set(waves.values())):
            print(f"Wave {wave}: " + ", ".join(sid for sid, value in waves.items() if value == wave))
        print("Scheduling view updated; ready-for-dev describes document readiness, not satisfied dependencies.")
        return 0
    except (OSError, ValueError, TypeError, yaml.YAMLError) as error:
        print("ERROR: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
