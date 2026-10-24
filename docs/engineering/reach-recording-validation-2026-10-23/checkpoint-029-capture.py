#!/usr/bin/env python3
"""Retain original P09 reader bytes at two external pass-through boundaries.

The product request keeps its failed status and exit code. Captures are serialized
only after the unchanged stock builder returns; they are not accepted artifacts.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import platform
import sys
import traceback
from types import MethodType


def ratio(value):
    assert type(value) is Fraction
    assert type(value.numerator) is int and type(value.denominator) is int
    assert value.denominator > 0
    assert max(value.numerator.bit_length(), value.denominator.bit_length()) <= 32768
    return {"numerator": value.numerator, "denominator": value.denominator}


def fields(value):
    if value is None:
        return None
    assert type(value) is tuple and len(value) == 2
    assert all(type(item) is int for item in value) and value[1] > 0
    assert max(item.bit_length() for item in value) <= 32768
    return {"numerator": value[0], "denominator": value[1]}


def decimal(value):
    # Bounded decimal serialization after the request, without changing Python's
    # global integer conversion policy during this or any later product request.
    if not value:
        return "0"
    sign = "-" if value < 0 else ""
    value = abs(value)
    chunks = []
    while value:
        value, remainder = divmod(value, 10 ** 1000)
        chunks.append(remainder)
    return sign + str(chunks[-1]) + "".join(f"{part:01000d}" for part in reversed(chunks[:-1]))


def serializable(value):
    if type(value) is dict:
        if set(value) == {"numerator", "denominator"} and all(type(v) is int for v in value.values()):
            return {name: decimal(number) for name, number in value.items()}
        return {name: serializable(item) for name, item in value.items()}
    if type(value) in (list, tuple):
        return [serializable(item) for item in value]
    return value


def write_json(path, value):
    with Path(path).open("x") as stream:
        json.dump(serializable(value), stream, indent=2, allow_nan=False)
        stream.write("\n")


def record(work):
    return {"operations": work.operations, "counts": dict(work.counts),
            "cache_entries": len(work._cache)}


def descriptor(path):
    raw = Path(path).read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def callable_name(value):
    if value is None:
        return None
    fn = getattr(value, "__func__", value)
    return {"module": getattr(fn, "__module__", None),
            "qualname": getattr(fn, "__qualname__", type(fn).__qualname__),
            "bound_owner_type": type(value.__self__).__qualname__ if type(value) is MethodType else None}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    root = args.repo.resolve()
    output = args.output_dir.resolve()
    assert not output.exists() and not output.is_relative_to(root)
    output.mkdir(parents=True)
    sys.path.insert(0, str(root))
    from tools.build_reach_source_artifacts import build
    from ontokin import gltf, reach_conformance as rc
    from ontokin.construction import ConstructionBudget
    from ontokin.reach_numeric import ReachExecutionWork

    assert sys.gettrace() is None and sys.getprofile() is None
    validate_original = gltf.validate_export
    flush_original = rc._CertificateBatch.flush
    dispatch = [(gltf, "export_glb", gltf.export_glb),
                (ConstructionBudget, "tick", ConstructionBudget.tick),
                (ConstructionBudget, "exceeded", ConstructionBudget.exceeded),
                (ReachExecutionWork, "charge", ReachExecutionWork.charge),
                (ReachExecutionWork, "guard_bits", ReachExecutionWork.guard_bits),
                (rc._CertificateBatch, "maximum", rc._CertificateBatch.maximum)]
    dispatch += [(rc._Bounds, name, getattr(rc._Bounds, name)) for name in
                 ("add", "mul", "div", "square", "op", "bits", "tick", "value", "compare", "total")]
    retained = {"reader_calls": 0, "flush_calls": 0}
    snapshots = []

    def capture_validate_export(*positional, **keywords):
        retained["reader_calls"] += 1
        assert retained["reader_calls"] == 1
        assert len(positional) == 2 and type(positional[0]) is bytes
        assert len(positional[0]) <= 64 * 1024 * 1024
        work = keywords["work"]
        assert type(work) is ReachExecutionWork
        external = work.external_check
        assert type(external) is MethodType and external.__func__ is ConstructionBudget.tick
        budget = external.__self__
        assert type(budget) is ConstructionBudget
        retained.update(data=positional[0], model=positional[1], options=keywords["options"],
                        work=work, check=keywords["check"], external=external,
                        observer=work._source_after_charge, budget=budget,
                        construction_check=budget.check, work_at_reader_entry=record(work),
                        shared_operations_at_reader_entry=budget.operations,
                        budget_limits=dict(budget.limits),
                        work_limits={name: getattr(work, name) for name in
                                     ("max_operations", "max_elapsed_ms", "max_operand_bits", "max_cache_entries")})
        try:
            return validate_original(*positional, **keywords)
        except BaseException as error:
            retained["error"] = error
            retained["same_callback_error_at_reader_exit"] = error is work.callback_error
            raise
        finally:
            retained["reader_owner_preserved"] = keywords["work"] is work
            retained["reader_arguments_preserved"] = (positional[0] is retained["data"] and
                positional[1] is retained["model"] and keywords["options"] is retained["options"] and
                keywords["check"] is retained["check"])
            retained["reader_external_preserved"] = work.external_check is external
            retained["reader_observer_restored"] = work._source_after_charge is retained["observer"]

    def capture_flush(batch):
        retained["flush_calls"] += 1
        assert retained["flush_calls"] <= 2
        assert type(batch) is rc._CertificateBatch and type(batch.groups) is dict
        assert len(batch.groups) <= 64
        arithmetic = batch.arithmetic
        work = arithmetic.work
        assert work is retained["work"]
        external, observer = work.external_check, work._source_after_charge
        groups = []
        for ordinal, (key, group) in enumerate(batch.groups.items(), 1):
            assert type(key) is tuple and len(key) == len(rc._NUMERIC_CERTIFICATE_KEYS) == 21
            assert type(group) is dict and tuple(group["quantities"]) == rc._NUMERIC_CERTIFICATE_KEYS
            assert type(group["minima"]) is dict and len(group["minima"]) <= 21
            assert all(type(value) in (int, float) for value in key)
            thresholds = group.get("thresholds")
            threshold_record = None
            if thresholds is not None:
                assert type(thresholds) is rc._CertificateThresholds
                assert len(thresholds.fields) == 21
                assert len(thresholds.domains) <= 21 and len(thresholds.minimum_fields) <= 21
                assert type(thresholds.domains) is dict
                assert all(type(value) is tuple and len(value) == 4 and
                           all(type(item) is int and 0 <= item <= 32768 for item in value)
                           for value in thresholds.domains.values())
                assert set(thresholds.extent_fields) == {"width", "stored_width", "magnitude"}
                threshold_record = {"used": thresholds.used, "enabled": thresholds.enabled,
                    "fields": [fields(value) for value in thresholds.fields],
                    "extent_fields": {name: {"value": ratio(value), "fields": fields(pair)}
                                      for name, (value, pair) in thresholds.extent_fields.items()},
                    "minimum_fields": {name: {"value": ratio(value), "fields": fields(pair)}
                                       for name, (value, pair) in thresholds.minimum_fields.items()},
                    "domains": dict(thresholds.domains)}
            groups.append({"ordinal": ordinal,
                "key": [{"type": type(value).__name__, "value": value} for value in key],
                "quantities": {name: ratio(value) for name, value in group["quantities"].items()},
                "width": ratio(group["width"]), "stored_width": ratio(group["stored_width"]),
                "magnitude": ratio(group["magnitude"]),
                "minima": {name: ratio(value) for name, value in group["minima"].items()},
                "minima_order": list(group["minima"]), "thresholds": threshold_record})
        entry = {"ordinal": retained["flush_calls"], "numeric_keys": list(rc._NUMERIC_CERTIFICATE_KEYS),
                 "groups": groups, "work_at_entry": record(work),
                 "shared_operations_at_entry": retained["budget"].operations,
                 "position_tolerance": ratio(batch.position_tolerance),
                 "rotation_tolerance": ratio(batch.rotation_tolerance),
                 "max_position": ratio(batch.max_position), "max_rotation": ratio(batch.max_rotation),
                 "thresholds_enabled": batch.thresholds_enabled,
                 "restart_requested": batch.restart_requested}
        snapshots.append(entry)
        try:
            return flush_original(batch)
        finally:
            entry["identity_checks"] = {"work_preserved": batch.arithmetic is arithmetic and arithmetic.work is work,
                "external_preserved": work.external_check is external,
                "observer_preserved_within_flush": work._source_after_charge is observer}

    report = None
    driver_error = None
    try:
        gltf.validate_export = capture_validate_export
        rc._CertificateBatch.flush = capture_flush
        report = build(output / "stock", ("P09",), 1.0)
    except BaseException as error:
        driver_error = {"type": type(error).__name__, "message": str(error), "traceback": traceback.format_exc()}
    finally:
        gltf.validate_export = validate_original
        rc._CertificateBatch.flush = flush_original

    # All serialization and hashing below occur after the capped request ended.
    result = {"schema_version": "ontokin.p09-reader-input-capture/0.1",
        "created_at": datetime.now(timezone.utc).isoformat(), "status": "capture_failed",
        "product_request_status": report.get("status") if report else "driver_failed",
        "accepted_artifact": False, "release_acceptance": False,
        "scope": "Observed unvalidated reader input from an original failed request; no successful ExportResult",
        "reader_calls": retained["reader_calls"], "flush_calls": retained["flush_calls"],
        "driver": descriptor(Path(__file__).resolve()),
        "actual_driver_command": [sys.executable, str(Path(__file__).resolve()), *sys.argv[1:]],
        "stock_api_call": {"callable": "tools.build_reach_source_artifacts.build",
            "output": str(output / "stock"), "cases": ["P09"], "fps": 1.0},
        "stock_report_command_note": "The unchanged builder synthesizes report.command from its own filename and this driver's argv. The actual replay command is actual_driver_command and the external command receipt; the actual API call is stock_api_call.",
        "execution": {"python": sys.version, "executable": sys.executable, "platform": platform.platform()},
        "identity_checks": {"validate_export_restored": gltf.validate_export is validate_original,
            "flush_restored": rc._CertificateBatch.flush is flush_original,
            "native_dispatch_preserved": all(getattr(owner, name) is value for owner, name, value in dispatch),
            "no_trace_hook": sys.gettrace() is None, "no_profile_hook": sys.getprofile() is None}}
    if driver_error:
        result["driver_error"] = driver_error
    if report:
        result.update(source_commit=report.get("source_commit"), source_tree=report.get("source_tree"),
                      inputs_stable=report.get("inputs_stable"))
    if retained.get("data") is not None:
        raw = retained["data"]
        with (output / "unvalidated-reader-input.glb").open("xb") as stream:
            stream.write(raw)
        result["artifact"] = {"path": "unvalidated-reader-input.glb", "bytes": len(raw),
                              "sha256": hashlib.sha256(raw).hexdigest()}
        work, budget = retained["work"], retained["budget"]
        result.update(work_at_reader_entry=retained["work_at_reader_entry"],
            shared_operations_at_reader_entry=retained["shared_operations_at_reader_entry"],
            work_after_request=record(work), shared_operations_after_request=budget.operations,
            budget_limits=retained["budget_limits"], work_limits=retained["work_limits"],
            original_request={"case_id": "P09", **(report["deliveries"][0]["options"]
                if report and report.get("deliveries") else
                {"end": "3", "fps": 1.0, "helpers": False, "position_tolerance_m": .001,
                 "rotation_tolerance_rad": .001, "time_tolerance_s": .000001})},
            callbacks={"external": callable_name(work.external_check),
                "construction_check": callable_name(budget.check),
                "observer_at_reader_entry": callable_name(retained["observer"]),
                "observer_after_request": callable_name(work._source_after_charge)})
        result["identity_checks"].update({name: retained.get(name, False) for name in
            ("reader_owner_preserved", "reader_arguments_preserved", "reader_external_preserved",
             "reader_observer_restored", "same_callback_error_at_reader_exit")})
        result["identity_checks"].update(external_callback_preserved=work.external_check is retained["external"],
            native_callback_owner_preserved=work.external_check.__self__ is budget,
            construction_check_preserved=budget.check is retained["construction_check"],
            observer_restored_after_request=work._source_after_charge is retained["observer"],
            callback_error_preserved=retained.get("error") is work.callback_error,
            work_limits_unchanged=all(getattr(work, name) == value for name, value in retained["work_limits"].items()),
            budget_limits_unchanged=budget.limits == retained["budget_limits"])
        if retained.get("error") is not None:
            error = retained["error"]
            result["exception"] = {"type": type(error).__name__, "message": str(error),
                "cause": None if error.__cause__ is None else type(error.__cause__).__name__,
                "context": None if error.__context__ is None else type(error.__context__).__name__,
                "suppress_context": error.__suppress_context__,
                "frames": [{"file": frame.filename, "line": frame.lineno, "function": frame.name}
                           for frame in traceback.extract_tb(error.__traceback__)]}
        if (report and report["status"] == "failed" and report.get("inputs_stable") and
                retained["reader_calls"] == retained["flush_calls"] == 1 and snapshots and
                all(result["identity_checks"].values()) and
                all(all(s["identity_checks"].values()) for s in snapshots)):
            result["status"] = "captured_failed_request"
    write_json(output / "flush-snapshots.json", {"schema_version": "ontokin.certificate-flush-capture/0.1",
               "scope": "Observed reader state only; minima are not independently certified source values",
               "snapshots": snapshots})
    write_json(output / "capture.json", result)
    print(json.dumps({"capture_status": result["status"], "product_request_status": result["product_request_status"],
                      "shared_operations": result.get("shared_operations_after_request"),
                      "captured_bytes": result.get("artifact", {}).get("bytes")}), flush=True)
    return 0 if report and report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
