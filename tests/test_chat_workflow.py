"""Adversarial controls for the repository-owned browser workflow helper."""

from contextlib import redirect_stdout
from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools import chat_workflow
from tools.chat_workflow import Invalid, Project, main

BASE = "5" * 40


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
        code, output = self.run_cli("new-task", "C264", "--title", "Source observer", "--intent", "Observe source", "--base", BASE, "--json")
        self.assertEqual(code, 0, output)
        result = json.loads(output)
        self.assertFalse(result["selected"])
        self.assertEqual(result["created_files"], ["docs/workflow/tasks/C264/task.json",
                                                "docs/workflow/tasks/C264/REQUIREMENTS.md",
                                                "docs/workflow/tasks/C264/PLAN.md"])
        created = self.root / "docs/workflow/tasks/C264/task.json"
        task = json.loads(created.read_text())
        self.assertEqual(task["status"], "draft")
        self.assertEqual((task["base_sha"], result["base_sha"]), (BASE, BASE))
        self.assertIn(f"CURRENT.observed_main records {self.current['observed_main']}", task["base_observation"])
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
        code, output = self.run_cli("new-task", "C264", "--title", "Changed", "--intent", "Changed", "--base", BASE, "--json")
        self.assertEqual(code, 1)
        self.assertIn("refusing overwrite", output)
        self.assertEqual(original, self.snapshot())

    def test_new_task_keeps_supplied_markup_inside_literal_blocks(self):
        title = "Title\n```\n# Embedded heading"
        intent = "```text\n</script>\n````\nUntrusted-looking sample"
        code, output = self.run_cli("new-task", "C264", "--title", title, "--intent", intent, "--base", BASE, "--json")
        self.assertEqual(code, 0, output)
        directory = self.root / "docs/workflow/tasks/C264"
        requirements = (directory / "REQUIREMENTS.md").read_text()
        self.assertIn("````text\n" + title + "\n````", requirements)
        self.assertIn("`````text\n" + intent + "\n`````", requirements)
        self.assertEqual(json.loads((directory / "task.json").read_text())["intent"], intent)

    def test_new_task_text_output_lists_all_scaffold_files(self):
        code, output = self.run_cli("new-task", "C264", "--title", "Task", "--intent", "Intent", "--base", BASE)
        self.assertEqual(code, 0, output)
        self.assertIn(f"Base: {BASE} (supplied with --base", output)
        for name in ("task.json", "REQUIREMENTS.md", "PLAN.md"):
            self.assertIn(f"docs/workflow/tasks/C264/{name}", output)

    def test_unplanned_draft_can_be_cancelled_or_retired_without_blocking_reads(self):
        for task_id, status in (("C264", "cancelled"), ("C265", "retired")):
            with self.subTest(status=status):
                code, output = self.run_cli("new-task", task_id, "--title", "Unselected task", "--intent", "Consider work", "--base", BASE, "--json")
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

    def test_earlier_schema_has_the_browser_entry_point_only(self):
        self.assertTrue(self.check()["passed"])
        code, output = self.run_cli("brief", "--json")
        self.assertEqual(code, 0, output)
        self.assertEqual(json.loads(output)["modes"], {"browser": {"entrypoint": "CHATGPT-START-HERE.md",
                                                                    "required_reads": ["CHATGPT-START-HERE.md", "AGENTS.md"]}})
        self.assertEqual(json.loads(output)["required_reads"], ["CHATGPT-START-HERE.md", "AGENTS.md"])

    def test_only_the_registry_and_current_have_a_second_schema(self):
        for record in (self.task, self.memory, self.knowledge):
            with self.subTest(record=sorted(record)[:3]):
                record["schema_version"] = 2
                self.rejected("unsupported schema_version; expected 1")
                record["schema_version"] = 1
        for record in (self.registry, self.current):
            for version in (0, 3, "2", 2.0, True, None):
                with self.subTest(version=version):
                    record["schema_version"] = version
                    self.rejected("unsupported schema_version; expected 1 or 2")
            record["schema_version"] = 1


