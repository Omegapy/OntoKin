#!/usr/bin/env python3
"""Run the frozen .22 hostile mutations through the actual Agent byte reader.

Every fixture first re-exports and accepts its exact original. Each hostile
export executes the unchanged producer, then injects only the prescribed
mutated bytes at encoding. Independent validation and durable publication are
ordinary product operations under the unchanged frozen request allocation.
"""
from __future__ import annotations
import argparse
import copy
from datetime import datetime, timezone
from fractions import Fraction as F
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3
import struct
import subprocess
import sys
import traceback
from unittest.mock import patch


def sha(data): return hashlib.sha256(data).hexdigest()
def save(path, value): path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
def ratio(value): return F(int(value["numerator"]), int(value["denominator"]))
def rational(value):
    value = F(value)
    return {"numerator": str(value.numerator), "denominator": str(value.denominator)}
def up(value):
    value = F(value); number = float(value)
    return math.nextafter(number, math.inf) if F(number) < value else number


def unpack(raw):
    magic, version, length = struct.unpack_from("<III", raw)
    assert magic == 0x46546C67 and version == 2 and length == len(raw)
    size, kind = struct.unpack_from("<II", raw, 12)
    assert kind == 0x4E4F534A
    document = json.loads(raw[20:20 + size])
    binary_size, binary_kind = struct.unpack_from("<II", raw, 20 + size)
    assert binary_kind == 0x004E4942 and len(raw) == 28 + size + binary_size
    return document, bytearray(raw[28 + size:])


def pack(document, binary):
    text = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=True).encode("utf-8")
    text += b" " * (-len(text) % 4)
    binary = bytes(binary) + b"\0" * (-len(binary) % 4)
    return (struct.pack("<III", 0x46546C67, 2, 28 + len(text) + len(binary)) +
            struct.pack("<II", len(text), 0x4E4F534A) + text +
            struct.pack("<II", len(binary), 0x004E4942) + binary)


def one(values, label):
    assert len(values) == 1, (label, len(values))
    return values[0]


def carrier_node(document, name):
    return one([i for i, row in enumerate(document["nodes"])
                if row.get("extras", {}).get("ontokin", {}).get("path") == name], name)


def accessor(document, binary, index):
    a = document["accessors"][index]; v = document["bufferViews"][a["bufferView"]]
    assert a["componentType"] == 5126
    size = {"SCALAR": 1, "VEC3": 3, "VEC4": 4}[a["type"]]
    stride = v.get("byteStride", size * 4)
    assert stride == size * 4
    begin = v.get("byteOffset", 0) + a.get("byteOffset", 0)
    return a, begin, size, stride


def channel_accessor(document, carrier, target):
    node = carrier_node(document, carrier); animation = document["animations"][0]
    channel = one([c for c in animation["channels"]
                   if c["target"] == {"node": node, "path": target}], (carrier, target))
    return animation["samplers"][channel["sampler"]]["output"]


def append_accessor(document, binary, index, selected):
    a, begin, size, stride = accessor(document, binary, index)
    data = b"".join(binary[begin + i * stride:begin + (i + 1) * stride] for i in selected)
    length = document["buffers"][0]["byteLength"]
    del binary[length:]
    binary.extend(b"\0" * (-len(binary) % 4)); offset = len(binary); binary.extend(data)
    document["buffers"][0]["byteLength"] = len(binary)
    view = {"buffer": 0, "byteOffset": offset, "byteLength": len(data)}
    document["bufferViews"].append(view)
    a.update(bufferView=len(document["bufferViews"]) - 1, count=len(selected))
    a.pop("byteOffset", None)
    values = [struct.unpack_from("<" + "f" * size, data, i * stride) for i in range(len(selected))]
    for field, fn in (("min", min), ("max", max)):
        if field in a: a[field] = [fn(value[i] for value in values) for i in range(size)]


