"""W4 audit 001, a05: item 5, the numerical audit, recomputed with this auditor's own code.

Usage: a05_numeric.py COHORT_ROOT C18_RECORD OUTPUT

For each case (Q01-positive, Q03-positive, Q01-changed-reference) of the cohort root:
  1. this script's own GLB reader (header, JSON and BIN chunks, accessors) gives each mesh node's
     float32 positions, normals and indices, and the node transforms; they are compared with the
     importer values that probe.json retains (positions, normals and indices exactly; the world matrices
     composed here in float64 within 1e-12);
  2. the expected row inventory is built from the retained reference (synthetic-audit.json) alone,
     in the probe's order: for each node identity in sorted order, 16 world-matrix terms; for each
     mesh node, one world-position row and one normal row per vertex and axis; then the minimum,
     maximum and size of the world bounds per axis;
  3. every row's actual value is recomputed: matrix terms are the retained importer world matrix; world
     positions are recomputed from the retained local positions and world matrix in the operation order
     of Three.js r186 Vector3.applyMatrix4; bounds from those positions; normals the retained values;
  4. difference = |actual - expected|; threshold = 5e-6 for positions, bounds and the terms [0..2][3],
     1e-6 otherwise; decision = finite and difference <= threshold;
  5. the rows are compared with probe.json's measurements (order, identity, every value), completeness and
     uniqueness are checked, and the findings are compared;
  6. the reference itself: its world vertices against its own world matrix and positions, and the changed
     reference against Q01's, member by member.
Finally the result is compared with C18's record. Starts nothing (an audit hook refuses process creation).
"""
import hashlib
import json
import math
import os
import struct
import sys


def _refuse(event, args):
    if event in ("subprocess.Popen", "os.posix_spawn", "os.exec", "os.fork", "os.forkpty", "os.spawn",
                 "os.system", "os.startfile"):
        raise PermissionError("this audit script starts no process: " + event)


sys.addaudithook(_refuse)
POSITION_THRESHOLD = 0.000005
MATRIX_THRESHOLD = 0.000001
CASES = ("Q01-positive", "Q03-positive", "Q01-changed-reference")


def read_glb(path):
    data = open(path, "rb").read()
    magic, version, length = struct.unpack_from("<III", data, 0)
    assert magic == 0x46546C67 and version == 2 and length == len(data), "GLB header"
    offset, chunks = 12, []
    while offset < length:
        chunk_length, chunk_type = struct.unpack_from("<II", data, offset)
        chunks.append((chunk_type, data[offset + 8: offset + 8 + chunk_length]))
        offset += 8 + chunk_length
    assert chunks[0][0] == 0x4E4F534A and chunks[1][0] == 0x004E4942, "GLB chunk types"
    gltf = json.loads(chunks[0][1].decode("utf-8"))
    return gltf, chunks[1][1], len(chunks)


def accessor_values(gltf, binary, index):
    accessor = gltf["accessors"][index]
    view = gltf["bufferViews"][accessor["bufferView"]]
    components = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[accessor["type"]]
    fmt, size = {5126: ("f", 4), 5123: ("H", 2), 5125: ("I", 4), 5121: ("B", 1)}[accessor["componentType"]]
    stride = view.get("byteStride") or size * components
    base = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    values = []
    for i in range(accessor["count"]):
        item = struct.unpack_from("<" + fmt * components, binary, base + i * stride)
        values.append(list(item) if components > 1 else item[0])
    return accessor, values


def mat_identity():
    return [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]


def compose(t, q, s):
    """Three.js Matrix4.compose, column-major elements."""
    x, y, z, w = q
    x2, y2, z2 = x + x, y + y, z + z
    xx, xy, xz = x * x2, x * y2, x * z2
    yy, yz, zz = y * y2, y * z2, z * z2
    wx, wy, wz = w * x2, w * y2, w * z2
    sx, sy, sz = s
    return [(1 - (yy + zz)) * sx, (xy + wz) * sx, (xz - wy) * sx, 0.0,
            (xy - wz) * sy, (1 - (xx + zz)) * sy, (yz + wx) * sy, 0.0,
            (xz + wy) * sz, (yz - wx) * sz, (1 - (xx + yy)) * sz, 0.0,
            t[0], t[1], t[2], 1.0]


