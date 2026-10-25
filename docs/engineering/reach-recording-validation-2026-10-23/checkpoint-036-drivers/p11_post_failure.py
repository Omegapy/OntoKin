#!/usr/bin/env python3
"""C036: unchanged full P11, with optional native census only after failure.

Both modes execute the same source/export statements. No product callable,
callback, observer, profiler, trace hook, or product limit is replaced. The
control collects standard failure metadata; only capture mode reads the deeper
whitelisted local fields, after the original exception has reached this driver.
"""
import argparse
from collections import OrderedDict
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import platform
import struct
import subprocess
import sys
import time
import traceback
import types

sys.dont_write_bytecode = True
COMMIT = "4ca73909f861fe4bef9694787473621c1d21c140"
TREE = "87c949b238055af1ce368c694e1d5683c8aeacde"
REVISION = "sha256:7ee1fca89536d3618b0a9a39e39ea2286be9973ce14ae148d7d8806d973ff000"
MANIFEST = "docs/language-design/planar-reach-v0.1/p11.files.json"
MANIFEST_SHA256 = "f76b4f8350b7d0adbf6e0acc2c8d48d72fc2a7c12b1d3e4a48f633e548fc98f8"
BOUNDS = {"frames": 64, "container_items": 512, "depth": 16,
          "scalar_bits": 32768, "string_characters": 4096, "native_nodes": 100000,
          "identities": 4096, "plans": 16, "plan_nodes": 128,
          "history_boundaries": 128, "json_bytes": 8 * 1024 * 1024}
F_NUM = Fraction.__dict__["_numerator"]
F_DEN = Fraction.__dict__["_denominator"]


def utc():
    return datetime.now(timezone.utc).isoformat()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def write(path, value):
    raw = (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()
    if len(raw) > BOUNDS["json_bytes"]:
        raise ValueError("C036 JSON byte bound exceeded; no truncated result is accepted")
    with path.open("xb") as stream:
        stream.write(raw)


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args]).decode().strip()