def shorten_accessors_in_place(document, binary, indices, selected):
    """Delete animation rows while retaining canonical view order and storage.

    Appending replacement animation views after immutable texture payloads
    changes the inherited layout contract and causes an unrelated texture
    refusal. Repack the existing views in their original order instead; only
    selected animation rows and resulting byte offsets/counts may change.
    Every geometry, UV and PNG view retains its exact original bytes.
    """
    replacements = {}
    originals = [bytes(binary[view.get("byteOffset", 0):view.get("byteOffset", 0) + view["byteLength"]])
                 for view in document["bufferViews"]]
    for index in sorted(indices):
        item, begin, size, stride = accessor(document, binary, index)
        view = item["bufferView"]
        assert view not in replacements and item.get("byteOffset", 0) == 0
        assert len(originals[view]) == item["count"] * stride
        data = b"".join(binary[begin + i*stride:begin + (i+1)*stride] for i in selected)
        replacements[view] = data
        item["count"] = len(selected)
        values = [struct.unpack_from("<" + "f" * size, data, i * stride) for i in range(len(selected))]
        for field, fn in (("min", min), ("max", max)):
            if field in item: item[field] = [fn(value[i] for value in values) for i in range(size)]
    packed = bytearray()
    for index, view in enumerate(document["bufferViews"]):
        packed.extend(b"\0" * (-len(packed) % 4))
        data = replacements.get(index, originals[index])
        view["byteOffset"], view["byteLength"] = len(packed), len(data)
        packed.extend(data)
    document["buffers"][0]["byteLength"] = len(packed)
    binary[:] = packed


def select_json(document, selector):
    """Resolve only the explicit frozen structural selectors."""
    def selected_index(array, query):
        if query.isdecimal(): return int(query)
        clauses = dict(item.split("=", 1) for item in query.split(","))
        def matches(row):
            for key, expected in clauses.items():
                if key == "authored-right-clock":
                    clocks = document["animations"][0]["extras"]["ontokin"]["exact_times_seconds"]
                    if ratio(clocks[row["right_key_index"]]) != F(0.1): return False
                elif key == "authored-Alpha":
                    if row["angular_acceleration_bound_rad_per_s2"] != float(expected): return False
                elif key == "left_key_index" and expected == "first-row-with-positive-width-phase":
                    if ratio(row["h_authored_seconds"]) <= 0: return False
                else:
                    observed = row
                    for field in key.split("."): observed = observed[field]
                    if observed != (int(expected) if key.endswith("index") else expected): return False
            return True
        selected = [i for i, row in enumerate(array) if matches(row)]
        if clauses.get("left_key_index") == "first-row-with-positive-width-phase":
            selected = sorted(selected, key=lambda i: array[i]["left_key_index"])[:1]
        return one(selected, query)
    parts = selector.split("/")[1:]; value = document
    for part in parts[:-1]:
        if "[" in part:
            name, query = part.split("[", 1); array = value[name]
            value = array[selected_index(array, query[:-1])]
        else: value = value[part]
    leaf = parts[-1]
    if "[" in leaf:
        name, query = leaf.split("[", 1); array = value[name]
        return array, selected_index(array, query[:-1])
    return value, leaf