def multiply(a, b):
    """Column-major a * b."""
    out = [0.0] * 16
    for row in range(4):
        for col in range(4):
            out[col * 4 + row] = (a[row] * b[col * 4] + a[4 + row] * b[col * 4 + 1] + a[8 + row] * b[col * 4 + 2]
                                  + a[12 + row] * b[col * 4 + 3])
    return out


def rows_of(elements):
    return [[elements[j * 4 + i] for j in range(4)] for i in range(4)]


def apply_matrix4(m, p):
    """Three.js r186 Vector3.applyMatrix4 on a row-indexed matrix m[i][j], in its operation order."""
    x, y, z = p
    w = 1 / (m[3][0] * x + m[3][1] * y + m[3][2] * z + m[3][3])
    return [(m[0][0] * x + m[0][1] * y + m[0][2] * z + m[0][3]) * w,
            (m[1][0] * x + m[1][1] * y + m[1][2] * z + m[1][3]) * w,
            (m[2][0] * x + m[2][1] * y + m[2][2] * z + m[2][3]) * w]


def row(semantic_id, field, actual, expected, threshold):
    difference = abs(actual - expected)
    passed = math.isfinite(actual) and math.isfinite(expected) and difference <= threshold
    return {"semantic_id": semantic_id, "field": field, "actual": actual, "expected": expected,
            "difference": difference, "threshold": threshold, "passed": passed}


