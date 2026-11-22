"""Independent inert candidate inspection. No product or author-code imports.

Reads bound data/source bytes and reconstructs declarative byte layouts only.
Does not implement or execute the proposed ELF acceptance policy.
Writes new review artifacts exclusively in this script's own directory.
"""
from pathlib import Path, PurePosixPath
import ast
import collections
import datetime
import hashlib
import json
import stat
import struct
import sys
import tarfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CANDIDATE = ROOT / "tag-design/candidate001"
REPO = ROOT.parent / "OntoKin"
ARCHIVE = ROOT.parent / "incoming/p15/recovery/session/source-provenance/downloads-attempt001/glibc_2.41.orig.tar.xz"
EXPECTED_MANIFEST = "61b18ceb15d3ee05d3022c60941ccbbce9c3e08bac148c7750da9f6588091156"
EXPECTED_EXPECTATIONS = "33a17cc66604f8b57be88dae7dd05a4bec066c0eaa191fc08400cfc79e18137e"
checks, reads, observations = [], {}, []


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path, scope="data bytes"):
    data = path.read_bytes()
    reads[str(path)] = {"path": str(path), "size_bytes": len(data), "sha256": sha(data), "scope": scope}
    return data


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key " + key)
        result[key] = value
    return result


def parse(path):
    return json.loads(read(path, "complete JSON decoded with duplicate-key refusal"), object_pairs_hook=unique_object)


def check(label, condition, details=None):
    checks.append({"label": label, "passed": bool(condition), **({"details": details} if details is not None else {})})


def descriptor(path, relative):
    raw = read(path)
    st = path.lstat()
    return {"path": relative, "sha256": sha(raw), "size_bytes": len(raw), "mode": oct(stat.S_IMODE(st.st_mode))}


def safe_relative(value):
    p = PurePosixPath(value)
    return bool(value) and not p.is_absolute() and ".." not in p.parts and str(p) == value


def differences(first, second, prefix=""):
    if isinstance(first, dict) and isinstance(second, dict):
        rows = []
        for key in sorted(set(first) | set(second)):
            path = prefix + "/" + key
            if key not in first:
                rows.append({"path": path, "before_absent": True, "after": second[key]})
            elif key not in second:
                rows.append({"path": path, "before": first[key], "after_absent": True})
            else:
                rows.extend(differences(first[key], second[key], path))
        return rows
    if type(first) != type(second) or first != second:
        return [{"path": prefix, "before": first, "after": second}]
    return []


