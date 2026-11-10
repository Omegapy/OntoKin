"""Host API for the explicitly selected C191 prototype."""
from __future__ import annotations

import platform
from pathlib import Path
import sys
import uuid

from .common import (Budget, Failure, LEVELS, OutputPathConflict, atomic_write_output,
                     canonical_bytes, check_output_path, load_contract, sha256)
from .source import Source


def _envelope(attempt_id, budget):
    return {
        "binding": "glb-guided-contact-0.1", "attempt_id": attempt_id,
        "source_sha256": None, "canonical_input_sha256": None,
        "successful": False, "committed": False, "accepted_revision": None,
        "previous_revision": None, "levels": {key: False for key in LEVELS},
        "diagnostics": [], "cost": budget.cost(),
        "runtime": {"executable_sha256": None, "build_hash": None, "platform": platform.platform()},
        "artifact_directory": None, "artifacts": {},
    }


def _failure(result, error, contract):
    rule = contract["diagnostics"][error.code]
    result["diagnostics"] = [{"code": error.code, "phase": rule["phase"],
                              "message": error.message, "span": error.span,
                              "blocked_levels": rule["blocked_levels"]}]
    result["successful"] = False
    result["committed"] = False
    for level in rule["blocked_levels"]:
        result["levels"][level] = False
    return result


def _read_source(source, budget, contract, result):
    path = Path(source)
    try:
        with path.open("rb") as stream:
            data = stream.read(contract["backend"]["limits"]["source_bytes"] + 1)
    except OSError as exc:
        raise Failure("E_IO", str(exc)) from exc
    if len(data) > contract["backend"]["limits"]["source_bytes"]:
        # The exact full revision is deliberately unavailable: do not pretend
        # this bounded prefix's digest identifies the oversized input.
        raise Failure("E_RESOURCE_LIMIT", "Source exceeds the 65536-byte admission ceiling")
    result["source_sha256"] = sha256(data)
    context = Source(path, data, budget, contract)
    context.parse()
    result["levels"]["represented"] = True
    context.validate()
    result["canonical_input_sha256"] = context.canonical_sha
    return context


def validate_source(source, *, host_max_operations=100000, host_max_elapsed_ms=30000,
                    canonical_out=None, result_path=None, cancel_file=None):
    """Check source without changing any accepted store state."""
    budget = Budget(host_max_operations, host_max_elapsed_ms, cancel_file)
    contract = load_contract()
    result = _envelope(uuid.uuid4().hex, budget)
    context = None
    try:
        context = _read_source(source, budget, contract, result)
        if canonical_out is not None:
            check_output_path(canonical_out, protected_files=(source,), other_output=result_path)
        if result_path is not None:
            check_output_path(result_path, protected_files=(source,), other_output=canonical_out)
        if canonical_out is not None:
            target = Path(canonical_out)
            target.parent.mkdir(parents=True, exist_ok=True)
            atomic_write_output(target, context.canonical_bytes)
        result["successful"] = True
    except Failure as exc:
        _failure(result, exc, contract)
    except OSError as exc:
        _failure(result, Failure("E_IO", str(exc), context.span(context.header_range) if context else None), contract)
    result["cost"] = budget.cost()
    if result_path:
        try:
            check_output_path(result_path, protected_files=(source,), other_output=canonical_out)
            atomic_write_output(result_path, canonical_bytes(result))
        except OutputPathConflict as exc:
            # Keep an earlier source rejection; an unsafe auxiliary receipt
            # must not replace its diagnostic or mutate the admitted bytes.
            if not result["diagnostics"]:
                _failure(result, Failure("E_IO", str(exc), context.span(context.header_range) if context else None), contract)
            print("C191 optional validation receipt suppressed: " + str(exc), file=sys.stderr)
        except OSError as exc:
            _failure(result, Failure("E_IO", str(exc), context.span(context.header_range) if context else None), contract)
    return result


def run(source, *, store, blender, host_max_operations=100000, host_max_elapsed_ms=30000,
        expected_revision=None, cancel_file=None, reopen=None, result_path=None,
        hooks=None):
    """Execute and atomically publish; hooks are trusted-host fault probes only."""
    from .transaction import run_transaction
    return run_transaction(source, store=store, blender=blender,
                           host_max_operations=host_max_operations,
                           host_max_elapsed_ms=host_max_elapsed_ms,
                           expected_revision=expected_revision, cancel_file=cancel_file,
                           reopen=reopen, result_path=result_path, hooks=hooks)