def same_number(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    return float(a) == float(b)


def audit_case(root, case):
    stage = os.path.join(root, case)
    probe = json.load(open(os.path.join(stage, "probe.json")))
    reference = json.load(open(os.path.join(stage, "synthetic-audit.json")))
    gltf, binary, chunk_count = read_glb(os.path.join(stage, "synthetic.glb"))
    retained = probe["three"]["nodes"]
    ref_nodes = reference["nodes"]
    result = {"case": case, "glb": {"chunks": chunk_count, "nodes": len(gltf["nodes"]), "meshes": len(gltf["meshes"]),
                                    "scenes": len(gltf.get("scenes", [])), "animations": len(gltf.get("animations", [])),
                                    "cameras": len(gltf.get("cameras", [])), "images": len(gltf.get("images", [])),
                                    "textures": len(gltf.get("textures", [])),
                                    "buffers": [{k: v for k, v in b.items()} for b in gltf.get("buffers", [])],
                                    "uri_anywhere": '"uri"' in json.dumps(gltf), "extensionsUsed": gltf.get("extensionsUsed")}}

    # 1. The GLB's own values against the importer's retained values.
    by_id, parent_of = {}, {}
    for index, node in enumerate(gltf["nodes"]):
        sem = node.get("extras", {}).get("semantic_id")
        by_id["/".join(sem) if isinstance(sem, list) else node.get("name")] = index
        for child in node.get("children", []):
            parent_of[child] = index
    world = {}

    def world_of(index):
        if index in world:
            return world[index]
        node = gltf["nodes"][index]
        if "matrix" in node:
            local = [float(v) for v in node["matrix"]]
        else:
            local = compose(node.get("translation", [0.0, 0.0, 0.0]), node.get("rotation", [0.0, 0.0, 0.0, 1.0]),
                            node.get("scale", [1.0, 1.0, 1.0]))
        parent = parent_of.get(index)
        world[index] = multiply(world_of(parent), local) if parent is not None else multiply(mat_identity(), local)
        return world[index]

    glb_checks = {"identity_set_equal": sorted(by_id) == sorted(retained), "positions_exact": True, "normals_exact": True,
                  "indices_exact": True, "max_world_matrix_deviation": 0.0, "layouts": set(), "mesh_nodes": 0}
    for sid, index in by_id.items():
        node = gltf["nodes"][index]
        deviation = max(abs(a - b) for ra, rb in zip(rows_of(world_of(index)), retained[sid]["world_matrix"])
                        for a, b in zip(ra, rb))
        glb_checks["max_world_matrix_deviation"] = max(glb_checks["max_world_matrix_deviation"], deviation)
        if "mesh" not in node:
            continue
        glb_checks["mesh_nodes"] += 1
        primitive = gltf["meshes"][node["mesh"]]["primitives"][0]
        pa, positions = accessor_values(gltf, binary, primitive["attributes"]["POSITION"])
        na, normals = accessor_values(gltf, binary, primitive["attributes"]["NORMAL"])
        ia, indices = accessor_values(gltf, binary, primitive["indices"])
        glb_checks["layouts"].add((pa["type"], pa["componentType"], pa["count"], na["type"], na["componentType"],
                                   ia["type"], ia["componentType"], ia["count"], primitive.get("mode", 4),
                                   tuple(sorted(primitive["attributes"]))))
        if positions != retained[sid]["positions"]:
            glb_checks["positions_exact"] = False
        if normals != retained[sid]["normals"]:
            glb_checks["normals_exact"] = False
        if indices != retained[sid]["indices"]:
            glb_checks["indices_exact"] = False
    glb_checks["layouts"] = sorted(list(x) for x in glb_checks["layouts"])
    result["glb_vs_importer"] = glb_checks

    # 2-4. The expected row inventory and every row, from the reference and the retained importer values.
    rows, geometry = [], {"vertices_equal_retained": True, "bounds_equal_retained": True}
    for sid in sorted(ref_nodes):
        ref = ref_nodes[sid]
        imported = retained[sid]
        matrix = imported["world_matrix"]
        for i in range(4):
            for j in range(4):
                rows.append(row(sid, "matrix_%d_%d" % (i, j), matrix[i][j], ref["world_matrix"][i][j],
                                POSITION_THRESHOLD if (j == 3 and i < 3) else MATRIX_THRESHOLD))
        if not ref.get("world_vertices"):
            continue
        vertices = [apply_matrix4(matrix, p) for p in imported["positions"]]
        if vertices != imported["world_vertices"]:
            geometry["vertices_equal_retained"] = False
        for i, (vertex, normal) in enumerate(zip(vertices, imported["normals"])):
            for axis in range(3):
                rows.append(row(sid, "world_vertex_%d_%d" % (i, axis), vertex[axis], ref["world_vertices"][i][axis],
                                POSITION_THRESHOLD))
                rows.append(row(sid, "normal_%d_%d" % (i, axis), normal[axis], ref["normals"][i][axis], MATRIX_THRESHOLD))
        low = [min(v[a] for v in vertices) for a in range(3)]
        high = [max(v[a] for v in vertices) for a in range(3)]
        ref_low = [min(v[a] for v in ref["world_vertices"]) for a in range(3)]
        ref_high = [max(v[a] for v in ref["world_vertices"]) for a in range(3)]
        if [low, high] != imported["world_bounds"]:
            geometry["bounds_equal_retained"] = False
        for axis in range(3):
            rows.append(row(sid, "world_min_%d" % axis, low[axis], ref_low[axis], POSITION_THRESHOLD))
            rows.append(row(sid, "world_max_%d" % axis, high[axis], ref_high[axis], POSITION_THRESHOLD))
            rows.append(row(sid, "world_size_%d" % axis, high[axis] - low[axis], ref_high[axis] - ref_low[axis],
                            POSITION_THRESHOLD))
    result["geometry"] = geometry

    # 5. Against the report's measurements.
    reported = probe["three"]["measurements"]
    keys = [(r["semantic_id"], r["field"]) for r in rows]
    reported_keys = [(r["semantic_id"], r["field"]) for r in reported]
    mismatched = []
    for mine, theirs in zip(rows, reported):
        if (mine["semantic_id"], mine["field"]) != (theirs["semantic_id"], theirs["field"]) or \
                set(theirs) != set(mine) or \
                not all(same_number(mine[k], theirs[k]) for k in ("actual", "expected", "difference", "threshold")) or \
                mine["passed"] is not theirs["passed"]:
            mismatched.append({"mine": mine, "report": theirs})
    failed = [r for r in rows if not r["passed"]]
    by_kind = {}
    for r in rows:
        field = r["field"]
        if field.startswith("matrix_"):
            kind = "matrix"
        elif field.startswith("world_vertex_"):
            kind = "world_vertex"
        elif field.startswith("normal_"):
            kind = "normal"
        else:
            kind = field[:-2]
        by_kind[kind] = by_kind.get(kind, 0) + 1
    result["_rows"] = rows
    expected_findings = [{k: r[k] for k in ("semantic_id", "field", "actual", "expected", "difference", "threshold")}
                         for r in failed]
    result["rows"] = {
        "expected_inventory": len(rows), "unique": len(set(keys)) == len(keys), "reported": len(reported),
        "reported_unique": len(set(reported_keys)) == len(reported_keys),
        "same_inventory_same_order": keys == reported_keys,
        "missing": sorted(set(keys) - set(reported_keys))[:20], "extra": sorted(set(reported_keys) - set(keys))[:20],
        "value_mismatches": len(mismatched), "mismatch_examples": mismatched[:5],
        "by_kind": by_kind, "nodes": len(ref_nodes),
        "mesh_nodes": sum(1 for n in ref_nodes.values() if n.get("world_vertices")),
        "failed_rows": failed,
        "max_passing_ratio": max((r["difference"] / r["threshold"]) for r in rows if r["passed"]),
        "findings_report": probe["three"]["findings"],
        "findings_equal_failed_rows": sorted(json.dumps(f, sort_keys=True) for f in probe["three"]["findings"])
                                      == sorted(json.dumps(f, sort_keys=True) for f in expected_findings),
        "report_passed": probe["passed"], "report_three_passed": probe["three"]["passed"], "error_member": "error" in probe,
    }

    # 6. The reference's own consistency.
    max_ref = 0.0
    for sid, ref in ref_nodes.items():
        if not ref.get("world_vertices"):
            continue
        for p, wv in zip(ref["positions"], ref["world_vertices"]):
            computed = apply_matrix4(ref["world_matrix"], p)
            max_ref = max(max_ref, max(abs(a - b) for a, b in zip(computed, wv)))
    result["reference_self_consistency_max_deviation"] = max_ref
    result["reference"] = {"passed": reference.get("passed"), "case": reference.get("case"),
                           "artifact_sha256_binds_glb": reference.get("artifact_sha256")
                           == hashlib.sha256(open(os.path.join(stage, "synthetic.glb"), "rb").read()).hexdigest(),
                           "findings": reference.get("findings"), "schema": reference.get("schema")}
    return result, reference


def diff_documents(a, b, where=""):
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for key in sorted(set(a) | set(b)):
            if key not in a or key not in b:
                out.append((where + "/" + key, "missing on one side"))
            else:
                out.extend(diff_documents(a[key], b[key], where + "/" + key))
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append((where, "length"))
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                out.extend(diff_documents(x, y, where + "/" + str(i)))
    elif a != b or type(a) is not type(b):
        out.append((where, [a, b]))
    return out


def main():
    root, c18_path, output = sys.argv[1], sys.argv[2], sys.argv[3]
    results, references = {}, {}
    for case in CASES:
        results[case], references[case] = audit_case(root, case)
    # The changed reference against Q01's, member by member; the GLBs byte for byte.
    differences = diff_documents(references["Q01-positive"], references["Q01-changed-reference"])
    glb_equal = open(os.path.join(root, "Q01-positive", "synthetic.glb"), "rb").read() == \
        open(os.path.join(root, "Q01-changed-reference", "synthetic.glb"), "rb").read()
    negative = results["Q01-changed-reference"]["rows"]["failed_rows"]
    negative_ok = (len(negative) == 1 and negative[0]["semantic_id"] == "equipment-tray/pair/left/base"
                   and negative[0]["field"] == "matrix_0_3" and negative[0]["threshold"] == 0.000005
                   and abs(negative[0]["difference"] - 0.001) <= 1e-9
                   and len(results["Q01-changed-reference"]["rows"]["findings_report"]) == 1)
    summary = {}
    for case, value in results.items():
        r = value["rows"]
        summary[case] = {"rows": r["expected_inventory"], "unique": r["unique"], "same_as_report": r["same_inventory_same_order"],
                         "value_mismatches": r["value_mismatches"], "failed_rows": len(r["failed_rows"]),
                         "findings": len(r["findings_report"]), "findings_equal_failed_rows": r["findings_equal_failed_rows"],
                         "report_passed": r["report_passed"], "error_member": r["error_member"],
                         "glb_positions_normals_indices_exact": value["glb_vs_importer"]["positions_exact"]
                         and value["glb_vs_importer"]["normals_exact"] and value["glb_vs_importer"]["indices_exact"],
                         "glb_world_matrix_max_deviation": value["glb_vs_importer"]["max_world_matrix_deviation"],
                         "world_vertices_recomputed_equal_retained": value["geometry"]["vertices_equal_retained"],
                         "bounds_recomputed_equal_retained": value["geometry"]["bounds_equal_retained"],
                         "max_difference_over_threshold_passing": r["max_passing_ratio"]}
    positives_ok = all(summary[c]["failed_rows"] == 0 and summary[c]["findings"] == 0 and summary[c]["report_passed"] is True
                       for c in ("Q01-positive", "Q03-positive"))
    # Comparison with C18's record, row by row (its rows are read, not trusted: they are compared with mine).
    c18 = json.load(open(c18_path))
    comparison = {}
    all_rows = {}
    for case in CASES:
        theirs = c18["cases"][case]
        mine = results[case].pop("_rows")
        all_rows[case] = mine
        key = ("semantic_id", "field", "actual", "expected", "difference", "threshold", "passed")
        their_rows = [tuple(r[k] for k in key) for r in theirs["rows"]]
        my_rows = [tuple(r[k] for k in key) for r in mine]
        comparison[case] = {"c18_passed": theirs["passed"], "c18_counts": theirs["counts"],
                            "c18_failed_rows": [(r["semantic_id"], r["field"]) for r in theirs["failed_rows"]],
                            "c18_rows_equal_mine": their_rows == my_rows,
                            "c18_rows": len(their_rows), "my_rows": len(my_rows),
                            "c18_report_column_values": sorted({r.get("report") for r in theirs["rows"]})}
    report = {"schema": "w4-audit-001.a05-numeric/1", "cohort_root": root, "summary": summary,
              "positives_all_rows_pass": positives_ok, "negative_exactly_one_intended_row_and_finding": negative_ok,
              "negative_row": negative, "negative_difference_minus_0_001": negative[0]["difference"] - 0.001 if negative else None,
              "changed_reference_differences_from_q01": differences, "changed_reference_glb_byte_identical": glb_equal,
              "cases": results, "c18": {"passed": c18["passed"], "cases": comparison, "tool_sha256": c18["tool"]["sha256"]}}
    rows_output = output[:-len(".json")] + "-rows.json"
    rows_data = json.dumps({"schema": "w4-audit-001.a05-numeric-rows/1", "rows": all_rows}, sort_keys=True).encode()
    fd = os.open(rows_output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        os.write(fd, rows_data)
        os.fsync(fd)
    finally:
        os.close(fd)
    data = json.dumps(report, indent=1, sort_keys=True, default=str).encode()
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    print(json.dumps(summary, indent=1))
    print("positives all rows pass", positives_ok)
    print("negative exactly one intended row and finding", negative_ok, json.dumps(negative))
    print("changed reference differences from Q01", differences)
    print("changed reference GLB byte identical", glb_equal)
    for case in CASES:
        print("glb", case, json.dumps(results[case]["glb"]), json.dumps(results[case]["glb_vs_importer"]))
        print("by kind", case, results[case]["rows"]["by_kind"], "nodes", results[case]["rows"]["nodes"],
              "meshes", results[case]["rows"]["mesh_nodes"], "reference self-consistency", results[case]["reference_self_consistency_max_deviation"],
              json.dumps(results[case]["reference"]))
        print("c18", case, json.dumps(comparison[case]))


main()
