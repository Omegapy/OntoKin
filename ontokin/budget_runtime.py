"""One authorized source 0.7 execution through independently checked GLB bytes.

This direct path has no durable Agent lifecycle. The embedding host supplies
policy; the source and caller can only request or reduce an execution budget.
No file is published until all source, recording and supplied-byte checks pass.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from . import __version__
from .bundle import ProgramBundle
from .construction import compile_construction
from .diagnostics import OntoKinError
from .execution_budget import HostPolicy, SharedExecutionBudget, admit_entry_budget
from .json_limits import JSONLimitError, measure_json
from .profile_capabilities import BUDGET_PROFILE, EXTRUSION_PROFILE, HOLES_PROFILE, RING_LOFT_PROFILE, FRAMED_LOFT_PROFILE, POCKETS_PROFILE, TEXTURE_PROFILE, KEYED_TRANSFORM_PROFILE, KEYED_REDUCTION_PROFILE, KEYED_FILTER_PROFILE, KEYED_REDUCTION_PROFILES, KEYED_TRANSFORM_PROFILES, POCKETS_PROFILES, EXECUTION_PROFILES
from .program_diagnostics import diagnostic_dict
from .scene import ExportOptions


TARGET = "ontokin.glb/0.7"


class _CallerInterrupt(BaseException):
    """Carry host cancellation past internal error translators unchanged."""

    def __init__(self, error: BaseException):
        self.error = error


@dataclass(frozen=True)
class BudgetedExport:
    """A success contains verified bytes; a failure contains a bounded receipt."""

    data: bytes | None
    report: dict


def execute_budgeted_export(source: ProgramBundle, *, policy: HostPolicy | None = None,
                            caller_caps: dict | None = None,
                            options: ExportOptions | None = None,
                            check: Callable[[], None] | None = None,
                            clock=None, profile=BUDGET_PROFILE) -> BudgetedExport:
    """Run one immutable entry under an independently supplied host policy.