def write_new(name, value):
    raw = (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n").encode()
    with (HERE / name).open("xb") as stream:
        stream.write(raw)
    return {"path": name, "sha256": sha(raw), "size_bytes": len(raw)}


manifest_raw = read(CANDIDATE / "CANDIDATE-MANIFEST.json")
check("manifest_exact_hash", sha(manifest_raw) == EXPECTED_MANIFEST)
check("manifest_exact_size", len(manifest_raw) == 36725)
manifest = parse(CANDIDATE / "CANDIDATE-MANIFEST.json")
listed_files = manifest["files"]
check("manifest_file_count", len(listed_files) == 169)
check("manifest_paths_unique", len({r["path"] for r in listed_files}) == len(listed_files))
actual_names = set()
actual_dirs = set()
actual_bindings = {}
for path in CANDIDATE.rglob("*"):
    rel = path.relative_to(CANDIDATE).as_posix()
    st = path.lstat()
    check("regular_or_directory:" + rel, stat.S_ISREG(st.st_mode) or stat.S_ISDIR(st.st_mode))
    if stat.S_ISREG(st.st_mode):
        if rel != "CANDIDATE-MANIFEST.json":
            actual_names.add(rel)
            actual_bindings[rel] = descriptor(path, rel)
    elif stat.S_ISDIR(st.st_mode):
        actual_dirs.add(rel)
check("manifest_exact_file_inventory", actual_names == {r["path"] for r in listed_files})
check("manifest_exact_directory_inventory", actual_dirs == {r["path"] for r in manifest["directories"]})
check("manifest_payload_bytes", sum(r["size_bytes"] for r in actual_bindings.values()) == 1074121)
for row in listed_files:
    check("relative_path:" + row["path"], safe_relative(row["path"]))
    check("manifest_binding:" + row["path"], actual_bindings.get(row["path"]) == row)
for row in manifest["directories"]:
    check("directory_mode:" + row["path"], oct(stat.S_IMODE((CANDIDATE / row["path"]).lstat().st_mode)) == row["mode"])

controls = parse(CANDIDATE / "CONTROLS.json")["cases"]
expectations = parse(CANDIDATE / "EXPECTATIONS.json")["cases"]
fixtures = parse(CANDIDATE / "FIXTURE-MANIFEST.json")["files"]
construction = parse(CANDIDATE / "CONSTRUCTION.json")["images"]
check("expectations_exact_hash", reads[str(CANDIDATE / "EXPECTATIONS.json")]["sha256"] == EXPECTED_EXPECTATIONS)
check("controls_exact_count", len(controls) == 73)
check("control_ids_unique", len({r["id"] for r in controls}) == 73)
check("controls_expectations_exact_ids", {r["id"] for r in controls} == set(expectations))
check("fixtures_exact_count", len(fixtures) == 120)
check("fixture_paths_unique", len({r["path"] for r in fixtures}) == 120)
check("fixture_inventory", {r["path"] for r in fixtures} == {x for x in actual_names if x.startswith(("elf/", "fixture_inputs/"))})
check("construction_exact_image_inventory", set(construction) == {x for x in actual_names if x.startswith("elf/")})
check("construction_image_count", len(construction) == 47)
for row in fixtures:
    check("fixture_binding:" + row["path"], actual_bindings.get(row["path"]) == row)
    check("fixture_inert_mode:" + row["path"], row["mode"] == "0o600")

all_contexts = {}
case_records = []
base_bytes = read(CANDIDATE / "elf/P01_opaque_p15_values.bin")
base_header = struct.unpack_from("<16sHHIQQQIHHHHHH", base_bytes)
base_layout = construction["elf/P01_opaque_p15_values.bin"]
for row in controls:
    name = row["id"]
    ctx = parse(CANDIDATE / row["input"])
    all_contexts[name] = ctx
    expected = expectations[name]
    check("case_linkage:" + name, ctx["case_id"] == name and ctx["route"] == row["route"] and ctx["mutation"] == row["mutation"] and row["expectation"] == name)
    check("nonoperational_context:" + name, ctx["operational"] is False and ctx["operational_approval"] == "none; this is a nonoperational control context")
    check("nonexecuted_expectation:" + name, expected["current_execution"] == "not_run" and expected["host_qualified"] is False and expected["operational_plan_accepted"] is False)
    check("zero_target_starts:" + name, all(expected[k] == 0 for k in ["expected_node_starts", "expected_ldd_starts", "expected_direct_loader_starts"]))
    has_image = "image" in ctx
    check("close_obligation:" + name, expected["opened_descriptor_close_count"] == int(has_image))
    record = {"id": name, "route": row["route"], "input": row["input"], "mutation": row["mutation"], "literal_expectation": expected}
    if has_image:
        image_row = ctx["image"]
        rel = image_row["path"]
        check("context_image_binding:" + name, actual_bindings.get(rel) == image_row)
        raw = read(CANDIDATE / rel)
        lay = construction[rel]
        header = struct.unpack_from("<16sHHIQQQIHHHHHH", raw)
        parsed_header = {"elf_type": header[1], "machine": header[2], "program_offset": header[5], "program_entry_bytes": header[9], "program_count": header[10]}
        check("construction_header:" + name, parsed_header == lay["header"])
        ph = [list(struct.unpack_from("<IIQQQQQQ", raw, 64 + 56 * i)) for i in range(2)]
        check("construction_program_headers:" + name, ph == lay["program_headers"])
        entries = [list(struct.unpack_from("<qQ", raw, offset)) for offset in range(lay["dynamic_offset"], lay["dynamic_offset"] + lay["dynamic_size"], 16)]
        check("construction_dynamic_entries:" + name, entries == lay["dynamic_entries"])
        strings = bytes.fromhex(lay["stored_string_hex"])
        check("construction_strings:" + name, raw[lay["stored_string_offset"]:lay["stored_string_offset"] + len(strings)] == strings)
        reconstruction = bytearray(lay["file_bytes"])
        struct.pack_into("<16sHHIQQQIHHHHHH", reconstruction, 0, b"\x7fELF\x02\x01\x01\x00" + bytes(8), lay["header"]["elf_type"], lay["header"]["machine"], 1, 0, 64, 0, 0, 64, 56, lay["header"]["program_count"], 0, 0, 0)
        for index, segment in enumerate(lay["program_headers"]):
            struct.pack_into("<IIQQQQQQ", reconstruction, 64 + 56 * index, *segment)
        for index, entry in enumerate(lay["dynamic_entries"]):
            struct.pack_into("<qQ", reconstruction, lay["dynamic_offset"] + 16 * index, *entry)
        reconstruction[lay["stored_string_offset"]:lay["stored_string_offset"] + len(strings)] = strings
        check("complete_byte_reconstruction:" + name, bytes(reconstruction) == raw)
        record.update({"image": image_row, "header": parsed_header, "dynamic_entries": entries, "stored_strings_hex": strings.hex(), "layout_changes_from_P01": differences(base_layout, lay), "fault": ctx.get("fault"), "byte_difference_count_from_P01": sum(a != b for a, b in zip(base_bytes, raw))})
        if ctx["actual_fixture_bytes"] != {k: image_row[k] for k in ["sha256", "size_bytes", "mode"]}:
            observations.append({"kind": "baseline_fixture_descriptor_differs_from_case_image", "case": name, "actual_fixture_bytes": ctx["actual_fixture_bytes"], "image": image_row, "interpretation_pending": True})
    else:
        record["complete_context"] = ctx
    case_records.append(record)

for record in case_records:
    name = record["id"]
    ctx = all_contexts[name]
    if name.startswith("B") and name != "B16_external_digest_mismatch":
        skip = {"case_id", "route", "mutation"}
        record["changes_from_B01"] = differences({k:v for k,v in all_contexts["B01_mocked_relations"].items() if k not in skip}, {k:v for k,v in ctx.items() if k not in skip})
    elif name.startswith("S"):
        skip = {"case_id", "route", "mutation"}
        record["changes_from_S01"] = differences({k:v for k,v in all_contexts["S01_new_pair_and_shape"].items() if k not in skip}, {k:v for k,v in ctx.items() if k not in skip})
    elif name.startswith("D"):
        record["before_after_changes"] = differences(ctx["before"], ctx["after"])

protected = parse(CANDIDATE / "PROTECTED-SOURCES.json")
correction = parse(CANDIDATE / "PROTECTED-PATH-RESOLUTION.json")
for row in protected["files"] + correction["additional_hash_only_preservation"]:
    raw = read(REPO / row["path"], "hash and size only; no execution")
    check("protected_source:" + row["path"], sha(raw) == row["sha256"] and len(raw) == row["size_bytes"])
check("recorded_missing_path_still_absent", not (REPO / correction["recorded_missing_assumption"]).exists())
source_member_rows = []
wanted = {"glibc-2.41/" + path.relative_to(CANDIDATE / "sources/upstream").as_posix(): path for path in (CANDIDATE / "sources/upstream").rglob("*") if path.is_file()}
archive_data = read(ARCHIVE, "exact archive identity plus comparison of all copied candidate upstream members")
check("upstream_archive_exact_hash", sha(archive_data) == "f24aa441021121a79266f0d75242706cab8843a47901fefe74527491807f1998")
found = set()
with tarfile.open(ARCHIVE, "r:xz") as archive:
    for member in archive:
        if member.name in wanted:
            found.add(member.name)
            stream = archive.extractfile(member)
            raw = stream.read() if stream is not None else b""
            local = read(wanted[member.name], "exact candidate source copy compared to bound upstream archive")
            check("upstream_member_exact:" + member.name, member.isfile() and raw == local)
            source_member_rows.append({"member": member.name, "candidate_path": str(wanted[member.name]), "size_bytes": len(raw), "sha256": sha(raw)})
check("all_candidate_upstream_copies_found", found == set(wanted))

script_imports = {}
for path in sorted(CANDIDATE.glob("*.py")):
    tree = ast.parse(read(path, "source text inspected; AST imports enumerated; never executed"))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(x.name for x in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    script_imports[path.name] = sorted(imports)
    check("stdlib_import_names:" + path.name, all(x.split(".")[0] in sys.stdlib_module_names for x in imports))

check("candidate_manifest_unchanged_at_end", sha(read(CANDIDATE / "CANDIDATE-MANIFEST.json")) == EXPECTED_MANIFEST)
outputs = []
outputs.append(write_new("CASE-INSPECTION.json", {"schema": "ontokin.c271.p16.independent-case-inspection/1", "basis": "Raw bytes, declarative construction, complete fixture contexts, and frozen literal expectations; no product execution", "cases": case_records, "observations": observations}))
outputs.append(write_new("STATIC-INSPECTION.json", {"schema": "ontokin.c271.p16.independent-static-inspection/1", "candidate_manifest_sha256": EXPECTED_MANIFEST, "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "command": [sys.executable, "-I", "-B", str(Path(__file__).resolve())], "inspector_sha256": sha(Path(__file__).read_bytes()), "assertion_count": len(checks), "passed_count": sum(x["passed"] for x in checks), "failed": [x for x in checks if not x["passed"]], "checks": checks, "source_members": source_member_rows, "author_script_import_names": script_imports, "counts": {"controls": len(controls), "elf_images": len(construction), "fixtures": len(fixtures), "payload_files": len(actual_names), "routes": dict(collections.Counter(x["route"] for x in controls)), "descriptor_observations": len(observations)}, "limits": {"product_imported": False, "product_executed": False, "author_scripts_executed": False, "operational_plan_accepted": False, "host_input_read": False, "H0_accepted": False, "H1_approved": False}}))
outputs.append(write_new("STATIC-READSET.json", {"schema": "ontokin.c271.p16.independent-static-readset/1", "files": sorted(reads.values(), key=lambda x: x["path"])}))
print(json.dumps({"assertions": len(checks), "passed": sum(x["passed"] for x in checks), "failures": [x for x in checks if not x["passed"]], "outputs": outputs, "descriptor_observations": len(observations)}, sort_keys=True))
