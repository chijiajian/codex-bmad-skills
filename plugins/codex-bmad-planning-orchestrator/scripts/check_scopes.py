#!/usr/bin/env python3
"""Check declared story scopes without accessing application files."""

import argparse
import json
import sys
from pathlib import Path

from planning_contract import scope_prefix, scopes_intersect, story_id, story_parts, story_status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--stories", type=Path)
    source.add_argument("--story-files", type=Path, nargs="+")
    parser.add_argument("--ids", default="")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()
    if args.stories and not args.stories.is_dir():
        parser.error("stories directory does not exist")
    files = sorted(args.stories.glob("*.story.md")) if args.stories else args.story_files
    selected = {story_id(value.strip()) for value in args.ids.split(",") if value.strip()}
    scopes, results, seen = {}, [], set()

    def blocked(sid, reason):
        results.append(dict(type="blocked", a=sid, b="", path="", reason=reason))

    for path in files:
        sid = story_id(path.name.removesuffix(".story.md"))
        if selected and sid not in selected:
            continue
        if sid in seen:
            blocked(sid, "duplicate story id")
            continue
        seen.add(sid)
        if not path.is_file():
            blocked(sid, "story file not found")
            continue
        if story_status(path) in {"done", "cancelled"}:
            continue
        scope, _ = story_parts(path)
        try:
            if not scope:
                raise ValueError("no Owned File/Module Scope declared")
            for value in scope:
                scope_prefix(value)
            scopes[sid] = scope
        except ValueError as error:
            blocked(sid, str(error))
    for sid in selected - seen:
        blocked(sid, "requested story id not found")
    if not files and not selected:
        blocked("", "no story files found")
    ids = list(scopes)
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            overlap = scopes_intersect(scopes[a], scopes[b])
            results.append(dict(type="conflict" if overlap else "ok", a=a, b=b,
                                path=" overlaps ".join(overlap) if overlap else "",
                                reason="reserved-scope-overlap" if overlap else ""))
    if args.format == "json":
        print(json.dumps(results))
    else:
        for row in results:
            print(f"{row['type'].upper()}: {row['a']} {row['b']} {row['path']} {row['reason']}".strip())
        print("Overlapping or unresolved scopes must be serialized or clarified.")
    return 2 if any(row["type"] != "ok" for row in results) else 0


if __name__ == "__main__":
    sys.exit(main())
