"""Real original callbacks cannot change the admitted source or its ledger."""
import copy
import math
import time
from dataclasses import replace
from fractions import Fraction as F
import unittest

from ontokin.diagnostics import OntoKinError
from ontokin.construction import compile_construction
from ontokin.execution_budget import SharedExecutionBudget, admit_entry_budget
from ontokin.evaluator import construct, evaluate, evaluate_prefix, preflight
from ontokin.torque_runtime import torque_record_bound
from test_torque_runtime import simulator, source


class TorqueCallbackAdmissionTests(unittest.TestCase):
    def refused_mutation(self, mutate, *, stage="torque_aggregate_begin", occurrence=1):
        owner, visits = {}, []
        def check():
            sim = owner.get("sim")
            if sim is not None and owner["ledger"].stage == stage:
                visits.append(owner["ledger"].operations)
                if len(visits) == occurrence:
                    owner["accepted"] = sim.state, copy.deepcopy(sim.state), sim.event_index
                    mutate(sim, owner["ledger"])
        sim, ledger = simulator(source("p08-split-neutral-overlap"), check=check)
        owner.update(sim=sim, ledger=ledger)
        with self.assertRaises(OntoKinError) as caught:
            sim.advance(F(3))
        self.assertEqual(caught.exception.diagnostic.code, "OKL-E-RESOURCE")
        self.assertEqual(caught.exception.diagnostic.details["budget_reason"], "execution_context_required")
        accepted, saved, index = owner["accepted"]
        self.assertIs(sim.state, accepted)
        self.assertEqual(sim.state, saved)
        self.assertEqual(sim.event_index, index)
        self.assertEqual(ledger.stage, "execution")
        self.assertIs(ledger.check, check)
        return sim, ledger, visits

    def test_future_event_removal_is_rejected_at_original_callback_return(self):
        self.refused_mutation(lambda sim, ledger: sim.events[1].events.clear())

    def test_future_event_order_and_equal_container_replacement_are_rejected(self):
        for mutate in (lambda sim, ledger: sim.events[1].events.reverse(),
                       lambda sim, ledger: setattr(sim.events[1], "events", list(sim.events[1].events))):
            with self.subTest(mutation=mutate):
                self.refused_mutation(mutate)

    def test_future_payload_clock_span_and_body_changes_are_rejected(self):
        mutations = (
            lambda sim, ledger: setattr(sim.events[1].events[0], "torque", replace(sim.events[1].events[0].torque, torque_n_m=9.0)),
            lambda sim, ledger: setattr(sim.events[1], "time", F(2)),
            lambda sim, ledger: setattr(sim.events[1].time, "_numerator", 5),
            lambda sim, ledger: setattr(sim.events[1].events[0].torque.duration, "_denominator", 2),
            lambda sim, ledger: setattr(sim.events[1].events[0].span, "start", 0),
            lambda sim, ledger: sim.model.objects["sibling"].physical.__setitem__("mass", 8.0))
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                self.refused_mutation(mutate)

    def test_original_counter_cannot_reset_decrease_overcount_or_become_boolean(self):
        for replace_count in (lambda n: 0, lambda n: n - 1, lambda n: n + 1, lambda n: True):
            with self.subTest(counter=replace_count):
                _, ledger, visits = self.refused_mutation(
                    lambda sim, ledger: setattr(ledger, "operations", replace_count(ledger.operations)))
                self.assertEqual(ledger.operations, visits[-1])

    def test_mid_projection_counter_reset_fails_before_more_primitives(self):
        _, ledger, visits = self.refused_mutation(
            lambda sim, ledger: setattr(ledger, "operations", 0),
            stage="torque_projection", occurrence=5)
        self.assertEqual(len(visits), 5)
        self.assertEqual(ledger.operations, visits[-1])

    def test_callback_guard_cannot_be_cleared(self):
        self.refused_mutation(lambda sim, ledger: setattr(ledger, "_torque_context_guard", None))

    def test_work_callback_and_limits_cannot_pass_by_foreign_equality(self):
        calls = []
        class Foreign:
            def __eq__(self, other):
                calls.append("equality")
                return True
            def __call__(self):
                calls.append("callback")
        for field in ("external_check", "started", "max_operand_bits", "max_cache_entries",
                      "max_operations", "max_elapsed_ms"):
            with self.subTest(field=field):
                self.refused_mutation(lambda sim, ledger: setattr(sim.work, field, Foreign()))
                self.assertEqual(calls, [])

    def test_original_exception_identity_wins_and_consumption_is_retained(self):
        owner = {}
        sentinel = RuntimeError("original mutation and exception")
        def check():
            if "sim" in owner and owner["ledger"].stage == "torque_aggregate_begin":
                owner["count"] = owner["ledger"].operations
                owner["ledger"].operations = 0
                raise sentinel
        sim, ledger = simulator(source("p01-spin-up"), check=check)
        owner.update(sim=sim, ledger=ledger)
        accepted = sim.state
        with self.assertRaises(RuntimeError) as caught:
            sim.advance(F(1))
        self.assertIs(caught.exception, sentinel)
        self.assertIs(ledger.callback_error, sentinel)
        self.assertEqual(ledger.operations, owner["count"])
        self.assertIs(sim.state, accepted)

    def test_preflight_completion_addition_is_charged_and_requires_original_work(self):
        sim, _ = simulator(source("p04-overlap"))
        before = sim.work.counts.get("exact_add", 0)
        torque_record_bound(sim.model, horizon=F(3), check=sim.work.tick)
        self.assertEqual(sim.work.counts.get("exact_add", 0) - before, 2)
        with self.assertRaises(OntoKinError):
            torque_record_bound(sim.model, horizon=F(3))

    def test_public_evaluator_closures_keep_the_original_numeric_work(self):
        for operation in (construct, evaluate, evaluate_prefix, preflight):
            with self.subTest(operation=operation.__name__):
                sim, ledger = simulator(source("p04-overlap"))
                before = sim.work.counts.get("exact_add", 0)
                if operation is evaluate_prefix:
                    result = operation(sim.model, "3", work=sim.work)
                    self.assertIsNone(result["failure"])
                else:
                    result = operation(sim.model, work=sim.work)
                    self.assertEqual(result["outcome"], "valid")
                self.assertIs(sim.work.execution_budget, ledger)
                if operation is not construct:
                    self.assertGreater(sim.work.counts.get("exact_add", 0), before)

    def test_non_torque_budget_callback_semantics_are_unchanged(self):
        owner = {}
        def check():
            owner["ledger"].operations = 0
        ledger = SharedExecutionBudget(check=check)
        owner["ledger"] = ledger
        ledger.operations = 5
        ledger.tick()
        self.assertEqual(ledger.operations, 1)

    def native_clock_ledger(self, host_clock):
        from ontokin.budget_agent import _BudgetCheck
        reader = object.__new__(_BudgetCheck)
        reader._host_clock = host_clock
        reader._clock_failed = False
        reader._last_clock = None
        ledger = SharedExecutionBudget(check=lambda: None, clock=reader._read_clock)
        reader.execution_budget = ledger
        admit_entry_budget(source("p01-spin-up").entry, ledger, profile="torque-0.1")
        return reader, ledger

    def test_only_exact_builtin_agent_clock_avoids_duplicate_source_scan(self):
        for clock, expected in ((time.monotonic, 1), (lambda: 100.0, 2)):
            with self.subTest(clock=clock):
                reader, ledger = self.native_clock_ledger(clock)
                visits = []
                ledger._torque_context_guard = lambda: visits.append(ledger.operations)
                before = ledger.operations
                ledger.tick()
                self.assertEqual(len(visits), expected)
                self.assertEqual(ledger.operations, before + 1)
                self.assertIs(ledger._clock.__self__, reader)
                self.assertIs(reader._host_clock, clock)

    def test_native_agent_clock_owner_cannot_change_during_original_poll(self):
        for field, value in (("_host_clock", lambda: 100.0), ("_clock_failed", True),
                             ("_last_clock", object()), ("_last_clock", 1 << 2000)):
            with self.subTest(field=field, value_type=type(value)):
                reader, ledger = self.native_clock_ledger(time.monotonic)
                original = lambda: setattr(reader, field, value)
                ledger.check = original
                before = ledger.operations
                with self.assertRaises(OntoKinError) as caught:
                    ledger.tick()
                self.assertEqual(caught.exception.diagnostic.details["budget_reason"], "execution_context_required")
                self.assertEqual(ledger.operations, before)
                self.assertIs(ledger.check, original)

    def test_native_clock_transitive_builtin_and_elapsed_method_cannot_be_replaced(self):
        for target in ("isfinite", "elapsed_ms"):
            with self.subTest(target=target):
                _, ledger = self.native_clock_ledger(time.monotonic)
                original = math.isfinite
                calls = []
                def foreign(*args):
                    calls.append(args)
                    return True if target == "isfinite" else 0.0
                def callback():
                    if target == "isfinite":
                        math.isfinite = foreign
                    else:
                        ledger.elapsed_ms = foreign
                ledger.check = callback
                before = ledger.operations
                try:
                    with self.assertRaises(OntoKinError) as caught:
                        ledger.tick()
                    self.assertEqual(caught.exception.diagnostic.details["budget_reason"], "execution_context_required")
                    self.assertEqual(ledger.operations, before)
                    self.assertEqual(calls, [])
                finally:
                    math.isfinite = original

    def test_original_poll_can_read_original_clock_and_keeps_full_second_scan(self):
        _, ledger = self.native_clock_ledger(time.monotonic)
        ledger.check = lambda: ledger.elapsed_ms()
        visits = []
        ledger._torque_context_guard = lambda: visits.append(ledger.operations)
        before = ledger.operations
        ledger.tick()
        self.assertEqual(len(visits), 2)
        self.assertEqual(ledger.operations, before + 1)

    def test_native_clock_function_object_cannot_change_code_or_defaults(self):
        from ontokin.budget_agent import _NATIVE_BUDGET_READ_CLOCK
        for function in (_NATIVE_BUDGET_READ_CLOCK, SharedExecutionBudget.elapsed_ms):
            for field in ("__code__", "__defaults__", "__kwdefaults__"):
                with self.subTest(function=function.__name__, field=field):
                    reader, ledger = self.native_clock_ledger(time.monotonic)
                    original = getattr(function, field)
                    def foreign(self):
                        self._unexpected_native_execution = True
                        return 0.0
                    replacement = (foreign.__code__ if field == "__code__" else
                                   (None,) if field == "__defaults__" else {"foreign": None})
                    ledger.check = lambda: setattr(function, field, replacement)
                    before = ledger.operations
                    try:
                        with self.assertRaises(OntoKinError) as caught:
                            ledger.tick()
                        self.assertEqual(caught.exception.diagnostic.details["budget_reason"], "execution_context_required")
                        self.assertEqual(ledger.operations, before)
                        self.assertFalse(hasattr(reader, "_unexpected_native_execution"))
                        self.assertFalse(hasattr(ledger, "_unexpected_native_execution"))
                    finally:
                        setattr(function, field, original)

    def test_native_clock_global_resolutions_cannot_add_late_user_code(self):
        import ontokin.budget_agent as agent
        for name in ("type", "int", "float"):
            with self.subTest(name=name):
                _, ledger = self.native_clock_ledger(time.monotonic)
                calls = []
                original = agent.__dict__.get(name)
                present = name in agent.__dict__
                def foreign(*args):
                    calls.append(args)
                    return type(args[0])
                ledger.check = lambda: setattr(agent, name, foreign)
                before = ledger.operations
                try:
                    with self.assertRaises(OntoKinError) as caught:
                        ledger.tick()
                    self.assertEqual(caught.exception.diagnostic.details["budget_reason"], "execution_context_required")
                    self.assertEqual(ledger.operations, before)
                    self.assertEqual(calls, [])
                finally:
                    if present:
                        setattr(agent, name, original)
                    else:
                        delattr(agent, name)

    def test_native_clock_fields_cannot_be_replaced_by_class_descriptors(self):
        from ontokin.budget_agent import _BudgetCheck
        for native, name in ((_BudgetCheck, "_host_clock"), (_BudgetCheck, "_clock_failed"),
                             (_BudgetCheck, "_last_clock"), (SharedExecutionBudget, "_clock"),
                             (SharedExecutionBudget, "started")):
            with self.subTest(native=native.__name__, name=name):
                _, ledger = self.native_clock_ledger(time.monotonic)
                calls = []
                def foreign(owner):
                    calls.append(name)
                    return vars(owner)[name]
                ledger.check = lambda: setattr(native, name, property(foreign))
                before = ledger.operations
                try:
                    with self.assertRaises(OntoKinError) as caught:
                        ledger.tick()
                    self.assertEqual(caught.exception.diagnostic.details["budget_reason"], "execution_context_required")
                    self.assertEqual(ledger.operations, before)
                    # Ledger metadata reads may observe a replacement before
                    # admission, but the elapsed-time/reader body cannot run.
                    if native is _BudgetCheck:
                        self.assertEqual(calls, [])
                finally:
                    delattr(native, name)

    def test_retained_native_views_never_call_replacement_value_equality(self):
        class Foreign:
            def __eq__(self, other):
                raise AssertionError("Foreign comparison must not run")
        self.refused_mutation(lambda sim, ledger: sim.model.objects["sibling"].physical.__setitem__("mass", Foreign()))

    def test_public_output_preflight_cannot_adopt_a_callback_mutated_source(self):
        for operation in (construct, evaluate, evaluate_prefix, preflight, torque_record_bound):
            with self.subTest(operation=operation.__name__):
                owner, visits = {}, []
                def callback():
                    if "compiler" in owner and not visits:
                        visits.append(ledger.operations)
                        owner["compiler"].model.events[1].events.clear()
                bundle = source("p04-overlap")
                ledger = SharedExecutionBudget(check=callback)
                admit_entry_budget(bundle.entry, ledger, profile="torque-0.1")
                compiler = compile_construction(bundle, execution_budget=ledger)
                self.assertIsNone(ledger._torque_context_guard)
                owner["compiler"] = compiler
                with self.assertRaises(OntoKinError) as caught:
                    if operation is evaluate_prefix:
                        operation(compiler.model, "3", work=compiler.reach_work)
                    elif operation is torque_record_bound:
                        operation(compiler.model, work=compiler.reach_work, check=compiler.reach_work.tick)
                    else:
                        operation(compiler.model, work=compiler.reach_work)
                self.assertEqual(caught.exception.diagnostic.details["budget_reason"], "execution_context_required")
                self.assertEqual(len(visits), 1)
                if operation is torque_record_bound:
                    self.assertIsNone(ledger._torque_context_guard)
                else:
                    self.assertIsNotNone(ledger._torque_context_guard)
                self.assertIs(ledger.check, callback)


if __name__ == "__main__":
    unittest.main()
