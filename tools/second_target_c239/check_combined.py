#!/usr/bin/env python3
"""Run the finite existing CPU checks on one verified private observation copy."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys
import tempfile

sys.dont_write_bytecode = True
REPOSITORY = Path(__file__).absolute().parents[2]
VERSION = "C239/0.1.0"
REPORT_SCHEMA = "ontokin.c239.combined-comparison/0.1"
INHERITED_REVISION = "f53c44ed6ef660c1a1ebc17af43e66e37b06d9fa"
CONTRACT_PATH = "docs/engineering/second-target-c239/CONTRACT.md"
CONTRACT_SHA256 = "55f5faf99f47a6fc70472af4cc4d87c9184bc868b6b5de23e516820aec0ed933"
CHECKER_PINS = {
    "C221": ("tools/second_target_c221/check_bindings.py", 31854, "fff5569d31b3cd900385ac4b955dc5b30c8ee440ef16d8851b5a0ffb5d03aa4b"),
    "C222": ("tools/second_target_c222/check_observations.py", 18786, "1eab170204d8f02b5d281f7e67d7f649040a1c525884fcc17eadfed6c765b6b9"),
    "C234": ("tools/second_target_c234/check_materials.py", 20025, "e68d212d4b5490c9e17466fb1a858a69a6d0764b0019cb4df265902bf0cabb13"),
    "C235": ("tools/second_target_c235/check_normals.py", 20057, "15acd1e95b47a9f6f6eee6c3c28875883d3722b5071ec37a14b7c720a9e8773c"),
    "C236": ("tools/second_target_c236/check_poses.py", 27129, "51864445f638a36ef5a93fd4bd58c07a416d342ce6e371a894f52f3af06bf584"),
    "C237": ("tools/second_target_c237/check_semantics.py", 20819, "c5127c265eb247ebeb1e7625e57179fb839ba932967c48ed071d5b60afb3a0c0"),
    "C238": ("tools/second_target_c238/check_envelope.py", 40475, "76c87096d810236b58ac47a13ad58ab9eec558500104c6c96acf89f462deea83"),
}
COMPONENTS = ("C222", "C234", "C235", "C236", "C237")
ROLES = ("geometry", "materials", "normals", "poses", "semantics", "corner_map")
PASS_RESULTS = {"C222": "PASS_CPU_CORRESPONDENCE", "C234": "PASS_CPU_MATERIALS", "C235": "PASS_CPU_NORMALS",
                "C236": "PASS_CPU_POSES", "C237": "PASS_CPU_SEMANTIC_RETENTION"}
STAT_FIELDS = ("st_dev", "st_ino", "st_mode", "st_size", "st_mtime_ns", "st_ctime_ns")
_MODULES = None


class Refusal(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def _require(condition, code, message):
    if not condition:
        raise Refusal(code, message)


def _binding(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def _stat_key(value):
    return tuple(getattr(value, key) for key in STAT_FIELDS)


def _open_root(path):
    _require(hasattr(os, "O_NOFOLLOW") and hasattr(os, "O_DIRECTORY") and hasattr(os, "pread") and
             os.open in os.supports_dir_fd, "PLATFORM", "Required POSIX descriptor operations are unavailable")
    supplied = os.fspath(path)
    _require(type(supplied) is str and supplied and "\x00" not in supplied and ".." not in supplied.split("/"),
             "PATH", "Invalid safe directory path")
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in Path(os.path.abspath(supplied)).parts[1:]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        return fd
    except BaseException:
        os.close(fd)
        raise


def _parent_fd(root_fd, path):
    parts = path.split("/")
    _require(parts and all(part and part not in (".", "..") and "\\" not in part and "\x00" not in part for part in parts),
             "PATH", "Invalid relative snapshot path")
    fd = os.dup(root_fd)
    try:
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        return fd, parts[-1]
    except BaseException:
        os.close(fd)
        raise


def _read_at(root_fd, path, ceiling):
    parent, name = _parent_fd(root_fd, path)
    fd = None
    try:
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        before = os.fstat(fd)
        _require(stat.S_ISREG(before.st_mode) and 0 < before.st_size <= ceiling,
                 "FILE", path + ": bounded regular file required")
        chunks, offset = [], 0
        while offset <= before.st_size:
            chunk = os.pread(fd, min(1024 * 1024, before.st_size + 1 - offset), offset)
            if not chunk:
                break
            chunks.append(chunk)
            offset += len(chunk)
        raw = b"".join(chunks)
        after = os.fstat(fd)
        named = os.stat(name, dir_fd=parent, follow_symlinks=False)
        _require(_stat_key(before) == _stat_key(after) == _stat_key(named) and len(raw) == before.st_size,
                 "CHANGED", path + ": input changed while reading")
        return raw, before
    finally:
        if fd is not None:
            os.close(fd)
        os.close(parent)


def _read_local(path, ceiling=128 * 1024):
    absolute = Path(path).absolute()
    fd = _open_root(absolute.parent)
    try:
        return _read_at(fd, absolute.name, ceiling)
    finally:
        os.close(fd)


try:
    _SELF_RAW, _SELF_STAT = _read_local(__file__)
    _SELF_BINDING = _binding(_SELF_RAW)
    _SELF_ERROR = None
except (OSError, Refusal) as _initial_error:
    _SELF_BINDING = None
    _SELF_ERROR = str(_initial_error)


def _source_guard(modules=None):
    _require(_SELF_BINDING is not None, "SOURCE", "C239 source could not be bound at loading: " + str(_SELF_ERROR))
    raw, info = _read_local(__file__)
    _require(_binding(raw) == _SELF_BINDING and stat.S_IMODE(info.st_mode) == 0o644,
             "SOURCE_CHANGED", "C239 source differs from its loaded source binding")
    rows, sources = [], {}
    for tag, (relative, size, sha256) in CHECKER_PINS.items():
        path = REPOSITORY / relative
        raw, info = _read_local(path)
        _require(len(raw) == size and _binding(raw)["sha256"] == sha256 and stat.S_IMODE(info.st_mode) == 0o644,
                 "SOURCE_PIN", tag + ": inherited implementation differs from the predeclared source")
        _require(not os.path.lexists(path.with_suffix(".pyc")) and
                 not os.path.lexists(path.parent / "__pycache__"),
                 "SOURCE_CACHE", tag + ": preexisting bytecode cache is not an inspected source")
        sources[tag] = raw
        rows.append({"component": tag, "path": relative, "bytes": size, "sha256": sha256, "mode": 0o644})
    contract, info = _read_local(REPOSITORY / CONTRACT_PATH)
    _require(_binding(contract)["sha256"] == CONTRACT_SHA256 and stat.S_IMODE(info.st_mode) == 0o644,
             "CONTRACT_CHANGED", "The predeclared C239 contract differs")
    origins = [] if modules is None else _module_origins(modules)
    authority_documents = []
    if modules is not None:
        c221 = modules["C221"]
        with c221.SafeRoot(REPOSITORY) as root:
            for name, (size, sha256, mode) in c221.AUTHORITY_PINS.items():
                path = c221.AUTHORITY_DIRECTORY + "/" + name
                root.read(path, size, sha256, mode)
                authority_documents.append({"path": path, "bytes": size, "sha256": sha256, "mode": mode})
    return {"inherited_reference": INHERITED_REVISION, "inherited_files": rows,
            "c239_source": {"path": "tools/second_target_c239/check_combined.py", **_SELF_BINDING},
            "contract": {"path": CONTRACT_PATH, **_binding(contract)}, "module_origins": origins,
            "authority_documents": authority_documents, "hostile_host_attestation": False}, sources


def _module_origins(modules):
    visited, rows = set(), []

    def visit(module, tag, chain):
        key = (id(module), tag)
        if key in visited:
            return
        visited.add(key)
        expected = str(REPOSITORY / CHECKER_PINS[tag][0])
        actual = getattr(module, "__file__", None)
        origin = getattr(getattr(module, "__spec__", None), "origin", None)
        _require(actual == expected and origin == expected,
                 "MODULE_ORIGIN", chain + ": loaded module is not the pinned local source")
        rows.append({"chain": chain, "component": tag, "file": actual, "spec_origin": origin})
        children = {"C222": (("c221", "C221"),), "C234": (("c222", "C222"), ("c221", "C221")),
                    "C235": (("c222", "C222"), ("c221", "C221")), "C236": (("c221", "C221"),),
                    "C237": (("authority", "C221"),), "C238": (("c221", "C221"),)}.get(tag, ())
        for attribute, child_tag in children:
            visit(getattr(module, attribute, None), child_tag, chain + "." + attribute)

    for tag in CHECKER_PINS:
        visit(modules[tag], tag, tag)
    return rows


def _load_components():
    global _MODULES
    _, sources = _source_guard(_MODULES)
    if _MODULES is None:
        modules = {}
        for tag, (relative, _, _) in CHECKER_PINS.items():
            path = str(REPOSITORY / relative)
            spec = importlib.util.spec_from_file_location("c239_dependency_" + tag.lower(), path)
            module = importlib.util.module_from_spec(spec)
            exec(compile(sources[tag], path, "exec"), module.__dict__)
            modules[tag] = module
        _source_guard(modules)
        _MODULES = modules
    return _MODULES


def _capture_inputs(package_root, envelope_path, admission, modules):
    c238, c221 = modules["C238"], modules["C221"]
    files, members = {}, {}
    with c238._Snapshot(envelope_path) as snapshot:
        raw, binding = snapshot.read(snapshot.envelope_name, 64 * 1024, admission["envelope_binding"])
        envelope_name = snapshot.envelope_name
        files["observations/" + envelope_name] = (raw, 0o400)
        for row in admission["members"]:
            role, name = row["role"], row["path"]
            raw, binding = snapshot.read(name, c238.ROLE_SPECS[role][1], row["inspected_binding"], role)
            relative = "observations/" + name
            files[relative] = (raw, 0o400)
            members[role] = {"path": relative, **binding}
        captured = snapshot.finish()
    with c221.SafeRoot(package_root) as authority:
        for pin in admission["authority"]["inputs"]:
            raw = authority.read(pin["packagePath"], pin["bytes"], pin["sha256"], pin["mode"])
            files["authority/" + pin["packagePath"]] = (raw, pin["mode"])
    _require(len(files) == 15 and set(members) == set(ROLES), "SNAPSHOT_INVENTORY", "The complete 7+8 file snapshot is required")
    manifest = [{"path": path, "mode": mode, **_binding(raw)} for path, (raw, mode) in sorted(files.items())]
    return files, members, envelope_name, {"capture": captured, "files": manifest,
            "envelope_path": "observations/" + envelope_name, "authority_files": 8, "observation_files": 7,
            "original_paths_reused_by_components": False, "post_capture_original_immutability": False}


def _write_private(root, files):
    for relative, (raw, mode) in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
        try:
            view = memoryview(raw)
            while view:
                written = os.write(fd, view)
                _require(written > 0, "SNAPSHOT_WRITE", "Private input write did not advance")
                view = view[written:]
            os.fchmod(fd, mode)
        finally:
            os.close(fd)


class _PrivateSnapshot:
    def __init__(self, root, manifest):
        self.root = root
        self.expected = {row["path"]: row for row in manifest}
        self.entries = []
        self.root_fd = _open_root(root)
        try:
            self.directories = self._inventory()
            identities = set()
            for path, pin in self.expected.items():
                raw, info = _read_at(self.root_fd, path, pin["bytes"])
                _require(_binding(raw) == {key: pin[key] for key in ("bytes", "sha256")} and
                         stat.S_IMODE(info.st_mode) == pin["mode"], "SNAPSHOT_BINDING", path + ": private bytes/mode differ")
                parent, name = _parent_fd(self.root_fd, path)
                try:
                    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
                finally:
                    os.close(parent)
                identity = (info.st_dev, info.st_ino)
                if identity in identities or _stat_key(os.fstat(fd)) != _stat_key(info):
                    os.close(fd)
                    raise Refusal("SNAPSHOT_CHANGED", path + ": private file alias or replacement")
                identities.add(identity)
                self.entries.append({"path": path, "fd": fd, "stat": _stat_key(info)})
        except BaseException:
            self.close()
            raise

    def _inventory(self):
        files, directories = set(), {}

        def visit(fd, prefix):
            directories[prefix] = _stat_key(os.fstat(fd))
            for name in os.listdir(fd):
                path = prefix + "/" + name if prefix else name
                info = os.stat(name, dir_fd=fd, follow_symlinks=False)
                if stat.S_ISDIR(info.st_mode):
                    child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                    try:
                        visit(child, path)
                    finally:
                        os.close(child)
                else:
                    _require(stat.S_ISREG(info.st_mode), "SNAPSHOT_FILE", path + ": private nonregular entry")
                    files.add(path)
        visit(self.root_fd, "")
        _require(files == set(self.expected), "SNAPSHOT_INVENTORY", "Private file inventory changed")
        wanted = {""}
        for path in self.expected:
            wanted.update(str(p) for p in Path(path).parents if str(p) != ".")
        _require(set(directories) == wanted, "SNAPSHOT_INVENTORY", "Private directory inventory changed")
        return directories

    def check(self, label):
        _require(self._inventory() == self.directories, "SNAPSHOT_CHANGED", "Private directory metadata changed")
        for entry in self.entries:
            path, pin = entry["path"], self.expected[entry["path"]]
            _require(_stat_key(os.fstat(entry["fd"])) == entry["stat"], "SNAPSHOT_CHANGED", path + ": held descriptor changed")
            raw, info = _read_at(self.root_fd, path, pin["bytes"])
            _require(_stat_key(info) == entry["stat"] and _binding(raw) == {key: pin[key] for key in ("bytes", "sha256")},
                     "SNAPSHOT_CHANGED", path + ": private entry or bytes changed")
        return {"boundary": label, "result": "PASS_PRIVATE_SNAPSHOT", "files": len(self.entries),
                "directories": len(self.directories), "bytes_verified": sum(row["bytes"] for row in self.expected.values())}

    def close(self):
        for entry in self.entries:
            os.close(entry["fd"])
        self.entries.clear()
        if self.root_fd is not None:
            os.close(self.root_fd)
            self.root_fd = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


def _known_refusals(modules):
    kinds = []
    for tag, module in modules.items():
        for candidate in (module, getattr(module, "c221", None), getattr(module, "c222", None), getattr(module, "authority", None)):
            for name in ("CheckError", "Refusal"):
                value = getattr(candidate, name, None)
                if isinstance(value, type) and issubclass(value, Exception):
                    kinds.append(value)
    return tuple(set(kinds))


def _invoke_component(tag, modules, authority_root, paths):
    module = modules[tag]
    if tag == "C222":
        return module.check_observations(authority_root, paths["geometry"])
    if tag == "C234":
        return module.check_materials(authority_root, paths["geometry"], paths["materials"])
    if tag == "C235":
        return module.check_normals(authority_root, paths["geometry"], paths["normals"])
    if tag == "C236":
        return module.check_poses(authority_root, paths["poses"])
    return module.check_semantics(authority_root, paths["semantics"])


def _classification(tag, report):
    if report["result"] == PASS_RESULTS[tag]:
        return "pass"
    if tag == "C234" and report.get("comparison", {}).get("result") == "FAIL_MATERIAL_PARAMETERS" and \
            report.get("error", {}).get("code") == "MATERIAL_COMPARISON":
        return "measured_loss"
    if tag == "C235" and report["result"] == "FAIL_STRICT_NORMAL_LIMIT":
        return "measured_loss"
    if tag == "C236" and report["result"] in ("FAIL_POSE_LIMIT", "FAIL_SCALE_PROFILE"):
        return "profile_loss" if report["result"] == "FAIL_SCALE_PROFILE" else "measured_loss"
    if tag == "C237" and report.get("resultClass") == "measured_loss":
        return "measured_loss"
    return "structural_refusal"


def _component_bindings(tag, component, members, geometry):
    if component is None:
        return []
    checks = []

    def compare(label, actual, expected):
        _require(type(actual) is dict and all(type(actual.get(k)) is type(expected[k]) and actual[k] == expected[k]
                 for k in ("bytes", "sha256")), "COMPONENT_BINDING", tag + ": " + label + " differs from retained bytes")
        checks.append({"binding": label, "equal": True, **{key: expected[key] for key in ("bytes", "sha256")}})

    role = {"C222": "geometry", "C234": "materials", "C235": "normals", "C236": "poses", "C237": "semantics"}[tag]
    if tag == "C237":
        if "observation" in component:
            compare(role, component["observation"], members[role])
    elif "observation_bytes" in component or "observation_sha256" in component:
        compare(role, {"bytes": component.get("observation_bytes"), "sha256": component.get("observation_sha256")}, members[role])
    if tag in ("C234", "C235"):
        inherited = component.get("geometry", {})
        if "observation_bytes" in inherited or "observation_sha256" in inherited:
            compare("geometry", {"bytes": inherited.get("observation_bytes"), "sha256": inherited.get("observation_sha256")}, members["geometry"])
            if geometry is not None:
                expected = geometry["correspondence"]["corner_map_sha256"]
                _require(inherited.get("corner_map_sha256") == expected, "COMPONENT_BINDING", tag + ": actual C222 map digest differs")
                checks.append({"binding": "derived_corner_map", "sha256": expected, "equal": True})
    if _classification(tag, component) != "structural_refusal":
        _require(any(row["binding"] == role for row in checks), "COMPONENT_BINDING", tag + ": checked observation binding is missing")
    return checks


def _compare_map(admission, geometry):
    declared = admission["corner_map_projection"]
    derived = geometry["correspondence"]
    left, right = declared["corner_map"], derived["corner_map"]
    fields_equal = declared["corner_map_fields"] == derived["corner_map_fields"]
    _require(len(left) == len(right) == 23400, "MAP_COUNT", "Complete declared and derived maps are required")
    mismatches = [{"row": index, "declared": a, "derived": b} for index, (a, b) in enumerate(zip(left, right)) if a != b]
    equal = fields_equal and not mismatches
    return {"result": "PASS_DECLARED_CORRESPONDENCE" if equal else "FAIL_DECLARED_CORRESPONDENCE",
            "rows": len(right), "fields_equal": fields_equal, "equal": equal,
            "declared_fields": declared["corner_map_fields"], "derived_fields": derived["corner_map_fields"],
            "declared_sha256": _binding(_canonical(left))["sha256"], "derived_sha256": _binding(_canonical(right))["sha256"],
            "declared_map": left, "derived_map": right, "mismatches": mismatches,
            "mapping_attested": False}


def _base_report():
    return {"schema": REPORT_SCHEMA, "version": VERSION, "result": "FAIL_CLOSED", "result_class": "structural_refusal",
            "stages": {name: "NOT_RUN" for name in ("source", "admission", "capture", "retained_admission", "components", "final_snapshot")},
            "components": {tag: {"state": "NOT_RUN", "result": "NOT_RUN", "classification": "not_run", "report": None} for tag in COMPONENTS},
            "correspondence": {"result": "NOT_RUN"}, "component_losses": [], "component_refusals": [],
            "snapshot_boundaries": [], "snapshot_valid": False, "scratch_cleanup": {"created": False, "removed": True},
            "limits": {"native_receiving_evidence": False, "native_mapping_attested": False, "native_capture_attested": False,
                       "shared_capture_provenance": False, "source_execution": False, "native_execution": False,
                       "aggregate_execution": False, "target_execution_authorized": False, "full_r07_acceptance": False,
                       "release_acceptance": False, "original_blender_normal_failure_repaired": False,
                       "target_starts": 0, "native_version_starts": 0, "source_evaluations": 0, "exports": 0,
                       "imports": 0, "renders": 0, "scene_writes": 0, "aggregate_runs": 0,
                       "meaning": "Finite CPU checks on one retained untrusted observation; native claims remain unestablished"}}


def _summarize(report):
    report["component_losses"] = [tag for tag, row in report["components"].items() if row["classification"] in ("measured_loss", "profile_loss")]
    report["component_refusals"] = [tag for tag, row in report["components"].items() if row["classification"] == "structural_refusal"]


def check_combined(package_root, envelope_path):
    """Return complete original component reports on one fresh verified snapshot."""
    report, stage, scratch = _base_report(), "source", None
    try:
        modules = _load_components()
        report["source_binding"], _ = _source_guard(modules)
        report["stages"][stage] = "PASS"
        stage = "admission"
        try:
            report["admission"] = modules["C238"].check_envelope(package_root, envelope_path)
        except modules["C238"].CheckError as exc:
            report["admission"] = exc.report
            raise
        report["stages"][stage] = "PASS"
        stage = "capture"
        files, members, envelope_name, report["snapshot"] = _capture_inputs(package_root, envelope_path, report["admission"], modules)
        _source_guard(modules)
        with tempfile.TemporaryDirectory(prefix="ontokin-c239-") as temporary:
            scratch = Path(temporary)
            report["scratch_cleanup"] = {"created": True, "removed": False}
            _write_private(scratch, files)
            del files
            with _PrivateSnapshot(scratch, report["snapshot"]["files"]) as snapshot:
                report["snapshot_boundaries"].append(snapshot.check("after_capture"))
                report["stages"][stage] = "PASS"
                stage = "retained_admission"
                retained_envelope = scratch / "observations" / envelope_name
                authority_root = scratch / "authority"
                try:
                    report["retained_admission"] = modules["C238"].check_envelope(authority_root, retained_envelope)
                except modules["C238"].CheckError as exc:
                    report["retained_admission"] = exc.report
                    raise
                _require(_canonical(report["retained_admission"]) == _canonical(report["admission"]),
                         "SNAPSHOT_ADMISSION", "Retained and original fresh C238 admissions differ")
                report["parts"] = report["retained_admission"]["parts"]
                report["snapshot_boundaries"].append(snapshot.check("after_retained_admission"))
                _source_guard(modules)
                report["stages"][stage] = "PASS"
                stage = "components"
                paths = {role: scratch / member["path"] for role, member in members.items()}
                geometry = None
                for tag in COMPONENTS:
                    report["snapshot_boundaries"].append(snapshot.check("before_" + tag))
                    _source_guard(modules)
                    row = {"state": "EXECUTED", "result": "NO_COMPONENT_REPORT", "classification": "structural_refusal",
                           "report": None, "snapshot_valid": False}
                    report["components"][tag] = row
                    try:
                        component = _invoke_component(tag, modules, authority_root, paths)
                    except _known_refusals(modules) as exc:
                        component = getattr(exc, "report", None)
                        row["error"] = {"code": getattr(exc, "code", "INPUT"), "stage": getattr(exc, "stage", None), "message": str(exc)}
                    except Exception as exc:
                        row.update(state="ERROR", error={"code": "COMPONENT_EXCEPTION", "type": type(exc).__name__, "message": str(exc)})
                        raise Refusal("COMPONENT_EXCEPTION", tag + ": unexpected " + type(exc).__name__ + ": " + str(exc)) from exc
                    row["report"] = component
                    if component is not None:
                        row["result"], row["classification"] = component["result"], _classification(tag, component)
                    report["snapshot_boundaries"].append(snapshot.check("after_" + tag))
                    _source_guard(modules)
                    row["bindings"] = _component_bindings(tag, component, members, geometry)
                    row["snapshot_valid"] = True
                    if tag == "C222":
                        if row["classification"] == "pass":
                            geometry = component
                            report["correspondence"] = _compare_map(report["retained_admission"], geometry)
                        else:
                            report["correspondence"] = {"result": "NOT_RUN", "reason": "C222 structural refusal", "geometry_error": row.get("error")}
                report["stages"][stage] = "PASS_EXECUTION_COMPLETED"
                stage = "final_snapshot"
                report["snapshot_boundaries"].append(snapshot.check("final"))
                report["source_binding_after"], _ = _source_guard(modules)
                _require(report["source_binding"] == report["source_binding_after"], "SOURCE_CHANGED", "Inspected executable bindings changed")
                report["stages"][stage] = "PASS"
                report["snapshot_valid"] = True
        report["scratch_cleanup"]["removed"] = not os.path.lexists(scratch)
        _require(report["scratch_cleanup"]["removed"], "SCRATCH_CLEANUP", "Private snapshot removal is incomplete")
        _summarize(report)
        if report["component_refusals"]:
            report.update(result="FAIL_COMPONENT_REFUSAL", result_class="structural_refusal")
        elif report["correspondence"]["result"] == "FAIL_DECLARED_CORRESPONDENCE":
            report.update(result="FAIL_DECLARED_CORRESPONDENCE", result_class="declared_correspondence_mismatch")
        elif report["component_losses"]:
            report.update(result="FAIL_COMPONENT_LOSS", result_class="measured_loss")
        else:
            _require(report["correspondence"]["result"] == "PASS_DECLARED_CORRESPONDENCE" and
                     all(row["classification"] == "pass" for row in report["components"].values()),
                     "INCOMPLETE", "Every finite component and complete correspondence must pass")
            report.update(result="PASS_CPU_COMBINED", result_class="pass")
    except Exception as exc:
        report.update(result="FAIL_CLOSED", result_class="structural_refusal", snapshot_valid=False)
        report["stages"][stage] = "FAIL_CLOSED"
        report["error"] = {"stage": stage, "code": getattr(exc, "code", "IO" if isinstance(exc, OSError) else "UNEXPECTED"),
                           "type": type(exc).__name__, "message": str(exc)}
        for row in report["components"].values():
            if row["state"] != "NOT_RUN":
                row["snapshot_valid"] = False
        _summarize(report)
        if scratch is not None:
            report["scratch_cleanup"]["removed"] = not os.path.lexists(scratch)
    return report


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise Refusal("ARGUMENT", message)


def main(argv=None):
    parser = _ArgumentParser(description=__doc__, add_help=False)
    parser.add_argument("--package-root", required=True)
    parser.add_argument("--envelope", required=True)
    try:
        args = parser.parse_args(argv)
        report = check_combined(args.package_root, args.envelope)
    except Refusal as exc:
        report = _base_report()
        report["error"] = {"stage": "arguments", "code": exc.code, "message": str(exc)}
    print(json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False))
    return 0 if report["result_class"] == "pass" else (2 if report["result_class"] == "structural_refusal" else 1)


if __name__ == "__main__":
    raise SystemExit(main())
