"""Static corpus integrity/layout checker; no product code or acceptance rule.

This checks self-consistency of declared fixtures, not whether any production
implementation implements the decision. It never opens host/kernel input paths.
"""
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import struct
import sys

root = Path(sys.argv[1]).resolve()
manifest = json.loads((root / "FIXTURE-MANIFEST.json").read_text())
expectations = json.loads((root / "EXPECTATIONS.json").read_text())["cases"]
construction = json.loads((root / "CONSTRUCTION.json").read_text())
checks = []
failures = []


def check(label, condition):
    checks.append(label)
    if not condition:
        failures.append(label)


file_rows = {row["path"]: row for row in manifest["files"]}
check("unique fixture paths", len(file_rows) == len(manifest["files"]))
check("exact fixture inventory", set(file_rows) == {str(p.relative_to(root)) for p in (root / "fixture_inputs").iterdir()})
for name, row in file_rows.items():
    path = root / name
    raw = path.read_bytes()
    check(name + " regular nonexecutable file", stat.S_ISREG(path.lstat().st_mode) and not path.is_symlink() and not path.stat().st_mode & 0o111)
    check(name + " exact size/hash/mode", row["size_bytes"] == len(raw) and row["sha256"] == hashlib.sha256(raw).hexdigest() and row["mode"] == oct(path.stat().st_mode & 0o777))

ids = [row["id"] for row in manifest["cases"]]
check("unique control IDs", len(ids) == len(set(ids)))
check("exact expectation coverage", set(ids) == set(expectations))
by_image = {row["binding"]["path"]: row for row in construction["elf_layouts"].values()}
for case in manifest["cases"]:
    ident = case["id"]
    context = json.loads((root / case["input"]["path"]).read_text())
    expected = expectations[ident]
    check(ident + " exact input reference", case["input"] == file_rows[case["input"]["path"]])
    check(ident + " exact image reference", case["image"] == file_rows[case["image"]["path"]] == context["image"])
    check(ident + " nonoperational", context["operational"] is False and expected["host_qualified"] is False and expected["target_starts"] == 0)
    check(ident + " precise outcome", expected["outcome"] in ("metadata", "refusal", "rule_acceptance", "propagated_callback", "bounded_read"))
    if expected["outcome"] == "refusal":
        check(ident + " refusal class/stage", expected["code"].startswith("CHI-") and bool(expected["stage"]) and bool(expected["rule_id"]))
    if expected["outcome"] == "rule_acceptance":
        check(ident + " raw metadata expectation", expected["metadata"] == by_image[case["image"]["path"]]["raw_expected_metadata"])
        check(ident + " positive declared mapping", expected["origin"] == context["origin_claim"] and expected["expanded_rpath"] == context["expanded_claim"])
        # Length/cardinality are authoring consistency facts, not a loader rule.
        paths = [context["subject"]["path"], context["origin_claim"], context["origin_claim"] + "/../lib", *context["expanded_claim"], *context["search_directories"], *context["absence_guards"], *[r["path"] for r in context["variants"]]]
        check(ident + " positive path lengths fit", all(len(p.encode("ascii")) <= 4096 for p in paths))
        check(ident + " positive component counts fit", all(len(PurePosixPath(p).parts) <= 128 for p in paths))
        check(ident + " positive bounds fit", len(context["needed_names_claim"]) <= 4096 and len(context["variants"]) <= 128 and sum(r["state"] == "directory" for r in context["variants"]) * len(context["needed_names_claim"]) <= 32768)

for name, layout in construction["elf_layouts"].items():
    raw = (root / layout["binding"]["path"]).read_bytes()
    check(name + " fixed ELF header", raw[:64].hex() == layout["elf_header_hex"])
    for index, ph in enumerate(layout["program_headers"]):
        check(name + " fixed program header " + str(index), raw[64+56*index:120+56*index] == struct.pack("<IIQQQQQQ", *ph))
        check(name + " no executable segment " + str(index), ph[1] & 1 == 0)
    dyn = b"".join(struct.pack("<qQ", *e) for e in layout["dynamic_entries"])
    check(name + " fixed dynamic bytes", raw[512:512+len(dyn)] == dyn)
    check(name + " fixed interpreter bytes", raw[1024:1024+len(bytes.fromhex(layout["interpreter_hex"]))].hex() == layout["interpreter_hex"])
    check(name + " fixed string bytes", raw[4096:].hex() == layout["string_table_hex"])
    for field in layout["fields"]:
        start = 4096 + field["offset"]
        check(name + " field " + str(field["offset"]), raw[start:start+len(bytes.fromhex(field["raw_hex"]))].hex() == field["raw_hex"] and bytes.fromhex(field["raw_hex"]) == field["text"].encode("ascii") + b"\0")
for name, spec in construction["auxiliary_vectors"].items():
    check(name + " exact auxiliary bytes", (root / spec["binding"]["path"]).read_bytes() == b"".join(struct.pack("<QQ", *p) for p in spec["pairs"]))

def context_for(identifier):
    case = next(case for case in manifest["cases"] if case["id"] == identifier)
    return json.loads((root / case["input"]["path"]).read_text())


