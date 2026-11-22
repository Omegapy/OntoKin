"""Execute the unchanged P16 inert corpus at its declared private boundaries.

The shared adapter also supports the separately frozen P17 corpus. Real file
reads are restricted to restored inert fixtures. Binding and recheck cases use
labelled logical observations; they prove no actual file or operational-plan
admission. ONTOKIN_LIBC_RETAIN_ROOT retains each case's complete observations.
"""
from __future__ import annotations

from contextlib import ExitStack
from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

from prototypes.static_tray_v01 import current_host_inspection_v01 as inspection


REPO = Path(__file__).resolve().parents[1]
BINDING_FIELDS = (
    "subject", "loader", "python_descriptor", "actual_python_needed", "actual_python_interpreter",
    "python_resolved_needed", "dependency_role_names", "forbidden_resolved_paths", "host_aliases",
    "runtime_aliases", "host_files", "runtime_files", "libc_image_descriptor", "loader_image_descriptor",
    "runtime_interpreter",
)
LIBC_SCHEMA = "ontokin.current-host-readback-libc-plt/0.1.0"
P16_SCHEMA = "ontokin.current-host-readback-inspection-plan/0.1.2"
P16_PROFILE = "linux-glibc-declared-python-origin-rpath-libc-plt-v1"


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def write_document(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write("\n")


def safe_name(value):
    name = PurePosixPath(value)
    if not isinstance(value, str) or not value or name.is_absolute() or str(name) != value or ".." in name.parts:
        raise AssertionError("Unsafe frozen relative name")
    return str(name)


def byte_count(row):
    return row["size_bytes"] if "size_bytes" in row else row["bytes"]


class FrozenCorpus:
    """Authenticate the entire archive before selecting any control or oracle."""

    def __init__(self, *, phase, archive_relative, archive_sha256, manifest_sha256,
                 expectations_sha256, fixtures_sha256, case_count):
        self.phase = phase
        self.identities = {"archive": archive_sha256, "manifest": manifest_sha256,
                           "expectations": expectations_sha256, "fixtures": fixtures_sha256}
        archive = REPO / archive_relative
        info = archive.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or any(p.is_symlink() for p in (archive, *archive.parents)):
            raise AssertionError("Frozen archive is not a canonical single-link regular file")
        raw = archive.read_bytes()
        if sha256(raw) != archive_sha256:
            raise AssertionError("Adopted archive identity changed")
        self.payload = {}
        with zipfile.ZipFile(io.BytesIO(raw)) as source:
            names = source.namelist()
            if len(names) != len(set(names)) or source.testzip() is not None:
                raise AssertionError("Frozen archive has duplicate names or a CRC failure")
            for name in names:
                parts = PurePosixPath(safe_name(name)).parts
                if len(parts) < 2 or parts[0] != "candidate001":
                    raise AssertionError("Unexpected archive root")
                entry = source.getinfo(name)
                mode = entry.external_attr >> 16
                if entry.is_dir() or stat.S_ISLNK(mode) or mode & 0o111:
                    raise AssertionError("Frozen payload is not inert regular-file data")
                self.payload[str(PurePosixPath(*parts[1:]))] = source.read(name)
        for name, expected in (("CANDIDATE-MANIFEST.json", manifest_sha256),
                               ("EXPECTATIONS.json", expectations_sha256),
                               ("FIXTURE-MANIFEST.json", fixtures_sha256)):
            if sha256(self.payload[name]) != expected:
                raise AssertionError("Independently selected frozen identity differs: " + name)
        manifest = json.loads(self.payload["CANDIDATE-MANIFEST.json"])
        self.rows = {safe_name(row["path"]): row for row in manifest["files"]}
        if len(self.rows) != len(manifest["files"]) or set(self.payload) != set(self.rows) | {"CANDIDATE-MANIFEST.json"}:
            raise AssertionError("Frozen complete payload inventory differs")
        for name, row in self.rows.items():
            data = self.payload[name]
            if len(data) != byte_count(row) or sha256(data) != row["sha256"] or int(row["mode"], 8) & 0o111:
                raise AssertionError("Frozen payload bytes or inert mode differ: " + name)
        self.fixtures = json.loads(self.payload["FIXTURE-MANIFEST.json"])["files"]
        for row in self.fixtures:
            if self.rows[row["path"]] != row or row["mode"] != "0o600":
                raise AssertionError("Fixture manifest differs from frozen candidate")
        controls = json.loads(self.payload["CONTROLS.json"])["cases"]
        self.cases = {row["id"]: row for row in controls}
        self.expectations = json.loads(self.payload["EXPECTATIONS.json"])["cases"]
        if len(self.cases) != case_count or len(controls) != case_count or set(self.cases) != set(self.expectations):
            raise AssertionError("Frozen case/oracle inventory differs")
        for row in controls:
            context = self.context(row)
            if context["case_id"] != row["id"] or context["route"] != row["route"] or context["operational"] is not False:
                raise AssertionError("Frozen context/route binding differs")

    def context(self, row):
        return json.loads(self.payload[row.get("input", row.get("context"))])

    def materialize(self, directory):
        directory.mkdir(mode=0o700)
        for name, raw in self.payload.items():
            target = directory / name
            target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            with target.open("xb") as stream:
                stream.write(raw)
            target.chmod(int(self.rows[name]["mode"], 8) if name in self.rows else 0o600)
            if target.read_bytes() != raw or target.stat().st_nlink != 1:
                raise AssertionError("Materialized frozen bytes changed")

    def image(self, directory, descriptor):
        name = safe_name(descriptor["path"])
        row = self.rows[name]
        if row != descriptor:
            raise AssertionError("Per-case image differs from the frozen manifest")
        path = directory / name
        raw = path.read_bytes()
        if len(raw) != byte_count(descriptor) or sha256(raw) != descriptor["sha256"] or oct(stat.S_IMODE(path.stat().st_mode)) != "0o600":
            raise AssertionError("Consumed inert image differs")
        return path


class SentinelRuntimeError(RuntimeError):
    pass


class MetadataProbe:
    """Observe the real opened descriptor and inject only at reached I/O seams."""

    def __init__(self, image=None, fault=None):
        self.image, self.fault = image, fault or {}
        self.opened, self.closed, self.reads, self.checkpoints, self.reader_routes = [], [], [], [], []
        self.active_checkpoint, self.final_identity, self.fault_reached = None, False, None
        self.check_calls, self.binding_calls = 0, 0
        kind = self.fault.get("exception", self.fault.get("type"))
        if kind == "HostInspectionError":
            self.sentinel = inspection.HostInspectionError(
                self.fault["category"], self.fault.get("reason", self.fault.get("message")),
                details=deepcopy(self.fault["details"]))
        elif kind == "OSError":
            self.sentinel = OSError(self.fault["message"])
        elif kind == "SentinelRuntimeError":
            self.sentinel = SentinelRuntimeError("p16 callback sentinel")
        else:
            self.sentinel = RuntimeError(self.fault.get("message", "p16 callback sentinel"))
        self.sentinel_details = deepcopy(getattr(self.sentinel, "details", None))

    def check(self):
        self.check_calls += 1
        at = self.fault.get("at")
        callback = self.fault.get("kind") == "callback" or "type" in self.fault
        if callback and (at == self.active_checkpoint or
                         (at == "before_header_pread" and self.opened and not self.reads)):
            self.fault_reached = at
            raise self.sentinel

    def enter(self, stack):
        original_open, original_close, original_pread = os.open, os.close, os.pread
        original_fstat, original_lstat = os.fstat, Path.lstat
        original_checkpoint = inspection._libc_metadata_checkpoint

        def opened(path, *args, **kwargs):
            if self.image is None or str(path) != str(self.image):
                raise AssertionError("Unexpected nonfixture file open: " + str(path))
            fd = original_open(path, *args, **kwargs)
            self.opened.append(fd)
            return fd

        def closed(fd):
            self.closed.append(fd)
            return original_close(fd)

        def pread(fd, size, offset):
            self.reads.append({"fd": fd, "offset": offset, "size": size})
            if self.fault.get("offset") == offset:
                kind = self.fault.get("kind")
                if kind == "pread_exception":
                    self.fault_reached = "pread_exception"
                    raise self.sentinel
                if kind == "pread_short":
                    self.fault_reached = "pread_short"
                    return original_pread(fd, size, offset)[:-self.fault["remove_last_bytes"]]
            return original_pread(fd, size, offset)

        def changed(info):
            fields = {name: getattr(info, name) for name in
                      ("st_dev", "st_ino", "st_mode", "st_nlink", "st_size", "st_mtime_ns", "st_ctime_ns")}
            fields[self.fault["field"]] += self.fault["delta"]
            return SimpleNamespace(**fields)

        def fstat(fd):
            value = original_fstat(fd)
            if self.final_identity and fd in self.opened and self.fault.get("at") == "final_fstat":
                self.fault_reached = "final_fstat"
                return changed(value)
            return value

        def lstat(path, *args, **kwargs):
            value = original_lstat(path, *args, **kwargs)
            if self.final_identity and path == self.image and self.fault.get("at") == "final_lstat":
                self.fault_reached = "final_lstat"
                return changed(value)
            return value

        def checkpoint(check, stage):
            self.checkpoints.append(stage)
            self.active_checkpoint = stage
            if stage == "before_final_elf_identity":
                self.final_identity = True
            try:
                return original_checkpoint(check, stage)
            finally:
                self.active_checkpoint = None

        for name, operation in (("open", opened), ("close", closed), ("pread", pread), ("fstat", fstat)):
            stack.enter_context(patch.object(inspection.os, name, operation))
        stack.enter_context(patch.object(Path, "lstat", lstat))
        stack.enter_context(patch.object(inspection, "_libc_metadata_checkpoint", checkpoint))
        for symbol, route in (("read_elf_metadata", "legacy_public_metadata"),
                              ("_read_origin_elf_metadata", "python_origin_metadata"),
                              ("_read_libc_plt_elf_metadata", "libc_plt_metadata"),
                              ("_read_libc_static_tls_elf_metadata", "static_tls_metadata")):
            original = getattr(inspection, symbol)
            def reader(*args, _original=original, _route=route, **kwargs):
                self.reader_routes.append(_route)
                return _original(*args, **kwargs)
            stack.enter_context(patch.object(inspection, symbol, reader))

    def record(self):
        return {"opened_descriptors": self.opened, "closed_descriptors": self.closed,
                "preads": self.reads, "checkpoints": self.checkpoints, "check_calls": self.check_calls,
                "fault_boundary_reached": self.fault_reached, "reader_routes": self.reader_routes,
                "binding_primitive_calls": self.binding_calls}


def call_bindings(context):
    return inspection._check_libc_plt_bindings(**{key: deepcopy(context[key]) for key in BINDING_FIELDS})


def binding_projection(context, selection):
    """Translate only declared logical observations into the real caller shapes."""
    c = deepcopy(context)
    python = c["python_descriptor"]
    forbidden = c["forbidden_resolved_paths"]
    metadata = {"class": 64, "endian": "little", "machine": 62, "type": 3,
                "interpreter": c["actual_python_interpreter"], "needed": c["actual_python_needed"],
                "soname": None, "rpath": ["$ORIGIN/../lib"], "runpath": []}
    origin = {"subject": python, "needed_names": sorted(set(c["actual_python_needed"])), "variants": []}
    resolution = {"profile": selection["profile"], "origin_rpath": origin,
                  "libc_plt": {"schema": LIBC_SCHEMA, "subject": c["subject"], "loader": c["loader"]},
                  "images": [
                      {"file": python, "metadata": metadata, "resolved_needed": c["python_resolved_needed"]},
                      {"file": c["libc_image_descriptor"], "metadata": {"needed": []}, "resolved_needed": {}},
                      {"file": c["loader_image_descriptor"], "metadata": {"needed": []}, "resolved_needed": {}}]}
    roles = {"python": python["path"], "node": "/synthetic/node", "ldd": "/synthetic/ldd",
             "inspector_interpreter": "/synthetic/shell", "elf_interpreter": c["runtime_interpreter"],
             "inspector_runtime": c["dependency_role_names"], "shared_libraries": []}
    runtime = {"executable": python, "interpreter": c["runtime_interpreter"], "files": c["runtime_files"],
               "aliases": c["runtime_aliases"], "extension_files": forbidden}
    plan = {"schema": selection["plan_schema"],
            "author": {"python_descriptor": python, "git_descriptor": {"path": "/synthetic/git"},
                       "entry_point": "/synthetic/inspection.py"},
            "host_static": {"files": c["host_files"], "aliases": c["host_aliases"], "roles": roles,
                            "resolution": resolution}}
    return plan, runtime, origin, metadata


class FrozenLibcCaseMixin:
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        retained = os.environ.get("ONTOKIN_LIBC_RETAIN_ROOT")
        if retained:
            cls.directory = Path(retained) / cls.corpus.phase
            cls.directory.mkdir(mode=0o700, parents=True, exist_ok=False)
        else:
            temporary = tempfile.TemporaryDirectory(prefix="ontokin-libc-" + cls.corpus.phase + "-")
            cls.addClassCleanup(temporary.cleanup)
            cls.directory = Path(temporary.name)
        cls.inputs = cls.directory / "candidate001"
        cls.corpus.materialize(cls.inputs)
        cls.observations = cls.directory / "observations"
        cls.observations.mkdir(mode=0o700)
        sources = {Path(inspection.__file__), Path(__file__), Path(sys.modules[cls.__module__].__file__)}
        cls.source_identities = [{"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path.read_bytes())}
                                 for path in sorted(sources)]
        write_document(cls.directory / "RUN-INPUTS.json", {
            "phase": cls.corpus.phase, "frozen_identities": cls.corpus.identities, "sources": cls.source_identities,
            "case_count": len(cls.corpus.cases), "python": sys.version, "executable": sys.executable,
            "whole_plan_or_host_admission": False, "historical_N57": "external_only_not_executed_not_skipped",
            "full_inert_candidate_materialized": True})

    def invoke(self, context, probe):
        route = context["route"]
        image = probe.image
        options = {"check": probe.check, "require_interpreter": context.get("require_interpreter", False)}
        if route == "legacy_public_metadata":
            return inspection.read_elf_metadata(image, **options)
        if route == "legacy_literal_plan_reader":
            return inspection._read_plan_elf_metadata(image, None, **options)
        if route in ("legacy_origin_plan_reader", "legacy_origin_other_reader"):
            subject = context.get("origin_subject_path", str(image.parent / "distinct-python"))
            return inspection._read_plan_elf_metadata(image, {"subject": {"path": subject}}, **options)
        if route in ("libc_plt_metadata", "p16_libc_plt_metadata", "metadata_fault"):
            return inspection._read_libc_plt_elf_metadata(image, **options)
        if route in ("static_tls_metadata", "new_metadata_fault"):
            return inspection._read_libc_static_tls_elf_metadata(image, **options)
        if route == "new_profile_rule":
            selection = context.get("selection", context)
            resolution = {"profile": selection["profile"]}
            if "libc_plt" in context:
                resolution["libc_plt"] = context["libc_plt"]
            selector = (inspection._select_libc_plt_profile if self.corpus.phase == "p16"
                        else inspection._select_libc_static_tls_profile)
            return selector(selection["plan_schema"], resolution)
        if route in ("binding_relations", "new_binding_relations"):
            if route == "new_binding_relations":
                inspection._select_libc_static_tls_profile(context["selection"]["plan_schema"], {
                    "profile": context["selection"]["profile"],
                    "libc_plt": {"schema": LIBC_SCHEMA, "subject": context["subject"], "loader": context["loader"]}})
            probe.binding_calls += 1
            return call_bindings(context)
        if route == "external_digest":
            return inspection._check_plan_digest(context["actual_digest"], context["expected_digest"])
        if route in ("recheck_boundary", "new_recheck_boundary"):
            # Before is a pure mocked relation; after reaches the actual policy
            # constructor through actual _recheck and _check_resolution calls.
            call_bindings(context["before"])
            selection = context.get("selection", {"plan_schema": P16_SCHEMA, "profile": P16_PROFILE})
            plan, runtime, origin, metadata = binding_projection(context["after"], selection)
            validated = SimpleNamespace(plan=plan, descriptor={"path": "/synthetic/plan.json", "sha256": "0" * 64,
                                        "size_bytes": 0, "mode": "0o600"}, _git_state={}, _helpers=None, _metadata={})
            original_binding = inspection._check_libc_plt_bindings
            def binding(**kwargs):
                probe.binding_calls += 1
                return original_binding(**kwargs)
            def python_observation(path, policy, **kwargs):
                self.assertEqual(path, context["after"]["python_descriptor"]["path"])
                return deepcopy(metadata)
            with ExitStack() as stack:
                # These mocks expose the newly specified binding fault, not a
                # claim that earlier actual-host prerequisites were satisfied.
                for name, value in (("_bound", None), ("_check_source_files", {}),
                                    ("_check_author_runtime", runtime), ("_check_host_static", None),
                                    ("_check_author_host_bindings", None), ("_prepare_origin_policy", inspection._freeze(origin))):
                    stack.enter_context(patch.object(inspection, name, return_value=value))
                stack.enter_context(patch.object(inspection, "_read_plan_elf_metadata", python_observation))
                stack.enter_context(patch.object(inspection, "_check_libc_plt_bindings", binding))
                stack.enter_context(patch.object(inspection, "_git_state", side_effect=AssertionError("Binding fault must precede Git witness")))
                return inspection._recheck(validated, check=probe.check)
        if route == "new_plan_reader_dispatch":
            logical = next(self.corpus.context(row) for row in self.corpus.cases.values()
                           if row["route"] == "new_binding_relations")
            descriptor = deepcopy(logical["subject"])
            relation = context["subject_relation"]
            if relation == "requested_fixture_is_bound_libc":
                descriptor["path"] = str(image)
            elif relation == "requested_fixture_is_other_non_python_image":
                descriptor["path"] = str(image.parent / "distinct-libc")
            else:
                raise AssertionError("Unknown frozen dispatch relation")
            # Deliberately mocked internal policy; no operational pin or _bound
            # success is claimed for the fixture at this private dispatch seam.
            policy = inspection._freeze({"schema": context["selection"]["plan_schema"],
                                         "subject": descriptor, "loader": logical["loader"]})
            return inspection._read_plan_elf_metadata(image, {"subject": {"path": str(image.parent / "distinct-python")}},
                                                       libc_policy=policy, **options)
        raise AssertionError("Unknown frozen route: " + route)

    def assert_error(self, error, expected, probe):
        self.assertIsInstance(error, inspection.HostInspectionError)
        for key in ("code", "reason", "state", "details"):
            self.assertEqual(getattr(error, key), expected[key])
        cause = expected["cause"]
        if cause is None:
            self.assertIsNone(error.cause)
        elif "code" in cause:
            self.assert_error(error.cause, cause, probe)
        else:
            self.assertEqual(type(error.cause).__name__, cause["type"])
            self.assertEqual(str(error.cause), cause["message"])
            if cause["same_exception_object"]:
                self.assertIs(error.cause, probe.sentinel)

    def run_case(self, case):
        context = self.corpus.context(case)
        expected = self.corpus.expectations[case["id"]]
        image = self.corpus.image(self.inputs, context["image"]) if "image" in context else None
        probe = MetadataProbe(image, context.get("fault"))
        value, error, passed = None, None, False
        record = {"case_id": case["id"], "route": case["route"], "context": context, "frozen_expectation": expected,
                  "sources": self.source_identities, "actual_file_binding_proved": False,
                  "operational_plan_accepted": False, "host_qualified": False}
        try:
            with ExitStack() as stack:
                def forbidden(*args, **kwargs):
                    raise AssertionError("Inert controls must not launch processes or load helpers")
                process = stack.enter_context(patch("subprocess.Popen", side_effect=forbidden))
                helper = stack.enter_context(patch.object(inspection, "_load_helpers", side_effect=forbidden))
                git = stack.enter_context(patch.object(inspection, "_check_git", side_effect=forbidden))
                probe.enter(stack)
                try:
                    value = self.invoke(context, probe)
                except Exception as exc:
                    error = exc
            self.assertEqual(process.call_count, 0)
            self.assertEqual(helper.call_count, 0)
            self.assertEqual(git.call_count, 0)
            self.assertEqual(len(probe.opened), expected["opened_descriptor_close_count"])
            self.assertEqual(probe.closed, probe.opened)
            self.assertEqual(len(set(probe.opened)), len(probe.opened))
            outcome = expected["outcome"]
            if outcome == "typed_refusal":
                self.assert_error(error, expected, probe)
            elif outcome in ("callback_exception", "same_callback_exception"):
                self.assertIs(error, probe.sentinel)
                self.assertEqual(type(error).__name__, expected.get("exception_type", expected.get("type")))
                self.assertEqual(getattr(error, "details", None), probe.sentinel_details)
                if "message" in expected:
                    self.assertEqual(str(error), expected["message"])
                if "original_details_unchanged" in expected:
                    self.assertEqual(error.details, expected["original_details_unchanged"])
            else:
                self.assertIsNone(error, repr(error))
                if outcome == "metadata_returned":
                    self.assertEqual(value, expected["metadata"])
                elif outcome in ("new_branch_selected_only", "new_fixed_profile_selected_only"):
                    self.assertEqual(value, context["libc_plt"])
                elif outcome == "mocked_binding_relations_accepted_only":
                    self.assertIsNone(value)
                else:
                    self.fail("Unknown frozen expected outcome")
            if context.get("fault"):
                fault = context["fault"]
                self.assertEqual(probe.fault_reached, fault.get("at", fault.get("kind")))
            if "callback_boundary_reached" in expected:
                self.assertEqual(probe.fault_reached, expected["callback_boundary_reached"])
            if context.get("require_actual_new_binding_primitive_call"):
                self.assertEqual(probe.binding_calls, 1)
            if "raw_libc_parser_calls" in expected or "raw_libc_parser_calls_after_fault" in expected:
                self.assertEqual(sum(name in ("libc_plt_metadata", "static_tls_metadata") for name in probe.reader_routes), 0)
            if "reader_route" in expected:
                self.assertEqual(probe.reader_routes, [expected["reader_route"]])
            # Every actual pread must stay within the independently bound small
            # fixture. Maximum opaque PLT values cannot create a read range.
            if image is not None:
                for row in probe.reads:
                    self.assertIn(row["fd"], probe.opened)
                    self.assertLessEqual(row["offset"] + row["size"], byte_count(context["image"]))
            passed = True
        finally:
            record.update(probe.record())
            record.update(passed=passed, observed_metadata=value if isinstance(value, dict) and "class" in value else None,
                          observed_error=inspection._failure(error),
                          same_callback_exception=error is probe.sentinel if context.get("fault") else None,
                          same_io_cause=getattr(error, "cause", None) is probe.sentinel if context.get("fault") else None)
            write_document(self.observations / (case["id"] + ".json"), record)


def install_cases(cls):
    for case in cls.corpus.cases.values():
        def method(self, _case=case):
            self.run_case(_case)
        method.__name__ = "test_" + case["id"]
        method.__doc__ = case.get("mutation", case.get("purpose", case["route"]))
        setattr(cls, method.__name__, method)
    return cls


CORPUS = FrozenCorpus(
    phase="p16",
    archive_relative="docs/engineering/localized-repair-c271/libc-tags-p16/design/CANDIDATE001.zip",
    archive_sha256="05d1cbe971678b8f505795e436f2bd096b81848f68b4f9da6adc64392f6fb5af",
    manifest_sha256="61b18ceb15d3ee05d3022c60941ccbbce9c3e08bac148c7750da9f6588091156",
    expectations_sha256="33a17cc66604f8b57be88dae7dd05a4bec066c0eaa191fc08400cfc79e18137e",
    fixtures_sha256="20a025e16507fd334c1bf18dbf1f47a508e1d7d4efe64aca10a86a89c43c0cd4",
    case_count=73,
)


@install_cases
class LibcPltFrozenTests(FrozenLibcCaseMixin, unittest.TestCase):
    corpus = CORPUS


if __name__ == "__main__":
    unittest.main()
