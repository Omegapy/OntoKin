#!/usr/bin/env python3
"""Read-only independent input-byte/formula audit; imports no OntoKin code."""
from pathlib import Path
import hashlib
import itertools
import json
import re
import sys

root = Path(sys.argv[1]).resolve()
output = Path(sys.argv[2])
checks = []
failures = []


def check(name, ok, detail=None):
    checks.append(name)
    if not ok:
        failures.append({"check": name, "detail": detail})


def read(name):
    return json.loads((root / name).read_text())


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(raw):
    return json.dumps(raw, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode()


# Byte identity and every files-manifest reference, including all controls.
file_manifests = sorted(root.rglob("*.files.json"))
for mf in file_manifests:
    data = json.loads(mf.read_text())
    check(str(mf.relative_to(root)) + ":schema", data["schema_version"] == "ontokin.files/0.2")
    for row in [data["entry"], *data.get("modules", []), *data.get("assets", [])]:
        p = (mf.parent / row["path"]).resolve()
        check(str(mf.relative_to(root)) + ":reference:" + row["path"], p.is_relative_to(root) and p.is_file())
        if "sha256" in row and p.is_file():
            check(str(mf.relative_to(root)) + ":asset-hash", row["sha256"] == "sha256:" + sha(p.read_bytes()))

source_cases = read("source-expected.json")["cases"]
for case in source_cases:
    p = root / case["source"]
    check("source-hash:" + case["id"], sha(p.read_bytes()) == case["source_sha256"])
    mf = read(case["files"])
    check("source-manifest:" + case["id"], (root / mf["entry"]["path"]).read_bytes() == p.read_bytes())
    span = case.get("expected", {}).get("diagnostic_span")
    if span:
        actual_span_bytes = p.read_bytes()[span["start_byte"]:span["end_byte"]]
        expected_span_identity = (actual_span_bytes == span["text"].encode()
                                  if "text" in span else sha(actual_span_bytes) == span["sha256"])
        check("source-diagnostic-byte-span:" + case["id"],
              expected_span_identity)

# Derive exact resource prefixes from elementary finite ordered membership.
resource = read("resource-expected.json")
for case in resource["cases"]:
    keys, query = case["keys"], case["query"]
    n = len(keys)
    k = keys.index(query) + 1 if query in keys else n
    ops = n + k + 3
    check("resource-result:" + case["id"], case["expected"] is (query in keys))
    check("resource-counts:" + case["id"], (case["n"], case["k"], case["operations"]) == (n, k, ops))
    phase_names = (["keyed_membership_admission"] + ["keyed_membership_input"] * n +
                   ["keyed_membership_query"] + ["keyed_membership_scan"] * k +
                   ["keyed_membership_publication"])
    check("resource-phases:" + case["id"], [x["phase"] for x in case["stages"]] == phase_names)
    check("resource-unit-costs:" + case["id"], all(x["amount"] == 1 for x in case["stages"]))
    check("resource-all-caps:" + case["id"], [x["available"] for x in case["operation_caps"]] == list(range(ops + 1)))
    for cap in case["operation_caps"]:
        a = cap["available"]
        check("resource-cap:" + case["id"] + ":" + str(a),
              cap["success"] is (a == ops) and
              (a == ops or (cap["completed_stages"] == a and cap["refusal_on_stage"] == a + 1)))
        check("resource-cap-counter:" + case["id"] + ":" + str(a),
              cap["incremented_local_counter"] == min(a + 1, ops) and
              cap["work_completed_local_steps"] == a)
        if a < ops:
            check("resource-cap-stage:" + case["id"] + ":" + str(a),
                  cap["refusal_stage"] == phase_names[a] and
                  cap["diagnostic_code"] == "OKL-E-RESOURCE" and
                  cap["budget_reason"] == "operation_budget_exhausted")
    check("resource-all-interruptions:" + case["id"],
          [x["before_step"] for x in case["interruptions"]] == list(range(1, ops + 1)))
    for row in case["interruptions"]:
        i = row["before_step"]
        check("resource-interruption:" + case["id"] + ":" + str(i),
              row["stage"] == phase_names[i - 1] and
              row["cancel"]["local_operations"] == i - 1 and
              row["cancel"]["completed_work_steps"] == i - 1 and
              row["cancel"]["same_exception_object"] is True and
              row["cancel"]["no_boolean"] is True and
              row["deadline"]["local_operations"] == i and
              row["deadline"]["completed_work_steps"] == i - 1 and
              row["deadline"]["code"] == "OKL-E-RESOURCE" and
              row["deadline"]["budget_reason"] == "execution_deadline_exceeded" and
              row["deadline"]["no_boolean"] is True)

# The positive native descriptors are literal shapes, not candidate output.
simple = {"Int", "Real", "Bool", "String", "FrameRef", "Rotation", "Pose", "Color",
          "LoftSection", "SurfaceMaterial", "TextureImage", "PlanarUV", "TextureBinding",
          "PolygonPocket", "FramedPolygonSection", "PolygonSection", "PolygonRing",
          "PlanarPoint", "PolygonVertex"}


def legal_descriptor(d, scalar_only=False):
    k = d["kind"]
    if k in simple:
        return (not scalar_only or k in {"Int", "Real"}) and all(d[x] is None for x in ("dimension", "element", "name"))
    if k == "Quantity":
        v = d["dimension"]
        return (type(v) is list and len(v) == 4 and
                all(type(x) is int and -16 <= x <= 16 for x in v) and any(v) and
                d["element"] is None and d["name"] is None)
    if scalar_only:
        return False
    if k in {"Vec3", "Vector3", "Range"}:
        return d["dimension"] is None and d["name"] is None and legal_descriptor(d["element"], True)
    if k == "Point3":
        return (d["dimension"] is None and d["name"] is None and
                d["element"]["kind"] == "Quantity" and
                d["element"]["dimension"] == [1, 0, 0, 0] and legal_descriptor(d["element"], True))
    if k == "Ref":
        return (d["dimension"] is None and d["element"] is None and
                type(d["name"]) is str and 1 <= len(d["name"]) <= 278)
    return False


native = read("native-admission-expected.json")
for case in native["valid_metadata_cases"]:
    check("native-positive-descriptor:" + case["id"], legal_descriptor(case["descriptor"]))
    n = len(case["keys"])
    query = case["query"]
    k = case["keys"].index(query) + 1 if query in case["keys"] else n
    check("native-positive-result:" + case["id"], case["expected"] is (query in case["keys"]) and case["operations"] == n + k + 3)

# Rebuild bundle identities without importing source implementation.
agent = read("agent/expected.json")
agent_cases = {x["id"]: x for x in agent["cases"]}
defaults = {"left": 1, "middle": 1.5, "right": 2}
mounts = {"left": 0, "middle": 3, "right": 6}
times = agent["times_seconds"]
for case in agent_cases.values():
    mf = read("agent/" + case["files"])
    entry_bytes = (root / "agent" / mf["entry"]["path"]).read_bytes()
    check("agent-source-hash:" + case["id"], sha(entry_bytes) == case["source_sha256"])
    units = [{"source_id": "entry", "package_id": None, "version": None,
              "filename": mf["entry"]["filename"], "source_revision": "sha256:" + sha(entry_bytes)}]
    for module in sorted(mf.get("modules", []), key=lambda m: "package:" + m["package_id"] + "@" + m["version"]):
        units.append({"source_id": "package:" + module["package_id"] + "@" + module["version"],
                      "package_id": module["package_id"], "version": module["version"],
                      "filename": module["filename"],
                      "source_revision": "sha256:" + sha((root / "agent" / module["path"]).read_bytes())})
    assets = [{"asset_id": a["asset_id"], "media_type": a["media_type"], "sha256": a["sha256"],
               "byte_length": len((root / "agent" / a["path"]).read_bytes())}
              for a in sorted(mf.get("assets", []), key=lambda a: a["asset_id"])]
    manifest = {"schema_version": "ontokin.bundle/0.2", "entry_source_id": "entry", "units": units, "assets": assets}
    check("agent-canonical-manifest:" + case["id"], manifest == case["canonical_manifest"])
    revision = "sha256:" + sha(b"ontokin.bundle/0.2\0" + canonical(manifest))
    check("agent-program-revision:" + case["id"], revision == case["program_revision"])
    for group, prefix, x_offset, y_speed in [("first", "front.", -10, 0.5), ("sibling", "back.", 2, 0)]:
        overrides = case[group + "_overrides"]
        expected = {k: overrides.get(k, value) for k, value in defaults.items()}
        check("agent-selection:" + case["id"] + ":" + group, case[group + "_selected"] == expected)
        check("agent-flags:" + case["id"] + ":" + group, case[group + "_flags"] == {k: k in overrides for k in defaults})
        check("agent-keys:" + case["id"] + ":" + group, case["generated_keys"][group] == [prefix + k for k in defaults])
        if case["status"] != "passed":
            continue
        for key, width in expected.items():
            g = case["geometry"][group + '.panels["' + prefix + key + '"]']
            check("agent-corners:" + case["id"] + ":" + group + ":" + key,
                  sorted(g["corners_m"]) == sorted([list(x) for x in itertools.product((0, width), (0, 2), (0, 0.25))]))
            check("agent-motion:" + case["id"] + ":" + group + ":" + key,
                  g["translation_samples_m"] == [[x_offset + mounts[key], y_speed * t, 0] for t in times])
            check("agent-identity:" + case["id"] + ":" + group + ":" + key,
                  g["element_id"] == ["sparse-panels", "demo", group, "panels", prefix + key])
            check("agent-surface:" + case["id"] + ":" + group + ":" + key,
                  g["width_m"] == width and g["height_m"] == 2 and g["depth_m"] == 0.25 and
                  g["triangles"] == 12 and g["metallic"] == 0 and g["roughness"] == 0.7 and
                  g["top_uv_formula"] == ["0.5*x", "1-0.5*y"] and g["texture_sha256"] == agent["texture"]["sha256"])
    if case["status"] == "passed":
        marker = case["geometry"]["marker"]
        check("agent-marker:" + case["id"], marker["translation_samples_m"] == [[0.25 * t, -3, 0] for t in times])

for patch in agent["patches"]:
    before = (root / "agent/sources" / (patch["before"] + ".ok")).read_bytes()
    after = (root / "agent/sources" / (patch["after"] + ".ok")).read_bytes()
    lo, hi = patch["start_byte"], patch["end_byte"]
    check("patch-precondition:" + patch["after"], before[lo:hi] == patch["expected_text"].encode())
    check("patch-output:" + patch["after"], before[:lo] + patch["replacement"].encode() + before[hi:] == after)
    check("patch-source-revisions:" + patch["after"], patch["source_revision"] == "sha256:" + sha(before) and patch["after_source_revision"] == "sha256:" + sha(after))
    check("patch-program-revisions:" + patch["after"], patch["before_program_revision"] == agent_cases[patch["before"]]["program_revision"] and patch["after_program_revision"] == agent_cases[patch["after"]]["program_revision"])

inventory = [{"path": str(p.relative_to(root)), "bytes": p.stat().st_size, "sha256": sha(p.read_bytes())}
             for p in sorted(root.rglob("*")) if p.is_file()]
result = {"schema_version": "ontokin.c088-input-byte-formula-review/1", "root": str(root),
          "product_code_imported": False, "product_executed": False, "input_modified": False,
          "inventory_canonical_sha256": sha(canonical(inventory)), "inventory_files": len(inventory),
          "files_manifests": len(file_manifests), "source_cases": len(source_cases),
          "resource_cases": len(resource["cases"]), "agent_cases": len(agent_cases),
          "checks": len(checks), "failed": len(failures), "failures": failures,
          "limits": "Byte/formula consistency only; manual contract/coverage/hostile-reader review remains required."}
output.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