def named_paths(context):
    return [context["subject"]["path"], context["kernel"]["proc_exe_path"], context["origin_claim"],
        *context["expanded_claim"], *context["search_directories"], *context["absence_guards"],
        *[row["path"] for row in context["guards"]], *[row["path"] for row in context["variants"]],
        *[row["absent_at"] for row in context["variants"] if "absent_at" in row]]


boundary_measurements = {}
for identifier, raw_bytes, raw_components in (("P07_expansion_4096_bytes", 4096, None),
    ("N69_expansion_4097_bytes", 4097, None), ("P09_expansion_128_components", None, 128),
    ("N75_expansion_129_components", None, 129)):
    context = context_for(identifier)
    raw = context["origin_claim"] + "/../lib"
    supplied = named_paths(context)
    required_guards = {str(p) for path in (context["origin_claim"], *context["expanded_claim"])
        for p in (PurePosixPath(path), *PurePosixPath(path).parents)}
    actual_guards = {row["path"] for row in context["guards"]}
    check(identifier + " complete exact logical ancestor guards", required_guards == actual_guards)
    check(identifier + " only raw expression may cross byte limit", all(len(p.encode("ascii")) <= 4096 for p in supplied))
    check(identifier + " only raw expression may cross component limit", all(len(PurePosixPath(p).parts) <= 128 for p in supplied))
    check(identifier + " synthetic base-only model", context["variant_review"]["suffixes"] == [""] and len(context["variants"]) == 1 and not context["absence_guards"])
    if raw_bytes is not None:
        check(identifier + " exact isolated raw byte length", len(raw.encode("ascii")) == raw_bytes)
        check(identifier + " raw component count fits", len(PurePosixPath(raw).parts) <= 128)
    if raw_components is not None:
        check(identifier + " exact isolated raw component count", len(PurePosixPath(raw).parts) == raw_components)
        check(identifier + " raw byte length fits", len(raw.encode("ascii")) <= 4096)
    boundary_measurements[identifier] = {"raw_bytes": len(raw.encode("ascii")),
        "raw_components_including_root": len(PurePosixPath(raw).parts),
        "max_supplied_bytes": max(len(p.encode("ascii")) for p in supplied),
        "max_supplied_components_including_root": max(len(PurePosixPath(p).parts) for p in supplied),
        "supplied_guard_count": len(actual_guards), "required_guard_count": len(required_guards)}

for name, spec in construction["variant_document_read_fixtures"].items():
    binding = spec["binding"]
    raw = (root / binding["path"]).read_bytes()
    recipe = spec["recipe"]
    check(name + " exact read-boundary byte recipe", raw == bytes.fromhex(recipe["prefix_hex"]) +
        bytes.fromhex(recipe["repeated_byte_hex"]) * recipe["repeat_count"] + bytes.fromhex(recipe["suffix_hex"]))
    check(name + " exact fixture descriptor", binding == file_rows[binding["path"]])
    value = json.loads(raw)
    check(name + " canonical JSON scalar, never variant shape", type(value) is str and
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii") == raw and
        spec["variant_document_schema_valid"] is False)
check("paired exact document byte boundaries", construction["variant_document_read_fixtures"]["variant_read_4mib"]["binding"]["size_bytes"] == 4194304 and
    construction["variant_document_read_fixtures"]["variant_read_4mib_plus1"]["binding"]["size_bytes"] == 4194305)
check("read positive scope only", expectations["P08_variant_reader_4mib"]["outcome"] == "bounded_read" and
    expectations["P08_variant_reader_4mib"]["canonical_decode_or_shape_acceptance"] is False)
for identifier in ("P08_variant_reader_4mib", "N74_variant_reader_over_bound"):
    context = context_for(identifier)
    check(identifier + " actual production cap seam", context["maximum_is_owned_by_production_reader"] is True and
        context["seam"] == "production_new_profile_variant_byte_reader_before_decode" and "maximum_bytes" not in context)
nonascii_origin = context_for("N76_nonascii_origin")
nonascii_suffix = context_for("N77_nonascii_variant_suffix")
check("non-ASCII origin control isolated", not nonascii_origin["origin_claim"].isascii() and
    all(len(p.encode("utf-8")) <= 4096 and len(PurePosixPath(p).parts) <= 128 for p in named_paths(nonascii_origin)))
check("non-ASCII suffix with ASCII origin isolated", nonascii_suffix["origin_claim"].isascii() and
    any(not suffix.isascii() for suffix in nonascii_suffix["variant_review"]["suffixes"]) and
    all(len(p.encode("utf-8")) <= 4096 and len(PurePosixPath(p).parts) <= 128 for p in named_paths(nonascii_suffix)))

report = {"schema": "ontokin.c271.p11-static-corpus-check/1", "candidate": root.name,
    "passed": not failures, "check_count": len(checks), "boundary_measurements": boundary_measurements, "failure_count": len(failures), "failures": failures,
    "case_count": len(ids), "fixture_file_count": len(file_rows), "elf_image_count": len(by_image),
    "product_imports": 0, "product_parser_calls": 0, "target_executions": 0, "host_observations": 0,
    "python_tooling_version": sys.version, "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "claim": "Fixture integrity and fixed construction layout only; no implementation, operational profile or host pass"}
print(json.dumps(report, indent=2, sort_keys=True))
sys.exit(0 if not failures else 1)
