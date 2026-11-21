"""Prepare a new, independent artifact revision without changing frozen inputs.

This edits only P11 authoring scripts and copies design records. It neither
imports nor executes OntoKin and does not implement its acceptance rule.
"""
from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parent
OLD = ROOT / "candidate002"
NEW = ROOT / "candidate003"
old_manifest = json.loads((OLD / "CANDIDATE-MANIFEST.json").read_text())
assert hashlib.sha256((OLD / "CANDIDATE-MANIFEST.json").read_bytes()).hexdigest() == "563e84cc83f31a202cc0eead9102b66b08050ea011dfbbf4ed6fc19db318c8f4"
for row in old_manifest["payload"] + old_manifest["supporting_files"]:
    raw = (OLD / row["path"]).read_bytes()
    assert len(raw) == row["size_bytes"] and hashlib.sha256(raw).hexdigest() == row["sha256"], row["path"]


def replace_once(text, before, after):
    assert text.count(before) == 1, before[:100]
    return text.replace(before, after)


builder = (ROOT / "build_controls.py").read_text()
builder = replace_once(builder, "from pathlib import Path\n", "from pathlib import Path, PurePosixPath\n")
start = builder.index('long_parent = "/" + "/".join')
end = builder.index('\ndef neg(identifier', start)
builder = builder[:start] + '''def relocated_context(parent, *, base_only=False, short_subject=False):
    # Logical data only: supply every ancestor required by the proposed rule.
    # No directory named in a context is inspected or created.
    context = json.loads(json.dumps(base()).replace("/fixture/app", parent))
    chain = list(reversed(PurePosixPath(parent).parents)) + [PurePosixPath(parent)]
    context["guards"] = [guard(str(path), 100 if str(path) == "/" else
        103 if str(path) == parent else 1000 + index)
        for index, path in enumerate(chain)]
    context["guards"].extend([guard(parent + "/bin", 104), guard(parent + "/lib", 105)])
    if short_subject:
        context["subject"]["path"] = parent + "/bin/py"
        context["kernel"]["proc_exe_path"] = parent + "/bin/py"
    if base_only:
        context["variant_review"]["suffixes"] = [""]
        context["variants"] = context["variants"][:1]
        context["absence_guards"] = {}
    return context


long_parent = "/" + "/".join(["a" * 63] * 63 + ["b" * 52])
assert len(long_parent) == 4085
c = relocated_context(long_parent, base_only=True, short_subject=True)
add("P07_expansion_4096_bytes", "origin_rule", "python_origin", c, accepted(long_parent + "/bin", long_parent + "/lib"), "Exact unnormalized expansion byte limit", "Origin/../lib is exactly 4096 ASCII bytes; synthetic logical paths only")
''' + builder[end:]
builder = replace_once(builder,
    'neg("N69_expansion_4097_bytes", lambda c: c.update(json.loads(json.dumps(base()).replace("/fixture/app", long_parent + "b"))),',
    'neg("N69_expansion_4097_bytes", lambda c: c.update(relocated_context(long_parent + "b", base_only=True, short_subject=True)),')
