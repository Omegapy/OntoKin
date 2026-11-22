"""Frozen P11 controls under the separately adopted P13 applicability boundary.

Exactly 96 methods exercise runtime primitives. N57 remains an unsatisfied
external review obligation; no method, skip, or synthetic runtime verdict is
created for it. Fixtures stay inert. Logical kernel/filesystem observations
are translated at named private observation seams, never into an approval.

ONTOKIN_LP_RETAIN_ROOT selects a fresh retained evidence directory. Ordinary
unittest use instead creates a private temporary directory. Neither form
executes fixture images, interpreters, loaders, or target commands.
"""
from __future__ import annotations

from contextlib import ExitStack
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from prototypes.static_tray_v01 import current_host_inspection_v01 as inspection


REPO = Path(__file__).resolve().parents[1]
P11 = REPO / "docs/engineering/localized-repair-c271/loader-path-p11/design/candidate004"
P13 = REPO / "docs/engineering/localized-repair-c271/review-boundary-p13"
# Independent identities come from P13 INPUTS E07-E09 and the adopted P13
# candidate manifest. They are not taken from the payload being authenticated.
IDENTITIES = {
    "p11_manifest": "e7b505aa768d0656db6c4dfaf7541e796aefee7148878a6fdf380d6ab0b911de",
    "p11_fixtures": "ea377d25e96631b70cd8909a5375fa3fd0feadf7f017f0673d8a094335186594",
    "p11_oracle": "dfb285f41a58a1f7254aaae4aa022f91afdc72fb7d5dad2f3d6b1e8257d14137",
    "p13_manifest": "82dbe17199b0625e512f3ac050d18cf048cfc2e42f20d0054bcbc292d228c085",
    "p13_mapping": "03c2a04733abcf41ef29281f69504d27b567ac1e9921e4e34858225af18f9be2",
}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def authenticated(path, expected):
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise AssertionError("Frozen input is not an ordinary single-link file: " + str(path))
    if any(parent.is_symlink() for parent in (path, *path.parents)):
        raise AssertionError("Frozen input traverses a symlink: " + str(path))
    raw = path.read_bytes()
    if sha256(raw) != expected:
        raise AssertionError("Frozen input identity changed: " + str(path))
    return raw


def safe_name(value):
    path = PurePosixPath(value)
    if not isinstance(value, str) or not value or path.is_absolute() or str(path) != value:
        raise AssertionError("Unsafe frozen relative path")
    if any(part in (".", "..") for part in path.parts):
        raise AssertionError("Frozen path leaves its candidate")
    return path


MANIFEST_RAW = authenticated(P11 / "CANDIDATE-MANIFEST.json", IDENTITIES["p11_manifest"])
FIXTURES_RAW = authenticated(P11 / "FIXTURE-MANIFEST.json", IDENTITIES["p11_fixtures"])
ORACLE_RAW = authenticated(P11 / "EXPECTATIONS.json", IDENTITIES["p11_oracle"])
P13_MANIFEST_RAW = authenticated(P13 / "design/candidate001/CANDIDATE-MANIFEST.json", IDENTITIES["p13_manifest"])
MAPPING_RAW = authenticated(P13 / "design/candidate001/CONTROL-MAPPING.json", IDENTITIES["p13_mapping"])
MANIFEST, FIXTURES, ORACLE, MAPPING = (json.loads(value) for value in
                                      (MANIFEST_RAW, FIXTURES_RAW, ORACLE_RAW, MAPPING_RAW))
CASES = {row["id"]: row for row in FIXTURES["cases"]}
ROWS = {row["id"]: row for row in MAPPING["cases"]}
if len(CASES) != 97 or len(ROWS) != 97 or set(CASES) != set(ROWS) or set(CASES) != set(ORACLE["cases"]):
    raise AssertionError("Original 97-case accounting changed")
for _name, _row in ROWS.items():
    _case = CASES[_name]
    if (_row["original_input"] != _case["input"]["path"] or
            _row["original_route"] != _case["route"] or
            _row["original_expected_key"] != _case["expected_key"]):
        raise AssertionError("P13 mapping changed a frozen case")
