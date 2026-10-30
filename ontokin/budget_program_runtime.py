"""Agent/0.7 operations paid by one request-owned execution ledger.

This adapter has no store or host policy of its own. The service supplies a
request context that admits one immutable candidate and retains the original
ledger through source preparation, construction, evaluation and delivery.
"""
from __future__ import annotations

from . import program_runtime as runtime
from .agent_runtime import _Interrupt
from .execution_budget import DEFAULT_LIMITS, SharedExecutionBudget, budget_error
from .profile_capabilities import BUDGET_PROFILE, EXECUTION_PROFILES


class ExecutionProgramBudget(runtime._Budget):
    """Keep fixed output limits while forwarding every work charge."""

    def __init__(self, budgets=None, check=None, *, profile=BUDGET_PROFILE):
        if not isinstance(profile, str) or profile not in EXECUTION_PROFILES:
            raise ValueError("Unknown execution-budget program profile.")
        ledger = getattr(check, "execution_budget", None)
        if not isinstance(ledger, SharedExecutionBudget) or not callable(getattr(check, "admit", None)):
            budget_error("execution_context_required",
                         "Agent/0.7 requires a request-owned execution context.")
        incoming = {} if budgets is None else budgets
        if type(incoming) is not dict or set(incoming) - set(runtime.MAX_BUDGETS):
            budget_error("invalid_declaration", "Unknown program work budget.")
        caps = {name: value for name, value in incoming.items() if name in DEFAULT_LIMITS}
        if caps != dict(ledger.caller_caps):
            budget_error("execution_context_required",
                         "Runtime execution caps must match the request's admitted context.")
        self.context = check
        self.execution_budget = ledger
        self.profile = profile
        self.started = ledger.started
        self.limits = {**runtime.MAX_BUDGETS, **ledger.limits}
        for name, value in incoming.items():
            if name in DEFAULT_LIMITS:
                continue
            ceiling = runtime.MAX_BUDGETS[name]
            if type(value) is not int or not 1 <= value <= ceiling:
                budget_error("invalid_declaration", "Invalid fixed program budget.",
                             budget=name, limit=ceiling)
            self.limits[name] = value

    @property
    def operations(self):
        return self.execution_budget.operations

    def tick(self):
        try:
            self.execution_budget.tick()
        except BaseException as error:
            # Preserve a host cancellation even when it uses the same exception
            # family as a normal source or materialization failure.
            if error is self.execution_budget.callback_error:
                raise _Interrupt(error) from None
            raise


class BudgetProgramRuntime:
    """Explicit .7 operations without registering a legacy service binding."""

    profile = BUDGET_PROFILE

    def _call(self, function, source, **kwargs):
        ledger = getattr(kwargs.get("check"), "execution_budget", None)
        try:
            result = function(source, profile=self.profile, **kwargs)
        except BaseException:
            if ledger is not None and ledger.callback_error is not None:
                raise ledger.callback_error from None
            raise
        if ledger is not None and ledger.callback_error is not None:
            raise ledger.callback_error from None
        return result

    def validate_revision(self, source, **kwargs):
        return self._call(runtime.validate_revision, source, **kwargs)

    def evaluate_revision(self, source, **kwargs):
        return self._call(runtime.evaluate_revision, source, **kwargs)

    def inspect_revision(self, source, **kwargs):
        return self._call(runtime.inspect_revision, source, **kwargs)

    def source_index(self, source, **kwargs):
        return self._call(runtime.source_index, source, **kwargs)

    def apply_patches(self, source, patches, **kwargs):
        return self._call(runtime.apply_patches, source, patches=patches, **kwargs)

    def compile_program(self, source, **kwargs):
        return self._call(runtime.compile_program, source, **kwargs)

    def prepare_delivery(self, source, **kwargs):
        return self._call(runtime.prepare_delivery, source, **kwargs)

    def identity_map(self, source, *, budgets=None, check=None):
        """Return every nominal occurrence identity for atomic acceptance.

        The service retains this complete map with an accepted revision. A
        later edit compares against that retained map, so lowering a source's
        budget never requires executing the old, more demanding declaration.
        Pagination and user-facing result-item limits do not truncate the map.
        Fixed object/value limits and the request's actual ledger still apply.
        """
        try:
            budget = ExecutionProgramBudget(budgets, check, profile=self.profile)
            check.admit(source)
            budget.limits.update(budget.execution_budget.limits)
            cached = getattr(check, "_budget_program_compiler", None)
            compiler = (cached[1] if cached is not None and cached[0] == source.program_revision
                        and cached[1].model.profile == self.profile
                        else runtime._compile(source, budget))
            budget.execution_budget.stage = "identity_validation"
            records = []
            for path, obj in compiler.model.objects.items():
                budget.tick()
                definition_id = compiler.occurrence_provenance[path]["definition_id"]
                records.append({"element_id": list(obj.element_id),
                                "definition_id": list(definition_id)})
            records.sort(key=lambda item: tuple(item["element_id"]))
            return budget.json(records)
        except _Interrupt as interrupted:
            raise interrupted.error from None
