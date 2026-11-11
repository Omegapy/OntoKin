"""Independent document/schema probes; no source frontend or native execution."""
from pathlib import Path
from fractions import Fraction
import copy
import hashlib
import itertools
import json
import platform
import struct
import subprocess
import sys
import jsonschema

ROOT = Path(sys.argv[1]).resolve()
DOC = ROOT / "docs/engineering/static-tray-mapping-c198"
OUT = Path(sys.argv[2]).resolve()
OUT.mkdir(parents=True, exist_ok=True)
checks = []
head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
tree = subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=ROOT, text=True).strip()


def check(name, condition, detail=None):
    checks.append({"name": name, "pass": bool(condition), "detail": detail})
    if not condition:
        raise AssertionError(name)


def load(name):
    def unique(items):
        result = {}
        for k, v in items:
            if k in result:
                raise ValueError("Duplicate key: " + k)
            result[k] = v
        return result
    return json.loads((DOC / name).read_text(), object_pairs_hook=unique)


def hx(x):
    return struct.pack(">d", 0.0 if x == 0 else float(x)).hex()


def vec(v):
    return [hx(x) for x in v]


def rn(op, *xs):
    fs = list(map(Fraction.from_float, map(float, xs)))
    return float(op(*fs))


add = lambda a, b: rn(lambda x, y: x + y, a, b)
mul = lambda a, b: rn(lambda x, y: x * y, a, b)
half = lambda a: rn(lambda x: x / 2, a)


def record_for(fixture):
    record = {
        "schema_version": "ontokin.static-tray.record/0.1.0",
        "profile": "ontokin.static-tray/0.1.0",
        "contract": "OK-MAP-STATIC-TRAY-001/0.1.0",
        "template_id": "static-tray-six-box/0.1.0",
        "length_unit": "m", "frame": "ontokin-world-rh-y-up",
        "numeric_encoding": "binary64-be-hex/1",
        "material_set": "static-tray-materials/0.1.0", "trays": [],
    }
    for side in ("left", "right"):
        q = fixture[side]
        px, py, pz = q["payload_m"]
        c, t, b, h = [q[k] for k in ("clearance_m", "wall_m", "base_m", "headroom_m")]
        W, D, H = add(px, mul(2, c)), add(pz, mul(2, c)), add(py, h)
        OX, OZ = add(W, mul(2, t)), add(D, mul(2, t))
        geometry = {
            "base": ((OX, b, OZ), (0, -half(b), 0)),
            "front": ((OX, H, t), (0, half(H), half(add(D, t)))),
            "back": ((OX, H, t), (0, half(H), -half(add(D, t)))),
            "left-wall": ((t, H, D), (-half(add(W, t)), half(H), 0)),
            "right-wall": ((t, H, D), (half(add(W, t)), half(H), 0)),
            "payload": ((px, py, pz), (0, half(py), 0)),
        }
        identity = ["equipment-tray", "pair", side]
        common = {"physical": "no_body", "motion": "prescribed", "collision": "disabled"}
        tray = {"id": identity, "owner_id": ["equipment-tray", "pair"],
                "role": "tray-root", "geometry": "empty", **common,
                "root_pose": {"reference": "world", "translation_m": vec(q["translation_m"]),
                              "rotation_wxyz": vec(q["rotation_wxyz"])},
                "parameters": {"payload_size_m": vec((px, py, pz)),
                               "horizontal_clearance_m": hx(c), "wall_thickness_m": hx(t),
                               "base_thickness_m": hx(b), "headroom_m": hx(h)}, "parts": []}
        for key in sorted(geometry):
            size, position = geometry[key]
            tray["parts"].append({"id": identity + [key], "owner_id": identity, "key": key,
                "role": "payload-proxy" if key == "payload" else key,
                "geometry": {"type": "box", "size_m": vec(size)}, **common,
                "material": "payload" if key == "payload" else "tray",
                "following": {"id": identity + ["follow-" + key], "parent_id": identity,
                              "offset": {"reference": "parent-frame", "translation_m": vec(position),
                                         "rotation_wxyz": vec((1, 0, 0, 0))}}})
        record["trays"].append(tray)
    return record


