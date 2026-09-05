#!/usr/bin/env python3
"""Validate the handoff schema and dependencies contained in its snapshot."""

import argparse
import json
from pathlib import Path
import sys

from planning_contract import scope_prefix, scopes_intersect, story_id


def schema_path():
    root = Path(__file__).resolve().parent.parent
    native = root / "skills/bmad-handoff/templates/handoff-manifest.schema.json"
    return native if native.is_file() else root.parent / "bmad-handoff/templates/handoff-manifest.schema.json"


def validate(manifest):
    try:
        from jsonschema import Draft202012Validator, FormatChecker
    except ImportError as error:
        raise ValueError("Install jsonschema for this Python interpreter (see repository requirements.txt)") from error
    schema = json.loads(schema_path().read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(manifest), key=lambda error: str(error.path))
    if errors:
        raise ValueError("; ".join(error.message for error in errors))
    stories = {story_id(row["id"]): row for row in manifest["stories"]}
    if len(stories) != len(manifest["stories"]):
        raise ValueError("duplicate story ids in manifest")
    for sid, row in stories.items():
        if not row["ownedScope"]:
            raise ValueError("missing owned scope: " + sid)
        scope_prefix(row["storyFilePath"])
        for scope in row["ownedScope"]:
            scope_prefix(scope)
        for dependency in row["dependencies"]:
            dependency = story_id(dependency)
            if dependency in stories and stories[dependency]["wave"] >= row["wave"]:
                raise ValueError(f"{sid}: dependency {dependency} must precede its wave")
    rows = list(stories.values())
    for i, row in enumerate(rows):
        for other in rows[i + 1:]:
            if row["wave"] == other["wave"] and scopes_intersect(row["ownedScope"], other["ownedScope"]):
                raise ValueError(f"overlapping scopes in wave {row['wave']}: {row['id']}, {other['id']}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        validate(json.loads(args.manifest.read_text(encoding="utf-8")))
        print("Handoff manifest is valid.")
    except (OSError, ValueError) as error:
        print("ERROR: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
