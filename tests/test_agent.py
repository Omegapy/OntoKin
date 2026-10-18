"""Independent protocol scenarios for the durable OntoKin agent interface.

The A01--A10 expectations come from the published language manifest. These
tests submit real source and operate the persistent service; they never stub
successful parsing, evaluation, editing, cancellation, or retry outcomes.
"""

from __future__ import annotations

import copy
import base64
from contextlib import contextmanager
from functools import lru_cache
import hashlib
import itertools
import json
import math
from pathlib import Path
import re
import select
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch as instrument

from ontokin.agent import AgentService
from ontokin.fixtures import DEFAULT_FIXTURES, load_manifest, materialize
from test_export import DecodedGLB


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "docs/language-design/agent-v0.1"
REQUEST_SCHEMA = SCHEMAS / "request.schema.json"
RESPONSE_SCHEMA = SCHEMAS / "response.schema.json"
PROJECT = "acceptance-project"
MODULE_ID = ["service-case"]
SCENE_ID = MODULE_ID + ["demo"]
FIRST_ID = SCENE_ID + ["first"]
SECOND_ID = SCENE_ID + ["second"]
RADIUS_ID = MODULE_ID + ["definitions", "ball", "radius"]

VALID_SOURCE = '''ontokin "0.1";
module ServiceCase @ "service-case";
profile "core-0.1";
class Ball @ "ball" {
    public param radius @ "radius": Length = 0.2[m];
    geometry = sphere(self.radius);
    appearance = rgba(0.2, 0.4, 0.6, 1);
}
scene Demo @ "demo" {
    duration = 2[s];
    gravity = vector(world, 0[m/s^2], -9.81[m/s^2], 0[m/s^2]);
    object first @ "first": Ball {
        // café 🟣: preserve this instance comment.
        placement = pose(world, vec3(0[m], 2[m], 0[m]), quat(1, 0, 0, 0));
    }
    object second @ "second": Ball {
        placement = pose(world, vec3(2[m], 2[m], 0[m]), quat(1, 0, 0, 0));
    }
    action travel @ "travel" = move(first, vector(world, 1[m/s], 0[m/s], 0[m/s]), 2[s]);
    at 0[s] sequence { start travel; }
}
'''

FUTURE_FAILURE_SOURCE = VALID_SOURCE.replace(
    "at 0[s] sequence { start travel; }",
    "at 0[s] sequence { start travel; }\n    at 1[s] sequence { start travel; }")

FRAME_SOURCE = VALID_SOURCE.replace(
    "quat(1, 0, 0, 0)", "axis_angle(vec3(0, 0, 1), 90[deg])", 1).replace(
    "at 0[s] sequence { start travel; }",
    '''action drift @ "drift" = move(second, vector(world, 2[m/s], 0[m/s], 0[m/s]), 2[s]);
    at 0[s] sequence { start travel; start drift; }''')

CASE_TESTS = {
    "A01": "test_A01_stale_edit_preserves_current_revision",
    "A02": "test_A02_invalid_multi_patch_candidate_is_atomic",
    "A03": "test_A03_same_canonical_request_has_one_durable_effect",
    "A04": "test_A04_request_identity_cannot_change_payload",
    "A05": "test_A05_inspection_is_repeatable_without_advancing_run",
    "A06": "test_A06_continuation_cannot_switch_context",
    "A07": "test_A07_requested_support_is_not_silently_downgraded",
    "A08": "test_A08_cancel_after_commit_reports_accepted_result",
    "A09": "test_A09_expired_result_retains_unknown_outcome_tombstone",
    "A10": "test_A10_rotated_velocity_keeps_world_measurement_frame",
}


@lru_cache(maxsize=None)
def _schema_document(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def schema_errors(value, schema_path, schema=None, path="$"):
    """Validate the finite JSON Schema keyword subset used by these artifacts.

    This independent test helper has no network resolver or runtime dependency.
    It is deliberately not advertised as a general JSON Schema implementation.
    """
    schema_path = Path(schema_path).resolve()
    root = _schema_document(schema_path)
    schema = root if schema is None else schema
    if "$ref" in schema:
        filename, _, pointer = schema["$ref"].partition("#")
        target_path = (schema_path.parent / filename).resolve() if filename else schema_path
        target = _schema_document(target_path)
        for part in pointer.removeprefix("/").split("/") if pointer else []:
            target = target[part.replace("~1", "/").replace("~0", "~")]
        return schema_errors(value, target_path, target, path)
    for keyword in ("oneOf", "anyOf"):
        if keyword in schema:
            matches = sum(not schema_errors(value, schema_path, option, path)
                          for option in schema[keyword])
            if (keyword == "oneOf" and matches != 1) or (keyword == "anyOf" and matches == 0):
                return [f"{path}: {keyword} matched {matches} alternatives"]
    check_type = {
        "object": lambda x: isinstance(x, dict),
        "array": lambda x: isinstance(x, list),
        "string": lambda x: isinstance(x, str),
        "integer": lambda x: type(x) is int or (type(x) is float and math.isfinite(x) and x.is_integer()),
        "number": lambda x: type(x) in (int, float) and math.isfinite(x),
        "boolean": lambda x: type(x) is bool,
        "null": lambda x: x is None,
    }
    if "type" in schema and not check_type[schema["type"]](value):
        return [f"{path}: wrong type"]
    errors = []
    if "if" in schema:
        branch = "else" if schema_errors(value, schema_path, schema["if"], path) else "then"
        if branch in schema:
            errors += schema_errors(value, schema_path, schema[branch], path)
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: wrong constant")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: unknown enum")
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}: missing {key}")
        for key, required in schema.get("dependentRequired", {}).items():
            if key in value:
                errors += [f"{path}: {key} requires {dependency}" for dependency in required if dependency not in value]
        properties = schema.get("properties", {})
        for key, item in value.items():
            if key in properties:
                errors += schema_errors(item, schema_path, properties[key], path + "." + key)
            elif schema.get("additionalProperties") is False:
                errors.append(f"{path}: extra {key}")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(f"{path}: too few items")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append(f"{path}: too many items")
        if schema.get("uniqueItems") and len({json.dumps(v, sort_keys=True) for v in value}) != len(value):
            errors.append(f"{path}: duplicate items")
        if "items" in schema:
            for index, item in enumerate(value):
                errors += schema_errors(item, schema_path, schema["items"], f"{path}[{index}]")
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{path}: empty string")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errors.append(f"{path}: long string")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            errors.append(f"{path}: invalid pattern")
    if type(value) in (int, float):
        for keyword, compare in (("minimum", lambda a, b: a < b),
                                 ("maximum", lambda a, b: a > b),
                                 ("exclusiveMinimum", lambda a, b: a <= b)):
            if keyword in schema and compare(value, schema[keyword]):
                errors.append(f"{path}: violates {keyword}")
    return errors


