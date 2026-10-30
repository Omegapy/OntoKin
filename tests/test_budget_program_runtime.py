"""Request-local .7 runtime accounting and source-safe candidate preparation."""
import unittest
from unittest.mock import patch

from ontokin.budget_program_runtime import BudgetProgramRuntime, ExecutionProgramBudget
from ontokin.bundle import ProgramBundle, SourceUnit
from ontokin.construction import ConstructionCompiler
from ontokin.diagnostics import OntoKinError
from ontokin.execution_budget import HostPolicy, SharedExecutionBudget, admit_entry_budget
from ontokin.gltf import export_glb
from ontokin.profile_capabilities import BUDGET_PROFILE
from ontokin.program_bindings import PROGRAM_BINDINGS, PROFILE_BINDINGS
from ontokin.program_runtime import ProgramRuntime, _Budget as LegacyBudget
from ontokin.program_surface import prepare_surface_page
from ontokin.scene import ExportOptions
from tests.test_surface_export import single_source


TEXT = '''ontokin "0.7";
module Workshop @ "workshop";
profile "planar-reach-budget-0.1";
execution { max_operations = 200000; max_elapsed = 60[s]; }
class Carrier @ "carrier-class" {
    public param width @ "width": Length = 1[m];
    geometry = box(vec3(self.width, 2[m], 3[m]));
    physical = no_body();
}
scene Demo @ "demo" {
    duration = 2[s];
    gravity = vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2]);
    object carrier @ "carrier": Carrier {}
}
'''


def source(text=TEXT):
    return ProgramBundle(SourceUnit("entry", "runtime-budget.ok", text.encode("utf-8")))


class RequestContext:
    """Minimal trusted caller for pure operations; it owns no durable state."""

    def __init__(self, *, policy=None, caps=None, callback=None, clock=None):
        self.execution_budget = SharedExecutionBudget(
            policy or HostPolicy(400000, 80000), caps, check=callback, clock=clock)
        self.program_revision = None
        self.admissions = 0

    def admit(self, program):
        if self.program_revision is None:
            admit_entry_budget(program.entry, self.execution_budget)
            self.program_revision = program.program_revision
            self.admissions += 1
        elif self.program_revision != program.program_revision:
            raise OntoKinError("OKL-E-RESOURCE", "A request cannot switch programs.",
                               category="resource_limit", phase="support",
                               details={"budget_reason": "execution_context_required"})

    def __call__(self):
        self.execution_budget.tick()


def byte_patch(program, old, new, *, occurrence=0, element_id=None):
    raw = old.encode("utf-8")
    start = -1
    for _ in range(occurrence + 1):
        start = program.entry.raw.index(raw, start + 1)
    return {"source_id": "entry", "source_revision": program.entry.revision,
            "element_id": element_id or ["sources", "entry"],
            "start_byte": start, "end_byte": start + len(raw),
            "expected_text": old, "replacement": new}


class BudgetProgramRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.runtime = BudgetProgramRuntime()

    def test_construction_evaluation_inspection_use_one_counter_and_start(self):
        program, check = source(), RequestContext()
        ledger = check.execution_budget
        original_start = ledger.started
        represented = self.runtime.validate_revision(program, level="constructed", check=check)
        self.assertEqual(represented["outcome"], "valid", represented)
        first = ledger.operations
        evaluated = self.runtime.evaluate_revision(program, until="0.5", check=check)
        self.assertEqual(evaluated["outcome"], "valid", evaluated)
        self.assertGreater(ledger.operations, first)
        second = ledger.operations
        inspected = self.runtime.inspect_revision(program, fields=["identity", "support"], check=check)
        self.assertEqual(inspected["outcome"], "valid", inspected)
        self.assertGreater(ledger.operations, second)
        self.assertEqual(ledger.started, original_start)
        self.assertEqual(check.admissions, 1)
        limits = inspected["items"][0]["support"]["limits"]
        self.assertEqual(limits["max_operations"], 200000)
        self.assertEqual(limits["max_elapsed_ms"], 60000)

    def test_exhaustion_in_later_operation_does_not_reset_allowance(self):
        program = source(TEXT.replace("200000", "600"))
        check = RequestContext(clock=lambda: 0.0)
        first = self.runtime.validate_revision(program, level="constructed", check=check)
        self.assertEqual(first["outcome"], "valid", first)
        consumed = check.execution_budget.operations
        failed = self.runtime.evaluate_revision(program, until="1", check=check)
        self.assertEqual(failed["outcome"], "resource_limit", failed)
        self.assertGreater(consumed, 0)
        self.assertEqual(check.execution_budget.operations, 601)
        self.assertEqual(check.admissions, 1)

    def test_rejected_host_request_cannot_construct_body(self):
        check = RequestContext(policy=HostPolicy())
        with patch.object(ConstructionCompiler, "run", side_effect=AssertionError("body executed")):
            result = self.runtime.validate_revision(source(), check=check)
        self.assertEqual(result["outcome"], "resource_limit", result)
        self.assertEqual(result["diagnostics"][0]["details"]["budget_reason"], "host_ceiling_exceeded")
        self.assertIsNone(check.execution_budget.resolved)

    def test_missing_or_unrelated_execution_context_is_rejected(self):
        result = self.runtime.validate_revision(source())
        self.assertEqual(result["outcome"], "resource_limit", result)
        self.assertEqual(result["diagnostics"][0]["details"]["budget_reason"], "execution_context_required")
        check = RequestContext()
        self.runtime.validate_revision(source(), check=check)
        changed = source(TEXT.replace("2[s]", "3[s]"))
        result = self.runtime.validate_revision(changed, check=check)
        self.assertEqual(result["outcome"], "resource_limit", result)
        self.assertEqual(check.admissions, 1)

    def test_runtime_cannot_substitute_caps_for_request_context(self):
        check = RequestContext(caps={"max_operations": 100000})
        result = self.runtime.validate_revision(source(), budgets={"max_operations": 150000}, check=check)
        self.assertEqual(result["outcome"], "resource_limit", result)
        self.assertEqual(result["diagnostics"][0]["details"]["budget_reason"], "execution_context_required")
        self.assertEqual(check.admissions, 0)

    def test_omitted_source_fields_keep_defaults_on_larger_host(self):
        program = source(TEXT.replace("execution { max_operations = 200000; max_elapsed = 60[s]; }\n", ""))
        check = RequestContext()
        result = self.runtime.validate_revision(program, check=check)
        self.assertEqual(result["outcome"], "valid", result)
        self.assertEqual(check.execution_budget.limits, {"max_operations": 100000, "max_elapsed_ms": 30000})

    def test_old_high_request_can_be_repaired_without_executing_it(self):
        original = source(TEXT.replace("200000", "400000"))
        check = RequestContext(policy=HostPolicy(200000, 60000))
        ledger = check.execution_budget
        original_start = ledger.started
        with patch.object(ConstructionCompiler, "run", side_effect=AssertionError("old body executed")):
            candidate = self.runtime.apply_patches(original, [byte_patch(original, "400000", "200000")], check=check)
        self.assertIsNone(ledger.resolved)
        prepared = ledger.operations
        result = self.runtime.validate_revision(candidate, level="constructed", check=check)
        self.assertEqual(result["outcome"], "valid", result)
        self.assertGreater(prepared, 0)
        self.assertGreater(ledger.operations, prepared)
        self.assertEqual(ledger.started, original_start)
        self.assertEqual(ledger.admitted_entry_revision, candidate.entry.revision)
        self.assertNotEqual(original.program_revision, candidate.program_revision)

    def test_edit_preparation_time_remains_in_original_deadline(self):
        clock = [0.0]
        check = RequestContext(caps={"max_elapsed_ms": 10}, clock=lambda: clock[0])
        original = source()
        candidate = self.runtime.apply_patches(original, [byte_patch(original, "2[s]", "3[s]")],
                                               budgets={"max_elapsed_ms": 10}, check=check)
        clock[0] = .011
        result = self.runtime.validate_revision(candidate, budgets={"max_elapsed_ms": 10}, check=check)
        self.assertEqual(result["outcome"], "resource_limit", result)
        self.assertEqual(check.execution_budget.started, 0.0)
        self.assertEqual(check.execution_budget.budget_reason, "execution_deadline_exceeded")

    def test_patch_stale_hash_expected_text_and_overlap_fail_atomically(self):
        program = source()
        valid = byte_patch(program, "200000", "100000")
        cases = [[{**valid, "source_revision": "sha256:" + "0" * 64}],
                 [{**valid, "expected_text": "300000"}], [valid, valid]]
        for patches in cases:
            with self.subTest(patches=patches), self.assertRaises(OntoKinError):
                self.runtime.apply_patches(program, patches, check=RequestContext())
        self.assertEqual(program.entry.text, TEXT)

    def test_patch_utf8_boundaries_and_source_scope_are_enforced(self):
        program = source(TEXT + "// café\n")
        start = program.entry.raw.index("é".encode()) + 1
        split = {"source_id": "entry", "source_revision": program.entry.revision,
                 "element_id": ["sources", "entry"], "start_byte": start, "end_byte": start,
                 "expected_text": "", "replacement": "x"}
        misplaced = byte_patch(program, "200000", "100000", element_id=["workshop", "demo", "carrier"])
        for request in (split, misplaced):
            with self.subTest(request=request), self.assertRaises(OntoKinError):
                self.runtime.apply_patches(program, [request], check=RequestContext())

    def test_identity_map_is_complete_beyond_inspection_page_limit(self):
        program = source(TEXT.replace('object carrier @ "carrier": Carrier {}',
            '\n'.join(f'object item{i} @ "item-{i}": Carrier {{}}' for i in range(3))))
        check = RequestContext()
        result = self.runtime.validate_revision(program, budgets={"max_result_items": 1}, check=check)
        self.assertEqual(result["outcome"], "valid", result)
        with patch.object(ConstructionCompiler, "run", side_effect=AssertionError("duplicate construction")):
            identities = self.runtime.identity_map(program, budgets={"max_result_items": 1}, check=check)
        self.assertEqual(len(identities), 3)
        self.assertEqual([item["element_id"][-1] for item in identities], ["item-0", "item-1", "item-2"])
        self.assertTrue(all(item["definition_id"] == ["entry", "workshop", "definitions", "carrier-class"]
                            for item in identities))

    def test_inspection_exposes_only_implemented_source_edit_scope(self):
        check = RequestContext()
        result = self.runtime.inspect_revision(source(), fields=["identity", "source"], limit=100, check=check)
        self.assertEqual(result["outcome"], "valid", result)
        for record in result["items"]:
            if record["kind"] != "source":
                self.assertEqual(record["source"]["writable_spans"], [])
            target = record["source"].get("initializer_target", {})
            if target.get("available"):
                self.assertEqual(target["element_id"], ["sources", target["span"]["source_id"]])

    def test_fixed_materialization_cap_still_applies(self):
        check = RequestContext()
        result = self.runtime.inspect_revision(source(), fields=["values"],
                                                budgets={"max_value_entries": 5}, check=check)
        self.assertEqual(result["outcome"], "resource_limit", result)
        self.assertEqual(check.execution_budget.limits["max_operations"], 200000)

    def test_native_mesh_build_and_page_use_admitted_ledger(self):
        text = single_source().replace('ontokin "0.3";', 'ontokin "0.7";').replace(
            'profile "surface-0.1";', 'profile "planar-reach-budget-0.1";\n'
            'execution { max_operations = 200000; max_elapsed = 60[s]; }')
        program, check = source(text), RequestContext()
        context = prepare_surface_page(program, ["native-export", "demo", "shell"],
                                       count=3, profile=BUDGET_PROFILE, check=check)
        before = check.execution_budget.operations
        page, offset = context.page(0, 3)
        self.assertEqual(page["returned_triangles"], 3)
        self.assertEqual(page["total_triangles"], 64)
        self.assertEqual(offset, 3)
        self.assertGreater(check.execution_budget.operations, before)
        self.assertIs(context.budget.execution_budget, check.execution_budget)
        self.assertEqual(check.admissions, 1)

    def test_delivery_retains_compiler_work_for_exact_glb_readback(self):
        program, check = source(), RequestContext()
        compiler, result = self.runtime.prepare_delivery(program, until="0.25", check=check)
        self.assertEqual(result["outcome"], "valid", result)
        before = check.execution_budget.operations
        output = export_glb(compiler.model, options=ExportOptions(fps=2, end="0.25", helpers=False),
                            source_uri=program.entry.filename, source_sha256=program.entry.revision,
                            target_contract="ontokin.glb/0.7", work=compiler.reach_work,
                            reach_plan=compiler.reach_delivery_plan)
        self.assertEqual(output.report["validation"]["status"], "passed")
        self.assertGreater(check.execution_budget.operations, before)
        self.assertIs(compiler.reach_work.execution_budget, check.execution_budget)
        self.assertEqual(check.admissions, 1)

    def test_host_exception_identity_survives_header_and_evaluation(self):
        for stage in ("header_admission", "evaluation"):
            error = OntoKinError("OKL-E-RESOURCE", "host cancelled", category="resource_limit", phase="support")
            check = None
            def callback():
                if check.execution_budget.stage == stage:
                    raise error
            check = RequestContext(callback=callback)
            with self.subTest(stage=stage), self.assertRaises(OntoKinError) as caught:
                self.runtime.evaluate_revision(source(), until="0.25", check=check)
            self.assertIs(caught.exception, error)

    def test_caller_ontokin_error_from_numeric_work_keeps_identity(self):
        # Numerical work calls the ledger directly rather than the program
        # adapter. Its exception still belongs to the original host callback.
        error = OntoKinError("OKL-E-RESOURCE", "numeric cancellation", category="resource_limit", phase="support")
        check = RequestContext()
        compiler = self.runtime.compile_program(source(), check=check)
        check.execution_budget.check = lambda: (_ for _ in ()).throw(error)
        with self.assertRaises(OntoKinError) as caught:
            compiler.reach_work.charge("c074-cancellation-probe")
        self.assertIs(caught.exception, error)

    def test_legacy_binding_maps_and_budget_constructor_remain_closed(self):
        self.assertNotIn("ontokin.agent/0.7", PROGRAM_BINDINGS)
        self.assertNotIn(BUDGET_PROFILE, PROFILE_BINDINGS)
        with self.assertRaises(ValueError):
            ProgramRuntime(BUDGET_PROFILE)
        with self.assertRaises(OntoKinError):
            LegacyBudget({"max_operations": 100001}, None)


if __name__ == "__main__":
    unittest.main()
