#!/usr/bin/env python3
"""
build-dependency-graph.py  -  BMAD Parallel Plan

Read a directory of story files, taking lifecycle, scope and dependencies from the
canonical Markdown headers and sections ({epic}.{story}.{slug}.story.md), then emit a dependency DAG as JSON:

  - nodes          : one per wave-eligible story  {id, slug, epic, status, scope}
  - ordering_edges : directed constraints  {from, to, reason}
        * intra-epic sequence  (stories within an epic are usually sequential)
        * explicit depends_on  (from each story's Dependency Maps section)
  - conflicts      : undirected mutual-exclusion pairs  {a, b, class, detail}
        * class "file"     : Owned File/Module Scopes intersect
        * class "semantic" : both touch a shared/cross-cutting module (see --shared)
  - blocked        : ready stories excluded for missing scope  {id, reason}

PLANS ONLY. Read-only. Does not run git, agents, or tests.

Usage:
  build-dependency-graph.py --status sprint-status.yaml --stories ./stories \
      --out dependency-graph.json [--max-parallel 3] [--shared src/auth src/db]

The --status argument is retained for CLI compatibility. Its YAML values cannot
override story headers or establish completion of a missing prerequisite.
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Locate shared helpers in plugin and skills-only installations.
_here = Path(__file__).resolve()
_shared = _here.parents[3] / "scripts"
if not (_shared / "planning_contract.py").is_file():
    _shared = _here.parents[2] / "_bmad-shared" / "scripts"
sys.path.insert(0, str(_shared))
from planning_contract import scope_prefix, scopes_intersect, story_id, story_parts, story_status

STORY_RE = re.compile(r"^(\d+)\.(\d+)\.(.+)\.story\.md$")


# --------------------------------------------------------------------------- #
# sprint-status.yaml  ->  {story_id: status}
# --------------------------------------------------------------------------- #
def load_status_map(status_path):
    """Return {id: status}. Tolerant: works with or without PyYAML."""
    p = Path(status_path)
    text = p.read_text(encoding="utf-8") if p.is_file() else ""
    if not text.strip():
        return {}
    try:
        import yaml  # type: ignore
        data = yaml.safe_load(text) or {}
        return _status_from_yaml(data)
    except Exception:
        return _status_from_lines(text)


def _status_from_yaml(data):
    out = {}

    def walk(node):
        if isinstance(node, dict):
            sid, st = node.get("id"), node.get("status")
            if sid is not None and st is not None:
                out[str(sid)] = str(st).strip()
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(data)
    return out


def _status_from_lines(text):
    """Fallback: pair the nearest preceding `id:` with a following `status:`."""
    out, cur = {}, None
    for raw in text.splitlines():
        line = raw.split("#", 1)[0]
        m = re.search(r'(?:^|[\s-])id:\s*["\']?([\w.\-]+)["\']?', line)
        if m:
            cur = m.group(1)
            continue
        m = re.search(r'status:\s*["\']?([\w\-]+)["\']?', line)
        if m and cur is not None:
            out[cur] = m.group(1)
            cur = None
    return out


# --------------------------------------------------------------------------- #
# story markdown -> scope[] and depends_on[]
# --------------------------------------------------------------------------- #
def parse_story(path):
    """Return (scope_paths, depends_on_ids) for one story file."""
    return story_parts(path)


# --------------------------------------------------------------------------- #
# graph assembly
# --------------------------------------------------------------------------- #
ELIGIBLE = {"ready-for-dev", "in-progress", "review"}


def shared_touch(scope, shared):
    return [item for item in shared if scopes_intersect(scope, [item])]


def build(stories_dir, status_map, shared):
    # Markdown owns lifecycle; stale YAML must not promote incomplete documents.
    status_map = {}
    for path in Path(stories_dir).glob("*.story.md"):
        sid = story_id(path.name.removesuffix(".story.md"))
        if sid in status_map:
            raise ValueError("duplicate story id: " + sid)
        status_map[sid] = story_status(path)
    nodes, blocked = [], []
    scope_by_id, deps_by_id, epic_members = {}, {}, {}

    for f in sorted(Path(stories_dir).glob("*.story.md")):
        m = STORY_RE.match(f.name)
        if not m:
            continue
        epic, story, slug = int(m.group(1)), int(m.group(2)), m.group(3)
        sid = f"{epic}.{story}"
        status = status_map.get(sid, "unknown")
        if status == "unknown":
            blocked.append({"id": sid, "reason": "missing or invalid story status"})
            continue
        if status not in ELIGIBLE:
            continue

        scope, deps = parse_story(f)
        if not scope:
            blocked.append({"id": sid, "reason": "no Owned File/Module Scope declared"})
            continue

        try:
            for value in scope:
                scope_prefix(value)
        except ValueError as error:
            blocked.append({"id": sid, "reason": str(error)})
            continue

        nodes.append({"id": sid, "slug": slug, "epic": epic,
                      "status": status, "scope": scope})
        scope_by_id[sid] = scope
        deps_by_id[sid] = deps
        epic_members.setdefault(epic, []).append((story, sid))

    # Missing/backlog/cancelled dependencies block the story and its dependents.
    while True:
        invalid = {sid for sid, deps in deps_by_id.items()
                   if any(dep not in scope_by_id and status_map.get(dep) != "done" for dep in deps)}
        if not invalid:
            break
        for sid in invalid:
            blocked.append({"id": sid, "reason": "dependency missing, cancelled, backlog, or blocked"})
            scope_by_id.pop(sid)
            deps_by_id.pop(sid)
        nodes = [node for node in nodes if node["id"] not in invalid]
        epic_members = {epic: [(number, sid) for number, sid in members if sid not in invalid]
                        for epic, members in epic_members.items()}
    valid = set(scope_by_id)

    # ordering edges: intra-epic sequence + explicit depends_on
    ordering, seen = [], set()

    def add_edge(frm, to, reason):
        k = (frm, to)
        if k not in seen:
            seen.add(k)
            ordering.append({"from": frm, "to": to, "reason": reason})

    for members in epic_members.values():
        members.sort()
        for (_, id_prev), (_, id_next) in zip(members, members[1:]):
            add_edge(id_prev, id_next, "intra-epic-sequence")
    for sid, deps in deps_by_id.items():
        for d in deps:
            if d in valid:
                add_edge(d, sid, "depends_on")

    # undirected conflicts: file overlap, else shared-module semantic
    conflicts = []
    ids = [n["id"] for n in nodes]
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = ids[i], ids[j]
            hit = scopes_intersect(scope_by_id[a], scope_by_id[b])
            if hit:
                conflicts.append({"a": a, "b": b, "class": "file",
                                  "detail": f"{hit[0]} / {hit[1]}"})
            elif shared:
                common = set(shared_touch(scope_by_id[a], shared)) & \
                         set(shared_touch(scope_by_id[b], shared))
                if common:
                    conflicts.append({"a": a, "b": b, "class": "semantic",
                                      "detail": "shared:" + ",".join(sorted(common))})

    return nodes, ordering, conflicts, blocked


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build the BMAD story dependency DAG (JSON).")
    ap.add_argument("--status", default="sprint-status.yaml")
    ap.add_argument("--stories", default="stories")
    ap.add_argument("--out", default="dependency-graph.json")
    ap.add_argument("--max-parallel", type=int, default=3)
    ap.add_argument("--shared", nargs="*", default=[],
                    help="Shared/cross-cutting module paths from architecture.md")
    args = ap.parse_args(argv)

    sdir = Path(args.stories)
    if not sdir.is_dir():
        print(f"error: stories directory not found: {sdir}", file=sys.stderr)
        return 2

    status_map = load_status_map(args.status)
    try:
        nodes, ordering, conflicts, blocked = build(sdir, status_map, args.shared)
    except ValueError as error:
        print("error: " + str(error), file=sys.stderr)
        return 2

    graph = {
        "max_parallel": args.max_parallel,
        "nodes": nodes,
        "ordering_edges": ordering,
        "conflicts": conflicts,
        "blocked": blocked,
    }
    text = json.dumps(graph, indent=2)
    Path(args.out).write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"\n[build-dependency-graph] {len(nodes)} eligible, "
          f"{len(ordering)} ordering edges, {len(conflicts)} conflicts, "
          f"{len(blocked)} blocked -> {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
