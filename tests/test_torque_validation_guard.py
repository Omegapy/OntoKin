"""Whole-reader source authority and final original-callback controls."""
from fractions import Fraction as F
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.execution_budget import HostPolicy, SharedExecutionBudget, admit_entry_budget
from ontokin.reach_reference import ReferenceError, build_reference
from ontokin.reach_conformance import validate_reach_export
from ontokin.texture_bundle import load_texture_file_manifest
from ontokin.torque_validation_guard import TorqueValidationScope
from ontokin.diagnostics import OntoKinError


FROZEN = Path(__file__).resolve().parents[1] / "docs/language-design/torque-v0.1/freeze"


def constructed(name="delivery-p01-spin-up", check=None):
    bundle = load_texture_file_manifest(FROZEN / (name + ".files.json"))
    ledger = SharedExecutionBudget(HostPolicy(max_operations=1000000, max_elapsed_ms=30000), check=check)
    admit_entry_budget(bundle.entry, ledger, profile="torque-0.1")
    compiler = compile_construction(bundle, execution_budget=ledger)
    return compiler.model, compiler.reach_work, ledger


class TorqueValidationGuardTests(unittest.TestCase):
    def test_all_frozen_sources_admit_without_new_or_foreign_type(self):
        cases = json.loads((FROZEN / "delivery-cases.json").read_text())["cases"]
        for case in cases:
            with self.subTest(case=case["id"]):
                model, work, ledger = constructed(case["id"])
                with TorqueValidationScope(model, work) as scope:
                    self.assertIsNot(scope.model, model)
                    self.assertEqual(scope.model.program_revision, model.program_revision)
                    self.assertEqual(scope.model.objects.keys(), model.objects.keys())
                    self.assertIsNot(scope.model.events, model.events)
                    self.assertEqual(scope.model.texture_assets, model.texture_assets)
                self.assertIsNone(work._source_after_charge)

    def test_detached_source_cannot_follow_transient_original_mutation(self):
        model, work, ledger = constructed()
        with TorqueValidationScope(model, work) as scope:
            original = model.objects["ball"].physical["inertia"]
            model.objects["ball"].physical["inertia"] = 2.0
            reference = build_reference(scope.model, end=F(1), work=work)
            speed = reference.sample(F(1))["objects"]["ball"]["torques"]["signed_angular_speed_rad_per_s"]
            self.assertTrue(speed.contains(2))
            self.assertFalse(speed.contains(1))
            model.objects["ball"].physical["inertia"] = original

    def test_detached_fraction_integer_slots_do_not_alias_original(self):
        model, work, ledger = constructed()
        with TorqueValidationScope(model, work) as scope:
            original = model.events[0].events[0].torque.duration
            detached = scope.model.events[0].events[0].torque.duration
            self.assertIsNot(original, detached)
            previous = original.numerator
            object.__setattr__(original, "_numerator", previous + original.denominator)
            self.assertEqual(detached, F(previous, original.denominator))
            object.__setattr__(original, "_numerator", previous)

    def final_callback_count(self):
        owner = {"armed": False, "calls": 0}
        def check():
            if owner["armed"]: owner["calls"] += 1
        model, work, ledger = constructed(check=check)
        with TorqueValidationScope(model, work):
            owner["armed"] = True
        return owner["calls"]

    def test_last_callback_cannot_change_source_clone_context_or_counter(self):
        last = self.final_callback_count()
        for mutation in ("source", "future_event", "detached", "counter", "callback_owner", "clock_owner",
                         "clock_fraction", "payload_fraction", "source_span", "work_charge", "ledger_tick",
                         "resolved_limit", "limit_owner", "producer_hook"):
            with self.subTest(mutation=mutation):
                owner = {"armed": False, "calls": 0}
                def check():
                    if not owner["armed"]: return
                    owner["calls"] += 1
                    if owner["calls"] == last:
                        if mutation == "source": owner["model"].objects["ball"].physical["inertia"] = 2.0
                        elif mutation == "future_event": owner["model"].events[0].events.clear()
                        elif mutation == "detached": owner["scope"].model.objects["ball"].physical["inertia"] = 2.0
                        elif mutation == "counter": owner["ledger"].operations = 0
                        elif mutation == "callback_owner": owner["ledger"].check = lambda: None
                        elif mutation == "clock_owner": owner["ledger"]._clock = lambda: 0.0
                        elif mutation == "clock_fraction":
                            time = owner["model"].events[0].time
                            object.__setattr__(time, "_numerator", time.numerator + time.denominator)
                        elif mutation == "payload_fraction":
                            duration = owner["model"].events[0].events[0].torque.duration
                            object.__setattr__(duration, "_numerator", duration.numerator + duration.denominator)
                        elif mutation == "source_span":
                            owner["model"].events[0].events[0].span.start += 1
                        elif mutation == "work_charge": owner["work"].charge = lambda *args, **kwargs: None
                        elif mutation == "ledger_tick": owner["ledger"].tick = lambda *args, **kwargs: None
                        elif mutation == "resolved_limit":
                            object.__setattr__(owner["ledger"].resolved, "effective", {"max_operations": 10**8})
                        elif mutation == "limit_owner": owner["ledger"]._limits = dict(owner["ledger"]._limits)
                        elif mutation == "producer_hook": owner["ledger"]._torque_context_guard = lambda: None
                model, work, ledger = constructed(check=check)
                owner.update(model=model, work=work, ledger=ledger)
                native_first = (getattr(ledger, "_torque_guarded", False) and mutation in
                                {"counter", "callback_owner", "clock_owner", "limit_owner", "producer_hook"})
                expected = OntoKinError if native_first else ReferenceError
                with self.assertRaises(expected) as caught:
                    with TorqueValidationScope(model, work) as scope:
                        owner.update(scope=scope, armed=True)
                if native_first:
                    self.assertEqual(caught.exception.diagnostic.code, "OKL-E-RESOURCE")
                    self.assertEqual(caught.exception.diagnostic.details["budget_reason"],
                                     "execution_context_required")
                else:
                    self.assertEqual(caught.exception.code, "identity")
                self.assertEqual(owner["calls"], last)
                self.assertIsNone(work._source_after_charge)

    def test_original_final_cancellation_is_propagated_by_identity(self):
        last = self.final_callback_count(); sentinel = RuntimeError("original cancellation")
        owner = {"armed": False, "calls": 0}
        def check():
            if owner["armed"]:
                owner["calls"] += 1
                if owner["calls"] == last: raise sentinel
        model, work, ledger = constructed(check=check)
        with self.assertRaises(RuntimeError) as caught:
            with TorqueValidationScope(model, work): owner["armed"] = True
        self.assertIs(caught.exception, sentinel)
        self.assertIs(work.callback_error, sentinel)
        self.assertIsNone(work._source_after_charge)

    def test_existing_after_charge_observer_is_chained_and_restored(self):
        model, work, ledger = constructed(); observed = []
        observer = lambda: observed.append(work.operations)
        work._source_after_charge = observer
        with TorqueValidationScope(model, work): work.charge("explicit_test")
        self.assertIs(work._source_after_charge, observer)
        self.assertGreater(len(observed), 2)
        self.assertEqual(observed, sorted(set(observed)))

    def test_inactive_producer_guard_is_admitted_suspended_and_restored(self):
        model, work, ledger = constructed()
        calls = []
        def producer_guard():
            calls.append(work.operations)
            self.assertIs(ledger._torque_context_guard, producer_guard)
        ledger._torque_context_guard = producer_guard
        with TorqueValidationScope(model, work):
            self.assertIsNone(ledger._torque_context_guard)
            self.assertEqual(len(calls), 1)
            work.charge("complete_independent_proof", 10)
            self.assertEqual(len(calls), 1)
        self.assertIs(ledger._torque_context_guard, producer_guard)
        self.assertEqual(len(calls), 2)
        self.assertGreater(calls[1], calls[0])

    def test_inactive_producer_guard_restores_without_masking_original_exception(self):
        owner = {"armed": False}; sentinel = RuntimeError("original reader cancellation")
        def check():
            if owner["armed"]:
                raise sentinel
        model, work, ledger = constructed(check=check)
        calls = []
        def producer_guard(): calls.append(work.operations)
        ledger._torque_context_guard = producer_guard
        with self.assertRaises(RuntimeError) as caught:
            with TorqueValidationScope(model, work):
                owner["armed"] = True
                work.charge("cancel_actual_independent_proof")
        self.assertIs(caught.exception, sentinel)
        self.assertIs(ledger._torque_context_guard, producer_guard)
        self.assertIsNone(work._source_after_charge)
        self.assertEqual(len(calls), 1)

    def test_public_validator_cannot_return_passed_before_final_source_admission(self):
        owner = {"armed": False}
        def check():
            if owner["armed"]: owner["model"].objects["ball"].physical["inertia"] = 2.0
        model, work, ledger = constructed(check=check); owner["model"] = model
        def proof(data, detached, **kwargs):
            self.assertIsNot(detached, model); owner["armed"] = True
            return {"status": "passed"}
        with patch("ontokin.reach_conformance._validate_reach_export", side_effect=proof):
            with self.assertRaises(OntoKinError) as caught:
                validate_reach_export(b"unused_controlled_stub", model, work=work,
                                      target_contract="ontokin.glb/0.22")
        self.assertEqual(caught.exception.diagnostic.details["export_code"], "OKE-E-INDEPENDENT-VALIDATION")

    def test_foreign_container_is_rejected_before_its_iteration(self):
        class Foreign(dict):
            def items(self): raise AssertionError("foreign iterator must not run")
        model, work, ledger = constructed(); model.objects["ball"].geometry = Foreign()
        with self.assertRaises(ReferenceError): TorqueValidationScope(model, work)


if __name__ == "__main__": unittest.main()
