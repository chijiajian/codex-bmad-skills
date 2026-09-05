"""Offline regressions for the public planning helpers and shipped templates."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/codex-bmad-planning-orchestrator"
sys.path.insert(0, str(PLUGIN / "scripts"))
from planning_contract import scope_prefix, scopes_intersect, story_parts, story_status
from planning_state import detect, recommend
from sequence_sprint import sequence, validate_schedule
from validate_handoff import validate

spec = importlib.util.spec_from_file_location("graph", PLUGIN / "skills/bmad-parallel-plan/scripts/build-dependency-graph.py")
graph = importlib.util.module_from_spec(spec)
spec.loader.exec_module(graph)


class PlanningContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="bmad-contract-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.output = self.root / "planning output"
        self.output.mkdir()

    def write(self, name, content):
        path = self.output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def workspace(self, track="bmad-method", ui=False):
        self.write("config.yaml", f"project:\n  track: '{track}'\n  has_ui: {str(ui).lower()}\n")
        self.write("project-context.md", "# Example product\n")
        self.write("decision-log.md", "Track: enterprise\n")
        self.write("tech-spec.md" if track == "quick-flow" else "prd.md", "# Requirements\nFR-001\nNFR-001\n")
        if track != "quick-flow":
            self.write("architecture.md", "# Architecture\nFR-001\nNFR-001\nRationale and constraints\n")
            self.write("epics.md", "# Epic 1\n")

    def story(self, sid="1.1", status="ready-for-dev", scope="src/auth.py", dependency="none"):
        return self.write(f"stories/{sid}.example.story.md", f"""<!-- ready-for-dev -> in-progress -> review -> done -->
