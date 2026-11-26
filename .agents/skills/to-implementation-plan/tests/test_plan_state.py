"""Contract and fault tests for the source-only To Implementation Plan package.

Every method named ``test_tst_NNN_*`` maps one row from the approved
TST-001..TST-050 matrix to executable evidence.  Tests use temporary project
roots and never install the skill or mutate a consumer project.  The few
behaviors that require the Codex dispatcher or inspection outside the package
also have a static package-side assertion here and are listed in
``DIRECTOR_LEVEL_SCENARIOS`` for the Project Director's behavioral audit.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch


SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / "scripts" / "plan_state.py"
EXAMPLE_PATH = SKILL / "assets" / "example-input.json"

EXPECTED_PACKAGE_FILES = {
    "ACTIONS.md",
    "INDEX.md",
    "README.md",
    "SKILL.md",
    "agents/openai.yaml",
    "assets/example-input.json",
    "assets/phase-template.md",
    "assets/plan-overview-template.md",
    "assets/traceability-template.md",
    "references/intent-and-project-discovery.md",
    "references/lifecycle-and-recovery.md",
    "references/plan-contract.md",
    "scripts/plan_state.py",
    "tests/test_plan_state.py",
}

EXPECTED_ACTION_IDS = {f"TO-IP-{number:03d}" for number in range(1, 13)}
EXPECTED_ROUTES = {
    "create",
    "show",
    "list",
    "update",
    "update-phase",
    "update-task",
    "record-evidence",
    "set-status",
    "validate",
    "rebuild-projections",
    "reindex",
    "reconcile",
}

# These rows contain a live-agent or environment-wide assertion that a local
# unittest cannot prove.  Their package/helper boundary remains executable in
# the matching test method; the Director must separately record the stated
# observation instead of treating the static assertion as end-to-end proof.
DIRECTOR_LEVEL_SCENARIOS = {
    "TST-003": "Send ordinary planning text without naming or invoking the skill and observe no activation or plan write.",
    "TST-004": "Invoke $to-implementation-plan and observe routing to only the requested operation.",
    "TST-005": "Give the skill one raw direct prompt and evaluate the synthesized draft against the full source and project context.",
    "TST-006": "Give the skill raw pasted text and compare every material constraint, exclusion, decision, and term with the resulting plan.",
    "TST-007": "Give the skill a real local text file and compare the inspected bytes, digest, facts, and resulting plan without source mutation.",
    "TST-008": "Exercise missing, final-symlink, parent-symlink, binary, unsupported, and format-aware local inputs through the complete intake route.",
    "TST-009": "Give the skill the current twenty-requirement TRD and audit every source ID, criterion, decision, question, assumption, exclusion, and lifecycle limitation.",
    "TST-010": "Give the skill a structured PRD and audit raw features, stories, constraints, exclusions, and acceptance against canonical coverage.",
    "TST-011": "Give the skill a narrative PRD and audit generated stable IDs, material outcomes, and unresolved ambiguity against the raw source.",
    "TST-012": "Use an agent browsing tool on one controlled accessible URL and compare the normalized source record with the observed page.",
    "TST-013": "Attempt authenticated, inaccessible, and dynamic URLs through the available host tools and record exact limitations.",
    "TST-016": "Inspect a temporary project's live guidance, stack, tests, and protected paths through the skill workflow.",
    "TST-017": "Present two plausible roots and observe one material clarification before any write.",
    "TST-018": "Present a source assumption that conflicts with live project evidence and observe the contradiction remain unresolved.",
    "TST-045": "Present a conflicting Task, TRD, or goal status and observe a mismatch report without another-ledger mutation.",
    "TST-050": "Inspect the final worktree, manifest, managed targets, skill roots, Git index, and remotes for source-only scope preservation.",
}


def package_inventory(package: Path = SKILL) -> set[str]:
    """Return regular files relative to the package, excluding bytecode junk."""
    return {
        path.relative_to(package).as_posix()
        for path in package.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix != ".pyc"
    }


def tree_snapshot(root: Path) -> dict[str, tuple[object, ...]]:
    """Capture bytes, directories, and link targets without following links."""
    result: dict[str, tuple[object, ...]] = {}
    if not root.exists() and not root.is_symlink():
        return result
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            result[relative] = ("symlink", os.readlink(path))
        elif path.is_dir():
            result[relative] = ("directory",)
        else:
            result[relative] = ("file", path.read_bytes())
    return result


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_helper():
    """Import the helper under a stable private test-module name."""
    module_name = "to_implementation_plan_state_under_test"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Cannot import helper at {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def local_markdown_links(text: str) -> list[str]:
    links: list[str] = []
    for target in re.findall(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", text):
        target = target.strip().split("#", 1)[0]
        if not target or target.startswith(("http://", "https://", "mailto:")):
            continue
        links.append(target)
    return links


def canonical_fixture(plan_state, context, payload: dict | None = None) -> dict:
    """Build a complete canonical record through the helper's public normalizer."""
    source = copy.deepcopy(payload if payload is not None else json.loads(
        EXAMPLE_PATH.read_text(encoding="utf-8")
    ))
    plan = plan_state.normalize_plan_input(source, context)
    created = plan_state.parse_timestamp(plan["created_at"], "created_at")
    suffix = "A1B2C3D4"
    plan["plan_id"] = f"PLAN-{created.strftime('%Y%m%d')}-{suffix}"
    plan["history"] = [
        {
            "revision": 1,
            "timestamp": plan["created_at"],
            "action_id": "TO-IP-001",
            "affected_ids": [
                plan["plan_id"],
                *plan_state.stable_record_ids(plan),
            ],
            "status_before": None,
            "status_after": "draft",
            "summary": "Created the isolated test plan.",
            "authority_basis": "Explicit synthetic unittest fixture authority.",
        }
    ]
    plan_state.refresh_validation(plan, plan["updated_at"])
    return plan


def finding_codes(findings: list[dict]) -> set[str]:
    return {str(item.get("code")) for item in findings}