RUNTIME_IDS = sorted(name for name, row in ROWS.items() if row["classification"] == "future_runtime_primitive")
EXTERNAL_IDS = sorted(name for name, row in ROWS.items() if row["classification"] == "independent_review_only")
if len(RUNTIME_IDS) != 96 or EXTERNAL_IDS != ["N57_source_variant_unknown"]:
    raise AssertionError("Adopted 96-runtime-plus-one-review applicability changed")
if ROWS[EXTERNAL_IDS[0]]["runtime_expectation"] is not None:
    raise AssertionError("External review has acquired a synthetic runtime oracle")


def exclusive_bytes(path, raw, mode=0o600):
    if path.exists() or path.is_symlink():
        raise AssertionError("Evidence destination already exists: " + str(path))
    with path.open("xb") as stream:
        stream.write(raw)
    path.chmod(mode)
    return {"path": str(path), "sha256": sha256(raw), "size_bytes": len(raw), "mode": oct(mode)}


def document(path, value):
    return exclusive_bytes(path, canonical(value))


class MaterializedInputs:
    """Restore only the 131 fixtures and consumed frozen metadata, not a full archive."""

    def __init__(self, root):
        self.root = root
        root.mkdir(mode=0o700)
        self.candidate = root / "candidate004"
        self.candidate.mkdir(mode=0o700)
        (self.candidate / "fixture_inputs").mkdir(mode=0o700)
        self.observations = root / "observations"
        self.observations.mkdir(mode=0o700)
        payload = {row["path"]: row for row in MANIFEST["payload"]}
        if len(payload) != len(MANIFEST["payload"]):
            raise AssertionError("Duplicate candidate payload names")
        for name in payload:
            safe_name(name)
        rows = FIXTURES["files"]
        if len(rows) != 131 or len({row["path"] for row in rows}) != 131:
            raise AssertionError("Frozen fixture inventory is not exactly 131 files")
        copied = []
        for row in rows:
            name = str(safe_name(row["path"]))
            if payload.get(name) != row or row["mode"] != "0o600":
                raise AssertionError("Fixture and candidate manifest disagree")
            raw = authenticated(P11 / name, row["sha256"])
            if len(raw) != row["size_bytes"]:
                raise AssertionError("Frozen fixture byte count differs")
            actual = exclusive_bytes(self.candidate / name, raw, int(row["mode"], 8))
            observed = (self.candidate / name).lstat()
            if observed.st_nlink != 1 or not stat.S_ISREG(observed.st_mode):
                raise AssertionError("Materialized fixture is not a single-link regular file")
            if oct(stat.S_IMODE(observed.st_mode)) != row["mode"] or (self.candidate / name).read_bytes() != raw:
                raise AssertionError("Materialized fixture does not match frozen bytes/mode")
            copied.append({**row, "destination": actual["path"]})
        for name, raw in (("CANDIDATE-MANIFEST.json", MANIFEST_RAW),
                          ("FIXTURE-MANIFEST.json", FIXTURES_RAW), ("EXPECTATIONS.json", ORACLE_RAW)):
            mode = int(payload[name]["mode"], 8) if name in payload else 0o644
            exclusive_bytes(self.candidate / name, raw, mode)
        exclusive_bytes(root / "P13-CANDIDATE-MANIFEST.json", P13_MANIFEST_RAW, 0o644)
        exclusive_bytes(root / "P13-CONTROL-MAPPING.json", MAPPING_RAW, 0o644)
        adoption_raw = (P13 / "ADOPTION.json").read_bytes()
        adoption = json.loads(adoption_raw)
        if adoption["candidate_manifest"]["sha256"] != IDENTITIES["p13_manifest"] or adoption["decision_id"] != "P13-RB-001":
            raise AssertionError("P13 adoption no longer identifies this mapping")
        exclusive_bytes(root / "P13-ADOPTION.json", adoption_raw, 0o644)
        document(root / "MATERIALIZATION.json", {
            "schema": "ontokin.c271.p14-control-materialization/1", "fixture_count": len(copied),
            "identities": IDENTITIES, "files": copied, "all_regular_single_link_inert": True,
            "source_fixture_modes_modified": False, "payload_scope": "131 fixtures and consumed oracle/manifests/mapping/adoption only",
            "full_candidate_materialization": False,
            "excluded_external_historical_payload": payload["REVISION-004.diff"],
        })
        document(root / "EXTERNAL-REVIEW-OBLIGATION.json", {
            "id": EXTERNAL_IDS[0], "decision": "P13-RB-001", "mapping": IDENTITIES["p13_mapping"],
            "original_input": CASES[EXTERNAL_IDS[0]]["input"],
            "original_oracle": ORACLE["cases"][EXTERNAL_IDS[0]],
            "runtime_execution": "not_applicable_under_adopted_P13", "runtime_pass": False,
            "historical_oracle_satisfied": False, "external_review": "not_established_by_supplied_inputs",
            "host_qualification": False, "not_counted_as_runtime_or_skip": True,
        })

    def context(self, case):
        row = case["input"]
        return json.loads(authenticated(self.candidate / row["path"], row["sha256"]))

    def image(self, row):
        path = self.candidate / row["path"]
        raw = authenticated(path, row["sha256"])
        if len(raw) != row["size_bytes"] or oct(stat.S_IMODE(path.stat().st_mode)) != row["mode"]:
            raise AssertionError("Consumed fixture bytes or mode changed")
        return path


