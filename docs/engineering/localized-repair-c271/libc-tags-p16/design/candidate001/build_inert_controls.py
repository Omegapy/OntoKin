"""Construct frozen synthetic data and literal expectations; never run a parser.

This is an evidence constructor, not a production/test adapter or policy model.
Run only into an absent output directory. It imports standard-library modules.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import os
import struct
import sys

TRIO = [(0x70000000, 0x28000), (0x70000001, 0x3D0), (0x70000003, 0x10)]
PLAN = "ontokin.current-host-readback-inspection-plan/0.1.2"
PROFILE = "linux-glibc-declared-python-origin-rpath-libc-plt-v1"
POLICY = "ontokin.current-host-readback-libc-plt/0.1.0"
LIBC = {"sha256": "9792e3cbb541c8f44c7acf5f14f4022ea62998ecc787d326bed4d8b6547dfd92", "size_bytes": 1995216, "mode": "0o755"}
LOADER = {"sha256": "c8438e4fde1934e61c88311633f00949ff645d5c04cdb8671fa3d78164d2f307", "size_bytes": 225672, "mode": "0o755"}
PYTHON = {"sha256": "fa67443527ed9647f760d807e2a38f26340757123e643c4639cf273ed15d5ea7", "size_bytes": 30894944, "mode": "0o755"}
LIBC_PATH = "/synthetic/system/lib/libc.so.6"
LOADER_PATH = "/synthetic/system/lib/ld-linux-x86-64.so.2"
PYTHON_PATH = "/synthetic/python/bin/python3.12"
LIBC_NAME = "/synthetic/aliases/libc.so.6"
LOADER_NAME = "/synthetic/aliases/ld-linux-x86-64.so.2"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False) + "\n").encode()


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)
    path.chmod(0o600)


def metadata(machine=62):
    # Literal independent result specification, not a decoded parser result.
    return {"class": 64, "endian": "little", "machine": machine, "type": 3,
            "interpreter": None, "needed": ["ld-linux-x86-64.so.2"], "soname": "libc.so.6", "rpath": [], "runpath": []}


def accepted(machine=62):
    return {"outcome": "metadata_returned", "metadata": metadata(machine), "opened_descriptor_close_count": 1,
            "tag_value_dereferences": 0, "tag_value_allocations": 0}


def refusal(code, reason, stage=None, rule=None, cause=None):
    return {"outcome": "typed_refusal", "code": code, "reason": reason, "state": "REJECTED",
            "details": {} if stage is None else {"stage": stage, "rule_id": rule}, "cause": cause}


UNKNOWN = refusal("CHI-UNSUPPORTED", "Unreviewed ELF dynamic loader feature")
FLAGS = refusal("CHI-UNSUPPORTED", "Unsupported dynamic flags")
ARCH = refusal("CHI-UNSUPPORTED", "Libc PLT metadata requires x86-64 ET_DYN", "libc_plt_tags", "PLT-ARCH")
COUNT = refusal("CHI-UNSUPPORTED", "Libc PLT metadata requires one complete tag trio", "libc_plt_tags", "PLT-TRIO")
PAIR = refusal("CHI-PLAN", "Unsupported libc PLT schema/profile pair", "profile_selection", "PLT-PROFILE")
SHAPE = refusal("CHI-PLAN", "Invalid libc PLT policy shape", "profile_selection", "PLT-SHAPE")
ROLE = refusal("CHI-INSPECTOR", "Selected libc is not the bound author-Python dependency", "libc_plt_binding", "PLT-ROLE")
DESCRIPTORS = refusal("CHI-INSPECTOR", "Libc PLT descriptors or aliases disagree", "libc_plt_binding", "PLT-DESCRIPTORS")
PIN = refusal("CHI-INSPECTOR", "Libc PLT input is not the selected libc/loader pair", "libc_plt_binding", "PLT-PIN")


def construct_elf(*, trio=TRIO, machine=62, elf_type=3, flags=(8,), flags1=(1,), extra=(),
                  needed=("ld-linux-x86-64.so.2",), rpath=None, runpath=None,
                  string_address=1536, terminated=True, program_count=2, duplicate_soname=False):
    strings = bytearray(b"\0")

    def text(value):
        offset = len(strings)
        strings.extend(value.encode("ascii") + b"\0")
        return offset

    entries = [(1, text(name)) for name in needed]
    soname = text("libc.so.6")
    entries.append((14, soname))
    if duplicate_soname:
        entries.append((14, soname))
    if rpath is not None:
        entries.append((15, text(rpath)))
    if runpath is not None:
        entries.append((29, text(runpath)))
    entries += [(5, string_address), (10, len(strings))]
    entries += [(30, value) for value in flags]
    entries += [(0x6FFFFFFB, value) for value in flags1]
    entries += list(trio) + list(extra)
    if terminated:
        entries.append((0, 0))
    raw = bytearray(2048)
    ident = b"\x7fELF\x02\x01\x01\x00" + bytes(8)
    struct.pack_into("<16sHHIQQQIHHHHHH", raw, 0, ident, elf_type, machine, 1, 0, 64, 0, 0, 64, 56, program_count, 0, 0, 0)
    struct.pack_into("<IIQQQQQQ", raw, 64, 1, 5, 0, 0, 0, 2048, 2048, 4096)
    struct.pack_into("<IIQQQQQQ", raw, 120, 2, 6, 512, 512, 512, len(entries) * 16, len(entries) * 16, 8)
    for index, (tag, value) in enumerate(entries):
        struct.pack_into("<qQ", raw, 512 + 16 * index, tag, value)
    raw[1536:1536 + len(strings)] = strings
    construction = {"file_bytes": 2048, "header": {"elf_type": elf_type, "machine": machine, "program_offset": 64,
                    "program_entry_bytes": 56, "program_count": program_count},
                    "program_headers": [[1, 5, 0, 0, 0, 2048, 2048, 4096], [2, 6, 512, 512, 512, len(entries) * 16, len(entries) * 16, 8]],
                    "dynamic_offset": 512, "dynamic_size": len(entries) * 16,
                    "dynamic_entries": [[tag, value] for tag, value in entries],
                    "stored_string_offset": 1536, "stored_string_hex": strings.hex(),
                    "declared_string_address": string_address,
                    "ordinary_success_read_ranges": [[0, 64], [64, 112], [512, len(entries) * 16], [1536, len(strings)]],
                    "intentionally_synthetic": True, "executable_correctness_claim": False}
    return bytes(raw), construction


def profile_context():
    return {"schema": "ontokin.c271.p16-profile-context/1", "operational": False,
            "plan_schema": PLAN, "profile": PROFILE,
            "libc_plt": {"schema": POLICY, "subject": {"path": LIBC_PATH, **LIBC}, "loader": {"path": LOADER_PATH, **LOADER}}}


def binding_context():
    aliases = {LIBC_NAME: {"resolved_path": LIBC_PATH, "symlink": True, "link_target": LIBC_PATH},
               LOADER_NAME: {"resolved_path": LOADER_PATH, "symlink": True, "link_target": LOADER_PATH}}
    files = {LIBC_PATH: LIBC, LOADER_PATH: LOADER, PYTHON_PATH: PYTHON}
    return {"schema": "ontokin.c271.p16-binding-context/1", "operational": False, "observations": "mocked_boundary_only",
            "subject": {"path": LIBC_PATH, **LIBC}, "loader": {"path": LOADER_PATH, **LOADER},
            "python_descriptor": {"path": PYTHON_PATH, **PYTHON},
            "actual_python_needed": ["libc.so.6"], "actual_python_interpreter": LOADER_NAME,
            "python_resolved_needed": {"libc.so.6": LIBC_NAME}, "runtime_interpreter": LOADER_NAME,
            "dependency_role_names": [LIBC_NAME],
            "forbidden_resolved_paths": [PYTHON_PATH, "/synthetic/node", "/synthetic/git", "/synthetic/shell", LOADER_PATH],
            "host_aliases": copy.deepcopy(aliases), "runtime_aliases": copy.deepcopy(aliases),
            "host_files": copy.deepcopy(files), "runtime_files": copy.deepcopy(files),
            "libc_image_descriptor": {"path": LIBC_PATH, **LIBC}, "loader_image_descriptor": {"path": LOADER_PATH, **LOADER}}


def coherent_pin_change(context, subject, binding):
    key, path, row = ("subject", LIBC_PATH, "libc_image_descriptor") if subject else ("loader", LOADER_PATH, "loader_image_descriptor")
    context[key] = {"path": path, **binding}
    context[row] = {"path": path, **binding}
    context["host_files"][path] = copy.deepcopy(binding)
    context["runtime_files"][path] = copy.deepcopy(binding)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    cases, expected, construction, fixtures = [], {}, {}, []

    def add(identifier, route, expectation, mutation, *, context=None, elf=None, fault=None):
        assert identifier not in expected
        current = copy.deepcopy(context) if context is not None else {"schema": "ontokin.c271.p16-metadata-context/1", "operational": False}
        current["case_id"] = identifier
        current["route"] = route
        current["mutation"] = mutation
        if elf is not None:
            data, layout = construct_elf(**elf)
            rel = "elf/" + identifier + ".bin"
            write(output / rel, data)
            binding = {"path": rel, "sha256": sha(data), "size_bytes": len(data), "mode": "0o600"}
            current["image"] = binding
            current["require_interpreter"] = False
            construction[rel] = layout
            fixtures.append(binding)
        if fault is not None:
            current["fault"] = copy.deepcopy(fault)
        current["operational_approval"] = "none; this is a nonoperational control context"
        current["actual_fixture_bytes"] = synthetic_binding
        rel = "fixture_inputs/" + identifier + ".json"
        raw = canonical(current)
        write(output / rel, raw)
        fixtures.append({"path": rel, "sha256": sha(raw), "size_bytes": len(raw), "mode": "0o600"})
        result = copy.deepcopy(expectation)
        result.update({"current_execution": "not_run", "operational_plan_accepted": False, "host_qualified": False,
                       "expected_node_starts": 0, "expected_ldd_starts": 0, "expected_direct_loader_starts": 0})
        if elf is not None:
            result.setdefault("opened_descriptor_close_count", 1)
        else:
            result.setdefault("opened_descriptor_close_count", 0)
        expected[identifier] = result
        cases.append({"id": identifier, "route": route, "input": rel, "expectation": identifier, "mutation": mutation})

    synthetic, _ = construct_elf()
    synthetic_binding = {"sha256": sha(synthetic), "size_bytes": len(synthetic), "mode": "0o600"}

    add("L01_public_trio_refuses", "legacy_public_metadata", UNKNOWN, "Exact trio on unchanged public route", elf={})
    add("L02_old_literal_plan_refuses", "legacy_literal_plan_reader", UNKNOWN, "Old literal plan reader has no new policy", elf={})
    add("L03_old_origin_plan_refuses", "legacy_origin_plan_reader", UNKNOWN, "Old origin policy subject is Python, not this image", elf={},
        context={"schema": "ontokin.c271.p16-legacy-reader-context/1", "operational": False, "origin_subject_path": PYTHON_PATH})
    add("L04_public_tagless_x86", "legacy_public_metadata", accepted(), "Remove the entire trio on old public route", elf={"trio": []})
    add("L05_public_tagless_aarch64", "legacy_public_metadata", accepted(183), "Old supported AArch64 metadata without processor tags", elf={"trio": [], "machine": 183})

    add("P01_opaque_p15_values", "libc_plt_metadata", accepted(), "P15 tuple as opaque values; synthetic PLT address exceeds file size", elf={})
    add("P02_opaque_zero_values", "libc_plt_metadata", accepted(), "All three opaque values are zero", elf={"trio": [(t, 0) for t, _ in TRIO]})
    add("P03_opaque_u64_max_values", "libc_plt_metadata", accepted(), "All three opaque values are 2^64-1", elf={"trio": [(t, 2**64 - 1) for t, _ in TRIO]})
    add("P04_opaque_inconsistent_values", "libc_plt_metadata", accepted(), "Address 5, byte size 3, entry size 7 are not validated as executable PLT", elf={"trio": [(TRIO[0][0], 5), (TRIO[1][0], 3), (TRIO[2][0], 7)]})
    add("P05_original_flag_masks", "libc_plt_metadata", accepted(), "Every permitted inherited flag bit remains permitted at the primitive", elf={"flags1": (0x08000001,)})
    add("P06_absent_flags", "libc_plt_metadata", accepted(), "Absent optional flag entries remain permitted", elf={"flags": (), "flags1": ()})
    add("P07_reordered_trio", "libc_plt_metadata", accepted(), "Reverse only the three tag entries", elf={"trio": list(reversed(TRIO))})

    add("N01_aarch64_collision", "libc_plt_metadata", ARCH, "Only machine changes to 183; processor numbers collide", elf={"machine": 183})
    add("N02_et_exec", "libc_plt_metadata", ARCH, "Only ELF type changes to ET_EXEC", elf={"elf_type": 2})
    add("N03_reserved_processor_hole", "libc_plt_metadata", UNKNOWN, "Append only 0x70000002; no processor-range allowance", elf={"extra": [(0x70000002, 0)]})
    add("N04_other_processor_tag", "libc_plt_metadata", UNKNOWN, "Append only 0x70000004", elf={"extra": [(0x70000004, 0)]})
    add("N05_unknown_os_tag", "libc_plt_metadata", UNKNOWN, "Append only unsupported OS-range 0x6ffffefc", elf={"extra": [(0x6FFFFEFC, 1)]})
    add("N06_missing_plt", "libc_plt_metadata", COUNT, "Remove only DT_X86_64_PLT", elf={"trio": TRIO[1:]})
    add("N07_missing_pltsz", "libc_plt_metadata", COUNT, "Remove only DT_X86_64_PLTSZ", elf={"trio": [TRIO[0], TRIO[2]]})
    add("N08_missing_pltent", "libc_plt_metadata", COUNT, "Remove only DT_X86_64_PLTENT", elf={"trio": TRIO[:2]})
    add("N09_absent_trio", "libc_plt_metadata", COUNT, "No trio on the subject-only private primitive", elf={"trio": []})
    add("N10_duplicate_plt_equal", "libc_plt_metadata", COUNT, "Append equal PLT duplicate", elf={"trio": TRIO + [TRIO[0]]})
    add("N11_duplicate_pltsz_equal", "libc_plt_metadata", COUNT, "Append equal PLTSZ duplicate", elf={"trio": TRIO + [TRIO[1]]})
    add("N12_duplicate_pltent_equal", "libc_plt_metadata", COUNT, "Append equal PLTENT duplicate", elf={"trio": TRIO + [TRIO[2]]})
    add("N13_duplicate_plt_unequal", "libc_plt_metadata", COUNT, "Append unequal PLT duplicate", elf={"trio": TRIO + [(TRIO[0][0], 1)]})
    add("N14_unknown_before_missing", "libc_plt_metadata", UNKNOWN, "Unknown tag with incomplete trio freezes precedence", elf={"trio": TRIO[1:], "extra": [(0x70000002, 0)]})
    add("N15_arch_before_unknown", "libc_plt_metadata", ARCH, "Architecture collision with unknown tag freezes precedence", elf={"machine": 183, "extra": [(0x70000002, 0)]})
    add("N16_flags_0x18_preserved", "libc_plt_metadata", FLAGS, "Only DT_FLAGS changes to retained raw 0x18; synthetic later-boundary control", elf={"flags": (0x18,)})
    add("N17_flags1_origin_preserved", "libc_plt_metadata", FLAGS, "Only DT_FLAGS_1 changes to forbidden bit 0x80", elf={"flags1": (0x80,)})
    add("N18_duplicate_flags", "libc_plt_metadata", FLAGS, "Two otherwise permitted DT_FLAGS entries", elf={"flags": (8, 8)})
    add("N19_duplicate_flags1", "libc_plt_metadata", FLAGS, "Two otherwise permitted DT_FLAGS_1 entries", elf={"flags1": (1, 1)})
    add("N20_unmapped_string_table", "libc_plt_metadata", refusal("CHI-UNSUPPORTED", "Ambiguous/unmapped ELF string table"), "Only declared string address is outside mapped data", elf={"string_address": 4096})
    add("N21_duplicate_needed", "libc_plt_metadata", refusal("CHI-UNSUPPORTED", "Duplicate or unsupported DT_NEEDED name"), "Duplicate the one needed name", elf={"needed": ("ld-linux-x86-64.so.2", "ld-linux-x86-64.so.2")})
    add("N22_slash_needed", "libc_plt_metadata", refusal("CHI-UNSUPPORTED", "Duplicate or unsupported DT_NEEDED name"), "Needed name contains slash", elf={"needed": ("dir/ld-linux-x86-64.so.2",)})
    add("N23_libc_origin_token", "libc_plt_metadata", refusal("CHI-UNSUPPORTED", "Unreviewed loader token expansion"), "Libc still receives no Python-origin token permission", elf={"rpath": "$ORIGIN/../lib"})
    add("N24_both_search_paths", "libc_plt_metadata", refusal("CHI-UNSUPPORTED", "Conflicting legacy and modern search paths"), "Literal RPATH and RUNPATH coexist", elf={"rpath": "/literal/a", "runpath": "/literal/b"})
    add("N25_program_table_invalid", "libc_plt_metadata", refusal("CHI-UNSUPPORTED", "Unsupported ELF program table"), "Only e_phnum is zero; structural guard precedes tags", elf={"program_count": 0})
    add("N26_dynamic_unterminated", "libc_plt_metadata", refusal("CHI-UNSUPPORTED", "Unterminated dynamic table"), "Dynamic segment ends without DT_NULL", elf={"terminated": False})
    add("N27_duplicate_soname", "libc_plt_metadata", refusal("CHI-UNSUPPORTED", "Duplicate/missing dynamic metadata"), "Duplicate SONAME reaches unchanged later singleton guard", elf={"duplicate_soname": True})

    add("S01_new_pair_and_shape", "new_profile_rule", {"outcome": "new_branch_selected_only"}, "Exact new pair and closed object", context=profile_context())
    c = profile_context(); c["profile"] = "linux-glibc-declared-python-origin-rpath-v1"
    add("S02_new_schema_old_profile", "new_profile_rule", PAIR, "New schema with old profile at new selector seam", context=c)
    c = profile_context(); c["plan_schema"] = "ontokin.current-host-readback-inspection-plan/0.1.1"
    add("S03_old_schema_new_profile", "new_profile_rule", PAIR, "Old schema with new profile at new selector seam", context=c)
    c = profile_context(); c["plan_schema"] = "ontokin.current-host-readback-inspection-plan/0.1.3"
    add("S04_unknown_schema", "new_profile_rule", PAIR, "Unknown schema at new selector seam; not full plan error ordering", context=c)
    c = profile_context(); del c["libc_plt"]
    add("S05_missing_policy", "new_profile_rule", SHAPE, "Missing new object", context=c)
    c = profile_context(); c["libc_plt"]["approved"] = True
    add("S06_unknown_approval_key", "new_profile_rule", SHAPE, "Unrecognized object member confers no authority", context=c)
    c = profile_context(); c["libc_plt"]["schema"] = "ontokin.current-host-readback-libc-plt/9"
    add("S07_unknown_object_schema", "new_profile_rule", SHAPE, "Only object schema differs", context=c)
    c = profile_context(); c["libc_plt"]["subject"]["size_bytes"] = True
    add("S08_descriptor_boolean_size", "new_profile_rule", SHAPE, "Boolean is not an integer byte count", context=c)

    add("B01_mocked_relations", "binding_relations", {"outcome": "mocked_binding_relations_accepted_only", "actual_file_binding_proved": False}, "Logical exact relation without real file observation", context=binding_context())
    c = binding_context(); c["actual_python_needed"] = []
    add("B02_not_python_needed", "binding_relations", ROLE, "Actual Python metadata lacks libc needed name", context=c)
    c = binding_context(); c["python_resolved_needed"] = {}
    add("B03_missing_selected_edge", "binding_relations", ROLE, "Selected needed edge is absent", context=c)
    c = binding_context(); c["subject"]["path"] = "/synthetic/unselected/libc.so.6"; c["libc_image_descriptor"]["path"] = c["subject"]["path"]
    c["host_files"][c["subject"]["path"]] = copy.deepcopy(LIBC); c["runtime_files"][c["subject"]["path"]] = copy.deepcopy(LIBC)
    add("B04_unselected_same_hash_row", "binding_relations", ROLE, "Same-hash unused image does not match the selected edge", context=c)
    c = binding_context(); c["dependency_role_names"] = []
    add("B05_missing_dependency_role", "binding_relations", ROLE, "Mapped name has no inspector/shared dependency role", context=c)
    c = binding_context(); c["runtime_aliases"][LIBC_NAME]["link_target"] = "/synthetic/different-target"
    add("B06_alias_records_disagree", "binding_relations", DESCRIPTORS, "Only full runtime alias record changes", context=c)
    c = binding_context(); c["host_files"][LIBC_PATH]["sha256"] = "0" * 64
    add("B07_host_file_disagrees", "binding_relations", DESCRIPTORS, "Only host file binding changes", context=c)
    c = binding_context(); c["libc_image_descriptor"]["size_bytes"] += 1
    add("B08_libc_image_row_disagrees", "binding_relations", DESCRIPTORS, "Only libc image row descriptor changes", context=c)
    c = binding_context(); c["actual_python_interpreter"] = "/synthetic/another-loader"
    add("B09_interpreter_relation_differs", "binding_relations", ROLE, "Actual selected Python interpreter differs", context=c)
    c = binding_context(); c["loader_image_descriptor"]["size_bytes"] += 1
    add("B10_loader_image_row_disagrees", "binding_relations", DESCRIPTORS, "Only loader image row descriptor changes", context=c)
    c = binding_context(); coherent_pin_change(c, True, {**LIBC, "sha256": "0" * 64})
    add("B11_coherent_wrong_libc_pin", "binding_relations", PIN, "Every logical subject binding agrees on an unselected hash", context=c)
    c = binding_context(); coherent_pin_change(c, False, {**LOADER, "sha256": "0" * 64})
    add("B12_coherent_wrong_loader_pin", "binding_relations", PIN, "Every logical loader binding agrees on an unselected hash", context=c)
    c = binding_context(); c["forbidden_resolved_paths"].append(LIBC_PATH)
    add("B13_forbidden_extension_role", "binding_relations", ROLE, "Selected path is also an author extension role", context=c)
    c = binding_context(); coherent_pin_change(c, True, {**LIBC, "mode": "0o644"})
    add("B14_coherent_wrong_libc_mode", "binding_relations", PIN, "Every logical subject binding agrees on nonoperational mode", context=c)
    c = binding_context(); coherent_pin_change(c, True, synthetic_binding)
    add("B15_synthetic_cannot_meet_real_pin", "binding_relations", PIN, "Coherent synthetic file descriptors still differ from fixed operational pin", context=c)
    add("B16_external_digest_mismatch", "external_digest",
        refusal("CHI-PLAN", "Plan differs from independently supplied expected digest", "plan_authentication", "LP-EXTERNAL-DIGEST"),
        "Existing external comparator remains separate from observed digest",
        context={"schema": "ontokin.c271.p16-digest-context/1", "operational": False, "actual_digest": "a" * 64, "expected_digest": "b" * 64})

    for identifier, key, name in (("D01_subject_binding_drift", LIBC_PATH, "libc"), ("D02_loader_binding_drift", LOADER_PATH, "loader")):
        before = binding_context(); after = copy.deepcopy(before); after["host_files"][key]["sha256"] = "0" * 64
        result = refusal("CHI-DRIFT", "An admitted input changed before/after the command", "recheck", "LP-RECHECK", cause=DESCRIPTORS)
        add(identifier, "recheck_boundary", result, "Fresh " + name + " binding mismatch must reach the existing drift wrapper",
            context={"schema": "ontokin.c271.p16-recheck-context/1", "operational": False, "before": before, "after": after,
                     "require_actual_new_binding_primitive_call": True, "raw_libc_parser_calls_after_fault": 0})

    runtime_sentinel = {"outcome": "callback_exception", "exception_type": "SentinelRuntimeError", "message": "p16 callback sentinel",
                        "same_exception_object": True, "opened_descriptor_close_count": 1}
    add("F01_callback_before_header_read", "metadata_fault", runtime_sentinel, "Raise sentinel at existing first read callback after open", elf={},
        fault={"kind": "callback", "at": "before_header_pread", "exception": "SentinelRuntimeError"})
    add("F02_callback_before_tag_policy", "metadata_fault", runtime_sentinel, "Raise sentinel at new policy entry checkpoint", elf={},
        fault={"kind": "callback", "at": "before_libc_plt_tag_policy", "exception": "SentinelRuntimeError"})
    add("F03_callback_during_tag_scan", "metadata_fault", {"outcome": "callback_exception", "exception_type": "HostInspectionError",
        "same_exception_object": True, "original_details_unchanged": {"sentinel": "p16-preserve"}, "opened_descriptor_close_count": 1},
        "Raise preconstructed HostInspectionError during actual new scan; preserve object and details", elf={},
        fault={"kind": "callback", "at": "during_libc_plt_tag_scan", "exception": "HostInspectionError", "category": "CALLBACK",
               "reason": "p16 callback sentinel", "details": {"sentinel": "p16-preserve"}})
    add("F04_callback_before_final_identity", "metadata_fault", runtime_sentinel, "Raise sentinel just before final identity check", elf={},
        fault={"kind": "callback", "at": "before_final_elf_identity", "exception": "SentinelRuntimeError"})
    add("F05_short_dynamic_read", "metadata_fault", refusal("CHI-UNSUPPORTED", "Truncated ELF range"), "Only dynamic-table pread returns one fewer byte", elf={},
        fault={"kind": "pread_short", "offset": 512, "remove_last_bytes": 1})
    add("F06_final_descriptor_identity", "metadata_fault", refusal("CHI-LOADER", "ELF changed during inspection"), "Change only final fstat inode observation", elf={},
        fault={"kind": "identity_observation", "at": "final_fstat", "field": "st_ino", "delta": 1})
    add("F07_final_named_path_identity", "metadata_fault", refusal("CHI-LOADER", "ELF changed during inspection"), "Change only final lstat inode observation", elf={},
        fault={"kind": "identity_observation", "at": "final_lstat", "field": "st_ino", "delta": 1})
    add("F08_dynamic_read_oserror", "metadata_fault", refusal("CHI-UNSUPPORTED", "Cannot parse bounded ELF metadata", cause={"type": "OSError", "message": "p16 pread sentinel", "same_exception_object": True}),
        "Only dynamic-table pread raises the bound OSError; inherited wrapper retains cause", elf={},
        fault={"kind": "pread_exception", "offset": 512, "exception": "OSError", "message": "p16 pread sentinel"})

    for name, value in (
        ("CONTROLS.json", {"schema": "ontokin.c271.libc-plt-controls/1", "status": "frozen_inert_obligations_not_executed", "cases": cases}),
        ("EXPECTATIONS.json", {"schema": "ontokin.c271.libc-plt-expectations/1", "independent_literal_oracles": True, "cases": expected}),
        ("CONSTRUCTION.json", {"schema": "ontokin.c271.libc-plt-construction/1", "method": "Fixed struct writes, no production imports or acceptance-predicate implementation", "images": construction}),
        ("FIXTURE-MANIFEST.json", {"schema": "ontokin.c271.libc-plt-fixture-manifest/1", "files": sorted(fixtures, key=lambda row: row["path"])}),
        ("AUTHOR-CONSTRUCTION-RECEIPT.json", {"schema": "ontokin.c271.p16-author-construction/1", "command": [sys.executable, "-I", "-B", str(Path(__file__).resolve()), *sys.argv[1:]],
            "script_sha256": sha(Path(__file__).read_bytes()), "python_version": sys.version, "platform": sys.platform,
            "case_count": len(cases), "elf_count": len(construction), "fixture_count": len(fixtures),
            "product_imported": False, "product_parser_called": False, "target_started": False, "current_host_input_read": False}),
    ):
        write(output / name, json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False).encode() + b"\n")
    print(json.dumps({"output": str(output), "cases": len(cases), "elf_images": len(construction), "fixtures": len(fixtures),
                      "expectations_sha256": sha((output / "EXPECTATIONS.json").read_bytes())}))


if __name__ == "__main__":
    main()
