"""Shared, read-only parsing for BMAD planning artifacts (Python 3.9+).

Globs reserve their fixed directory prefix. This is deliberately conservative:
planned paths need not exist yet, and two arbitrary glob languages are not
assumed disjoint just because their strings differ.
"""

import re
import shlex
from pathlib import PurePosixPath

STATUSES = {"backlog", "ready-for-dev", "in-progress", "review", "done", "cancelled"}
TRACKS = {"quick-flow", "bmad-method", "enterprise"}


def text(path):
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def scalar(path, key):
    """Read a scalar from the simple project/config YAML contract, never eval it."""
    for line in text(path).splitlines():
        match = re.match(r"^\s*" + re.escape(key) + r":\s*(.*?)\s*$", line)
        if match:
            try:
                return " ".join(shlex.split(match[1], comments=True))
            except ValueError:
                return ""
    return ""


def normalize_track(value):
    value = re.sub(r"[ _]+", "-", value.strip().lower())
    return value if value in TRACKS else "unknown"


def track_for(output, compatibility=None):
    configured = scalar(output / "config.yaml", "track")
    if configured:
        return normalize_track(configured)
    log = text(output / "decision-log.md")
    matches = re.findall(
        r"\btrack\s*[:=]\s*[*`\"']*(quick[- _]flow|bmad[- _]method|enterprise)\b",
        log, re.I,
    )
    if matches:
        return normalize_track(matches[-1])
    if compatibility:
        for name in ("workflow-status.yaml", "project.yaml"):
            value = scalar(compatibility / name, "track")
            if value:
                return normalize_track(value)
    return "unknown"


def field_value(content, name, values):
    """Read a named field or heading; ignore examples in comments/code fences."""
    content = re.sub(r"<!--.*?-->", "", content, flags=re.S)
    content = re.sub(r"^```.*?^```[^\n]*", "", content, flags=re.M | re.S)
    awaiting = False
    for raw in content.splitlines():
        line = raw.strip().replace("**", "").replace("`", "")
        match = re.match(r"^" + re.escape(name) + r"\s*:\s*(.*)$", line, re.I)
        if match:
            candidate = match[1].strip().strip("\"'").split()
            value = candidate[0].lower() if candidate else ""
            return value if value in values else "unknown"
        if re.fullmatch(r"#{1,6}\s+" + re.escape(name), line, re.I):
            awaiting = True
            continue
        if awaiting and line:
            value = line.split()[0].lower()
            return value if value in values else "unknown"
    return "unknown"


def story_status(path):
    return field_value(text(path), "status", STATUSES)


def story_id(value):
    match = re.match(r"^(\d+)\.(\d+)(?:\.|$)", str(value))
    return ".".join(match.groups()) if match else str(value)


def story_parts(path):
    """Read canonical scope bullets and Blocked by/depends_on dependencies."""
    section = ""
    scopes, dependencies = [], []
    content = re.sub(r"<!--.*?-->", "", text(path), flags=re.S)
    for line in content.splitlines():
        heading = re.match(r"^#{1,6}\s+(.+)", line)
        if heading:
            section = heading[1].lower()
            continue
        bullet = re.match(r"^\s*[-*]\s+(.+)", line)
        if not bullet:
            continue
        item = bullet[1]
        if "owned file" in section or "module scope" in section:
            code = re.findall(r"`([^`]+)`", item)
            value = code[0] if len(code) == 1 else item.split(" #", 1)[0].strip()
            if value.lower() not in {"none", "n/a"}:
                scopes.append(value)
        elif "dependency map" in section or section == "dependencies":
            plain = item.replace("**", "").replace("`", "")
            if re.match(r"^(blocked by|depends_on|depends on)\s*:", plain, re.I):
                dependencies.extend(re.findall(r"\b\d+\.\d+\b", plain))
    return list(dict.fromkeys(scopes)), list(dict.fromkeys(dependencies))


def scope_prefix(value):
    """Validate a repository-relative scope and return its reserved prefix."""
    value = value.strip().replace("\\", "/")
    if not value or value.startswith("/") or re.match(r"^[A-Za-z]:", value):
        raise ValueError("scope must be a nonempty repository-relative path")
    if any(marker in value for marker in ("{{", "}}", "${", "\n", "\r")):
        raise ValueError("unresolved or malformed scope")
    parts = []
    wildcard = False
    for part in PurePosixPath(value).parts:
        if part == "..":
            raise ValueError("scope may not traverse parent directories")
        if any(char in part for char in "*?[]{}"):
            wildcard = True
        if not wildcard:
            parts.append(part)
    return "/".join(parts)


def scopes_intersect(left, right):
    for x in left:
        px = scope_prefix(x)
        for y in right:
            py = scope_prefix(y)
            if not px or not py or px == py or px.startswith(py + "/") or py.startswith(px + "/"):
                return x, y
    return None