def inventory(root):
    head, tree = git(root, "rev-parse", "HEAD"), git(root, "rev-parse", "HEAD^{tree}")
    status = git(root, "status", "--porcelain=v1", "--untracked-files=all")
    if (head, tree, status) != (COMMIT, TREE, ""):
        raise ValueError("Execution checkout must be the clean exact held candidate")
    entries = subprocess.check_output(["git", "-C", str(root), "ls-files", "-s", "-z"]).decode()
    rows = []
    for line in entries.split("\0"):
        if not line:
            continue
        metadata, name = line.split("\t", 1)
        mode, expected, stage = metadata.split()
        path = root / name
        if stage != "0" or path.is_symlink() or not path.is_file():
            raise ValueError("Invalid or missing tracked input: " + name)
        raw = path.read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        actual_mode = "100755" if path.stat().st_mode & 0o111 else "100644"
        if (actual, actual_mode) != (expected, mode):
            raise ValueError("Tracked input differs from its exact Git object: " + name)
        rows.append({"path": name, "bytes": len(raw), "git_blob": actual,
                     "mode": mode, "sha256": digest(raw)})
    if git(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise ValueError("Source changed during inventory")
    return {"commit": head, "tree": tree, "status": status,
            "files": rows, "file_count": len(rows), "total_bytes": sum(x["bytes"] for x in rows)}


def typename(value):
    cls = type(value)
    return type.__getattribute__(cls, "__module__") + "." + type.__getattribute__(cls, "__qualname__")


def rawdict(value, expected=None):
    """Use only a captured native instance-dictionary descriptor, never a getter."""
    cls = type(value)
    name = typename(value)
    if expected is not None and name != expected:
        raise ValueError("Unexpected storage class: " + name)
    if not name.startswith("ontokin."):
        raise ValueError("Only declared OntoKin instance storage is read")
    for base in type.__getattribute__(cls, "__mro__"):
        descriptor = type.__getattribute__(base, "__dict__").get("__dict__")
        if type(descriptor) is types.GetSetDescriptorType:
            result = descriptor.__get__(value, cls)
            if type(result) is not dict:
                raise ValueError("Non-native instance dictionary")
            return result
    raise ValueError("No native instance dictionary for " + name)


class Native:
    def __init__(self):
        self.count = 0
        self.identities = []

    def token(self, value):
        for index, saved in enumerate(self.identities):
            if value is saved:
                return "identity-%04d" % index
        if len(self.identities) >= BOUNDS["identities"]:
            raise ValueError("Identity bound exceeded")
        self.identities.append(value)
        return "identity-%04d" % (len(self.identities) - 1)

    def integer(self, value):
        if type(value) is not int or value.bit_length() > BOUNDS["scalar_bits"]:
            raise ValueError("Native integer bound exceeded")
        return hex(value)

    def encode(self, value, depth=0):
        self.count += 1
        if depth > BOUNDS["depth"] or self.count > BOUNDS["native_nodes"]:
            raise ValueError("Native shape bound exceeded")
        cls = type(value)
        if value is None:
            return {"type": "NoneType", "value": None}
        if cls is bool:
            return {"type": "bool", "value": value}
        if cls is str:
            if len(value) > BOUNDS["string_characters"]:
                raise ValueError("Native string bound exceeded")
            return {"type": "str", "value": value}
        if cls is int:
            return {"type": "int", "hex": self.integer(value)}
        if cls is float:
            return {"type": "float", "hex": float.hex(value),
                    "bits_be": struct.pack(">d", value).hex()}
        if cls is Fraction:
            numerator, denominator = F_NUM.__get__(value, Fraction), F_DEN.__get__(value, Fraction)
            if type(denominator) is not int or denominator <= 0:
                raise ValueError("Invalid native Fraction storage")
            return {"type": "Fraction", "numerator_hex": self.integer(numerator),
                    "denominator_hex": self.integer(denominator)}
        if cls in (tuple, list):
            if len(value) > BOUNDS["container_items"]:
                raise ValueError("Native sequence bound exceeded")
            return {"type": cls.__name__, "items": [self.encode(x, depth + 1) for x in value]}
        if cls is dict:
            if len(value) > BOUNDS["container_items"]:
                raise ValueError("Native mapping bound exceeded")
            return {"type": "dict", "entries": [[self.encode(k, depth + 1), self.encode(v, depth + 1)]
                                                  for k, v in dict.items(value)]}
        # Opaque identities are never traversed and never represented by repr().
        return {"type": "opaque", "class": typename(value), "identity": self.token(value)}

    def fields(self, mapping, names):
        if type(mapping) is not dict:
            raise ValueError("Expected native field map")
        return {name: self.encode(mapping[name]) if name in mapping else {"type": "unavailable"}
                for name in names}

    def object_fields(self, value, expected, names):
        return {"class": typename(value), "identity": self.token(value),
                "fields": self.fields(rawdict(value, expected), names)}


def frames_of(error, root):
    rows, retained = [], []
    trace = error.__traceback__
    while trace is not None:
        if len(rows) >= BOUNDS["frames"]:
            raise ValueError("Traceback frame bound exceeded")
        frame, code = trace.tb_frame, trace.tb_frame.f_code
        file = Path(code.co_filename).resolve()
        product = file.is_relative_to(root)
        raw = file.read_bytes()
        lines = raw.decode().splitlines()
        rows.append({"scope": "product" if product else "external_driver",
                     "path": file.relative_to(root).as_posix() if product else str(file),
                     "name": code.co_name, "qualname": code.co_qualname,
                     "line": trace.tb_lineno, "first_line": code.co_firstlineno,
                     "statement": lines[trace.tb_lineno - 1],
                     "source_sha256": digest(raw), "bytecode_sha256": digest(code.co_code)})
        retained.append(frame)
        trace = trace.tb_next
    return rows, retained


def pick(frames, name):
    selected = [frame for frame in frames if frame.f_code.co_name == name
                and frame.f_globals.get("__name__") == "ontokin.reach_conformance"]
    if len(selected) != 1:
        raise ValueError("Expected exactly one retained frame: " + name)
    return selected[0].f_locals


def common_post_state(compiler, frames):
    """Same post-failure counter/cache observation in both modes."""
    work = compiler.reach_work
    wd = rawdict(work, "ontokin.reach_numeric.ReachExecutionWork")
    kd = pick(frames, "_key_comparisons")
    reference = kd["reference"]
    rd = rawdict(reference)
    ad = rawdict(rd["a"], "ontokin.reach_reference._Arithmetic")
    cache = ad["cache"]
    if type(cache) not in (dict, OrderedDict) or len(cache) > 256:
        raise ValueError("Unexpected independent arithmetic cache")
    if type(wd["counts"]) is not dict or type(wd["_cache"]) is not OrderedDict:
        raise ValueError("Unexpected request work storage")
    return {"shared_operations": compiler.budget.operations,
            "reach_work": {"operations": wd["operations"], "counts": dict(wd["counts"]),
                           "cache_entries": len(wd["_cache"])},
            "work_limits": {name: wd[name] for name in
                            ("max_operations", "max_elapsed_ms", "max_operand_bits", "max_cache_entries")},
            "construction_limits": dict(compiler.budget.limits),
            "independent_arithmetic_cache_entries_post_cleanup": len(cache),
            "independent_arithmetic_cache_operand_limit": ad["_cache_operand_limit"],
            "independent_arithmetic_work_operand_limit": rawdict(ad["work"], "ontokin.reach_numeric.ReachExecutionWork")["max_operand_bits"],
            "independent_arithmetic_precision_bits": ad["bits"],
            "shared_minus_reach_operations": compiler.budget.operations - work.operations}


def census(compiler, error, frames):
    native = Native()
    key = pick(frames, "_key_comparisons")
    center = pick(frames, "_recording_centered_comparison")
    l1 = pick(frames, "l1")
    checked = pick(frames, "checked")
    op = pick(frames, "op")
    caller = pick(frames, "compare_certificates")
    reference, batch = key["reference"], caller["source_batch"]
    rd = rawdict(reference)
    bd = rawdict(batch, "ontokin.reach_reference_plan._SourceBatch")
    wd = rawdict(compiler.reach_work, "ontokin.reach_numeric.ReachExecutionWork")
    ad = rawdict(center["arithmetic"], "ontokin.reach_conformance._Bounds")
    result, pending, completed = key["result"], key["pending"], center["completed"]
    if type(result) is not dict or type(pending) is not list or type(completed) is not tuple:
        raise ValueError("Unexpected comparison carrier storage")
    if max(len(result), len(pending), len(completed), len(key["geometry"])) > BOUNDS["container_items"]:
        raise ValueError("Carrier bound exceeded")
    proofs = []
    for index, comparison in enumerate(completed):
        names = [carrier for carrier, value in result.items() if value is comparison]
        if len(names) != 1 or type(comparison) is not dict:
            raise ValueError("Completed proof cannot be mapped uniquely to its carrier")
        proofs.append({"order": index, "carrier": names[0], "comparison_identity": native.token(comparison),
                       "orientation_proof": native.encode(comparison.get("_centered_orientation_proof")),
                       "record": native.encode(comparison)})
    plans = bd["plans"]
    if type(plans) is not dict or len(plans) > BOUNDS["plans"]:
        raise ValueError("Source batch plan bound exceeded")
    plan_rows = []
    for cache_identity, (plan, registered_time) in plans.items():
        pd = rawdict(plan, "ontokin.reach_reference_plan._Plan")
        nodes = pd["nodes"]
        if type(nodes) is not tuple or len(nodes) > BOUNDS["plan_nodes"]:
            raise ValueError("Source plan node bound exceeded")
        plan_rows.append({"identity": native.token(plan), "state_identity": native.token(pd["state"]),
                          "cache_identity": native.token(cache_identity),
                          "cache_identity_matches_plan": cache_identity is pd["cache_identity"],
                          "registered_time": native.encode(registered_time),
                          "context": native.encode(pd["context"]),
                          "context_state_id_matches": (type(pd["context"]) is tuple and len(pd["context"]) == 4
                                                       and pd["context"][1] == id(pd["state"])),
                          "context_token_same_as_request": (type(pd["context"]) is tuple and len(pd["context"]) == 4
                                                            and pd["context"][0] is caller["recording_context"]),
                          "targets": native.encode(pd["targets"]),
                          "remaining": native.encode(pd["remaining"]),
                          "nodes_identity": native.token(nodes), "receipts_count": len(pd["receipts"]),
                          "owners": native.encode(pd["owners"]),
                          "nodes": [native.object_fields(node, "ontokin.reach_reference_plan._Node",
                                    ("path", "kind", "parent", "relation", "axis", "stationary", "source_stationary"))
                                    for node in nodes]})
    boundaries = rd["boundaries"]
    if type(boundaries) is not tuple or len(boundaries) > BOUNDS["history_boundaries"]:
        raise ValueError("Source history boundary bound exceeded")
    if len(rd["_before"]) != len(boundaries) or len(rd["_after"]) != len(boundaries):
        raise ValueError("Source history shape differs")
    history = [{"index": index, "time": native.encode(value),
                "before_state_identity": native.token(rd["_before"][index]),
                "after_state_identity": native.token(rd["_after"][index])}
               for index, value in enumerate(boundaries)]
    current_carrier = key["carrier"]
    pending_names = [row[0] for row in pending]
    current_index = pending_names.index(current_carrier)
    out = {
        "schema": "ontokin.checkpoint036-post-failure-census/0.1",
        "capture_boundary": "After original exception reached external driver; no request resumed",
        "bounds": BOUNDS,
        "provenance": {"frame_locals": "Retained after unwind, read only after failure",
                       "detached_operands": "Native immutable operand values retained in comparison/l1 frames",
                       "mutable_objects": "Observed post-cleanup; no assertion of refusal-time state",
                       "predicate_calls": "Completed reused() frames are absent; decisions require offline reconstruction"},
        "key": native.fields(key, ("index", "time", "carrier", "previous_time", "position", "quaternion", "limits", "recording_context")),
        "source_frame": key["item"]["frame"],
        "carrier_order": {"geometry": list(key["geometry"]),
                          "observed": [row[0] for row in key["observed"]],
                          "completed": list(result), "pending_original": pending_names,
                          "pending_before_current": pending_names[:current_index],
                          "current": current_carrier, "pending_after_current": pending_names[current_index + 1:],
                          "centered_fallback_before_current": [row[0] for row in key["remaining"]]},
        "comparison": native.fields(center, ("position", "quaternion", "limits", "fields", "saved_seal", "integers", "values",
                            "source_position", "source_rotation", "position_radius", "rotation_radius", "expected", "axis",
                            "position_error", "quaternion_error", "distance", "invalidated", "magnitude")),
        "ideal_post_cleanup": native.object_fields(center["ideal"], "ontokin.reach_reference_center._CenteredPose",
                            ("position", "orientation", "position_radius", "orientation_radius", "axis", "seal")),
        "l1": native.fields(l1, ("actual", "expected", "raw", "point", "value", "error", "distance")),
        "attempted_operation": {"completed": False, "operation": op["operation"],
                                "ordered_operands": native.encode((op["a"], op["b"])),
                                "checked_args": native.encode(checked["args"]),
                                "checked_result_available": "result" in checked},
        "completed_orientation_proofs": proofs,
        "caller": native.fields(caller, ("key", "left", "right", "recording_context", "thresholds")),
        "source": {"reference_identity": native.token(reference),
                   "fields": native.fields(rd, ("end", "end_side", "mode")),
                   "model_identity": native.token(rd["model"]),
                   "arithmetic_identity": native.token(rd["a"]), "history": history,
                   "phase_plan_identity_post_cleanup": native.token(rd.get("_recording_phase_plan"))},
        "batch_post_cleanup": {"identity": native.token(batch),
                               "fields": native.fields(bd, ("active", "prepared", "depth", "context", "current_plan", "header")),
                               "reference_batch_is_none": rd.get("_recording_batch") is None,
                               "cursor_ledger_entries": len(bd["cursors"]),
                               "receipt_count": len(bd["receipts"]), "plans": plan_rows},
        "identity_relationships": {"key_and_caller_context_same": key["recording_context"] is caller["recording_context"],
                         "batch_and_caller_context_same": bd["context"] is caller["recording_context"],
                         "batch_reference_same": bd["reference"] is reference,
                         "comparison_work_is_compiler_work": ad["work"] is compiler.reach_work,
                         "saved_owner_is_compiler_work": center["owner"] is compiler.reach_work,
                         "saved_external_is_current": center["external"] is wd["external_check"],
                         "work_callback_error_is_original": wd["callback_error"] is error,
                         "ideal_is_key_center": center["ideal"] is key["centered"][key["item"]["frame"]]},
    }
    out["capture_counts"] = {"native_nodes": native.count, "identity_tokens": len(native.identities),
                             "completed_proofs": len(proofs), "plans": len(plan_rows)}
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=("control", "capture"), required=True)
    args = parser.parse_args()
    root, output = args.root.resolve(), args.output.resolve()
    if output.is_relative_to(root) or Path(__file__).resolve().is_relative_to(root):
        raise ValueError("Driver and receipts must be external to execution checkout")
    if sys.getprofile() is not None or sys.gettrace() is not None:
        raise ValueError("No profiler or trace hook is permitted")
    output.mkdir(parents=True, exist_ok=False)
    before = inventory(root)
    write(output / "inputs-before.json", before)
    sys.path.insert(0, str(root))
    from tools.reach_delivery_inventory import settings
    from ontokin.bundle import load_file_manifest
    from ontokin.construction import compile_construction
    from ontokin.gltf import export_glb
    from ontokin.scene import ExportOptions
    from ontokin.diagnostics import OntoKinError
    manifest = root / MANIFEST
    if digest(manifest.read_bytes()) != MANIFEST_SHA256:
        raise ValueError("Original P11 source manifest changed")
    options = settings("P11", fps=1)
    start = {"schema": "ontokin.checkpoint036-request/0.1", "mode": args.mode,
             "command": [sys.executable, str(Path(__file__).resolve()), *sys.argv[1:]],
             "cwd": str(root), "source_commit": COMMIT, "source_tree": TREE,
             "driver_sha256": digest(Path(__file__).read_bytes()), "started_at": utc(),
             "environment": {"python": sys.version, "executable": sys.executable, "platform": platform.platform(),
                             "executable_sha256": digest(Path(sys.executable).resolve().read_bytes())},
             "options": options, "source_files": MANIFEST, "source_manifest_sha256": MANIFEST_SHA256,
             "expected_program_revision": REVISION, "target_contract": "ontokin.glb/0.6",
             "native_capture_bounds": BOUNDS, "profile_installed": False, "trace_installed": False}
    write(output / "start.json", start)
    compiler = bundle = failure = None
    started = time.monotonic()
    try:
        bundle = load_file_manifest(manifest)
        if bundle.program_revision != REVISION:
            raise ValueError("Original frozen P11 program revision changed")
        compiler = compile_construction(bundle, level="constructed")
        result = export_glb(compiler.model, options=ExportOptions(**{**options, "end": Fraction(options["end"])}),
                            target_contract="ontokin.glb/0.6", work=compiler.reach_work)
    except Exception as error:
        failure = error
    elapsed = time.monotonic() - started
    row = {**start, "finished_request_at": utc(), "product_elapsed_seconds": elapsed,
           "status": "failed" if failure is not None else "passed",
           "release_acceptance": False, "capture_status": "not_requested"}
    if failure is None:
        row["unexpected_completion"] = True
    else:
        # All receipt construction and local inspection starts after termination.
        raw_traceback = "".join(traceback.format_exception(failure))
        (output / "traceback.txt").write_text(raw_traceback)
        row.update(failure={"type": type(failure).__name__, "class": typename(failure), "message": str(failure)},
                   original_exception_identity_preserved=True)
        try:
            stack, frames = frames_of(failure, root)
            row["traceback_frames"] = stack
            if type(failure) is OntoKinError and bundle is not None:
                source_id = getattr(failure.diagnostic.node, "source_id", "entry")
                row["diagnostic"] = failure.diagnostic.to_dict(bundle.sources.get(source_id, bundle.entry.to_source()))
            if bundle is not None:
                row["program_revision"] = bundle.program_revision
                row["source_units"] = [{"source_id": unit.source_id, "bytes": len(unit.raw), "sha256": digest(unit.raw)}
                                       for unit in bundle.units]
            if compiler is not None:
                row["post_state"] = common_post_state(compiler, frames)
            # This is the only mode-dependent observation, and is strictly post-failure.
            if args.mode == "capture":
                try:
                    captured = census(compiler, failure, frames)
                    write(output / "census.json", captured)
                    row["capture_status"] = "captured"
                    row["census_sha256"] = digest((output / "census.json").read_bytes())
                except Exception as capture_error:
                    row["capture_status"] = "failed"
                    row["capture_failure"] = {"type": type(capture_error).__name__, "message": str(capture_error)}
                    (output / "capture-error.txt").write_text("".join(traceback.format_exception(capture_error)))
            if compiler is not None:
                row["post_observation_state"] = common_post_state(compiler, frames)
                row["observation_preserved_counters_and_caches"] = row["post_state"] == row["post_observation_state"]
        except Exception as metadata_error:
            row["metadata_status"] = "failed"
            row["metadata_error"] = {"type": type(metadata_error).__name__, "message": str(metadata_error)}
            (output / "metadata-error.txt").write_text("".join(traceback.format_exception(metadata_error)))
    try:
        after = inventory(root)
        write(output / "inputs-after.json", after)
        row["inputs_stable"] = before == after
    except Exception as inventory_error:
        row["inputs_stable"] = False
        row["inventory_error"] = {"type": type(inventory_error).__name__, "message": str(inventory_error)}
    row["finished_receipt_at"] = utc()
    row["driver_unchanged"] = row["driver_sha256"] == digest(Path(__file__).read_bytes())
    write(output / "request-result.json", row)
    print(json.dumps({"mode": args.mode, "status": row["status"], "capture_status": row["capture_status"],
                      "shared_operations": row.get("post_state", {}).get("shared_operations"),
                      "inputs_stable": row["inputs_stable"]}), flush=True)
    return 1 if failure is not None else 0


if __name__ == "__main__":
    raise SystemExit(main())
