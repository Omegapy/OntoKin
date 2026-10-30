"""Source/CLI resource boundaries, recorded prefixes and publication failures."""
from contextlib import redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ontokin import scene, validator
from ontokin.agent_runtime import _Budget as LegacyBudget
from ontokin.budget_runtime import execute_budgeted_export
from ontokin.bundle import ProgramBundle, SourceUnit
from ontokin.cli import capabilities, main, _write_export_transaction
from ontokin.construction import ConstructionBudget, ExecutionConstructionBudget, ConstructionCompiler, compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.execution_budget import HostPolicy, SharedExecutionBudget, admit_entry_budget
from ontokin.json_limits import JSONLimitError
from ontokin.program_bindings import PROGRAM_BINDINGS, PROFILE_BINDINGS
from ontokin.program_runtime import _Budget as LegacyProgramBudget
from ontokin.reach_numeric import ReachExecutionWork
from ontokin.scene import ExportOptions


TEXT = '''ontokin "0.7";
module Workshop @ "workshop";
profile "planar-reach-budget-0.1";
execution { max_operations = 200000; max_elapsed = 60[s]; }
class Carrier @ "carrier-class" {
    geometry = box(vec3(1[m], 2[m], 3[m]));
    physical = no_body();
}
scene Demo @ "demo" {
    duration = 2[s];
    gravity = vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2]);
    object carrier @ "carrier": Carrier {}
}
'''
POLICY = HostPolicy(400000, 80000)
OPTIONS = ExportOptions(fps=2, end="0.25", helpers=False)


def bundle(text=TEXT):
    return ProgramBundle(SourceUnit("entry", "workshop.ok", text.encode()))