class ExecutionModeSchemaTests(ChatWorkflowTests):
    """Schema 2 of the registry and CURRENT. Every inherited control runs again under it."""

    def setUp(self):
        super().setUp()
        self.write("LOCAL-START-HERE.md", "Read the local instructions.\n")
        self.write("docs/workflow/HANDOFF.md", "# Handoff\n")
        self.write("evidence/CURRENT-before.json", json.dumps({"historical_handoff": self.current.pop("historical_handoff")}))
        self.registry.update(schema_version=2, modes={
            "browser": {"entrypoint": self.registry.pop("entrypoint"), "required_reads": self.registry.pop("required_reads"), "declared_by": "Entry document"},
            "local": {"entrypoint": "LOCAL-START-HERE.md", "required_reads": ["LOCAL-START-HERE.md", "AGENTS.md"], "declared_by": "Entry document"}})
        retained = (self.root / "evidence/CURRENT-before.json").read_bytes()
        self.current.update(
            schema_version=2, execution_mode="local", checkpoint={"record": "docs/workflow/tasks/C263/task.json", "session": None},
            unfinished=[{"task": "C271", "status": "blocked", "mode": "browser", "branch": "work/c271", "observed_head": "7" * 40,
                         "observed_at": "2026-11-25T06:00:00Z", "pull_request": "https://github.com/Omegapy/OntoKin/pull/274",
                         "scope_issue": None, "open_gates": ["publication"], "record": "evidence/result.txt#gates"}],
            delivery_policy={"local": {"contract": "docs/workflow/HANDOFF.md#local-sessions", "completion_gate": "checkpoint"},
                             "browser": {"contract": "docs/workflow/HANDOFF.md", "completion_gate": "saved ZIP"}},
            history=[{"path": "evidence/CURRENT-before.json", "sha256": hashlib.sha256(retained).hexdigest(), "bytes": len(retained),
                      "source_commit": "8" * 40, "holds": ["historical_handoff"], "purpose": "Earlier record"}])
        self.task["execution_mode"] = "local"
        self.save()

    def completed(self):
        super().completed()
        self.current["execution_mode"] = None

    # Controls that act on the fields schema 2 moves into modes, or that state the earlier schema.
    def test_path_traversal_absolute_and_backslash_rejected(self):
        for value in ("../outside.md", "/etc/passwd", "docs/../AGENTS.md", "docs\\AGENTS.md", "docs//file.md"):
            for mode in ("local", "browser"):
                with self.subTest(value=value, mode=mode):
                    kept = self.registry["modes"][mode]["entrypoint"]
                    self.registry["modes"][mode]["entrypoint"] = value
                    self.rejected("path")
                    self.registry["modes"][mode]["entrypoint"] = kept

    def test_missing_read_and_symlink_escape_rejected(self):
        outside = Path(self.temp.name) / "outside.md"
        outside.write_text("outside")
        (self.root / "escape.md").symlink_to(outside)
        for mode in ("local", "browser"):
            reads = self.registry["modes"][mode]["required_reads"]
            for value, fragment in (("missing.md", "missing file"), ("escape.md", "path escapes")):
                with self.subTest(mode=mode, value=value):
                    reads.append(value)
                    self.rejected(fragment)
                    reads.pop()

    def test_earlier_schema_has_the_browser_entry_point_only(self):
        code, output = self.run_cli("brief", "--json")
        self.assertEqual(code, 0, output)
        brief = json.loads(output)
        self.assertEqual({name: entry["entrypoint"] for name, entry in brief["modes"].items()},
                         {"local": "LOCAL-START-HERE.md", "browser": "CHATGPT-START-HERE.md"})
        self.assertEqual(brief["required_reads"], ["LOCAL-START-HERE.md", "AGENTS.md"])
        self.completed()
        self.save()
        self.assertIsNone(json.loads(self.run_cli("brief", "--json")[1])["required_reads"], "Without a recorded mode none is guessed.")

    def test_only_the_registry_and_current_have_a_second_schema(self):
        self.task["schema_version"] = 2
        self.rejected("unsupported schema_version; expected 1")

    def test_unknown_schema_and_duplicate_json_keys(self):
        self.registry["schema_version"] = 3
        self.rejected("unsupported schema_version; expected 1 or 2")

    def test_each_mode_has_its_own_complete_read_set(self):
        for change, fragment in ((lambda modes: modes.pop("local"), "expected exactly browser, local"),
                                 (lambda modes: modes.update(cloud=deepcopy(modes["local"])), "expected exactly browser, local"),
                                 (lambda modes: modes["local"]["required_reads"].remove("LOCAL-START-HERE.md"), "must include entrypoint"),
                                 (lambda modes: modes["local"].update(declared_by=""), "declared_by"),
                                 (lambda modes: modes["local"].update(required_reads=[]), "must not be empty"),
                                 (lambda modes: modes["local"].update(deepcopy(modes["browser"])), "own entrypoint")):
            with self.subTest(fragment=fragment):
                kept = deepcopy(self.registry["modes"])
                change(self.registry["modes"])
                self.rejected(fragment)
                self.registry["modes"] = kept
        self.registry["entrypoint"] = "AGENTS.md"
        self.rejected("schema 2 names it only inside modes")

    def test_mode_is_explicit_and_agrees_with_the_task_record(self):
        for mode, fragment in ((None, "an active task needs its recorded mode"), ("cloud", "expected one of browser, local"), (["local"], "expected one of browser, local"),
                               ({"local": 1}, "expected one of browser, local"), (1, "expected one of browser, local"),
                               ("browser", "differs from the active task's recorded mode")):
            with self.subTest(mode=mode):
                self.current["execution_mode"] = mode
                self.rejected(fragment)
        self.current["execution_mode"] = "local"
        del self.task["execution_mode"]
        self.rejected("differs from the active task's recorded mode")
        self.task["execution_mode"] = "cloud"
        self.rejected("execution_mode: expected one of browser, local")

    def test_checkpoint_points_to_the_active_record(self):
        for value, fragment in (({"record": "AGENTS.md", "session": None}, "must be the active task's record"),
                                ({"record": None, "session": None}, "must be the active task's record"),
                                ({"record": "docs/workflow/tasks/C263/task.json"}, "expected a path or null"),
                                ({"record": "docs/workflow/tasks/C263/task.json", "session": "missing.md"}, "missing file")):
            with self.subTest(value=value):
                self.current["checkpoint"] = value
                self.rejected(fragment)
        self.current["checkpoint"] = {"record": "docs/workflow/tasks/C263/task.json", "session": "evidence/result.txt"}
        self.assertTrue(self.check()["passed"])

    def test_receipts_are_linked_and_not_embedded(self):
        for key in ("historical_handoff", "latest_handoff", "previous_handoff", "older_handoffs", "latest_recovery", "previous_recovery", "older_recoveries",
                    "pending_phase_delivery", "p29_r02_prior_current_fields", "prior_p24_start_pending_delivery", "anything_else"):
            with self.subTest(key=key):
                self.current[key] = {"url": "https://example.com/receipt"}
                self.rejected(f"current.{key}: schema 2 keeps receipts and phase records in linked history")
                del self.current[key]

    def test_both_records_use_the_same_schema(self):
        for version in (1, 2):
            self.registry["schema_version"], self.current["schema_version"] = version, 3 - version
            with self.subTest(registry=version):
                self.assertFalse(self.check()["passed"])
        self.registry["schema_version"], self.current["schema_version"] = 2, 1
        self.rejected("must equal the registry's")

    def test_mode_belongs_to_an_active_task_only(self):
        self.completed()
        self.assertTrue(self.check()["passed"])
        self.current["execution_mode"] = "local"
        self.rejected("only an active task has one")

    def test_retained_keys_must_be_in_the_retained_file(self):
        self.current["history"][0]["holds"].append("absent_key")
        self.rejected("absent_key is not in the retained file")
        self.write("evidence/notes.txt", "not JSON")
        data = (self.root / "evidence/notes.txt").read_bytes()
        self.current["history"][0].update(path="evidence/notes.txt", sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))
        self.rejected("expected a JSON record")

    def test_unfinished_scope_is_not_closed_in_its_own_record(self):
        other = deepcopy(self.task)
        other.update(id="C271", status="cancelled")
        self.write("docs/workflow/tasks/C271/task.json", json.dumps(other))
        self.rejected("C271 is closed in its own record")
        other["status"] = "blocked"
        self.write("docs/workflow/tasks/C271/task.json", json.dumps(other))
        self.assertTrue(self.check()["passed"])

    def test_retained_history_is_checked_against_its_bytes(self):
        entry = self.current["history"][0]
        for key, value, fragment in (("sha256", "0" * 64, "SHA-256 differs"), ("bytes", 1, "size differs"), ("path", "missing.json", "missing file"),
                                     ("source_commit", "main", "40 lowercase"), ("holds", [], "must not be empty"), ("purpose", "", "nonempty text")):
            with self.subTest(key=key):
                kept = entry[key]
                entry[key] = value
                self.rejected(fragment)
                entry[key] = kept
        self.write("evidence/CURRENT-before.json", "changed")
        self.rejected("SHA-256 differs")
        self.current["history"] = []
        self.rejected("current.history: must not be empty")

    def test_unfinished_scopes_stay_visible_and_open(self):
        entry = self.current["unfinished"][0]
        for key, value, fragment in (("status", "done", "expected one of"), ("open_gates", [], "must not be empty"), ("observed_head", "main", "40 lowercase"),
                                     ("observed_at", "yesterday", "timestamp"), ("mode", "cloud", "expected one of"), ("task", "C263", "is the active task"),
                                     ("record", "missing.md", "missing file"), ("pull_request", "http://example.com", "HTTPS")):
            with self.subTest(key=key):
                kept = entry[key]
                entry[key] = value
                self.rejected(fragment)
                entry[key] = kept
        self.current["unfinished"].append(deepcopy(entry))
        self.rejected("is repeated")
        self.current["unfinished"] = []
        self.assertTrue(self.check()["passed"])

    def test_each_mode_has_a_delivery_contract(self):
        policy = self.current["delivery_policy"]
        kept = deepcopy(policy)
        for change, fragment in ((lambda: policy.pop("browser"), "expected exactly browser, local"),
                                 (lambda: policy["local"].update(contract="missing.md#local"), "missing file"),
                                 (lambda: policy["browser"].update(completion_gate=""), "nonempty text")):
            with self.subTest(fragment=fragment):
                change()
                self.rejected(fragment)
                policy.clear()
                policy.update(deepcopy(kept))


