"""Adversarial controls for the repository-owned browser workflow helper."""

from contextlib import redirect_stdout
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from tools.chat_workflow import Invalid, Project, main


class ChatWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repo"
        self.root.mkdir()
        self.write("CHATGPT-START-HERE.md", "Read the current state and actual repository instructions.\n")
        self.write("AGENTS.md", "Preserve existing evidence and verify actual changes.\n")
        self.write("evidence/result.txt", "A retained observed result.\n")
        self.write(".agents/skills/continue-project/SKILL.md", "---\nname: continue-project\ndescription: Continue one bounded task from current state.\n---\nRead the current sources.\n")
        self.registry = {
            "schema_version": 1, "repository": "Omegapy/OntoKin", "entrypoint": "CHATGPT-START-HERE.md",
            "required_reads": ["CHATGPT-START-HERE.md", "AGENTS.md"],
            "skills": [{"id": "continue-project", "path": ".agents/skills/continue-project/SKILL.md", "when": "Resume a task"}],
            "task_root": "docs/workflow/tasks", "memory": "docs/workflow/memory.json",
            "knowledge": "docs/workflow/knowledge.json", "current": "docs/workflow/CURRENT.json",
        }
        self.current = {
            "schema_version": 1, "project": "Omegapy/OntoKin", "latest_task": "C263", "active_task": "C263",
            "observed_main": "1" * 40, "snapshot_date": "2026-11-18T20:00:00Z",
            "next_action": {"status": "awaiting_user_direction", "summary": "Await the next selected task",
                            "suggested_task": "Source observer", "sources": ["AGENTS.md"]},
            "historical_handoff": {"url": "https://chatgpt.com/library?file_id=example", "sha256": "2" * 64,
                                   "bytes": 100, "scope": "Historical recovery only"},
            "boundaries": ["No scientific release qualification"],
        }
        self.task = {
            "schema_version": 1, "id": "C263", "title": "Workflow", "intent": "Reliable browser continuation",
            "status": "in_progress", "owner": "root-test", "branch": "work/c263", "base_sha": "1" * 40,
            "requirements": [{"id": "R01", "description": "Explicit startup", "acceptance": "Entry file exists",
                              "status": "not_done", "evidence": []}],
            "plan": [{"id": "P01", "title": "Implement startup", "requirements": ["R01"], "status": "in_progress",
                      "artifacts": ["future.md"], "verification": ["Inspect the entry"]}],
            "checks": [], "completion": {"implementation_commit": None, "merge_commit": None, "pull_request": None,
                                          "branch_disposition": "active", "evidence": []},
            "next_action": "Finish and verify startup",
        }
        self.memory = {"schema_version": 1, "records": [{"id": "M01", "kind": "lesson", "summary": "Load instructions explicitly",
                        "status": "current", "sources": ["AGENTS.md"], "scope": "Browser workflow",
                        "recorded_at": "2026-11-18", "supersedes": None}]}
        self.knowledge = {
            "schema_version": 1,
            "terms": [{"id": "K01", "term": "Source authority", "definition": "Accepted source owns meaning",
                       "authority": ["AGENTS.md#preservation"], "status": "current"}],
            "capabilities": [{"id": "CAP01", "name": "Workflow lookup", "description": "Literal source-backed lookup",
                              "status": "partial", "sources": ["AGENTS.md"], "limits": "No inference"}],
            "relationships": [{"subject": "CAP01", "relation": "uses", "object": "K01", "source": "AGENTS.md"}],
        }
        self.save()

    def write(self, path, content):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def save(self):
        for path, value in (("docs/workflow/registry.json", self.registry), ("docs/workflow/CURRENT.json", self.current),
                            ("docs/workflow/tasks/C263/task.json", self.task), ("docs/workflow/memory.json", self.memory),
                            ("docs/workflow/knowledge.json", self.knowledge)):
            self.write(path, json.dumps(value))

    def check(self):
        self.save()
        return Project(self.root).validate()

    def rejected(self, fragment):
        report = self.check()
        self.assertFalse(report["passed"], report)
        self.assertIn(fragment, "\n".join(report["errors"]))

    def completed(self):
        self.task["status"] = "done"
        self.task["requirements"][0].update(status="done", evidence=["evidence/result.txt"])
        self.task["plan"][0].update(status="done", artifacts=["CHATGPT-START-HERE.md"])
        self.task["checks"] = [{"name": "Startup", "command": "inspect startup", "result": "passed",
                                "required": True, "evidence": ["evidence/result.txt"]}]
        self.task["completion"] = {"implementation_commit": "3" * 40, "merge_commit": "4" * 40,
                                   "pull_request": "https://github.com/Omegapy/OntoKin/pull/253",
                                   "branch_disposition": "deleted", "evidence": ["evidence/result.txt"]}
        self.current["active_task"] = None

    def run_cli(self, *args):
        output = io.StringIO()
        with redirect_stdout(output):
            code = main(["--root", str(self.root), *args])
        return code, output.getvalue()

    def snapshot(self):
        return {p.relative_to(self.root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in self.root.rglob("*") if p.is_file()}

    def test_valid_active_and_done_records(self):
        self.assertTrue(self.check()["passed"])
        self.completed()
        self.assertTrue(self.check()["passed"])
        self.task["completion"]["branch_disposition"] = "deletion_pending"
        self.assertTrue(self.check()["passed"])

    def test_unknown_schema_and_duplicate_json_keys(self):
        self.registry["schema_version"] = True
        self.rejected("unsupported schema_version")
        self.registry["schema_version"] = 1
        self.save()
        self.write("docs/workflow/registry.json", '{"schema_version":1,"schema_version":1}')
        self.assertIn("duplicate JSON key", " ".join(Project(self.root).validate()["errors"]))

    def test_bad_json_and_top_level_shapes(self):
        for value in ("{bad", "null", "[]"):
            with self.subTest(value=value):
                self.write("docs/workflow/registry.json", value)
                code, output = self.run_cli("check", "--json")
                self.assertEqual(code, 1)
                self.assertFalse(json.loads(output)["passed"])

    def test_path_traversal_absolute_and_backslash_rejected(self):
        for value in ("../outside.md", "/etc/passwd", "docs/../AGENTS.md", "docs\\AGENTS.md", "docs//file.md"):
            with self.subTest(value=value):
                self.registry["entrypoint"] = value
                self.rejected("path")

    def test_missing_read_and_symlink_escape_rejected(self):
        self.registry["required_reads"].append("missing.md")
        self.rejected("missing file")
        self.registry["required_reads"].pop()
        outside = Path(self.temp.name) / "outside.md"
        outside.write_text("outside")
        (self.root / "escape.md").symlink_to(outside)
        self.registry["required_reads"].append("escape.md")
        self.rejected("path escapes")

    def test_malformed_skill_frontmatter_rejected(self):
        for value in ("no frontmatter", "---\nname: wrong\ndescription: valid\n---", "---\nname: continue-project\ndescription:\n---"):
            with self.subTest(value=value):
                self.write(self.registry["skills"][0]["path"], value)
                self.assertFalse(self.check()["passed"])

    def test_duplicate_skill_and_requirement_ids_rejected(self):
        self.registry["skills"].append(deepcopy(self.registry["skills"][0]))
        self.rejected("duplicate id")
        self.registry["skills"].pop()
        self.task["requirements"].append(deepcopy(self.task["requirements"][0]))
        self.rejected("duplicate id")

    def test_plan_must_cover_requirements_without_unknown_ids(self):
        self.task["requirements"].append({"id": "R02", "description": "Recovery", "acceptance": "Recovery present",
                                           "status": "not_done", "evidence": []})
        self.rejected("requirements missing from plan: R02")
        self.task["plan"][0]["requirements"].append("R99")
        self.rejected("unknown requirement R99")

    def test_task_pointers_malformed_and_missing_rejected(self):
        for value in ("missing", ["C263"], {"id": "C263"}, 42):
            with self.subTest(value=value):
                self.current["active_task"] = value
                code, output = (None, None)
                self.save()
                code, output = self.run_cli("check", "--json")
                self.assertEqual(code, 1)
                self.assertTrue(json.loads(output)["errors"])

    def test_active_task_cannot_be_completed(self):
        self.completed()
        self.current["active_task"] = "C263"
        self.rejected("cannot be active")

    def test_done_requires_all_requirements_and_steps(self):
        self.completed()
        self.task["requirements"][0]["status"] = "not_done"
        self.rejected("unfinished requirement")
        self.task["requirements"][0]["status"] = "done"
        self.task["plan"][0]["status"] = "in_progress"
        self.rejected("unfinished plan")

    def test_done_requires_actual_artifact_and_evidence_paths(self):
        self.completed()
        self.task["plan"][0]["artifacts"] = ["missing.md"]
        self.rejected("missing file")
        self.task["plan"][0]["artifacts"] = ["AGENTS.md"]
        self.task["requirements"][0]["evidence"] = []
        self.rejected("must not be empty")

    def test_done_requires_passing_required_checks(self):
        self.completed()
        for value in ([], [{"name": "Test", "command": "test", "result": "not_run", "required": True, "evidence": []}],
                      [{"name": "Test", "command": "test", "result": "failed", "required": True, "evidence": ["evidence/result.txt"]}]):
            with self.subTest(value=value):
                self.task["checks"] = value
                self.rejected("passing recorded required checks")

    def test_check_requires_evidence_and_boolean_flag(self):
        self.completed()
        self.task["checks"][0]["required"] = "true"
        self.rejected("expected Boolean")
        self.task["checks"][0]["required"] = True
        self.task["checks"][0]["evidence"] = []
        self.rejected("must not be empty")

    def test_done_rejects_unmerged_or_wrong_project_claims(self):
        self.completed()
        self.task["completion"]["merge_commit"] = None
        self.rejected("40 lowercase")
        self.task["completion"]["merge_commit"] = "4" * 40
        self.task["completion"]["pull_request"] = "https://github.com/example/other/pull/1"
        self.rejected("must identify an OntoKin PR")
        self.task["completion"]["pull_request"] = "https://github.com/Omegapy/OntoKin/pull/253"
        self.task["completion"]["branch_disposition"] = "active"
        self.rejected("branch cleanup disposition")

    def test_memory_requires_evidence_and_acyclic_supersession(self):
        self.memory["records"][0]["sources"] = []
        self.rejected("must not be empty")
        self.memory["records"][0]["sources"] = ["AGENTS.md"]
        other = deepcopy(self.memory["records"][0])
        other.update(id="M02", supersedes="M01")
        self.memory["records"][0]["supersedes"] = "M02"
        self.memory["records"].append(other)
        self.rejected("supersedes cycle")

    def test_knowledge_relationships_must_reference_known_ids(self):
        self.knowledge["relationships"][0]["object"] = "unknown"
        self.rejected("unknown knowledge ID")

    def test_external_sources_are_https_and_never_fetched(self):
        self.memory["records"][0]["sources"] = ["https://example.invalid/evidence"]
        self.assertTrue(self.check()["passed"])
        for value in ("http://example.com/evidence", "https://user:secret@example.com/evidence", "https://bad%host/evidence"):
            with self.subTest(value=value):
                self.memory["records"][0]["sources"] = [value]
                self.assertFalse(self.check()["passed"])

    def test_required_timestamp_has_explicit_utc(self):
        for value in ("yesterday", "2026-11-18", "2026-11-18T12:00:00-07:00"):
            with self.subTest(value=value):
                self.current["snapshot_date"] = value
                self.rejected("timestamp")

    def test_lookup_returns_original_sources_and_no_inference(self):
        code, output = self.run_cli("lookup", "SOURCE", "--json")
        self.assertEqual(code, 0)
        result = json.loads(output)
        self.assertEqual({m["kind"] for m in result["matches"]}, {"term", "capability"})
        self.assertIn("no inference", result["method"])
        self.assertTrue(all("sources" in m["record"] or "authority" in m["record"] for m in result["matches"]))
        code, output = self.run_cli("lookup", "nonexistent", "--json")
        self.assertEqual(json.loads(output)["matches"], [])

    def test_read_commands_preserve_all_file_bytes(self):
        before = self.snapshot()
        for args in (("check", "--json"), ("brief", "--json"), ("lookup", "source", "--json")):
            with self.subTest(args=args):
                code, output = self.run_cli(*args)
                self.assertEqual(code, 0, output)
                self.assertIn("Local structural", json.loads(output)["notice"])
                self.assertEqual(before, self.snapshot())

    def test_new_task_is_unselected_draft_and_refuses_overwrite(self):
        before = (self.root / "docs/workflow/CURRENT.json").read_bytes()
        code, output = self.run_cli("new-task", "C264", "--title", "Source observer", "--intent", "Observe source", "--json")
        self.assertEqual(code, 0, output)
        result = json.loads(output)
        self.assertFalse(result["selected"])
        self.assertEqual(result["created_files"], ["docs/workflow/tasks/C264/task.json",
                                                "docs/workflow/tasks/C264/REQUIREMENTS.md",
                                                "docs/workflow/tasks/C264/PLAN.md"])
        created = self.root / "docs/workflow/tasks/C264/task.json"
        task = json.loads(created.read_text())
        self.assertEqual(task["status"], "draft")
        self.assertEqual(task["base_sha"], self.current["observed_main"])
        requirements = created.with_name("REQUIREMENTS.md").read_text()
        plan = created.with_name("PLAN.md").read_text()
        self.assertIn("Source observer", requirements)
        self.assertIn("Observe source", requirements)
        self.assertIn("Source observer", plan)
        self.assertIn("draft", requirements)
        self.assertIn("draft", plan)
        self.assertEqual(before, (self.root / "docs/workflow/CURRENT.json").read_bytes())
        self.assertTrue(Project(self.root).validate()["passed"])
        original = self.snapshot()
        code, output = self.run_cli("new-task", "C264", "--title", "Changed", "--intent", "Changed", "--json")
        self.assertEqual(code, 1)
        self.assertIn("refusing overwrite", output)
        self.assertEqual(original, self.snapshot())

    def test_new_task_keeps_supplied_markup_inside_literal_blocks(self):
        title = "Title\n```\n# Embedded heading"
        intent = "```text\n</script>\n````\nUntrusted-looking sample"
        code, output = self.run_cli("new-task", "C264", "--title", title, "--intent", intent, "--json")
        self.assertEqual(code, 0, output)
        directory = self.root / "docs/workflow/tasks/C264"
        requirements = (directory / "REQUIREMENTS.md").read_text()
        self.assertIn("````text\n" + title + "\n````", requirements)
        self.assertIn("`````text\n" + intent + "\n`````", requirements)
        self.assertEqual(json.loads((directory / "task.json").read_text())["intent"], intent)

    def test_new_task_text_output_lists_all_scaffold_files(self):
        code, output = self.run_cli("new-task", "C264", "--title", "Task", "--intent", "Intent")
        self.assertEqual(code, 0, output)
        for name in ("task.json", "REQUIREMENTS.md", "PLAN.md"):
            self.assertIn(f"docs/workflow/tasks/C264/{name}", output)

    def test_unplanned_draft_can_be_cancelled_or_retired_without_blocking_reads(self):
        for task_id, status in (("C264", "cancelled"), ("C265", "retired")):
            with self.subTest(status=status):
                code, output = self.run_cli("new-task", task_id, "--title", "Unselected task", "--intent", "Consider work", "--json")
                self.assertEqual(code, 0, output)
                file = self.root / f"docs/workflow/tasks/{task_id}/task.json"
                draft = json.loads(file.read_text())
                self.assertEqual(draft["requirements"], [])
                self.assertEqual(draft["plan"], [])
                draft["status"] = status
                file.write_text(json.dumps(draft), encoding="utf-8")
                for args in (("check", "--json"), ("brief", "--json"), ("lookup", "source", "--json")):
                    code, output = self.run_cli(*args)
                    self.assertEqual(code, 0, output)
                # Retirement does not relax references already present in a record.
                draft["requirements"] = [{"id": "R01", "description": "Unfinished", "acceptance": "Observable check",
                                          "status": "not_done", "evidence": []}]
                file.write_text(json.dumps(draft), encoding="utf-8")
                report = Project(self.root).validate()
                self.assertFalse(report["passed"])
                self.assertIn("requirements missing from plan", " ".join(report["errors"]))
                draft["requirements"] = []
                file.write_text(json.dumps(draft), encoding="utf-8")

    def test_execution_states_still_require_planning(self):
        self.task["requirements"] = []
        self.task["plan"] = []
        for status in ("ready", "in_progress", "blocked", "review", "done"):
            with self.subTest(status=status):
                self.task["status"] = status
                self.rejected("requirements: must not be empty")

    def test_new_task_rejects_unsafe_id_without_writing(self):
        before = self.snapshot()
        code, output = self.run_cli("new-task", "../escape", "--title", "Test", "--intent", "Test", "--json")
        self.assertEqual(code, 1)
        self.assertIn("invalid identifier", output)
        self.assertEqual(before, self.snapshot())

    def test_empty_lookup_fails_cleanly(self):
        code, output = self.run_cli("lookup", " ", "--json")
        self.assertEqual(code, 1)
        self.assertIn("must not be empty", json.loads(output)["errors"][0])


if __name__ == "__main__":
    unittest.main()