class ExecutionBudgetRuntimeTests(unittest.TestCase):
    def run_source(self, text=TEXT, **kwargs):
        return execute_budgeted_export(bundle(text), policy=POLICY, options=OPTIONS, **kwargs)

    def test_EB02_actual_source_to_independent_output_has_complete_identity(self):
        source = bundle()
        result = execute_budgeted_export(source, policy=POLICY, options=OPTIONS)
        self.assertIsNotNone(result.data)
        report = result.report
        self.assertEqual(report["validation"]["status"], "passed")
        self.assertEqual(report["artifact"]["sha256"], "sha256:" + hashlib.sha256(result.data).hexdigest())
        self.assertEqual(report["source_revision"], source.entry.revision)
        self.assertEqual(report["program_revision"], source.program_revision)
        self.assertIn("source_code_sha256", report["implementation_identity"])
        self.assertEqual(report["execution_budget"]["effective"],
                         {"max_operations": 200000, "max_elapsed_ms": 60000})
        self.assertGreater(report["execution_budget"]["consumed_operations"], 100)
        self.assertEqual(report["valid_prefix"]["valid_until_seconds"], "0.25")

    def test_EB03_EB04_actual_75_and_80_second_source_paths(self):
        for elapsed in (75, 80):
            text = TEXT.replace("200000", "400000").replace("60[s]", str(elapsed) + "[s]")
            with self.subTest(elapsed_seconds=elapsed):
                result = self.run_source(text, clock=lambda: 0.0)
                self.assertIsNotNone(result.data, result.report)
                self.assertEqual(result.report["execution_budget"]["effective"],
                                 {"max_operations": 400000, "max_elapsed_ms": elapsed * 1000})
                self.assertEqual(result.report["validation"]["status"], "passed")

    def test_EB13_larger_execution_still_rejects_object_and_keyed_limits(self):
        many_objects = "\n".join(f'    object item{i} @ "item-{i}": Carrier {{}}' for i in range(1001))
        objects = TEXT.replace('    object carrier @ "carrier": Carrier {}', many_objects)
        object_result = self.run_source(objects)
        self.assertIsNone(object_result.data)
        self.assertEqual(object_result.report["diagnostics"][0]["details"]["budget"], "max_objects")
        entries = ",\n".join(f'        "k{i}": {i}' for i in range(257))
        keyed = TEXT.replace('    geometry = box', '    public param values @ "values": Keyed<Int> = keyed<Int> {\n'
                             + entries + '\n    };\n    geometry = box')
        keyed_result = self.run_source(keyed)
        self.assertIsNone(keyed_result.data)
        self.assertEqual(keyed_result.report["diagnostics"][0]["details"]["budget"], "keyed_entries")

    def test_EB10_complete_request_succeeds_at_exact_count_and_fails_one_lower(self):
        reference = self.run_source(caller_caps={"max_operations": 200000}, clock=lambda: 0.0)
        self.assertIsNotNone(reference.data)
        count = reference.report["execution_budget"]["consumed_operations"]
        exact = self.run_source(caller_caps={"max_operations": count}, clock=lambda: 0.0)
        self.assertIsNotNone(exact.data, exact.report)
        self.assertEqual(exact.report["execution_budget"]["consumed_operations"], count)
        failed = self.run_source(caller_caps={"max_operations": count - 1}, clock=lambda: 0.0)
        self.assertIsNone(failed.data)
        self.assertEqual(failed.report["execution_budget"]["budget_reason"], "operation_budget_exhausted")
        self.assertEqual(failed.report["execution_budget"]["consumed_operations"], count)
        self.assertNotIn("artifact", failed.report)

    def test_EB19_numerical_callbacks_keep_exception_identity_and_diagnostic(self):
        for marker in (OntoKinError("OKL-E-TYPE", "caller stop"), RecursionError("caller stop"),
                       JSONLimitError("caller_limit", 1, 2)):
            state = {"numeric": False}
            def check():
                if state["numeric"]:
                    raise marker
            def numeric_probe(compiler):
                state["numeric"] = True
                compiler.reach_work.charge("callback_probe")
            with self.subTest(type=type(marker).__name__), patch.object(ConstructionCompiler, "run", numeric_probe):
                with self.assertRaises(type(marker)) as caught:
                    self.run_source(check=check)
                self.assertIs(caught.exception, marker)
                if isinstance(marker, OntoKinError):
                    self.assertIsNone(marker.diagnostic.node)
                    self.assertEqual(marker.diagnostic.details, {})

    def test_EB19_header_callback_json_error_is_not_a_product_failure(self):
        marker = JSONLimitError("caller_limit", 1, 2)
        def cancel():
            raise marker
        with self.assertRaises(JSONLimitError) as caught:
            self.run_source(check=cancel)
        self.assertIs(caught.exception, marker)

    def test_EB19_field_and_provenance_callbacks_keep_identity_and_details(self):
        for owner, name in ((validator.Validator, "field"), (scene, "program_metadata")):
            original = getattr(owner, name)
            for marker in (OntoKinError("OKL-E-TYPE", "caller stop"), ValueError("caller stop"),
                           JSONLimitError("caller_limit", 1, 2)):
                state = {"inside": False}
                def check():
                    if state["inside"]:
                        raise marker
                def enter(*args, **kwargs):
                    state["inside"] = True
                    try:
                        return original(*args, **kwargs)
                    finally:
                        state["inside"] = False
                with self.subTest(stage=name, error=type(marker).__name__), patch.object(owner, name, enter):
                    with self.assertRaises(type(marker)) as caught:
                        self.run_source(check=check)
                    self.assertIs(caught.exception, marker)
                    if isinstance(marker, OntoKinError):
                        self.assertIsNone(marker.diagnostic.node)
                        self.assertIsNone(marker.diagnostic.element_id)
                        self.assertEqual(marker.diagnostic.details, {})

    def test_EB20_failed_later_boundary_preserves_only_the_valid_prefix(self):
        text = TEXT.replace('    object carrier @ "carrier": Carrier {}', '''    object carrier @ "carrier": Carrier {}
    action travel @ "travel" = move(carrier, vector(world, 1[m/s], 0[m/s], 0[m/s]), 2[s]);
    at 0[s] sequence { start travel; }
    at 1[s] sequence { start travel; }''')
        short = self.run_source(text)
        self.assertIsNotNone(short.data, short.report)
        failed = execute_budgeted_export(bundle(text), policy=POLICY,
                                        options=ExportOptions(fps=2, end="2", helpers=False))
        self.assertIsNone(failed.data)
        self.assertEqual(failed.report["valid_prefix"]["valid_until_seconds"], "1")
        self.assertEqual(failed.report["valid_prefix"]["valid_until_side"], "before")
        self.assertNotEqual(failed.report["achieved_level"], "delivered")

    def test_EB21_legacy_limits_and_agent_routes_stay_closed(self):
        for constructor in (LegacyBudget, LegacyProgramBudget, ConstructionBudget):
            with self.subTest(constructor=constructor.__name__), self.assertRaises(OntoKinError):
                constructor({"max_operations": 100001}, None)
        with self.assertRaises(ValueError):
            ReachExecutionWork(max_operations=100001)
        self.assertNotIn("ontokin.agent/0.7", PROGRAM_BINDINGS)
        self.assertNotIn("planar-reach-budget-0.1", PROFILE_BINDINGS)
        with self.assertRaises(OntoKinError) as caught:
            compile_construction(bundle())
        self.assertEqual(caught.exception.diagnostic.details["budget_reason"], "execution_context_required")

    def test_EB21_legacy_native_budget_and_explicit_adapter_stay_separate(self):
        from ontokin import reach_conformance as reader
        text = TEXT.replace('ontokin "0.7";', 'ontokin "0.6";').replace(
            'profile "planar-reach-budget-0.1";', 'profile "planar-reach-0.1";').replace(
            'execution { max_operations = 200000; max_elapsed = 60[s]; }\n', '')
        ordinary = compile_construction(bundle(text))
        self.assertIs(type(ordinary.budget), ConstructionBudget)
        self.assertIs(type(ordinary.budget.__dict__["operations"]), int)
        self.assertNotIn("execution_budget", ordinary.budget.__dict__)
        self.assertNotIn("operations", ConstructionBudget.__dict__)
        legacy_decode = reader._CertificateFieldDecodes.create(
            reader._Bounds(ordinary.reach_work), (1.0, 1.0, 1.0))
        self.assertIsNotNone(legacy_decode)
        source = bundle()
        ledger = SharedExecutionBudget(POLICY, clock=lambda: 0.0)
        admit_entry_budget(source.entry, ledger)
        explicit = compile_construction(source, execution_budget=ledger)
        self.assertIs(type(explicit.budget), ExecutionConstructionBudget)
        self.assertIs(explicit.budget.execution_budget, ledger)
        self.assertIs(explicit.reach_work.execution_budget, ledger)
        self.assertIsNone(reader._CertificateFieldDecodes.create(
            reader._Bounds(explicit.reach_work), (1.0, 1.0, 1.0)))
        before = ledger.operations
        explicit.budget.tick(amount=2)
        explicit.reach_work.tick()
        self.assertEqual(ledger.operations, before + 3)
        self.assertEqual(explicit.budget.operations, ledger.operations)
        self.assertEqual(explicit.budget.report()["operations"], ledger.operations)
        self.assertEqual(explicit.budget.started, ledger.started)
        self.assertEqual(explicit.budget.limits["max_objects"], 1000)
        self.assertEqual(explicit.budget.limits["max_value_entries"], 100000)

    def test_EB23_an_admission_cannot_compile_different_entry_bytes(self):
        source = bundle()
        ledger = SharedExecutionBudget(POLICY)
        admit_entry_budget(source.entry, ledger)
        with self.assertRaises(OntoKinError) as caught:
            compile_construction(bundle(TEXT + "// changed revision\n"), execution_budget=ledger)
        self.assertEqual(caught.exception.diagnostic.details["budget_reason"], "execution_context_required")

    def test_EB26_discovery_separates_defaults_from_host_ceilings(self):
        ordinary_capabilities = capabilities()
        large_capabilities = capabilities(host_policy=POLICY)
        ordinary = ordinary_capabilities["execution_budget_interface"]
        large = large_capabilities["execution_budget_interface"]
        self.assertEqual(ordinary["defaults"], large["defaults"])
        self.assertEqual(ordinary["host_ceilings"], ordinary["defaults"])
        self.assertEqual(large["host_ceilings"], POLICY.ceilings)
        self.assertIsNone(large["agent_contract"])
        self.assertEqual(set(large["export_targets"]), {"ontokin.glb/0.7"})
        self.assertEqual(ordinary["export_targets"], large["export_targets"])
        self.assertEqual(large["export_targets"]["ontokin.glb/0.7"]["profile"],
                         "planar-reach-budget-0.1")
        self.assertEqual(large["delivery_contract"], "ontokin.glb/0.7")
        legacy_targets = ordinary_capabilities["export_targets"]
        self.assertEqual(set(legacy_targets), {"ontokin.glb/0.1", "ontokin.glb/0.2",
                         "ontokin.glb/0.3", "ontokin.glb/0.4", "ontokin.glb/0.5", "ontokin.glb/0.6"})
        self.assertEqual(legacy_targets, large_capabilities["export_targets"])
        # Freeze every legacy descriptor value from the verified C072 baseline,
        # commit 6277e57915c943ea933cd306956181ee18cdd084, as canonical JSON.
        self.assertEqual(hashlib.sha256(json.dumps(legacy_targets, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")).hexdigest(),
                         "ed7a32850811969a7943923965eb1543e3a8db4593364bd31ce9aa182cf918d6")

    def test_EB27_computation_timeout_does_not_change_recorded_time(self):
        first = self.run_source()
        second = self.run_source(TEXT.replace("60[s]", "80[s]"))
        self.assertIsNotNone(first.data)
        self.assertIsNotNone(second.data)
        self.assertEqual(first.report["valid_prefix"]["valid_until_seconds"], "0.25")
        self.assertEqual(first.report["sampling"], second.report["sampling"])


class ExecutionBudgetCLITests(unittest.TestCase):
    def invoke(self, args, **kwargs):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            status = main([str(item) for item in args], **kwargs)
        return status, json.loads(stdout.getvalue())

    def paths(self, root):
        source, output = Path(root) / "workshop.ok", Path(root) / "workshop.glb"
        source.write_text(TEXT)
        return source, output, output.with_suffix(".export.json")

    def args(self, source, output):
        return ["export", source, "--target", "ontokin.glb/0.7", "--output", output,
                "--end", "0.25", "--fps", "2", "--no-helpers"]

    def test_EB05_default_cli_refuses_source_increase_before_creating_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            source, output, report = self.paths(directory)
            status, result = self.invoke(self.args(source, output))
            self.assertEqual(status, 2)
            self.assertEqual(result["execution_budget"]["budget_reason"], "host_ceiling_exceeded")
            self.assertFalse(output.exists())
            self.assertFalse(report.exists())

    def test_EB17_trusted_host_and_caller_reduction_execute_actual_cli(self):
        with tempfile.TemporaryDirectory() as directory:
            source, output, report = self.paths(directory)
            status, result = self.invoke(self.args(source, output) + ["--max-operations", 100000,
                "--max-elapsed-ms", 30000], host_policy=POLICY)
            self.assertEqual(status, 0, result)
            self.assertEqual(json.loads(report.read_text()), result)
            self.assertEqual(result["artifact"]["sha256"], "sha256:" + hashlib.sha256(output.read_bytes()).hexdigest())
            self.assertEqual(result["execution_budget"]["effective"],
                             {"max_operations": 100000, "max_elapsed_ms": 30000})

    def test_EB20_resource_failure_keeps_existing_destinations(self):
        with tempfile.TemporaryDirectory() as directory:
            source, output, report = self.paths(directory)
            output.write_bytes(b"existing glb")
            report.write_bytes(b"existing report")
            status, result = self.invoke(self.args(source, output) + ["--max-operations", 80], host_policy=POLICY)
            self.assertEqual(status, 2)
            self.assertEqual(result["execution_budget"]["budget_reason"], "operation_budget_exhausted")
            self.assertEqual(output.read_bytes(), b"existing glb")
            self.assertEqual(report.read_bytes(), b"existing report")
            self.assertEqual(list(Path(directory).glob(".ontokin-*")), [])

    def test_EB20_deadline_failure_does_not_publish_or_retry(self):
        from ontokin.gltf import export_glb
        now = {"value": 0.0, "attempts": 0}
        def ledger_factory(policy, caller_caps, **kwargs):
            return SharedExecutionBudget(policy, caller_caps, check=kwargs.get("check"),
                                         clock=lambda: now["value"])
        def expire_before_export(*args, **kwargs):
            now["attempts"] += 1
            now["value"] = 60.001
            return export_glb(*args, **kwargs)
        with tempfile.TemporaryDirectory() as directory:
            source, output, report = self.paths(directory)
            output.write_bytes(b"existing glb")
            report.write_bytes(b"existing report")
            with patch("ontokin.budget_runtime.SharedExecutionBudget", ledger_factory), \
                    patch("ontokin.gltf.export_glb", expire_before_export):
                status, result = self.invoke(self.args(source, output), host_policy=POLICY)
            self.assertEqual(status, 2)
            self.assertEqual(result["execution_budget"]["budget_reason"], "execution_deadline_exceeded")
            self.assertEqual(now["attempts"], 1)
            self.assertEqual(output.read_bytes(), b"existing glb")
            self.assertEqual(report.read_bytes(), b"existing report")

    def test_EB20_second_publication_error_restores_both_original_files(self):
        with tempfile.TemporaryDirectory() as directory:
            _, output, report = self.paths(directory)
            output.write_bytes(b"existing glb")
            report.write_bytes(b"existing report")
            replace = os.replace
            def fail_second(src, dst):
                if Path(src).suffix == ".tmp" and Path(dst) == report:
                    raise OSError("second publication failed")
                return replace(src, dst)
            with patch("ontokin.cli.os.replace", fail_second), self.assertRaises(OSError):
                _write_export_transaction(output, b"new glb", report, {"outcome": "valid"})
            self.assertEqual(output.read_bytes(), b"existing glb")
            self.assertEqual(report.read_bytes(), b"existing report")
            self.assertEqual(list(Path(directory).glob(".ontokin-*")), [])

    def test_EB20_failed_restore_retains_original_recovery_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            _, output, report = self.paths(directory)
            output.write_bytes(b"existing glb")
            report.write_bytes(b"existing report")
            replace = os.replace
            def fail_twice(src, dst):
                if (Path(src).suffix == ".tmp" and Path(dst) == report) or Path(src).suffix == ".backup":
                    raise OSError("storage failure")
                return replace(src, dst)
            with patch("ontokin.cli.os.replace", fail_twice), self.assertRaises(OSError) as caught:
                _write_export_transaction(output, b"new glb", report, {"outcome": "valid"})
            retained = list(Path(directory).glob(".ontokin-*.backup"))
            self.assertEqual(sorted(p.read_bytes() for p in retained),
                             [b"existing glb", b"existing report"])
            for path in retained:
                self.assertIn(str(path), str(caught.exception))

    def test_EB20_output_unlink_failure_does_not_prevent_original_restoration(self):
        with tempfile.TemporaryDirectory() as directory:
            _, output, report = self.paths(directory)
            output.write_bytes(b"existing glb")
            report.write_bytes(b"existing report")
            replace, unlink = os.replace, Path.unlink
            def fail_second(src, dst):
                if Path(src).suffix == ".tmp" and Path(dst) == report:
                    raise OSError("second publication failed")
                return replace(src, dst)
            def cannot_unlink(path, *args, **kwargs):
                if path == output:
                    raise OSError("cannot unlink output")
                return unlink(path, *args, **kwargs)
            with patch("ontokin.cli.os.replace", fail_second), patch.object(Path, "unlink", cannot_unlink), \
                    self.assertRaisesRegex(OSError, "second publication failed"):
                _write_export_transaction(output, b"new glb", report, {"outcome": "valid"})
            self.assertEqual(output.read_bytes(), b"existing glb")
            self.assertEqual(report.read_bytes(), b"existing report")
            self.assertEqual(list(Path(directory).glob(".ontokin-*")), [])


if __name__ == "__main__":
    unittest.main()
