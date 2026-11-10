#!/usr/bin/env python3
"""Analytic C191 controls; imports no evaluator or adapter implementation."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import struct

import numpy as np

HERE = Path(__file__).resolve().parent
STOPS = {"A": 380., "B": 355., "C": 367.5, "D": 380.}


def build(case, fault="good"):
    parts = json.loads((HERE.parent / "frozen/c190-assembly.json").read_text())["parts"]
    near = STOPS[case]
    ideal = (near - 180) / 125
    times = np.arange(481, dtype=np.float64) / 240
    if fault == "missing-key":
        times = np.delete(times, 101)
    left = 125 * times if case == "D" else 125 * np.minimum(times, ideal)
    right = 150 * times
    if fault == "pass-through":
        left = 125 * times
    if fault == "baked-stop":
        left = 125 * np.minimum(times, 1.6)
    if fault == "hardcoded-time":
        left = 125 * np.minimum(times, 1.6)
    if fault == "residual-after-gate":
        index = round((ideal + .1) * 240)
        left[index] += .003
    if fault == "allowed-settling":
        index = round(ideal * 240) + 3
        left[index] += .003
    if fault == "transient-penetration":
        index = round(ideal * 240) + 1
        left[index] += .6
    if fault == "early-rebound":
        index = round(ideal * 240) + 3
        left[index] -= .12
    if fault == "wrong-pre-speed":
        left[96] += .003
    if fault == "wrong-right-speed":
        right[96] += .003
    if fault == "wrong-final":
        left[-1] += .6
    doc = {"asset": {"version": "2.0", "generator": "Independent analytic C191 fixtures"},
        "scene": 0, "scenes": [{"nodes": []}], "nodes": [], "meshes": [], "materials": [],
        "accessors": [], "bufferViews": [], "buffers": [],
        "animations": [{"channels": [], "samplers": []}]}
    blob = bytearray()

    def access(values, kind, component=5126):
        arr = np.array(values, dtype={5126: "<f4", 5123: "<u2"}[component])
        if kind == "SCALAR":
            arr = arr.reshape(-1, 1)
        blob.extend(b"\0" * (-len(blob) % 4))
        view = len(doc["bufferViews"])
        doc["bufferViews"].append({"buffer": 0, "byteOffset": len(blob), "byteLength": arr.nbytes})
        blob.extend(arr.tobytes())
        index = len(doc["accessors"])
        doc["accessors"].append({"bufferView": view, "componentType": component, "type": kind,
            "count": len(arr), "min": arr.min(0).tolist(), "max": arr.max(0).tolist()})
        return index

    corners = np.array(list(itertools.product([-1, 1], repeat=3)))
    corner_index = {tuple(c): index for index, c in enumerate(corners)}
    triangles = []
    for axis in range(3):
        for side in (-1, 1):
            quad = []
            for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                location = np.zeros(3, dtype=int)
                location[axis], location[(axis + 1) % 3], location[(axis + 2) % 3] = side, x, y
                quad.append(corner_index[tuple(location)])
            if side == -1:
                quad.reverse()
            a, b, c, d = quad
            triangles.extend([a, b, c, a, c, d])
    centers, nodes = {}, {}
    for part in parts:
        name = part["id"]
        low, high = np.array(part["worldBoundsAt0Mm"], dtype=float)
        if name == "left_stop":
            low[0] += near - 495
            high[0] += near - 495
        if fault == "unrelated-overlap" and name in ("left_carriage", "left_shoe"):
            low[1] -= .01
            high[1] -= .01
        center = (low + high) / 2000
        centers[name] = center
        vertices = corners * (high - low) / 2000
        indices = triangles[:-3] if fault == "missing-face" and name == "left_shoe" else triangles
        output_name = "renamed_unknown_shoe" if fault == "wrong-id" and name == "left_shoe" else name
        material = len(doc["materials"])
        color = part["baseColorLinearRGB"]
        if fault == "wrong-color" and name == "left_shoe":
            color = [color[0] + .006, *color[1:]]
        doc["materials"].append({"pbrMetallicRoughness": {"baseColorFactor": color + [1.]}})
        mesh = len(doc["meshes"])
        doc["meshes"].append({"name": output_name, "primitives": [{"attributes": {"POSITION": access(vertices, "VEC3")},
            "indices": access(indices, "SCALAR", 5123), "material": material}]})
        node = {"name": output_name, "mesh": mesh, "translation": center.tolist()}
        nodes[name] = len(doc["nodes"])
        if name.endswith("_shoe"):
            owner = name.replace("_shoe", "_carriage")
            node["translation"] = (center - centers[owner]).tolist()
            doc["nodes"][nodes[owner]]["children"] = [len(doc["nodes"])]
        else:
            doc["scenes"][0]["nodes"].append(len(doc["nodes"]))
        doc["nodes"].append(node)
    animation = doc["animations"][0]

    def track(name, values):
        animation["channels"].append({"target": {"node": nodes[name], "path": "translation"},
            "sampler": len(animation["samplers"])})
        animation["samplers"].append({"input": access(times, "SCALAR"),
            "output": access(values, "VEC3"), "interpolation": "LINEAR"})

    for lane, motion in (("left", left), ("right", right)):
        name = lane + "_carriage"
        track(name, centers[name] + np.column_stack([motion / 1000, 0 * motion, 0 * motion]))
    if fault == "attachment-drift":
        local = np.array(doc["nodes"][nodes["left_shoe"]]["translation"])
        drift = .00011 * np.sin(np.pi * times / 2)
        track("left_shoe", local + np.column_stack([drift, 0 * drift, 0 * drift]))
    if fault == "fixed-drift":
        drift = .00011 * np.sin(np.pi * times / 2)
        track("base", centers["base"] + np.column_stack([drift, 0 * drift, 0 * drift]))
    blob.extend(b"\0" * (-len(blob) % 4))
    doc["buffers"] = [{"byteLength": len(blob)}]
    header = json.dumps(doc, separators=(",", ":"), allow_nan=False).encode()
    header += b" " * (-len(header) % 4)
    return (struct.pack("<4sII", b"glTF", 2, 28 + len(header) + len(blob)) +
        struct.pack("<I4s", len(header), b"JSON") + header +
        struct.pack("<I4s", len(blob), b"BIN\0") + blob)


def definitions():
    rows = []
    for case in STOPS:
        rows.append((case, "good", True, None))
        shared = {"missing-key": "C191_CADENCE", "wrong-final": "C191_FINAL_TRAVEL",
            "wrong-right-speed": "C191_FEED_SPEED", "unrelated-overlap": "C191_UNRELATED_OVERLAP",
            "attachment-drift": "C191_ATTACHMENT_DRIFT", "fixed-drift": "C191_FIXED_DRIFT",
            "missing-face": "incomplete or overlapping cuboid face", "wrong-id": "mesh node and mesh must share",
            "wrong-color": "C191_COLOR"}
        rows.extend((case, name, False, code) for name, code in shared.items())
        if case != "D":
            rows.append((case, "allowed-settling", True, None))
            rows.extend((case, name, False, code) for name, code in {
                "pass-through": "C191_FINAL_TRAVEL", "residual-after-gate": "C191_SETTLED_SPEED",
                "transient-penetration": "C191_CONTINUOUS_PENETRATION", "early-rebound": "C191_REBOUND",
                "wrong-pre-speed": "C191_PRECONTACT_SPEED"}.items())
            rows.append((case, "hardcoded-time", case == "A", None if case == "A" else "C191_FINAL_TRAVEL"))
        else:
            rows.append((case, "baked-stop", False, "C191_FINAL_TRAVEL"))
    return rows


def generate(destination):
    destination.mkdir(parents=True, exist_ok=True)
    manifest = []
    for case, fault, passing, reason in definitions():
        data = build(case, fault)
        name = f"{case}-{fault}.glb"
        (destination / name).write_bytes(data)
        manifest.append({"case": case, "fault": fault, "file": name, "sha256": hashlib.sha256(data).hexdigest(),
            "expected_pass": passing, "expected_reason_contains": reason})
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    records = generate(args.out)
    (args.out / "manifest.json").write_text(json.dumps(records, indent=2) + "\n")
    print(json.dumps({"controls": len(records), "positive": sum(row["expected_pass"] for row in records)}))