# {sid}: Review feature
**Story ID:** {sid}
**Status:** {status} <!-- lifecycle: backlog -> ready-for-dev -> done -->
## Dependency Maps
- **Blocked by:** {dependency}
## Owned File/Module Scope
- `{scope}`
""")

    def ready(self):
        return self.write("readiness-report.md", "# Readiness\n**Verdict:** PASS\n")

    def command(self, relative, *args, cwd=None):
        return subprocess.run(["sh", str(PLUGIN / relative), *map(str, args)],
                              cwd=cwd or self.root, text=True, capture_output=True)

    def manifest(self):
        return {
            "schemaVersion": "1.0", "generatedAt": "2026-09-05T00:00:00Z",
            "projectName": "Example", "outputFolder": "planning output",
            "stories": [{
                "id": "1.1", "storyFilePath": "planning output/stories/1.1.example.story.md",
                "status": "ready-for-dev", "epic": "1", "storyNumber": "1", "title": "Example",
                "ownedScope": ["src/auth.py"], "wave": 1, "parallelSet": None,
                "dependencies": [], "acceptanceCriteriaSummary": ["The behavior is observable."],
                "lockedSectionsNote": "Sections Acceptance Criteria, Dev Notes, and Testing are LOCKED. External dev tools must not edit them. Populate only the Dev Agent Record section.",
                "devAgentRecord": None,
            }],
        }

    def test_config_track_precedes_legacy_log(self):
        self.workspace("quick-flow")
        self.assertEqual(detect(self.output, self.root)["TRACK"], "quick-flow")

    def test_invalid_config_does_not_silently_use_old_track(self):
        self.workspace("invalid")
        self.assertEqual(detect(self.output, self.root)["TRACK"], "unknown")

    def test_legacy_track_fallback(self):
        self.workspace()
        (self.output / "config.yaml").unlink()
        self.assertEqual(detect(self.output, self.root)["TRACK"], "enterprise")

    def test_canonical_template_status_ignores_lifecycle_comment(self):
        template = (PLUGIN / "skills/bmad-epics-and-stories/templates/story.template.md").read_text()
        path = self.write("story.md", template.replace("**Status:** backlog", "**Status:** ready-for-dev"))
        self.assertEqual(story_status(path), "ready-for-dev")

    def test_all_status_formats_and_invalid_value(self):
        for content, expected in [
            ("status: ready-for-dev\n", "ready-for-dev"),
            ("## Status\n\nready-for-dev\n", "ready-for-dev"),
            ("**Status:** backlog\nThis review is done.\n", "backlog"),
            ("```yaml\nstatus: done\n```\n**Status:** review", "review"),
            ("**Status:** not-ready-for-dev", "unknown"),
        ]:
            with self.subTest(content=content):
                self.assertEqual(story_status(self.write("status.md", content)), expected)

    def test_ux_pair_and_partial_migration(self):
        self.workspace(ui=True)
        self.write("DESIGN.md", "Tokens\n")
        self.write("ux-design.md", "Legacy\n")
        self.assertEqual(recommend(detect(self.output, self.root))[0], "bmad-ux")
        self.write("EXPERIENCE.md", "Journeys\n")
        self.assertEqual(detect(self.output, self.root)["HAS_UX"], 1)
        self.assertEqual(recommend(detect(self.output, self.root))[0], "bmad-readiness-check")

    def test_ui_false_skips_ux(self):
        self.workspace()
        self.assertEqual(recommend(detect(self.output, self.root))[0], "bmad-readiness-check")
        self.write("DESIGN.md", "Legacy visual design")
        self.write("EXPERIENCE.md", "Legacy journeys")
        self.assertEqual(detect(self.output, self.root)["HAS_UI"], "0")

    def test_method_requires_prd_even_if_tech_spec_exists(self):
        self.workspace()
        (self.output / "prd.md").rename(self.output / "tech-spec.md")
        self.assertEqual(recommend(detect(self.output, self.root))[0], "bmad-prd")

    def test_ready_stories_do_not_skip_readiness_or_scheduling(self):
        self.workspace()
        self.story()
        self.assertEqual(recommend(detect(self.output, self.root))[0], "bmad-readiness-check")
        self.ready()
        self.assertEqual(recommend(detect(self.output, self.root))[0], "bmad-sprint-planning")
        self.write("sprint-status.yaml", "stories: []\n")
        self.assertEqual(recommend(detect(self.output, self.root))[0], "bmad-sprint-planning")
        self.write("sprint-status.yaml", json.dumps({"stories": [dict(
            id="1.1", status="ready-for-dev", parallel_set=1,
            dependencies=[], owned_scope=["src/auth.py"],
        )]}))
        self.assertEqual(recommend(detect(self.output, self.root))[0], "bmad-handoff")
        self.write("handoff-manifest.json", json.dumps(self.manifest()))
        self.assertEqual(recommend(detect(self.output, self.root))[0], "(none — handoff complete)")

    def test_failed_unknown_and_stale_readiness(self):
        self.workspace()
        self.story()
        for verdict in ("FAIL", "unknown"):
            self.write("readiness-report.md", "**Verdict:** " + verdict)
            self.assertEqual(recommend(detect(self.output, self.root))[0], "bmad-readiness-check")
        report = self.ready()
        os.utime(report, (1, 1))
        self.assertEqual(detect(self.output, self.root)["READINESS"], "stale")

    def test_shared_phase_router_uses_same_readiness_gate(self):
        self.workspace()
        self.story()
        result = self.command("scripts/check-phase.sh", "--output", self.output)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("NEXT_SKILL=bmad-readiness-check", result.stdout)
        self.assertNotIn("PHASE=handoff-complete", result.stdout)

    def test_config_output_pointer_and_paths_with_spaces(self):
        self.workspace("quick-flow")
        pointer = self.root / "bmad-output/config.yaml"
        pointer.parent.mkdir()
        pointer.write_text('paths:\n  output_folder: "planning output"\n')
        result = self.command("skills/bmad-help/scripts/recommend-next.sh")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("NEXT_SKILL=bmad-readiness-check", result.stdout)

    def test_cancelled_stories_do_not_count_as_unfinished(self):
        self.workspace()
        self.story()
        self.story("1.2", status="cancelled")
        self.ready()
        state = detect(self.output, self.root)
        self.assertEqual((state["STORY_COUNT"], state["READY_COUNT"], state["CANCELLED_COUNT"]), (1, 1, 1))

    def test_scope_globs_and_directory_boundaries(self):
        self.assertIsNotNone(scopes_intersect(["src/auth/**"], ["src/auth/login.ts"]))
        self.assertIsNotNone(scopes_intersect(["src/*.py"], ["src/auth.py"]))
        self.assertIsNone(scopes_intersect(["src/auth/**"], ["src/payments/api.py"]))
        self.assertIsNone(scopes_intersect(["src/auth"], ["src/authorization/file.py"]))
        self.assertIsNotNone(scopes_intersect(["**/*.py"], ["any/file.ts"]))

    def test_scope_rejects_unresolved_or_outside_paths(self):
        for value in ("../secrets", "/tmp/file", "{{path}}", "C:\\outside", "src/../../file"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                scope_prefix(value)

    def test_scope_annotation_and_bold_dependency(self):
        path = self.story(dependency="2.3 — shared interface", scope="src/my folder/file.py")
        path.write_text(path.read_text().replace("- `src/", "- Shared/contended: `src/"))
        self.assertEqual(story_parts(path), (["src/my folder/file.py"], ["2.3"]))

    def test_checker_reports_conflict_and_missing_file(self):
        self.story(scope="src/auth/**")
        self.story("2.1", scope="src/auth/login.ts")
        result = self.command("scripts/scope-conflict-check.sh", "--stories", self.output / "stories", "--format", "json")
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(json.loads(result.stdout)[0]["type"], "conflict")
        result = self.command("scripts/scope-conflict-check.sh", "--story-files", self.output / "missing.story.md")
        self.assertEqual(result.returncode, 2)
        self.assertIn("not found", result.stdout)

    def test_graph_uses_story_status_dependencies_and_glob_conflicts(self):
        self.story(scope="src/auth/**")
        self.story("2.1", scope="src/auth/login.ts", dependency="1.1")
        self.story("3.1", status="backlog")
        nodes, edges, conflicts, blocked = graph.build(self.output / "stories", {}, [])
        self.assertEqual({row["id"] for row in nodes}, {"1.1", "2.1"})
        self.assertIn({"from": "1.1", "to": "2.1", "reason": "depends_on"}, edges)
        self.assertEqual(len(conflicts), 1)
        self.assertFalse(blocked)

    def test_graph_blocks_unknown_prerequisites_and_dependents(self):
        self.story(dependency="9.9")
        self.story("2.1", dependency="1.1")
        nodes, _, _, blocked = graph.build(self.output / "stories", {}, [])
        self.assertFalse(nodes)
        self.assertEqual(len(blocked), 2)

    def test_graph_accepts_completed_prerequisite(self):
        self.story(status="done")
        self.story("2.1", dependency="1.1")
        nodes, _, _, blocked = graph.build(self.output / "stories", {}, [])
        self.assertEqual([row["id"] for row in nodes], ["2.1"])
        self.assertFalse(blocked)

    def test_graph_rejects_duplicate_ids_and_stale_yaml_status(self):
        path = self.story(status="unknown")
        nodes, _, _, blocked = graph.build(self.output / "stories", {"1.1": "ready-for-dev"}, [])
        self.assertFalse(nodes)
        self.assertTrue(blocked)
        self.write("stories/1.1.duplicate.story.md", path.read_text())
        with self.assertRaisesRegex(ValueError, "duplicate story id"):
            graph.build(self.output / "stories", {}, [])

    def test_quick_flow_preflight_requests_semantic_review_without_architecture(self):
        self.workspace("quick-flow")
        result = self.command("skills/bmad-readiness-check/scripts/readiness-check.sh", self.output)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("CONCERNS", result.stdout)
        self.assertNotIn("Missing:", result.stdout)
        self.assertNotIn("unbound", result.stderr)

    def test_readiness_does_not_count_unrelated_requirement_ids(self):
        self.workspace()
        self.write("architecture.md", "FR-999 NFR-999\nArchitecture rationale constraints")
        result = self.command("skills/bmad-readiness-check/scripts/readiness-check.sh", self.output)
        self.assertEqual(result.returncode, 2)
        self.assertIn("fr_coverage=0pct", result.stdout)

    def test_sequence_preserves_readiness_and_dependency_history(self):
        data = {"stories": [
            dict(id="1.1", status="ready-for-dev", dependencies=[], owned_scope=["src/auth/**"]),
            dict(id="2.1", status="ready-for-dev", dependencies=[], owned_scope=["src/auth/login.ts"]),
            dict(id="3.1", status="ready-for-dev", dependencies=["2.1"], owned_scope=["src/payments.py"]),
        ]}
        waves = sequence(data)
        self.assertEqual(waves, {"1.1": 1, "2.1": 2, "3.1": 3})
        self.assertTrue(all(row["status"] == "ready-for-dev" for row in data["stories"]))
        self.assertEqual(data["stories"][2]["dependencies"], ["2.1"])

    def test_sequence_cycle_or_unknown_dependency_leaves_file_intact(self):
        for dependency in ("1.1", "9.9"):
            content = json.dumps({"stories": [dict(id="1.1", status="ready-for-dev", dependencies=[dependency], owned_scope=["src/a.py"])]})
            path = self.write("sprint-status.yaml", content)
            result = self.command("skills/bmad-sprint-planning/scripts/sequence-stories.sh", path)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(path.read_text(), content)

    def test_sequence_cli_reads_source_and_preserves_later_wave_readiness(self):
        first = self.story()
        second = self.story("2.1", dependency="1.1", scope="src/other.py")
        path = self.write("sprint-status.yaml", json.dumps({"custom": "retain", "stories": [
            dict(id="1.1", file=str(first), status="backlog"),
            dict(id="2.1", file=str(second), status="backlog"),
        ]}))
        result = self.command("skills/bmad-sprint-planning/scripts/sequence-stories.sh", path)
        self.assertEqual(result.returncode, 0, result.stderr)
        import yaml
        data = yaml.safe_load(path.read_text())
        self.assertEqual(data["custom"], "retain")
        self.assertEqual([row["status"] for row in data["stories"]], ["ready-for-dev"] * 2)
        self.assertEqual([row["parallel_set"] for row in data["stories"]], [1, 2])
        validate_schedule(data, [first, second])

    def test_schedule_rejects_same_wave_conflicts_and_stale_dependencies(self):
        paths = [self.story(scope="src/auth/**"), self.story("2.1", scope="src/auth/login.py")]
        data = {"stories": [
            dict(id="1.1", status="ready-for-dev", parallel_set=1, dependencies=[], owned_scope=["src/auth/**"]),
            dict(id="2.1", status="ready-for-dev", parallel_set=1, dependencies=[], owned_scope=["src/auth/login.py"]),
        ]}
        with self.assertRaisesRegex(ValueError, "same-wave scope overlap"):
            validate_schedule(data, paths)
        data["stories"][1]["parallel_set"] = 2
        validate_schedule(data, paths)
        self.story("2.1", dependency="1.1", scope="src/auth/login.py")
        with self.assertRaisesRegex(ValueError, "stale dependencies"):
            validate_schedule(data, paths)

    def test_manifest_null_required_field_is_rejected(self):
        manifest = self.manifest()
        validate(manifest)
        manifest["stories"][0]["ownedScope"] = None
        with self.assertRaisesRegex(ValueError, "not of type"):
            validate(manifest)

    def test_manifest_same_wave_overlap_is_rejected(self):
        manifest = self.manifest()
        manifest["stories"].append(dict(manifest["stories"][0], id="2.1", epic="2"))
        with self.assertRaisesRegex(ValueError, "overlapping scopes"):
            validate(manifest)

    def test_manifest_requires_declared_scope_even_for_new_files(self):
        manifest = self.manifest()
        manifest["stories"][0]["ownedScope"] = []
        with self.assertRaisesRegex(ValueError, "missing owned scope"):
            validate(manifest)

    def test_manifest_must_match_source_story_and_scheduled_wave(self):
        self.workspace()
        self.story()
        self.ready()
        self.write("sprint-status.yaml", json.dumps({"stories": [dict(
            id="1.1", status="ready-for-dev", parallel_set=1,
            dependencies=[], owned_scope=["src/auth.py"],
        )]}))
        for key, value in (("ownedScope", ["src/other.py"]), ("wave", 2),
                           ("storyFilePath", "missing.story.md"), ("dependencies", ["9.9"])):
            with self.subTest(key=key):
                manifest = self.manifest()
                manifest["stories"][0][key] = value
                self.write("handoff-manifest.json", json.dumps(manifest))
                self.assertEqual(recommend(detect(self.output, self.root))[0], "bmad-handoff")

    def test_skills_only_install_resolves_shared_helpers(self):
        destination = self.root / "installed skills"
        result = subprocess.run(["sh", str(ROOT / "scripts/install-skills.sh"), "--destination", str(destination)],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.workspace("quick-flow")
        result = subprocess.run(["sh", str(destination / "bmad-help/scripts/detect-state.sh"), str(self.output)],
                                cwd=self.root, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("TRACK=quick-flow", result.stdout)
        candidate = self.write("candidate.json", json.dumps(self.manifest()))
        result = subprocess.run([sys.executable, str(destination / "_bmad-shared/scripts/validate_handoff.py"), str(candidate)],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
