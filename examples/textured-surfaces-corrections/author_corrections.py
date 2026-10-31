#!/usr/bin/env python3
"""Author explicit input errata with stdlib only; never execute the product.

The original published corpus is read-only. A second version names 100 exact
original cases and two separately hashed corrections. Initial actual failures
are copied without editing and remain part of the correction's provenance.
"""
from __future__ import annotations

import copy
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[2]
ORIGINAL = ROOT / "examples/textured-surfaces"
OUTPUT = Path(__file__).resolve().parent
EVIDENCE = ROOT.parent / "c080-results/acceptance-001"
FREEZE = "4e5da7152e775b065299f2000ca80d51301bcd21"
FREEZE_HASH = "27705dc723d388fc92fe5fda58f97de75e492618ce1330dbfe51ae4ddeb08015"
CORRECTED = ("inherited-loft", "older-user-function-png-asset")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(raw):
    return "sha256:" + sha(raw)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def write(name, raw):
    path = OUTPUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    path.chmod(0o644)


def save(name, value):
    write(name, (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode())


def identity(file_manifest):
    units = []
    for index, unit in enumerate([file_manifest["entry"], *file_manifest["modules"]]):
        units.append({"source_id": "entry" if index == 0 else "package:" + unit["package_id"] + "@" + unit["version"],
            "package_id": None if index == 0 else unit["package_id"],
            "version": None if index == 0 else unit["version"], "filename": unit["filename"],
            "source_revision": digest((OUTPUT / unit["path"]).read_bytes())})
    schema = "ontokin.bundle/0.2" if file_manifest["schema_version"].endswith("/0.2") else "ontokin.bundle/0.1"
    manifest = {"schema_version": schema, "entry_source_id": "entry", "units": sorted(units, key=lambda x: x["source_id"])}
    if schema.endswith("/0.2"):
        manifest["assets"] = sorted([{k: a[k] for k in ("asset_id", "sha256", "media_type")} |
            {"byte_length": len((OUTPUT / a["path"]).read_bytes())} for a in file_manifest["assets"]], key=lambda x: x["asset_id"])
    return digest(schema.encode() + b"\0" + canonical(manifest)), manifest


def uv_probe(point, mapping):
    delta = [Fraction(float(p)) - Fraction(float(o)) for p, o in zip(point, mapping["origin_m"])]
    exact = [sum((Fraction(float(a)) * b for a, b in zip(row, delta)), Fraction(float(offset)))
             for row, offset in zip((mapping["u_per_m"], mapping["v_per_m"]), mapping["offset"])]
    binary64 = [float(x) for x in exact]
    binary32 = [struct.unpack("<f", struct.pack("<f", x))[0] for x in binary64]
    return {"position_m": list(point), "uv_exact": [{"numerator": str(x.numerator), "denominator": str(x.denominator)} for x in exact],
        "uv_binary64": binary64, "uv_binary64_hex": [x.hex() for x in binary64],
        "uv_binary32": binary32, "uv_binary32_le_hex": [struct.pack("<f", x).hex() for x in binary32]}


def main():
    assert sha((ORIGINAL / "acceptance-freeze.json").read_bytes()) == FREEZE_HASH
    original = json.loads((ORIGINAL / "expected.json").read_bytes())
    first = json.loads((EVIDENCE / "summary.json").read_bytes())
    assert first["git"]["commit"] == "c83cfcffc86af4cdcaa67ab7be9d49592cfd0de7" and first["git"]["status"] == ""
    write("first-failure/summary.json", (EVIDENCE / "summary.json").read_bytes())
    old_module = (ORIGINAL / "modules/legacy-name.ok").read_bytes()
    assert old_module.count(b"digest: String") == 1
    new_module = old_module.replace(b"digest: String", b"digest_text: String")
    write("modules/legacy-name.ok", new_module)
    new_pin, old_pin = digest(new_module), digest(old_module)
    active = {"schema_version": "ontokin.c080-active-corpus/0.2", "corpus_version": 2,
        "original_input_commit": FREEZE, "original_manifest_sha256": FREEZE_HASH,
        "unchanged_original_cases": 100, "corrected_cases": 2, "case_count": 102,
        "original_input_policy": "The original freeze and its failed expectations remain immutable; these are explicit new inputs, not retroactive passes.",
        "first_failed_execution": {"git": first["git"], "summary": "first-failure/summary.json",
                                   "summary_sha256": sha((EVIDENCE / "summary.json").read_bytes())},
        "cases": []}
    for original_case in original["cases"]:
        name = original_case["name"]
        record = {"id": original_case["id"], "name": name, "original_program_revision": original_case["program_revision"]}
        if name not in CORRECTED:
            active["cases"].append({**record, "origin": "original_published_freeze"})
            continue
        case = copy.deepcopy(original_case)
        manifest = json.loads((ORIGINAL / case["file_manifest"]).read_bytes())
        control_name = case["untextured_control"]["file_manifest"]
        control = json.loads((ORIGINAL / control_name).read_bytes())
        for spec in (manifest, control):
            raw = (ORIGINAL / spec["entry"]["path"]).read_bytes()
            if name == "inherited-loft":
                assert raw.count(b'}, 4, "flat")') == 1
                corrected = raw.replace(b'}, 4, "flat")', b'}, 8, "flat")')
            else:
                assert raw.count(old_pin.encode()) == 1
                corrected = raw.replace(old_pin.encode(), new_pin.encode())
            write(spec["entry"]["path"], corrected)
            for asset in spec.get("assets", []):
                write(asset["path"], (ORIGINAL / asset["path"]).read_bytes())
        save(case["file_manifest"], manifest)
        save(control_name, control)
        revision, canonical_manifest = identity(manifest)
        control_revision, _ = identity(control)
        case["program_revision"], case["canonical_manifest"] = revision, canonical_manifest
        case["untextured_control"]["source_revision"] = digest((OUTPUT / control["entry"]["path"]).read_bytes())
        case["untextured_control"]["program_revision"] = control_revision
        case["input_corpus_version"] = 2
        case["erratum"] = {"id": "INPUT-ERRATA-001", "original_case_id": original_case["id"],
                           "original_program_revision": original_case["program_revision"],
                           "original_expected_outcome": "valid", "original_actual_outcome": "refused"}
        if name == "inherited-loft":
            reason = "Original facets=4 violates unchanged inherited minimum8/divisible4; replace only that literal by8 in textured source and underlying .12 control."
            case["loft_facets"] = 8
            corners = [(0., 0., z) for z in (0., 1.)]
            corners += [(math.cos(2 * math.pi * i / 8), math.sin(2 * math.pi * i / 8), z) for z in (0., 1.) for i in range(8)]
            case["analytic_geometry"] = {"facets": 8, "radius_m": 1, "height_m": 1,
                "triangles": 32, "logical_vertices": 18, "volume_m3": 2 * math.sqrt(2),
                "surface_area_m2": 4 * math.sqrt(2) + 16 * math.sin(math.pi / 8),
                "formulas": {"volume": "n*sin(2*pi/n)/2", "area": "n*sin(2*pi/n)+2*n*sin(pi/n)", "n": 8}}
            binding = case["texture_bindings"][0]
            binding["probe_role"] = "independent_eight_facet_loft_ring_and_cap_center_candidates"
            binding["uv_probes"] = [uv_probe(p, binding["mapping"]) for p in corners]
            code = "OKL-E-SURFACE-FACETS"
        else:
            reason = "The original .12 user-function parameter `digest` is a reserved keyword; rename that parameter only to `digest_text` and update exact imported source hashes in entry/control."
            code = "OKL-E-SYNTAX"
        case["notes"] = case["notes"] + " Input corpus version2: " + reason
        failure = (EVIDENCE / "sources" / (name + ".receipt.json")).read_bytes()
        assert code in [d["code"] for d in json.loads(failure)["diagnostics"]]
        write("first-failure/" + name + ".receipt.json", failure)
        expected_path = "cases/" + name + ".expected.json"
        save(expected_path, case)
        active["cases"].append({**record, "origin": "input_erratum_001", "expected_file": expected_path,
            "corrected_program_revision": revision, "reason": reason,
            "first_failure": {"receipt": "first-failure/" + name + ".receipt.json", "sha256": sha(failure), "code": code}})
    save("active-corpus.json", active)
    files = [{"path": p.relative_to(OUTPUT).as_posix(), "size": p.stat().st_size,
              "mode": "100644", "sha256": sha(p.read_bytes())}
             for p in sorted(OUTPUT.rglob("*")) if p.is_file() and p.name != "correction-freeze.json"]
    erratum = ROOT / "docs/language-design/textured-surfaces-v0.1/INPUT-ERRATA-001.md"
    save("correction-freeze.json", {"schema_version": "ontokin.c080-input-corrections-freeze/0.1",
        "original_input_commit": FREEZE, "original_manifest_sha256": FREEZE_HASH,
        "corpus_version": 2, "case_count": 102, "unchanged_original_cases": 100, "corrected_cases": 2,
        "active_corpus_sha256": sha((OUTPUT / "active-corpus.json").read_bytes()),
        "erratum_document": {"path": erratum.relative_to(ROOT).as_posix(), "sha256": sha(erratum.read_bytes())},
        "files": files, "file_count": len(files), "bytes": sum(x["size"] for x in files),
        "authorship": "Standard-library-only corrections; no product imports, runtime execution or test execution during correction authoring.",
        "first_failure_policy": "Initial observed refusals remain retained verbatim. Original expected-valid inputs do not become passes retroactively.",
        "corrected_runtime_execution_at_authoring": False,
        "self_manifest_rule": "This file excludes itself; root must publish its exact bytes/commit before any corrected runtime execution."})


if __name__ == "__main__":
    main()
