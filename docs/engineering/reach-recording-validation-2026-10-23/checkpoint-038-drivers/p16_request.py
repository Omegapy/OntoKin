#!/usr/bin/env python3
"""C038 original P16 request; optional native capture starts after failure only.

Control and capture execute identical source loading, construction and export
statements. No callback, observer, trace/profile hook or product helper is
replaced. Every receipt describes the original failed request; post-failure
capture does not resume it or create another work allowance.
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
REVISION = "sha256:0487f3f410944484f0a6aad7bef37e1a59a1d13464b19af85661251c430388f7"
MANIFEST = "docs/language-design/planar-reach-v0.1/p16.files.json"
MANIFEST_SHA256 = "0d218a8b1245766fa3e4892ec5ccafd275ee92fd4195b3b852d5daaefa9e4070"
BOUNDS = {"frames": 64, "sequence_items": 10000, "mapping_items": 1024,
          "depth": 16, "scalar_bits": 32768, "string_characters": 10000,
          "native_nodes": 1000000, "json_bytes": 64 * 1024 * 1024,
          "glb_bytes": 64 * 1024 * 1024, "categories": 512,
          "numerical_cache_entries": 256}
F_NUM = Fraction.__dict__["_numerator"]
F_DEN = Fraction.__dict__["_denominator"]


def utc():
    return datetime.now(timezone.utc).isoformat()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def write(path, value):
    raw = (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()
    if len(raw) > BOUNDS["json_bytes"]:
        raise ValueError("C038 JSON byte bound exceeded; truncated evidence is not accepted")
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


def rawdict(value, expected):
    """Read exact loaded native class storage through its dictionary descriptor."""
    module_name, class_name = expected.rsplit(".", 1)
    module = sys.modules.get(module_name)
    if type(module) is not types.ModuleType:
        raise ValueError("Expected loaded native module: " + module_name)
    native_class = types.ModuleType.__getattribute__(module, "__dict__").get(class_name)
    cls = type(value)
    if cls is not native_class or typename(value) != expected:
        raise ValueError("Unexpected native storage class: " + typename(value))
    for base in type.__getattribute__(cls, "__mro__"):
        descriptor = type.__getattribute__(base, "__dict__").get("__dict__")
        if type(descriptor) is types.GetSetDescriptorType:
            result = descriptor.__get__(value, cls)
            if type(result) is not dict:
                raise ValueError("Non-native instance dictionary")
            return result
    raise ValueError("Native instance dictionary unavailable: " + expected)


def native_mapping(value, maximum=None):
    if type(value) is not dict or len(value) > (maximum or BOUNDS["mapping_items"]):
        raise ValueError("Native mapping type/size bound exceeded")
    return value


def native_sequence(value, maximum=None):
    if type(value) not in (list, tuple) or len(value) > (maximum or BOUNDS["sequence_items"]):
        raise ValueError("Native sequence type/size bound exceeded")
    return value


def fraction_fields(value):
    if type(value) is not Fraction:
        raise ValueError("Expected exact native Fraction")
    numerator, denominator = F_NUM.__get__(value, Fraction), F_DEN.__get__(value, Fraction)
    if (type(numerator) is not int or type(denominator) is not int or denominator <= 0
            or max(numerator.bit_length(), denominator.bit_length()) > BOUNDS["scalar_bits"]):
        raise ValueError("Native Fraction field/domain bound exceeded")
    return numerator, denominator


class Native:
    def __init__(self):
        self.count = 0

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
            numerator, denominator = fraction_fields(value)
            return {"type": "Fraction", "numerator_hex": self.integer(numerator),
                    "denominator_hex": self.integer(denominator)}
        if cls in (tuple, list):
            native_sequence(value)
            return {"type": cls.__name__, "items": [self.encode(x, depth + 1) for x in value]}
        if cls is set:
            if len(value) > BOUNDS["sequence_items"]:
                raise ValueError("Native set bound exceeded")
            return {"type": "set", "iteration_order_semantics": "unordered",
                    "items": [self.encode(x, depth + 1) for x in value]}
        if cls is dict:
            native_mapping(value)
            return {"type": "dict", "entries": [[self.encode(k, depth + 1), self.encode(v, depth + 1)]
                                                  for k, v in dict.items(value)]}
        # A required field cannot silently become an opaque or truncated value.
        # Do not invoke foreign getters, repr or graph traversal to recover it.
        raise ValueError("Unsupported native census field type: " + typename(value))

    def fields(self, mapping, names):
        native_mapping(mapping)
        return {name: self.encode(mapping[name]) if name in mapping else {"type": "unavailable"}
                for name in names}


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
                     "module": frame.f_globals.get("__name__"),
                     "name": code.co_name, "qualname": code.co_qualname,
                     "line": trace.tb_lineno, "first_line": code.co_firstlineno,
                     "statement": lines[trace.tb_lineno - 1],
                     "source_sha256": digest(raw), "bytecode_sha256": digest(code.co_code)})
        retained.append(frame)
        trace = trace.tb_next
    return rows, retained


def select(frames, module, name, *, qualname=None, required=False):
    found = [frame for frame in frames if frame.f_globals.get("__name__") == module
             and frame.f_code.co_name == name
             and (qualname is None or frame.f_code.co_qualname == qualname)]
    if len(found) > 1 or (required and len(found) != 1):
        raise ValueError("Retained frame is absent or ambiguous: " + module + "." + (qualname or name))
    return found[0] if found else None


def method_matches(value, owner, function):
    return type(value) is types.MethodType and value.__self__ is owner and value.__func__ is function


def reader_bytes(validation):
    data = validation.get("data")
    if type(data) is not bytes or not 28 <= len(data) <= BOUNDS["glb_bytes"]:
        raise ValueError("Retained reader input must be native bounded GLB bytes")
    return data


def common_post_state(compiler, error, frames):
    """Identical bounded post-failure observation for control and capture."""
    cd = rawdict(compiler, "ontokin.construction.ConstructionCompiler")
    budget, work = cd["budget"], cd["reach_work"]
    bd = rawdict(budget, "ontokin.construction.ConstructionBudget")
    wd = rawdict(work, "ontokin.reach_numeric.ReachExecutionWork")
    counts = native_mapping(wd["counts"], BOUNDS["categories"])
    if any(type(k) is not str or type(v) is not int or v < 0 for k, v in counts.items()):
        raise ValueError("Invalid completed category map")
    if type(wd["_cache"]) is not OrderedDict or len(wd["_cache"]) > 256:
        raise ValueError("Unexpected request numerical cache")
    limits = native_mapping(bd["limits"])
    if any(type(k) is not str or type(v) is not int for k, v in limits.items()):
        raise ValueError("Invalid construction limits")
    result = {"shared_operations": bd["operations"],
              "reach_work": {"operations": wd["operations"], "counts": dict(counts),
                             "cache_entries": len(wd["_cache"])},
              "work_limits": {name: wd[name] for name in
                              ("max_operations", "max_elapsed_ms", "max_operand_bits", "max_cache_entries")},
              "construction_limits": dict(limits),
              "category_metadata_limit": BOUNDS["categories"],
              "shared_minus_reach_operations": bd["operations"] - wd["operations"],
              "work_callback_error_is_original": wd["callback_error"] is error,
              "construction_callback_error_is_original": bd["callback_error"] is error,
              "work_external_check_is_construction_tick": method_matches(
                  wd["external_check"], budget, type(budget).__dict__["tick"]),
              "construction_external_check_is_none": bd["check"] is None,
              "source_after_charge_is_none_post_cleanup": wd["_source_after_charge"] is None,
              "trace_installed_post_failure": sys.gettrace() is not None,
              "profile_installed_post_failure": sys.getprofile() is not None,
              "independent_arithmetic": {"available": False},
              "decoded_cache": {"available": False},
              "reader_input": {"available": False}}
    frame = select(frames, "ontokin.reach_conformance", "validate_reach_export")
    if frame is None:
        return result
    validation = frame.f_locals
    data = reader_bytes(validation)
    result["reader_input"] = {"available": True, "bytes": len(data), "sha256": digest(data),
                              "status": "unvalidated_reader_input_from_failed_request"}
    result["validation_work_is_compiler_work"] = validation.get("work") is work
    result["validation_model_is_compiler_model"] = validation.get("model") is cd["model"]
    if "decoded" in validation:
        dd = rawdict(validation["decoded"], "ontokin.gltf.DecodedGLB")
        ac, cc = native_mapping(dd["_cache"], 10000), native_mapping(dd["_clocks"], 10000)
        if any(type(k) is not int or type(v) is not list for k, v in (*ac.items(), *cc.items())):
            raise ValueError("Unexpected decoded-cache storage")
        result["decoded_cache"] = {"available": True, "accessor_entries": len(ac), "clock_entries": len(cc),
            "accessor_lengths_in_insertion_order": [[k, len(v)] for k, v in ac.items()],
            "clock_lengths_in_insertion_order": [[k, len(v)] for k, v in cc.items()],
            "check_is_work_tick": method_matches(dd["check"], work, type(work).__dict__["tick"])}
    if "reference" in validation:
        rd = rawdict(validation["reference"], "ontokin.reach_reference.ReachReference")
        ad = rawdict(rd["a"], "ontokin.reach_reference._Arithmetic")
        cache = ad["cache"]
        if type(cache) not in (dict, OrderedDict) or len(cache) > 256:
            raise ValueError("Unexpected independent arithmetic cache")
        result["independent_arithmetic"] = {"available": True,
            "cache_entries_post_cleanup": len(cache), "cache_operand_limit": ad["_cache_operand_limit"],
            "precision_bits": ad["bits"], "work_is_compiler_work": ad["work"] is work,
            "check_is_work_tick": method_matches(ad["check"], work, type(work).__dict__["tick"]),
            "recording_after_tick_is_none_post_cleanup": ad["_recording_after_tick"] is None,
            "recording_product_after_tick_is_none_post_cleanup": ad["_recording_product_after_tick"] is None,
            "recording_batch_is_none_post_cleanup": rd["_recording_batch"] is None}
    return result


def clock_storage(decoded, times, native):
    """Copy native clock descriptors and actual word bytes, without reader calls."""
    dd = rawdict(decoded, "ontokin.gltf.DecodedGLB")
    document = native_mapping(dd["document"])
    animations = native_sequence(document["animations"])
    animation = native_mapping(animations[0])
    samplers = native_sequence(animation["samplers"])
    sampler = native_mapping(samplers[0])
    accessor_index = sampler["input"]
    accessors, views = native_sequence(document["accessors"]), native_sequence(document["bufferViews"])
    if type(accessor_index) is not int or not 0 <= accessor_index < len(accessors):
        raise ValueError("Invalid retained clock accessor index")
    accessor = native_mapping(accessors[accessor_index])
    view_index = accessor["bufferView"]
    if type(view_index) is not int or not 0 <= view_index < len(views):
        raise ValueError("Invalid retained clock buffer-view index")
    view = native_mapping(views[view_index])
    count = accessor["count"]
    if (accessor["componentType"] != 5126 or accessor["type"] != "SCALAR"
            or type(count) is not int or not 1 <= count <= BOUNDS["sequence_items"] or count != len(times)):
        raise ValueError("Retained time accessor is not the bounded complete binary32 axis")
    offset, stride = view.get("byteOffset", 0) + accessor.get("byteOffset", 0), view.get("byteStride", 4)
    binary = dd["binary"]
    if (type(offset) is not int or type(stride) is not int or offset < 0 or stride < 4
            or type(binary) is not bytes or len(binary) > BOUNDS["glb_bytes"]
            or offset + (count - 1) * stride + 4 > len(binary)):
        raise ValueError("Retained binary clock layout is out of bounds")
    words = []
    for index in range(count):
        raw = binary[offset + index * stride:offset + index * stride + 4]
        words.append({"index": index, "bytes_le": raw.hex(),
                      "binary32_bits_hex": format(struct.unpack("<I", raw)[0], "08x")})
    return {"accessor_index": accessor_index, "accessor": native.encode(accessor),
            "buffer_view_index": view_index, "buffer_view": native.encode(view),
            "samplers": native.encode(samplers), "binary_bytes": len(binary),
            "binary_sha256": digest(binary), "words": words,
            "times_is_native_clock_cache_entry": dd["_clocks"].get(accessor_index) is times,
            "provenance": "Raw byte slices of retained decoded.binary; no accessor/clock helper invoked"}


def bind_pair(clock, generator, comparison):
    result = {"status": "unavailable", "reason": "Unique retained generator/compare operands not established",
              "matched_indices": [], "retained_iterator_touched": False}
    if generator is None or comparison is None or "authored" not in clock:
        return result
    gd, xd = generator.f_locals, comparison.f_locals
    if any(name not in gd or name not in xd for name in ("a", "b")):
        return result
    authored = native_sequence(clock["authored"])
    if any(type(value) is not Fraction for value in (*authored, gd["a"], gd["b"], xd["a"], xd["b"])):
        result["reason"] = "Attempted operands or authored values are not exact native Fractions"
        return result
    left, right = fraction_fields(gd["a"]), fraction_fields(gd["b"])
    identity_matches, value_matches = [], []
    for index in range(len(authored) - 1):
        a, b = authored[index], authored[index + 1]
        if a is gd["a"] and b is gd["b"]:
            identity_matches.append(index)
        if fraction_fields(a) == left and fraction_fields(b) == right:
            value_matches.append(index)
    relation = gd["a"] is xd["a"] and gd["b"] is xd["b"]
    result.update(generator_and_compare_operands_identical=relation,
                  identity_match_count=len(identity_matches), value_match_count=len(value_matches),
                  generator_and_compare_native_values_equal=(left, right) ==
                      (fraction_fields(xd["a"]), fraction_fields(xd["b"])))
    if relation and len(identity_matches) == 1 and identity_matches == value_matches:
        result.update(status="uniquely_bound", matched_indices=identity_matches,
                      left_index=identity_matches[0], right_index=identity_matches[0] + 1,
                      reason="One adjacent authored pair matches retained native identities and typed exact values")
    return result


def census(compiler, error, frames):
    native = Native()
    vf = select(frames, "ontokin.reach_conformance", "validate_reach_export", required=True)
    cf = select(frames, "ontokin.reach_conformance", "verify_retained_clocks", required=True)
    validation, clock = vf.f_locals, cf.f_locals
    generator = select(frames, "ontokin.reach_conformance", "<genexpr>",
                       qualname="verify_retained_clocks.<locals>.<genexpr>")
    comparison = select(frames, "ontokin.reach_conformance", "compare", qualname="_Bounds.compare")
    cd = rawdict(compiler, "ontokin.construction.ConstructionCompiler")
    work, budget = cd["reach_work"], cd["budget"]
    reference = validation["reference"]
    rd = rawdict(reference, "ontokin.reach_reference.ReachReference")
    ad = rawdict(clock["arithmetic"], "ontokin.reach_conformance._Bounds")
    refad = rawdict(rd["a"], "ontokin.reach_reference._Arithmetic")
    wd = rawdict(work, "ontokin.reach_numeric.ReachExecutionWork")
    native_sequence(clock["authored_records"])
    native_sequence(clock["retained"])
    native_sequence(clock["times"])
    if not all(type(x) is Fraction for x in native_sequence(clock["authored"])):
        raise ValueError("Parsed authored clocks are not complete native Fraction storage")
    options = rawdict(validation["options"], "ontokin.scene.ExportOptions")
    stages = []
    names = {("ontokin.reach_conformance", "tick"): ("kind",),
             ("ontokin.reach_conformance", "_tick"): ("kind",),
             ("ontokin.reach_numeric", "charge"): ("kind", "amount"),
             ("ontokin.construction", "tick"): ("amount",),
             ("ontokin.construction", "exceeded"): ("name", "consumed"),
             ("ontokin.reach_conformance", "value"): ("value",),
             ("ontokin.reach_conformance", "op"): ("a", "b", "operation")}
    for frame in frames:
        key = frame.f_globals.get("__name__"), frame.f_code.co_name
        if key in names:
            stages.append({"module": key[0], "function": frame.f_code.co_qualname,
                           "fields": native.fields(frame.f_locals, names[key])})
    out = {"schema": "ontokin.checkpoint038-post-failure-clock-census/0.1",
        "capture_boundary": "Original exception retained by external driver; failed request never resumed",
        "bounds": BOUNDS,
        "provenance": {"immutable_operands": "Native retained values after unwind",
                       "mutable_storage": "Post-cleanup observation, not a refusal-time snapshot",
                       "unvisited_tail": "Not executed; no complete remaining-cost inference",
                       "retained_iterator": "Never inspected or advanced"},
        "clock": native.fields(clock, ("authored_records", "retained", "times", "authored", "boundaries",
             "semantic", "end", "time_tolerance", "maximum_shift", "index", "record", "source_record",
             "actual", "source", "bits")),
        "generator": {"available": generator is not None,
                      "qualname": None if generator is None else generator.f_code.co_qualname,
                      "first_line": None if generator is None else generator.f_code.co_firstlineno,
                      "fields": {} if generator is None else native.fields(generator.f_locals, ("a", "b")),
                      "iterator_touched": False},
        "attempted_comparison": {"available": comparison is not None,
                     "fields": {} if comparison is None else native.fields(comparison.f_locals, ("a", "b")),
                     "result_available_in_frame": False if comparison is None else "result" in comparison.f_locals,
                     "stage_interpretation": "Determine refusal stage from the original traceback and stage locals"},
        "pair_binding": bind_pair(clock, generator, comparison),
        "stage_locals": stages,
        "stored_axis": clock_storage(validation["decoded"], clock["times"], native),
        "source_reference": {"fields": native.fields(rd, ("end", "end_side", "mode", "boundaries")),
                             "recording_batch_is_none_post_cleanup": rd["_recording_batch"] is None},
        "actual_export_options": native.fields(options, ("end", "fps", "helpers", "position_tolerance_m",
                                                         "rotation_tolerance_rad", "time_tolerance_s")),
        "identity_relationships": {
            "clock_work_is_compiler_work": clock["work"] is work,
            "clock_bounds_work_is_compiler_work": ad["work"] is work,
            "validation_work_is_compiler_work": validation["work"] is work,
            "reference_arithmetic_work_is_compiler_work": refad["work"] is work,
            "reference_model_is_compiler_model": rd["model"] is cd["model"],
            "clock_decoded_is_validation_decoded": clock["decoded"] is validation["decoded"],
            "clock_quantization_is_validation_quantization": clock["quantization"] is validation["quantization"],
            "clock_authored_records_is_validation_authored_records": clock["authored_records"] is validation["authored_records"],
            "clock_boundaries_is_reference_boundaries": clock["boundaries"] is rd["boundaries"],
            "clock_end_is_validation_end": clock["end"] is validation["end"],
            "original_error_is_work_callback_error": wd["callback_error"] is error,
            "work_external_check_is_construction_tick": method_matches(
                wd["external_check"], budget, type(budget).__dict__["tick"]),
            "compare_bounds_is_clock_bounds": None if comparison is None else comparison.f_locals.get("self") is clock["arithmetic"]}}
    out["native_nodes_encoded"] = native.count
    return out, reader_bytes(validation)


def source_identity(bundle):
    bd = rawdict(bundle, "ontokin.bundle.ProgramBundle")
    modules = native_sequence(bd["modules"], 128)
    units = (bd["entry"], *modules)
    rows = []
    for unit in units:
        ud = rawdict(unit, "ontokin.bundle.SourceUnit")
        raw = ud["raw"]
        if type(raw) is not bytes:
            raise ValueError("Source unit bytes are not native")
        rows.append({"source_id": ud["source_id"], "filename": ud["filename"],
                     "bytes": len(raw), "sha256": digest(raw), "source_revision": ud["revision"]})
    return bd["program_revision"], rows


def error_record(error):
    return {"type": type(error).__name__, "class": typename(error), "message": str(error)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=("control", "capture"), required=True)
    args = parser.parse_args()
    root, output = args.root.resolve(), args.output.resolve()
    if output.is_relative_to(root) or Path(__file__).resolve().is_relative_to(root):
        raise ValueError("Driver and receipts must be external to execution checkout")
    output.mkdir(parents=True, exist_ok=False)
    row = {"schema": "ontokin.checkpoint038-request/0.1", "mode": args.mode,
           "command": [sys.executable, str(Path(__file__).resolve()), *sys.argv[1:]],
           "cwd": str(root), "source_commit": COMMIT, "source_tree": TREE,
           "driver_sha256": digest(Path(__file__).read_bytes()), "started_at": utc(),
           "environment": {"python": sys.version, "executable": sys.executable, "platform": platform.platform(),
                           "executable_sha256": digest(Path(sys.executable).resolve().read_bytes())},
           "source_files": MANIFEST, "source_manifest_sha256": MANIFEST_SHA256,
           "expected_program_revision": REVISION, "target_contract": "ontokin.glb/0.6",
           "native_capture_bounds": BOUNDS, "status": "not_started", "metadata_status": "not_started",
           "release_acceptance": False, "capture_status": "not_requested", "inputs_stable": False,
           "request_executed": False, "profile_installed": sys.getprofile() is not None,
           "trace_installed": sys.gettrace() is not None}
    before = bundle = compiler = failure = None
    exit_code = 2
    write(output / "start.json", row)
    try:
        if row["profile_installed"] or row["trace_installed"]:
            raise ValueError("No profiler or trace hook is permitted")
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
            raise ValueError("Original P16 source manifest changed")
        options = settings("P16", fps=1)
        if options != {"end": "4", "fps": 1, "helpers": False, "position_tolerance_m": .001,
                       "rotation_tolerance_rad": .001, "time_tolerance_s": .000001} or type(options["fps"]) is not int:
            raise ValueError("Original P16 settings changed")
        row["options"] = options
        write(output / "request-start.json", row)
        started = time.monotonic()
        row["request_executed"] = True
        try:
            bundle = load_file_manifest(manifest)
            if bundle.program_revision != REVISION:
                raise ValueError("Original frozen P16 program revision changed")
            compiler = compile_construction(bundle, level="constructed")
            result = export_glb(compiler.model, options=ExportOptions(**{**options, "end": Fraction(options["end"])}),
                                target_contract="ontokin.glb/0.6", work=compiler.reach_work)
        except BaseException as error:
            failure = error
        row.update(finished_request_at=utc(), product_elapsed_seconds=time.monotonic() - started,
                   status="failed" if failure is not None else "passed")
        exit_code = 1 if failure is not None else 0
        if failure is None:
            row["unexpected_completion"] = True
        else:
            # All failure metadata and capture occur after retaining the original exception.
            row.update(failure=error_record(failure), original_exception_identity_preserved=True)
            (output / "traceback.txt").write_text("".join(traceback.format_exception(failure)))
            try:
                stack, frames = frames_of(failure, root)
                row["traceback_frames"] = stack
                if bundle is not None:
                    row["program_revision"], row["source_units"] = source_identity(bundle)
                if type(failure) is OntoKinError and bundle is not None:
                    # This is the established diagnostic serializer, not a numerical reader.
                    source_id = getattr(failure.diagnostic.node, "source_id", "entry")
                    row["diagnostic"] = failure.diagnostic.to_dict(bundle.sources.get(source_id, bundle.entry.to_source()))
                if compiler is not None:
                    row["post_state"] = common_post_state(compiler, failure, frames)
                row["metadata_status"] = "captured"
                # Sole mode-dependent branch, strictly after original request failure.
                if args.mode == "capture":
                    try:
                        captured, unvalidated = census(compiler, failure, frames)
                        write(output / "census.json", captured)
                        with (output / "unvalidated-reader-input.glb").open("xb") as stream:
                            stream.write(unvalidated)
                        row.update(capture_status="captured",
                            census_sha256=digest((output / "census.json").read_bytes()),
                            retained_reader_input={"path": "unvalidated-reader-input.glb", "bytes": len(unvalidated),
                                "sha256": digest(unvalidated), "status": "unvalidated_reader_input_from_failed_request"})
                    except BaseException as capture_error:
                        row.update(capture_status="failed", capture_failure=error_record(capture_error))
                        (output / "capture-error.txt").write_text("".join(traceback.format_exception(capture_error)))
                if compiler is not None:
                    row["post_observation_state"] = common_post_state(compiler, failure, frames)
                    row["observation_preserved_counters_and_caches"] = row["post_state"] == row["post_observation_state"]
            except BaseException as metadata_error:
                row.update(metadata_status="failed", metadata_error=error_record(metadata_error))
                (output / "metadata-error.txt").write_text("".join(traceback.format_exception(metadata_error)))
    except BaseException as outer_error:
        row["driver_failure"] = error_record(outer_error)
        if not row["request_executed"]:
            row["status"] = "preflight_failed"
        (output / "driver-error.txt").write_text("".join(traceback.format_exception(outer_error)))
    finally:
        try:
            after = inventory(root)
            write(output / "inputs-after.json", after)
            row["inputs_stable"] = before is not None and before == after
        except BaseException as inventory_error:
            row["inventory_error"] = error_record(inventory_error)
        row.update(finished_receipt_at=utc(), driver_unchanged=row["driver_sha256"] == digest(Path(__file__).read_bytes()),
                   exit_code=exit_code)
        write(output / "request-result.json", row)
    print(json.dumps({"mode": args.mode, "status": row["status"], "capture_status": row["capture_status"],
                      "shared_operations": row.get("post_state", {}).get("shared_operations"),
                      "inputs_stable": row["inputs_stable"], "metadata_status": row["metadata_status"]}), flush=True)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