class HelperContractTests(unittest.TestCase):
    """Source normalization, project context, graph, and security contracts."""

    @classmethod
    def setUpClass(cls):
        cls.plan_state = load_helper()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.context = self.plan_state.resolve_context(
            str(self.root), "Implementation_Plans"
        )
        self.example = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))

    def make_plan(self, payload: dict | None = None) -> dict:
        plan = canonical_fixture(self.plan_state, self.context, payload)
        errors = self.plan_state.validate_plan_structure(plan, self.context)
        self.assertEqual(errors, [], errors)
        return plan

    def assert_app_error(self, category: str, function, *args, **kwargs):
        with self.assertRaises(self.plan_state.AppError) as caught:
            function(*args, **kwargs)
        self.assertEqual(caught.exception.category, category, str(caught.exception))
        return caught.exception

    def test_tst_005_create_normalized_direct_prompt_plan(self):
        """TST-005: a direct prompt yields a truthful complete draft payload."""
        plan = self.make_plan()
        self.assertEqual(plan["status"], "draft")
        self.assertEqual(plan["sources"][0]["kind"], "prompt")
        self.assertIn("health-check", plan["objective"]["summary"])
        self.assertEqual(len(plan["requirements"]), 1)
        self.assertEqual(len(plan["phases"]), 1)
        self.assertEqual(len(plan["tasks"]), 2)
        self.assertEqual(plan["validation"]["status"], "pass")

    def test_tst_006_pasted_text_preserves_material_content(self):
        """TST-006: text vocabulary, constraints, exclusions, and provenance survive."""
        payload = copy.deepcopy(self.example)
        payload["sources"][0].update(
            {
                "kind": "text",
                "locator": "Pasted text supplied in the current request",
                "title": "Pasted zero-write diagnostic brief",
                "facts_used": [
                    "Use the existing dispatcher vocabulary.",
                    "Do not write configuration or contact the network.",
                ],
            }
        )
        plan = self.make_plan(payload)
        source = plan["sources"][0]
        self.assertEqual(source["kind"], "text")
        self.assertEqual(source["provenance_mode"], "user_supplied")
        self.assertIn("existing dispatcher", " ".join(source["facts_used"]))
        self.assertIn("Do not add a runtime dependency.", plan["project"]["constraints"])
        self.assertIn("Change production configuration.", plan["scope"]["out_of_scope"])

    def test_tst_007_local_text_locator_digest_and_source_parity(self):
        """TST-007: a regular local file has exact provenance and is not modified."""
        source_path = self.root / "source brief.txt"
        source_path.write_text("Add the existing read-only health check.\n", encoding="utf-8")
        before = source_path.read_bytes()
        payload = copy.deepcopy(self.example)
        payload["sources"][0].update(
            {
                "kind": "file",
                "locator": str(source_path),
                "title": "Local health-check brief",
                "digest": "sha256:" + hashlib.sha256(before).hexdigest(),
                "facts_used": ["Add the existing read-only health check."],
                "provenance_mode": "agent_inspected",
            }
        )
        observed = self.plan_state.read_bounded_regular_file(source_path, label="source")
        plan = self.make_plan(payload)
        self.assertEqual(observed, before)
        self.assertEqual(source_path.read_bytes(), before)
        self.assertEqual(plan["sources"][0]["locator"], str(source_path))
        self.assertEqual(plan["sources"][0]["digest"], "sha256:" + hashlib.sha256(before).hexdigest())

    def test_tst_008_unsafe_missing_binary_and_unsupported_local_input(self):
        """TST-008: unsafe or unreadable input fails before any plan write."""
        missing = self.root / "missing.txt"
        self.assert_app_error(
            "not_found", self.plan_state.read_bounded_regular_file, missing, label="source"
        )
        regular = self.root / "brief.txt"
        regular.write_text("safe source", encoding="utf-8")
        linked = self.root / "linked.txt"
        linked.symlink_to(regular)
        self.assert_app_error(
            "unsafe_or_corrupt",
            self.plan_state.read_bounded_regular_file,
            linked,
            label="source",
        )
        self.assert_app_error(
            "unsafe_or_corrupt",
            self.plan_state.read_bounded_regular_file,
            self.root,
            label="source",
        )
        self.assert_app_error(
            "invalid_input", self.plan_state.decode_json_bytes, b"\xff\x00", "binary input"
        )
        self.assert_app_error(
            "invalid_input",
            self.plan_state.decode_json_bytes,
            b" " * (self.plan_state.MAX_JSON_BYTES + 1),
            "oversized input",
        )
        self.assert_app_error(
            "unsafe_or_corrupt",
            self.plan_state.decode_json_bytes,
            b'{"title":"one","title":"two"}',
            "duplicate-key input",
        )
        self.assert_app_error(
            "invalid_input",
            self.plan_state.decode_json_bytes,
            b'{"overflow":1e9999}',
            "overflow exponent input",
        )
        self.assert_app_error(
            "invalid_input",
            self.plan_state.decode_json_bytes,
            b'{"integer":' + b"9" * (self.plan_state.MAX_INTEGER_DIGITS + 1) + b"}",
            "oversized integer input",
        )
        for surrogate in (b'{"text":"\\ud800"}', b'{"text":"\\udfff"}'):
            self.assert_app_error(
                "invalid_input",
                self.plan_state.decode_json_bytes,
                surrogate,
                "surrogate input",
            )
        deeply_nested = ("[" * 34 + "0" + "]" * 34).encode("utf-8")
        self.assert_app_error(
            "invalid_input",
            self.plan_state.decode_json_bytes,
            deeply_nested,
            "deeply nested input",
        )
        false_claim = copy.deepcopy(self.example)
        false_claim["sources"][0].update(
            {
                "kind": "file",
                "locator": str(missing),
                "facts_used": ["This fact was not actually inspected."],
                "access_limitations": [],
                "provenance_mode": "agent_inspected",
            }
        )
        self.assert_app_error(
            "not_found", self.plan_state.normalize_plan_input, false_claim, self.context
        )
        honest_gap = copy.deepcopy(false_claim)
        honest_gap["sources"][0]["facts_used"] = []
        honest_gap["sources"][0]["access_limitations"] = [
            "The supplied file does not exist in the current host."
        ]
        draft = self.plan_state.normalize_plan_input(honest_gap, self.context)
        self.assertEqual(draft["sources"][0]["facts_used"], [])
        self.assertTrue(draft["sources"][0]["access_limitations"])

        real_parent = self.root / "real-parent"
        real_parent.mkdir()
        parent_source = real_parent / "source.txt"
        parent_source.write_text("parent symlink source\n", encoding="utf-8")
        linked_parent = self.root / "linked-parent"
        linked_parent.symlink_to(real_parent, target_is_directory=True)
        parent_claim = copy.deepcopy(self.example)
        parent_claim["sources"][0].update(
            {
                "kind": "file",
                "locator": str(linked_parent / "source.txt"),
                "digest": "sha256:" + file_sha256(parent_source),
                "facts_used": ["Claimed through a symlinked parent."],
                "provenance_mode": "agent_inspected",
                "inspection_method": "direct_text",
            }
        )
        self.assert_app_error(
            "unsafe_or_corrupt",
            self.plan_state.normalize_plan_input,
            parent_claim,
            self.context,
        )
        symlinked_input = real_parent / "create.json"
        symlinked_input.write_text(json.dumps(self.example), encoding="utf-8")
        input_root = self.root / "symlinked-input-project"
        input_root.mkdir()
        process = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--project-root",
                str(input_root),
                "create",
                "--input",
                str(linked_parent / "create.json"),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(process.returncode, 5, process.stdout)
        self.assertFalse((input_root / "Implementation_Plans").exists())

        binary = self.root / "unsupported.bin"
        binary.write_bytes(b"binary\x00payload\xff")
        binary_claim = copy.deepcopy(self.example)
        binary_claim["sources"][0].update(
            {
                "kind": "file",
                "locator": str(binary),
                "digest": "sha256:" + file_sha256(binary),
                "facts_used": ["A fabricated binary extraction."],
                "provenance_mode": "agent_inspected",
                "inspection_method": "direct_text",
            }
        )
        self.assert_app_error(
            "invalid_input",
            self.plan_state.normalize_plan_input,
            binary_claim,
            self.context,
        )

        for label, changed in (
            (
                "kind switch",
                {"kind": "other", "inspection_method": "direct_text"},
            ),
            (
                "browser on local file",
                {"kind": "file", "inspection_method": "browser_tool"},
            ),
            (
                "direct text on URL",
                {
                    "kind": "url",
                    "locator": "https://example.invalid/source",
                    "inspection_method": "direct_text",
                },
            ),
        ):
            with self.subTest(provenance_matrix=label):
                bypass = copy.deepcopy(self.example)
                bypass["sources"][0].update(
                    {
                        "locator": str(regular),
                        "digest": "sha256:" + file_sha256(regular),
                        "facts_used": ["Claimed inspected fact."],
                        "access_limitations": [],
                        "provenance_mode": "agent_inspected",
                        **changed,
                    }
                )
                self.assert_app_error(
                    "invalid_input",
                    self.plan_state.normalize_plan_input,
                    bypass,
                    self.context,
                )

        for label, digest in (
            ("omitted direct digest", None),
            ("mismatched direct digest", "sha256:" + "0" * 64),
        ):
            with self.subTest(local_digest=label):
                digest_claim = copy.deepcopy(self.example)
                digest_claim["sources"][0].update(
                    {
                        "kind": "file",
                        "locator": str(regular),
                        "digest": digest,
                        "facts_used": ["Claimed inspected fact."],
                        "access_limitations": [],
                        "provenance_mode": "agent_inspected",
                        "inspection_method": "direct_text",
                    }
                )
                self.assert_app_error(
                    "invalid_input",
                    self.plan_state.normalize_plan_input,
                    digest_claim,
                    self.context,
                )

        nul_locator = copy.deepcopy(false_claim)
        nul_locator["sources"][0]["locator"] = "bad\u0000path"
        self.assert_app_error(
            "invalid_input",
            self.plan_state.normalize_plan_input,
            nul_locator,
            self.context,
        )

        fifo = self.root / "blocking.fifo"
        os.mkfifo(fifo)
        fifo_process = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--project-root",
                str(self.root),
                "create",
                "--input",
                str(fifo),
            ],
            text=True,
            capture_output=True,
            check=False,
            timeout=3,
        )
        self.assertEqual(fifo_process.returncode, 5, fifo_process.stdout)
        socket_path = self.root / "source.sock"
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
            server.bind(str(socket_path))
            self.assert_app_error(
                "unsafe_or_corrupt",
                self.plan_state.read_bounded_regular_file,
                socket_path,
                label="source",
            )
        self.assert_app_error(
            "unsafe_or_corrupt",
            self.plan_state.read_bounded_regular_file,
            Path("/dev/null"),
            label="source",
        )

        for name, cli_payload, expected_code in (
            ("missing", false_claim, 3),
            ("parent-symlink", parent_claim, 5),
            ("unsupported-binary", binary_claim, 2),
        ):
            case_root = self.root / f"cli-{name}"
            case_root.mkdir()
            process = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--project-root",
                    str(case_root),
                    "create",
                    "--input",
                    "-",
                ],
                input=json.dumps(cli_payload),
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(process.returncode, expected_code, process.stdout)
            self.assertFalse((case_root / "Implementation_Plans").exists())

        supported_root = self.root / "supported-format"
        supported_root.mkdir()
        supported_pdf = supported_root / "brief.pdf"
        supported_pdf.write_bytes(b"%PDF-1.7\nsynthetic\x00format-aware fixture\n%%EOF\n")
        supported_claim = copy.deepcopy(self.example)
        supported_claim["sources"][0].update(
            {
                "kind": "file",
                "locator": str(supported_pdf),
                "digest": "sha256:" + file_sha256(supported_pdf),
                "facts_used": ["A format-aware PDF tool extracted the synthetic brief."],
                "provenance_mode": "agent_inspected",
                "inspection_method": "pdf_tool",
            }
        )
        process = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--project-root",
                str(supported_root),
                "create",
                "--input",
                "-",
            ],
            input=json.dumps(supported_claim),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(process.returncode, 0, process.stdout)
        discovery = (SKILL / "references" / "intent-and-project-discovery.md").read_text(encoding="utf-8")
        self.assertIn("unsupported", discovery.casefold())
        self.assertFalse((self.root / "Implementation_Plans").exists())

    def test_tst_009_twenty_requirement_trd_payload_is_exactly_covered(self):
        """TST-009: all 20 TRD IDs and acceptance criteria reach tasks."""
        payload = copy.deepcopy(self.example)
        payload["title"] = "Implement the twenty-requirement TRD fixture"
        trd_path = self.root / "fixture" / "trd.md"
        trd_path.parent.mkdir()
        trd_path.write_text("# Twenty-requirement TRD fixture\n", encoding="utf-8")
        payload["sources"] = [
            {
                "source_id": "SRC-001",
                "kind": "trd",
                "locator": str(trd_path),
                "title": "Twenty-requirement TRD",
                "accessed_at": "2026-08-28T12:00:00-06:00",
                "digest": "sha256:" + hashlib.sha256(trd_path.read_bytes()).hexdigest(),
                "facts_used": ["The draft contains 20 stable requirements."],
                "access_limitations": ["The source lifecycle state is draft."],
                "provenance_mode": "agent_inspected",
                "external_id": "TRD-20260828-D209CF52",
            }
        ]
        payload["requirements"] = []
        payload["tasks"] = []
        for number in range(1, 21):
            requirement_id = f"REQ-{number:03d}"
            task_id = f"TASK-{number:03d}"
            payload["requirements"].append(
                {
                    "requirement_id": requirement_id,
                    "title": f"Requirement {number}",
                    "outcome": f"Deliver bounded outcome {number}.",
                    "intent": f"Preserve source intent {number}.",
                    "source_ids": ["SRC-001"],
                    "acceptance_criteria": [f"Observable acceptance {number} is satisfied."],
                    "dependencies": [],
                    "negative_requirements": [],
                    "status": "active",
                    "disposition": None,
                    "evidence": [],
                }
            )
            payload["tasks"].append(
                {
                    "task_id": task_id,
                    "phase_id": "PHASE-001",
                    "title": f"Implement requirement {number}",
                    "action": f"Implement and verify bounded outcome {number}.",
                    "requirement_ids": [requirement_id],
                    "design_basis": [],
                    "target_artifacts": [f"artifact-{number}.txt"],
                    "dependencies": [],
                    "parallel_group": None,
                    "risks": [],
                    "acceptance_criteria": [f"Task result {number} is reviewable."],
                    "verification_steps": [f"Inspect artifact {number}."],
                    "status": "planned",
                    "blocker_reason": None,
                    "pause_reason": None,
                    "skip_reason": None,
                    "skip_authority": None,
                    "evidence": [],
                    "completed_at": None,
                }
            )
        payload["phases"][0]["task_ids"] = [f"TASK-{number:03d}" for number in range(1, 21)]
        payload.pop("coverage", None)
        plan = self.make_plan(payload)
        self.assertEqual([item["requirement_id"] for item in plan["requirements"]],
                         [f"REQ-{number:03d}" for number in range(1, 21)])
        self.assertEqual(len(plan["coverage"]["requirement_to_task"]), 20)
        for edge in plan["coverage"]["requirement_to_task"]:
            with self.subTest(requirement=edge["requirement_id"]):
                self.assertEqual(len(edge["task_ids"]), 1)

    def test_tst_010_structured_prd_features_and_constraints_are_traceable(self):
        """TST-010: structured PRD features, story, exclusions, and acceptance map."""
        payload = copy.deepcopy(self.example)
        payload["sources"][0].update(
            {
                "kind": "prd",
                "locator": "fixture/structured-prd.md",
                "title": "Structured health-check PRD",
                "external_id": "PRD-HEALTH-001",
                "facts_used": [
                    "Feature: read-only health check.",
                    "User story: a maintainer diagnoses configuration before startup.",
                    "Constraint: no network call.",
                    "Exclusion: do not modify production configuration.",
                ],
            }
        )
        plan = self.make_plan(payload)
        source = plan["sources"][0]
        self.assertEqual(source["kind"], "prd")
        self.assertIn("User story", " ".join(source["facts_used"]))
        self.assertTrue(plan["requirements"][0]["acceptance_criteria"])
        self.assertTrue(plan["coverage"]["requirement_to_task"][0]["task_ids"])

    def test_tst_011_narrative_prd_generates_stable_ids_and_uncertainty(self):
        """TST-011: unnumbered narrative outcomes receive stable generated IDs."""
        payload = copy.deepcopy(self.example)
        payload["sources"][0].update(
            {
                "kind": "prd",
                "locator": "fixture/narrative-prd.md",
                "title": "Narrative PRD",
                "facts_used": ["Operators need a diagnostic.", "The output format remains undecided."],
            }
        )
        payload["requirements"] = [
            {
                "title": "Report configuration health",
                "outcome": "Report whether local configuration loads.",
                "intent": "Operators need a diagnostic.",
                "source_ids": ["SRC-001"],
                "acceptance_criteria": ["A result states whether configuration loads."],
                "dependencies": [],
                "negative_requirements": [],
                "status": "active",
                "disposition": None,
                "evidence": [],
            },
            {
                "title": "Protect configuration",
                "outcome": "Do not modify configuration during the diagnostic.",
                "intent": "The operation must remain safe.",
                "source_ids": ["SRC-001"],
                "acceptance_criteria": ["Configuration bytes remain unchanged."],
                "dependencies": [],
                "negative_requirements": ["Do not write configuration."],
                "status": "active",
                "disposition": None,
                "evidence": [],
            },
        ]
        payload["tasks"][0]["requirement_ids"] = ["REQ-001"]
        payload["tasks"][1]["requirement_ids"] = ["REQ-002"]
        payload["open_questions"] = [
            {
                "question_id": "Q-001",
                "question": "Which output format is required?",
                "affects": ["REQ-001"],
                "prerequisites": [],
                "status": "open",
                "answer": None,
                "authority_basis": None,
            }
        ]
        payload.pop("coverage", None)
        first = self.make_plan(payload)
        second = self.make_plan(payload)
        expected = ["REQ-001", "REQ-002"]
        self.assertEqual([item["requirement_id"] for item in first["requirements"]], expected)
        self.assertEqual([item["requirement_id"] for item in second["requirements"]], expected)
        self.assertIn("open_question", finding_codes(self.plan_state.quality_findings(first)))

    def test_tst_012_accessible_url_normalized_payload_has_no_snapshot(self):
        """TST-012: normalized accessible URL provenance is truthful and bounded."""
        payload = copy.deepcopy(self.example)
        payload["sources"][0].update(
            {
                "kind": "url",
                "locator": "https://example.invalid/controlled-health-check",
                "title": "Controlled health-check reference",
                "accessed_at": "2026-08-28T13:00:00-06:00",
                "digest": "sha256:" + "b" * 64,
                "facts_used": ["The reference describes a read-only diagnostic."],
                "access_limitations": [],
                "provenance_mode": "agent_inspected",
            }
        )
        plan = self.make_plan(payload)
        source = plan["sources"][0]
        self.assertEqual(source["kind"], "url")
        self.assertEqual(source["locator"], "https://example.invalid/controlled-health-check")
        self.assertNotIn("snapshot", source)
        self.assertNotIn("content", source)
        self.assertIn("TST-012", DIRECTOR_LEVEL_SCENARIOS)

    def test_tst_013_inaccessible_url_limitations_do_not_become_requirements(self):
        """TST-013: inaccessible URL cases remain limitations and block readiness."""
        for limitation in (
            "Authentication is required.",
            "The page is inaccessible from this host.",
            "Dynamic content could not be rendered.",
        ):
            with self.subTest(limitation=limitation):
                payload = copy.deepcopy(self.example)
                payload["sources"].append(
                    {
                        "source_id": "SRC-002",
                        "kind": "url",
                        "locator": "https://example.invalid/unavailable",
                        "title": "Unavailable URL",
                        "accessed_at": "2026-08-28T13:00:00-06:00",
                        "digest": None,
                        "facts_used": [],
                        "access_limitations": [limitation],
                        "provenance_mode": "agent_inspected",
                        "external_id": None,
                    }
                )
                payload.pop("coverage", None)
                plan = canonical_fixture(self.plan_state, self.context, payload)
                self.assertEqual(plan["sources"][1]["access_limitations"], [limitation])
                self.assertFalse(any("SRC-002" in item["source_ids"] for item in plan["requirements"]))
                codes = finding_codes(self.plan_state.readiness_findings(plan))
                self.assertIn("source_access_limitation", codes)
                self.assertIn("uncovered_source", codes)
        resolved_payload = copy.deepcopy(self.example)
        resolved_payload["sources"].extend(
            [
                {
                    "source_id": "SRC-002",
                    "kind": "url",
                    "locator": "https://example.invalid/unavailable",
                    "title": "Unavailable historical URL",
                    "accessed_at": "2026-08-28T13:00:00-06:00",
                    "digest": None,
                    "facts_used": [],
                    "access_limitations": ["Authentication is required."],
                    "provenance_mode": "agent_inspected",
                    "inspection_method": "browser_tool",
                    "external_id": None,
                },
                {
                    "source_id": "SRC-003",
                    "kind": "text",
                    "locator": None,
                    "title": "Authorized replacement observation",
                    "accessed_at": "2026-08-28T13:01:00-06:00",
                    "digest": None,
                    "facts_used": ["The replacement confirms the required behavior."],
                    "access_limitations": [],
                    "provenance_mode": "user_supplied",
                    "inspection_method": None,
                    "external_id": None,
                },
            ]
        )
        resolved_payload["requirements"][0]["source_ids"].append("SRC-003")
        resolved_payload.pop("coverage", None)
        resolved = canonical_fixture(
            self.plan_state, self.context, resolved_payload
        )
        historical_edge = next(
            edge
            for edge in resolved["coverage"]["source_to_requirement"]
            if edge["source_id"] == "SRC-002"
        )
        historical_edge["disposition"] = {
            "kind": "superseded",
            "reason": "SRC-003 replaced the inaccessible historical source.",
            "authority_basis": "Explicit source-resolution authority for this fixture.",
        }
        self.plan_state.refresh_validation(resolved, resolved["updated_at"])
        self.assertFalse(self.plan_state.readiness_findings(resolved))
        historical_codes = finding_codes(self.plan_state.quality_findings(resolved))
        self.assertIn("historical_source_access_limitation", historical_codes)
        self.assertNotIn("source_access_limitation", historical_codes)
        self.assertFalse(
            self.plan_state.validate_plan_structure(resolved, self.context)
        )

        inactive_replacement_payload = copy.deepcopy(self.example)
        inactive_replacement_source = copy.deepcopy(resolved_payload["sources"][2])
        inactive_replacement_source["source_id"] = "SRC-002"
        inaccessible_active_source = copy.deepcopy(resolved_payload["sources"][1])
        inaccessible_active_source["source_id"] = "SRC-003"
        inactive_replacement_payload["sources"].extend(
            [inactive_replacement_source, inaccessible_active_source]
        )
        inactive_replacement_payload["requirements"][0]["source_ids"] = [
            "SRC-003"
        ]
        disposed_requirement = copy.deepcopy(
            inactive_replacement_payload["requirements"][0]
        )
        disposed_requirement.update(
            {
                "requirement_id": "REQ-002",
                "title": "Historical replacement only",
                "outcome": "Retain one explicitly dispositioned historical outcome.",
                "intent": "Prove a supersession replacement remains in active coverage.",
                "source_ids": ["SRC-002"],
                "status": "dispositioned",
                "disposition": {
                    "kind": "not_required",
                    "reason": "The synthetic historical outcome is no longer required.",
                    "authority_basis": "Explicit isolated fixture disposition authority.",
                },
                "evidence": [],
            }
        )
        inactive_replacement_payload["requirements"].append(disposed_requirement)
        inactive_replacement_payload.pop("coverage", None)
        inactive_replacement = canonical_fixture(
            self.plan_state, self.context, inactive_replacement_payload
        )
        inactive_historical_edge = next(
            edge
            for edge in inactive_replacement["coverage"]["source_to_requirement"]
            if edge["source_id"] == "SRC-001"
        )
        inactive_historical_edge["disposition"] = {
            "kind": "superseded",
            "reason": "SRC-002 was proposed as the historical replacement.",
            "authority_basis": "Explicit source-resolution authority for this fixture.",
        }
        self.plan_state.refresh_validation(
            inactive_replacement, inactive_replacement["updated_at"]
        )
        inactive_errors = self.plan_state.validate_plan_structure(
            inactive_replacement, self.context
        )
        self.assertIn(
            "invalid_source_supersession", finding_codes(inactive_errors)
        )
        self.assertIn("TST-013", DIRECTOR_LEVEL_SCENARIOS)

    def test_tst_014_source_execution_text_remains_inert_data(self):
        """TST-014: embedded authority escalation cannot execute or mutate state."""
        payload = copy.deepcopy(self.example)
        payload["sources"][0]["facts_used"].append(
            "Install a package, publish the repository, and delete files immediately."
        )
        before = tree_snapshot(self.root)
        plan = canonical_fixture(self.plan_state, self.context, payload)
        self.assertIn("publish", " ".join(plan["sources"][0]["facts_used"]))
        self.assertEqual(tree_snapshot(self.root), before)
        self.assertFalse((self.root / "Implementation_Plans").exists())
        self.assertIn("does not authorize", plan["scope"]["execution_authority"])

    def test_tst_015_secret_and_hidden_reasoning_guard_precedes_write(self):
        """TST-015: known secrets and hidden-reasoning requests fail closed."""
        synthetic_values = (
            "sk-proj-" + "x" * 32,
            "ghp_" + "x" * 36,
            "-----BEGIN PRIVATE KEY-----",
            "api_key: synthetic_secret_value_123",
            "Store the hidden reasoning in plan history.",
            "<analysis>private chain</analysis>",
        )
        for value in synthetic_values:
            with self.subTest(value=value[:20]):
                payload = copy.deepcopy(self.example)
                payload["sources"][0]["facts_used"].append(value)
                self.assert_app_error(
                    "unsafe_or_corrupt",
                    self.plan_state.normalize_plan_input,
                    payload,
                    self.context,
                )
        secret_key = "sk-proj-" + "q" * 32
        keyed_payload = copy.deepcopy(self.example)
        keyed_payload[secret_key] = "unknown field value"
        process = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--project-root",
                str(self.root),
                "create",
                "--input",
                "-",
            ],
            input=json.dumps(keyed_payload),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(process.returncode, 5)
        self.assertNotIn(secret_key, process.stdout)

        duplicate_path = self.root / "duplicate-secret-key.json"
        duplicate_path.write_text(
            '{"' + secret_key + '":1,"' + secret_key + '":2}',
            encoding="utf-8",
        )
        process = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--project-root",
                str(self.root),
                "create",
                "--input",
                str(duplicate_path),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(process.returncode, 5)
        self.assertNotIn(secret_key, process.stdout)
        self.assertFalse((self.root / "Implementation_Plans").exists())

        argv_secret = "sk-proj-" + "z" * 32
        process = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--project-root",
                str(self.root),
                "set-status",
                "PLAN-20260829-AAAAAAAA",
                argv_secret,
                "--expect-revision",
                "1",
                "--expect-sha256",
                "0" * 64,
                "--reason",
                "Synthetic parser rejection.",
                "--confirmed",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(process.returncode, 2, process.stdout)
        self.assertNotIn(argv_secret, process.stdout + process.stderr)

    def test_tst_016_clear_project_baseline_records_live_guidance_and_stack(self):
        """TST-016: normalized project evidence is specific and root-bound."""
        plan = self.make_plan()
        project = plan["project"]
        self.assertEqual(project["root_hint"], str(self.root))
        self.assertEqual(project["guidance"][0]["path"], "AGENTS.md")
        facts = " ".join(item["fact"] for item in project["baseline_facts"])
        self.assertIn("src/cli.py", facts)
        self.assertIn("unittest", facts)
        self.assertEqual(project["preserved_paths"], ["config/production.json"])
        self.assertIn("TST-016", DIRECTOR_LEVEL_SCENARIOS)

    def test_tst_017_ambiguous_root_contract_writes_nothing(self):
        """TST-017: local boundary for the Director's two-root clarification."""
        discovery = (SKILL / "references" / "intent-and-project-discovery.md").read_text(encoding="utf-8")
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        before = tree_snapshot(self.root)
        self.assertIn("If two plausible roots remain", discovery)
        self.assertIn("ask for the material choice before writing", skill)
        self.assert_app_error(
            "invalid_input",
            self.plan_state.resolve_context,
            "relative-project-root",
            "Implementation_Plans",
        )
        self.assertEqual(tree_snapshot(self.root), before)
        self.assertIn("TST-017", DIRECTOR_LEVEL_SCENARIOS)

    def test_tst_018_source_project_conflict_remains_visible(self):
        """TST-018: source assumptions cannot replace observed project facts."""
        payload = copy.deepcopy(self.example)
        payload["sources"][0]["facts_used"].append("The project uses pytest.")
        payload["project"]["baseline_facts"].append(
            {
                "fact": "The project uses unittest, not pytest.",
                "evidence_locator": "tests/test_cli.py",
                "observed_at": "2026-08-28T12:00:00-06:00",
            }
        )
        payload["open_questions"] = [
            {
                "question_id": "Q-001",
                "question": "Should the plan preserve the observed unittest convention?",
                "affects": ["TASK-002"],
                "prerequisites": [],
                "status": "open",
                "answer": None,
                "authority_basis": None,
            }
        ]
        plan = self.make_plan(payload)
        self.assertIn("pytest", " ".join(plan["sources"][0]["facts_used"]))
        self.assertIn("not pytest", " ".join(item["fact"] for item in plan["project"]["baseline_facts"]))
        self.assertIn("open_question", finding_codes(self.plan_state.readiness_findings(plan)))
        self.assertIn("TST-018", DIRECTOR_LEVEL_SCENARIOS)

    def test_tst_019_two_phase_order_membership_and_derived_status(self):
        """TST-019: two ordered phases have full contracts and derived states."""
        payload = copy.deepcopy(self.example)
        payload["phases"][0]["task_ids"] = ["TASK-001"]
        payload["phases"].append(
            {
                "phase_id": "PHASE-002",
                "title": "Verify and document",
                "objective": "Verify behavior and finish the command reference.",
                "scope": ["Focused tests", "Documentation"],
                "depends_on_phase_ids": ["PHASE-001"],
                "entry_conditions": ["The command implementation is available."],
                "exit_criteria": ["Tests and documentation meet acceptance."],
                "task_ids": ["TASK-002"],
                "risks": ["Documentation could drift from behavior."],
            }
        )
        payload["tasks"][1]["phase_id"] = "PHASE-002"
        plan = self.make_plan(payload)
        self.assertEqual([phase["phase_id"] for phase in plan["phases"]], ["PHASE-001", "PHASE-002"])
        self.assertEqual(plan["phases"][1]["depends_on_phase_ids"], ["PHASE-001"])
        self.assertTrue(all(phase["status"] == "planned" for phase in plan["phases"]))
        memberships = [task_id for phase in plan["phases"] for task_id in phase["task_ids"]]
        self.assertEqual(memberships, ["TASK-001", "TASK-002"])

    def test_tst_020_fully_populated_task_contract(self):
        """TST-020: every complete task field is present and machine-valid."""
        plan = self.make_plan()
        expected = {
            "task_id",
            "phase_id",
            "title",
            "action",
            "requirement_ids",
            "design_basis",
            "target_artifacts",
            "dependencies",
            "parallel_group",
            "risks",
            "acceptance_criteria",
            "verification_steps",
            "status",
            "blocker_reason",
            "pause_reason",
            "skip_reason",
            "skip_authority",
            "evidence",
            "completed_at",
        }
        for task in plan["tasks"]:
            with self.subTest(task=task["task_id"]):
                self.assertEqual(set(task), expected)
                self.assertTrue(task["target_artifacts"])
                self.assertTrue(task["acceptance_criteria"])
                self.assertTrue(task["verification_steps"])
                self.assertTrue(task["requirement_ids"] or task["design_basis"])

        base_evidence = {
            "evidence_id": "EVID-900",
            "timestamp": plan["updated_at"],
            "evidence_type": "test",
            "result_status": "passed",
            "description": "The complete focused suite was executed.",
            "locator_or_command": "python -m unittest discover -s tests -v",
            "observed_result": (
                "Tests: 50 passed, 0 failed, 0 errors, failures=0, errors=0."
            ),
            "verification_level": "broader_suite_passed",
            "observation_source": "tool",
            "target_digest": "sha256:" + "0" * 64,
        }
        zero_failure_errors: list[dict] = []
        self.plan_state._check_evidence_record(
            copy.deepcopy(base_evidence),
            "evidence",
            zero_failure_errors,
            set(),
        )
        self.assertNotIn(
            "evidence_result_contradiction", finding_codes(zero_failure_errors)
        )

        positive_failure = copy.deepcopy(base_evidence)
        positive_failure["observed_result"] = "Tests: 49 passed, 1 failed."
        positive_failure_errors: list[dict] = []
        self.plan_state._check_evidence_record(
            positive_failure,
            "evidence",
            positive_failure_errors,
            set(),
        )
        self.assertIn(
            "evidence_result_contradiction",
            finding_codes(positive_failure_errors),
        )
        for failure_summary in (
            "Ran 50 tests. FAILED (failures=1).",
            "Ran 50 tests with failures=1.",
            "Ran 50 tests with errors=1.",
            "Ran 50 tests: 1 error.",
        ):
            with self.subTest(failure_summary=failure_summary):
                failure_record = copy.deepcopy(base_evidence)
                failure_record["observed_result"] = failure_summary
                failure_errors: list[dict] = []
                self.plan_state._check_evidence_record(
                    failure_record,
                    "evidence",
                    failure_errors,
                    set(),
                )
                self.assertIn(
                    "evidence_result_contradiction",
                    finding_codes(failure_errors),
                )

        contradictory_not_exercised = copy.deepcopy(base_evidence)
        contradictory_not_exercised.update(
            {
                "evidence_type": "user_report",
                "result_status": "failed",
                "verification_level": "not_exercised",
                "observation_source": "user",
                "locator_or_command": None,
            }
        )
        not_exercised_errors: list[dict] = []
        self.plan_state._check_evidence_record(
            contradictory_not_exercised,
            "evidence",
            not_exercised_errors,
            set(),
        )
        self.assertIn("evidence_semantics", finding_codes(not_exercised_errors))

    def test_tst_021_missing_self_cycle_and_phase_order_dependencies(self):
        """TST-021: dependency faults are each named and block the plan."""
        base = self.make_plan()
        cases: list[tuple[str, dict, str]] = []

        missing_task = copy.deepcopy(base)
        missing_task["tasks"][0]["dependencies"] = ["TASK-999"]
        cases.append(("missing task", missing_task, "missing_dependency"))

        self_task = copy.deepcopy(base)
        self_task["tasks"][0]["dependencies"] = ["TASK-001"]
        cases.append(("self task", self_task, "self_dependency"))

        cycle_task = copy.deepcopy(base)
        cycle_task["tasks"][0]["dependencies"] = ["TASK-002"]
        cycle_task["tasks"][1]["dependencies"] = ["TASK-001"]
        cases.append(("task cycle", cycle_task, "dependency_cycle"))

        missing_phase = copy.deepcopy(base)
        missing_phase["phases"][0]["depends_on_phase_ids"] = ["PHASE-999"]
        cases.append(("missing phase", missing_phase, "missing_dependency"))

        self_phase = copy.deepcopy(base)
        self_phase["phases"][0]["depends_on_phase_ids"] = ["PHASE-001"]
        cases.append(("self phase", self_phase, "self_dependency"))

        later_phase = copy.deepcopy(base)
        later_phase["phases"][0]["task_ids"] = ["TASK-001"]
        later_phase["tasks"][1]["phase_id"] = "PHASE-002"
        later_phase["phases"].append(
            {
                "phase_id": "PHASE-002",
                "title": "Later phase",
                "objective": "Complete later work.",
                "scope": ["Later work"],
                "depends_on_phase_ids": [],
                "entry_conditions": ["Earlier work completes."],
                "exit_criteria": ["Later work completes."],
                "task_ids": ["TASK-002"],
                "risks": [],
                "status": "planned",
            }
        )
        later_phase["phases"][0]["depends_on_phase_ids"] = ["PHASE-002"]
        cases.append(("later phase", later_phase, "phase_order"))

        missing_membership = copy.deepcopy(base)
        missing_membership["phases"][0]["task_ids"].remove("TASK-002")
        cases.append(("missing membership", missing_membership, "membership_mismatch"))

        duplicate_membership = copy.deepcopy(base)
        duplicate_membership["phases"][0]["task_ids"].append("TASK-001")
        cases.append(("duplicate membership", duplicate_membership, "duplicate_reference"))

        duplicate_task = copy.deepcopy(base)
        duplicate_task["tasks"].append(copy.deepcopy(duplicate_task["tasks"][0]))
        cases.append(("duplicate task ID", duplicate_task, "duplicate_identifier"))

        normalized_overlap = copy.deepcopy(base)
        normalized_overlap["tasks"][0]["parallel_group"] = "safe-group"
        normalized_overlap["tasks"][1]["parallel_group"] = "safe-group"
        normalized_overlap["tasks"][1]["dependencies"] = []
        normalized_overlap["tasks"][0]["target_artifacts"] = ["build/../shared.txt"]
        normalized_overlap["tasks"][1]["target_artifacts"] = ["shared.txt"]
        cases.append(
            ("normalized parallel overlap", normalized_overlap, "unsafe_parallel_group")
        )

        ancestor_overlap = copy.deepcopy(base)
        ancestor_overlap["tasks"][0]["parallel_group"] = "ancestor-group"
        ancestor_overlap["tasks"][1]["parallel_group"] = "ancestor-group"
        ancestor_overlap["tasks"][1]["dependencies"] = []
        ancestor_overlap["tasks"][0]["target_artifacts"] = ["src"]
        ancestor_overlap["tasks"][1]["target_artifacts"] = ["src/generated.py"]
        cases.append(
            ("ancestor parallel overlap", ancestor_overlap, "unsafe_parallel_group")
        )

        glob_overlap = copy.deepcopy(base)
        glob_overlap["tasks"][0]["parallel_group"] = "glob-group"
        glob_overlap["tasks"][1]["parallel_group"] = "glob-group"
        glob_overlap["tasks"][1]["dependencies"] = []
        glob_overlap["tasks"][0]["target_artifacts"] = ["src/*.py"]
        glob_overlap["tasks"][1]["target_artifacts"] = ["src/generated.py"]
        cases.append(("glob parallel overlap", glob_overlap, "unsafe_parallel_group"))

        phase_parallel = copy.deepcopy(base)
        phase_parallel["phases"][0]["task_ids"] = ["TASK-001"]
        phase_parallel["phases"].append(
            {
                "phase_id": "PHASE-002",
                "title": "Dependent phase",
                "objective": "Exercise dependent-phase parallel rejection.",
                "scope": ["Dependent work"],
                "depends_on_phase_ids": ["PHASE-001"],
                "entry_conditions": ["PHASE-001 completes."],
                "exit_criteria": ["TASK-002 completes."],
                "task_ids": ["TASK-002"],
                "risks": [],
                "status": "planned",
            }
        )
        phase_parallel["tasks"][1]["phase_id"] = "PHASE-002"
        phase_parallel["tasks"][1]["dependencies"] = []
        phase_parallel["tasks"][0]["parallel_group"] = "phase-group"
        phase_parallel["tasks"][1]["parallel_group"] = "phase-group"
        cases.append(
            ("dependent phases in one parallel group", phase_parallel, "unsafe_parallel_group")
        )

        for collection, index, field, malformed in (
            ("tasks", 0, "task_id", "TASK-000"),
            ("tasks", 0, "task_id", "TASK-0001"),
            ("phases", 0, "phase_id", "PHASE-000"),
            ("sources", 0, "source_id", "SRC-000"),
        ):
            malformed_id = copy.deepcopy(base)
            malformed_id[collection][index][field] = malformed
            cases.append(
                (
                    f"noncanonical local ID {malformed}",
                    malformed_id,
                    "noncanonical_identifier",
                )
            )

        for label, left_target, right_target in (
            ("prefixed and bare overlap", "file:shared.txt", "shared.txt"),
            ("path and file prefix overlap", "path:shared.txt", "file:shared.txt"),
            (
                "absolute and relative overlap",
                str(self.context.project_root / "shared.txt"),
                "shared.txt",
            ),
        ):
            prefixed_overlap = copy.deepcopy(base)
            prefixed_overlap["tasks"][0]["parallel_group"] = "prefix-group"
            prefixed_overlap["tasks"][1]["parallel_group"] = "prefix-group"
            prefixed_overlap["tasks"][1]["dependencies"] = []
            prefixed_overlap["tasks"][0]["target_artifacts"] = [left_target]
            prefixed_overlap["tasks"][1]["target_artifacts"] = [right_target]
            cases.append((label, prefixed_overlap, "unsafe_parallel_group"))

        if self.plan_state.filesystem_is_case_insensitive(self.context.project_root):
            case_overlap = copy.deepcopy(base)
            case_overlap["tasks"][0]["parallel_group"] = "case-group"
            case_overlap["tasks"][1]["parallel_group"] = "case-group"
            case_overlap["tasks"][1]["dependencies"] = []
            case_overlap["tasks"][0]["target_artifacts"] = ["src/Foo.py"]
            case_overlap["tasks"][1]["target_artifacts"] = ["src/foo.py"]
            cases.append(
                ("case-folded parallel overlap", case_overlap, "unsafe_parallel_group")
            )

        for label, plan, expected_code in cases:
            with self.subTest(case=label):
                codes = finding_codes(self.plan_state.validate_plan_structure(plan, self.context))
                self.assertIn(expected_code, codes, codes)

        scale_plan = copy.deepcopy(base)
        task_template = copy.deepcopy(scale_plan["tasks"][0])
        scale_tasks = []
        for number in range(1, 5001):
            task = copy.deepcopy(task_template)
            task["task_id"] = f"TASK-{number:03d}"
            task["title"] = f"Independent sibling task {number}"
            task["dependencies"] = []
            task["parallel_group"] = "large-sibling-group"
            task["target_artifacts"] = [f"generated/item-{number:05d}.txt"]
            scale_tasks.append(task)
        scale_plan["tasks"] = scale_tasks
        scale_plan["phases"][0]["task_ids"] = [
            task["task_id"] for task in scale_tasks
        ]
        started = time.perf_counter()
        scale_codes = finding_codes(
            self.plan_state.validate_plan_structure(scale_plan, self.context)
        )
        elapsed = time.perf_counter() - started
        self.assertNotIn("unsafe_parallel_group", scale_codes)
        self.assertLess(elapsed, 5.0)

    def test_tst_041_forward_coverage_names_the_missing_requirement(self):
        """TST-041: an uncovered source requirement blocks readiness by ID."""
        plan = self.make_plan()
        for task in plan["tasks"]:
            task["requirement_ids"] = []
            task["design_basis"] = ["Synthetic quality basis retained only for this coverage test."]
        plan["coverage"]["requirement_to_task"][0]["task_ids"] = []
        findings = self.plan_state.quality_findings(plan)
        self.assertIn("uncovered_requirement", finding_codes(findings))
        missing = [item for item in findings if item["code"] == "uncovered_requirement"]
        self.assertEqual(missing[0]["targets"], ["REQ-001"])
        self.assertTrue(self.plan_state.readiness_findings(plan))

    def test_tst_042_reverse_coverage_reports_orphan_task(self):
        """TST-042: a task without requirement or design basis blocks readiness."""
        plan = self.make_plan()
        orphan = copy.deepcopy(plan["tasks"][0])
        orphan.update(
            {
                "task_id": "TASK-003",
                "title": "Unexplained task",
                "requirement_ids": [],
                "design_basis": [],
                "dependencies": [],
            }
        )
        plan["tasks"].append(orphan)
        plan["phases"][0]["task_ids"].append("TASK-003")
        findings = self.plan_state.quality_findings(plan)
        self.assertIn("orphan_task", finding_codes(findings))
        orphan_findings = [item for item in findings if item["code"] == "orphan_task"]
        self.assertEqual(orphan_findings[0]["targets"], ["TASK-003"])
        structural = self.plan_state.validate_plan_structure(plan, self.context)
        self.assertIn("orphan_task", finding_codes(structural))

    def test_tst_044_open_question_and_unconfirmed_assumption_block_ready(self):
        """TST-044: uncertainty is valid draft state but fails readiness."""
        payload = copy.deepcopy(self.example)
        payload["open_questions"] = [
            {
                "question_id": "Q-001",
                "question": "Which compatibility floor is required?",
                "affects": ["REQ-001"],
                "prerequisites": [],
                "status": "open",
                "answer": None,
                "authority_basis": None,
            }
        ]
        payload["assumptions"] = [
            {
                "assumption_id": "ASM-001",
                "statement": "The existing runtime supports the proposed route.",
                "basis": "The runtime version has not yet been inspected.",
                "status": "unconfirmed",
                "authority_basis": None,
            }
        ]
        plan = self.make_plan(payload)
        self.assertEqual(plan["status"], "draft")
        self.assertEqual(plan["validation"]["status"], "unresolved")
        codes = finding_codes(self.plan_state.readiness_findings(plan))
        self.assertIn("open_question", codes)
        self.assertIn("unconfirmed_assumption", codes)

        placeholder_payload = copy.deepcopy(self.example)
        placeholder_payload["status_reason"] = "TBD"
        placeholder_payload["objective"].update(
            {
                "summary": "TBD",
                "user_value": "TBD",
                "success_outcomes": ["TBD"],
            }
        )
        placeholder_payload["requirements"][0].update(
            {
                "outcome": "TBD",
                "intent": "TBD",
                "acceptance_criteria": ["TBD"],
            }
        )
        for task in placeholder_payload["tasks"]:
            task.update(
                {
                    "action": "TBD",
                    "target_artifacts": ["TBD"],
                    "acceptance_criteria": ["TBD"],
                    "verification_steps": ["TBD"],
                }
            )
        placeholder_plan = canonical_fixture(
            self.plan_state, self.context, placeholder_payload
        )
        self.assertEqual(placeholder_plan["status"], "draft")
        self.assertEqual(placeholder_plan["validation"]["status"], "fail")
        placeholder_findings = self.plan_state.readiness_findings(
            placeholder_plan
        )
        self.assertIn(
            "placeholder_semantic_text", finding_codes(placeholder_findings)
        )
        placeholder_targets = {
            target
            for finding in placeholder_findings
            if finding["code"] == "placeholder_semantic_text"
            for target in finding["targets"]
        }
        self.assertTrue(
            {
                "objective.summary",
                "status_reason",
                "requirements[0].outcome",
                "tasks[0].action",
                "tasks[0].target_artifacts[0]",
                "tasks[0].acceptance_criteria[0]",
                "tasks[0].verification_steps[0]",
            }
            <= placeholder_targets
        )
        for placeholder_variant in (
            "T.B.D.",
            "T B D",
            "TO DO",
            "N/A",
            "N.A.",
            "NA",
            "not applicable",
            "none",
        ):
            with self.subTest(placeholder_variant=placeholder_variant):
                variant_payload = copy.deepcopy(self.example)
                variant_payload["objective"]["summary"] = placeholder_variant
                variant_plan = canonical_fixture(
                    self.plan_state, self.context, variant_payload
                )
                variant_findings = self.plan_state.readiness_findings(
                    variant_plan
                )
                variant_targets = {
                    target
                    for finding in variant_findings
                    if finding["code"] == "placeholder_semantic_text"
                    for target in finding["targets"]
                }
                self.assertIn("objective.summary", variant_targets)

        substantive_payload = copy.deepcopy(self.example)
        substantive_payload["status_reason"] = (
            "Draft created to replace an existing placeholder command."
        )
        substantive_payload["objective"]["summary"] = (
            "Replace the existing csv_filter.py placeholder with working behavior."
        )
        substantive_payload["scope"]["in_scope"] = [
            "Replace the command placeholder without changing unrelated routes."
        ]
        substantive_payload["sources"][0]["title"] = (
            "Existing command placeholder specification"
        )
        substantive_payload["tasks"][0]["action"] = (
            "Replace the existing placeholder implementation with the required filter."
        )
        substantive_payload["tasks"][0]["target_artifacts"] = [
            "src/csv_filter_placeholder.py"
        ]
        substantive_plan = canonical_fixture(
            self.plan_state, self.context, substantive_payload
        )
        substantive_findings = self.plan_state.readiness_findings(
            substantive_plan
        )
        self.assertNotIn(
            "placeholder_semantic_text", finding_codes(substantive_findings)
        )
        self.assertEqual(substantive_plan["validation"]["status"], "pass")

    def test_tst_045_other_state_system_mismatch_is_isolated(self):
        """TST-045: conflicting external-ledger status remains data only."""
        task_ledger = self.root / "Tasks" / "task.json"
        trd_state = self.root / "TRDs" / "source.md"
        goal_state = self.root / "goal-state.json"
        task_ledger.parent.mkdir()
        trd_state.parent.mkdir()
        task_ledger.write_text('{"status":"completed"}\n', encoding="utf-8")
        trd_state.write_text("state: draft\n", encoding="utf-8")
        goal_state.write_text('{"status":"active"}\n', encoding="utf-8")
        before = tree_snapshot(self.root)
        payload = copy.deepcopy(self.example)
        payload["sources"][0]["facts_used"].append(
            "A separate Task ledger reports completed while this plan remains draft."
        )
        plan = canonical_fixture(self.plan_state, self.context, payload)
        self.assertEqual(plan["status"], "draft")
        self.assertEqual(tree_snapshot(self.root), before)
        contract = (SKILL / "references" / "plan-contract.md").read_text(encoding="utf-8")
        self.assertIn("does not own a project Task ledger", contract)
        self.assertIn("TST-045", DIRECTOR_LEVEL_SCENARIOS)

    def test_tst_046_projection_rendering_is_split_deterministic_and_round_trips(self):
        """TST-046: overview, phase, traceability, and index are byte-stable."""
        payload = copy.deepcopy(self.example)
        payload["title"] = "Report | [external](https://example.invalid)"
        plan = self.make_plan(payload)
        created_time = self.plan_state.parse_timestamp(plan["created_at"], "created")
        earlier_time = created_time + self.plan_state.dt.timedelta(minutes=1)
        later_time = created_time + self.plan_state.dt.timedelta(minutes=2)
        update_time = created_time + self.plan_state.dt.timedelta(minutes=3)
        plus_two = self.plan_state.dt.timezone(
            self.plan_state.dt.timedelta(hours=2)
        )
        evidence_digest = self.plan_state.target_definition_digest(
            plan["tasks"][0], "task", plan
        )
        plan["tasks"][0]["evidence"] = [
            {
                "evidence_id": "EVID-010",
                "timestamp": earlier_time.astimezone(plus_two).isoformat(),
                "evidence_type": "inspection",
                "result_status": "passed",
                "description": "Earlier absolute-time observation.",
                "locator_or_command": "mixed-offset fixture one",
                "observed_result": "The earlier observation passed.",
                "verification_level": "inspected_only",
                "observation_source": "tool",
                "target_digest": evidence_digest,
            },
            {
                "evidence_id": "EVID-011",
                "timestamp": self.plan_state.timestamp(later_time),
                "evidence_type": "inspection",
                "result_status": "passed",
                "description": "Later absolute-time observation.",
                "locator_or_command": "mixed-offset fixture two",
                "observed_result": "The later observation passed.",
                "verification_level": "inspected_only",
                "observation_source": "tool",
                "target_digest": evidence_digest,
            },
        ]
        plan["revision"] = 2
        plan["updated_at"] = self.plan_state.timestamp(update_time)
        plan["history"].append(
            self.plan_state.history_entry(
                plan,
                revision=2,
                event_time=plan["updated_at"],
                action_id="TO-IP-004",
                affected_ids=["TASK-001", "EVID-010", "EVID-011"],
                status_before="draft",
                status_after="draft",
                summary="Recorded mixed-offset projection-order evidence.",
                authority_basis="Explicit isolated projection-order fixture.",
            )
        )
        self.plan_state.refresh_validation(plan, plan["updated_at"])
        date = plan["plan_id"].split("-")[1]
        directory = f"Plan_{plan['slug']}_{date[:4]}-{date[4:6]}-{date[6:]}_A1B2C3D4"
        plan_dir = self.context.plans_root / directory
        plan_dir.mkdir(parents=True)
        canonical = self.plan_state.canonical_bytes(plan)
        canonical_path = plan_dir / "plan.json"
        canonical_path.write_bytes(canonical)
        record = self.plan_state.PlanRecord(
            directory=directory,
            path=plan_dir,
            canonical_path=canonical_path,
            plan=plan,
            raw=canonical,
            sha256=hashlib.sha256(canonical).hexdigest(),
            directory_identity=(plan_dir.stat().st_dev, plan_dir.stat().st_ino),
        )
        first = self.plan_state.expected_plan_projections(record)
        second = self.plan_state.expected_plan_projections(record)
        self.assertEqual(first, second)
        phase_projection = next(
            data
            for path, data in first.items()
            if path.parent.name == "phases"
        ).decode("utf-8")
        self.assertLess(
            phase_projection.index("EVID-010"),
            phase_projection.index("EVID-011"),
        )
        names = {path.relative_to(plan_dir).as_posix() for path in first}
        self.assertEqual(
            names,
            {
                "PLAN.md",
                "TRACEABILITY.md",
                "phases/PHASE-001_implement-and-verify-the-health-check.md",
            },
        )
        merged = b"\n".join(first.values())
        for identifier in ("PLAN-", "PHASE-001", "TASK-001", "TASK-002", "REQ-001"):
            with self.subTest(identifier=identifier):
                self.assertIn(identifier.encode(), merged)
        self.assertIn(b"Report \\| [external](https://example.invalid)", self.plan_state.render_index([record]))
        self.plan_state.write_plan_projections(record)
        self.plan_state.write_index(self.context, [record])
        before = tree_snapshot(self.root)
        self.assertEqual(self.plan_state.write_plan_projections(record), [])
        self.assertFalse(self.plan_state.write_index(self.context, [record]))
        self.assertEqual(tree_snapshot(self.root), before)
        loaded = self.plan_state.load_plan_record(self.context, plan_dir)
        self.assertEqual(loaded.plan, plan)

    def test_tst_047_unmanaged_markdown_is_preserved_and_not_catalogued(self):
        """TST-047: unmanaged files and unknown directories stay byte-identical."""
        self.context.plans_root.mkdir()
        standalone = self.context.plans_root / "existing-plan.md"
        standalone.write_text("# Project-owned plan\n\nDo not adopt me.\n", encoding="utf-8")
        unknown = self.context.plans_root / "archive"
        unknown.mkdir()
        (unknown / "notes.md").write_text("project-owned\n", encoding="utf-8")
        before = tree_snapshot(self.root)
        records, unmanaged = self.plan_state.discover_managed_plans(self.context)
        self.assertEqual(records, [])
        self.assertEqual(unmanaged, ["archive", "existing-plan.md"])
        self.assertEqual(tree_snapshot(self.root), before)
        self.assertFalse((self.context.plans_root / "INDEX.md").exists())

        unmanaged_index = self.context.plans_root / "INDEX.md"
        unmanaged_index.write_text(
            "# Project-owned implementation-plan index\n\nDo not replace me.\n",
            encoding="utf-8",
        )
        before_reindex = tree_snapshot(self.root)
        with self.assertRaises(self.plan_state.AppError) as caught:
            self.plan_state.handle_reindex(self.context, SimpleNamespace())
        self.assertEqual(caught.exception.category, "unsafe_or_corrupt")
        self.assertEqual(tree_snapshot(self.root), before_reindex)