class LogicalProjection:
    """Translate frozen observations into operational field shapes and read seams.

The synthetic completeness label, assumptions, case ID, and oracle never enter
any production call. The selected real descriptor describes the rule's declared
subject precondition only. Actual synthetic ELF bytes are always separately
bound and read as data; they are never claimed to satisfy operational admission.
"""

    def __init__(self, materialized, context, directory):
        self.materialized, self.context, self.directory = materialized, deepcopy(context), directory
        self.trace, self.checkpoints, self.callback_triggers = [], [], []
        self.active_checkpoint = None
        self.sentinel = RuntimeError("SENTINEL-P11-DEADLINE")
        self.subject = context["subject"]
        self.subject_path = self.subject["path"]
        self.subject_descriptor = {"path": self.subject_path, **self.subject["operational_pin"]}
        review = context["variant_review"]
        loader_bytes = review["loader_identity"].encode("ascii")
        self.loader = {"path": "/fixture/ld-linux-x86-64.so.2", "sha256": sha256(loader_bytes),
                       "size_bytes": len(loader_bytes), "mode": "0o600"}
        rationale_bytes = review["source_review_identity"].encode("ascii")
        self.rationale = exclusive_bytes(directory / "rationale.txt", rationale_bytes)
        self.variant_value = {"schema": "ontokin.current-host-readback-origin-variants/0.1.0",
                              "loader": self.loader, "source_review": self.rationale,
                              "suffixes": deepcopy(review["suffixes"])}
        self.variant_descriptor = document(directory / "variants.json", self.variant_value)
        selection = context["plan_selection"]
        if not selection["variant_descriptor_matches"]:
            # The frozen observation is referenced-byte mismatch. Only the
            # adapter's projected descriptor changes; frozen input is untouched.
            self.variant_descriptor["sha256"] = "0" * 64
        if not selection["rationale_descriptor_matches"]:
            # Real bytes drift after their descriptor was bound. The inherited
            # production _bound reader detects this, not a Boolean policy hook.
            with (directory / "rationale.txt").open("ab") as stream:
                stream.write(b"\nchanged logical rationale bytes")
        self.origin = {
            "schema": "ontokin.current-host-readback-python-origin-rpath/0.1.0",
            "subject": deepcopy(self.subject_descriptor), "invocation": self.subject["invocation"],
            "raw_rpath": ["$ORIGIN/../lib"], "origin": context["origin_claim"],
            "expanded_rpath": deepcopy(context["expanded_claim"]),
            "kernel_origin": {"exe_path": self.subject_path, "at_secure": context["kernel"]["at_secure_claim"]},
            "variant_review": deepcopy(self.variant_descriptor), "variants": deepcopy(context["variants"]),
            "needed_names": deepcopy(context["needed_names_claim"]),
        }
        for key in selection["origin_object_unknown_keys"]:
            self.origin[key] = "unrecognized frozen input field"
        self.resolution = {"profile": selection["profile"], "images": [], "needed_edges": [],
                           "loader_inputs": [], "search_directories": [], "inspector_commands": {},
                           "ignored_kernel_rows": [], "rationale": self.rationale}
        if selection["origin_object_present"]:
            self.resolution["origin_rpath"] = self.origin
        self.declared_guards = deepcopy(context["guards"])
        self.declared_searches = deepcopy(context["search_directories"])
        self.actual_guards = deepcopy(context["guards"])
        self.actual_searches = deepcopy(context["search_directories"])
        self.actual_kernel = deepcopy(context["kernel"])
        self.absence_guards = deepcopy(context["absence_guards"])
        self.images = {}
        for row in context["closure_images"]:
            path = self.subject_path if row["id"] == "python" else "/fixture/closure/" + row["id"]
            self.images[path] = {"class": 64, "endian": "little", "machine": 62, "type": 3,
                                 "interpreter": None, "needed": deepcopy(row["needed"]),
                                 "soname": row["soname"], "rpath": deepcopy(row.get("raw_rpath", [])),
                                 "runpath": deepcopy(row.get("runpath", []))}
        if context["phase"] == "recheck":
            before = context["approved_before"]
            if isinstance(before, list):
                self.declared_guards = deepcopy(before)
            elif "proc_exe_path" in before:
                self.before_kernel = deepcopy(before)
            else:
                self.declared_searches = deepcopy(before)
        self.resolution["search_directories"] = self.search_rows()

    def search_rows(self):
        return [{"path": name, **deepcopy(row)} for name, row in sorted(self.declared_searches.items())]

    def search_map(self):
        return {row["path"]: row for row in self.search_rows()}

    def guard_rows(self):
        rows = deepcopy(self.declared_guards)
        rows.extend({"path": name, **{k: value for k, value in row.items() if k != "absent"}}
                    for name, row in sorted(self.absence_guards.items()))
        return rows

    def subject_observation(self, path):
        self.trace.append({"seam": "_origin_subject_observation", "path": str(path)})
        if str(path) != self.subject_path:
            raise AssertionError("Undeclared logical subject read")
        row = self.subject
        kind_bits = {"file": stat.S_IFREG, "symlink": stat.S_IFLNK, "directory": stat.S_IFDIR,
                     "special": stat.S_IFIFO}[row["kind"]]
        identity = (row["device"], row["inode"], kind_bits | int(row["mode"], 8), row["nlink"],
                    row["operational_pin"]["size_bytes"], 0, 0)
        return {"path": row["path"], "kind": row["kind"], "device": row["device"], "inode": row["inode"],
                "mode": row["mode"], "nlink": row["nlink"], "identity": identity}

    def kernel_observation(self, *, check=lambda: None):
        self.trace.append({"seam": "_read_kernel_origin"})
        check()
        kernel = self.actual_kernel
        if kernel["read_status"] != "read":
            raise OSError("Frozen logical kernel origin unavailable")
        subject = self.subject_observation(self.subject_path)
        identity = list(subject["identity"])
        identity[:2] = [kernel["proc_file_identity"]["device"], kernel["proc_file_identity"]["inode"]]
        raw = self.materialized.image(kernel["auxv"]).read_bytes()
        return {"exe_path": kernel["proc_exe_path"], "identity": tuple(identity), "auxv": raw}

    def path_row(self, path):
        name = str(path)
        self.trace.append({"seam": "_path_row", "path": name})
        rows = {row["path"]: row for row in self.actual_guards}
        if name in rows:
            return deepcopy(rows[name])
        if name == self.subject_path:
            row = self.subject
            return {"path": name, **{k: row[k] for k in ("kind", "device", "inode", "mode")}, "target": None}
        raise AssertionError("Undeclared logical path-row read: " + name)

    def absent(self, path):
        name = str(path)
        self.trace.append({"seam": "_origin_absent", "path": name})
        if name not in self.absence_guards:
            raise AssertionError("Undeclared logical absence read: " + name)
        return self.absence_guards[name]["absent"]

    def directory_entries(self, path, *, check=lambda: None, _candidate_names=None):
        name = str(path)
        self.trace.append({"seam": "_directory_entries", "path": name})
        check()
        if name not in self.actual_searches:
            raise AssertionError("Undeclared logical directory read: " + name)
        return {"path": name, **deepcopy(self.actual_searches[name])}

    def callback(self):
        fault = self.context["fault"]
        if fault and self.active_checkpoint == fault["at"]:
            self.callback_triggers.append(self.active_checkpoint)
            raise self.sentinel

    def patches(self, stack):
        for name, method in (("_origin_subject_observation", self.subject_observation),
                             ("_read_kernel_origin", self.kernel_observation), ("_path_row", self.path_row),
                             ("_origin_absent", self.absent), ("_directory_entries", self.directory_entries)):
            stack.enter_context(patch.object(inspection, name, side_effect=method))
        checkpoint = inspection._origin_checkpoint

        def at_checkpoint(check, stage):
            self.checkpoints.append(stage)
            self.active_checkpoint = stage
            try:
                return checkpoint(check, stage)
            finally:
                self.active_checkpoint = None

        stack.enter_context(patch.object(inspection, "_origin_checkpoint", side_effect=at_checkpoint))

    def read_metadata(self):
        path = self.materialized.image(self.context["image"])
        self.trace.append({"boundary": "_read_origin_elf_metadata", "path": str(path)})
        metadata = inspection._read_origin_elf_metadata(path, check=self.callback, require_interpreter=True)
        self.images[self.subject_path] = metadata
        return metadata

    def role(self):
        role = self.subject["role"]
        python_path = self.subject_path if role == "author_python" else "/fixture/roles/author_python"
        forbidden = [] if role == "author_python" else [self.subject_path]
        self.trace.append({"boundary": "_check_origin_role", "subject_role": role})
        inspection._check_origin_role(self.subject_path, python_path, forbidden, self.subject["invocation"])

    def rule(self):
        self.trace.append({"boundary": "_select_origin_profile"})
        origin = inspection._select_origin_profile(self.context["plan_selection"]["schema"], self.resolution)
        self.trace.append({"boundary": "_check_origin_bounds"})
        inspection._check_origin_bounds(origin, images=self.images, check=self.callback)
        self.role()
        metadata = self.read_metadata()
        self.trace.append({"boundary": "_check_origin_rule"})
        result = inspection._check_origin_rule(origin, metadata, self.images,
            search_directories=self.search_map(), path_guards=self.guard_rows(),
            loader=self.loader, rationale=self.rationale, check=self.callback)
        return metadata, result

    def approved_before(self):
        """Establish the frozen before-state at the raw-rule boundary only."""
        after = self.actual_guards, self.actual_searches, self.actual_kernel
        self.actual_guards = deepcopy(self.declared_guards)
        self.actual_searches = deepcopy(self.declared_searches)
        self.actual_kernel = deepcopy(getattr(self, "before_kernel", self.actual_kernel))
        try:
            return self.rule()
        finally:
            self.actual_guards, self.actual_searches, self.actual_kernel = after

    def caller_failure(self, boundary):
        """Negative caller-order experiment with explicit admitted prerequisites.

        These nonoperational contexts cannot form a positive operational plan.
        Unrelated inherited source/host admissions and the real-pin precondition
        are therefore isolated here. Actual _validate/_recheck ordering,
        _check_resolution, subject ELF parser, complete origin proof, and error
        wrapping remain live. Every later effect is guarded and must stay zero.
        """
        if boundary not in ("_validate", "_recheck"):
            raise AssertionError("Undeclared caller boundary")
        image_binding = {key: self.context["image"][key] for key in ("sha256", "size_bytes", "mode")}
        files = {self.subject_path: image_binding, self.loader["path"]: inspection._binding(self.loader)}
        rows = []
        for path, metadata in self.images.items():
            if path != self.subject_path:
                raw = canonical(metadata)
                files[path] = {"sha256": sha256(raw), "size_bytes": len(raw), "mode": "0o600"}
            rows.append({"file": {"path": path, **files[path]}, "metadata": deepcopy(metadata),
                         "resolved_needed": {name: "/fixture/closure/" + name for name in metadata["needed"]}})
        resolution = deepcopy(self.resolution)
        resolution["images"] = rows
        resolution["search_directories"] = self.search_rows()
        runtime = {"executable": self.subject_descriptor, "interpreter": self.loader["path"],
                   "extension_files": [], "files": files, "aliases": {}}
        plan = {"schema": self.context["plan_selection"]["schema"],
                "source": {"root": str(REPO), "commit": "4023a878ccc9980726e3b56102b41faa51be0eb1"},
                "author": {"python_descriptor": self.subject_descriptor},
                "host_static": {"resolution": resolution, "files": files,
                    "aliases": {self.loader["path"]: {"resolved_path": self.loader["path"]}},
                    "path_guards": self.guard_rows()}, "evidence": {"parent": str(self.directory)}}
        descriptor = document(self.directory / (boundary.removeprefix("_") + "-plan.json"), plan)
        patched = {
            "_plan_shape": "Supply already-admitted unrelated plan fields; actual _select_origin_profile still runs.",
            "_check_source_files": "Source inventory admission is an inherited prerequisite, unrelated to logical origin drift.",
            "_git_state": "Supply the equal pre-existing source ref/index witness; no Git read executes.",
            "_check_author_runtime": "Supply admitted author-runtime descriptor/closure; exact synthetic pin refusal tested separately.",
            "_check_host_static": "Supply unrelated host/platform admission; new path/kernel observations remain live.",
            "_check_author_host_bindings": "Supply inherited author/HOST role consistency only.",
            "_prepare_origin_policy": "Supply immutable subject policy under explicit synthetic private-rule precondition, never operational approval.",
            "_bound": "Only logical closure-file bindings are admitted; real plan, variant, and rationale documents retain the actual reader.",
            "_read_origin_elf_metadata": "Map logical subject pathname to its exact frozen inert bytes; actual raw parser executes.",
            "_read_plan_elf_metadata": "Supply frozen nonsubject metadata observations; subject still uses actual plan dispatch and actual byte parser.",
        }
        effect_names = ("_load_helpers", "_check_git", "_check_metadata", "_check_runtime_dependencies", "_run_command")
        effects, calls = {}, []
        actual_bound = inspection._bound
        actual_origin_reader = inspection._read_origin_elf_metadata
        actual_plan_reader = inspection._read_plan_elf_metadata
        actual_resolution = inspection._check_resolution

        def bound(path, expected, **kwargs):
            if str(path) in self.images:
                if expected != files[str(path)]:
                    raise AssertionError("Caller harness changed a logical closure binding")
                kwargs.get("check", lambda: None)()
                return expected
            return actual_bound(path, expected, **kwargs)

        def origin_reader(path, **kwargs):
            if str(path) == self.subject_path:
                path = self.materialized.image(self.context["image"])
            return actual_origin_reader(path, **kwargs)

        def plan_reader(path, policy, **kwargs):
            if str(path) == self.subject_path:
                calls.append("actual_subject_parser")
                return actual_plan_reader(path, policy, **kwargs)
            if str(path) not in self.images:
                raise AssertionError("Unbound logical closure parse")
            return deepcopy(self.images[str(path)])

        def resolution_reader(*args, **kwargs):
            calls.append("actual_check_resolution")
            return actual_resolution(*args, **kwargs)

        caught = None
        with ExitStack() as stack:
            stack.enter_context(patch.object(inspection, "_plan_shape", side_effect=lambda p:
                inspection._select_origin_profile(p["schema"], p["host_static"]["resolution"])))
            stack.enter_context(patch.object(inspection, "_check_source_files", return_value={"files": {}}))
            stack.enter_context(patch.object(inspection, "_git_state", return_value={}))
            stack.enter_context(patch.object(inspection, "_check_author_runtime", return_value=runtime))
            stack.enter_context(patch.object(inspection, "_check_host_static", return_value=None))
            stack.enter_context(patch.object(inspection, "_check_author_host_bindings", return_value=None))
            stack.enter_context(patch.object(inspection, "_prepare_origin_policy", return_value=inspection._freeze(self.origin)))
            stack.enter_context(patch.object(inspection, "_bound", side_effect=bound))
            stack.enter_context(patch.object(inspection, "_read_origin_elf_metadata", side_effect=origin_reader))
            stack.enter_context(patch.object(inspection, "_read_plan_elf_metadata", side_effect=plan_reader))
            stack.enter_context(patch.object(inspection, "_check_resolution", side_effect=resolution_reader))
            for name in effect_names:
                effects[name] = stack.enter_context(patch.object(inspection, name,
                    side_effect=AssertionError("Origin proof did not refuse before later effect: " + name)))
            try:
                if boundary == "_validate":
                    inspection._validate(descriptor["path"], descriptor["sha256"], fresh=True)
                else:
                    validated = SimpleNamespace(plan=inspection._freeze(plan), descriptor=inspection._freeze(descriptor),
                        _git_state={}, _helpers=(), _metadata={"expected_resolution": {}})
                    inspection._recheck(validated, check=self.callback)
            except BaseException as exc:
                caught = exc
        report = {"boundary": boundary, "patched_prerequisites": patched,
                  "observed_boundaries": calls, "effect_guard_calls": {key: value.call_count for key, value in effects.items()},
                  "exception": inspection._failure(caught), "positive_operational_admission": False}
        if not isinstance(caught, inspection.HostInspectionError):
            raise AssertionError("Actual caller did not produce the production refusal: " + repr(caught))
        if not calls or "actual_check_resolution" not in calls or "actual_subject_parser" not in calls:
            raise AssertionError("Caller did not reach the real resolution and subject parser")
        if any(value.call_count for value in effects.values()):
            raise AssertionError("A later effect ran before the origin refusal")
        return caught, report


class LoaderPathControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        retained = os.environ.get("ONTOKIN_LP_RETAIN_ROOT")
        if retained:
            root = Path(retained)
            if not root.is_absolute() or root.resolve() != root or root.exists():
                raise AssertionError("A fresh canonical absolute loader evidence root is required")
        else:
            temporary = tempfile.TemporaryDirectory(prefix="ontokin-loader-path-")
            cls.addClassCleanup(temporary.cleanup)
            root = Path(temporary.name) / "controls"
        cls.materialized = MaterializedInputs(root)

    def run_frozen_case(self, case):
        context = self.materialized.context(case)
        self.assertIs(context["operational"], False)
        directory = self.materialized.observations / case["id"]
        directory.mkdir(mode=0o700)
        projection = None
        caught, observed, raw_result, caller_reports = None, None, None, []
        before_result = None
        route = case["route"]
        try:
            if route == "legacy_metadata":
                value = inspection.read_elf_metadata(self.materialized.image(context["image"]),
                                                    require_interpreter=context["require_interpreter"])
                observed = {"outcome": "metadata", "value": value, "host_qualified": False, "target_starts": 0}
            elif route == "binding_rule":
                projection = LogicalProjection(self.materialized, context, directory)
                if not context["plan_selection"]["external_digest_matches"]:
                    concrete = document(directory / "binding-plan.json", {"schema": context["plan_selection"]["schema"],
                                                                         "resolution": projection.resolution})
                    # Exercise the actual pre-decode outer authentication as a
                    # separate preserved diagnostic check before the raw predicate.
                    with self.assertRaises(inspection.HostInspectionError) as outer:
                        inspection._validate(concrete["path"], "0" * 64, fresh=True)
                    self.assertEqual((outer.exception.code, outer.exception.reason, outer.exception.details),
                                     ("CHI-PLAN", "Plan differs from independently supplied expected digest", {}))
                    caller_reports.append({"boundary": "_validate_external_digest", "exception": outer.exception.as_dict()})
                    projection.trace.append({"boundary": "_check_plan_digest", "actual": concrete["sha256"], "expected": "0" * 64})
                    inspection._check_plan_digest(concrete["sha256"], "0" * 64)
                else:
                    actual = context["subject"]["actual_bytes"]
                    self.materialized.image(actual)
                    subject = {"path": context["subject"]["path"],
                               **{key: actual[key] for key in ("sha256", "size_bytes", "mode")}}
                    author = deepcopy(subject)
                    if not context["subject"]["descriptor_matches"]:
                        author["sha256"] = "0" * 64
                    projection.trace.append({"boundary": "_check_origin_subject_binding", "subject": subject, "author": author,
                                             "runtime": subject, "resolved_python": subject})
                    inspection._check_origin_subject_binding(subject, author, subject, subject)
                raise AssertionError("A frozen negative binding observation was admitted")
            else:
                projection = LogicalProjection(self.materialized, context, directory)
                with ExitStack() as stack:
                    projection.patches(stack)
                    if route == "recheck_rule":
                        metadata, before_result = projection.approved_before()
                        self.assertIs(before_result["nonselecting"], True)
                        caught, report = projection.caller_failure("_recheck")
                        caller_reports.append(report)
                        raise caught
                    metadata, raw_result = projection.rule()
                    observed = {"outcome": "rule_acceptance", "accepted_for": "synthetic_private_rule_only",
                                "metadata": metadata, "host_qualified": False, "target_starts": 0,
                                **{key: raw_result[key] for key in ("origin", "expanded_rpath", "raw_rpath", "runpath", "nonselecting")}}
        except inspection.HostInspectionError as exc:
            caught = exc
            observed = {"outcome": "refusal", "code": exc.code, "state": exc.state,
                        "stage": "legacy_parser" if route == "legacy_metadata" else exc.details.get("stage"),
                        "rule_id": "LEGACY-UNCHANGED" if route == "legacy_metadata" else exc.details.get("rule_id"),
                        "host_qualified": False, "target_starts": 0}
            if route == "legacy_metadata":
                observed["reason"] = exc.reason
            if route == "recheck_rule":
                observed["cause_code"] = getattr(exc.cause, "code", None)
        except BaseException as exc:
            caught = exc
            if projection is not None and exc is projection.sentinel:
                observed = {"outcome": "propagated_callback", "exception_identity": str(exc),
                            "stage": projection.callback_triggers[-1] if projection.callback_triggers else None,
                            "host_qualified": False, "target_starts": 0}
            else:
                observed = {"outcome": "unexpected_exception", "type": type(exc).__name__, "reason": str(exc)}
        finally:
            document(directory / "OBSERVATION.json", {
                "case": case["id"], "route": route, "input": case["input"], "oracle_sha256": IDENTITIES["p11_oracle"],
                "expected": ORACLE["cases"][case["expected_key"]], "observed": observed,
                "exception": inspection._failure(caught), "raw_rule_result": raw_result,
                "before_rule_result": before_result, "caller_reports": caller_reports,
                "trace": projection.trace if projection else [], "checkpoints": projection.checkpoints if projection else [],
                "callback_triggers": projection.callback_triggers if projection else [],
                "callback_exception_identity_preserved": projection is not None and caught is projection.sentinel,
                "operational_selected_pin_admission": False, "external_review_approval_supplied": False,
            })
        self.assertEqual(observed, ORACLE["cases"][case["expected_key"]])
        if route == "fault_contract":
            self.assertEqual(projection.callback_triggers, [context["fault"]["at"]])
            self.assertIs(caught, projection.sentinel)
            self.assertIn(context["fault"]["at"], projection.checkpoints)
        # These additional negative experiments retain the real caller order.
        # Selection is by the already observed failure domain, never by an
        # oracle to manufacture an exception or alter the original observation.
        if route == "origin_rule" and isinstance(caught, inspection.HostInspectionError) and caught.details.get("rule_id") in ("LP-ORIGIN", "LP-CANDIDATE"):
            with ExitStack() as stack:
                projection.patches(stack)
                for boundary in ("_validate", "_recheck"):
                    error, report = projection.caller_failure(boundary)
                    if boundary == "_validate":
                        self.assertEqual((error.code, error.details), (caught.code, caught.details))
                    else:
                        self.assertEqual(error.code, "CHI-DRIFT")
                        self.assertEqual((error.cause.code, error.cause.details), (caught.code, caught.details))
                    document(directory / (boundary.removeprefix("_") + "-ordering.json"), report)


def frozen_method(case):
    def test(self):
        self.run_frozen_case(case)
    test.__name__ = "test_" + case["id"]
    test.__doc__ = case["purpose"]
    return test


for _case_id in RUNTIME_IDS:
    setattr(LoaderPathControls, "test_" + _case_id, frozen_method(CASES[_case_id]))


if __name__ == "__main__":
    unittest.main()