def mutate(raw, case):
    document, binary = unpack(raw); original_binary = bytes(binary)
    metadata = document["extras"]["ontokin"]; quantization = metadata["reach_quantization"]
    operation = case["mutation"]["operation"]; selector = case["selector"]; identifier = case["id"]
    receipt = {"case": identifier, "selector": selector, "operation": operation}
    if selector.startswith("/extras/"):
        parent, leaf = select_json(document, selector)
        if operation == "delete": del parent[leaf]
        elif operation == "replace": parent[leaf] = copy.deepcopy(case["mutation"]["value"])
        elif operation == "add": parent[leaf][case["mutation"]["key"]] = case["mutation"]["value"]
        elif operation == "delete-first": del parent[leaf][0]
        elif operation == "duplicate-first": parent[leaf].insert(0, copy.deepcopy(parent[leaf][0]))
        elif operation == "replace-right-index-with-left": parent[leaf][0]["right_key_index"] = parent[leaf][0]["left_key_index"]
        elif operation == "append-first-again": parent[leaf].append(parent[leaf][0])
        elif operation == "raw-json-number-token": parent[leaf] = float("nan")
        elif operation == "multiply-both-integer-strings":
            for key in ("numerator", "denominator"):
                parent[leaf][key] = str(int(parent[leaf][key]) * case["mutation"]["factor"])
        elif identifier == "self-consistent-understatement":
            row = parent[leaf]; row.update(angular_acceleration_bound_rad_per_s2=0.0,
                                          enclosing_angular_acceleration_bound_rad_per_s2=0.0)
            h = ratio(row["h_authored_seconds"]); q = lambda name: F(row[name])
            row["unit_quaternion_difference_bound"] = up(q("max_endpoint_unit_quaternion_error") + q("angular_speed_bound_rad_per_s")**2*h*h/32 + q("stored_quaternion_arc_upper_rad")**2/8)
            row["ideal_rotation_bound_rad"] = up(q("angular_speed_bound_rad_per_s")**2*h*h/4)
            row["total_rotation_bound_rad"] = up(4*q("unit_quaternion_difference_bound") + q("source_numeric_rotation_bound_rad") + q("destination_numeric_rotation_bound_rad") + q("enclosing_angular_speed_bound_rad_per_s")*q("max_endpoint_time_shift_s"))
            row["total_position_bound_m"] = up(q("carrier_position_bound_m") + q("landmark_radius_m")*q("total_rotation_bound_rad") + q("local_vertex_error_bound_m"))
        else: raise AssertionError((identifier, operation))
    elif identifier.startswith("history-"):
        state = metadata["boundary_states"][-1 if identifier == "history-drop-shadow" else 0]["torque_states_after"]["ball"]
        if identifier in ("history-axis", "history-key", "history-sign", "history-program", "history-span"):
            record = one([row for row in state["active"] if row["torque_key"] == "drive"], "drive")
            key = {"history-axis": "axis", "history-key": "torque_key", "history-sign": "torque_n_m", "history-program": "program_revision", "history-span": "start_byte"}[identifier]
            if identifier == "history-span": record = record["source_location"]
            record[key] = case["mutation"]["value"]
        elif identifier == "history-missing-zero": del state["active"][0]
        elif identifier == "history-reordered": state["active"].reverse()
        elif identifier == "history-fake-route": state["rotation_route"] = case["mutation"]["value"]
        elif identifier == "history-drop-shadow": state["angular_error_bound_rad"] = copy.deepcopy(case["mutation"]["value"])
        else: raise AssertionError(identifier)
    elif identifier == "root-topology":
        root, child = carrier_node(document, "ball"), carrier_node(document, "ball.label")
        assert "children" not in document["nodes"][root]
        document["nodes"][root]["children"] = [child]
        document["scenes"][document.get("scene", 0)]["nodes"].remove(child)
    elif identifier in ("actual-clock-binary32-rounding", "reordered-common-clock", "different-channel-clock"):
        animation = document["animations"][0]; index = animation["samplers"][0]["input"]
        if identifier == "different-channel-clock":
            original = copy.deepcopy(document["accessors"][index]); document["accessors"].append(original)
            index = len(document["accessors"]) - 1
            append_accessor(document, binary, index, list(range(original["count"])))
            animation["samplers"][1]["input"] = index
        a, begin, size, stride = accessor(document, binary, index); assert size == 1 and a["count"] > 3
        first = one([i for i in range(1, a["count"] - 1) if struct.unpack_from("<f", binary, begin + 4*i)[0] > 0][:1], "first positive interior")
        if identifier == "reordered-common-clock":
            binary[begin+4*first:begin+4*(first+2)] = binary[begin+4*(first+1):begin+4*(first+2)] + binary[begin+4*first:begin+4*(first+1)]
        else:
            bits = struct.unpack_from("<I", binary, begin + 4*first)[0]
            struct.pack_into("<I", binary, begin + 4*first, bits + 1)
        receipt.update(accessor=index, key_index=first)
    elif identifier == "incoherent-quaternion-sign":
        index = channel_accessor(document, "ball", "rotation"); a, begin, size, stride = accessor(document, binary, index)
        middle = a["count"] // 2; assert 0 < middle < a["count"] - 1 and size == 4
        for component in range(4):
            offset = begin + middle*stride + component*4
            struct.pack_into("<I", binary, offset, struct.unpack_from("<I", binary, offset)[0] ^ (1 << 31))
        receipt.update(accessor=index, key_index=middle)
    elif identifier == "equal-endpoints-delete-interior":
        animation = document["animations"][0]; clocks = animation["extras"]["ontokin"]["exact_times_seconds"]
        assert ratio(clocks[0]) == 0 and ratio(clocks[-1]) == 1
        count = len(clocks); old = quantization["interval_certificates"]
        indices = {s[key] for s in animation["samplers"] for key in ("input", "output")}
        shorten_accessors_in_place(document, binary, indices, [0, count-1])
        animation["extras"]["ontokin"]["exact_times_seconds"] = [clocks[0], clocks[-1]]
        quantization["retained_keys"] = [quantization["retained_keys"][0], quantization["retained_keys"][-1]]
        rows = []
        for node in document["nodes"]:
            path = node["extras"]["ontokin"]["path"]
            originals = [r for r in old if r["carrier"]["path"] == path]
            row = copy.deepcopy(one([r for r in originals if r["left_key_index"] == 0], path))
            row.update(left_key_index=0, right_key_index=1, h_authored_seconds=rational(1), h_stored_seconds=rational(1))
            row["source_phase_indices"] = sorted({i for r in originals for i in r["source_phase_indices"]})
            # Both retained exact endpoints are unchanged. Their old complete
            # endpoint ceilings therefore still enclose the new endpoint pair.
            for key in ("max_endpoint_position_error_m", "max_endpoint_unit_quaternion_error", "max_endpoint_time_shift_s"):
                row[key] = max(originals[0][key], originals[-1][key])
            rows.append(row)
        quantization["interval_certificates"] = rows
        receipt.update(old_key_count=count, new_key_count=2)
    else: raise AssertionError((identifier, selector))
    mutated = pack(document, binary)
    assert mutated != raw
    receipt.update(original_sha256=sha(raw), hostile_sha256=sha(mutated), hostile_bytes=len(mutated),
                   bin_changed=bytes(binary) != original_binary)
    if selector.startswith("/extras/") or identifier.startswith("history-") or identifier == "root-topology":
        assert bytes(binary) == original_binary
    return mutated, receipt