schema = load("canonical-record.schema.json")
controls = load("CONTROLS.json")
jsonschema.Draft202012Validator.check_schema(schema)
check("schema_meta_validation", True)
validator = jsonschema.Draft202012Validator(schema)
records = {key: record_for(value) for key, value in controls["fixture_sets"].items()}
for key, value in records.items():
    errors = [e.message for e in validator.iter_errors(value)]
    check("synthetic_schema_" + key, not errors, errors)
    size = len(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())
    check("record_cap_" + key, size <= 32768, size)

base = records["Q01"]
catalog = schema["$defs"]["rootPose"]["properties"]["rotation_wxyz"]["enum"]
check("twelve_unique_catalog_tuples", len(catalog) == len(set(map(tuple, catalog))) == 12)
for index, bits in enumerate(catalog):
    q = [Fraction.from_float(struct.unpack(">d", bytes.fromhex(x))[0]) for x in bits]
    w, x, y, z = q
    matrix = [[1-2*(y*y+z*z), 2*(x*y-w*z), 2*(x*z+w*y)],
              [2*(x*y+w*z), 1-2*(x*x+z*z), 2*(y*z-w*x)],
              [2*(x*z-w*y), 2*(y*z+w*x), 1-2*(x*x+y*y)]]
    det = sum((1 if p in [(0,1,2),(1,2,0),(2,0,1)] else -1) *
              matrix[0][p[0]] * matrix[1][p[1]] * matrix[2][p[2]]
              for p in itertools.permutations(range(3)))
    check("rotation_exact_proper_" + str(index), sum(v*v for v in q) == 1 and det == 1 and
          all(v in (-1,0,1) for row in matrix for v in row) and
          all(sum(v != 0 for v in row) == 1 for row in matrix) and
          all(sum(matrix[r][c] != 0 for r in range(3)) == 1 for c in range(3)))
    for side in range(2):
        probe = copy.deepcopy(base)
        probe["trays"][side]["root_pose"]["rotation_wxyz"] = bits
        check("catalog_schema_%s_%s" % (index, side), validator.is_valid(probe))

def reject(name, mutate):
    probe = copy.deepcopy(base)
    mutate(probe)
    check("schema_reject_" + name, not validator.is_valid(probe))

reject("unknown_root_key", lambda p: p.update(route="ontokin"))
reject("swapped_trays", lambda p: p["trays"].reverse())
reject("missing_tray", lambda p: p["trays"].pop())
reject("swapped_parts", lambda p: p["trays"][0]["parts"].reverse())
reject("wrong_owner", lambda p: p["trays"][0]["parts"][0].update(owner_id=["equipment-tray","pair","right"]))
reject("wrong_follow_parent", lambda p: p["trays"][0]["parts"][0]["following"].update(parent_id=["equipment-tray","pair","right"]))
reject("missing_follow", lambda p: p["trays"][0]["parts"][0].pop("following"))
reject("wrong_payload_role", lambda p: p["trays"][0]["parts"][4].update(role="base"))
reject("extra_body", lambda p: p["trays"][0]["parts"][0].update(physical="dynamic"))
for name, value in [("negative_zero","8000000000000000"),("nan","7ff8000000000000"),
                    ("positive_infinity","7ff0000000000000"),("negative_infinity","fff0000000000000"),
                    ("uppercase","3FE0000000000000"),("json_number",0.5),("boolean",True),
                    ("hex_prefix","0x3fe0000000000000")]:
    reject(name, lambda p,v=value: p["trays"][0]["parameters"].update(horizontal_clearance_m=v))

probe = copy.deepcopy(base)
probe["trays"][0]["parts"][0]["geometry"]["size_m"][0] = hx(0.5)
check("schema_deliberately_requires_semantic_geometry_check", validator.is_valid(probe))

