"""Actual source-only Agent04 repair, influence history and publication bounds."""
import base64
import copy
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch as instrument

from ontokin.bundle import load_bundle, load_file_manifest
from ontokin.json_limits import measure_json
from ontokin.program_agent import ProgramAgentService
from tools.impulse_oracles import CASES, FIXTURES


PROTOCOL = "ontokin.agent/0.4"
TARGET = "ontokin.glb/0.4"
BALL = ["impulse-demo", "demo", "ball"]
RACK = ["impulse-demo", "demo", "rack"]
FIRST = RACK + ["props", "first"]
SECOND = RACK + ["props", "second"]


def source_case(name):
    program = load_file_manifest(FIXTURES / CASES[name]["file_manifest"])
    if program.program_revision != CASES[name]["program_revision"]:
        raise AssertionError("The adopted source corpus changed")
    return program


def minimal_patch(before, after, identity):
    """One contiguous exact UTF-8 difference, independent of compiler offsets."""
    a, b = before.entry.raw, after.entry.raw
    start = 0
    while start < min(len(a), len(b)) and a[start] == b[start]:
        start += 1
    end_a, end_b = len(a), len(b)
    while end_a > start and end_b > start and a[end_a-1] == b[end_b-1]:
        end_a -= 1; end_b -= 1
    return {"source_id": "entry", "source_revision": before.entry.revision,
            "element_id": identity, "start_byte": start, "end_byte": end_a,
            "expected_text": a[start:end_a].decode("utf-8"),
            "replacement": b[start:end_b].decode("utf-8")}


class _CommitGate(ProgramAgentService):
    def __init__(self, path):
        self.ready = threading.Event(); self.release = threading.Event()
        self.prepared = None; self.errors = []
        super().__init__(path, protocol=PROTOCOL)

    def _finish(self, task):
        self.prepared = (copy.deepcopy(task.response), task.accept,
                         task.run is not None, task.artifact is not None)
        self.ready.set()
        if not self.release.wait(15):
            raise TimeoutError("Test did not release the actual publication transaction")
        super()._finish(task)

    def work(self):
        try:
            if not self.work_next(): raise AssertionError("No request was claimed")
        except BaseException as error:
            self.errors.append(error); self.ready.set()


class ImpulseAgentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="ontokin-impulse-agent-")
        self.path = Path(self.tmp.name)
        self.service = ProgramAgentService(self.path, protocol=PROTOCOL)
        self.sequence = 0

    def tearDown(self):
        self.service.close(); self.tmp.cleanup()

    def request(self, operation, *, project="impulse", **fields):
        self.sequence += 1
        return dict(schema_version=PROTOCOL, project_id=project,
                    request_id=f"impulse-{self.sequence}", operation=operation, **fields)

    def send(self, operation, **fields):
        response = self.service.handle(self.request(operation, **fields))
        self.assertEqual(response["schema_version"], PROTOCOL)
        self.assertEqual(response["operation"], operation)
        return response

    def success(self, response):
        self.assertEqual(response["status"], "succeeded", response)
        self.assertIsNone(response["protocol_error"], response)
        return response

    def code(self, response, code):
        self.assertIn(response["status"], ("failed", "rejected"), response)
        codes = [d["code"] for d in response["diagnostics"]]
        if response["protocol_error"]: codes.append(response["protocol_error"]["code"])
        self.assertIn(code, codes, response)
        return response

    def create(self, name, *, project="impulse", level="constructed"):
        program = source_case(name)
        response = self.success(self.send("create", project=project, bundle=program.to_payload(),
            expected_program_revision=None, requested_level=level))
        self.assertEqual(response["accepted_program_revision"], program.program_revision)
        return program, response

    def inspect(self, program, path, *, run=None, time="2", side="after", fields=None, **extra):
        arguments = {} if run is None else dict(run_id=run, time={"seconds": time, "side": side})
        response = self.success(self.send("inspect", program_revision=program.program_revision,
            selector={"path": path}, fields=fields or ["identity", "source", "geometry", "state"],
            limit=1, **arguments, **extra))
        self.assertEqual(response["result"]["total"], 1)
        return response["result"]["items"][0]

    def evaluate(self, program, *, project="impulse"):
        return self.success(self.send("evaluate", project=project, program_revision=program.program_revision,
                                      run_id=None, until_seconds="2"))

    def effects(self):
        with self.service._store.connection() as db:
            return {t: db.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
                    for t in ("runs", "artifacts")}

    def test_frozen_mass_and_radius_repairs_are_single_occurrence_source_edits(self):
        for target, speed, spin, inertia in (("P09", .5, 2.5, .4), ("P10", 1., 1.25, .8)):
            with self.subTest(target=target):
                project = target.lower()
                original, _ = self.create("P08", project=project)
                expected = source_case(target)
                initial_run = self.evaluate(original, project=project)
                before = self.inspect(original, 'rack.props["second"]', run=initial_run["run_id"], project=project)
                source = self.inspect(original, "rack", fields=["source"], project=project)["source"]
                patch = minimal_patch(original, expected, RACK)
                self.assertEqual(patch["expected_text"], "2" if target == "P09" else "0.5")
                self.assertEqual(patch["replacement"], "4" if target == "P09" else "1")
                self.assertTrue(any(s["start_byte"] <= patch["start_byte"] < patch["end_byte"] <= s["end_byte"]
                                    for s in source["writable_spans"]))
                edited = self.success(self.send("edit", project=project, expected_program_revision=original.program_revision,
                                               patches=[patch], requested_level="evaluated"))
                self.assertEqual(edited["program_revision"], expected.program_revision)
                self.assertEqual(self.service.read_program(project, expected.program_revision).to_payload(), expected.to_payload())
                self.assertEqual(original.modules, expected.modules)
                first = self.inspect(expected, 'rack.props["first"]', run=edited["run_id"], project=project)
                second = self.inspect(expected, 'rack.props["second"]', run=edited["run_id"], project=project)
                self.assertEqual(first["element_id"], FIRST); self.assertEqual(second["element_id"], SECOND)
                self.assertEqual(first["state"]["velocity_m_per_s"], [0., speed, 0.])
                self.assertEqual(first["state"]["angular_velocity_rad_per_s"], [0., 0., spin])
                self.assertEqual(first["state"]["inertia_kg_m2"], inertia)
                for key in ("position_m", "orientation_wxyz", "velocity_m_per_s", "angular_velocity_rad_per_s", "physical"):
                    self.assertEqual(second["state"][key], before["state"][key])
                self.assertEqual(second["geometry"], before["geometry"])
                self.assertEqual(first["geometry"], self.inspect(original, 'rack.props["first"]', project=project)["geometry"])
                self.assertEqual(second["state"]["impulses"]["last_applications"][0]["source_location"]["source_revision"], expected.entry.revision)
                historical = self.inspect(original, 'rack.props["first"]', run=initial_run["run_id"], project=project)
                self.assertEqual(historical["state"]["angular_velocity_rad_per_s"], [0., 0., 5.])
                self.code(self.send("edit", project=project, expected_program_revision=original.program_revision,
                                    patches=[patch], requested_level="constructed"), "OKL-E-REVISION")

    def test_rejected_evaluated_candidate_keeps_head_rollback_retry_and_history(self):
        accepted, _ = self.create("P01")
        invalid = source_case("N19")
        candidate_request = self.request("edit", expected_program_revision=accepted.program_revision,
            patches=[minimal_patch(accepted, invalid, ["sources", "entry"])], requested_level="evaluated")
        rejected = self.code(self.service.handle(candidate_request), "OKL-E-MOTION-MODE")
        self.assertEqual(rejected["program_revision"], invalid.program_revision)
        self.assertEqual(rejected["accepted_program_revision"], accepted.program_revision)
        self.assertEqual(self.service.handle(candidate_request), rejected)
        self.code(self.service.handle({**candidate_request, "requested_level": "constructed"}), "OKL-E-REQUEST-ID")
        run = self.service.get_run("impulse", rejected["run_id"])
        self.assertTrue(run["candidate_only"]); self.assertEqual(run["status"], "failed")
        self.assertEqual((run["valid_until_seconds"], run["valid_until_side"]), ("1", "before"))
        ball = run["last_valid_state"]["objects"]["ball"]
        self.assertEqual(ball["velocity_m_per_s"], [0., 0., 0.])
        self.assertEqual(ball["impulses"], {"applied_count": 0, "last_application_time_seconds": None, "last_applications": []})
        diagnostic = next(d for d in rejected["diagnostics"] if d["code"] == "OKL-E-MOTION-MODE")
        self.assertEqual(diagnostic["program_revision"], invalid.program_revision)
        self.assertEqual(diagnostic["source_revision"], invalid.entry.revision)
        self.assertEqual(diagnostic["details"]["sequence_index"], 1)
        statement = CASES["N19"]["source_impulse_statements"][1]["source_location"]
        self.assertEqual(diagnostic["primary"]["start_byte"], statement["start_byte"])
        self.assertEqual(diagnostic["primary"]["end_byte"], statement["end_byte"])
        for operation, fields in (("surface.mesh_page", dict(element_id=BALL, count=1)),
                                  ("evaluate", dict(run_id=None, until_seconds="2")),
                                  ("export", dict(destination=TARGET))):
            self.code(self.send(operation, program_revision=invalid.program_revision, **fields), "OKL-E-REVISION")
        self.assertEqual(self.service.accepted_revision("impulse"), accepted.program_revision)

    def test_mesh_context_retains_surface_capability_and_binds_all_impulse_identity(self):
        program, _ = self.create("P02")
        shape = self.inspect(program, "ball", fields=["geometry", "support"])
        self.assertEqual(shape["geometry"]["surface"]["profile"], "surface-0.1")
        self.assertEqual(shape["support"]["profile"], "impulse-0.1")
        self.assertEqual(shape["support"]["named_destination"], TARGET)
        first = self.success(self.send("surface.mesh_page", program_revision=program.program_revision, element_id=BALL, count=7))
        page = first["result"]
        self.assertEqual(page["profile"], "surface-0.1")
        self.assertNotIn("entry_profile", page)
        decoded = json.loads(base64.urlsafe_b64decode(first["next_cursor"] + "=" * (-len(first["next_cursor"]) % 4))[32:])
        context = decoded["context"]
        self.assertEqual(context["protocol"], PROTOCOL)
        self.assertEqual(context["entry_profile"], "impulse-0.1")
        self.assertEqual(context["implementation"], self.service.implementation)
        variants = {"program_revision": "sha256:" + "f" * 64, "element_id": FIRST,
                    "region": "paint", "protocol": "ontokin.agent/0.3", "entry_profile": "surface-0.1",
                    "implementation": {**self.service.implementation, "version": "stale"}}
        for field, value in variants.items():
            with self.subTest(field=field):
                token = self.service._cursor({**context, field: value}, decoded["offset"])
                self.code(self.send("surface.mesh_page", program_revision=program.program_revision,
                                    element_id=BALL, count=1, cursor=token), "OKL-E-REVISION")
        following = self.success(self.send("surface.mesh_page", program_revision=program.program_revision,
                                          element_id=BALL, count=256, cursor=first["next_cursor"]))
        self.assertEqual(following["result"]["source_triangle_ordinals"], list(range(7, 96)))
        self.assertEqual(following["result"]["geometry_sha256"], page["geometry_sha256"])
        self.assertEqual(self.effects(), {"runs": 0, "artifacts": 0})

    def test_frame_projection_keeps_explicit_impulse_records_byte_equivalent(self):
        program, _ = self.create("P03")
        run = self.evaluate(program)["run_id"]
        world = self.inspect(program, "ball", run=run, frame="world")["state"]
        local = self.inspect(program, "ball", run=run, frame="ball.frame")["state"]
        self.assertNotEqual(world["orientation_wxyz"], local["orientation_wxyz"])
        self.assertEqual(local["position_m"], [0., 0., 0.])
        self.assertEqual(json.dumps(world["impulses"], sort_keys=True), json.dumps(local["impulses"], sort_keys=True))
        record = local["impulses"]["last_applications"][0]
        self.assertEqual(len(record), 13)
        self.assertAlmostEqual(record["lever_arm_world_m"][2], -.5)
        self.assertAlmostEqual(record["angular_impulse_world_n_m_s"][0], 1.)
        self.assertAlmostEqual(record["angular_velocity_after_world_rad_per_s"][0], 5.)

    def test_inspection_final_budget_counts_complete_latest_boundary_records(self):
        program, _ = self.create("P02")
        run = self.evaluate(program)["run_id"]
        fields = dict(program_revision=program.program_revision, run_id=run,
                      selector={"path": "ball"}, fields=["state"], limit=1,
                      time={"seconds": "1", "side": "after"})
        complete = self.success(self.send("inspect", **fields))
        entries = measure_json(complete)["entries"]
        self.assertGreater(entries, measure_json(complete["result"])["entries"])
        prior = self.effects()
        failed = self.code(self.send("inspect", **fields, budgets={"max_value_entries": entries - 1}), "OKA-E-RESOURCE")
        self.assertFalse(failed["protocol_error"]["details"]["effects_committed"])
        self.assertIsNone(failed["result"]); self.assertEqual(self.effects(), prior)
        exact = self.success(self.send("inspect", **fields, budgets={"max_value_entries": entries}))
        self.assertEqual(measure_json(exact)["entries"], entries)
        self.assertEqual(exact["result"], complete["result"])

    def test_final_delivery_budget_rolls_back_impulse_source_run_and_artifact(self):
        original, _ = self.create("P08")
        self.create("P08", project="baseline")
        changed = source_case("P09")
        fields = dict(expected_program_revision=original.program_revision,
                      patches=[minimal_patch(original, changed, RACK)], requested_level="delivered",
                      destination=TARGET, options={"end": "2", "fps": 2, "helpers": False})
        baseline = self.success(self.send("edit", project="baseline", **fields))
        entries = measure_json(baseline)["entries"]
        previous = self.effects(); prepared = []
        execute = self.service._execute
        def observe(task, check):
            execute(task, check)
            prepared.append((task.accept, task.run is not None, task.artifact is not None))
        with instrument.object(self.service, "_execute", side_effect=observe):
            failed = self.code(self.send("edit", **fields, budgets={"max_value_entries": entries-1}), "OKA-E-RESOURCE")
        self.assertEqual(prepared, [(True, True, True)])
        self.assertFalse(failed["protocol_error"]["details"]["effects_committed"])
        self.assertEqual(failed["accepted_program_revision"], original.program_revision)
        self.assertEqual(failed["program_revision"], changed.program_revision)
        self.assertIsNone(failed["run_id"]); self.assertIsNone(failed["result"])
        self.assertEqual(self.effects(), previous)
        self.code(self.send("surface.mesh_page", program_revision=changed.program_revision, element_id=FIRST, count=1), "OKL-E-REVISION")
        exact = self.success(self.send("edit", **fields, budgets={"max_value_entries": entries}))
        self.assertEqual(measure_json(exact)["entries"], entries)
        self.assertEqual(exact["accepted_program_revision"], changed.program_revision)

    def test_cancellation_after_real_impulse_delivery_publishes_no_effects(self):
        original, _ = self.create("P08")
        changed = source_case("P09")
        request = self.request("edit", expected_program_revision=original.program_revision,
            patches=[minimal_patch(original, changed, RACK)], requested_level="delivered",
            destination=TARGET, options={"end": "2", "fps": 2, "helpers": False})
        self.assertEqual(self.service.submit(request)["status"], "queued")
        worker = _CommitGate(self.path)
        thread = threading.Thread(target=worker.work, daemon=True)
        try:
            thread.start(); self.assertTrue(worker.ready.wait(15))
            self.assertEqual(worker.errors, [])
            self.success(worker.prepared[0]); self.assertEqual(worker.prepared[1:], (True, True, True))
            self.success(self.send("cancel", target_request_id=request["request_id"]))
        finally:
            worker.release.set(); thread.join(15); worker.close()
        self.assertFalse(thread.is_alive()); self.assertEqual(worker.errors, [])
        failed = self.service.handle(request)
        self.assertEqual(failed["status"], "cancelled", failed)
        self.assertEqual(failed["accepted_program_revision"], original.program_revision)
        self.assertIsNone(failed["result"]); self.assertIsNone(failed["run_id"])
        self.assertEqual(self.effects(), {"runs": 0, "artifacts": 0})
        self.code(self.send("surface.mesh_page", program_revision=changed.program_revision, element_id=FIRST, count=1), "OKL-E-REVISION")
        retry = self.success(self.service.handle({**request, "request_id": "recovered-delivery"}))
        self.assertEqual(retry["accepted_program_revision"], changed.program_revision)

    def test_run_provenance_rejects_wrong_revision_and_implementation(self):
        program, _ = self.create("P02")
        run = self.evaluate(program)["run_id"]
        fields = dict(program_revision=program.program_revision, run_id=run,
                      selector={"path": "ball"}, fields=["state"], limit=1)
        retained = self.service.get_run("impulse", run)
        self.assertEqual(retained["implementation"], self.service.implementation)
        with instrument.object(self.service, "get_run", return_value={**retained, "program_revision": "sha256:"+"0"*64}):
            self.code(self.send("inspect", **fields), "OKL-E-SAMPLE")
        with instrument.object(self.service, "get_run", return_value={**retained, "implementation": {}}):
            self.code(self.send("inspect", **fields), "OKL-E-SAMPLE")
        self.assertEqual(self.service.get_run("impulse", run), retained)
        self.success(self.send("inspect", **fields))

    def test_huge_finite_evaluation_retains_json_safe_impulse_record(self):
        program, _ = self.create("P12")
        run = self.evaluate(program)["run_id"]
        before = self.inspect(program, "ball", run=run, time="1", side="before")["state"]
        after = self.inspect(program, "ball", run=run, time="1")["state"]
        self.assertEqual(before["velocity_m_per_s"], [-1e308, 0., 0.])
        self.assertEqual(after["velocity_m_per_s"], [1e308, 0., 0.])
        self.assertEqual(after["position_m"], [-1e308, 0., 0.])
        record = after["impulses"]["last_applications"][0]
        self.assertEqual(record["linear_velocity_before_world_m_per_s"], [-1e308, 0., 0.])
        self.assertEqual(record["linear_velocity_after_world_m_per_s"], [1e308, 0., 0.])
        json.dumps(after, allow_nan=False); measure_json(after)
        self.assertEqual(self.inspect(program, "ball", run=run)["state"]["position_m"], [0., 0., 0.])


if __name__ == "__main__":
    unittest.main()
