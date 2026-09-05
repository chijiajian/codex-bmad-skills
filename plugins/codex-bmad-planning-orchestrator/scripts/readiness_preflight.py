#!/usr/bin/env python3
"""Advisory artifact checks, followed by the skill's semantic readiness review."""

import argparse
import re
import sys
from pathlib import Path

from planning_contract import text, track_for


def ids(content, prefix):
    return {value.upper() for value in re.findall(r"(?<![\w-])" + prefix + r"-\d+\b", content, re.I)}


def first(output, *patterns):
    for pattern in patterns:
        for path in sorted(output.glob(pattern)):
            if path.is_file() and text(path).strip():
                return path
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", nargs="?", type=Path, default=Path("bmad-output"))
    args = parser.parse_args()
    output = args.output
    track = track_for(output, Path("bmad"))
    quick = track == "quick-flow"
    req = first(output, "tech-spec.md", "planning/tech-spec.md") if quick else first(output, "prd.md", "planning/prd.md")
    arch = first(output, "architecture.md", "solutioning/architecture.md")
    missing = []
    if track == "unknown":
        missing.append("valid project.track in config.yaml")
    if req is None:
        missing.append("tech-spec.md" if quick else "prd.md")
    if not quick and arch is None:
        missing.append("architecture.md")
    if missing:
        print("PRE-FLIGHT VERDICT: FAIL\nMissing: " + ", ".join(missing))
        print("Record the track with $bmad-init; use $bmad-prd / $bmad-tech-spec / $bmad-architecture as applicable.")
        return 2

    requirements = text(req)
    design = text(arch) if arch else requirements
    concerns, failures = [], []
    scores = {}
    for prefix in ("FR", "NFR"):
        required, referenced = ids(requirements, prefix), ids(design, prefix)
        if quick:
            scores[prefix] = "manual"
            concerns.append(prefix + " coverage requires review within the combined tech-spec, not self-reference counting")
        elif not required:
            scores[prefix] = "manual"
            concerns.append(prefix + " identifiers absent; semantic review required")
        else:
            covered = required & referenced
            percentage = len(covered) * 100 // len(required)
            scores[prefix] = str(percentage) + "pct"
            print(f"{prefix}: {len(covered)}/{len(required)} matching IDs; missing: {', '.join(sorted(required - covered)) or 'none'}")
            if percentage < 80:
                failures.append(f"{prefix} identifier coverage below 80%")
            elif percentage < 90:
                concerns.append(f"{prefix} identifier coverage below 90%")

    # These are indicators for human/agent review, not proof of architecture quality.
    indicators = {
        "technical approach": r"technical approach|architectur|component|module",
        "choices and trade-offs": r"rationale|trade.off|alternative|because",
        "constraints": r"constraint|assumption|limitation",
    }
    for label, pattern in indicators.items():
        if not re.search(pattern, design, re.I):
            concerns.append("Review missing " + label + " discussion")
    verdict = "FAIL" if failures else "CONCERNS" if concerns else "PASS"
    for line in failures + concerns:
        print("- " + line)
    print("PRE-FLIGHT VERDICT: " + verdict)
    print(f"SUMMARY: verdict={verdict} fr_coverage={scores['FR']} nfr_coverage={scores['NFR']}")
    print(f"ARTIFACTS: req={req} arch={arch or 'combined-tech-spec'} track={track}")
    print("Pre-flight is advisory. Read the artifacts and write a semantic readiness report before handoff.")
    return {"PASS": 0, "CONCERNS": 1, "FAIL": 2}[verdict]


if __name__ == "__main__":
    sys.exit(main())