addition = '''# Exact document byte boundaries are a private reader primitive, not a
# variant-schema or profile acceptance. The production new-profile reader must
# own the fixed cap; a future adapter must not supply a replacement maximum.
variant_read_specs = {}
for name, size in (("variant_read_4mib", 4 * 1024 * 1024),
                   ("variant_read_4mib_plus1", 4 * 1024 * 1024 + 1)):
    raw = b'"' + b"v" * (size - 2) + b'"'
    binding = put(INPUTS / (name + ".bin"), raw)
    variant_read_specs[name] = {"binding": binding,
        "recipe": {"prefix_hex": "22", "repeated_byte_hex": "76",
                   "repeat_count": size - 2, "suffix_hex": "22"},
        "canonical_json_kind": "string",
        "variant_document_schema_valid": False}


def variant_read_context(name):
    return {"schema": "ontokin.c271.p11-bounded-variant-read-context/1",
        "operational": False, "variant_document": variant_read_specs[name]["binding"],
        "seam": "production_new_profile_variant_byte_reader_before_decode",
        "maximum_is_owned_by_production_reader": True,
        "subsequent_json_and_closed_shape_validation": "not_exercised_by_this_primitive"}


add("P08_variant_reader_4mib", "bounded_variant_read", "python_origin", variant_read_context("variant_read_4mib"),
    {"outcome": "bounded_read", "accepted_for": "new_profile_variant_byte_reader_only",
     "size_bytes": 4 * 1024 * 1024, "sha256": variant_read_specs["variant_read_4mib"]["binding"]["sha256"],
     "canonical_decode_or_shape_acceptance": False, "host_qualified": False, "target_starts": 0},
    "Read exactly 4 MiB under the actual new-profile reader's fixed internal cap",
    "Exact canonical JSON scalar bytes; later variant-object schema rejects; no caller-selected cap")
add("N74_variant_reader_over_bound", "bounded_variant_read", "python_origin", variant_read_context("variant_read_4mib_plus1"),
    refusal("CHI-UNSUPPORTED", "bounds", "LP-BOUND"),
    "Refuse 4 MiB plus one byte before canonical decoding or variant shape checks",
    "Exact paired scalar byte recipe; production reader cap, not an adapter parameter")

component_parent = "/" + "/".join("p%03d" % index for index in range(124))
c = relocated_context(component_parent, base_only=True, short_subject=True)
add("P09_expansion_128_components", "origin_rule", "python_origin", c,
    accepted(component_parent + "/bin", component_parent + "/lib"),
    "Exactly 128 pre-reduction components including leading root and literal parent component",
    "All other named paths have at most 128 components and fewer than 4096 ASCII bytes; synthetic base-only variants")
neg("N75_expansion_129_components",
    lambda c: c.update(relocated_context(component_parent + "/q", base_only=True, short_subject=True)),
    "CHI-UNSUPPORTED", "bounds", "LP-BOUND",
    "Only the pre-reduction path exceeds 128 components; all supplied paths and byte lengths fit")
neg("N76_nonascii_origin", lambda c: c.update(relocated_context("/fixture/caf\\u00e9")),
    "CHI-UNSUPPORTED", "new_path_policy", "LP-PATH-ASCII",
    "New origin/subject/kernel/derived path fields must be ASCII; legacy absolute-path semantics stay unchanged")


def nonascii_suffix(context):
    suffix = "h\\u00e1rdware"
    path = "/fixture/app/lib/" + suffix
    context["variant_review"]["suffixes"] = ["", suffix]
    context["variants"] = [context["variants"][0],
        {"suffix": suffix, "path": path, "state": "absent", "absent_at": path}]
    context["absence_guards"] = {path: {"parent": "/fixture/app/lib",
        "parent_device": 101, "parent_inode": 105, "absent": True}}


neg("N77_nonascii_variant_suffix", nonascii_suffix,
    "CHI-UNSUPPORTED", "new_path_policy", "LP-PATH-ASCII",
    "New reviewed suffix and derived variant path must be ASCII even with an ASCII origin")

'''
builder = replace_once(builder, "def drift_candidate(c):\n", addition + "def drift_candidate(c):\n")
builder = replace_once(builder,
    '"truncated_auxiliary_vector": aux_bindings["auxv_truncated"],',
    '"truncated_auxiliary_vector": aux_bindings["auxv_truncated"],\n    "variant_document_read_fixtures": variant_read_specs,')
builder = replace_once(builder,
    '"constructor": {"path": "../build_controls.py",',
    '"constructor": {"path": "../" + Path(__file__).name,')
with (ROOT / "build_controls_attempt003.py").open("x") as stream:
    stream.write(builder)

validator = (ROOT / "validate_artifacts.py").read_text()
validator = replace_once(validator, "from pathlib import Path\n", "from pathlib import Path, PurePosixPath\n")
validator = replace_once(validator,
    '("metadata", "refusal", "rule_acceptance", "propagated_callback")',
    '("metadata", "refusal", "rule_acceptance", "propagated_callback", "bounded_read")')
validator = replace_once(validator,
    'check(ident + " positive path lengths fit", all(len(p.encode("ascii")) <= 4096 for p in paths))',
    'check(ident + " positive path lengths fit", all(len(p.encode("ascii")) <= 4096 for p in paths))\n        check(ident + " positive component counts fit", all(len(PurePosixPath(p).parts) <= 128 for p in paths))')
extra_checks = '''def context_for(identifier):
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

'''
validator = replace_once(validator, 'report = {"schema":', extra_checks + 'report = {"schema":')
validator = replace_once(validator,
    '"passed": not failures, "check_count": len(checks),',
    '"passed": not failures, "check_count": len(checks), "boundary_measurements": boundary_measurements,')
with (ROOT / "validate_artifacts_attempt003.py").open("x") as stream:
    stream.write(validator)

NEW.mkdir()
for path in sorted(OLD.iterdir()):
    if path.is_file() and path.name not in {"CANDIDATE-MANIFEST.json", "EXPECTATIONS.json", "CONSTRUCTION.json", "FIXTURE-MANIFEST.json"}:
        shutil.copy2(path, NEW / path.name)
print(json.dumps({"prepared": NEW.name, "old_payloads_verified": len(old_manifest["payload"]),
    "old_support_files_verified": len(old_manifest["supporting_files"]),
    "new_scripts": ["build_controls_attempt003.py", "validate_artifacts_attempt003.py"],
    "product_execution": False}, sort_keys=True))