class CliWorkflowTests(unittest.TestCase):
    """Public CLI lifecycle, concurrency, transaction, and recovery tests."""

    @classmethod
    def setUpClass(cls):
        cls.plan_state = load_helper()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.example = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))

    def cli(
        self,
        *arguments: str,
        payload: dict | None = None,
        expected: int = 0,
        root: Path | None = None,
        script: Path | None = None,
    ) -> dict:
        project_root = (root or self.root).resolve()
        command_script = script or SCRIPT
        process = subprocess.run(
            [
                sys.executable,
                str(command_script),
                "--project-root",
                str(project_root),
                *arguments,
            ],
            input=json.dumps(payload) if payload is not None else None,
            text=True,
            capture_output=True,
            timeout=30,
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
        )
        self.assertEqual(process.returncode, expected, process.stdout + process.stderr)
        self.assertEqual(process.stderr, "", process.stderr)
        envelope = json.loads(process.stdout)
        self.assertEqual(
            set(envelope),
            {
                "schema_version",
                "command",
                "project_root",
                "plans_root",
                "status",
                "mutation",
                "warnings",
                "errors",
                "recovery_required",
                "plan",
                "data",
            },
        )
        self.assertEqual(envelope["schema_version"], 1)
        self.assertEqual(envelope["project_root"], str(project_root))
        return envelope

    def create(
        self,
        *,
        root: Path | None = None,
        payload: dict | None = None,
        script: Path | None = None,
    ) -> dict:
        result = self.cli(
            "create",
            "--input",
            "-",
            payload=copy.deepcopy(payload or self.example),
            root=root,
            script=script,
        )
        self.assertEqual(result["status"], "ok")
        self.assertTrue(result["mutation"])
        return result["plan"]

    def show(
        self,
        receipt: dict,
        *,
        root: Path | None = None,
        script: Path | None = None,
    ) -> dict:
        return self.cli("show", receipt["plan_id"], root=root, script=script)

    def update_task(
        self,
        receipt: dict,
        task_id: str,
        patch_value: dict,
        *,
        confirmed: bool = True,
        expected: int = 0,
        root: Path | None = None,
        script: Path | None = None,
    ) -> dict:
        payload = {
            "patch": copy.deepcopy(patch_value),
            "summary": f"Synthetic transition for {task_id}.",
            "authority_basis": "Explicit isolated unittest authority.",
            "confirmed": confirmed,
        }
        return self.cli(
            "update-task",
            receipt["plan_id"],
            task_id,
            "--expect-revision",
            str(receipt["revision"]),
            "--expect-sha256",
            receipt["sha256"],
            "--input",
            "-",
            payload=payload,
            expected=expected,
            root=root,
            script=script,
        )

    def update_baseline(
        self,
        receipt: dict,
        patch_value: dict,
        *,
        material_change: bool = False,
        expected: int = 0,
        root: Path | None = None,
        script: Path | None = None,
    ) -> dict:
        return self.cli(
            "update",
            receipt["plan_id"],
            "--expect-revision",
            str(receipt["revision"]),
            "--expect-sha256",
            receipt["sha256"],
            "--input",
            "-",
            payload={
                "patch": copy.deepcopy(patch_value),
                "summary": "Synthetic bounded baseline update.",
                "authority_basis": "Explicit isolated unittest authority.",
                "material_change": material_change,
            },
            expected=expected,
            root=root,
            script=script,
        )

    def set_status(
        self,
        receipt: dict,
        status: str,
        *,
        reason: str | None = None,
        expected: int = 0,
        root: Path | None = None,
        script: Path | None = None,
    ) -> dict:
        return self.cli(
            "set-status",
            receipt["plan_id"],
            "--expect-revision",
            str(receipt["revision"]),
            "--expect-sha256",
            receipt["sha256"],
            "--status",
            status,
            "--reason",
            reason or f"Explicit synthetic transition to {status}.",
            "--confirmed",
            expected=expected,
            root=root,
            script=script,
        )

    def record_evidence(
        self,
        receipt: dict,
        target_id: str,
        sequence: int,
        *,
        root: Path | None = None,
        script: Path | None = None,
    ) -> dict:
        canonical = self.show(receipt, root=root, script=script)["data"]["canonical"]
        collection = "tasks" if target_id.startswith("TASK-") else "requirements"
        id_key = "task_id" if collection == "tasks" else "requirement_id"
        target = next(item for item in canonical[collection] if item[id_key] == target_id)
        criterion = target["acceptance_criteria"][sequence - 1]
        verification_step = None
        if collection == "tasks" and sequence <= len(target["verification_steps"]):
            verification_step = target["verification_steps"][sequence - 1]
        description = f"Acceptance criterion: {criterion}"
        observed_result = f"Observed passing result for acceptance criterion: {criterion}"
        if verification_step is not None:
            description += f" Planned verification step: {verification_step}"
            observed_result += f" Verification step reported: {verification_step}"
        return self.cli(
            "record-evidence",
            receipt["plan_id"],
            target_id,
            "--expect-revision",
            str(receipt["revision"]),
            "--expect-sha256",
            receipt["sha256"],
            "--input",
            "-",
            payload={
                "evidence_type": "test",
                "result_status": "passed",
                "description": description,
                "locator_or_command": f"test fixture step {sequence}",
                "observed_result": observed_result,
                "verification_level": "targeted_tests_passed",
                "observation_source": "tool",
                "authority_basis": "Explicit isolated unittest evidence authority.",
                "summary": f"Record synthetic criterion evidence {sequence}.",
            },
            root=root,
            script=script,
        )

    def make_in_progress(
        self,
        *,
        root: Path | None = None,
        payload: dict | None = None,
        script: Path | None = None,
    ) -> dict:
        receipt = self.create(root=root, payload=payload, script=script)
        receipt = self.set_status(receipt, "ready", root=root, script=script)["plan"]
        return self.set_status(receipt, "in_progress", root=root, script=script)["plan"]

    def complete_task(
        self,
        receipt: dict,
        task_id: str,
        criterion_count: int,
        *,
        root: Path | None = None,
        script: Path | None = None,
    ) -> dict:
        receipt = self.update_task(
            receipt, task_id, {"status": "in_progress"}, root=root, script=script
        )["plan"]
        for sequence in range(1, criterion_count + 1):
            receipt = self.record_evidence(
                receipt, task_id, sequence, root=root, script=script
            )["plan"]
        return self.update_task(
            receipt, task_id, {"status": "completed"}, root=root, script=script
        )["plan"]

    def prepare_plan_completion(
        self,
        *,
        root: Path | None = None,
        script: Path | None = None,
        final_inspection: bool = True,
    ) -> dict:
        receipt = self.make_in_progress(root=root, script=script)
        receipt = self.complete_task(receipt, "TASK-001", 2, root=root, script=script)
        receipt = self.complete_task(receipt, "TASK-002", 2, root=root, script=script)
        for sequence in range(1, 4):
            receipt = self.record_evidence(
                receipt, "REQ-001", sequence, root=root, script=script
            )["plan"]
        canonical = self.show(receipt, root=root, script=script)["data"]["canonical"]
        requirements = copy.deepcopy(canonical["requirements"])
        requirements[0]["status"] = "satisfied"
        receipt = self.update_baseline(
            receipt,
            {"requirements": requirements},
            root=root,
            script=script,
        )["plan"]
        if not final_inspection:
            return receipt
        canonical = self.show(receipt, root=root, script=script)["data"]["canonical"]
        project = copy.deepcopy(canonical["project"])
        project_root = Path(project["root_hint"])
        protected = project_root / "config" / "production.json"
        protected.parent.mkdir(parents=True, exist_ok=True)
        if not protected.exists():
            protected.write_text('{"mode":"test-fixture"}\n', encoding="utf-8")
        observed_at = self.plan_state.timestamp()
        project["inspected_at"] = observed_at
        project["baseline_facts"].extend(
            [
                {
                    "fact": "The final project state was reinspected after all current task and requirement evidence.",
                    "evidence_locator": str(project_root),
                    "observed_at": observed_at,
                },
                {
                    "fact": "The protected config/production.json file remained unchanged; its SHA-256 was reinspected.",
                    "evidence_locator": "config/production.json",
                    "observed_at": observed_at,
                },
            ]
        )
        return self.update_baseline(
            receipt,
            {"project": project},
            root=root,
            script=script,
        )["plan"]

    def disposed_payload(self) -> dict:
        payload = copy.deepcopy(self.example)
        disposition = {
            "kind": "out_of_scope",
            "reason": "The current user approved this synthetic exception.",
            "authority_basis": "Explicit isolated unittest skip authority.",
        }
        payload["requirements"][0]["status"] = "dispositioned"
        payload["requirements"][0]["disposition"] = copy.deepcopy(disposition)
        payload["coverage"]["requirement_to_task"][0]["disposition"] = copy.deepcopy(disposition)
        return payload

    def task_patch(self, status: str) -> dict:
        result = {"status": status}
        if status == "blocked":
            result["blocker_reason"] = "A named synthetic dependency is unavailable."
        elif status == "paused":
            result["pause_reason"] = "The isolated test intentionally paused work."
        elif status == "skipped":
            result["skip_reason"] = "The synthetic exception disposes this work."
            result["skip_authority"] = "Current explicit unittest skip approval."
        return result

    def make_plan_state(self, state: str, root: Path) -> dict:
        """Reach one plan state only through public legal transitions."""
        if state == "completed":
            receipt = self.prepare_plan_completion(root=root)
            return self.set_status(receipt, "completed", root=root)["plan"]
        receipt = self.create(root=root)
        if state == "draft":
            return receipt
        if state in {"retired", "cancelled"}:
            return self.set_status(receipt, state, root=root)["plan"]
        receipt = self.set_status(receipt, "ready", root=root)["plan"]
        if state == "ready":
            return receipt
        receipt = self.set_status(receipt, "in_progress", root=root)["plan"]
        if state == "in_progress":
            return receipt
        if state in {"paused", "blocked"}:
            return self.set_status(receipt, state, root=root)["plan"]
        raise AssertionError(f"Unsupported fixture plan state: {state}")

    def make_task_state(
        self,
        state: str,
        root: Path,
        *,
        disposed: bool = False,
        completion_ready: bool = False,
    ) -> dict:
        """Reach TASK-001 state through public operations while the plan runs."""
        receipt = self.make_in_progress(
            root=root,
            payload=self.disposed_payload() if disposed else None,
        )
        if state == "planned":
            return receipt
        if state == "blocked":
            return self.update_task(
                receipt,
                "TASK-001",
                self.task_patch("blocked"),
                root=root,
            )["plan"]
        if state == "skipped":
            return self.update_task(
                receipt,
                "TASK-001",
                self.task_patch("skipped"),
                root=root,
            )["plan"]
        receipt = self.update_task(
            receipt,
            "TASK-001",
            self.task_patch("in_progress"),
            root=root,
        )["plan"]
        if state == "in_progress" and completion_ready:
            for sequence in range(1, 3):
                receipt = self.record_evidence(
                    receipt, "TASK-001", sequence, root=root
                )["plan"]
            return receipt
        if state == "in_progress":
            return receipt
        if state == "paused":
            return self.update_task(
                receipt,
                "TASK-001",
                self.task_patch("paused"),
                root=root,
            )["plan"]
        if state == "completed":
            for sequence in range(1, 3):
                receipt = self.record_evidence(
                    receipt, "TASK-001", sequence, root=root
                )["plan"]
            return self.update_task(
                receipt,
                "TASK-001",
                self.task_patch("completed"),
                root=root,
            )["plan"]
        raise AssertionError(f"Unsupported fixture task state: {state}")

    def test_tst_022_dependent_task_cannot_start_before_predecessor(self):
        """TST-022: predecessor order rejects early TASK-002 execution."""
        receipt = self.make_in_progress()
        before = tree_snapshot(self.root)
        result = self.update_task(
            receipt,
            "TASK-002",
            {"status": "in_progress"},
            expected=9,
        )
        self.assertEqual(result["errors"][0]["category"], "unmet_gate")
        self.assertIn("TASK-001", result["errors"][0]["targets"])
        self.assertEqual(tree_snapshot(self.root), before)

        phase_root = self.root / "phase-predecessor-gate"
        phase_root.mkdir()
        phase_payload = copy.deepcopy(self.example)
        phase_payload["phases"][0]["task_ids"] = ["TASK-001"]
        phase_payload["phases"].append(
            {
                "phase_id": "PHASE-002",
                "title": "Dependent phase",
                "objective": "Exercise the phase-level predecessor gate.",
                "scope": ["Dependent task"],
                "depends_on_phase_ids": ["PHASE-001"],
                "entry_conditions": ["PHASE-001 is completed."],
                "exit_criteria": ["TASK-002 is completed."],
                "task_ids": ["TASK-002"],
                "risks": [],
            }
        )
        phase_payload["tasks"][1]["phase_id"] = "PHASE-002"
        phase_payload["tasks"][1]["dependencies"] = []
        phase_receipt = self.make_in_progress(
            root=phase_root, payload=phase_payload
        )
        phase_result = self.update_task(
            phase_receipt,
            "TASK-002",
            {"status": "in_progress"},
            root=phase_root,
            expected=9,
        )
        self.assertIn("PHASE-001", phase_result["errors"][0]["targets"])

        tampered = self.show(phase_receipt, root=phase_root)["data"]["canonical"]
        tampered["tasks"][1]["status"] = "in_progress"
        self.plan_state.recompute_phase_statuses(tampered)
        structural_codes = finding_codes(
            self.plan_state.validate_plan_structure(
                tampered,
                self.plan_state.resolve_context(
                    str(phase_root), "Implementation_Plans"
                ),
                directory_name=Path(phase_receipt["canonical_path"]).parent.name,
            )
        )
        self.assertIn("phase_predecessor_incomplete", structural_codes)

    def test_tst_023_same_title_creation_is_collision_safe(self):
        """TST-023: same-title plans receive distinct IDs and directories."""
        self.assertEqual(self.plan_state.safe_slug("Café / Plan"), "cafe-plan")
        self.assertEqual(self.plan_state.safe_slug("!!!"), "plan")
        first = self.create()
        second = self.create()
        self.assertRegex(first["plan_id"], r"^PLAN-\d{8}-[A-F0-9]{8}$")
        self.assertRegex(first["directory"], r"^Plan_[a-z0-9-]+_\d{4}-\d{2}-\d{2}_[A-F0-9]{8}$")
        self.assertNotEqual(first["plan_id"], second["plan_id"])
        self.assertNotEqual(first["directory"], second["directory"])
        self.assertTrue(Path(first["canonical_path"]).is_file())
        self.assertTrue(Path(second["canonical_path"]).is_file())
        listed = self.cli("list")
        self.assertEqual(listed["data"]["count"], 2)

        collision_root = self.root / "unmanaged-collision"
        collision_root.mkdir()
        context = self.plan_state.resolve_context(
            str(collision_root), "Implementation_Plans"
        )
        context.plans_root.mkdir()
        date_display = self.plan_state.utc_now().date().isoformat()
        unmanaged = context.plans_root / (
            f"Plan_{self.plan_state.safe_slug(self.example['title'])}_"
            f"{date_display}_11111111"
        )
        unmanaged.mkdir()
        marker = unmanaged / "project-owned.txt"
        marker.write_text("preserve me\n", encoding="utf-8")
        payload_path = collision_root / "create.json"
        payload_path.write_text(json.dumps(self.example), encoding="utf-8")
        fake_hexes = ["1" * 32, "A" * 32, "2" * 32] + [
            f"{number:032X}" for number in range(3, 20)
        ]
        fake_ids = [SimpleNamespace(hex=value) for value in fake_hexes]
        with patch.object(self.plan_state.uuid, "uuid4", side_effect=fake_ids):
            envelope, exit_code = self.plan_state.handle_create(
                context, SimpleNamespace(input=str(payload_path))
            )
        self.assertEqual(exit_code, 0)
        self.assertEqual(envelope["plan"]["plan_id"].rsplit("-", 1)[1], "22222222")
        self.assertTrue(marker.is_file())
        self.assertEqual(marker.read_text(encoding="utf-8"), "preserve me\n")

        identity_root = self.root / "cross-slug-id-collision"
        identity_root.mkdir()
        first = self.create(root=identity_root)
        reused_suffix = first["plan_id"].rsplit("-", 1)[1]
        second_payload = copy.deepcopy(self.example)
        second_payload["title"] = "A different slug with a colliding UUID suffix"
        payload_path = identity_root / "second.json"
        payload_path.write_text(json.dumps(second_payload), encoding="utf-8")
        context = self.plan_state.resolve_context(
            str(identity_root), "Implementation_Plans"
        )
        fake_ids = [
            SimpleNamespace(hex=reused_suffix * 4),
            SimpleNamespace(hex="C" * 32),
            SimpleNamespace(hex="D" * 32),
            *[SimpleNamespace(hex=f"{number:032X}") for number in range(4, 20)],
        ]
        with patch.object(self.plan_state.uuid, "uuid4", side_effect=fake_ids):
            second, exit_code = self.plan_state.handle_create(
                context, SimpleNamespace(input=str(payload_path))
            )
        self.assertEqual(exit_code, 0)
        self.assertNotEqual(second["plan"]["plan_id"], first["plan_id"])
        self.assertEqual(second["plan"]["plan_id"].rsplit("-", 1)[1], "DDDDDDDD")
        self.assertEqual(self.cli("list", root=identity_root)["data"]["count"], 2)

    def test_tst_024_exact_plan_id_resumes_canonical_state_without_context(self):
        """TST-024: exact ID reconstructs durable plan/task state."""
        receipt = self.make_in_progress()
        receipt = self.update_task(
            receipt, "TASK-001", {"status": "in_progress"}
        )["plan"]
        resumed = self.cli("show", receipt["plan_id"])
        canonical = resumed["data"]["canonical"]
        self.assertEqual(canonical["plan_id"], receipt["plan_id"])
        self.assertEqual(canonical["status"], "in_progress")
        self.assertEqual(canonical["tasks"][0]["status"], "in_progress")
        self.assertNotIn("transcript", canonical)
        self.assertNotIn("memory", canonical)

    def test_tst_025_exact_and_ambiguous_selector_contract(self):
        """TST-025: exact selectors resolve; partial, fuzzy, and ambiguous do not."""
        first = self.create()
        unique_payload = copy.deepcopy(self.example)
        unique_payload["title"] = "A Unique Complete Title"
        unique = self.create(payload=unique_payload)
        for selector in (
            first["plan_id"],
            first["directory"],
            "a unique complete title",
        ):
            with self.subTest(selector=selector):
                self.assertEqual(self.cli("show", selector)["status"], "ok")
        self.create()
        before = tree_snapshot(self.root)
        ambiguous = self.cli("show", self.example["title"], expected=4)
        self.assertEqual(ambiguous["errors"][0]["category"], "ambiguous_selector")
        for selector in (first["plan_id"][:-2], "project health", "Add health command"):
            with self.subTest(selector=selector):
                self.assertEqual(self.cli("show", selector, expected=3)["status"], "error")
        for selector in ("../escape", ".hidden", "bad\\selector"):
            with self.subTest(selector=selector):
                self.assertEqual(self.cli("show", selector, expected=5)["status"], "error")
        self.assertEqual(tree_snapshot(self.root), before)

    def test_tst_026_every_allowed_plan_transition_and_self_no_op(self):
        """TST-026: every listed plan edge succeeds with its required gates."""
        sequence = 0
        for before_state in sorted(self.plan_state.PLAN_STATES):
            for after_state in sorted(self.plan_state.PLAN_TRANSITIONS[before_state]):
                sequence += 1
                with self.subTest(before=before_state, after=after_state):
                    case_root = self.root / f"allowed-plan-{sequence:02d}"
                    case_root.mkdir()
                    if before_state == "in_progress" and after_state == "completed":
                        receipt = self.prepare_plan_completion(root=case_root)
                    else:
                        receipt = self.make_plan_state(before_state, case_root)
                    result = self.set_status(receipt, after_state, root=case_root)
                    self.assertEqual(result["status"], "ok")
                    self.assertTrue(result["mutation"])
                    canonical = self.show(result["plan"], root=case_root)["data"]["canonical"]
                    self.assertEqual(canonical["status"], after_state)
                    self.assertEqual(canonical["revision"], receipt["revision"] + 1)

        for before_state in sorted(self.plan_state.PLAN_STATES):
            sequence += 1
            with self.subTest(before=before_state, after=before_state, behavior="no_op"):
                case_root = self.root / f"noop-plan-{sequence:02d}"
                case_root.mkdir()
                receipt = self.make_plan_state(before_state, case_root)
                canonical = self.show(receipt, root=case_root)["data"]["canonical"]
                before = tree_snapshot(case_root)
                result = self.set_status(
                    receipt,
                    before_state,
                    reason=canonical["status_reason"],
                    root=case_root,
                )
                self.assertEqual(result["status"], "no_op")
                self.assertFalse(result["mutation"])
                self.assertEqual(tree_snapshot(case_root), before)

    def test_tst_027_every_prohibited_plan_transition_is_byte_preserving(self):
        """TST-027: every unlisted plan edge rejects with one stable category."""
        sequence = 0
        for before_state in sorted(self.plan_state.PLAN_STATES):
            sequence += 1
            case_root = self.root / f"prohibited-plan-{sequence:02d}"
            case_root.mkdir()
            receipt = self.make_plan_state(before_state, case_root)
            prohibited = sorted(
                self.plan_state.PLAN_STATES
                - self.plan_state.PLAN_TRANSITIONS[before_state]
                - {before_state}
            )
            for after_state in prohibited:
                with self.subTest(before=before_state, after=after_state):
                    before = tree_snapshot(case_root)
                    result = self.set_status(
                        receipt,
                        after_state,
                        expected=8,
                        root=case_root,
                    )
                    self.assertEqual(result["errors"][0]["category"], "prohibited_transition")
                    self.assertEqual(tree_snapshot(case_root), before)

    def test_tst_028_every_task_transition_rollup_and_rejection(self):
        """TST-028: every listed/unlisted task edge and same-state no-op is exercised."""
        sequence = 0
        for before_state in sorted(self.plan_state.TASK_STATES):
            for after_state in sorted(self.plan_state.TASK_TRANSITIONS[before_state]):
                sequence += 1
                with self.subTest(before=before_state, after=after_state):
                    case_root = self.root / f"allowed-task-{sequence:02d}"
                    case_root.mkdir()
                    disposed = before_state == "skipped" or after_state == "skipped"
                    receipt = self.make_task_state(
                        before_state,
                        case_root,
                        disposed=disposed,
                        completion_ready=(
                            before_state == "in_progress" and after_state == "completed"
                        ),
                    )
                    result = self.update_task(
                        receipt,
                        "TASK-001",
                        self.task_patch(after_state),
                        root=case_root,
                    )
                    self.assertEqual(result["status"], "ok")
                    canonical = self.show(result["plan"], root=case_root)["data"]["canonical"]
                    task = next(item for item in canonical["tasks"] if item["task_id"] == "TASK-001")
                    phase = canonical["phases"][0]
                    self.assertEqual(task["status"], after_state)
                    owned = [
                        item
                        for item in canonical["tasks"]
                        if item["phase_id"] == phase["phase_id"]
                    ]
                    self.assertEqual(
                        phase["status"],
                        self.plan_state.derive_phase_status(owned, canonical),
                    )

        for before_state in sorted(self.plan_state.TASK_STATES):
            sequence += 1
            case_root = self.root / f"prohibited-task-{sequence:02d}"
            case_root.mkdir()
            receipt = self.make_task_state(
                before_state,
                case_root,
                disposed=before_state == "skipped",
            )
            same_before = tree_snapshot(case_root)
            same = self.update_task(
                receipt,
                "TASK-001",
                {"status": before_state},
                root=case_root,
            )
            self.assertEqual(same["status"], "no_op")
            self.assertEqual(tree_snapshot(case_root), same_before)
            prohibited = sorted(
                self.plan_state.TASK_STATES
                - self.plan_state.TASK_TRANSITIONS[before_state]
                - {before_state}
            )
            for after_state in prohibited:
                with self.subTest(before=before_state, after=after_state):
                    before = tree_snapshot(case_root)
                    result = self.update_task(
                        receipt,
                        "TASK-001",
                        self.task_patch(after_state),
                        expected=8,
                        root=case_root,
                    )
                    self.assertEqual(result["errors"][0]["category"], "prohibited_transition")
                    self.assertEqual(tree_snapshot(case_root), before)

        paused_root = self.root / "paused-predecessor-rollup"
        paused_root.mkdir()
        receipt = self.make_in_progress(root=paused_root)
        receipt = self.update_task(
            receipt, "TASK-001", {"status": "in_progress"}, root=paused_root
        )["plan"]
        receipt = self.update_task(
            receipt,
            "TASK-001",
            {"status": "paused", "pause_reason": "Awaiting an explicit resume."},
            root=paused_root,
        )["plan"]
        canonical = self.show(receipt, root=paused_root)["data"]["canonical"]
        self.assertEqual(canonical["tasks"][1]["status"], "planned")
        self.assertEqual(canonical["phases"][0]["status"], "paused")

    def test_tst_029_task_completion_requires_acceptance_evidence(self):
        """TST-029: a started task cannot complete without current evidence."""
        receipt = self.make_in_progress()
        receipt = self.update_task(receipt, "TASK-001", {"status": "in_progress"})["plan"]
        before = tree_snapshot(self.root)
        result = self.update_task(
            receipt, "TASK-001", {"status": "completed"}, expected=9
        )
        self.assertEqual(result["errors"][0]["category"], "unmet_gate")
        self.assertEqual(tree_snapshot(self.root), before)

        criterion = self.show(receipt)["data"]["canonical"]["tasks"][0][
            "acceptance_criteria"
        ][0]
        for marker in (
            "Pass.",
            "OK!!",
            "success:",
            "OK, done.",
            "Success: pass",
            "Pass successful.",
            "P.a.s.s.",
        ):
            with self.subTest(meaningless_marker=marker):
                marker_before = tree_snapshot(self.root)
                rejected_marker = self.cli(
                    "record-evidence",
                    receipt["plan_id"],
                    "TASK-001",
                    "--expect-revision",
                    str(receipt["revision"]),
                    "--expect-sha256",
                    receipt["sha256"],
                    "--input",
                    "-",
                    payload={
                        "evidence_type": "test",
                        "result_status": "passed",
                        "description": f"Acceptance criterion: {criterion}",
                        "locator_or_command": "python -m unittest focused-test",
                        "observed_result": marker,
                        "verification_level": "targeted_tests_passed",
                        "observation_source": "tool",
                    },
                    expected=2,
                )
                self.assertEqual(
                    rejected_marker["errors"][0]["category"], "invalid_input"
                )
                self.assertEqual(tree_snapshot(self.root), marker_before)

        for failure_summary in (
            f"{criterion} Ran 50 tests. FAILED (failures=1).",
            f"{criterion} Ran 50 tests with errors=1.",
        ):
            with self.subTest(contradictory_summary=failure_summary):
                summary_before = tree_snapshot(self.root)
                rejected_summary = self.cli(
                    "record-evidence",
                    receipt["plan_id"],
                    "TASK-001",
                    "--expect-revision",
                    str(receipt["revision"]),
                    "--expect-sha256",
                    receipt["sha256"],
                    "--input",
                    "-",
                    payload={
                        "evidence_type": "test",
                        "result_status": "passed",
                        "description": f"Acceptance criterion: {criterion}",
                        "locator_or_command": "python -m unittest focused-test",
                        "observed_result": failure_summary,
                        "verification_level": "broader_suite_passed",
                        "observation_source": "tool",
                    },
                    expected=2,
                )
                self.assertEqual(
                    rejected_summary["errors"][0]["category"], "invalid_input"
                )
                self.assertEqual(tree_snapshot(self.root), summary_before)

        for sequence in range(1, 3):
            receipt = self.cli(
                "record-evidence",
                receipt["plan_id"],
                "TASK-001",
                "--expect-revision",
                str(receipt["revision"]),
                "--expect-sha256",
                receipt["sha256"],
                "--input",
                "-",
                payload={
                    "evidence_type": "test",
                    "result_status": "passed",
                    "description": f"Unrelated synthetic observation {sequence}.",
                    "locator_or_command": f"unrelated step {sequence}",
                    "observed_result": f"An unrelated operation produced output {sequence}.",
                    "verification_level": "targeted_tests_passed",
                    "observation_source": "tool",
                },
            )["plan"]
        unrelated_before = tree_snapshot(self.root)
        unrelated = self.update_task(
            receipt, "TASK-001", {"status": "completed"}, expected=9
        )
        self.assertEqual(unrelated["errors"][0]["category"], "unmet_gate")
        self.assertEqual(tree_snapshot(self.root), unrelated_before)

        plan_source = self.cli(
            "record-evidence",
            receipt["plan_id"],
            "TASK-001",
            "--expect-revision",
            str(receipt["revision"]),
            "--expect-sha256",
            receipt["sha256"],
            "--input",
            "-",
            payload={
                "evidence_type": "test",
                "result_status": "passed",
                "description": "Plan-authored claim must not count as observed test evidence.",
                "locator_or_command": "planned test",
                "observed_result": "The plan claims a passing result without observation.",
                "verification_level": "targeted_tests_passed",
                "observation_source": "plan",
            },
            expected=2,
        )
        self.assertEqual(plan_source["errors"][0]["category"], "invalid_input")

        missing_locator = self.cli(
            "record-evidence",
            receipt["plan_id"],
            "TASK-001",
            "--expect-revision",
            str(receipt["revision"]),
            "--expect-sha256",
            receipt["sha256"],
            "--input",
            "-",
            payload={
                "evidence_type": "test",
                "result_status": "passed",
                "description": "Observed test evidence without a reviewable locator.",
                "locator_or_command": None,
                "observed_result": "The synthetic test was reported as passing.",
                "verification_level": "targeted_tests_passed",
                "observation_source": "tool",
            },
            expected=2,
        )
        self.assertEqual(missing_locator["errors"][0]["category"], "invalid_input")

        planned_runtime = self.cli(
            "record-evidence",
            receipt["plan_id"],
            "TASK-001",
            "--expect-revision",
            str(receipt["revision"]),
            "--expect-sha256",
            receipt["sha256"],
            "--input",
            "-",
            payload={
                "evidence_type": "test",
                "result_status": "planned",
                "description": "A command is only planned and was not run.",
                "locator_or_command": "pytest -q",
                "observed_result": "The command remains planned.",
                "verification_level": "planned",
                "observation_source": "tool",
            },
            expected=2,
        )
        self.assertEqual(planned_runtime["errors"][0]["category"], "invalid_input")
        verification_step = self.show(receipt)["data"]["canonical"]["tasks"][0][
            "verification_steps"
        ][0]
        self.assertEqual(
            self.plan_state.missing_verification_reports(
                [verification_step],
                [
                    {
                        "evidence_type": "test",
                        "result_status": "planned",
                        "description": verification_step,
                        "observed_result": "This remains planned.",
                    }
                ],
            ),
            [verification_step],
        )

        contradictory = self.cli(
            "record-evidence",
            receipt["plan_id"],
            "TASK-001",
            "--expect-revision",
            str(receipt["revision"]),
            "--expect-sha256",
            receipt["sha256"],
            "--input",
            "-",
            payload={
                "evidence_type": "test",
                "result_status": "passed",
                "description": "Acceptance criterion: Valid configuration produces exit status 0 and a concise success result.",
                "locator_or_command": "pytest -q",
                "observed_result": "pytest exited with code 1 after AssertionError. 2 failed, 5 passed.",
                "verification_level": "targeted_tests_passed",
                "observation_source": "tool",
            },
            expected=2,
        )
        self.assertEqual(contradictory["errors"][0]["category"], "invalid_input")

        final_root = self.root / "missing-final-inspection"
        final_root.mkdir()
        completion_ready = self.prepare_plan_completion(
            root=final_root, final_inspection=False
        )
        blocked_completion = self.set_status(
            completion_ready, "completed", root=final_root, expected=9
        )
        findings = blocked_completion["data"]["details"]["findings"]
        self.assertIn("final_project_reinspection_missing", finding_codes(findings))
        self.assertIn("protected_path_reinspection_missing", finding_codes(findings))
        equal_boundary = self.show(
            completion_ready, root=final_root
        )["data"]["canonical"]
        observation_times = [
            self.plan_state.parse_timestamp(evidence["timestamp"], "evidence")
            for collection in ("tasks", "requirements")
            for target in equal_boundary[collection]
            for evidence in target["evidence"]
        ]
        cutoff = max(observation_times)
        cutoff_text = cutoff.isoformat().replace("+00:00", "Z")
        equal_boundary["project"]["inspected_at"] = cutoff_text
        equal_boundary["project"]["baseline_facts"].extend(
            [
                {
                    "fact": "The final project state was reinspected at the evidence cutoff.",
                    "evidence_locator": str(final_root),
                    "observed_at": cutoff_text,
                },
                {
                    "fact": "config/production.json was preserved unchanged at the cutoff.",
                    "evidence_locator": "config/production.json",
                    "observed_at": cutoff_text,
                },
            ]
        )
        self.assertIn(
            "final_project_reinspection_missing",
            finding_codes(self.plan_state.completion_findings(equal_boundary)),
        )

        level_root = self.root / "failed-high-level-evidence"
        level_root.mkdir()
        level_receipt = self.make_in_progress(root=level_root)
        level_receipt = self.complete_task(
            level_receipt, "TASK-001", 2, root=level_root
        )
        level_receipt = self.cli(
            "record-evidence",
            level_receipt["plan_id"],
            "TASK-001",
            "--expect-revision",
            str(level_receipt["revision"]),
            "--expect-sha256",
            level_receipt["sha256"],
            "--input",
            "-",
            payload={
                "evidence_type": "runtime",
                "result_status": "failed",
                "description": "End-to-end workflow failed during the synthetic run.",
                "locator_or_command": "synthetic end-to-end fixture",
                "observed_result": "This workflow failed before end-to-end completion.",
                "verification_level": "runtime_observed",
                "observation_source": "tool",
            },
            root=level_root,
        )["plan"]
        level_plan = self.show(level_receipt, root=level_root)["data"]["canonical"]
        self.assertEqual(
            self.plan_state.highest_verification_level(level_plan),
            "targeted_tests_passed",
        )

        reason_root = self.root / "completion-reason"
        reason_root.mkdir()
        reason_receipt = self.prepare_plan_completion(root=reason_root)
        completion_ready_plan = self.show(
            reason_receipt, root=reason_root
        )["data"]["canonical"]
        protected_index = next(
            index
            for index, fact in enumerate(
                completion_ready_plan["project"]["baseline_facts"]
            )
            if fact["evidence_locator"] == "config/production.json"
        )
        for negative_fact in (
            "The protected config/production.json file was not preserved because it changed unexpectedly.",
            "The protected config/production.json file was not unchanged after reinspection.",
            "The protected config/production.json file had failed preservation during reinspection.",
            "The protected config/production.json file was preserved: false.",
            "The protected config/production.json file was preserved? No.",
            "The protected config/production.json file was preserved unsuccessfully.",
        ):
            with self.subTest(negative_preservation=negative_fact):
                negative_plan = copy.deepcopy(completion_ready_plan)
                negative_plan["project"]["baseline_facts"][protected_index][
                    "fact"
                ] = negative_fact
                self.assertIn(
                    "protected_path_reinspection_missing",
                    finding_codes(
                        self.plan_state.completion_findings(negative_plan)
                    ),
                )
        affirmative_plan = copy.deepcopy(completion_ready_plan)
        affirmative_plan["project"]["baseline_facts"][protected_index][
            "fact"
        ] = (
            "The protected config/production.json file was not modified; its SHA-256 remained identical."
        )
        self.assertNotIn(
            "protected_path_reinspection_missing",
            finding_codes(self.plan_state.completion_findings(affirmative_plan)),
        )

        competing_reasons = (
            "Highest verification level reached: end_to_end_verified.",
            "Completion confirmed after end-to-end verified review.",
            "Completion confirmed after runtime observed review.",
            "Completion confirmed after a broader-suite review.",
            "Completion confirmed after a broader test suite passed.",
            "Completion confirmed after targeted tests passed.",
            "Completion confirmed after a targeted test suite passed.",
            "Completion confirmed after static checks passed.",
            "Completion confirmed after inspected-only review.",
            "Completion confirmed after not-exercised review.",
            "Completion confirmed by the E2E verified workflow.",
            "Completion confirmed by the end2end verified workflow.",
        )
        for competing_reason in competing_reasons:
            with self.subTest(competing_reason=competing_reason):
                competing_before = tree_snapshot(reason_root)
                overclaim = self.set_status(
                    reason_receipt,
                    "completed",
                    reason=competing_reason,
                    root=reason_root,
                    expected=2,
                )
                self.assertEqual(
                    overclaim["errors"][0]["category"], "invalid_input"
                )
                self.assertEqual(tree_snapshot(reason_root), competing_before)
        completed = self.set_status(
            reason_receipt,
            "completed",
            reason="All planned work and checks are complete",
            root=reason_root,
        )["plan"]
        completed_plan = self.show(completed, root=reason_root)["data"]["canonical"]
        expected_level = self.plan_state.highest_verification_level(completed_plan)
        self.assertEqual(
            completed_plan["status_reason"].count(
                "Highest verification level reached:"
            ),
            1,
        )
        self.assertTrue(
            completed_plan["status_reason"].endswith(f"{expected_level}.")
        )

    def test_tst_030_phase_completes_only_after_all_tasks_complete(self):
        """TST-030: derived phase rollup follows all required task states."""
        receipt = self.make_in_progress()
        receipt = self.complete_task(receipt, "TASK-001", 2)
        halfway = self.show(receipt)["data"]["canonical"]
        self.assertEqual(halfway["phases"][0]["status"], "in_progress")
        receipt = self.complete_task(receipt, "TASK-002", 2)
        finished = self.show(receipt)["data"]["canonical"]
        self.assertEqual(finished["phases"][0]["status"], "completed")
        self.assertTrue(all(task["status"] == "completed" for task in finished["tasks"]))

    def test_tst_031_skip_requires_current_explicit_approval(self):
        """TST-031: a skip and later exception rewrite require confirmation."""
        receipt = self.make_in_progress(payload=self.disposed_payload())
        before = tree_snapshot(self.root)
        result = self.update_task(
            receipt,
            "TASK-001",
            {"status": "skipped"},
            confirmed=False,
            expected=9,
        )
        self.assertEqual(result["errors"][0]["category"], "unmet_gate")
        self.assertEqual(tree_snapshot(self.root), before)

        for placeholder_patch in (
            {"status": "blocked", "blocker_reason": "TBD"},
            {"status": "blocked", "blocker_reason": "N/A"},
            {
                "status": "skipped",
                "skip_reason": "TBD",
                "skip_authority": "TBD",
            },
            {
                "status": "skipped",
                "skip_reason": "N/A",
                "skip_authority": "not applicable",
            },
        ):
            placeholder_before = tree_snapshot(self.root)
            rejected_placeholder = self.update_task(
                receipt,
                "TASK-001",
                placeholder_patch,
                confirmed=True,
                expected=2,
            )
            self.assertEqual(
                rejected_placeholder["errors"][0]["category"], "invalid_input"
            )
            self.assertEqual(tree_snapshot(self.root), placeholder_before)

        receipt = self.update_task(
            receipt,
            "TASK-001",
            self.task_patch("skipped"),
        )["plan"]
        before_rewrite = tree_snapshot(self.root)
        rejected_rewrite = self.update_task(
            receipt,
            "TASK-001",
            {"skip_authority": "Unconfirmed replacement skip authority."},
            confirmed=False,
            expected=9,
        )
        self.assertEqual(
            rejected_rewrite["errors"][0]["category"], "unmet_gate"
        )
        self.assertEqual(tree_snapshot(self.root), before_rewrite)
        placeholder_rewrite_before = tree_snapshot(self.root)
        placeholder_rewrite = self.update_task(
            receipt,
            "TASK-001",
            {"skip_authority": "TBD"},
            confirmed=True,
            expected=2,
        )
        self.assertEqual(
            placeholder_rewrite["errors"][0]["category"], "invalid_input"
        )
        self.assertEqual(tree_snapshot(self.root), placeholder_rewrite_before)
        confirmed_rewrite = self.update_task(
            receipt,
            "TASK-001",
            {"skip_authority": "Current confirmed replacement skip authority."},
            confirmed=True,
        )["plan"]
        canonical = self.show(confirmed_rewrite)["data"]["canonical"]
        task = next(
            item for item in canonical["tasks"] if item["task_id"] == "TASK-001"
        )
        self.assertEqual(
            task["skip_authority"],
            "Current confirmed replacement skip authority.",
        )

    def test_tst_032_material_scope_revision_returns_ready_or_active_plan_to_draft(self):
        """TST-032: material scope change revokes readiness and execution state."""
        for start in ("ready", "in_progress"):
            with self.subTest(start=start):
                case_root = self.root / start
                case_root.mkdir()
                receipt = self.create(root=case_root)
                receipt = self.set_status(receipt, "ready", root=case_root)["plan"]
                if start == "in_progress":
                    receipt = self.set_status(receipt, "in_progress", root=case_root)["plan"]
                result = self.update_baseline(
                    receipt,
                    {
                        "objective": {
                            "summary": "Materially revised isolated objective.",
                            "user_value": "The revised outcome changes approved scope.",
                            "success_outcomes": ["The revised outcome is re-approved."],
                        }
                    },
                    material_change=True,
                    root=case_root,
                )
                self.assertEqual(result["plan"]["plan_status"], "draft")
                canonical = self.show(result["plan"], root=case_root)["data"]["canonical"]
                self.assertIn("Material baseline changed", canonical["status_reason"])

        placeholder_root = self.root / "placeholder-ready-gate"
        placeholder_root.mkdir()
        placeholder_payload = copy.deepcopy(self.example)
        placeholder_payload["objective"]["summary"] = "TBD"
        placeholder_receipt = self.create(
            root=placeholder_root, payload=placeholder_payload
        )
        placeholder_plan = self.show(
            placeholder_receipt, root=placeholder_root
        )["data"]["canonical"]
        self.assertEqual(placeholder_plan["status"], "draft")
        self.assertEqual(placeholder_plan["validation"]["status"], "fail")
        placeholder_before = tree_snapshot(placeholder_root)
        placeholder_ready = self.set_status(
            placeholder_receipt,
            "ready",
            root=placeholder_root,
            expected=9,
        )
        self.assertIn(
            "placeholder_semantic_text",
            finding_codes(placeholder_ready["data"]["details"]["findings"]),
        )
        self.assertEqual(tree_snapshot(placeholder_root), placeholder_before)

        placeholder_reason_root = self.root / "placeholder-status-reason"
        placeholder_reason_root.mkdir()
        placeholder_reason_receipt = self.create(root=placeholder_reason_root)
        for placeholder_reason_text in ("TBD", "N/A"):
            with self.subTest(placeholder_reason=placeholder_reason_text):
                placeholder_reason_before = tree_snapshot(placeholder_reason_root)
                placeholder_reason = self.set_status(
                    placeholder_reason_receipt,
                    "ready",
                    reason=placeholder_reason_text,
                    root=placeholder_reason_root,
                    expected=2,
                )
                self.assertEqual(
                    placeholder_reason["errors"][0]["category"], "invalid_input"
                )
                self.assertEqual(
                    tree_snapshot(placeholder_reason_root),
                    placeholder_reason_before,
                )

        active_root = self.root / "active-task-material-change"
        active_root.mkdir()
        receipt = self.make_in_progress(root=active_root)
        receipt = self.update_task(
            receipt, "TASK-001", {"status": "in_progress"}, root=active_root
        )["plan"]
        before = tree_snapshot(active_root)
        direct_draft = self.set_status(
            receipt, "draft", root=active_root, expected=9
        )
        self.assertEqual(direct_draft["errors"][0]["category"], "unmet_gate")
        self.assertEqual(tree_snapshot(active_root), before)
        rejected = self.update_baseline(
            receipt,
            {"title": "Material change while a task is active"},
            material_change=True,
            root=active_root,
            expected=9,
        )
        self.assertEqual(rejected["errors"][0]["category"], "unmet_gate")
        self.assertIn("TASK-001", rejected["errors"][0]["targets"])
        self.assertEqual(tree_snapshot(active_root), before)
        receipt = self.update_task(
            receipt,
            "TASK-001",
            {"status": "paused", "pause_reason": "Pause before baseline review."},
            root=active_root,
        )["plan"]
        revised = self.update_baseline(
            receipt,
            {"title": "Material change after pausing active work"},
            material_change=True,
            root=active_root,
        )
        revised_plan = self.show(revised["plan"], root=active_root)["data"]["canonical"]
        self.assertEqual(revised_plan["status"], "draft")
        self.assertEqual(revised_plan["tasks"][0]["status"], "paused")
        self.assertEqual(revised_plan["phases"][0]["status"], "paused")

        extension_root = self.root / "unrelated-extension"
        extension_root.mkdir()
        receipt = self.make_in_progress(root=extension_root)
        receipt = self.complete_task(
            receipt, "TASK-001", 2, root=extension_root
        )
        canonical = self.show(receipt, root=extension_root)["data"]["canonical"]
        original_evidence = copy.deepcopy(canonical["tasks"][0]["evidence"])
        phases = copy.deepcopy(canonical["phases"])
        tasks = copy.deepcopy(canonical["tasks"])
        phases.append(
            {
                "phase_id": "PHASE-002",
                "title": "Independent follow-up",
                "objective": "Perform a separately based follow-up check.",
                "scope": ["Add one independent quality task."],
                "depends_on_phase_ids": ["PHASE-001"],
                "entry_conditions": ["PHASE-001 is complete."],
                "exit_criteria": ["The independent task is complete."],
                "task_ids": ["TASK-003"],
                "risks": [],
                "status": "planned",
            }
        )
        tasks.append(
            {
                "task_id": "TASK-003",
                "phase_id": "PHASE-002",
                "title": "Run independent follow-up",
                "action": "Perform an independently justified quality check.",
                "requirement_ids": [],
                "design_basis": ["Quality: independent follow-up requested."],
                "target_artifacts": ["follow-up-report.txt"],
                "dependencies": ["TASK-002"],
                "parallel_group": None,
                "risks": [],
                "acceptance_criteria": ["The follow-up result is reviewable."],
                "verification_steps": ["Inspect follow-up-report.txt."],
                "status": "planned",
                "blocker_reason": None,
                "pause_reason": None,
                "skip_reason": None,
                "skip_authority": None,
                "evidence": [],
                "completed_at": None,
            }
        )
        extended = self.update_baseline(
            receipt,
            {"phases": phases, "tasks": tasks},
            material_change=True,
            root=extension_root,
        )["plan"]
        extended_plan = self.show(extended, root=extension_root)["data"]["canonical"]
        self.assertEqual(extended_plan["tasks"][0]["status"], "completed")
        self.assertEqual(extended_plan["tasks"][0]["evidence"], original_evidence)

        append_root = self.root / "append-only-observations"
        append_root.mkdir()
        append_receipt = self.create(root=append_root)
        append_plan = self.show(append_receipt, root=append_root)["data"]["canonical"]
        base_project = copy.deepcopy(append_plan["project"])
        inserted = copy.deepcopy(base_project)
        inserted["baseline_facts"] = [
            {
                "fact": "Inserted before the immutable observation prefix.",
                "evidence_locator": "synthetic",
                "observed_at": inserted["inspected_at"],
            },
            *inserted["baseline_facts"],
        ]
        duplicate = copy.deepcopy(base_project)
        duplicate["baseline_facts"].append(
            copy.deepcopy(duplicate["baseline_facts"][0])
        )
        duplicate_guidance = copy.deepcopy(base_project)
        duplicate_guidance["guidance"].append(
            copy.deepcopy(duplicate_guidance["guidance"][0])
        )
        phase_status = copy.deepcopy(append_plan["phases"])
        phase_status[0]["status"] = "blocked"
        for label, patch_value in (
            ("inserted fact", {"project": inserted}),
            ("duplicate fact", {"project": duplicate}),
            ("duplicate guidance", {"project": duplicate_guidance}),
            ("derived phase status", {"phases": phase_status}),
        ):
            with self.subTest(append_only=label):
                before_rejection = tree_snapshot(append_root)
                rejected_update = self.update_baseline(
                    append_receipt,
                    patch_value,
                    root=append_root,
                    expected=2,
                )
                self.assertEqual(
                    rejected_update["errors"][0]["category"], "invalid_input"
                )
                self.assertEqual(tree_snapshot(append_root), before_rejection)

    def test_tst_033_list_show_validate_are_byte_identical_read_only(self):
        """TST-033: useful read-only output does not modify any file."""
        receipt = self.create()
        before = tree_snapshot(self.root)
        listed = self.cli("list")
        shown = self.cli("show", receipt["plan_id"])
        validated = self.cli("validate", receipt["plan_id"])
        self.assertEqual(listed["data"]["count"], 1)
        self.assertEqual(shown["data"]["canonical"]["plan_id"], receipt["plan_id"])
        self.assertEqual(validated["data"]["status"], "pass")
        self.assertFalse(listed["mutation"] or shown["mutation"] or validated["mutation"])
        self.assertEqual(tree_snapshot(self.root), before)

    def test_tst_034_catalog_and_plan_locks_reject_second_writer(self):
        """TST-034: an existing lock returns busy and preserves state."""
        receipt = self.create()
        plans_root = self.root / "Implementation_Plans"
        cases = (
            (plans_root / ".to-implementation-plan.catalog.lock", "create"),
            (Path(receipt["canonical_path"]).parent / ".to-implementation-plan.plan.lock", "update"),
        )
        for index, (lock_path, route) in enumerate(cases, 1):
            with self.subTest(route=route):
                lock_path.mkdir()
                (lock_path / "owner.json").write_text(
                    json.dumps(
                        {
                            "schema_version": 1,
                            "token": f"{index:032X}",
                            "pid": os.getpid(),
                            "host": "synthetic-host",
                            "started_at": "2026-08-28T12:00:00Z",
                            "command": route,
                        }
                    )
                    + "\n",
                    encoding="utf-8",
                )
                before = tree_snapshot(self.root)
                if route == "create":
                    result = self.cli(
                        "create", "--input", "-", payload=self.example, expected=7
                    )
                else:
                    result = self.update_baseline(
                        receipt, {"title": "Must not write"}, expected=7
                    )
                self.assertEqual(result["errors"][0]["category"], "active_lock")
                self.assertEqual(tree_snapshot(self.root), before)
                (lock_path / "owner.json").unlink()
                lock_path.rmdir()

        secret = "sk-" + "A" * 24
        catalog_lock = plans_root / ".to-implementation-plan.catalog.lock"
        catalog_lock.mkdir()
        (catalog_lock / "owner.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "token": secret,
                    "pid": os.getpid(),
                    "host": secret,
                    "started_at": secret,
                    "command": secret,
                    secret: secret,
                }
            ),
            encoding="utf-8",
        )
        process = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--project-root",
                str(self.root),
                "create",
                "--input",
                "-",
            ],
            input=json.dumps(self.example),
            text=True,
            capture_output=True,
            check=False,
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
        )
        self.assertEqual(process.returncode, 7)
        self.assertNotIn(secret, process.stdout)
        (catalog_lock / "owner.json").unlink()
        catalog_lock.rmdir()

    def test_tst_035_stale_revision_hash_and_no_op_are_safe(self):
        """TST-035: stale clients cannot overwrite; exact no-op does not revise."""
        original = self.create()
        first = self.update_baseline(original, {"title": "Updated display title"})["plan"]
        before = tree_snapshot(self.root)
        stale = self.update_baseline(original, {"title": "Stale overwrite"}, expected=6)
        self.assertEqual(stale["errors"][0]["category"], "stale_state")
        self.assertEqual(tree_snapshot(self.root), before)
        wrong_hash = copy.deepcopy(first)
        wrong_hash["sha256"] = "0" * 64
        hash_result = self.update_baseline(
            wrong_hash, {"title": "Wrong-hash overwrite"}, expected=6
        )
        self.assertEqual(hash_result["errors"][0]["category"], "stale_state")
        self.assertEqual(tree_snapshot(self.root), before)
        no_op = self.update_baseline(first, {"title": "Updated display title"})
        self.assertEqual(no_op["status"], "no_op")
        self.assertFalse(no_op["mutation"])
        self.assertEqual(no_op["plan"]["revision"], first["revision"])
        self.assertEqual(tree_snapshot(self.root), before)

        timestamp_root = self.root / "evidence-timestamp-order"
        timestamp_root.mkdir()
        receipt = self.make_in_progress(root=timestamp_root)
        for evidence_time in ("2000-01-01T00:00:00Z", "2999-01-01T00:00:00Z"):
            with self.subTest(evidence_time=evidence_time):
                state_before = tree_snapshot(timestamp_root)
                result = self.cli(
                    "record-evidence",
                    receipt["plan_id"],
                    "TASK-001",
                    "--expect-revision",
                    str(receipt["revision"]),
                    "--expect-sha256",
                    receipt["sha256"],
                    "--input",
                    "-",
                    payload={
                        "timestamp": evidence_time,
                        "evidence_type": "test",
                        "result_status": "passed",
                        "description": "Timestamp-bound synthetic observation.",
                        "locator_or_command": "python -m unittest timestamp_fixture",
                        "observed_result": "The timestamp fixture reported a pass.",
                        "verification_level": "targeted_tests_passed",
                        "observation_source": "tool",
                    },
                    expected=2,
                    root=timestamp_root,
                )
                self.assertEqual(result["errors"][0]["category"], "invalid_input")
                self.assertEqual(tree_snapshot(timestamp_root), state_before)

    def test_tst_036_interruption_before_canonical_replace_preserves_canonical(self):
        """TST-036: pre-replace failure leaves canonical unchanged and named residue."""
        receipt = self.create()
        canonical_path = Path(receipt["canonical_path"])
        canonical_before = canonical_path.read_bytes()
        payload_path = self.root / "update-input.json"
        payload_path.write_text(
            json.dumps(
                {
                    "patch": {"title": "Interrupted update"},
                    "summary": "Inject replacement failure.",
                    "authority_basis": "Explicit isolated fault injection.",
                }
            ),
            encoding="utf-8",
        )
        context = self.plan_state.resolve_context(str(self.root), "Implementation_Plans")
        args = SimpleNamespace(
            selector=receipt["plan_id"],
            expect_revision=receipt["revision"],
            expect_sha256=receipt["sha256"],
            input=str(payload_path),
        )
        with patch.object(
            self.plan_state.os,
            "replace",
            side_effect=OSError("Injected canonical replacement failure"),
        ):
            with self.assertRaises(self.plan_state.AppError) as caught:
                self.plan_state.handle_update(context, args)
        self.assertEqual(caught.exception.category, "io_error")
        self.assertEqual(canonical_path.read_bytes(), canonical_before)
        residue = list(canonical_path.parent.glob(".plan.json.tmp-*"))
        self.assertEqual(len(residue), 1)
        self.assertRegex(residue[0].name, r"^\.plan\.json\.tmp-[A-F0-9]{32}$")
        self.assertFalse((canonical_path.parent / ".to-implementation-plan.plan.lock").exists())
        self.assertFalse((self.root / "Implementation_Plans" / ".to-implementation-plan.catalog.lock").exists())

        create_root = self.root / "partial-create-recovery"
        create_root.mkdir()
        create_payload = create_root / "create.json"
        create_payload.write_text(json.dumps(self.example), encoding="utf-8")
        captured = io.StringIO()
        with patch.object(
            self.plan_state.os,
            "replace",
            side_effect=OSError("Injected initial canonical replacement failure"),
        ), patch("sys.stdout", captured):
            create_exit = self.plan_state.main(
                [
                    "--project-root",
                    str(create_root),
                    "create",
                    "--input",
                    str(create_payload),
                ]
            )
        create_failure = json.loads(captured.getvalue())
        self.assertEqual(create_exit, 10)
        self.assertEqual(create_failure["status"], "error")
        self.assertFalse(create_failure["mutation"])
        recovery = create_failure["recovery_required"]
        self.assertEqual(recovery["command"], "reconcile")
        self.assertEqual(recovery["selector"], "catalog")
        self.assertEqual(recovery["input"]["action"], "remove_partial_create")
        residue_dir = create_root / "Implementation_Plans" / recovery["input"]["directory"]
        self.assertTrue(residue_dir.is_dir())
        recovered = self.cli(
            "reconcile",
            "catalog",
            "--input",
            "-",
            "--confirmed",
            payload=recovery["input"],
            root=create_root,
        )
        self.assertEqual(recovered["status"], "ok")
        self.assertFalse(residue_dir.exists())
        repeated = self.cli(
            "reconcile",
            "catalog",
            "--input",
            "-",
            "--confirmed",
            payload=recovery["input"],
            root=create_root,
        )
        self.assertEqual(repeated["status"], "no_op")

        swap_root = self.root / "parent-swap"
        swap_root.mkdir()
        swap_receipt = self.create(root=swap_root)
        swap_context = self.plan_state.resolve_context(
            str(swap_root), "Implementation_Plans"
        )
        plan_dir = Path(swap_receipt["canonical_path"]).parent
        record = self.plan_state.load_plan_record(swap_context, plan_dir)
        original_bytes = record.raw
        backup_dir = plan_dir.with_name(plan_dir.name + "-original")
        outside_dir = swap_root / "outside"
        outside_dir.mkdir()
        outside_canonical = outside_dir / "plan.json"
        outside_canonical.write_bytes(b"outside sentinel\n")
        plan_dir.rename(backup_dir)
        plan_dir.symlink_to(outside_dir, target_is_directory=True)
        with self.assertRaises(self.plan_state.AppError) as caught:
            self.plan_state.atomic_write_bytes(
                plan_dir / "plan.json",
                original_bytes.replace(
                    b"Add a project health-check command",
                    b"Escaped write must not occur",
                ),
                expected_parent_identity=record.directory_identity,
            )
        self.assertEqual(caught.exception.category, "unsafe_or_corrupt")
        self.assertEqual(outside_canonical.read_bytes(), b"outside sentinel\n")
        self.assertEqual((backup_dir / "plan.json").read_bytes(), original_bytes)
        with self.assertRaises(self.plan_state.AppError) as lock_redirect:
            self.plan_state.acquire_lock(
                self.plan_state.plan_lock_path(plan_dir), "update"
            )
        self.assertEqual(lock_redirect.exception.category, "unsafe_or_corrupt")
        self.assertFalse(
            (outside_dir / ".to-implementation-plan.plan.lock").exists()
        )

        catalog_swap_root = self.root / "catalog-lock-parent-swap"
        catalog_plans = catalog_swap_root / "Implementation_Plans"
        catalog_outside = catalog_swap_root / "outside"
        catalog_plans.mkdir(parents=True)
        catalog_outside.mkdir()
        catalog_bound = catalog_swap_root / "Implementation_Plans-bound"
        catalog_plans.rename(catalog_bound)
        catalog_plans.symlink_to(catalog_outside, target_is_directory=True)
        with self.assertRaises(self.plan_state.AppError) as catalog_redirect:
            self.plan_state.acquire_lock(
                catalog_plans / ".to-implementation-plan.catalog.lock",
                "create",
            )
        self.assertEqual(catalog_redirect.exception.category, "unsafe_or_corrupt")
        self.assertFalse(
            (catalog_outside / ".to-implementation-plan.catalog.lock").exists()
        )

        noop_root = self.root / "noop-parent-swap"
        noop_parent = noop_root / "ancestor" / "bound-parent"
        noop_parent.mkdir(parents=True)
        noop_file = noop_parent / "managed.txt"
        noop_data = b"exact no-op bytes\n"
        noop_file.write_bytes(noop_data)
        ancestor = noop_root / "ancestor"
        moved_ancestor = noop_root / "ancestor-moved"
        real_sha256_bytes = self.plan_state.sha256_bytes
        swapped = False

        def swap_ancestor_during_hash(data):
            nonlocal swapped
            if not swapped:
                ancestor.rename(moved_ancestor)
                ancestor.symlink_to(moved_ancestor, target_is_directory=True)
                swapped = True
            return real_sha256_bytes(data)

        with patch.object(
            self.plan_state,
            "sha256_bytes",
            side_effect=swap_ancestor_during_hash,
        ):
            with self.assertRaises(self.plan_state.AppError) as noop_swap:
                self.plan_state.atomic_write_bytes(noop_file, noop_data)
        self.assertEqual(noop_swap.exception.category, "unsafe_or_corrupt")
        self.assertEqual(
            (moved_ancestor / "bound-parent" / "managed.txt").read_bytes(),
            noop_data,
        )

        release_root = self.root / "release-parent-swap"
        release_plan_dir = release_root / "Plan_release_2026-08-29_AAAAAAAA"
        release_plan_dir.mkdir(parents=True)
        release_lock_path = self.plan_state.plan_lock_path(release_plan_dir)
        release_handle = self.plan_state.acquire_lock(release_lock_path, "update")
        release_backup = release_plan_dir.with_name(release_plan_dir.name + "-bound")
        release_outside = release_root / "outside"
        release_outside.mkdir()
        release_plan_dir.rename(release_backup)
        release_plan_dir.symlink_to(release_outside, target_is_directory=True)
        with self.assertRaises(self.plan_state.AppError) as release_swap:
            self.plan_state.release_lock(release_handle)
        self.assertEqual(release_swap.exception.category, "unsafe_or_corrupt")
        self.assertFalse(
            (release_outside / ".to-implementation-plan.plan.lock").exists()
        )
        self.assertTrue(
            (release_backup / ".to-implementation-plan.plan.lock").is_dir()
        )

        init_root = self.root / "lock-init-failure"
        init_root.mkdir()
        init_lock = init_root / ".to-implementation-plan.plan.lock"
        real_open = self.plan_state.os.open

        def interrupt_owner_open(path_value, *open_args, **open_kwargs):
            if path_value == "owner.json":
                raise KeyboardInterrupt()
            return real_open(path_value, *open_args, **open_kwargs)

        with patch.object(
            self.plan_state.os, "open", side_effect=interrupt_owner_open
        ):
            with self.assertRaises(self.plan_state.AppError) as init_failure:
                self.plan_state.acquire_lock(init_lock, "update")
        self.assertEqual(init_failure.exception.category, "io_error")
        self.assertFalse(init_lock.exists())
        self.assertFalse(list(init_root.glob("*.released-*")))

        mkdir_root = self.root / "mkdir-fsync-failure"
        mkdir_root.mkdir()
        mkdir_context = self.plan_state.resolve_context(
            str(mkdir_root), "Implementation_Plans"
        )
        self.plan_state.ensure_catalog_for_write(mkdir_context)
        mkdir_payload = mkdir_root / "create.json"
        mkdir_payload.write_text(json.dumps(self.example), encoding="utf-8")
        real_fsync = self.plan_state.os.fsync
        catalog_info = mkdir_context.plans_root.stat()
        catalog_identity = (catalog_info.st_dev, catalog_info.st_ino)
        failed_once = False

        def fail_plan_directory_fsync(descriptor_value):
            nonlocal failed_once
            descriptor_info = self.plan_state.os.fstat(descriptor_value)
            plan_directory_exists = any(
                item.is_dir() and item.name.startswith("Plan_")
                for item in mkdir_context.plans_root.iterdir()
            )
            if (
                (descriptor_info.st_dev, descriptor_info.st_ino)
                == catalog_identity
                and plan_directory_exists
                and not failed_once
            ):
                failed_once = True
                raise OSError("Injected plan-directory fsync failure")
            return real_fsync(descriptor_value)

        with patch.object(
            self.plan_state.os,
            "fsync",
            side_effect=fail_plan_directory_fsync,
        ):
            with self.assertRaises(self.plan_state.AppError) as mkdir_failure:
                self.plan_state.handle_create(
                    mkdir_context, SimpleNamespace(input=str(mkdir_payload))
                )
        self.assertEqual(mkdir_failure.exception.category, "io_error")
        self.assertFalse(
            any(
                item.is_dir() and item.name.startswith("Plan_")
                for item in mkdir_context.plans_root.iterdir()
            )
        )

        catalog_race_root = self.root / "create-catalog-swap"
        catalog_race_root.mkdir()
        catalog_race_context = self.plan_state.resolve_context(
            str(catalog_race_root), "Implementation_Plans"
        )
        self.plan_state.ensure_catalog_for_write(catalog_race_context)
        catalog_race_input = catalog_race_root / "create.json"
        catalog_race_input.write_text(json.dumps(self.example), encoding="utf-8")
        catalog_backup = catalog_race_root / "Implementation_Plans-bound"
        catalog_outside = catalog_race_root / "outside"
        catalog_outside.mkdir()
        real_discover = self.plan_state.discover_managed_plans
        swapped_catalog = False

        def swap_catalog_after_discovery(context_value):
            nonlocal swapped_catalog
            result = real_discover(context_value)
            if not swapped_catalog:
                catalog_race_context.plans_root.rename(catalog_backup)
                catalog_race_context.plans_root.symlink_to(
                    catalog_outside, target_is_directory=True
                )
                swapped_catalog = True
            return result

        with patch.object(
            self.plan_state,
            "discover_managed_plans",
            side_effect=swap_catalog_after_discovery,
        ):
            with self.assertRaises(self.plan_state.AppError) as catalog_race:
                self.plan_state.handle_create(
                    catalog_race_context,
                    SimpleNamespace(input=str(catalog_race_input)),
                )
        self.assertEqual(catalog_race.exception.category, "unsafe_or_corrupt")
        self.assertFalse(
            any(item.name.startswith("Plan_") for item in catalog_outside.iterdir())
        )
        self.assertFalse(
            any(item.name.startswith("Plan_") for item in catalog_backup.iterdir())
        )

    def test_tst_037_partial_projection_receipt_repairs_without_repeating_mutation(self):
        """TST-037: post-commit projection failure reports partial and rebuilds."""
        receipt = self.create()
        payload_path = self.root / "partial-update.json"
        payload_path.write_text(
            json.dumps(
                {
                    "patch": {"title": "Canonically committed title"},
                    "summary": "Inject projection publication failure.",
                    "authority_basis": "Explicit isolated fault injection.",
                }
            ),
            encoding="utf-8",
        )
        context = self.plan_state.resolve_context(str(self.root), "Implementation_Plans")
        args = SimpleNamespace(
            selector=receipt["plan_id"],
            expect_revision=receipt["revision"],
            expect_sha256=receipt["sha256"],
            input=str(payload_path),
        )
        with patch.object(
            self.plan_state,
            "write_plan_projections",
            side_effect=self.plan_state.AppError("io_error", "Injected projection failure."),
        ):
            envelope, exit_code = self.plan_state.handle_update(context, args)
        self.assertEqual(exit_code, 11)
        self.assertEqual(envelope["status"], "partial")
        self.assertTrue(envelope["plan"]["canonical_committed"])
        self.assertEqual(envelope["plan"]["revision"], receipt["revision"] + 1)
        self.assertEqual(envelope["recovery_required"]["command"], "rebuild-projections")
        partial_receipt = envelope["plan"]
        rebuilt = self.cli("rebuild-projections", partial_receipt["plan_id"])
        self.assertIn(rebuilt["status"], {"ok", "no_op"})
        self.cli("reindex")
        shown = self.show(partial_receipt)
        self.assertEqual(shown["plan"]["revision"], partial_receipt["revision"])
        self.assertEqual(shown["data"]["canonical"]["title"], "Canonically committed title")

        cleanup_root = self.root / "post-commit-lock-cleanup"
        cleanup_root.mkdir()
        cleanup_receipt = self.create(root=cleanup_root)
        cleanup_payload = cleanup_root / "cleanup-update.json"
        cleanup_payload.write_text(
            json.dumps(
                {
                    "patch": {"title": "Committed before cleanup failure"},
                    "summary": "Inject post-commit lock cleanup failure.",
                    "authority_basis": "Explicit isolated fault injection.",
                }
            ),
            encoding="utf-8",
        )
        real_release = self.plan_state.release_lock

        def release_then_fail(handle):
            real_release(handle)
            raise self.plan_state.AppError(
                "io_error",
                "Injected durability failure after owned lock removal.",
                details={
                    "lock_cleanup_failed": True,
                    "lock_path": str(handle.path),
                    "token": handle.token,
                },
            )

        captured = io.StringIO()
        with patch.object(
            self.plan_state, "release_lock", side_effect=release_then_fail
        ), patch("sys.stdout", captured):
            exit_code = self.plan_state.main(
                [
                    "--project-root",
                    str(cleanup_root),
                    "update",
                    cleanup_receipt["plan_id"],
                    "--expect-revision",
                    str(cleanup_receipt["revision"]),
                    "--expect-sha256",
                    cleanup_receipt["sha256"],
                    "--input",
                    str(cleanup_payload),
                ]
            )
        cleanup_result = json.loads(captured.getvalue())
        self.assertEqual(exit_code, 10)
        self.assertEqual(cleanup_result["status"], "partial")
        self.assertTrue(cleanup_result["mutation"])
        self.assertEqual(
            cleanup_result["plan"]["revision"], cleanup_receipt["revision"] + 1
        )
        self.assertEqual(
            cleanup_result["recovery_required"]["command"], "reconcile"
        )
        shown = self.show(cleanup_result["plan"], root=cleanup_root)
        self.assertEqual(
            shown["data"]["canonical"]["title"],
            "Committed before cleanup failure",
        )

        compound_root = self.root / "projection-and-lock-cleanup"
        compound_root.mkdir()
        compound_receipt = self.create(root=compound_root)
        compound_payload = compound_root / "compound-update.json"
        compound_payload.write_text(
            json.dumps(
                {
                    "patch": {"title": "Committed before compound failures"},
                    "summary": "Inject projection and lock cleanup failures.",
                    "authority_basis": "Explicit isolated compound fault injection.",
                }
            ),
            encoding="utf-8",
        )
        captured = io.StringIO()
        with patch.object(
            self.plan_state,
            "write_plan_projections",
            side_effect=self.plan_state.AppError(
                "io_error", "Injected projection failure before lock cleanup."
            ),
        ), patch.object(
            self.plan_state, "release_lock", side_effect=release_then_fail
        ), patch("sys.stdout", captured):
            compound_exit = self.plan_state.main(
                [
                    "--project-root",
                    str(compound_root),
                    "update",
                    compound_receipt["plan_id"],
                    "--expect-revision",
                    str(compound_receipt["revision"]),
                    "--expect-sha256",
                    compound_receipt["sha256"],
                    "--input",
                    str(compound_payload),
                ]
            )
        compound_result = json.loads(captured.getvalue())
        self.assertEqual(compound_exit, self.plan_state.EXIT_CODES["io_error"])
        self.assertEqual(compound_result["status"], "partial")
        self.assertTrue(compound_result["mutation"])
        self.assertEqual(
            compound_result["plan"]["projection_status"], "failed"
        )
        self.assertEqual(compound_result["plan"]["index_status"], "failed")
        compound_recovery = compound_result["recovery_required"]
        self.assertEqual(compound_recovery["command"], "reconcile")
        projection_recovery = compound_recovery["then"]
        self.assertEqual(projection_recovery["command"], "rebuild-projections")
        reindex_recovery = projection_recovery["then"]
        self.assertEqual(reindex_recovery["command"], "reindex")
        validate_recovery = reindex_recovery["then"]
        self.assertEqual(validate_recovery["command"], "validate")

        no_op_payload = cleanup_root / "cleanup-no-op.json"
        no_op_payload.write_text(
            json.dumps(
                {
                    "patch": {"title": "Committed before cleanup failure"},
                    "summary": "Exercise no-op cleanup reporting.",
                    "authority_basis": "Explicit isolated fault injection.",
                }
            ),
            encoding="utf-8",
        )
        captured = io.StringIO()
        with patch.object(
            self.plan_state, "release_lock", side_effect=release_then_fail
        ), patch("sys.stdout", captured):
            no_op_exit = self.plan_state.main(
                [
                    "--project-root",
                    str(cleanup_root),
                    "update",
                    cleanup_result["plan"]["plan_id"],
                    "--expect-revision",
                    str(cleanup_result["plan"]["revision"]),
                    "--expect-sha256",
                    cleanup_result["plan"]["sha256"],
                    "--input",
                    str(no_op_payload),
                ]
            )
        no_op_cleanup = json.loads(captured.getvalue())
        self.assertEqual(no_op_exit, 10)
        self.assertEqual(no_op_cleanup["status"], "error")
        self.assertFalse(no_op_cleanup["mutation"])
        self.assertEqual(
            no_op_cleanup["recovery_required"]["command"], "reconcile"
        )

        interrupt_root = self.root / "post-replace-interrupt"
        interrupt_root.mkdir()
        interrupt_receipt = self.create(root=interrupt_root)
        interrupt_payload = interrupt_root / "interrupt-update.json"
        interrupt_payload.write_text(
            json.dumps(
                {
                    "patch": {"title": "Committed before interruption"},
                    "summary": "Inject an interrupt after canonical replacement.",
                    "authority_basis": "Explicit isolated fault injection.",
                }
            ),
            encoding="utf-8",
        )
        interrupt_context = self.plan_state.resolve_context(
            str(interrupt_root), "Implementation_Plans"
        )
        interrupt_args = SimpleNamespace(
            selector=interrupt_receipt["plan_id"],
            expect_revision=interrupt_receipt["revision"],
            expect_sha256=interrupt_receipt["sha256"],
            input=str(interrupt_payload),
        )
        real_replace = self.plan_state.os.replace

        def observed_replace(source, destination, *args, **kwargs):
            real_replace(source, destination, *args, **kwargs)
            raise KeyboardInterrupt()

        with patch.object(
            self.plan_state.os, "replace", side_effect=observed_replace
        ):
            interrupted, interrupt_exit = self.plan_state.handle_update(
                interrupt_context, interrupt_args
            )
        self.assertEqual(interrupt_exit, 11)
        self.assertEqual(interrupted["status"], "partial")
        self.assertTrue(interrupted["mutation"])
        self.assertEqual(
            interrupted["plan"]["revision"], interrupt_receipt["revision"] + 1
        )

        boundary_root = self.root / "post-atomic-return-interrupt"
        boundary_root.mkdir()
        boundary_receipt = self.create(root=boundary_root)
        boundary_payload = boundary_root / "boundary-update.json"
        boundary_payload.write_text(
            json.dumps(
                {
                    "patch": {"title": "Committed before wrapper interruption"},
                    "summary": "Interrupt immediately after atomic_write_bytes returns.",
                    "authority_basis": "Explicit isolated fault injection.",
                }
            ),
            encoding="utf-8",
        )
        boundary_context = self.plan_state.resolve_context(
            str(boundary_root), "Implementation_Plans"
        )
        boundary_args = SimpleNamespace(
            selector=boundary_receipt["plan_id"],
            expect_revision=boundary_receipt["revision"],
            expect_sha256=boundary_receipt["sha256"],
            input=str(boundary_payload),
        )
        real_atomic_write = self.plan_state.atomic_write_bytes

        def atomic_then_interrupt(*atomic_args, **atomic_kwargs):
            real_atomic_write(*atomic_args, **atomic_kwargs)
            raise KeyboardInterrupt()

        with patch.object(
            self.plan_state,
            "atomic_write_bytes",
            side_effect=atomic_then_interrupt,
        ):
            boundary_result, boundary_exit = self.plan_state.handle_update(
                boundary_context, boundary_args
            )
        self.assertEqual(boundary_exit, 11)
        self.assertEqual(boundary_result["status"], "partial")
        self.assertTrue(boundary_result["mutation"])

        load_root = self.root / "persistent-post-commit-load-failure"
        load_root.mkdir()
        load_receipt = self.create(root=load_root)
        load_payload = load_root / "load-update.json"
        load_payload.write_text(
            json.dumps(
                {
                    "patch": {"title": "Committed before persistent load failure"},
                    "summary": "Make every post-commit canonical reload fail.",
                    "authority_basis": "Explicit isolated fault injection.",
                }
            ),
            encoding="utf-8",
        )
        load_context = self.plan_state.resolve_context(
            str(load_root), "Implementation_Plans"
        )
        load_args = SimpleNamespace(
            selector=load_receipt["plan_id"],
            expect_revision=load_receipt["revision"],
            expect_sha256=load_receipt["sha256"],
            input=str(load_payload),
        )
        real_load_record = self.plan_state.load_plan_record

        def reject_new_revision(context_value, plan_directory):
            raw_value = json.loads(
                (Path(plan_directory) / "plan.json").read_text(encoding="utf-8")
            )
            if raw_value["revision"] > load_receipt["revision"]:
                raise self.plan_state.AppError(
                    "io_error", "Injected persistent post-commit load failure."
                )
            return real_load_record(context_value, plan_directory)

        with patch.object(
            self.plan_state,
            "load_plan_record",
            side_effect=reject_new_revision,
        ):
            load_result, load_exit = self.plan_state.handle_update(
                load_context, load_args
            )
        self.assertEqual(load_exit, 11)
        self.assertEqual(load_result["status"], "partial")
        self.assertTrue(load_result["mutation"])
        self.assertEqual(
            load_result["plan"]["revision"], load_receipt["revision"] + 1
        )

        lock_root = self.root / "released-lock-recovery"
        lock_root.mkdir()
        lock_receipt = self.create(root=lock_root)
        lock_context = self.plan_state.resolve_context(
            str(lock_root), "Implementation_Plans"
        )
        lock_path = self.plan_state.plan_lock_path(
            Path(lock_receipt["canonical_path"]).parent
        )
        handle = self.plan_state.acquire_lock(lock_path, "update")
        with patch.object(
            self.plan_state.os,
            "fsync",
            side_effect=OSError("Injected release durability failure"),
        ):
            with self.assertRaises(self.plan_state.AppError) as release_error:
                self.plan_state.release_lock(handle)
        self.assertTrue(release_error.exception.details["release_renamed"])
        recovery_spec = self.plan_state.lock_cleanup_recovery(
            lock_path, handle.token, release_error.exception.details
        )
        self.assertEqual(
            recovery_spec["input"]["action"], "remove_released_lock"
        )
        recovery_path = lock_root / "released-recovery.json"
        recovery_path.write_text(
            json.dumps(recovery_spec["input"]), encoding="utf-8"
        )
        with patch.object(self.plan_state, "_pid_is_active", return_value=False):
            recovered_lock, recovered_exit = self.plan_state.handle_reconcile(
                lock_context,
                SimpleNamespace(
                    confirmed=True,
                    input=str(recovery_path),
                    selector=lock_receipt["plan_id"],
                ),
            )
        self.assertEqual(recovered_exit, 0)
        self.assertEqual(recovered_lock["status"], "ok")
        released_name = recovery_spec["input"]["relative_name"]
        self.assertFalse((lock_path.parent / released_name).exists())

    def test_tst_038_projection_drift_is_detected_and_explicitly_rebuilt(self):
        """TST-038: edited/deleted generated files never alter canonical meaning."""
        receipt = self.create()
        plan_dir = Path(receipt["canonical_path"]).parent
        canonical_before = Path(receipt["canonical_path"]).read_bytes()
        project_owned_phase = plan_dir / "phases" / "PHASE-999_project-owned.md"
        project_owned_phase.write_text(
            "# Project-owned phase notes\n\nDo not remove me.\n", encoding="utf-8"
        )
        (plan_dir / "PLAN.md").write_bytes(
            self.plan_state.GENERATED_PROJECTION_MARKER + b"drift\n"
        )
        (plan_dir / "TRACEABILITY.md").unlink()
        validation = self.cli("validate", receipt["plan_id"])
        self.assertEqual(validation["data"]["status"], "fail")
        codes = finding_codes(validation["data"]["plans"][0]["projection_findings"])
        self.assertIn("projection_drift", codes)
        self.assertIn("missing_projection", codes)
        rebuilt = self.cli("rebuild-projections", receipt["plan_id"])
        self.assertTrue(rebuilt["mutation"])
        self.assertEqual(self.cli("validate", receipt["plan_id"])["data"]["status"], "pass")
        self.assertEqual(Path(receipt["canonical_path"]).read_bytes(), canonical_before)
        self.assertEqual(
            project_owned_phase.read_text(encoding="utf-8"),
            "# Project-owned phase notes\n\nDo not remove me.\n",
        )
        self.assertEqual(self.cli("rebuild-projections", receipt["plan_id"])["status"], "no_op")

        for fixed_name in ("PLAN.md", "TRACEABILITY.md"):
            with self.subTest(unmanaged_destination=fixed_name):
                destination = plan_dir / fixed_name
                generated_before = destination.read_bytes()
                destination.write_text(
                    "# Project-owned collision\n\nDo not overwrite.\n",
                    encoding="utf-8",
                )
                canonical_before_collision = Path(receipt["canonical_path"]).read_bytes()
                blocked = self.update_baseline(
                    receipt,
                    {"title": f"Blocked by unmanaged {fixed_name}"},
                    material_change=True,
                    expected=5,
                )
                self.assertEqual(blocked["errors"][0]["category"], "unsafe_or_corrupt")
                self.assertEqual(
                    destination.read_text(encoding="utf-8"),
                    "# Project-owned collision\n\nDo not overwrite.\n",
                )
                self.assertEqual(
                    Path(receipt["canonical_path"]).read_bytes(),
                    canonical_before_collision,
                )
                destination.write_bytes(generated_before)

        colliding_phase = plan_dir / "phases" / "PHASE-001_colliding.md"
        colliding_phase.write_text(
            "# Project-owned colliding phase\n\nDo not overwrite.\n",
            encoding="utf-8",
        )
        canonical_before_collision = Path(receipt["canonical_path"]).read_bytes()
        blocked_phase = self.cli(
            "update-phase",
            receipt["plan_id"],
            "PHASE-001",
            "--expect-revision",
            str(receipt["revision"]),
            "--expect-sha256",
            receipt["sha256"],
            "--input",
            "-",
            payload={
                "patch": {"title": "Colliding"},
                "summary": "Exercise unmanaged phase destination protection.",
                "authority_basis": "Explicit isolated regression authority.",
            },
            expected=5,
        )
        self.assertEqual(blocked_phase["errors"][0]["category"], "unsafe_or_corrupt")
        self.assertEqual(
            colliding_phase.read_text(encoding="utf-8"),
            "# Project-owned colliding phase\n\nDo not overwrite.\n",
        )
        self.assertEqual(
            Path(receipt["canonical_path"]).read_bytes(),
            canonical_before_collision,
        )

        expanded_projection = plan_dir / "expanded-projection-fixture.md"
        expanded_bytes = self.plan_state.GENERATED_PROJECTION_MARKER + b"x" * (
            self.plan_state.MAX_JSON_BYTES + 1024
        )
        self.assertTrue(
            self.plan_state.atomic_write_bytes(expanded_projection, expanded_bytes)
        )
        self.assertFalse(
            self.plan_state.atomic_write_bytes(expanded_projection, expanded_bytes)
        )
        self.assertEqual(expanded_projection.stat().st_size, len(expanded_bytes))
        expanded_index = self.root / "Implementation_Plans" / "INDEX.md"
        expanded_index.write_bytes(
            self.plan_state.GENERATED_PROJECTION_MARKER
            + b"y" * (self.plan_state.MAX_JSON_BYTES + 1024)
        )
        context = self.plan_state.resolve_context(
            str(self.root), "Implementation_Plans"
        )
        self.plan_state.ensure_index_is_managed(context)
        self.assertEqual(self.cli("reindex")["status"], "ok")

        obsolete = plan_dir / "phases" / "PHASE-999_obsolete.md"
        obsolete.write_bytes(
            self.plan_state.GENERATED_PROJECTION_MARKER + b"obsolete\n"
        )
        record = self.plan_state.load_plan_record(context, plan_dir)
        real_unlink = self.plan_state.os.unlink
        real_fsync = self.plan_state.os.fsync
        obsolete_deleted = False

        def observe_obsolete_unlink(path_value, *unlink_args, **unlink_kwargs):
            nonlocal obsolete_deleted
            result = real_unlink(path_value, *unlink_args, **unlink_kwargs)
            if path_value == obsolete.name:
                obsolete_deleted = True
            return result

        def fail_fsync_after_obsolete(fd_value):
            if obsolete_deleted:
                raise OSError("Injected post-delete phases fsync failure")
            return real_fsync(fd_value)

        with patch.object(
            self.plan_state.os, "unlink", side_effect=observe_obsolete_unlink
        ), patch.object(
            self.plan_state.os, "fsync", side_effect=fail_fsync_after_obsolete
        ):
            with self.assertRaises(self.plan_state.AppError) as delete_failure:
                self.plan_state.write_plan_projections(record)
        self.assertEqual(delete_failure.exception.category, "io_error")
        self.assertIn(
            "phases/PHASE-999_obsolete.md",
            delete_failure.exception.details["generated_files_changed"],
        )
        self.assertFalse(obsolete.exists())

    def test_tst_039_corrupt_or_unknown_canonical_stops_catalog_mutation(self):
        """TST-039: malformed JSON and unknown schema both fail closed."""
        for case in (
            "malformed",
            "unknown_version",
            "duplicate_key",
            "bad_revision",
            "naive_timestamp",
            "unknown_action",
            "creation_action",
            "creation_affected",
            "future_observation",
            "future_validation",
            "past_validation",
            "future_updated_boundary",
            "huge_revision",
            "oversized",
        ):
            with self.subTest(case=case):
                case_root = self.root / case
                case_root.mkdir()
                receipt = self.create(root=case_root)
                canonical_path = Path(receipt["canonical_path"])
                if case == "malformed":
                    canonical_path.write_text('{"schema_version":', encoding="utf-8")
                elif case == "duplicate_key":
                    raw = canonical_path.read_bytes()
                    canonical_path.write_bytes(
                        raw.replace(b"{\n", b'{\n  "schema_version": 1,\n', 1)
                    )
                elif case == "oversized":
                    canonical_path.write_bytes(b" " * (self.plan_state.MAX_JSON_BYTES + 1))
                else:
                    value = json.loads(canonical_path.read_text(encoding="utf-8"))
                    if case == "unknown_version":
                        value["schema_version"] = 99
                    elif case == "bad_revision":
                        value["revision"] = True
                    elif case == "naive_timestamp":
                        value["created_at"] = value["created_at"].removesuffix("Z")
                    elif case == "unknown_action":
                        value["history"][0]["action_id"] = "TO-IP-999"
                    elif case == "creation_action":
                        value["history"][0]["action_id"] = "TO-IP-004"
                        value["history"][0]["status_before"] = "draft"
                    elif case == "creation_affected":
                        value["history"][0]["affected_ids"].remove("TASK-002")
                    elif case == "future_observation":
                        value["sources"][0]["accessed_at"] = "2999-01-01T00:00:00Z"
                    elif case == "future_validation":
                        value["validation"]["checked_at"] = "2999-01-01T00:00:00Z"
                    elif case == "past_validation":
                        value["validation"]["checked_at"] = "2000-01-01T00:00:00Z"
                    elif case == "future_updated_boundary":
                        value["updated_at"] = "2999-01-01T00:00:00Z"
                        value["validation"]["checked_at"] = value["updated_at"]
                    elif case == "huge_revision":
                        value["revision"] = 10**12
                    canonical_path.write_bytes(self.plan_state.canonical_bytes(value))
                before = tree_snapshot(case_root)
                validated = self.cli("validate", expected=5, root=case_root)
                self.assertEqual(validated["errors"][0]["category"], "unsafe_or_corrupt")
                created = self.cli(
                    "create",
                    "--input",
                    "-",
                    payload=self.example,
                    expected=5,
                    root=case_root,
                )
                self.assertEqual(created["errors"][0]["category"], "unsafe_or_corrupt")
                self.assertEqual(tree_snapshot(case_root), before)

        matrix_context = self.plan_state.resolve_context(
            str(self.root), "Implementation_Plans"
        )
        matrix_plan = canonical_fixture(
            self.plan_state, matrix_context, copy.deepcopy(self.example)
        )

        def value_paths(value, prefix=()):
            paths = []
            if isinstance(value, dict):
                for key, item in value.items():
                    path = (*prefix, key)
                    paths.append(path)
                    paths.extend(value_paths(item, path))
            elif isinstance(value, list):
                for index, item in enumerate(value):
                    path = (*prefix, index)
                    paths.append(path)
                    paths.extend(value_paths(item, path))
            return paths

        malformed_cases = 0
        for path in value_paths(matrix_plan):
            for replacement in (None, {}, [], [{"malformed": True}]):
                malformed = copy.deepcopy(matrix_plan)
                parent = malformed
                for component in path[:-1]:
                    parent = parent[component]
                if parent[path[-1]] == replacement:
                    continue
                parent[path[-1]] = copy.deepcopy(replacement)
                malformed_cases += 1
                try:
                    findings = self.plan_state.validate_plan_structure(
                        malformed, matrix_context
                    )
                except BaseException as exc:  # pragma: no cover - failure detail
                    self.fail(
                        f"Malformed-field matrix crashed at {path!r} with {replacement!r}: {exc!r}"
                    )
                self.assertIsInstance(findings, list)
        self.assertGreaterEqual(malformed_cases, 500)

    def test_tst_040_explicit_reconcile_is_bounded_and_repeatable(self):
        """TST-040: one reviewed orphan-temp removal becomes an idempotent no-op."""
        receipt = self.create()
        plan_dir = Path(receipt["canonical_path"]).parent
        orphan = plan_dir / (".PLAN.md.tmp-" + "A" * 32)
        orphan.write_bytes(b"synthetic transaction residue\n")
        digest = hashlib.sha256(orphan.read_bytes()).hexdigest()
        recovery = {
            "action": "remove_orphan_temp",
            "scope": "plan",
            "relative_path": orphan.name,
            "sha256": digest,
        }
        revision = receipt["revision"]
        first = self.cli(
            "reconcile",
            receipt["plan_id"],
            "--input",
            "-",
            "--confirmed",
            payload=recovery,
        )
        self.assertEqual(first["status"], "ok")
        self.assertTrue(first["mutation"])
        self.assertFalse(orphan.exists())
        second = self.cli(
            "reconcile",
            receipt["plan_id"],
            "--input",
            "-",
            "--confirmed",
            payload=recovery,
        )
        self.assertEqual(second["status"], "no_op")
        self.assertFalse(second["mutation"])
        self.assertEqual(second["plan"]["revision"], revision)

        absent_root = self.root / "absent-catalog-recovery"
        absent_root.mkdir()
        absent_before = tree_snapshot(absent_root)
        absent_token = "9" * 32
        absent_payloads = (
            {
                "action": "remove_abandoned_lock",
                "scope": "catalog",
                "token": absent_token,
            },
            {
                "action": "remove_released_lock",
                "scope": "catalog",
                "relative_name": (
                    ".to-implementation-plan.catalog.lock.released-"
                    + absent_token
                ),
                "token": absent_token,
            },
            {
                "action": "remove_partial_create",
                "scope": "catalog",
                "state": "empty",
                "directory": "Plan_absent_2026-08-29_99999999",
            },
            {
                "action": "remove_orphan_temp",
                "scope": "catalog",
                "relative_path": ".INDEX.md.tmp-" + "9" * 32,
                "sha256": "0" * 64,
            },
        )
        for absent_payload in absent_payloads:
            with self.subTest(absent_action=absent_payload["action"]):
                absent_result = self.cli(
                    "reconcile",
                    "catalog",
                    "--input",
                    "-",
                    "--confirmed",
                    payload=absent_payload,
                    root=absent_root,
                )
                self.assertEqual(absent_result["status"], "no_op")
                self.assertFalse(absent_result["mutation"])
                self.assertEqual(tree_snapshot(absent_root), absent_before)

        for malformed_recovery in (
            {"action": "remove_released_lock", "scope": {}},
            {
                "action": "remove_partial_create",
                "scope": "catalog",
                "state": {},
                "directory": "Plan_absent_2026-08-29_99999999",
            },
        ):
            malformed_result = self.cli(
                "reconcile",
                "catalog",
                "--input",
                "-",
                "--confirmed",
                payload=malformed_recovery,
                root=absent_root,
                expected=2,
            )
            self.assertEqual(
                malformed_result["errors"][0]["category"], "invalid_input"
            )
            self.assertEqual(tree_snapshot(absent_root), absent_before)

        plans_root = self.root / "Implementation_Plans"
        catalog_lock = plans_root / ".to-implementation-plan.catalog.lock"
        catalog_lock.mkdir()
        catalog_token = "B" * 32
        (catalog_lock / "owner.json").write_bytes(
            self.plan_state.canonical_bytes(
                {
                    "schema_version": 1,
                    "token": catalog_token,
                    "pid": 2_147_483_647,
                    "host": self.plan_state.socket.gethostname(),
                    "started_at": self.plan_state.timestamp(),
                    "command": "reindex",
                }
            )
        )
        catalog_recovery = {
            "action": "remove_abandoned_lock",
            "scope": "catalog",
            "token": catalog_token,
        }
        recovered = self.cli(
            "reconcile",
            "catalog",
            "--input",
            "-",
            "--confirmed",
            payload=catalog_recovery,
        )
        self.assertEqual(recovered["status"], "ok")
        self.assertTrue(recovered["mutation"])
        self.assertFalse(catalog_lock.exists())
        repeated = self.cli(
            "reconcile",
            "catalog",
            "--input",
            "-",
            "--confirmed",
            payload=catalog_recovery,
        )
        self.assertEqual(repeated["status"], "no_op")

        catalog_temp = plans_root / (".INDEX.md.tmp-" + "C" * 32)
        catalog_temp.write_bytes(b"reviewed catalog residue\n")
        temp_recovery = {
            "action": "remove_orphan_temp",
            "scope": "catalog",
            "relative_path": catalog_temp.name,
            "sha256": file_sha256(catalog_temp),
        }
        removed = self.cli(
            "reconcile",
            "catalog",
            "--input",
            "-",
            "--confirmed",
            payload=temp_recovery,
        )
        self.assertEqual(removed["status"], "ok")
        self.assertFalse(catalog_temp.exists())

        partial_retry_root = self.root / "partial-retry"
        partial_retry_root.mkdir()
        partial_retry_context = self.plan_state.resolve_context(
            str(partial_retry_root), "Implementation_Plans"
        )
        self.plan_state.ensure_catalog_for_write(partial_retry_context)
        partial_retry_directory = "Plan_retry_2026-08-29_12121212"
        partial_retry_name = ".plan.json.tmp-" + "1" * 32
        partial_retry_dir = (
            partial_retry_context.plans_root / partial_retry_directory
        )
        partial_retry_dir.mkdir()
        partial_retry_temp = partial_retry_dir / partial_retry_name
        partial_retry_temp.write_bytes(b"reviewed partial-create residue\n")
        partial_retry_payload = {
            "action": "remove_partial_create",
            "scope": "catalog",
            "state": "temporary",
            "directory": partial_retry_directory,
            "relative_path": partial_retry_name,
            "sha256": file_sha256(partial_retry_temp),
        }
        partial_retry_input = partial_retry_root / "partial-retry.json"
        partial_retry_input.write_text(
            json.dumps(partial_retry_payload), encoding="utf-8"
        )
        partial_identity_info = partial_retry_dir.stat()
        partial_identity = (
            partial_identity_info.st_dev,
            partial_identity_info.st_ino,
        )
        real_fsync = self.plan_state.os.fsync
        fsync_failed = False

        def fail_partial_directory_fsync(file_descriptor):
            nonlocal fsync_failed
            info = self.plan_state.os.fstat(file_descriptor)
            if (
                not fsync_failed
                and (info.st_dev, info.st_ino) == partial_identity
            ):
                fsync_failed = True
                raise OSError("synthetic post-unlink directory fsync failure")
            return real_fsync(file_descriptor)

        with patch.object(
            self.plan_state.os,
            "fsync",
            side_effect=fail_partial_directory_fsync,
        ):
            partial_outcome, partial_exit = self.plan_state.handle_reconcile(
                partial_retry_context,
                SimpleNamespace(
                    confirmed=True,
                    input=str(partial_retry_input),
                    selector="catalog",
                ),
            )
        self.assertEqual(partial_exit, self.plan_state.EXIT_CODES["io_error"])
        self.assertEqual(partial_outcome["status"], "partial")
        self.assertTrue(partial_outcome["mutation"])
        self.assertFalse(partial_retry_temp.exists())
        self.assertTrue(partial_retry_dir.is_dir())
        retry_payload = partial_outcome["recovery_required"]["input"]
        self.assertEqual(retry_payload["state"], "empty")
        self.assertNotIn("relative_path", retry_payload)
        self.assertNotIn("sha256", retry_payload)
        partial_retry_input.write_text(json.dumps(retry_payload), encoding="utf-8")
        retry_outcome, retry_exit = self.plan_state.handle_reconcile(
            partial_retry_context,
            SimpleNamespace(
                confirmed=True,
                input=str(partial_retry_input),
                selector="catalog",
            ),
        )
        self.assertEqual(retry_exit, 0)
        self.assertEqual(retry_outcome["status"], "ok")
        self.assertTrue(retry_outcome["mutation"])
        self.assertFalse(partial_retry_dir.exists())

        released_retry_root = self.root / "released-retry"
        released_retry_root.mkdir()
        released_retry_context = self.plan_state.resolve_context(
            str(released_retry_root), "Implementation_Plans"
        )
        self.plan_state.ensure_catalog_for_write(released_retry_context)
        released_retry_token = "2" * 32
        released_retry_name = (
            ".to-implementation-plan.catalog.lock.released-"
            + released_retry_token
        )
        released_retry_dir = (
            released_retry_context.plans_root / released_retry_name
        )
        released_retry_dir.mkdir()
        (released_retry_dir / "owner.json").write_bytes(
            self.plan_state.canonical_bytes(
                {
                    "schema_version": 1,
                    "token": released_retry_token,
                    "pid": 2_147_483_647,
                    "host": self.plan_state.socket.gethostname(),
                    "started_at": self.plan_state.timestamp(),
                    "command": "reindex",
                }
            )
        )
        released_retry_payload = {
            "action": "remove_released_lock",
            "scope": "catalog",
            "relative_name": released_retry_name,
            "token": released_retry_token,
        }
        released_retry_input = released_retry_root / "released-retry.json"
        released_retry_input.write_text(
            json.dumps(released_retry_payload), encoding="utf-8"
        )
        released_catalog_info = released_retry_context.plans_root.stat()
        released_catalog_identity = (
            released_catalog_info.st_dev,
            released_catalog_info.st_ino,
        )
        real_released_fsync = self.plan_state.os.fsync
        released_fsync_failed = False

        def fail_released_parent_fsync(file_descriptor):
            nonlocal released_fsync_failed
            info = self.plan_state.os.fstat(file_descriptor)
            if (
                not released_fsync_failed
                and (info.st_dev, info.st_ino) == released_catalog_identity
                and not released_retry_dir.exists()
            ):
                released_fsync_failed = True
                raise OSError("synthetic post-removal catalog fsync failure")
            return real_released_fsync(file_descriptor)

        with patch.object(
            self.plan_state.os,
            "fsync",
            side_effect=fail_released_parent_fsync,
        ):
            released_outcome, released_exit = self.plan_state.handle_reconcile(
                released_retry_context,
                SimpleNamespace(
                    confirmed=True,
                    input=str(released_retry_input),
                    selector="catalog",
                ),
            )
        self.assertEqual(released_exit, self.plan_state.EXIT_CODES["io_error"])
        self.assertEqual(released_outcome["status"], "partial")
        self.assertEqual(
            released_outcome["recovery_required"]["input"],
            released_retry_payload,
        )
        self.assertFalse(released_retry_dir.exists())
        released_retry, released_retry_exit = self.plan_state.handle_reconcile(
            released_retry_context,
            SimpleNamespace(
                confirmed=True,
                input=str(released_retry_input),
                selector="catalog",
            ),
        )
        self.assertEqual(released_retry_exit, 0)
        self.assertEqual(released_retry["status"], "no_op")
        self.assertFalse(released_retry["mutation"])

        race_root = self.root / "recovery-parent-swaps"
        inside_parent = race_root / "inside"
        outside_parent = race_root / "outside"
        inside_parent.mkdir(parents=True)
        outside_parent.mkdir()
        abandoned_token = "D" * 32
        owner = {
            "schema_version": 1,
            "token": abandoned_token,
            "pid": 2_147_483_647,
            "host": self.plan_state.socket.gethostname(),
            "started_at": self.plan_state.timestamp(),
            "command": "reindex",
        }
        for parent in (inside_parent, outside_parent):
            lock = parent / ".to-implementation-plan.catalog.lock"
            lock.mkdir()
            (lock / "owner.json").write_bytes(
                self.plan_state.canonical_bytes(owner)
            )
        bound_parent = race_root / "inside-bound"
        swapped = False

        def swap_abandoned_parent(_owner):
            nonlocal swapped
            if not swapped:
                inside_parent.rename(bound_parent)
                inside_parent.symlink_to(outside_parent, target_is_directory=True)
                swapped = True
            return False

        with patch.object(
            self.plan_state,
            "_pid_is_active",
            side_effect=swap_abandoned_parent,
        ):
            with self.assertRaises(self.plan_state.AppError) as abandoned_race:
                self.plan_state._remove_reviewed_lock(
                    inside_parent / ".to-implementation-plan.catalog.lock",
                    abandoned_token,
                )
        self.assertEqual(abandoned_race.exception.category, "unsafe_or_corrupt")
        self.assertTrue(
            (bound_parent / ".to-implementation-plan.catalog.lock").is_dir()
        )
        self.assertTrue(
            (outside_parent / ".to-implementation-plan.catalog.lock").is_dir()
        )

        released_inside = race_root / "released-inside"
        released_outside = race_root / "released-outside"
        released_inside.mkdir()
        released_outside.mkdir()
        released_token = "E" * 32
        released_name = (
            ".to-implementation-plan.plan.lock.released-" + released_token
        )
        released_owner = {**owner, "token": released_token, "command": "update"}
        for parent in (released_inside, released_outside):
            residue = parent / released_name
            residue.mkdir()
            (residue / "owner.json").write_bytes(
                self.plan_state.canonical_bytes(released_owner)
            )
        released_identity_info = released_inside.stat()
        released_identity = (
            released_identity_info.st_dev,
            released_identity_info.st_ino,
        )
        released_bound = race_root / "released-inside-bound"
        released_swapped = False

        def swap_released_parent(_owner):
            nonlocal released_swapped
            if not released_swapped:
                released_inside.rename(released_bound)
                released_inside.symlink_to(
                    released_outside, target_is_directory=True
                )
                released_swapped = True
            return False

        with patch.object(
            self.plan_state,
            "_pid_is_active",
            side_effect=swap_released_parent,
        ):
            with self.assertRaises(self.plan_state.AppError) as released_race:
                self.plan_state.remove_released_lock_residue_bound(
                    parent_path=released_inside,
                    expected_parent_identity=released_identity,
                    relative_name=released_name,
                    token=released_token,
                    expected_owner_hash=None,
                )
        self.assertEqual(released_race.exception.category, "unsafe_or_corrupt")
        self.assertTrue((released_bound / released_name).is_dir())
        self.assertTrue((released_outside / released_name).is_dir())

        partial_inside = race_root / "partial-inside"
        partial_outside = race_root / "partial-outside"
        partial_inside.mkdir()
        partial_outside.mkdir()
        partial_directory = "Plan_race_2026-08-29_ABCDEF12"
        partial_name = ".plan.json.tmp-" + "F" * 32
        for parent in (partial_inside, partial_outside):
            directory_path = parent / partial_directory
            directory_path.mkdir()
            (directory_path / partial_name).write_bytes(b"partial race bytes\n")
        partial_info = partial_inside.stat()
        partial_identity = (partial_info.st_dev, partial_info.st_ino)
        partial_bound = race_root / "partial-inside-bound"
        real_hash_at = self.plan_state.sha256_regular_file_at
        partial_swapped = False

        def hash_then_swap_partial(directory_fd, name):
            nonlocal partial_swapped
            result = real_hash_at(directory_fd, name)
            if not partial_swapped:
                partial_inside.rename(partial_bound)
                partial_inside.symlink_to(partial_outside, target_is_directory=True)
                partial_swapped = True
            return result

        with patch.object(
            self.plan_state,
            "sha256_regular_file_at",
            side_effect=hash_then_swap_partial,
        ):
            with self.assertRaises(self.plan_state.AppError) as partial_race:
                self.plan_state.remove_partial_create_bound(
                    catalog_path=partial_inside,
                    expected_catalog_identity=partial_identity,
                    directory=partial_directory,
                    expected_state="temporary",
                    relative_path=partial_name,
                    expected_hash=hashlib.sha256(b"partial race bytes\n").hexdigest(),
                )
        self.assertEqual(partial_race.exception.category, "unsafe_or_corrupt")
        self.assertTrue((partial_bound / partial_directory / partial_name).is_file())
        self.assertTrue((partial_outside / partial_directory / partial_name).is_file())

        orphan_inside = race_root / "orphan-inside"
        orphan_outside = race_root / "orphan-outside"
        orphan_inside.mkdir()
        orphan_outside.mkdir()
        orphan_name = ".INDEX.md.tmp-" + "A" * 32
        for parent in (orphan_inside, orphan_outside):
            (parent / orphan_name).write_bytes(b"orphan race bytes\n")
        orphan_info = orphan_inside.stat()
        orphan_identity = (orphan_info.st_dev, orphan_info.st_ino)
        orphan_bound = race_root / "orphan-inside-bound"
        orphan_swapped = False

        def hash_then_swap_orphan(directory_fd, name):
            nonlocal orphan_swapped
            result = real_hash_at(directory_fd, name)
            if not orphan_swapped:
                orphan_inside.rename(orphan_bound)
                orphan_inside.symlink_to(orphan_outside, target_is_directory=True)
                orphan_swapped = True
            return result

        with patch.object(
            self.plan_state,
            "sha256_regular_file_at",
            side_effect=hash_then_swap_orphan,
        ):
            with self.assertRaises(self.plan_state.AppError) as orphan_race:
                self.plan_state.remove_orphan_temp_bound(
                    parent_path=orphan_inside,
                    expected_parent_identity=orphan_identity,
                    target_name=orphan_name,
                    expected_hash=hashlib.sha256(b"orphan race bytes\n").hexdigest(),
                )
        self.assertEqual(orphan_race.exception.category, "unsafe_or_corrupt")
        self.assertTrue((orphan_bound / orphan_name).is_file())
        self.assertTrue((orphan_outside / orphan_name).is_file())

    def test_tst_043_requirement_id_cannot_be_reused_for_new_meaning(self):
        """TST-043: semantic identity fields cannot change under a stable ID."""
        receipt = self.create()
        canonical = self.show(receipt)["data"]["canonical"]

        malformed_baseline_values = (
            ("title", None),
            ("project", None),
            ("objective", []),
            ("scope", []),
            ("sources", {}),
            ("requirements", {}),
            ("decisions", {}),
            ("open_questions", {}),
            ("assumptions", {}),
            ("phases", {}),
            ("tasks", {}),
            ("coverage", []),
        )
        malformed_before = tree_snapshot(self.root)
        for field, malformed_value in malformed_baseline_values:
            with self.subTest(malformed_baseline_field=field):
                malformed = self.update_baseline(
                    receipt,
                    {field: malformed_value},
                    expected=2,
                )
                self.assertEqual(
                    malformed["errors"][0]["category"], "invalid_input"
                )
                self.assertEqual(tree_snapshot(self.root), malformed_before)

        malformed_phase = self.cli(
            "update-phase",
            receipt["plan_id"],
            "PHASE-001",
            "--expect-revision",
            str(receipt["revision"]),
            "--expect-sha256",
            receipt["sha256"],
            "--input",
            "-",
            payload={
                "patch": {"scope": None},
                "summary": "Malformed phase patch fixture.",
                "authority_basis": "Explicit isolated malformed-input fixture.",
            },
            expected=2,
        )
        self.assertEqual(
            malformed_phase["errors"][0]["category"], "invalid_input"
        )
        self.assertEqual(tree_snapshot(self.root), malformed_before)
        malformed_task = self.update_task(
            receipt,
            "TASK-001",
            {"dependencies": None},
            expected=2,
        )
        self.assertEqual(
            malformed_task["errors"][0]["category"], "invalid_input"
        )
        self.assertEqual(tree_snapshot(self.root), malformed_before)

        requirements = copy.deepcopy(canonical["requirements"])
        requirements[0].update(
            {
                "title": "Publish a destructive migration",
                "outcome": "Replace the original diagnostic with unrelated destructive work.",
                "intent": "Reuse the old identifier for a different meaning.",
            }
        )
        before = tree_snapshot(self.root)
        result = self.update_baseline(
            receipt,
            {"requirements": requirements},
            material_change=True,
            expected=2,
        )
        self.assertEqual(result["errors"][0]["category"], "invalid_input")
        self.assertIn("REQ-001", result["errors"][0]["targets"])
        self.assertEqual(tree_snapshot(self.root), before)

        canonical = self.show(receipt)["data"]["canonical"]
        tasks = copy.deepcopy(canonical["tasks"])
        tasks[0]["status"] = "completed"
        tasks[0]["completed_at"] = "2026-08-29T00:00:00Z"
        tasks[0]["evidence"] = [
            {
                "evidence_id": "EVID-900",
                "timestamp": "2026-08-29T00:00:00Z",
                "evidence_type": "test",
                "result_status": "passed",
                "description": "Forged baseline-update evidence.",
                "locator_or_command": "forged",
                "observed_result": "Forged baseline update claimed success.",
                "verification_level": "targeted_tests_passed",
                "observation_source": "tool",
                "target_digest": self.plan_state.target_definition_digest(tasks[0], "task"),
            }
        ]
        lifecycle_before = tree_snapshot(self.root)
        lifecycle = self.update_baseline(receipt, {"tasks": tasks}, expected=2)
        self.assertEqual(lifecycle["errors"][0]["category"], "invalid_input")
        self.assertEqual(tree_snapshot(self.root), lifecycle_before)

        mismatch = copy.deepcopy(self.example)
        mismatch["requirements"][0]["status"] = "dispositioned"
        mismatch["requirements"][0]["disposition"] = {
            "kind": "out_of_scope",
            "reason": "Requirement-level reason.",
            "authority_basis": "Current explicit fixture authority.",
        }
        mismatch["coverage"]["requirement_to_task"][0]["disposition"] = {
            "kind": "not_required",
            "reason": "Different coverage reason.",
            "authority_basis": "Different authority.",
        }
        mismatch_root = self.root / "disposition-mismatch"
        mismatch_root.mkdir()
        mismatch_result = self.cli(
            "create", "--input", "-", payload=mismatch, expected=2, root=mismatch_root
        )
        self.assertEqual(mismatch_result["errors"][0]["category"], "invalid_input")

        sources = copy.deepcopy(canonical["sources"])
        sources[0]["title"] = "Rewritten provenance under the same source ID"
        source_before = tree_snapshot(self.root)
        source_rewrite = self.update_baseline(
            receipt, {"sources": sources}, material_change=True, expected=2
        )
        self.assertEqual(source_rewrite["errors"][0]["category"], "invalid_input")
        self.assertIn("SRC-001", source_rewrite["errors"][0]["targets"])
        self.assertEqual(tree_snapshot(self.root), source_before)

        changed_tasks = copy.deepcopy(canonical["tasks"])
        changed_tasks[0]["title"] = "Clarified bounded task title"
        updated = self.update_baseline(
            receipt, {"tasks": changed_tasks}, material_change=True
        )["plan"]
        updated_plan = self.show(updated)["data"]["canonical"]
        self.assertEqual(updated_plan["history"][-1]["action_id"], "TO-IP-004")
        self.assertIn("TASK-001", updated_plan["history"][-1]["affected_ids"])

        bypass = copy.deepcopy(self.example)
        bypass["tasks"][0]["status"] = "completed"
        bypass["tasks"][0]["completed_at"] = "2026-08-29T00:00:00Z"
        bypass["requirements"][0]["status"] = "satisfied"
        bypass_root = self.root / "create-lifecycle-bypass"
        bypass_root.mkdir()
        rejected_bypass = self.cli(
            "create", "--input", "-", payload=bypass, expected=2, root=bypass_root
        )
        self.assertEqual(rejected_bypass["errors"][0]["category"], "invalid_input")
        self.assertFalse((bypass_root / "Implementation_Plans").exists())

        namespace_collision = copy.deepcopy(self.example)
        namespace_collision["requirements"][0]["requirement_id"] = "TASK-001"
        for task in namespace_collision["tasks"]:
            task["requirement_ids"] = ["TASK-001"]
        namespace_collision["coverage"]["source_to_requirement"][0][
            "requirement_ids"
        ] = ["TASK-001"]
        namespace_collision["coverage"]["requirement_to_task"][0][
            "requirement_id"
        ] = "TASK-001"
        collision_root = self.root / "cross-namespace-collision"
        collision_root.mkdir()
        rejected_collision = self.cli(
            "create",
            "--input",
            "-",
            payload=namespace_collision,
            expected=2,
            root=collision_root,
        )
        collision_findings = rejected_collision["data"]["details"]["findings"]
        self.assertIn(
            "reserved_identifier_namespace", finding_codes(collision_findings)
        )
        self.assertFalse((collision_root / "Implementation_Plans").exists())

    def test_tst_049_isolated_package_copy_smoke(self):
        """TST-049: copied package runs create/show/validate/update/evidence/rebuild."""
        package_before = tree_snapshot(SKILL)
        copied_parent = self.root / "portable"
        copied_skill = copied_parent / "to-implementation-plan"
        shutil.copytree(
            SKILL,
            copied_skill,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        project = self.root / "isolated-project"
        project.mkdir()
        copied_script = copied_skill / "scripts" / "plan_state.py"
        receipt = self.create(root=project, script=copied_script)
        self.assertEqual(self.show(receipt, root=project, script=copied_script)["status"], "ok")
        self.assertEqual(
            self.cli(
                "validate", receipt["plan_id"], root=project, script=copied_script
            )["data"]["status"],
            "pass",
        )
        receipt = self.update_baseline(
            receipt,
            {"title": "Portable updated title"},
            root=project,
            script=copied_script,
        )["plan"]
        receipt = self.cli(
            "update-phase",
            receipt["plan_id"],
            "PHASE-001",
            "--expect-revision",
            str(receipt["revision"]),
            "--expect-sha256",
            receipt["sha256"],
            "--input",
            "-",
            payload={
                "patch": {
                    "risks": [
                        "Portable smoke must preserve the isolated project boundary."
                    ]
                },
                "summary": "Exercise the copied update-phase route.",
                "authority_basis": "Explicit isolated portability smoke authority.",
            },
            root=project,
            script=copied_script,
        )["plan"]
        receipt = self.set_status(
            receipt, "ready", root=project, script=copied_script
        )["plan"]
        receipt = self.set_status(
            receipt, "in_progress", root=project, script=copied_script
        )["plan"]
        receipt = self.record_evidence(
            receipt, "TASK-001", 1, root=project, script=copied_script
        )["plan"]
        plan_dir = Path(receipt["canonical_path"]).parent
        (plan_dir / "PLAN.md").unlink()
        self.assertTrue(
            self.cli(
                "rebuild-projections",
                receipt["plan_id"],
                root=project,
                script=copied_script,
            )["mutation"]
        )
        self.assertEqual(
            self.cli(
                "validate", receipt["plan_id"], root=project, script=copied_script
            )["data"]["status"],
            "pass",
        )
        self.assertEqual(tree_snapshot(SKILL), package_before)
        self.assertFalse(any(path.name == "__pycache__" for path in copied_skill.rglob("__pycache__")))


class PackageContractTests(unittest.TestCase):
    maxDiff = None

    def test_tst_001_skill_frontmatter_and_name(self):
        """TST-001: validate frontmatter, exact name, and no scaffold residue."""
        raw = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(raw.startswith("---\n"))
        parts = raw.split("---", 2)
        self.assertEqual(len(parts), 3)
        fields: dict[str, str] = {}
        for line in parts[1].strip().splitlines():
            key, separator, value = line.partition(":")
            self.assertEqual(separator, ":", line)
            self.assertNotIn(key.strip(), fields)
            fields[key.strip()] = value.strip()
        self.assertEqual(set(fields), {"name", "description"})
        self.assertEqual(fields["name"], "to-implementation-plan")
        self.assertRegex(fields["name"], r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
        self.assertLessEqual(len(fields["name"]), 64)
        self.assertTrue(fields["description"])
        self.assertLessEqual(len(fields["description"]), 1024)
        self.assertIn("explicit", fields["description"].lower())
        self.assertNotRegex(raw, r"(?i)\b(?:TODO|TBD|FIXME)\b|\[\s*TODO\s*\]")

    def test_tst_002_ui_metadata_is_explicit_only(self):
        """TST-002: UI values match the skill and implicit invocation is false."""
        raw = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertRegex(raw, r'(?m)^  display_name: "To Implementation Plan"$')
        self.assertRegex(raw, r'(?m)^  short_description: "Create and track implementation plans"$')
        self.assertIn("$to-implementation-plan", raw)
        self.assertRegex(
            raw,
            r"(?m)^policy:\n  allow_implicit_invocation: false$",
        )
        self.assertNotRegex(raw, r"(?m)^\s*(?:icon|dependencies|mcp_servers):")

    def test_tst_003_ordinary_planning_has_static_no_activation_contract(self):
        """TST-003: static half of the Director's ordinary-prompt scenario."""
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        metadata = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
        before = tree_snapshot(SKILL)
        self.assertIn("Ordinary requests", skill)
        self.assertIn("do not activate this skill", skill)
        self.assertIn("allow_implicit_invocation: false", metadata)
        self.assertIn("TST-003", DIRECTOR_LEVEL_SCENARIOS)
        self.assertEqual(tree_snapshot(SKILL), before)

    def test_tst_004_explicit_invocation_routes_one_requested_operation(self):
        """TST-004: explicit invocation and one-operation routing contract."""
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        actions = (SKILL / "ACTIONS.md").read_text(encoding="utf-8")
        metadata = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn("invokes `$to-implementation-plan`", skill)
        self.assertIn("one action ID and helper route", skill)
        self.assertIn("$to-implementation-plan", metadata)
        self.assertEqual(set(re.findall(r"TO-IP-\d{3}", actions)), EXPECTED_ACTION_IDS)
        self.assertIn("TST-004", DIRECTOR_LEVEL_SCENARIOS)

    def test_tst_048_package_links_metadata_templates_and_readme(self):
        """TST-048: complete inventory, links, templates, docs, and routes."""
        self.assertEqual(package_inventory(), EXPECTED_PACKAGE_FILES)
        for relative in sorted(EXPECTED_PACKAGE_FILES):
            with self.subTest(file=relative):
                self.assertTrue((SKILL / relative).is_file(), relative)

        markdown_files = sorted(SKILL.rglob("*.md"))
        for document in markdown_files:
            raw = document.read_text(encoding="utf-8")
            with self.subTest(document=document.relative_to(SKILL).as_posix()):
                self.assertFalse(raw.startswith("\ufeff"))
                self.assertTrue(raw.endswith("\n"))
                if document.parent.name != "assets":
                    self.assertNotRegex(raw, r"(?i)\b(?:TODO|TBD|FIXME)\b|\[\s*TODO\s*\]")
                for target in local_markdown_links(raw):
                    resolved = (document.parent / target).resolve()
                    self.assertTrue(resolved.is_file(), f"{document}: {target}")

        readme = (SKILL / "README.md").read_text(encoding="utf-8")
        for concept in (
            "source-only",
            "install",
            "explicit",
            "input",
            "Implementation_Plans",
            "lifecycle",
            "evidence",
            "validate",
            "recovery",
        ):
            with self.subTest(readme_concept=concept):
                self.assertIn(concept.casefold(), readme.casefold())

        actions = (SKILL / "ACTIONS.md").read_text(encoding="utf-8")
        self.assertEqual(set(re.findall(r"`([a-z][a-z-]+)(?:\s|`)", actions)) & EXPECTED_ROUTES,
                         EXPECTED_ROUTES)
        contract = (SKILL / "references" / "plan-contract.md").read_text(
            encoding="utf-8"
        )
        lifecycle = (
            SKILL / "references" / "lifecycle-and-recovery.md"
        ).read_text(encoding="utf-8")
        phase_template = (SKILL / "assets" / "phase-template.md").read_text(
            encoding="utf-8"
        )
        for marker in (
            "initial_record_ids",
            "result_status",
            "remove_released_lock",
            "state: temporary",
        ):
            with self.subTest(contract_marker=marker):
                self.assertIn(marker, contract)
        self.assertIn("result_status", lifecycle)
        self.assertIn("result status", phase_template)

    def test_tst_050_source_only_static_scope_and_director_audit_route(self):
        """TST-050: portable source boundary plus the Director's live-state audit."""
        self.assertEqual(package_inventory(), EXPECTED_PACKAGE_FILES)
        self.assertIn("TST-050", DIRECTOR_LEVEL_SCENARIOS)
        test_source = Path(__file__).read_text(encoding="utf-8")
        covered = {
            int(value)
            for value in re.findall(r"(?m)^\s+def test_tst_(\d{3})_", test_source)
        }
        self.assertEqual(covered, set(range(1, 51)))
        self.assertEqual(
            len(re.findall(r"(?m)^\s+def test_tst_\d{3}_", test_source)),
            50,
        )
        script = SCRIPT.read_text(encoding="utf-8")
        syntax = ast.parse(script)
        imports: set[str] = set()
        for node in ast.walk(syntax):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".", 1)[0])
        self.assertTrue(imports <= sys.stdlib_module_names, sorted(imports - sys.stdlib_module_names))
        prohibited = (
            "depot/manifest.json",
            ".agents/skills",
            "git push",
            "git commit",
            "gh pr",
            "requests.",
            "urllib.request",
        )
        # Only the optional read-only adapter resolves the selected installed
        # ontology helper. It grants no installation or cross-project writes.
        tree = ast.parse(script)
        adapter = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                       and node.name == "_ontology_guard_adapter")
        lines = script.splitlines()
        source_without_adapter = "\n".join(lines[:adapter.lineno - 1] + lines[adapter.end_lineno:])
        for marker in prohibited:
            with self.subTest(marker=marker):
                self.assertNotIn(marker, source_without_adapter if marker == ".agents/skills" else script)
        for node in ast.walk(adapter):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                self.assertNotIn(node.func.attr, {"write_text", "write_bytes", "unlink", "replace", "copytree"})


if __name__ == "__main__":
    unittest.main()