class StartingRevisionTests(ExecutionModeSchemaTests):
    """A new task starts from an observed or supplied revision in a real Git checkout."""

    def git(self, *arguments):
        environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        environment.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
        return subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "-C", str(self.root), *arguments],
                              env=environment, check=True, capture_output=True, text=True).stdout.strip()

    def commit(self, message):
        self.git("add", "-A")
        self.git("commit", "--quiet", "--no-verify", "-m", message)
        return self.git("rev-parse", "HEAD")

    def create(self, task, *options):
        code, output = self.run_cli("new-task", task, "--title", "Task", "--intent", "Intent", *options, "--json")
        record = self.root / f"docs/workflow/tasks/{task}/task.json"
        return code, json.loads(output), json.loads(record.read_text()) if record.is_file() else None

    def test_task_created_after_the_head_moved_records_the_actual_head(self):
        self.git("init", "--quiet", "--template=")
        first = self.commit("First")
        self.current["observed_main"] = first
        self.save()
        code, _, task = self.create("C300")
        self.assertEqual((code, task["base_sha"]), (0, first))
        self.assertNotIn("CURRENT.observed_main", task["base_observation"])
        moved = self.commit("Moved")
        self.assertNotEqual(first, moved)
        code, result, task = self.create("C301")
        self.assertEqual((code, task["base_sha"], result["base_sha"]), (0, moved, moved))
        self.assertIn(f"CURRENT.observed_main records {first}", task["base_observation"])
        self.assertEqual(json.loads((self.root / "docs/workflow/CURRENT.json").read_text())["observed_main"], first)

    def test_supplied_revision_is_recorded_and_must_be_a_full_commit(self):
        self.git("init", "--quiet", "--template=")
        self.commit("First")
        code, _, task = self.create("C300", "--base", BASE)
        self.assertEqual((code, task["base_sha"], task["base_observation"].split(";")[0]), (0, BASE, "supplied with --base"))
        for value in ("main", "HEAD", "5" * 39, "5" * 41, "G" * 40, ""):
            with self.subTest(value=value):
                code, result, task = self.create("C301", "--base", value)
                self.assertEqual((code, task), (1, None))
                self.assertIn("new-task.base", result["errors"][0])

    def test_recorded_observation_is_never_inherited(self):
        before = self.snapshot()
        code, result, task = self.create("C300")
        self.assertEqual((code, task), (1, None))
        self.assertIn("supply --base", result["errors"][0])
        self.assertEqual(self.snapshot(), before)
        outer, environment = self.root.parent, {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
        for arguments in (["init", "--quiet", "--template="], ["-c", "user.name=T", "-c", "user.email=t@example.invalid", "commit", "--quiet", "--allow-empty", "-m", "Outer"]):
            subprocess.run(["git", "-C", str(outer), *arguments], check=True, capture_output=True, env=environment)
        code, result, task = self.create("C300")
        self.assertEqual((code, task), (1, None), "A surrounding repository is not this checkout.")

    def test_repository_named_by_the_caller_is_not_observed(self):
        self.git("init", "--quiet", "--template=")
        first = self.commit("First")
        other = self.root.parent / "other"
        other.mkdir()
        for arguments in (["init", "--quiet", "--template="], ["-c", "user.name=T", "-c", "user.email=t@example.invalid", "commit", "--quiet", "--allow-empty", "-m", "Other"]):
            subprocess.run(["git", "-C", str(other), *arguments], check=True, capture_output=True)
        with patch.dict(os.environ, {"GIT_DIR": str(other / ".git"), "GIT_WORK_TREE": str(other)}):
            code, _, task = self.create("C300")
        self.assertEqual((code, task["base_sha"]), (0, first))

    def test_observation_names_the_branch(self):
        self.git("init", "--quiet", "--template=")
        self.commit("First")
        self.git("checkout", "--quiet", "-b", "work/example")
        self.assertIn("branch work/example", self.create("C300")[2]["base_observation"])
        self.git("checkout", "--quiet", "--detach")
        self.assertIn("detached", self.create("C301")[2]["base_observation"])

    def test_mode_is_recorded_only_when_it_is_given(self):
        self.assertNotIn("execution_mode", self.create("C300", "--base", BASE)[2])
        self.assertEqual(self.create("C301", "--base", BASE, "--mode", "local")[2]["execution_mode"], "local")
        self.assertTrue(Project(self.root).validate()["passed"])
        code, result, task = self.create("C302", "--base", BASE, "--mode", "cloud")
        self.assertEqual((code, task), (1, None))
        self.assertIn("expected one of browser, local", result["errors"][0])

    def test_base_observation_contacts_no_remote(self):
        self.git("init", "--quiet", "--template=")
        self.commit("First")
        started = []
        real = subprocess.run

        def record(argv, *arguments, **options):
            started.append(list(argv))
            return real(argv, *arguments, **options)

        with patch.object(chat_workflow.subprocess, "run", record):
            self.create("C300")
        commands = {argv[argv.index("-C") + 2] for argv in started}
        self.assertIn("rev-parse", commands)
        self.assertLessEqual(commands, {"rev-parse", "status", "symbolic-ref"})


if __name__ == "__main__":
    unittest.main()