def patch(source, needle, replacement, element_id):
    raw, selected = source.encode("utf-8"), needle.encode("utf-8")
    if raw.count(selected) != 1:
        raise AssertionError(f"Test patch must have one source match: {needle!r}")
    start = raw.index(selected)
    return {"element_id": list(element_id), "start_byte": start,
            "end_byte": start + len(selected), "expected_text": needle,
            "replacement": replacement}


def request(operation, request_id, *, project_id=PROJECT, **fields):
    return {"schema_version": "ontokin.agent/0.1", "project_id": project_id,
            "request_id": request_id, "operation": operation, **fields}


class AgentContractTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="ontokin-agent-test-")
        self.store_path = Path(self.temporary.name) / "state"
        self.service = AgentService(self.store_path)
        self.serial = itertools.count(1)
        self.evidence = []

    def tearDown(self):
        self.service.close()
        self.temporary.cleanup()

    def make(self, operation, **fields):
        return request(operation, f"request-{next(self.serial)}", **fields)

    def call(self, submitted):
        self.assertEqual(schema_errors(submitted, REQUEST_SCHEMA), [])
        result = self.service.handle(submitted, wait=True)
        self.assertEnvelope(result)
        self.evidence.append({"request": copy.deepcopy(submitted), "response": copy.deepcopy(result)})
        return result

    def assertEnvelope(self, result):
        self.assertEqual(schema_errors(result, RESPONSE_SCHEMA), [], result)
        json.dumps(result, ensure_ascii=False, allow_nan=False).encode("utf-8")

    def assertSuccess(self, result):
        self.assertEqual(result["status"], "succeeded", result)
        self.assertIsNone(result["protocol_error"], result)

    def assertCode(self, result, code):
        self.assertIn(result["status"], ("rejected", "failed"), result)
        codes = [d["code"] for d in result["diagnostics"]]
        if result["protocol_error"] is not None:
            codes.append(result["protocol_error"]["code"])
        self.assertIn(code, codes, result)

    def create(self, source=VALID_SOURCE, level="represented"):
        result = self.call(self.make("create", filename="service.ok", source=source,
                                     expected_revision=None, requested_level=level, budgets={}))
        self.assertSuccess(result)
        self.assertEqual(result["accepted_revision"], result["source_revision"])
        self.assertTrue(result["source_revision"])
        return result

    def edit(self, revision, patches, level="represented", **extra):
        return self.call(self.make("edit", expected_revision=revision, patches=patches,
                                   requested_level=level, budgets=extra.pop("budgets", {}), **extra))

    def read(self, revision):
        return self.service.read_source(PROJECT, revision).raw.decode("utf-8")

    def inspect(self, revision, *, selector=None, fields=None, run_id=None, time=None,
                limit=100, cursor=None, frame="world"):
        return self.call(self.make("inspect", source_revision=revision,
                                   selector=selector if selector is not None else {"kind": "object"},
                                   fields=fields or ["identity", "state"], limit=limit,
                                   cursor=cursor, run_id=run_id, time=time, frame=frame))

    def evaluate(self, revision, time, run_id=None):
        return self.call(self.make("evaluate", source_revision=revision, run_id=run_id,
                                   until_seconds=time, budgets={}))

    def reopen(self):
        self.service.close()
        self.service = AgentService(self.store_path)

    @contextmanager
    def prepared_worker(self):
        """Pause a real subprocess after computation, before its atomic commit.

        The wrapper only synchronizes the race. Parsing, validation, evaluation,
        source retention, ownership, and commit all use the real implementation.
        """
        code = '''import sys
from pathlib import Path
from ontokin.agent import AgentService
service = AgentService(Path(sys.argv[1]))
execute = service._execute
def pause_after_computation(task, check):
    execute(task, check)
    print("prepared", flush=True)
    sys.stdin.readline()
service._execute = pause_after_computation
try:
    assert service.work_next(), "No queued work to prepare"
finally:
    service.close()
'''
        process = subprocess.Popen([sys.executable, "-c", code, str(self.store_path)], cwd=ROOT,
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, bufsize=1)
        try:
            self.assertTrue(select.select([process.stdout], [], [], 10)[0], "Worker did not prepare real work")
            self.assertEqual(process.stdout.readline().strip(), "prepared")
            yield process
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
            for stream in (process.stdin, process.stdout, process.stderr):
                stream.close()

    def test_A01_stale_edit_preserves_current_revision(self):
        first = self.create()["source_revision"]
        change = patch(VALID_SOURCE, "0.2[m]", "0.3[m]", RADIUS_ID)
        accepted = self.edit(first, [change])
        self.assertSuccess(accepted)
        stale = self.edit(first, [patch(VALID_SOURCE, "0.2[m]", "0.4[m]", RADIUS_ID)])
        self.assertCode(stale, "OKL-E-REVISION")
        self.assertEqual(stale["accepted_revision"], accepted["accepted_revision"])
        self.assertEqual(self.read(accepted["source_revision"]), VALID_SOURCE.replace("0.2[m]", "0.3[m]"))

    def test_A02_invalid_multi_patch_candidate_is_atomic(self):
        revision = self.create()["source_revision"]
        changes = [patch(VALID_SOURCE, "1[m/s]", "2[m/s]", SCENE_ID + ["travel"]),
                   patch(VALID_SOURCE, "0.2[m]", "1[kg]", RADIUS_ID)]
        rejected = self.edit(revision, changes)
        self.assertCode(rejected, "OKL-E-UNIT")
        self.assertEqual(rejected["accepted_revision"], revision)
        self.assertEqual(self.read(revision), VALID_SOURCE)
        candidate = VALID_SOURCE.replace("1[m/s]", "2[m/s]").replace("0.2[m]", "1[kg]")
        self.assertEqual(self.read(rejected["source_revision"]), candidate)
        diagnostic = next(d for d in rejected["diagnostics"] if d["code"] == "OKL-E-UNIT")
        self.assertEqual(diagnostic["source_revision"], rejected["source_revision"])
        location = diagnostic["primary"]
        self.assertEqual(candidate.encode()[location["start_byte"]:location["end_byte"]], b"1[kg]")

    def test_A03_same_canonical_request_has_one_durable_effect(self):
        revision = self.create()["source_revision"]
        submitted = self.make("edit", expected_revision=revision,
                              patches=[patch(VALID_SOURCE, "0.2[m]", "0.3[m]", RADIUS_ID)],
                              requested_level="evaluated", budgets={})
        receipt = self.service.submit(submitted)
        retry = self.service.submit(dict(reversed(list(submitted.items()))))
        self.assertEnvelope(receipt)
        self.assertEqual(retry, receipt)
        self.assertEqual(receipt["status"], "queued")
        self.assertTrue(self.service.work_next())
        completed = self.call(submitted)
        self.assertSuccess(completed)
        self.assertTrue(completed["run_id"])
        self.reopen()
        repeated = self.call(dict(reversed(list(submitted.items()))))
        self.assertEqual(repeated, completed)
        self.assertFalse(self.service.work_next())
        self.assertEqual(self.read(completed["source_revision"]), VALID_SOURCE.replace("0.2[m]", "0.3[m]"))

    def test_A04_request_identity_cannot_change_payload(self):
        revision = self.create()["source_revision"]
        submitted = self.make("edit", expected_revision=revision,
                              patches=[patch(VALID_SOURCE, "0.2[m]", "0.3[m]", RADIUS_ID),
                                       patch(VALID_SOURCE, "café", "touché", FIRST_ID)],
                              requested_level="represented", budgets={})
        original = self.call(submitted)
        self.assertSuccess(original)
        modified = copy.deepcopy(submitted)
        modified["patches"][0]["replacement"] = "0.4[m]"
        self.assertCode(self.call(modified), "OKL-E-REQUEST-ID")
        reordered = {**submitted, "patches": list(reversed(submitted["patches"]))}
        self.assertCode(self.call(reordered), "OKL-E-REQUEST-ID")
        self.assertEqual(self.call(submitted), original)
        self.assertEqual(self.read(original["source_revision"]),
                         VALID_SOURCE.replace("0.2[m]", "0.3[m]").replace("café", "touché"))

    def test_A05_inspection_is_repeatable_without_advancing_run(self):
        revision = self.create()["source_revision"]
        evaluated = self.evaluate(revision, "1")
        self.assertSuccess(evaluated)
        before = copy.deepcopy(self.service.get_run(PROJECT, evaluated["run_id"]))
        first = self.inspect(revision, selector={"element_id": FIRST_ID}, run_id=evaluated["run_id"],
                             time={"seconds": "0.5", "side": "after"})
        second = self.inspect(revision, selector={"element_id": FIRST_ID}, run_id=evaluated["run_id"],
                              time={"seconds": "0.5", "side": "after"})
        self.assertSuccess(first)
        self.assertSuccess(second)
        self.assertNotEqual(first["request_id"], second["request_id"])
        self.assertEqual(first["result"], second["result"])
        self.assertEqual(len(first["result"]["items"]), 1)
        self.assertEqual(first["result"]["items"][0]["state"]["position_m"], [0.5, 2, 0])
        self.assertEqual(self.service.get_run(PROJECT, evaluated["run_id"]), before)
        self.assertEqual(before["valid_until_seconds"], "1")
        self.assertEqual(before["valid_until_side"], "after")

    def test_A06_continuation_cannot_switch_context(self):
        revision = self.create()["source_revision"]
        run = self.evaluate(revision, "1")["run_id"]
        common = {"source_revision": revision, "selector": {"kind": "object"},
                  "fields": ["identity"], "limit": 1, "run_id": run,
                  "time": {"seconds": "0.5", "side": "after"}, "frame": "world"}
        first = self.call(self.make("inspect", cursor=None, **common))
        self.assertSuccess(first)
        self.assertTrue(first["truncated"])
        cursor = first["next_cursor"]
        self.assertTrue(cursor)
        continued = self.call(self.make("inspect", cursor=cursor, **common))
        self.assertSuccess(continued)
        self.assertIsNone(continued["next_cursor"])
        identities = [item["element_id"] for page in (first, continued) for item in page["result"]["items"]]
        self.assertCountEqual(identities, [FIRST_ID, SECOND_ID])
        newer = self.edit(revision, [patch(VALID_SOURCE, "0.2[m]", "0.3[m]", RADIUS_ID)])["source_revision"]
        another_run = self.call(self.make("reset", source_revision=revision))["run_id"]
        changes = ({"source_revision": newer}, {"run_id": another_run},
                   {"time": {"seconds": "0.75", "side": "after"}},
                   {"time": {"seconds": "0.5", "side": "before"}},
                   {"selector": {"element_id": FIRST_ID}}, {"fields": ["identity", "geometry"]},
                   {"frame": "first.frame"})
        for change in changes:
            with self.subTest(change=change):
                result = self.call(self.make("inspect", cursor=cursor, **{**common, **change}))
                self.assertCode(result, "OKL-E-REVISION")
        # A changed head does not mutate the explicitly pinned old context.
        retained = self.call(self.make("inspect", cursor=cursor, **common))
        self.assertSuccess(retained)
        self.assertEqual(retained["result"]["items"], continued["result"]["items"])
        latest_query = {"source_revision": revision, "selector": {"kind": "object"},
                        "fields": ["state"], "limit": 1, "run_id": run}
        latest = self.call(self.make("inspect", **latest_query))
        self.assertSuccess(latest)
        self.assertTrue(latest["next_cursor"])
        self.assertSuccess(self.evaluate(revision, "1.5", run))
        # An omitted time initially resolves to the run's current sample. A
        # later continuation cannot silently reinterpret it as a newer sample.
        moved = self.call(self.make("inspect", cursor=latest["next_cursor"], **latest_query))
        self.assertCode(moved, "OKL-E-REVISION")

    def test_A07_requested_support_is_not_silently_downgraded(self):
        case = next(c for c in load_manifest()["cases"] if c["id"] == "N25")
        source = materialize(case)
        revision = self.create(source)["source_revision"]
        result = self.call(self.make("validate", source_revision=revision,
                                    requested_level="evaluated", budgets={}))
        self.assertCode(result, "OKL-E-CAPABILITY-UNSUPPORTED")
        self.assertTrue(any(d["category"] == "unsupported" for d in result["diagnostics"]))
        self.assertNotEqual(result["achieved_level"], "evaluated")
        self.assertEqual(result["accepted_revision"], revision)
        self.assertEqual(self.read(revision), source)

    def test_A08_cancel_after_commit_reports_accepted_result(self):
        revision = self.create()["source_revision"]
        original = self.edit(revision, [patch(VALID_SOURCE, "0.2[m]", "0.3[m]", RADIUS_ID)])
        self.assertSuccess(original)
        cancelled = self.call(self.make("cancel", target_request_id=original["request_id"]))
        self.assertSuccess(cancelled)
        self.assertEqual(cancelled["result"]["target_status"], "succeeded")
        self.assertEqual(cancelled["result"]["disposition"], "already_completed")
        self.assertEqual(cancelled["result"]["target"], original)
        self.assertEqual(self.read(original["accepted_revision"]), VALID_SOURCE.replace("0.2[m]", "0.3[m]"))

    def test_A09_expired_result_retains_unknown_outcome_tombstone(self):
        submitted = self.make("create", filename="service.ok", source=VALID_SOURCE,
                              expected_revision=None, requested_level="evaluated", budgets={})
        original = self.call(submitted)
        self.assertSuccess(original)
        run_before = self.service.get_run(PROJECT, original["run_id"])
        self.assertTrue(self.service.expire_result(PROJECT, submitted["request_id"]))
        self.reopen()
        status = self.call(self.make("status", target_request_id=submitted["request_id"]))
        self.assertSuccess(status)
        self.assertEqual(status["result"]["target_status"], "unknown_outcome")
        self.assertEqual(status["result"]["target"]["status"], "unknown_outcome")
        retry = self.call(submitted)
        self.assertEqual(retry["status"], "unknown_outcome")
        self.assertFalse(self.service.work_next())
        self.assertEqual(self.service.get_run(PROJECT, original["run_id"]), run_before)
        self.assertEqual(self.read(original["source_revision"]), VALID_SOURCE)
        changed = {**submitted, "requested_level": "represented"}
        self.assertCode(self.call(changed), "OKL-E-REQUEST-ID")

    def test_A10_rotated_velocity_keeps_world_measurement_frame(self):
        revision = self.create(FRAME_SOURCE)["source_revision"]
        evaluated = self.evaluate(revision, "1")
        self.assertSuccess(evaluated)
        inspected = self.inspect(revision, selector={"element_id": SECOND_ID}, fields=["state"],
                                 run_id=evaluated["run_id"], time={"seconds": "0.5", "side": "after"},
                                 frame="first.frame")
        self.assertSuccess(inspected)
        self.assertEqual(len(inspected["result"]["items"]), 1)
        state = inspected["result"]["items"][0]["state"]
        self.assertEqual(state["velocity_measured_in"], "world")
        self.assertEqual(state["velocity_expressed_in"], "first.frame")
        self.assertLessEqual(max(abs(a-b) for a,b in zip(state["velocity_m_per_s"], [0, -2, 0])), 1e-9)
        self.assertLessEqual(max(abs(a-b) for a,b in zip(state["position_m"], [0, -2.5, 0])), 1e-9)

    def test_queued_cancellation_prevents_a_real_candidate_acceptance(self):
        submitted = self.make("create", filename="service.ok", source=VALID_SOURCE,
                              expected_revision=None, requested_level="represented", budgets={})
        receipt = self.service.submit(submitted)
        self.assertEqual(receipt["status"], "queued")
        result = self.call(self.make("cancel", target_request_id=submitted["request_id"]))
        self.assertSuccess(result)
        self.assertEqual(result["result"]["target_status"], "cancelled")
        self.reopen()
        self.assertEqual(self.call(submitted)["status"], "cancelled")
        self.assertFalse(self.service.work_next())
        # A fresh create can still be accepted, proving the cancelled one did
        # not create a hidden accepted head.
        self.create()

    def test_two_queued_edits_recheck_head_before_acceptance(self):
        revision = self.create()["source_revision"]
        first = self.make("edit", expected_revision=revision,
                          patches=[patch(VALID_SOURCE, "0.2[m]", "0.3[m]", RADIUS_ID)],
                          requested_level="represented", budgets={})
        second = self.make("edit", expected_revision=revision,
                           patches=[patch(VALID_SOURCE, "0.2[m]", "0.4[m]", RADIUS_ID)],
                           requested_level="represented", budgets={})
        self.assertEqual(self.service.submit(first)["status"], "queued")
        peer = AgentService(self.store_path)
        try:
            self.assertEqual(peer.submit(second)["status"], "queued")
            self.assertTrue(self.service.work_next())
            self.assertTrue(peer.work_next())
            accepted = self.call(first)
            stale = self.call(second)
            self.assertSuccess(accepted)
            self.assertCode(stale, "OKL-E-REVISION")
            self.assertEqual(stale["accepted_revision"], accepted["source_revision"])
        finally:
            peer.close()

    def test_retry_is_durable_across_an_independent_python_process(self):
        submitted = self.make("create", filename="service.ok", source=VALID_SOURCE,
                              expected_revision=None, requested_level="evaluated", budgets={})
        original = self.call(submitted)
        self.assertSuccess(original)
        filename = Path(self.temporary.name) / "request.json"
        filename.write_text(json.dumps(submitted), encoding="utf-8")
        code = """import json,sys
from pathlib import Path
from ontokin.agent import AgentService
service=AgentService(Path(sys.argv[1]))
try:
    print(json.dumps(service.handle(json.loads(Path(sys.argv[2]).read_text()),wait=True),allow_nan=False))
finally:
    service.close()
"""
        process = subprocess.run([sys.executable, "-c", code, str(self.store_path), str(filename)],
                                 cwd=ROOT, capture_output=True, text=True, timeout=15)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(json.loads(process.stdout), original)
        self.assertFalse(self.service.work_next())

    def test_protocol_failures_without_a_snapshot_do_not_invent_diagnostics(self):
        malformed = [None, [], {}, {"schema_version": "other", "project_id": PROJECT,
                                   "request_id": "bad-version", "operation": "discover"},
                     self.make("not-an-operation")]
        for submitted in malformed:
            with self.subTest(request=submitted):
                result = self.service.handle(submitted, wait=True)
                self.assertEnvelope(result)
                self.assertEqual(result["status"], "rejected", result)
                self.assertEqual(result["diagnostics"], [])
                self.assertIsNotNone(result["protocol_error"])
                self.assertIsNone(result["source_revision"])
        # An unknown identity is a valid status query, with no invented target
        # execution or source diagnostics; its outer operation still succeeds.
        unknown = self.call(self.make("status", target_request_id="never-seen"))
        self.assertSuccess(unknown)
        self.assertEqual(unknown["result"]["target_status"], "unknown_outcome")
        self.assertEqual(unknown["result"]["disposition"], "unknown_identity")
        target = unknown["result"]["target"]
        self.assertEnvelope(target)
        self.assertEqual(target["diagnostics"], [])
        self.assertIsNone(target["source_revision"])

    def test_running_cancellation_wins_before_a_prepared_candidate_commits(self):
        revision = self.create()["source_revision"]
        submitted = self.make("edit", expected_revision=revision,
                              patches=[patch(VALID_SOURCE, "0.2[m]", "0.3[m]", RADIUS_ID)],
                              requested_level="evaluated", budgets={})
        self.assertEqual(self.service.submit(submitted)["status"], "queued")
        with self.prepared_worker() as worker:
            running = self.call(self.make("status", target_request_id=submitted["request_id"]))
            self.assertEqual(running["result"]["target_status"], "running")
            cancel = self.call(self.make("cancel", target_request_id=submitted["request_id"]))
            self.assertEqual(cancel["result"]["disposition"], "cancellation_requested")
            self.assertEqual(cancel["result"]["target_status"], "running")
            worker.stdin.write("continue\n")
            worker.stdin.flush()
            worker.wait(timeout=10)
            self.assertEqual(worker.returncode, 0, worker.stderr.read())
        terminal = self.call(submitted)
        self.assertEqual(terminal["status"], "cancelled", terminal)
        self.assertEqual(terminal["accepted_revision"], revision)
        self.assertIsNone(terminal["run_id"])
        self.assertIsNone(terminal["result"])
        self.assertIn("0.3[m]", self.read(terminal["source_revision"]))
        self.assertCode(self.evaluate(terminal["source_revision"], "0"), "OKL-E-REVISION")
        self.assertSuccess(self.edit(revision, [patch(VALID_SOURCE, "0.2[m]", "0.4[m]", RADIUS_ID)]))

    def test_malformed_payload_boundaries_always_return_encodable_protocol_errors(self):
        nested = []
        for _ in range(1500):
            nested = [nested]
        valid_inspect = self.make("inspect", source_revision="missing", selector={}, fields=["identity"], limit=1)
        valid_create = self.make("create", filename="source.ok", source=VALID_SOURCE,
                                 expected_revision=None, requested_level="represented")
        cases = [
            ("empty request identity", request("status", "", target_request_id="missing")),
            ("empty project identity", request("status", "empty-project", project_id="", target_request_id="missing")),
            ("invalid Unicode identity", request("status", "invalid-unicode", project_id="\ud800", target_request_id="missing")),
            ("list operation", self.make(["inspect"])),
            ("object operation", self.make({"name": "inspect"})),
            ("list requested stage", {**valid_create, "request_id": "bad-stage-list", "requested_level": ["represented"]}),
            ("object requested stage", {**valid_create, "request_id": "bad-stage-object", "requested_level": {"name": "represented"}}),
            ("list revision", {**valid_inspect, "request_id": "bad-revision", "source_revision": []}),
            ("malformed field group", {**valid_inspect, "request_id": "bad-fields", "fields": [{}]}),
            ("missing field groups", {**valid_inspect, "request_id": "null-fields", "fields": None}),
            ("empty catalog search", self.make("discover", profile="core-0.1", limit=1, filter="")),
            ("unknown catalog filter", self.make("discover", profile="core-0.1", limit=1, filter={"unknown": "kind"})),
            ("invalid catalog filter value", self.make("discover", profile="core-0.1", limit=1, filter={"kind": []})),
            ("deep JSON structure", self.make("discover", profile="core-0.1", limit=1, filter={"nested": nested})),
            ("huge finite numeric option", self.make("export", source_revision="missing", destination="ontokin.glb/0.1",
                                                     options={"position_tolerance_m": 10 ** 400})),
            ("non-JSON source bytes", {**valid_create, "request_id": "raw-bytes", "source": b"\xff"}),
            ("non-UTF8 source string", {**valid_create, "request_id": "surrogate-source", "source": "\ud800"}),
        ]
        for label, submitted in cases:
            with self.subTest(boundary=label):
                result = self.service.handle(submitted)
                self.assertEnvelope(result)
                self.assertEqual(result["status"], "rejected", result)
                self.assertIsNotNone(result["protocol_error"])
                self.assertEqual(result["diagnostics"], [])
                self.assertIsNone(result["accepted_revision"])
                self.assertIsNone(result["achieved_level"])
        self.create()

    def test_dead_worker_is_fenced_and_live_worker_is_never_stolen(self):
        revision = self.create()["source_revision"]
        initial = self.call(self.make("reset", source_revision=revision))
        before = self.service.get_run(PROJECT, initial["run_id"])
        submitted = self.make("evaluate", source_revision=revision, run_id=initial["run_id"],
                              until_seconds="0.5", budgets={})
        self.assertEqual(self.service.submit(submitted)["status"], "queued")
        with self.prepared_worker() as worker:
            peer = AgentService(self.store_path)
            try:
                observed = peer.handle(self.make("status", target_request_id=submitted["request_id"]))
                self.assertEnvelope(observed)
                self.assertEqual(observed["result"]["target_status"], "running")
                self.assertFalse(peer.work_next(), "A live process must retain exclusive work ownership")
                self.assertEqual(peer.get_run(PROJECT, initial["run_id"]), before)
            finally:
                peer.close()
            worker.kill()
            worker.wait(timeout=5)
        self.reopen()
        status = self.call(self.make("status", target_request_id=submitted["request_id"]))
        self.assertEqual(status["result"]["target_status"], "unknown_outcome")
        self.assertEqual(self.call(submitted)["status"], "unknown_outcome")
        self.assertFalse(self.service.work_next())
        self.assertEqual(self.service.get_run(PROJECT, initial["run_id"]), before)
        changed_payload = {**submitted, "until_seconds": "1"}
        self.assertCode(self.call(changed_payload), "OKL-E-REQUEST-ID")
        reconciled = self.evaluate(revision, "0.5", initial["run_id"])
        self.assertSuccess(reconciled)
        self.assertEqual(self.service.get_run(PROJECT, initial["run_id"])["last_valid_state"]
                         ["objects"]["first"]["position_m"], [0.5, 2, 0])

    def test_engine_change_preserves_old_results_but_cannot_replay_old_runs_or_receipts(self):
        created = self.create()
        revision = created["source_revision"]
        initial = self.evaluate(revision, "0.5")
        before = self.service.get_run(PROJECT, initial["run_id"])
        queued = self.make("evaluate", source_revision=revision, run_id=initial["run_id"],
                           until_seconds="1", budgets={})
        self.assertEqual(self.service.submit(queued)["status"], "queued")
        alternate = copy.deepcopy(self.service.implementation)
        alternate["source_code_sha256"] = "sha256:" + "0" * 64
        self.assertNotEqual(alternate, self.service.implementation)
        # A controlled engine identity changes no parsing or evaluator behavior.
        with instrument("ontokin.agent.implementation_identity", return_value=alternate):
            peer = AgentService(self.store_path)
        try:
            self.assertTrue(peer.work_next())
            fenced = peer.handle(queued)
            self.assertEnvelope(fenced)
            self.assertCode(fenced, "OKA-E-ENGINE")
            self.assertEqual(peer.get_run(PROJECT, initial["run_id"]), before)
            mismatch = peer.handle(self.make("evaluate", source_revision=revision, run_id=initial["run_id"],
                                             until_seconds="1", budgets={}))
            self.assertEnvelope(mismatch)
            self.assertCode(mismatch, "OKL-E-SAMPLE")
            original_request = next(record["request"] for record in self.evidence
                                    if record["response"]["request_id"] == created["request_id"])
            self.assertEqual(peer.handle(original_request), created)
            self.assertEqual(peer.read_source(PROJECT, revision).text, VALID_SOURCE)
            fresh = peer.handle(self.make("reset", source_revision=revision))
            self.assertEnvelope(fresh)
            self.assertSuccess(fresh)
            self.assertNotEqual(fresh["run_id"], initial["run_id"])
            self.assertEqual(peer.get_run(PROJECT, fresh["run_id"])["implementation"], alternate)
        finally:
            peer.close()

    def test_utf8_edits_use_original_bytes_and_preserve_unselected_comments(self):
        revision = self.create()["source_revision"]
        change = patch(VALID_SOURCE, "café", "touché", FIRST_ID)
        # A preceding multibyte character is needed to distinguish a byte
        # offset from a character index in the patch selected below.
        marker = patch(VALID_SOURCE, "🟣", "🟢", FIRST_ID)
        self.assertGreater(marker["start_byte"], VALID_SOURCE.index("🟣"))
        inside_character = marker.copy()
        inside_character["start_byte"] += 1
        self.assertCode(self.edit(revision, [inside_character]), "OKL-E-REVISION")
        result = self.edit(revision, [change, marker])
        self.assertSuccess(result)
        expected = VALID_SOURCE.replace("café", "touché").replace("🟣", "🟢")
        self.assertEqual(self.read(result["source_revision"]), expected)

    def test_patch_mismatch_overlap_and_wrong_element_never_partially_apply(self):
        revision = self.create()["source_revision"]
        valid = patch(VALID_SOURCE, "0.2[m]", "0.3[m]", RADIUS_ID)
        wrong_text = {**valid, "expected_text": "0.25[m]"}
        wrong_scope = {**valid, "element_id": FIRST_ID}
        insertion = {"element_id": FIRST_ID, "start_byte": VALID_SOURCE.encode().index(b"// caf"),
                     "end_byte": VALID_SOURCE.encode().index(b"// caf"),
                     "expected_text": "", "replacement": " "}
        for changes in ([wrong_text], [wrong_scope], [valid, valid], [insertion, insertion]):
            with self.subTest(patches=changes):
                self.assertCode(self.edit(revision, changes), "OKL-E-REVISION")
                self.assertEqual(self.read(revision), VALID_SOURCE)

    def test_rejected_first_create_keeps_source_for_an_explicit_repair(self):
        invalid = VALID_SOURCE.replace("0.2[m]", "1[kg]")
        failed = self.call(self.make("create", filename="service.ok", source=invalid,
                                    expected_revision=None, requested_level="represented", budgets={}))
        self.assertCode(failed, "OKL-E-UNIT")
        self.assertIsNone(failed["accepted_revision"])
        self.assertEqual(self.read(failed["source_revision"]), invalid)
        inspected = self.inspect(failed["source_revision"], selector={"kind": "module"}, fields=["source"])
        self.assertSuccess(inspected)
        self.assertEqual(inspected["result"]["source_text"], invalid)
        accepted = self.create()
        self.assertNotEqual(accepted["source_revision"], failed["source_revision"])
        self.assertCode(self.evaluate(failed["source_revision"], "0"), "OKL-E-REVISION")

    def test_syntax_invalid_snapshot_is_retrievable_without_fabricated_identity(self):
        invalid = 'ontokin "0.1";\nmodule Broken @ "broken";\nprofile "core-0.1";\nscene'
        failed = self.call(self.make("create", filename="broken.ok", source=invalid,
                                    expected_revision=None, requested_level="represented", budgets={}))
        self.assertCode(failed, "OKL-E-SYNTAX")
        retrieved = self.inspect(failed["source_revision"], selector={"kind": "module"}, fields=["source"])
        self.assertSuccess(retrieved)
        self.assertEqual(retrieved["result"]["source_text"], invalid)
        self.assertFalse(retrieved["result"]["index_complete"])
        self.assertEqual(self.read(failed["source_revision"]), invalid)

    def test_single_instance_override_cannot_edit_a_shared_default(self):
        revision = self.create()["source_revision"]
        inherited_id = FIRST_ID + ["radius"]
        denied = self.edit(revision, [patch(VALID_SOURCE, "0.2[m]", "0.4[m]", inherited_id)])
        self.assertCode(denied, "OKL-E-REVISION")
        needle = 'object first @ "first": Ball {'
        override = patch(VALID_SOURCE, needle, needle + "\n        radius = 0.4[m];", FIRST_ID)
        changed = self.edit(revision, [override], level="evaluated")
        self.assertSuccess(changed)
        source = self.read(changed["source_revision"])
        self.assertEqual(source, VALID_SOURCE.replace(needle, needle + "\n        radius = 0.4[m];"))
        objects = self.service.get_run(PROJECT, changed["run_id"])["last_valid_state"]["objects"]
        self.assertEqual(objects["first"]["geometry"]["radius"], 0.4)
        self.assertEqual(objects["second"]["geometry"]["radius"], 0.2)

    def test_reset_is_before_zero_and_historical_accepted_runs_stay_pinned(self):
        revision = self.create()["source_revision"]
        reset = self.call(self.make("reset", source_revision=revision))
        self.assertSuccess(reset)
        initial = self.service.get_run(PROJECT, reset["run_id"])
        self.assertEqual((initial["valid_until_seconds"], initial["valid_until_side"]), ("0", "before"))
        self.assertEqual(initial["last_valid_state"]["actions"]["travel"]["status"], "pending")
        after = self.evaluate(revision, "0", reset["run_id"])
        self.assertSuccess(after)
        at_zero = self.service.get_run(PROJECT, reset["run_id"])
        self.assertEqual(at_zero["valid_until_side"], "after")
        self.assertEqual(at_zero["last_valid_state"]["actions"]["travel"]["status"], "running")
        newer = self.edit(revision, [patch(VALID_SOURCE, "0.2[m]", "0.3[m]", RADIUS_ID)])["source_revision"]
        continued = self.evaluate(revision, "0.5", reset["run_id"])
        self.assertSuccess(continued)
        self.assertEqual(continued["source_revision"], revision)
        self.assertEqual(continued["accepted_revision"], newer)
        old = self.service.get_run(PROJECT, reset["run_id"])
        self.assertEqual(old["source_revision"], revision)
        self.assertEqual(old["last_valid_state"]["objects"]["first"]["position_m"], [0.5, 2, 0])
        fresh_historical = self.call(self.make("reset", source_revision=revision))
        self.assertSuccess(fresh_historical)
        self.assertNotEqual(fresh_historical["run_id"], reset["run_id"])

    def test_short_evaluation_retains_valid_prefix_before_a_later_failure(self):
        revision = self.create(FUTURE_FAILURE_SOURCE, level="constructed")["source_revision"]
        earlier = self.evaluate(revision, "0.5")
        self.assertSuccess(earlier)
        failed = self.evaluate(revision, "1", earlier["run_id"])
        self.assertCode(failed, "OKL-E-ACTION-STATE")
        retained = self.service.get_run(PROJECT, earlier["run_id"])
        self.assertEqual(retained["status"], "failed")
        self.assertEqual((retained["valid_until_seconds"], retained["valid_until_side"]), ("1", "before"))
        self.assertEqual(retained["last_valid_state"]["objects"]["first"]["position_m"], [1, 2, 0])
        inspected = self.inspect(revision, selector={"element_id": FIRST_ID}, fields=["state"],
                                 run_id=earlier["run_id"], time={"seconds": "1", "side": "before"})
        self.assertSuccess(inspected)
        unavailable = self.inspect(revision, selector={"element_id": FIRST_ID}, fields=["state"],
                                   run_id=earlier["run_id"], time={"seconds": "1", "side": "after"})
        self.assertCode(unavailable, "OKL-E-SAMPLE")
        self.assertEqual(self.service.get_run(PROJECT, earlier["run_id"]), retained)

    def test_source_only_inspection_and_invalid_run_requests_do_not_invent_state(self):
        revision = self.create()["source_revision"]
        source_only = self.inspect(revision, selector={"element_id": FIRST_ID}, fields=["state"])
        self.assertSuccess(source_only)
        self.assertEqual(source_only["result"]["items"][0]["state"], {"available": False, "reason": "run_required"})
        current = self.evaluate(revision, "1")
        self.assertSuccess(current)
        self.assertCode(self.evaluate(revision, "0.5", current["run_id"]), "OKL-E-SAMPLE")
        self.assertCode(self.evaluate(revision, "1", "nonexistent-run"), "OKL-E-SAMPLE")
        self.assertCode(self.inspect(revision, run_id=current["run_id"],
                                    time={"seconds": "1.5", "side": "after"}), "OKL-E-SAMPLE")

    def test_requested_object_budget_is_enforced_without_losing_the_head(self):
        revision = self.create()["source_revision"]
        result = self.edit(revision, [patch(VALID_SOURCE, "0.2[m]", "0.3[m]", RADIUS_ID)],
                           budgets={"max_objects": 1})
        self.assertCode(result, "OKL-E-RESOURCE")
        self.assertTrue(any(d["category"] == "resource_limit" for d in result["diagnostics"]))
        self.assertEqual(result["accepted_revision"], revision)
        self.assertEqual(self.read(revision), VALID_SOURCE)

    def test_explicit_delivery_produces_retrievable_revision_bound_glb_bytes(self):
        created = self.call(self.make("create", filename="service.ok", source=VALID_SOURCE,
                                     expected_revision=None, requested_level="delivered",
                                     destination="ontokin.glb/0.1", options={"helpers": False}, budgets={}))
        self.assertSuccess(created)
        self.assertEqual(created["achieved_level"], "delivered")
        revision, artifact = created["source_revision"], created["result"]["artifact_id"]
        self.assertEqual(self.read(revision), VALID_SOURCE)
        chunks, offset, total = [], 0, None
        while offset is not None:
            chunk = self.call(self.make("artifact", artifact_id=artifact, offset=offset,
                                        max_bytes=256 if offset == 0 else 65536))
            self.assertSuccess(chunk)
            record = chunk["result"]
            self.assertEqual(record["artifact_id"], artifact)
            self.assertEqual(record["source_revision"], revision)
            self.assertEqual(record["offset"], offset)
            content = base64.b64decode(record["data_base64"], validate=True)
            self.assertLessEqual(len(content), 256 if offset == 0 else 65536)
            self.assertTrue(content)
            total = record["total_bytes"] if total is None else total
            self.assertEqual(record["total_bytes"], total)
            self.assertIn(record["next_offset"], (None, offset + len(content)))
            chunks.append(content)
            offset = record["next_offset"]
        data = b"".join(chunks)
        self.assertEqual(len(data), total)
        self.assertEqual(record["sha256"], "sha256:" + hashlib.sha256(data).hexdigest())
        decoded = DecodedGLB(data)
        self.assertEqual(decoded.document["extras"]["ontokin"]["source"]["revision"], revision)
        self.assertEqual(decoded.node_pose("first", 0.5)["translation"], (0.5, 2, 0))
        self.reopen()
        retained = self.call(self.make("artifact", artifact_id=artifact, offset=0, max_bytes=256))
        self.assertEqual(base64.b64decode(retained["result"]["data_base64"]), data[:256])

    def test_failed_actual_delivery_cannot_accept_an_otherwise_valid_edit(self):
        revision = self.create()["source_revision"]
        changed = patch(VALID_SOURCE, "vec3(0[m], 2[m], 0[m])",
                        "vec3(10000000001[m], 2[m], 0[m])", FIRST_ID)
        result = self.edit(revision, [changed], level="delivered", destination="ontokin.glb/0.1",
                           options={"helpers": False})
        self.assertCode(result, "OKL-E-NUMERIC")
        self.assertEqual(result["accepted_revision"], revision)
        self.assertEqual(self.read(revision), VALID_SOURCE)
        self.assertIn("10000000001[m]", self.read(result["source_revision"]))

    def test_schemas_cover_manifest_cases_and_reject_unbounded_or_ambiguous_requests(self):
        self.assertEqual(set(CASE_TESTS), {c["id"] for c in load_manifest()["agent_contract_checks"]})
        valid = self.make("inspect", source_revision="revision", selector={"kind": "object"},
                          fields=["identity"], limit=1000)
        self.assertEqual(schema_errors(valid, REQUEST_SCHEMA), [])
        catalog = self.make("discover", profile="core-0.1", limit=1, filter={})
        self.assertEqual(schema_errors(catalog, REQUEST_SCHEMA), [])
        self.assertEqual(schema_errors({**catalog, "filter": {"kind": "type", "name": "Length"}}, REQUEST_SCHEMA), [])
        for invalid_filter in ("", {"unknown": "kind"}, {"kind": []}, {"name": ""}):
            self.assertTrue(schema_errors({**catalog, "filter": invalid_filter}, REQUEST_SCHEMA))
        invalid = [{**valid, "limit": 1001}, {**valid, "limit": True},
                   {**valid, "fields": ["identity", "identity"]}, {**valid, "surprise": True},
                   {**valid, "time": {"seconds": "1e-3", "side": "after"}},
                   {**valid, "budgets": {"max_objects": 1001}}]
        for value in invalid:
            with self.subTest(request=value):
                self.assertTrue(schema_errors(value, REQUEST_SCHEMA))


if __name__ == "__main__":
    unittest.main()
