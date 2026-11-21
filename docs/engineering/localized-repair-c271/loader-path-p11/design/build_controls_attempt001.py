"""Construct inert P11 control bytes; never import/execute OntoKin or a target.

Expected outcomes are explicit author inputs below, not output from a policy
implementation. The script is a fixture constructor, not a loader validator.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(sys.argv[1]).resolve()
INPUTS = ROOT / "fixture_inputs"
INPUTS.mkdir(exist_ok=True)
NEW_SCHEMA = "ontokin.current-host-readback-inspection-plan/0.1.1"
NEW_PROFILE = "linux-glibc-declared-python-origin-rpath-v1"
OLD_SCHEMA = "ontokin.current-host-readback-inspection-plan/0.1.0"
OLD_PROFILE = "linux-glibc-declared-closure-v1"
SELECTED = {"sha256": "fa67443527ed9647f760d807e2a38f26340757123e643c4639cf273ed15d5ea7", "size_bytes": 30894944, "mode": "0o755"}


def put(path, raw, mode=0o600):
    with path.open("xb") as stream:
        stream.write(raw)
    path.chmod(mode)
    return {"path": str(path.relative_to(ROOT)), "size_bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "mode": oct(mode)}


def document(path, value):
    return put(path, (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n").encode("ascii"))


layouts = {}
image_bindings = {}


def image(name, *, rpath=None, runpath=None, needed=("libalpha.so", "libbeta.so"), flags=0, flags1=1, extra=(), machine=62):
    # A single read-only PT_LOAD maps all bytes. Entry point is zero; there is
    # no machine code or executable segment. These are parser data only.
    strings = bytearray(b"\0")
    fields = []
    for tag, value in [(1, n) for n in needed] + ([(15, rpath)] if rpath is not None else []) + ([(29, runpath)] if runpath is not None else []):
        pos = len(strings)
        raw = value.encode("ascii") + b"\0"
        strings.extend(raw)
        fields.append({"tag": tag, "offset": pos, "text": value, "raw_hex": raw.hex()})
    entries = [(5, 0x401000), (10, len(strings))] + [(f["tag"], f["offset"]) for f in fields]
    if flags:
        entries.append((30, flags))
    entries.append((0x6FFFFFFB, flags1))
    entries.extend(extra)
    entries.append((0, 0))
    dyn = b"".join(struct.pack("<qQ", *e) for e in entries)
    interp = b"/fixture/ld-linux-x86-64.so.2\0"
    raw = bytearray(4096 + len(strings))
    ident = b"\x7fELF\x02\x01\x01\x00" + bytes(8)
    head = struct.pack("<16sHHIQQQIHHHHHH", ident, 2, machine, 1, 0, 64, 0, 0, 64, 56, 3, 0, 0, 0)
    raw[:64] = head
    pheaders = [(1, 4, 0, 0x400000, 0, len(raw), len(raw), 4096),
                (2, 4, 512, 0x400200, 0, len(dyn), len(dyn), 8),
                (3, 4, 1024, 0x400400, 0, len(interp), len(interp), 1)]
    for index, values in enumerate(pheaders):
        raw[64 + 56 * index:120 + 56 * index] = struct.pack("<IIQQQQQQ", *values)
    raw[512:512 + len(dyn)] = dyn
    raw[1024:1024 + len(interp)] = interp
    raw[4096:] = strings
    binding = put(INPUTS / (name + ".bin"), bytes(raw))
    image_bindings[name] = binding
    layouts[name] = {"binding": binding, "elf_header_hex": head.hex(), "program_headers": pheaders,
                     "dynamic_offset": 512, "dynamic_entries": entries, "interpreter_offset": 1024,
                     "interpreter_hex": interp.hex(), "string_table_offset": 4096,
                     "string_table_hex": strings.hex(), "fields": fields,
                     "machine": machine, "flags": flags, "flags1": flags1,
                     "raw_expected_metadata": {"class": 64, "endian": "little", "machine": machine,
                         "type": 2, "interpreter": interp[:-1].decode("ascii"), "needed": list(needed), "soname": None,
                         "rpath": [] if rpath is None else rpath.split(":"), "runpath": [] if runpath is None else runpath.split(":")}}
    return name


image("literal_none")
image("literal_rpath", rpath="/fixture/app/lib")
image("literal_runpath", runpath="/fixture/app/lib")
image("python_origin", rpath="$ORIGIN/../lib")
image("braced_origin", rpath="${ORIGIN}/../lib")
image("origin_lib", rpath="$ORIGIN/lib")
image("origin_lib_token", rpath="$ORIGIN/../$LIB")
image("origin_platform_token", rpath="$ORIGIN/../$PLATFORM")
image("origin_unknown_token", rpath="$UNKNOWN/../lib")
image("origin_twice", rpath="$ORIGIN/$ORIGIN/../lib")
image("origin_empty_entry", rpath="$ORIGIN/../lib:")
image("origin_duplicate", rpath="$ORIGIN/../lib:$ORIGIN/../lib")
image("origin_literal_mix", rpath="$ORIGIN/../lib:/fixture/other")
image("origin_relative", rpath="../lib")
image("origin_double_parent", rpath="$ORIGIN/../../lib")
image("origin_whitespace", rpath="$ORIGIN/../lib ")
image("origin_runpath", runpath="$ORIGIN/../lib")
image("both_literal", rpath="/fixture/app/lib", runpath="/fixture/other")
image("origin_both", rpath="$ORIGIN/../lib", runpath="/fixture/other")
image("origin_df_origin", rpath="$ORIGIN/../lib", flags=1)
image("origin_df1_origin", rpath="$ORIGIN/../lib", flags1=0x81)
image("origin_allowed_flags", rpath="$ORIGIN/../lib", flags=8, flags1=0x08000001)
image("origin_unknown_tag", rpath="$ORIGIN/../lib", extra=((0x7FFFFFFF, 1),))
image("origin_needed_token", rpath="$ORIGIN/../lib", needed=("$ORIGIN", "libbeta.so"))
image("origin_duplicate_tag", rpath="$ORIGIN/../lib", extra=((15, 25),))
image("origin_aarch64", rpath="$ORIGIN/../lib", machine=183)

aux_bindings = {}
aux_specs = {
    "auxv_zero": [(6, 4096), (23, 0), (0, 0)],
    "auxv_secure": [(6, 4096), (23, 1), (0, 0)],
    "auxv_missing": [(6, 4096), (0, 0)],
    "auxv_duplicate": [(23, 0), (23, 0), (0, 0)],
    "auxv_no_terminator": [(6, 4096), (23, 0)],
    "auxv_256_pairs": [(1, 0)] * 254 + [(23, 0), (0, 0)],
    "auxv_257_pairs": [(1, 0)] * 255 + [(23, 0), (0, 0)],
}
for name, pairs in aux_specs.items():
    aux_bindings[name] = put(INPUTS / (name + ".bin"), b"".join(struct.pack("<QQ", *p) for p in pairs))
aux_bindings["auxv_truncated"] = put(INPUTS / "auxv_truncated.bin", struct.pack("<QQ", 23, 0) + b"\0")


def guard(path, inode, kind="directory", target=None):
    return {"path": path, "kind": kind, "device": 101, "inode": inode, "mode": "0o755", "target": target}


def base():
    subject = "/fixture/app/bin/python"
    return {"schema": "ontokin.c271.p11-portable-rule-context/1", "operational": False,
        "assumptions": ["Synthetic rule seam only; operational selected-image pin is not bypassed",
                        "Synthetic loader suffix review is complete for this finite logical context",
                        "All inherited P07 source and non-origin closure checks are separately required"],
        "plan_selection": {"schema": NEW_SCHEMA, "profile": NEW_PROFILE,
            "shared_libraries_stdout_predicate": OLD_PROFILE, "external_digest_matches": True,
            "origin_object_present": True, "origin_object_unknown_keys": [], "variant_descriptor_matches": True,
            "rationale_descriptor_matches": True},
        "subject": {"path": subject, "role": "author_python", "invocation": "linux-direct-main",
            "kind": "file", "device": 101, "inode": 107, "mode": "0o755", "nlink": 1,
            "actual_bytes": image_bindings["python_origin"], "descriptor_matches": True,
            "operational_pin": SELECTED},
        "origin_claim": "/fixture/app/bin", "expanded_claim": ["/fixture/app/lib"],
        "kernel": {"proc_exe_path": subject, "proc_file_identity": {"device": 101, "inode": 107},
            "read_status": "read", "at_secure_claim": 0, "auxv": aux_bindings["auxv_zero"]},
        "guards": [guard("/", 100), guard("/fixture", 102), guard("/fixture/app", 103),
                   guard("/fixture/app/bin", 104), guard("/fixture/app/lib", 105)],
        "search_directories": {"/fixture/app/lib": {"device": 101, "inode": 105, "mode": "0o755", "entries": {}}},
        "absence_guards": {"/fixture/app/lib/glibc-hwcaps": {"parent": "/fixture/app/lib", "parent_device": 101, "parent_inode": 105, "absent": True},
                           "/fixture/app/lib/tls": {"parent": "/fixture/app/lib", "parent_device": 101, "parent_inode": 105, "absent": True}},
        "variant_review": {"loader_identity": "synthetic-loader-v1", "source_review_identity": "synthetic-review-v1",
            "suffixes": ["", "glibc-hwcaps/x86-64-v2", "tls/x86_64"], "completeness": "synthetic_declared_complete"},
        "variants": [{"suffix": "", "path": "/fixture/app/lib", "state": "directory"},
                     {"suffix": "glibc-hwcaps/x86-64-v2", "path": "/fixture/app/lib/glibc-hwcaps/x86-64-v2", "state": "absent", "absent_at": "/fixture/app/lib/glibc-hwcaps"},
                     {"suffix": "tls/x86_64", "path": "/fixture/app/lib/tls/x86_64", "state": "absent", "absent_at": "/fixture/app/lib/tls"}],
        "closure_images": [{"id": "python", "needed": ["libalpha.so", "libbeta.so"], "soname": None},
                           {"id": "libalpha", "needed": ["libbeta.so"], "soname": "libalpha.so"},
                           {"id": "libbeta", "needed": [], "soname": "libbeta.so"}],
        "needed_names_claim": ["libalpha.so", "libbeta.so"],
        "phase": "initial", "approved_before": None, "fault": None}


cases = []
expectations = {}


def refusal(code, stage, rule, *, reason=None, cause=None, state="REJECTED"):
    value = {"outcome": "refusal", "code": code, "stage": stage, "rule_id": rule, "state": state,
             "host_qualified": False, "target_starts": 0}
    if reason is not None:
        value["reason"] = reason
    if cause is not None:
        value["cause_code"] = cause
    return value


def accepted(origin="/fixture/app/bin", expanded="/fixture/app/lib"):
    return {"outcome": "rule_acceptance", "accepted_for": "synthetic_private_rule_only", "origin": origin,
            "raw_rpath": ["$ORIGIN/../lib"], "expanded_rpath": [expanded], "runpath": [],
            "metadata": layouts["python_origin"]["raw_expected_metadata"],
            "nonselecting": True, "host_qualified": False, "target_starts": 0}


def add(identifier, route, image_name, context, expected, purpose, mutation):
    context = deepcopy(context)
    context["image"] = image_bindings[image_name]
    if "subject" in context:
        context["subject"]["actual_bytes"] = image_bindings[image_name]
    descriptor = document(INPUTS / (identifier + ".json"), context)
    cases.append({"id": identifier, "route": route, "input": descriptor, "image": image_bindings[image_name],
                  "purpose": purpose, "mutation": mutation, "expected_key": identifier})
    expectations[identifier] = expected


for ident, name in (("L01_no_search_paths", "literal_none"), ("L02_absolute_rpath", "literal_rpath"), ("L03_absolute_runpath", "literal_runpath")):
    add(ident, "legacy_metadata", name, {"schema": "ontokin.c271.p11-legacy-context/1", "operational": False, "require_interpreter": True},
        {"outcome": "metadata", "value": layouts[name]["raw_expected_metadata"], "target_starts": 0, "host_qualified": False},
        "Preserve a literal/default legacy result exactly", "None")
for ident, name, why in (("L04_origin_still_refuses", "python_origin", "Unreviewed loader token expansion"),
                         ("L05_braced_still_refuses", "braced_origin", "Unreviewed loader token expansion"),
                         ("L06_both_tags_refuse", "both_literal", "Conflicting legacy and modern search paths"),
                         ("L07_origin_flag_refuses", "origin_df_origin", "Unsupported dynamic flags")):
    add(ident, "legacy_metadata", name, {"schema": "ontokin.c271.p11-legacy-context/1", "operational": False, "require_interpreter": True},
        refusal("CHI-UNSUPPORTED", "legacy_parser", "LEGACY-UNCHANGED", reason=why),
        "Preserve the historical default refusal", "Only the named inert ELF field differs")

add("P01_nonselecting_base", "origin_rule", "python_origin", base(), accepted(), "Exact token expands under complete nonselecting context", "None")
c = base(); c["search_directories"]["/fixture/app/lib"]["entries"]["README"] = {"kind": "file", "device": 101, "inode": 120, "mode": "0o644", "target": None}
add("P02_unrelated_entry", "origin_rule", "python_origin", c, accepted(), "A noncandidate basename does not select a dependency", "Add README only")


def present_variant(context, branch, leaf, candidate=None, candidate_kind="file"):
    # All data stays logical JSON. No symlink or directory tree is materialized.
    prefix = "/fixture/app/lib/" + branch
    path = prefix + "/" + leaf
    context["absence_guards"].pop(prefix, None)
    context["search_directories"]["/fixture/app/lib"]["entries"][branch] = {"kind": "directory", "device": 101, "inode": 121, "mode": "0o755", "target": None}
    context["search_directories"][prefix] = {"device": 101, "inode": 121, "mode": "0o755", "entries": {leaf: {"kind": "directory", "device": 101, "inode": 122, "mode": "0o755", "target": None}}}
    entries = {} if candidate is None else {candidate: {"kind": candidate_kind, "device": 101, "inode": 123, "mode": "0o644", "target": "/unbound" if candidate_kind == "symlink" else None}}
    context["search_directories"][path] = {"device": 101, "inode": 122, "mode": "0o755", "entries": entries}
    context["guards"].extend([guard(prefix, 121), guard(path, 122)])
    for row in context["variants"]:
        if row["path"] == path:
            row["state"] = "directory"; row.pop("absent_at", None)


c = base(); present_variant(c, "glibc-hwcaps", "x86-64-v2")
add("P03_present_hwcaps_empty", "origin_rule", "python_origin", c, accepted(), "Present hardware alternative is nonselecting", "Replace exact guarded absence by fully bound empty hardware directory")
c = base(); c["closure_images"].append({"id": "extension", "needed": ["libgamma.so"], "soname": None}); c["needed_names_claim"].append("libgamma.so")
add("P04_extension_name_covered", "origin_rule", "python_origin", c, accepted(), "Full name union includes extension dependency", "Add extension and corresponding absent candidate name")
add("P05_allowed_flags_preserved", "origin_rule", "origin_allowed_flags", base(), accepted(), "Current allowed flags do not become a new origin flag exemption", "DT_FLAGS=8; DT_FLAGS_1=0x08000001; primitive only")
c = base(); c["kernel"]["auxv"] = aux_bindings["auxv_256_pairs"]
add("P06_auxv_256_pairs", "origin_rule", "python_origin", c, accepted(), "Exact auxiliary-vector pair limit", "256 complete pairs including terminator")
long_parent = "/" + "/".join(["a" * 63] * 63 + ["b" * 52])
assert len(long_parent) == 4085
c = json.loads(json.dumps(base()).replace("/fixture/app", long_parent))
add("P07_expansion_4096_bytes", "origin_rule", "python_origin", c, accepted(long_parent + "/bin", long_parent + "/lib"), "Exact unnormalized expansion byte limit", "Origin/../lib is exactly 4096 ASCII bytes; synthetic logical paths only")

def neg(identifier, change, code, stage, rule, purpose, *, image_name="python_origin", route="origin_rule", cause=None):
    c = base(); change(c)
    add(identifier, route, image_name, c, refusal(code, stage, rule, cause=cause), purpose, purpose)

neg("N01_old_schema_new_profile", lambda c: c["plan_selection"].update(schema=OLD_SCHEMA), "CHI-PLAN", "profile_selection", "LP-SCHEMA-PROFILE", "Old schema cannot select new profile")
neg("N02_new_schema_old_profile", lambda c: c["plan_selection"].update(profile=OLD_PROFILE), "CHI-PLAN", "profile_selection", "LP-SCHEMA-PROFILE", "New schema cannot silently fall back")
neg("N03_origin_field_missing", lambda c: c["plan_selection"].update(origin_object_present=False), "CHI-PLAN", "profile_selection", "LP-CLOSED-SHAPE", "Required new origin object absent")
neg("N04_origin_unknown_key", lambda c: c["plan_selection"].update(origin_object_unknown_keys=["approved"]), "CHI-PLAN", "profile_selection", "LP-CLOSED-SHAPE", "Self-approval or unknown key refuses")
neg("N05_external_digest_mismatch", lambda c: c["plan_selection"].update(external_digest_matches=False), "CHI-PLAN", "plan_authentication", "LP-EXTERNAL-DIGEST", "Unauthenticated plan never opens token admission", route="binding_rule")
neg("N06_variant_descriptor_mismatch", lambda c: c["plan_selection"].update(variant_descriptor_matches=False), "CHI-LOADER", "variant_binding", "LP-VARIANT-BINDING", "Variant document bytes drift")
neg("N07_rationale_descriptor_mismatch", lambda c: c["plan_selection"].update(rationale_descriptor_matches=False), "CHI-LOADER", "variant_binding", "LP-VARIANT-BINDING", "Source rationale bytes drift")
for i, role in enumerate(("shared_object", "node", "ldd_target", "git"), 8):
    neg("N%02d_wrong_role_%s" % (i, role), lambda c, r=role: c["subject"].update(role=r), "CHI-UNSUPPORTED", "subject_context", "LP-ROLE", "Token subject role is " + role)
neg("N12_explicit_loader", lambda c: c["subject"].update(invocation="explicit-loader"), "CHI-UNSUPPORTED", "subject_context", "LP-INVOCATION", "Explicit loader origin remains outside profile")
neg("N13_kernel_loader_path", lambda c: c["kernel"].update(proc_exe_path="/fixture/ld-linux-x86-64.so.2"), "CHI-INSPECTOR", "kernel_origin", "LP-KERNEL-EXE", "Kernel executable is loader despite Python pathname claim")
neg("N14_kernel_deleted", lambda c: c["kernel"].update(proc_exe_path="/fixture/app/bin/python (deleted)"), "CHI-INSPECTOR", "kernel_origin", "LP-KERNEL-EXE", "Deleted executable pathname cannot supply origin")
neg("N15_kernel_unavailable", lambda c: c["kernel"].update(read_status="unavailable", proc_exe_path=None), "CHI-INSPECTOR", "kernel_origin", "LP-KERNEL-EXE", "No fallback when kernel origin unavailable")
neg("N16_kernel_inode_mismatch", lambda c: c["kernel"]["proc_file_identity"].update(inode=999), "CHI-INSPECTOR", "kernel_origin", "LP-KERNEL-IDENTITY", "Kernel image and selected file inode differ")
neg("N17_evidence_copy_origin", lambda c: c.update(origin_claim="/retained/evidence", expanded_claim=["/retained/lib"]), "CHI-PATH", "origin_binding", "LP-ORIGIN", "Inert evidence-copy directory is not execution origin")
neg("N18_cwd_origin", lambda c: c.update(origin_claim="/current/working/directory"), "CHI-PATH", "origin_binding", "LP-ORIGIN", "Working directory cannot supply origin")
neg("N19_leaf_symlink", lambda c: c["subject"].update(kind="symlink"), "CHI-PATH", "origin_binding", "LP-ALIAS", "Token-bearing subject is a symlink")
neg("N20_origin_symlink", lambda c: c["guards"][3].update(kind="symlink", target="/other/bin"), "CHI-PATH", "origin_binding", "LP-ALIAS", "Do not lexically cancel symlink/..")
neg("N21_ancestor_symlink", lambda c: c["guards"][2].update(kind="symlink", target="/other/app"), "CHI-PATH", "origin_binding", "LP-ALIAS", "Origin ancestor alias is not admitted")
neg("N22_hardlink_subject", lambda c: c["subject"].update(nlink=2), "CHI-PATH", "origin_binding", "LP-ALIAS", "Token-bearing executable has a hardlink alias")
neg("N23_sibling_lib_symlink", lambda c: c["guards"][4].update(kind="symlink", target="/other/lib"), "CHI-PATH", "origin_binding", "LP-ALIAS", "Expanded sibling directory is a symlink")
neg("N24_subject_binding_mismatch", lambda c: c["subject"].update(descriptor_matches=False), "CHI-INSPECTOR", "subject_binding", "LP-SUBJECT-BINDING", "Descriptor differs from observed synthetic bytes", route="binding_rule")
neg("N25_synthetic_fails_real_pin", lambda c: c["subject"].update(enforce_operational_pin=True), "CHI-INSPECTOR", "subject_binding", "LP-SELECTED-PIN", "Synthetic ELF bytes cannot satisfy real selected Python pin", route="binding_rule")
neg("N26_secure_mode", lambda c: c["kernel"].update(auxv=aux_bindings["auxv_secure"]), "CHI-UNSUPPORTED", "kernel_origin", "LP-SECURE", "AT_SECURE=1 is outside supported semantics")
for identifier, auxname in (("N27_auxv_missing_secure", "auxv_missing"), ("N28_auxv_duplicate_secure", "auxv_duplicate"), ("N29_auxv_unterminated", "auxv_no_terminator"), ("N30_auxv_truncated", "auxv_truncated")):
    neg(identifier, lambda c, a=auxname: c["kernel"].update(auxv=aux_bindings[a]), "CHI-INSPECTOR", "kernel_origin", "LP-AUXV", "Malformed or ambiguous secure-mode witness: " + auxname)
neg("N31_auxv_over_bound", lambda c: c["kernel"].update(auxv=aux_bindings["auxv_257_pairs"]), "CHI-UNSUPPORTED", "bounds", "LP-BOUND", "Auxiliary vector exceeds 256 pairs")
neg("N32_at_secure_boolean", lambda c: c["kernel"].update(at_secure_claim=False), "CHI-PLAN", "profile_selection", "LP-CLOSED-SHAPE", "Boolean false is not integer zero")

for index, name in enumerate(("braced_origin", "origin_lib", "origin_lib_token", "origin_platform_token", "origin_unknown_token", "origin_twice", "origin_empty_entry", "origin_duplicate", "origin_literal_mix", "origin_relative", "origin_double_parent", "origin_whitespace", "origin_runpath", "origin_both"), 33):
    neg("N%02d_%s" % (index, name), lambda c: None, "CHI-UNSUPPORTED", "raw_metadata_policy", "LP-RAW-RPATH", "Unsupported exact token/search spelling: " + name, image_name=name)
for index, name in enumerate(("origin_df_origin", "origin_df1_origin", "origin_unknown_tag", "origin_duplicate_tag"), 47):
    neg("N%02d_%s" % (index, name), lambda c: None, "CHI-UNSUPPORTED", "elf_metadata", "LEGACY-ELF-GUARD", "Existing flag/tag/uniqueness refusal is retained: " + name, image_name=name)
neg("N51_expanded_mismatch", lambda c: c.update(expanded_claim=["/fixture/wrong/lib"]), "CHI-LOADER", "expanded_binding", "LP-EXPANDED", "Derived expansion and declared directory differ")
neg("N52_expanded_unbound", lambda c: c["search_directories"].clear(), "CHI-LOADER", "expanded_binding", "LP-EXPANDED", "Expanded directory has no complete bound inventory")
neg("N53_missing_needed_name", lambda c: c.update(needed_names_claim=["libalpha.so"]), "CHI-LOADER", "name_union", "LP-NAMES", "One transitive name omitted from proof")
neg("N54_extra_needed_name", lambda c: c["needed_names_claim"].append("libunknown.so"), "CHI-LOADER", "name_union", "LP-NAMES", "Extra name is not the exact union")
neg("N55_missing_variant", lambda c: c["variants"].pop(), "CHI-LOADER", "variant_inventory", "LP-VARIANTS", "Reviewed TLS alternative lacks presence/absence row")
neg("N56_wrong_variant_path", lambda c: c["variants"][1].update(path="/unrelated/x86-64-v2"), "CHI-LOADER", "variant_inventory", "LP-VARIANTS", "Variant escapes derived expansion")
neg("N57_source_variant_unknown", lambda c: c["variant_review"].update(completeness="unsupported"), "CHI-UNSUPPORTED", "variant_review", "LP-VARIANT-SEMANTICS", "Actual-loader suffix completeness has not been justified")
neg("N58_absence_changed", lambda c: c["absence_guards"]["/fixture/app/lib/tls"].update(absent=False), "CHI-LOADER", "variant_inventory", "LP-ABSENCE", "Previously absent hardware/TLS branch is now present")
for number, kind in ((59, "file"), (60, "symlink"), (61, "directory"), (62, "special")):
    def change(c, k=kind):
        c["search_directories"]["/fixture/app/lib"]["entries"]["libbeta.so"] = {"kind": k, "device": 101, "inode": 150, "mode": "0o644", "target": "/fixture/system/libbeta.so" if k == "symlink" else None}
    neg("N%02d_candidate_%s" % (number, kind), change, "CHI-LOADER", "nonselecting", "LP-CANDIDATE", "Any same-name candidate refuses, including " + kind)
neg("N63_hwcaps_candidate", lambda c: present_variant(c, "glibc-hwcaps", "x86-64-v2", "libalpha.so"), "CHI-LOADER", "nonselecting", "LP-CANDIDATE", "Hardware directory can supply a declared dependency")
neg("N64_tls_candidate", lambda c: present_variant(c, "tls", "x86_64", "libbeta.so"), "CHI-LOADER", "nonselecting", "LP-CANDIDATE", "TLS directory can supply a declared dependency")
def extension_candidate(c):
    c["closure_images"].append({"id": "extension", "needed": ["libgamma.so"], "soname": None})
    c["needed_names_claim"].append("libgamma.so")
    c["search_directories"]["/fixture/app/lib"]["entries"]["libgamma.so"] = {"kind": "file", "device": 101, "inode": 151, "mode": "0o644", "target": None}
neg("N65_extension_candidate", extension_candidate, "CHI-LOADER", "nonselecting", "LP-CANDIDATE", "Immediate Python-only name checking would miss this extension dependency")
neg("N66_needed_token", lambda c: c["closure_images"][0].update(needed=["$ORIGIN", "libbeta.so"]), "CHI-UNSUPPORTED", "name_union", "LP-NAME-TOKEN", "No token expansion in DT_NEEDED", image_name="origin_needed_token")
neg("N67_soname_token", lambda c: c["closure_images"][1].update(soname="$ORIGIN"), "CHI-UNSUPPORTED", "name_union", "LP-NAME-TOKEN", "Token-bearing SONAME refused conservatively")
neg("N68_second_token_image", lambda c: c["closure_images"][1].update(raw_rpath=["$ORIGIN/../lib"]), "CHI-UNSUPPORTED", "subject_context", "LP-ROLE", "No token admission for a second image")
neg("N69_expansion_4097_bytes", lambda c: c.update(json.loads(json.dumps(base()).replace("/fixture/app", long_parent + "b"))), "CHI-UNSUPPORTED", "bounds", "LP-BOUND", "Pre-normalization expansion exceeds 4096 bytes")
def too_many_names(c):
    names = ["libn%04d.so" % i for i in range(4097)]
    c["closure_images"] = [{"id": "n%02d" % i, "needed": names[i*256:(i+1)*256], "soname": None} for i in range(17)]
    c["needed_names_claim"] = names
neg("N70_name_union_over_bound", too_many_names, "CHI-UNSUPPORTED", "bounds", "LP-BOUND", "4097 names exceed new union ceiling; each image still has at most 256")
neg("N71_suffixes_over_bound", lambda c: c["variant_review"].update(suffixes=[""] + ["v%03d" % i for i in range(128)]), "CHI-UNSUPPORTED", "bounds", "LP-BOUND", "129 suffixes exceed ceiling")
def cross_product(c):
    names = ["libn%04d.so" % i for i in range(257)]
    c["closure_images"] = [{"id": "group1", "needed": names[:256], "soname": None}, {"id": "group2", "needed": names[256:], "soname": None}]
    c["needed_names_claim"] = names
    c["variant_review"]["suffixes"] = [""] + ["v%03d" % i for i in range(127)]
    c["variants"] = [{"suffix": s, "path": "/fixture/app/lib" + ("/" + s if s else ""), "state": "directory"} for s in c["variant_review"]["suffixes"]]
neg("N72_candidate_product_over_bound", cross_product, "CHI-UNSUPPORTED", "bounds", "LP-BOUND", "257 names times 128 present variants exceeds 32768 checks")
neg("N73_selected_machine_mismatch", lambda c: None, "CHI-UNSUPPORTED", "subject_context", "LP-SUBJECT-MACHINE", "Selected new profile is for x86-64 Python; old AArch64 literal behavior remains separate", image_name="origin_aarch64")

def drift_candidate(c):
    c["approved_before"] = deepcopy(c["search_directories"])
    c["phase"] = "recheck"
    c["search_directories"]["/fixture/app/lib"]["entries"]["libalpha.so"] = {"kind": "file", "device": 101, "inode": 199, "mode": "0o644", "target": None}
neg("D01_postapproval_new_candidate", drift_candidate, "CHI-DRIFT", "recheck", "LP-RECHECK", "Postapproval directory growth cannot reuse cached nonselection", route="recheck_rule", cause="CHI-LOADER")
def drift_origin(c):
    c["approved_before"] = deepcopy(c["guards"])
    c["phase"] = "recheck"; c["guards"][3]["inode"] = 999
neg("D02_origin_inode_changed", drift_origin, "CHI-DRIFT", "recheck", "LP-RECHECK", "Origin directory identity drift invalidates expansion", route="recheck_rule", cause="CHI-PATH")
def drift_kernel(c):
    c["approved_before"] = deepcopy(c["kernel"])
    c["phase"] = "recheck"; c["kernel"]["proc_exe_path"] = "/other/bin/python"
neg("D03_kernel_origin_changed", drift_kernel, "CHI-DRIFT", "recheck", "LP-RECHECK", "Current process origin witness must be reread", route="recheck_rule", cause="CHI-INSPECTOR")
for number, stage in ((1, "before_variant_read"), (2, "during_candidate_scan"), (3, "before_final_identity")):
    c = base(); c["fault"] = {"kind": "check_callback_exception", "at": stage, "exception_identity": "SENTINEL-P11-DEADLINE"}
    add("F%02d_%s" % (number, stage), "fault_contract", "python_origin", c,
        {"outcome": "propagated_callback", "stage": stage, "exception_identity": "SENTINEL-P11-DEADLINE", "target_starts": 0, "host_qualified": False},
        "No new helper swallows callback/deadline failures", "Future source-bound injection; not executed in P11")

document(ROOT / "EXPECTATIONS.json", {"schema": "ontokin.c271.p11-independent-expectations/1", "author": "/root/loader_design",
    "derived_from_production_output": False, "production_parser_calls": 0, "cases": expectations})
document(ROOT / "CONSTRUCTION.json", {"schema": "ontokin.c271.p11-inert-construction/1", "elf_layouts": layouts,
    "auxiliary_vectors": {name: {"binding": aux_bindings[name], "pairs": pairs} for name, pairs in aux_specs.items()},
    "truncated_auxiliary_vector": aux_bindings["auxv_truncated"],
    "constructor": {"path": "../build_controls.py", "sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
    "execution": {"product_imports": 0, "product_parser_calls": 0, "target_executions": 0, "actual_special_files": 0},
    "note": "Fixed-layout independent byte construction. No expected outcome is obtained from production code or an implemented acceptance predicate."})
fixture_files = []
for path in sorted(INPUTS.iterdir()):
    raw = path.read_bytes()
    fixture_files.append({"path": str(path.relative_to(ROOT)), "size_bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "mode": oct(path.stat().st_mode & 0o777)})
document(ROOT / "FIXTURE-MANIFEST.json", {"schema": "ontokin.c271.p11-control-freeze/1", "status": "frozen_before_future_implementation",
    "author": "/root/loader_design", "operational": False, "cases": cases, "files": fixture_files,
    "all_expected_target_starts": 0, "actual_product_execution": "not_run", "synthetic_positive_scope": "private rule only; never operational selected-image admission"})
print(json.dumps({"created_cases": len(cases), "created_images": len(layouts), "created_fixture_files": len(fixture_files), "product_parser_calls": 0, "target_executions": 0}, sort_keys=True))