Caller cancellation propagates with the original exception identity. Expected
source, authorization, numeric and resource failures return no artifact bytes.
The receipt never authorizes a later execution or an independent reader.
"""
    if not isinstance(profile, str) or profile not in EXECUTION_PROFILES:
        raise ValueError("Unknown execution-budget source profile.")
    target = {BUDGET_PROFILE: TARGET, EXTRUSION_PROFILE: "ontokin.glb/0.8",
              HOLES_PROFILE: "ontokin.glb/0.9", RING_LOFT_PROFILE: "ontokin.glb/0.10", FRAMED_LOFT_PROFILE: "ontokin.glb/0.11", POCKETS_PROFILE: "ontokin.glb/0.12", TEXTURE_PROFILE: "ontokin.glb/0.13", KEYED_TRANSFORM_PROFILE: "ontokin.glb/0.14", KEYED_REDUCTION_PROFILE: "ontokin.glb/0.15", KEYED_FILTER_PROFILE: "ontokin.glb/0.16"}[profile]
    language_version = {BUDGET_PROFILE: "0.7", EXTRUSION_PROFILE: "0.8", HOLES_PROFILE: "0.9", RING_LOFT_PROFILE: "0.10", FRAMED_LOFT_PROFILE: "0.11", POCKETS_PROFILE: "0.12", TEXTURE_PROFILE: "0.13", KEYED_TRANSFORM_PROFILE: "0.14", KEYED_REDUCTION_PROFILE: "0.15", KEYED_FILTER_PROFILE: "0.16"}[profile]
    if not isinstance(source, ProgramBundle):
        raise TypeError("source must be a sealed ProgramBundle.")
    ledger = None
    prefix = None
    achieved = None
    from .agent import implementation_identity
    identity = {"schema_version": "ontokin.source-execution/0.1",
                "implementation": "ontokin-reference", "version": __version__,
                "language_version": language_version, "profile": profile,
                "target_contract": target, "requested_level": "delivered",
                "source_revision": source.entry.revision,
                "program_revision": source.program_revision,
                "implementation_identity": implementation_identity()}

    def valid_prefix():
        if prefix is None:
            return None
        return {"program_revision": source.program_revision,
                "valid_until_seconds": prefix["valid_until_seconds"],
                "valid_until_side": prefix["valid_until_side"],
                "status": "valid" if prefix["failure"] is None else "failed"}

    def caller_check():
        try:
            check()
        except BaseException as error:
            raise _CallerInterrupt(error) from None

    try:
        ledger = SharedExecutionBudget(policy, caller_caps,
                                       check=caller_check if check is not None else None, clock=clock)
        admit_entry_budget(source.entry, ledger, profile=profile)
        ledger.stage = "construction"
        compiler = compile_construction(source, execution_budget=ledger)
        achieved = "represented"
        # The ordinary source-support decision still applies to this profile.
        from .program_runtime import _support
        _support(compiler)
        options = options or ExportOptions()
        endpoint = options.checked_end(compiler.model)
        from .evaluator import evaluate_prefix
        from .reach_delivery import ReachDeliveryCapture
        ledger.stage = "evaluation"
        capture = ReachDeliveryCapture(compiler.model, endpoint, work=compiler.reach_work)
        prefix = evaluate_prefix(compiler.model, endpoint, check=ledger.tick,
                                 work=compiler.reach_work, capture_observer=capture)
        if prefix["last_valid_state"] is not None:
            achieved = "constructed"
        if prefix["failure"] is not None:
            raise prefix["failure"]
        achieved = "evaluated"
        plan = capture.finish()
        ledger.stage = "recording_export_readback"
        from .gltf import export_glb
        exported = export_glb(compiler.model, options=options,
                              source_uri=source.entry.filename,
                              source_sha256=source.entry.revision,
                              target_contract=target, work=compiler.reach_work,
                              reach_plan=plan)
        report = {**exported.report, **identity, "achieved_level": "delivered",
                  "source_diagnostics": [diagnostic_dict(d, source)
                                         for d in compiler.model.diagnostics],
                  "valid_prefix": valid_prefix()}
        ledger.stage = "result"
        report["execution_budget"] = ledger.report(status="valid")
        # Reporting remains within the request and the existing JSON limits.
        measure_json(report, check=ledger.tick, work=compiler.reach_work)
        ledger.checkpoint()
        report["execution_budget"] = ledger.report(status="valid")
        return BudgetedExport(exported.data, report)
    except _CallerInterrupt as interrupted:
        raise interrupted.error from None
    except OntoKinError as error:
        if ledger is not None and error is ledger.callback_error:
            raise
        diagnostic = diagnostic_dict(error.diagnostic, source)
        reason = diagnostic["details"].get("budget_reason")
        receipt = {**identity, "outcome": diagnostic["category"],
                   "achieved_level": achieved, "diagnostics": [diagnostic],
                   "valid_prefix": valid_prefix(),
                   "execution_budget": (None if ledger is None else
                       ledger.report(status="failed", budget_reason=reason))}
        # An exhausted success allowance must still permit a bounded failure.
        # This transport guard grants no product work or artifact authority.
        try:
            measure_json(receipt)
        except JSONLimitError:
            diagnostic["details"] = {"budget_reason": reason, "details_truncated": True}
            diagnostic["related"] = []
            diagnostic["message"] = diagnostic["message"][:2048]
            try:
                measure_json(receipt)
            except JSONLimitError:
                receipt["diagnostics"] = [{"code": diagnostic["code"],
                    "category": diagnostic["category"], "message": diagnostic["message"][:512],
                    "details": {"budget_reason": reason, "diagnostic_truncated": True}}]
                measure_json(receipt)
        return BudgetedExport(None, receipt)
    except JSONLimitError as error:
        if ledger is not None and error is ledger.callback_error:
            raise
        return BudgetedExport(None, {**identity, "outcome": "resource_limit",
            "achieved_level": achieved, "valid_prefix": valid_prefix(),
            "execution_budget": None if ledger is None else ledger.report(status="failed"),
            "error": {"code": "OKL-E-RESOURCE", "message": str(error),
                      "details": error.details}})


def execute_extrusion_export(source: ProgramBundle, **kwargs) -> BudgetedExport:
    """Explicit .8 entry with the same source-authorized cumulative allowance."""
    if "profile" in kwargs:
        raise TypeError("execute_extrusion_export fixes polygon-extrusion-0.1 explicitly.")
    return execute_budgeted_export(source, profile=EXTRUSION_PROFILE, **kwargs)


def execute_holes_export(source: ProgramBundle, **kwargs) -> BudgetedExport:
    """Execute the explicit .9 source/GLB binding under the original request ledger."""
    return execute_budgeted_export(source, profile=HOLES_PROFILE, **kwargs)


def execute_ring_loft_export(source: ProgramBundle, **kwargs) -> BudgetedExport:
    """Execute explicit .10 source/GLB under the same cumulative request ledger."""
    if "profile" in kwargs:
        raise TypeError("execute_ring_loft_export fixes polygon-loft-0.1 explicitly.")
    return execute_budgeted_export(source, profile=RING_LOFT_PROFILE, **kwargs)


def execute_framed_loft_export(source: ProgramBundle, **kwargs) -> BudgetedExport:
    """Execute explicit .11 source/GLB under the cumulative request ledger."""
    if "profile" in kwargs:
        raise TypeError("execute_framed_loft_export fixes framed-polygon-loft-0.1 explicitly.")
    return execute_budgeted_export(source, profile=FRAMED_LOFT_PROFILE, **kwargs)


def execute_pockets_export(source: ProgramBundle, **kwargs) -> BudgetedExport:
    """Select source .12 and GLB/0.12 without changing earlier defaults."""
    if "profile" in kwargs:
        raise TypeError("execute_pockets_export fixes polygon-pockets-0.1 explicitly.")
    return execute_budgeted_export(source, profile=POCKETS_PROFILE, **kwargs)


def execute_texture_export(source, **kwargs):
    """Select immutable bundle .2, source .13 and GLB .13 explicitly."""
    if "profile" in kwargs:
        raise TypeError("execute_texture_export fixes textured-surfaces-0.1 explicitly.")
    return execute_budgeted_export(source, profile=TEXTURE_PROFILE, **kwargs)


def execute_keyed_transform_export(source, **kwargs):
    """Select .14 construction and recorded delivery under current authority."""
    if "profile" in kwargs:
        raise TypeError("execute_keyed_transform_export fixes keyed-transform-0.1 explicitly.")
    return execute_budgeted_export(source, profile=KEYED_TRANSFORM_PROFILE, **kwargs)


def execute_keyed_reduction_export(source, **kwargs):
    """Select .15 reduction and recorded delivery under current authority."""
    if "profile" in kwargs:
        raise TypeError("execute_keyed_reduction_export fixes keyed-reduction-0.1 explicitly.")
    return execute_budgeted_export(source, profile=KEYED_REDUCTION_PROFILE, **kwargs)


def execute_keyed_filter_export(source, **kwargs):
    if "profile" in kwargs:
        raise TypeError("execute_keyed_filter_export fixes keyed-filter-0.1 explicitly.")
    return execute_budgeted_export(source, profile=KEYED_FILTER_PROFILE, **kwargs)