slots = controls["future_qualification_native_slots"]
check("twelve_single_use_native_slots", len(slots) == len({s["slot"] for s in slots}) == 12 and
      all(s["maximum_starts"] == 1 for s in slots))
check("qualifications_cover_both_routes", all({s["route"] for s in slots if s["case"] == case} ==
      {"ontokin", "direct-python"} for case in records))
check("later_admission_four_no_retry", controls["later_admission_limits"]["native_starts_including_failure"] == 4 and
      controls["later_admission_limits"]["automatic_retries"] == 0)

for name in ("BASELINE-INPUTS.json", "DEPENDENCIES.json"):
    manifest = load(name)
    revision = manifest.get("baseline_commit", manifest.get("source_commit"))
    for row in manifest["files"]:
        raw = subprocess.check_output(["git", "show", revision + ":" + row["path"]], cwd=ROOT)
        check(name + ":" + row["path"], len(raw) == row["bytes"] and
              hashlib.sha256(raw).hexdigest() == row["sha256"])

freeze = load("INPUT-FREEZE.json")
for row in freeze["files"]:
    raw = (DOC / row["path"]).read_bytes()
    check("freeze:" + row["path"], len(raw) == row["bytes"] and
          hashlib.sha256(raw).hexdigest() == row["sha256"])
check("freeze_nine_normative_inputs", len(freeze["files"]) == 9)
check("freeze_39_controls", len(controls["controls"]) == freeze["control_count"] == 39)
digest_bytes = json.dumps(freeze["files"], sort_keys=True, separators=(",", ":")).encode()
check("freeze_file_list_canonical_digest", hashlib.sha256(digest_bytes).hexdigest() == freeze["files_digest_sha256"])

def inventory(revision):
    raw = subprocess.check_output(["git", "ls-tree", "-rz", revision], cwd=ROOT)
    return {row.split(b"\t", 1)[1].decode(): row.split(b"\t", 1)[0].decode()
            for row in raw.split(b"\0") if row}

baseline = inventory(freeze["baseline_commit"])
candidate = inventory(head)
changed = [p for p in baseline if candidate.get(p) != baseline[p]]
added = [p for p in candidate if p not in baseline]
check("historical_scope_preserved", set(changed) <= {"README.md", "STATUS.md", "docs/README.md"}, changed)
check("new_files_scoped", all(p.startswith("docs/engineering/static-tray-mapping-c198/") for p in added), added)
retained = json.loads((Path(__file__).resolve().parent / "INHERITED-REFS.json").read_text())
for ref, expected in retained.items():
    actual = subprocess.check_output(["git", "rev-parse", ref], cwd=ROOT, text=True).strip()
    check("inherited_ref:" + ref, actual == expected)
check("all_54_inherited_refs", len(retained) == 54)
check("source_unchanged_during_review", subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == head)

files = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in DOC.iterdir() if p.is_file()}
result = {"schema": "ontokin.c198.independent-contract-probes/0.1", "pass": True,
          "executed_check_count": len(checks), "checks": checks, "reviewed_files": files,
          "candidate_commit": head, "candidate_tree": tree,
          "input_freeze_sha256": hashlib.sha256((DOC / "INPUT-FREEZE.json").read_bytes()).hexdigest(),
          "baseline_file_count": len(baseline), "historical_files_unchanged": len(baseline) - len(changed),
          "permitted_modified_existing": changed, "new_scoped_file_count": len(added),
          "interpreter": sys.version, "platform": platform.platform(),
          "jsonschema_version": __import__("importlib.metadata", fromlist=["version"]).version("jsonschema"),
          "source_frontend_executions": 0, "native_executions": 0,
          "scope": "Document/source-binding and synthetic JSON-schema review; not adapter semantic validation or native qualification"}
(OUT / "PROBES.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"pass": True, "checks": len(checks), "result": str(OUT / "PROBES.json")}, indent=2))
