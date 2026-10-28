#!/usr/bin/env python3
"""Audit failed original recording pairs and passive reader-setup attribution.

The unchanged C060 standard-library auditor remains an explicit, hash-pinned
dependency. Its source, input, command, exception, byte and work-map checks all
run before this program reconciles the additional setup observations. Neither
auditor imports OntoKin, evaluates source, resumes a request or accepts a GLB.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import importlib.util
import math
from pathlib import Path
import platform
import sys
import traceback

ADAPTER_PATH = "tools/audit_reach_reader_setup.py"
CORE_PATH = "tools/audit_reach_recording_work.py"
CORE_SHA256 = "5a1ece268ba6f8bf71f2f62fbe2963da34175280797ec66be668261b2886b0cf"
COLLECTOR_PATH = "tools/capture_reach_reader_setup.py"
MAX_SPANS = 4096
SCALARS = ("shared_operations", "reach_operations", "checkpoint")
SCALAR_FIELDS = set(SCALARS)
FULL_FIELDS = SCALAR_FIELDS | {"counts", "work_cache_entries", "reference_cache"}
SPAN_IDENTITIES = {
    "positional_objects_preserved", "keyword_objects_preserved", "work_owner_preserved",
    "external_callback_preserved", "callback_owner_preserved", "work_observer_preserved",
}
SETUP_IDENTITIES = {
    "restored_before_first_key", "all_targets_restored", "all_recorded_restore_checks",
    "native_dispatch_preserved", "native_dispatch_before_install", "native_dispatch_at_cutoff",
}
# label, source module, qualified function name, nested, axial-only
TARGETS = (
    ("gltf.read_glb", "gltf", "read_glb", False, False),
    ("gltf._validate_geometry", "gltf", "_validate_geometry", False, False),
    ("scene.program_metadata", "scene", "program_metadata", False, False),
    ("reference.build_reference", "reach_reference", "build_reference", False, False),
    ("reader.verify_numeric_bases", "reach_conformance", "verify_numeric_bases", False, False),
    ("reader._verify_metadata", "reach_conformance", "_verify_metadata", False, False),
    ("reader.verify_retained_clocks", "reach_conformance", "verify_retained_clocks", False, False),
    ("reader._geometry_bounds", "reach_conformance", "_geometry_bounds", False, False),
    ("reader._phase_tables", "reach_conformance", "_phase_tables", False, False),
    ("reader._boundary_allowances", "reach_conformance", "_boundary_allowances", False, False),
    ("reader._assert_projection", "reach_conformance", "_assert_projection", False, False),
    ("reader._tracks", "reach_conformance", "_tracks", False, False),
    ("reference.boundary_states", "reach_reference", "ReachReference.boundary_states", False, False),
    ("reference.point_phase", "reach_reference", "ReachReference.point_phase", False, False),
    ("reference._phase", "reach_reference", "ReachReference._phase", True, False),
    ("reference._axial_derivatives", "reach_reference", "ReachReference._axial_derivatives", True, False),
    ("reference._l1", "reach_reference", "ReachReference._l1", True, True),
    ("reference._axis_transport", "reach_reference", "ReachReference._axis_transport", True, True),
)
TARGET_BY_LABEL = {row[0]: row for row in TARGETS}
CORE = None


def require(condition, message):
    if CORE is None:
        if not condition:
            raise ValueError(message)
    else:
        CORE.require(condition, message)


def load_core():
    """Load only the reviewed auditor, never package initializers or product code."""
    path = Path(__file__).absolute().parent / Path(CORE_PATH).name
    require(not any(p.is_symlink() for p in (path, *path.parents)), "Auditor dependency uses a symlink")
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == CORE_SHA256, "C060 auditor dependency differs from reviewed bytes")
    specification = importlib.util.spec_from_file_location("ontokin_c060_offline_auditor", path)
    require(specification is not None and specification.loader is not None, "Cannot load offline audit dependency")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    require(module.WRAPPER_NAMES == {"capture_validate_export", "capture_key_comparisons", "capture_recording_stage"},
            "C060 named-wrapper policy changed")
    module.CAPTURE_PATH = COLLECTOR_PATH
    require(path.read_bytes() == raw, "Auditor dependency changed during loading")
    return module, path, raw


def nonnegative(value, label, maximum=100000):
    require(type(value) is int and 0 <= value <= maximum, "Invalid bounded integer: " + label)
    return value


def opaque(value, label):
    require(type(value) is int and 0 < value < 2 ** 128, "Invalid process-local identity: " + label)
    return value


def scalar_delta(first, last):
    result = {name: last[name] - first[name] for name in SCALARS}
    require(all(type(value) is int and value >= 0 for value in result.values())
            and result["shared_operations"] >= result["reach_operations"] >= result["checkpoint"],
            "Setup scalar delta is not a monotone subset partition")
    return result


def subtract_scalars(total, parts):
    result = {name: total[name] - sum(row[name] for row in parts) for name in SCALARS}
    require(all(value >= 0 for value in result.values())
            and result["shared_operations"] >= result["reach_operations"] >= result["checkpoint"],
            "Exclusive setup cost is negative or violates shared/Reach/checkpoint containment")
    return result


def full_state(snapshot):
    return {"shared_operations": snapshot["shared_operations"], "reach": {
        "operations": snapshot["reach_operations"], "counts": snapshot["counts"],
        "cache_entries": snapshot["work_cache_entries"]}}


def cache_snapshot(cache):
    if cache is None:
        return
    require(type(cache) is dict and set(cache) == {
        "reference_identity", "arithmetic_identity", "arithmetic_bits", "operand_limit_field",
        "arithmetic_entries", "arithmetic_categories", "other_existing_cache_entries"},
        "Unexpected independent-reference cache observation fields")
    opaque(cache["reference_identity"], "reference")
    opaque(cache["arithmetic_identity"], "arithmetic")
    require(type(cache["arithmetic_bits"]) is int and 1 <= cache["arithmetic_bits"] <= 32768
            and type(cache["operand_limit_field"]) is int and cache["operand_limit_field"] == 32768,
            "Observed arithmetic domain differs from its original bounded domain")
    size = nonnegative(cache["arithmetic_entries"], "arithmetic cache entries", 256)
    categories = cache["arithmetic_categories"]
    require(type(categories) is dict and len(categories) <= 256
            and all(type(name) is str and 0 < len(name) <= 4096
                    and type(value) is int and 0 < value <= 256 for name, value in categories.items())
            and sum(categories.values()) == size, "Source cache occupancy does not reconcile")
    others = cache["other_existing_cache_entries"]
    require(type(others) is dict and set(others) <= {"_targets", "_poses", "_phase_cache", "_basis_cache"}
            and all(type(value) is int and 0 <= value <= 256 for value in others.values()),
            "Unexpected existing reference cache inventory")


def validate_snapshot(snapshot, *, full):
    require(type(snapshot) is dict and set(snapshot) == (FULL_FIELDS if full else SCALAR_FIELDS),
            "Unexpected setup snapshot fields")
    for name in SCALARS:
        nonnegative(snapshot[name], name)
    require(snapshot["checkpoint"] <= snapshot["reach_operations"] <= snapshot["shared_operations"],
            "Setup snapshot counters do not form nested subsets")
    if full:
        CORE.state(snapshot["shared_operations"], full_state(snapshot)["reach"])
        require(snapshot["checkpoint"] == snapshot["counts"].get("checkpoint", 0),
                "Setup checkpoint scalar differs from the full category map")
        cache_snapshot(snapshot["reference_cache"])


def typed(value, depth=0, tally=None):
    """Validate detached exact types; this is syntax/identity, not source evaluation."""
    tally = [0] if tally is None else tally
    tally[0] += 1
    require(type(value) is dict and depth <= 8 and tally[0] <= 512 and type(value.get("type")) is str,
            "Typed setup operand exceeds its structural allowance")
    kind = value["type"]
    if kind == "NoneType":
        require(set(value) == {"type"}, "Malformed typed None")
        return None
    if kind == "bool":
        require(set(value) == {"type", "value"} and type(value["value"]) is bool, "Malformed typed bool")
        return value["value"]
    if kind == "int":
        require(set(value) == {"type", "value"}, "Malformed typed integer fields")
        number = value["value"]
        if type(number) is dict:
            require(set(number) == {"integer_decimal"}, "Malformed large diagnostic integer")
            number = CORE.decimal(number["integer_decimal"])
            require(abs(number).bit_length() > 4096, "Noncanonical large diagnostic integer")
        else:
            require(type(number) is int and abs(number).bit_length() <= 4096,
                    "Unbounded native diagnostic integer")
        return number
    if kind == "float":
        require(set(value) == {"type", "hex"} and type(value["hex"]) is str and len(value["hex"]) <= 64,
                "Malformed typed binary64 value")
        number = float.fromhex(value["hex"])
        require(math.isfinite(number) and number.hex() == value["hex"], "Nonfinite or noncanonical binary64 bits")
        return number
    if kind == "str":
        require(set(value) == {"type", "value"} and type(value["value"]) is str and len(value["value"]) <= 4096,
                "Malformed bounded typed string")
        return value["value"]
    if kind == "Fraction":
        require(set(value) == {"type", "value"}, "Malformed typed exact rational")
        return CORE.rational(value["value"])
    if kind == "Interval":
        require(set(value) == {"type", "lo", "hi"}, "Malformed typed interval")
        low, high = (typed(value[name], depth + 1, tally) for name in ("lo", "hi"))
        require(value["lo"]["type"] == value["hi"]["type"] == "Fraction" and low <= high,
                "Independent interval endpoints are not ordered exact rationals")
        return (low, high)
    if kind in ("tuple", "list"):
        require(set(value) == {"type", "items"} and type(value["items"]) is list and len(value["items"]) <= 128,
                "Malformed bounded typed sequence")
        return tuple(typed(item, depth + 1, tally) for item in value["items"])
    raise ValueError("Unexpected setup operand type: " + kind)


def typed_scalar(value):
    number = typed(value)
    require(value["type"] in ("int", "float", "Fraction"), "Expected a native numeric scalar")
    return number


def nested_descriptor(row, reference_identity, domain, model_ids):
    label, supplied, result = row["label"], row["input"], row["result"]
    require(type(supplied) is dict, "Missing typed structural-call input")
    require(opaque(supplied.get("reference_identity"), "nested reference") == reference_identity,
            "Nested observations refer to another independent reference")
    if label in ("reference._phase", "reference._axial_derivatives"):
        require(set(supplied) == {"reference_identity", "state_identity", "model_identity", "carrier",
            "start", "end", "arithmetic_bits", "operand_limit_field"}, "Unexpected phase input fields")
        opaque(supplied["state_identity"], "phase state")
        model_ids.add(opaque(supplied["model_identity"], "phase model"))
        require(type(supplied["carrier"]) is str and 0 < len(supplied["carrier"]) <= 4096
                and supplied["arithmetic_bits"] == domain[0] and supplied["operand_limit_field"] == domain[1]
                and type(supplied["arithmetic_bits"]) is int and type(supplied["operand_limit_field"]) is int,
                "Phase carrier or arithmetic-domain observation differs")
        start, end = typed_scalar(supplied["start"]), typed_scalar(supplied["end"])
        require(0 <= start <= end, "Phase interval is invalid")
        if label == "reference._phase":
            require(type(result) is dict and set(result) == {"type", "start", "end", "carrier", "speed",
                    "acceleration", "angular_speed", "path"} and result["type"] == "ReferencePhase",
                    "Malformed detached ReferencePhase result")
            require(typed_scalar(result["start"]) == start and typed_scalar(result["end"]) == end
                    and typed(result["carrier"]) == supplied["carrier"], "Phase output identity differs from its request")
            for name in ("speed", "acceleration", "angular_speed"):
                require(typed_scalar(result[name]) >= 0, "Negative observed phase bound")
            typed(result["path"])
            require(result["path"]["type"] == "tuple"
                    and all(item["type"] == "str" for item in result["path"]["items"]),
                    "Phase ancestry is not a typed path tuple")
        elif type(result) is dict and result.get("type") == "NoneType":
            typed(result)
        else:
            require(type(result) is dict and set(result) == {"type", "speed", "acceleration", "axis", "rate"}
                    and result["type"] == "_AxialDerivative", "Malformed detached axial derivative result")
            require(typed_scalar(result["speed"]) >= 0 and typed_scalar(result["acceleration"]) >= 0,
                    "Negative observed axial bound")
            typed_scalar(result["rate"])
            axis = typed(result["axis"])
            require(axis is None or type(axis) is int and 0 <= axis <= 2, "Invalid observed axial axis")
        require(row["positional_count"] == 5 and row["keyword_names"] == [], "Structural-call signature differs")
    elif label == "reference._l1":
        require(set(supplied) == {"reference_identity", "vector"}, "Unexpected L1 input fields")
        typed(supplied["vector"])
        require(supplied["vector"]["type"] in ("tuple", "list")
                and all(item["type"] in ("int", "float", "Fraction", "Interval")
                        for item in supplied["vector"]["items"]), "L1 input contains unsupported operand types")
        require(typed_scalar(result) >= 0 and row["positional_count"] == 2 and row["keyword_names"] == [],
                "L1 result or signature differs")
    elif label == "reference._axis_transport":
        require(set(supplied) == {"reference_identity", "rotation", "axis"}, "Unexpected axis-transport input fields")
        typed(supplied["rotation"])
        require(supplied["rotation"]["type"] in ("tuple", "list")
                and len(supplied["rotation"]["items"]) == 4
                and all(item["type"] in ("int", "float", "Fraction", "Interval")
                        for item in supplied["rotation"]["items"]), "Axis transport quaternion is malformed")
        axis, sign = typed(supplied["axis"]), typed(result)
        require(type(axis) is int and 0 <= axis <= 2 and (sign is None or type(sign) is int and sign in (-1, 1))
                and row["positional_count"] == 3 and row["keyword_names"] == [],
                "Axis transport index, result or signature differs")
    else:
        raise ValueError("Undeclared nested structural function")


def source_function_line(raw, qualname):
    body = ast.parse(raw).body
    parts = qualname.split(".")
    for index, part in enumerate(parts):
        nodes = [node for node in body if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and node.name == part]
        require(len(nodes) == 1, "Observed setup function is missing or ambiguous in bound source")
        node = nodes[0]
        if index < len(parts) - 1:
            require(isinstance(node, ast.ClassDef), "Setup function qualifier is not a source class")
            body = node.body
    require(isinstance(node, ast.FunctionDef), "Setup target is not a source function")
    return min([node.lineno, *[decorator.lineno for decorator in node.decorator_list]])


def verify_targets(setup, repo, inputs):
    targets = setup["targets"]
    require(type(targets) is list and len(targets) == len(TARGETS), "Setup wrapper target inventory differs")
    for row, expected in zip(targets, TARGETS):
        label, module, qualname, nested, axial = expected
        require(type(row) is dict and set(row) == {"label", "name", "original", "source_file", "source_first_line",
                    "nested", "only_during_axial"} and row["label"] == label
                and row["name"] == qualname.split(".")[-1] and row["nested"] is nested
                and row["only_during_axial"] is axial, "Setup target declaration differs")
        require(CORE.same(row["original"], {"module": "ontokin." + module, "qualname": qualname,
                                          "bound_owner_type": None}), "Setup target original callable identity differs")
        path = repo / ("ontokin/" + module + ".py")
        require(type(row["source_file"]) is str and Path(row["source_file"]).resolve() == path,
                "Setup target points to a foreign source file")
        require(type(row["source_first_line"]) is int
                and row["source_first_line"] == source_function_line(inputs.read(path), qualname),
                "Setup target code first line differs from bound source syntax")
    restorations = setup["restorations"]
    boundaries = ("first_key_entry", "reader_exit", "final_cleanup")
    require(type(restorations) is list and [row.get("boundary") for row in restorations] == list(boundaries),
            "Setup restoration boundary sequence differs")
    labels = [row[0] for row in reversed(TARGETS)]
    for row, boundary in zip(restorations, boundaries):
        require(set(row) == {"boundary", "checks"} and type(row["checks"]) is list
                and [item.get("label") for item in row["checks"]] == labels, "Restoration target order differs")
        for item in row["checks"]:
            require(set(item) == {"label", "expected_dispatch", "was_wrapper", "was_original", "restored"}
                    and item["expected_dispatch"] is True and item["restored"] is True
                    and item["was_wrapper"] is (boundary == "first_key_entry")
                    and item["was_original"] is (boundary != "first_key_entry"),
                    "Setup dispatch was changed early or not restored at its declared boundary")


def repeat_inventory(spans, costs):
    exact = defaultdict(list)
    phase_groups = defaultdict(list)
    for row in spans:
        if row["label"] in ("reference._l1", "reference._axis_transport"):
            exact[(row["label"], CORE.canonical(row["input"]))].append(row)
        elif row["label"] == "reference._axial_derivatives":
            phase_groups[CORE.canonical({name: value for name, value in row["input"].items()
                                          if name != "carrier"})].append(row)
    repeats = []
    for (label, _), rows in exact.items():
        if len(rows) < 2:
            continue
        repeats.append({"label": label, "input": rows[0]["input"], "call_count": len(rows),
            "span_ids": [row["id"] for row in rows],
            "observed_result_variants": len({CORE.canonical(row["result"]) for row in rows}),
            "inclusive_observed_work": {name: sum(costs[row["id"]]["inclusive"][name] for row in rows)
                                        for name in SCALARS},
            "net_savings": None, "source_reuse_authority_established": False})
    repeats.sort(key=lambda row: (-row["inclusive_observed_work"]["reach_operations"], row["label"], row["span_ids"][0]))
    phases = [{"group": {name: value for name, value in rows[0]["input"].items() if name != "carrier"},
               "call_count": len(rows), "carriers": [row["input"]["carrier"] for row in rows],
               "span_ids": [row["id"] for row in rows],
               "inclusive_observed_work": {name: sum(costs[row["id"]]["inclusive"][name] for row in rows)
                                           for name in SCALARS},
               "same_state_identity_proves_equivalence": False} for rows in phase_groups.values()]
    return {"repeated_typed_arguments": repeats, "axial_phase_groups": phases,
            "group_identities_are_process_local": True, "net_savings_established": False,
            "interpretation": "Repeated typed values and within-run state IDs identify observations only. Admission, invalidation, lookup, insertion and displacement costs remain unmeasured."}


def reconcile_setup(repo, case, capture_dir, capture, source, ledger, inputs):
    setup = inputs.json(capture_dir / "reader-setup.json")
    require(setup["schema_version"] == "ontokin.reach-reader-setup-capture/0.1" and setup["case_id"] == case
            and setup["source_commit"] == source["source_commit"] and setup["source_tree"] == source["source_tree"]
            and CORE.same(setup["driver"], capture["driver"])
            and CORE.same(setup["actual_driver_command"], capture["actual_driver_command"]),
            "Setup artifact source, case or executed driver identity differs")
    require(setup["status"] == "captured_setup" and setup["product_request_status"] == "failed"
            and setup["accepted_artifact"] is False and setup["release_acceptance"] is False
            and setup["timing_neutrality_claimed"] is False and setup["optimization_saving_claimed"] is False
            and setup["disabled"] is False and type(setup["installations"]) is int and setup["installations"] == 1
            and type(setup["max_spans"]) is int and setup["max_spans"] == MAX_SPANS
            and setup["observation_errors"] == [] and setup["open_spans_at_cutoff"] == [],
            "Setup capture is incomplete, clipped, disabled or claims unsupported acceptance")
    CORE.check_identities(setup["identity_checks"], SETUP_IDENTITIES, "Reader setup")
    require(capture["identity_checks"].get("setup_dispatch_restored") is True
            and capture["identity_checks"].get("setup_restored_before_first_key") is True,
            "Failed-request capture does not bind setup restoration")
    verify_targets(setup, repo, inputs)
    spans = setup["spans"]
    require(type(spans) is list and 0 < len(spans) <= MAX_SPANS
            and CORE.same(capture["reader_setup"], {"path": "reader-setup.json", "status": "captured_setup",
                                                   "span_count": len(spans)}), "Setup span inventory differs")
    entry, cutoff = setup["entry"], setup["first_key_entry"]
    validate_snapshot(entry, full=True)
    validate_snapshot(cutoff, full=True)
    require(CORE.same(full_state(entry), {"shared_operations": capture["shared_operations_at_reader_entry"],
                                        "reach": capture["work_at_reader_entry"]}), "Setup entry differs from original reader entry")
    key_ledger = inputs.json(capture_dir / "key-ledger.json")
    first_key = key_ledger["keys"][0]
    require(first_key["index"] == 0
            and CORE.same(full_state(cutoff), {"shared_operations": first_key["entry"]["shared_operations"],
                                              "reach": first_key["entry"]["reach"]}),
            "Setup cutoff is not the unchanged first key entry")
    total = CORE.diff(full_state(entry), full_state(cutoff))
    setup_segment = [row for row in ledger["segments"] if row["kind"] == "reader_setup"]
    require(len(setup_segment) == 1 and all(CORE.same(total[name], setup_segment[0][name]) for name in total),
            "Setup total does not reconcile to the original independently audited work ledger")
    first_cache = cutoff["reference_cache"]
    require(first_cache is not None and first_cache["arithmetic_entries"] == first_key["entry"]["source_cache_entries"],
            "Setup reference-cache occupancy differs at the first key boundary")
    key_cache_categories = Counter()
    for name, value in first_key["entry"]["source_cache_categories"].items():
        key_cache_categories["reference_pose" if name.startswith("reference_pose:") else name] += value
    require(dict(key_cache_categories) == first_cache["arithmetic_categories"],
            "Setup reference-cache categories differ at the first key boundary")
    reference_identity = first_cache["reference_identity"]
    domain = (first_cache["arithmetic_bits"], first_cache["operand_limit_field"])
    entry_event, cutoff_event, event_count = setup["entry_event"], setup["first_key_entry_event"], setup["event_count"]
    require(all(type(value) is int for value in (entry_event, cutoff_event, event_count))
            and entry_event == 0 and cutoff_event == 2 * len(spans) + 1 and event_count == cutoff_event + 1,
            "Setup event envelope is not one complete bounded span sequence")
    events = {entry_event: ("reader_entry", None, entry), cutoff_event: ("first_key_entry", None, cutoff)}
    children = defaultdict(list)
    costs, model_ids = [], set()
    common_fields = {"id", "parent", "label", "nested", "outcome", "depth", "entry_event", "exit_event",
        "positional_count", "keyword_names", "entry", "exit", "clipped_at_first_key", "identity_checks"}
    for ordinal, row in enumerate(spans):
        require(type(row) is dict and type(row.get("nested")) is bool
                and set(row) == common_fields | ({"input", "result"} if row["nested"] else set()),
                "Unexpected setup span fields")
        require(type(row["id"]) is int and row["id"] == ordinal and row["label"] in TARGET_BY_LABEL
                and row["nested"] is TARGET_BY_LABEL[row["label"]][3]
                and row["outcome"] == "returned" and row["clipped_at_first_key"] is False,
                "Setup span identity, function or completion differs")
        parent = row["parent"]
        require(parent is None or type(parent) is int and 0 <= parent < ordinal, "Invalid setup span parent")
        nonnegative(row["depth"], "span depth", 63)
        nonnegative(row["positional_count"], "positional argument count", 64)
        require(type(row["keyword_names"]) is list and len(row["keyword_names"]) <= 64
                and all(type(name) is str and 0 < len(name) <= 128 for name in row["keyword_names"])
                and len(row["keyword_names"]) == len(set(row["keyword_names"])), "Invalid observed keyword inventory")
        CORE.check_identities(row["identity_checks"], SPAN_IDENTITIES, "Setup span")
        for boundary in ("entry", "exit"):
            validate_snapshot(row[boundary], full=not row["nested"])
            event = row[boundary + "_event"]
            require(type(event) is int and 0 < event < cutoff_event and event not in events,
                    "Duplicate or out-of-scope setup event")
            events[event] = (boundary, ordinal, row[boundary])
        require(row["entry_event"] < row["exit_event"], "Setup span returns before it enters")
        if row["nested"]:
            nested_descriptor(row, reference_identity, domain, model_ids)
        children[parent].append(ordinal)
        costs.append({"id": ordinal, "parent": parent, "label": row["label"], "depth": row["depth"],
                      "entry_event": row["entry_event"], "exit_event": row["exit_event"],
                      "inclusive": scalar_delta(row["entry"], row["exit"])})
    require(set(events) == set(range(event_count)), "Setup endpoint events are not contiguous")
    require(len(model_ids) <= 1, "Setup spans contain different private source models")
    stack, prior, prior_full, ordered_entries, cache_ids = [], entry, entry, [], set()
    for event in range(event_count):
        boundary, span_id, snapshot = events[event]
        scalar_delta(prior, snapshot)
        prior = snapshot
        if set(snapshot) == FULL_FIELDS:
            CORE.diff(full_state(prior_full), full_state(snapshot))
            prior_full = snapshot
            cache = snapshot["reference_cache"]
            if cache is not None:
                require(cache["reference_identity"] == reference_identity
                        and (cache["arithmetic_bits"], cache["operand_limit_field"]) == domain,
                        "Coarse observations change independent reference identity or domain")
                cache_ids.add(cache["arithmetic_identity"])
        if boundary == "entry":
            row = spans[span_id]
            require(row["parent"] == (stack[-1] if stack else None) and row["depth"] == len(stack),
                    "Setup parent/depth does not match replayed call stack")
            if TARGET_BY_LABEL[row["label"]][4]:
                require(any(spans[parent]["label"] == "reference._axial_derivatives" for parent in stack),
                        "Attachment observation occurred outside an axial call")
            if row["label"] == "reference._axial_derivatives":
                require(any(spans[parent]["label"] == "reference._phase" for parent in stack),
                        "Axial observation lacks its enclosing source phase")
            stack.append(span_id)
            ordered_entries.append(span_id)
        elif boundary == "exit":
            require(stack and stack[-1] == span_id, "Setup exit is unbalanced or crosses sibling spans")
            stack.pop()
        else:
            require(not stack, "Reader envelope boundary contains open setup spans")
    require(ordered_entries == list(range(len(spans))) and not stack and len(cache_ids) == 1,
            "Setup entry order or independent arithmetic ownership differs")
    for row in costs:
        row["exclusive"] = subtract_scalars(row["inclusive"], [costs[child]["inclusive"] for child in children[row["id"]]])
        if not spans[row["id"]]["nested"]:
            row["inclusive_category_delta"] = CORE.diff(full_state(spans[row["id"]]["entry"]),
                                                       full_state(spans[row["id"]]["exit"]))["reach_category_delta"]
        row["exclusive_category_delta"] = None
    root_ids = children[None]
    require(all(not spans[index]["nested"] for index in root_ids),
            "A root structural span lacks full-category boundary observations")
    segments, categories, previous, previous_label = [], Counter(), entry, "reader_entry"
    for index in root_ids:
        row = spans[index]
        gap = CORE.diff(full_state(previous), full_state(row["entry"]))
        segments.append({"kind": "unwrapped_setup", "after": previous_label, "before": row["label"], **gap})
        categories.update(gap["reach_category_delta"])
        delta = CORE.diff(full_state(row["entry"]), full_state(row["exit"]))
        segments.append({"kind": "observed_stage", "span_id": index, "label": row["label"], **delta})
        categories.update(delta["reach_category_delta"])
        previous, previous_label = row["exit"], row["label"]
    gap = CORE.diff(full_state(previous), full_state(cutoff))
    segments.append({"kind": "unwrapped_setup", "after": previous_label, "before": "first_key_entry", **gap})
    categories.update(gap["reach_category_delta"])
    require(dict(categories) == total["reach_category_delta"]
            and sum(row["shared_operations"] for row in segments) == total["shared_operations"]
            and sum(row["admitted_reach_operations"] for row in segments) == total["admitted_reach_operations"],
            "Disjoint setup stage categories fail to reconcile to the original interval")
    total_scalar = scalar_delta(entry, cutoff)
    residual = subtract_scalars(total_scalar, [costs[index]["inclusive"] for index in root_ids])
    require(all(sum(row["exclusive"][name] for row in costs) + residual[name] == total_scalar[name] for name in SCALARS),
            "Exclusive structural work plus unwrapped residual does not equal reader setup")
    forwarded = setup["recursive_forwarded_calls"]
    require(type(forwarded) is dict and set(forwarded) <= {"reader._assert_projection"}
            and all(type(value) is int and 0 < value <= 100000 for value in forwarded.values()),
            "Unexpected unobserved recursive forwarding")
    labels = Counter(row["label"] for row in spans)
    require(labels["reference.build_reference"] == 1
            and all(labels[label] >= 1 for label, _, _, nested, _ in TARGETS if not nested),
            "A required original reader-setup stage was not observed")
    by_label = []
    for label in sorted(labels):
        rows = [row for row in costs if row["label"] == label]
        by_label.append({"label": label, "calls": len(rows),
            "inclusive": {name: sum(row["inclusive"][name] for row in rows) for name in SCALARS},
            "exclusive": {name: sum(row["exclusive"][name] for row in rows) for name in SCALARS}})
    return {"schema_version": "ontokin.reach-reader-setup-analysis/0.1", "case_id": case,
        "status": "passed", "product_request_status": "failed", "accepted_artifact": False,
        "release_acceptance": False, "entry": entry, "first_key_entry": cutoff,
        "setup_total": total, "setup_scalar_total": total_scalar, "span_count": len(spans),
        "balanced_event_count": event_count, "disjoint_stage_ledger": segments,
        "span_costs": costs, "observed_costs_by_label": by_label, "unwrapped_setup_scalar_residual": residual,
        "complete_category_reconciliation": True, "complete_scalar_exclusive_reconciliation": True,
        "nested_full_category_attribution_available": False,
        "nested_category_note": "Nested structural spans carry shared/Reach/checkpoint scalars. Full category maps are reconciled only at coarse boundaries; nested exclusive category maps are not inferred.",
        "recursive_forwarded_calls": forwarded, "repeat_inventory": repeat_inventory(spans, costs),
        "identity_checks": setup["identity_checks"], "source_reuse_authority_established": False,
        "complete_request_cost": None, "optimization_savings": None, "elapsed_time_neutrality_claimed": False}


def main(argv=None):
    global CORE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--baseline-command", type=Path)
    parser.add_argument("--capture-command", type=Path)
    args = parser.parse_args(argv)
    CORE, dependency_path, dependency_raw = load_core()
    output_dir = args.output_dir.absolute()
    require(not output_dir.exists() and not any(path.is_symlink() for path in (output_dir, *output_dir.parents))
            and output_dir.parent.is_dir(), "Audit output must be a fresh directory with an existing nonsymlink parent")
    output_dir.mkdir()
    inputs = CORE.Inputs()
    baseline_dir, capture_dir = args.baseline.absolute(), args.capture.absolute()
    provenance = {"schema_version": "ontokin.reach-reader-setup-independent-audit/0.1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "scope": "Original failed P11/L03 control/capture pair and reader entry through first-key attribution",
        "product_request_status": "failed", "accepted_artifact": False, "release_acceptance": False,
        "complete_stock_harness": False, "source_numeric_accuracy_certified": False,
        "retained_artifact_validity_certified": False, "implementation": "Python standard library only",
        "execution": {"python": sys.version, "executable": sys.executable, "platform": platform.platform()},
        "actual_audit_command": [sys.executable, *sys.argv],
        "dependency_configuration": {"CAPTURE_PATH": COLLECTOR_PATH,
            "WRAPPER_NAMES": sorted(CORE.WRAPPER_NAMES), "other_policy_changes": []}}
    try:
        own_path = Path(__file__).absolute()
        own = inputs.read(own_path)
        require(inputs.read(dependency_path) == dependency_raw, "Loaded dependency bytes changed")
        provenance["auditor"] = {"path": str(own_path), "bytes": len(own), "sha256": CORE.digest(own)}
        provenance["unchanged_c060_dependency"] = {"path": str(dependency_path), "bytes": len(dependency_raw),
                                                  "sha256": CORE.digest(dependency_raw)}
        # Every original C060 check is retained, with only the exact collector
        # path changed. No extra traceback wrapper names are admitted.
        repo, case, capture, baseline, wrapped, source, comparison = CORE.compare_requests(baseline_dir, capture_dir, inputs)
        require(own_path.resolve() == repo / ADAPTER_PATH and dependency_path.resolve() == repo / CORE_PATH
                and not output_dir.resolve().is_relative_to(repo), "Auditor or output is outside its declared source/evidence scope")
        snapshot = inputs.json(baseline_dir / "inputs-before.json")
        named = {row["path"]: row for row in snapshot["files"]}
        for path in (ADAPTER_PATH, CORE_PATH, COLLECTOR_PATH, "tools/probe_reach_recording_work.py"):
            require(path in named, "Executed diagnostic/audit tool is absent from the tracked source snapshot: " + path)
            CORE.verify_descriptor(inputs, repo / path, named[path])
        census, authored, boundaries, tracks = CORE.census_bytes(repo, case, capture_dir, capture, baseline, inputs)
        ledger = CORE.reconcile_ledger(case, capture_dir, capture, baseline, census, authored, boundaries, tracks, inputs)
        failure = CORE.audit_failure_locals(repo, case, capture_dir, capture, baseline, ledger, inputs)
        commands = []
        for mode, directory, supplied in (("control", baseline_dir, args.baseline_command),
                                          ("capture", capture_dir, args.capture_command)):
            path = supplied.absolute() if supplied is not None else directory.parent.parent / "commands" / (case + "-" + mode + ".json")
            commands.append(CORE.audit_command(path, case, mode, directory, repo, source, baseline, inputs))
        setup = reconcile_setup(repo, case, capture_dir, capture, source, ledger, inputs)
        require(not any(name == "ontokin" or name.startswith("ontokin.") for name in sys.modules),
                "Offline audit unexpectedly imported product modules")
        receipts = inputs.stable_receipts()
        summary = CORE.compact_summary(case, comparison, census, ledger, failure)
        summary["reader_setup"] = {"shared_operations": setup["setup_total"]["shared_operations"],
            "reach_operations": setup["setup_total"]["admitted_reach_operations"], "span_count": setup["span_count"],
            "balanced_event_count": setup["balanced_event_count"],
            "unwrapped_residual": setup["unwrapped_setup_scalar_residual"],
            "observed_costs_by_label": setup["observed_costs_by_label"],
            "source_reuse_authority_established": False, "optimization_savings": None}
        members = [CORE.write_json(output_dir, name, value) for name, value in (
            ("summary.json", summary), ("work-ledger.json", ledger), ("byte-census.json", census),
            ("failure-analysis.json", failure), ("reader-setup-analysis.json", setup),
            ("input-receipts.json", {"all_inputs_stable": True, "files": receipts}))]
        CORE.write_json(output_dir, "audit.json", {**provenance, "status": "passed", "case_id": case,
            "assertions_checked": CORE.CHECKS, "comparison": comparison,
            "all_c060_checks_passed": True, "actual_command_receipts": commands,
            "members": members, "all_analysis_inputs_stable": True,
            "limitations": [
                "The original product request failed; this audit does not accept a recording, release or retained GLB.",
                "No product module is imported, source evaluated, failed request resumed or tail cost inferred.",
                "Materialized bytes and full Git tree identity are checked; omitted tracked payloads remain unverified.",
                "Only exact named C060 wrapper frame blocks are removed from the failed-request tracebacks.",
                "Full categories reconcile at coarse boundaries. Nested exclusive work uses shared/Reach/checkpoint scalars.",
                "Repeated operands and process-local identities do not establish cache admission authority or net savings.",
                "Observation equality establishes neither elapsed-time neutrality nor a future request guarantee."]})
        print(CORE.json.dumps({"status": "passed", "case_id": case, "product_request_status": "failed",
                              "reader_setup_operations": setup["setup_total"]["shared_operations"],
                              "release_acceptance": False, "output_dir": str(output_dir)}))
        return 0
    except Exception as error:
        record = {**provenance, "status": "failed", "assertions_checked": CORE.CHECKS,
            "error_type": type(error).__name__, "error": str(error), "traceback": traceback.format_exc(),
            "all_analysis_inputs_stable": False,
            "input_receipts_so_far": [inputs.records[name] for name in sorted(inputs.records)]}
        if not (output_dir / "audit.json").exists():
            CORE.write_json(output_dir, "audit.json", record)
        print(CORE.json.dumps({"status": "failed", "error_type": type(error).__name__, "error": str(error),
                              "output_dir": str(output_dir)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