def inventory(store):
    path = store / "torque-program-agent.sqlite3"
    with sqlite3.connect("file:" + str(path) + "?mode=ro", uri=True) as db:
        rows = db.execute("SELECT project_id,id,source_revision,sha256,data FROM artifacts ORDER BY project_id,id").fetchall()
    return [{"project_id": p, "artifact_id": i, "program_revision": r, "sha256": digest,
             "bytes": len(data), "actual_sha256": "sha256:" + sha(data)} for p,i,r,digest,data in rows]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--accepted", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--case", action="append")
    args = parser.parse_args(); root = args.checkout.resolve(); sys.path.insert(0, str(root))
    from ontokin.torque_agent import TorqueAgentService
    from ontokin.execution_budget import HostPolicy
    from ontokin.texture_bundle import load_texture_file_manifest
    from ontokin import gltf
    frozen = root / "docs/language-design/torque-v0.1/freeze"
    hostiles = json.loads((frozen / "hostile-delivery-cases.json").read_bytes())["cases"]
    hostiles = [row for row in hostiles if not args.case or row["id"] in args.case]
    assert not args.case or len(hostiles) == len(args.case)
    deliveries = {r["id"]: r for r in json.loads((frozen / "delivery-cases.json").read_bytes())["cases"]}
    args.output.mkdir(parents=True, exist_ok=False); controls = {}; results = []
    store = args.output / "store"
    identity = {"schema_version": "ontokin.c091-actual-agent-hostile-bytes/1", "started": datetime.now(timezone.utc).isoformat(),
        "source_revision": subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip(),
        "harness_sha256": sha(Path(__file__).read_bytes()), "frozen_cases_sha256": sha((frozen / "hostile-delivery-cases.json").read_bytes()),
        "scope": "Actual unchanged producer plus selected encoding-byte injection; normal independent reader and durable Agent publication under frozen caps."}
    save(args.output / "identity.json", identity)
    for case in hostiles:
        row = {"id": case["id"], "status": "failed", "case": case}; folder=args.output/case["id"]; folder.mkdir()
        try:
            fixture = case["original_fixture"]; delivery = deliveries[fixture]
            original_result = json.loads((args.accepted / fixture / "original/result.json").read_bytes())
            assert original_result["status"] == "passed"
            original = (args.accepted / fixture / "original" / original_result["artifact"]["path"]).read_bytes()
            assert sha(original) == original_result["artifact"]["sha256"]
            bundle = load_texture_file_manifest(frozen / delivery["file_manifest"])
            base = {"schema_version": "ontokin.agent/0.22", "project_id": fixture}
            if fixture not in controls:
                with TorqueAgentService(store, host_policy=HostPolicy(**delivery["host_policy"])) as service:
                    create = {**base, "request_id": fixture+"-create", "operation": "create", "requested_level": "constructed", "expected_program_revision": None, "bundle": bundle.to_payload()}
                    made = service.handle(create); assert made["status"] == "succeeded", made
                    request = {**base, "request_id": fixture+"-original", "operation": "export", "destination": "ontokin.glb/0.22", "program_revision": bundle.program_revision, "options": delivery["options"]}
                    response = service.handle(request); assert response["status"] == "succeeded", response
                    assert response["result"]["sha256"] == "sha256:" + sha(original)
                controls[fixture] = {"create_request": create,"create_response": made,"export_request": request,"export_response": response,"accepted_original_path": str(args.accepted / fixture / "original" / original_result["artifact"]["path"]),"accepted_original_sha256": sha(original)}
                save(args.output / (fixture+"-control.json"), controls[fixture])
            before = inventory(store); mutated, receipt = mutate(original, case)
            (folder / "hostile.glb").write_bytes(mutated); save(folder / "mutation.json", receipt)
            encoder = gltf._encode; called=[]
            def injected(*a, **kw):
                actual, error = encoder(*a, **kw)
                assert actual == original, "The unchanged normal producer no longer matches the accepted original"
                called.append({"actual_original_sha256": sha(actual), "replacement_sha256": sha(mutated)})
                return mutated, error
            request = {**base, "request_id": case["id"]+"-hostile", "operation": "export", "destination": "ontokin.glb/0.22", "program_revision": bundle.program_revision,"options": delivery["options"]}
            with TorqueAgentService(store, host_policy=HostPolicy(**delivery["host_policy"])) as service, patch.object(gltf, "_encode", injected):
                response = service.handle(request)
            after = inventory(store); save(folder / "request.json", request); save(folder / "response.json", response)
            assert len(called) == 1, called
            assert response["status"] == case["expected_agent_status"], response
            diagnostic = one([d for d in response["diagnostics"] if d["details"].get("export_code") == case["expected_export_code"]], "expected refusal")
            for field, key in (("code", "expected_code"), ("phase", "expected_phase"),("category", "expected_category"),("blocks", "expected_blocks")):
                assert diagnostic[field] == case[key], (field,diagnostic[field],case[key])
            for field, value in case["expected_details"].items(): assert diagnostic["details"][field] == value, (field, diagnostic)
            assert before == after and all(r["sha256"] != "sha256:" + sha(mutated) for r in after)
            row.update(status="passed", mutation=receipt, injection=called, diagnostic=diagnostic,
                       inventory_before=before, inventory_after=after, source_budget=response.get("execution_budget"))
        except BaseException as error:
            row.update(error=repr(error), traceback=traceback.format_exc())
        save(folder / "result.json", row); results.append({"id":row["id"],"status":row["status"],"result_sha256":sha((folder/"result.json").read_bytes()),"error":row.get("error")})
        print(json.dumps(results[-1]),flush=True)
        save(args.output / "summary.json", {**identity,"status":"passed" if all(r["status"]=="passed" for r in results) else "failed","cases":results,"controls":sorted(controls)})
    return int(any(r["status"] != "passed" for r in results))


if __name__ == "__main__": raise SystemExit(main())
