"""C209 CPU controls; package modules and external receipts are synthetic files."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from prototypes.static_tray_admission_c201 import input_lock, readback_binding as rb
from prototypes.static_tray_admission_c201 import readback_entries as module, transaction as tx
from prototypes.static_tray_admission_c201.schedule import canonical
from tests.test_static_tray_admission_c201_transaction import TransactionFixture


ROOT = Path(__file__).resolve().parents[1]


class EntryFixture:
    """Independently repinned synthetic lock; never an executable production lock."""

    def __init__(self, root):
        self.native = TransactionFixture(root)
        self.inputs = self.native.inputs
        lock = self.inputs.lock
        old = lock["roles"]["node_packages"][0]
        del lock["inputs"][old]
        del lock["dependencies"][old]
        self.keys = {}
        rows = {
            "validator_package": ("validator/package.json", canonical({"name": "gltf-validator", "version": "2.0.0-dev.3.10", "main": "index.js"})),
            "validator_entry": ("validator/index.js", b"// Synthetic validator entry; never executed\n"),
            "validator_transitive": ("validator/gltf_validator.dart.js", b"// Synthetic validator transitive file\n"),
            "three_package": ("three/package.json", canonical({"name": "three", "version": "0.186.1", "type": "module", "exports": {
                "./webgpu": "./build/three.webgpu.js", "./examples/jsm/*": "./examples/jsm/*"}})),
            "three_entry": ("three/build/three.webgpu.js", b"// Synthetic Three entry; never executed\n"),
            "gltf_loader_entry": ("three/examples/jsm/loaders/GLTFLoader.js", b"// Synthetic GLTFLoader; never executed\n"),
        }
        for role, (relative, raw) in rows.items():
            self.keys[role] = self.add(relative, raw, "host")
        lock["roles"]["node_packages"] = list(self.keys.values())
        helper = self.add(module.HELPER_PATH, (ROOT / module.HELPER_PATH).read_bytes(), "repository")
        base = self.add(module.BASE_HELPER_PATH, (ROOT / module.BASE_HELPER_PATH).read_bytes(), "repository")
        for role, lock_role in (("module_loader", "node_loader"), ("probe", "admission_node_probe"),
                                ("wrapper", "admission_format_check")):
            self.keys[role] = lock["roles"][lock_role][0]
        self.keys["binding_helper"] = helper
        graph = lock["dependencies"]
        graph[helper] = [base]
        graph[self.keys["wrapper"]] = [helper, self.keys["probe"], self.keys["module_loader"], lock["roles"]["node_executable"][0]]
        for origin, targets in {
            "probe": ["validator_package", "validator_entry", "three_package", "three_entry", "gltf_loader_entry"],
            "module_loader": ["three_entry", "three_package"],
            "validator_entry": ["validator_package", "validator_transitive"],
            "three_entry": ["three_package"], "gltf_loader_entry": ["three_entry", "three_package"],
        }.items():
            graph[self.keys[origin]] = [self.keys[target] for target in targets]
        self.seal()

    def add(self, relative, raw, root):
        directory = self.inputs.repo if root == "repository" else self.inputs.host
        path = directory / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        key = root + ":" + relative
        self.inputs.lock["inputs"][key] = self.inputs.binding(path, root)
        self.inputs.lock["dependencies"][key] = []
        return key

    def path(self, role):
        row = self.inputs.lock["inputs"][self.keys[role]]
        return (self.inputs.repo if row["root"] == "repository" else self.inputs.host) / row["path"]

    def metadata(self, role, change):
        path = self.path(role)
        value = json.loads(path.read_bytes())
        change(value)
        path.write_bytes(canonical(value))
        self.inputs.lock["inputs"][self.keys[role]] = self.inputs.binding(path, "host")

    def seal(self):
        lock = self.inputs.lock
        lock["source"]["files"] = sorted(k for k, row in lock["inputs"].items() if row["root"] == "repository")
        digest = input_lock.closure_digest(lock)
        self.inputs.context = replace(self.inputs.context, closure_sha256=digest)
        for row in lock["gate_receipts"].values():
            path = self.inputs.host / row["path"]
            receipt = json.loads(path.read_bytes())
            receipt["closure_sha256"] = digest
            path.write_bytes(canonical(receipt))
            row.update(self.inputs.binding(path, "host"))
        self.inputs.repin()
        self.native.session = tx.bind_transactions(self.inputs.lock_path, self.inputs.approval_path,
                                                   context=self.inputs.context)

    def bind(self):
        return module.bind_entry_readbacks(self.native.session)

    def prepare(self):
        self.bindings = self.bind()
        self.accepted = self.native.accept("A01")
        return module.prepare_entry_readback(self.bindings, "A01", accepted=self.accepted)


class EntryFixtureCase(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="ontokin-c209-entry-")
        self.addCleanup(temp.cleanup)
        for target in ("subprocess.Popen", "os.fork", "os.system", "os.posix_spawn", "os.posix_spawnp"):
            self.enterContext(mock.patch(target, side_effect=AssertionError("No child may start")))
        self.fixture = EntryFixture(temp.name)

    def reject(self, operation, code=None, state="REJECTED"):
        with self.assertRaises(module.EntryBindingError) as caught:
            operation()
        if code:
            self.assertEqual(caught.exception.code, "C201-READBACK-ENTRY-" + code)
        self.assertEqual(caught.exception.state, state)
        return caught.exception

    def mutate(self, operation, code=None):
        operation()
        self.fixture.seal()
        self.reject(self.fixture.bind, code)


class EntryGraphControls(EntryFixtureCase):
    def test_binding_validates_real_files_without_output_or_authority(self):
        before = sorted(str(p) for p in self.fixture.inputs.base.rglob("*"))
        self.fixture.bind()
        self.assertEqual(before, sorted(str(p) for p in self.fixture.inputs.base.rglob("*")))

    def test_wrong_validator_version(self):
        self.mutate(lambda: self.fixture.metadata("validator_package", lambda p: p.update(version="2.0.0-dev.3.9")), "PACKAGE")

    def test_wrong_three_version(self):
        self.mutate(lambda: self.fixture.metadata("three_package", lambda p: p.update(version="0.185.0")), "PACKAGE")

    def test_wrong_metadata_name(self):
        self.mutate(lambda: self.fixture.metadata("validator_package", lambda p: p.update(name="other-validator")), "PACKAGE")

    def test_wrong_validator_main(self):
        self.mutate(lambda: self.fixture.metadata("validator_package", lambda p: p.update(main="other.js")), "SELECTOR")

    def test_aliased_validator_main(self):
        self.mutate(lambda: self.fixture.metadata("validator_package", lambda p: p.update(main="./index.js")), "SELECTOR")

    def test_validator_conditional_exports(self):
        self.mutate(lambda: self.fixture.metadata("validator_package", lambda p: p.update(exports={".": "./other.js"})), "SELECTOR")

    def test_wrong_three_module_type(self):
        self.mutate(lambda: self.fixture.metadata("three_package", lambda p: p.update(type="commonjs")), "SELECTOR")

    def test_wrong_three_webgpu_export(self):
        self.mutate(lambda: self.fixture.metadata("three_package", lambda p: p["exports"].update({"./webgpu": "./build/three.module.js"})), "SELECTOR")

    def test_ambiguous_three_export(self):
        self.mutate(lambda: self.fixture.metadata("three_package", lambda p: p["exports"].update({"./webgpu": {"import": "./build/three.webgpu.js"}})), "SELECTOR")

    def test_wrong_loader_export(self):
        self.mutate(lambda: self.fixture.metadata("three_package", lambda p: p["exports"].update({"./examples/jsm/*": "./other/*"})), "SELECTOR")

    def test_duplicate_validator_package(self):
        def change():
            key = self.fixture.add("duplicate/package.json", self.fixture.path("validator_package").read_bytes(), "host")
            self.fixture.inputs.lock["roles"]["node_packages"].append(key)
        self.mutate(change, "PACKAGE")

    def test_duplicate_json_key(self):
        path = self.fixture.path("validator_package")
        path.write_bytes(b'{"name":"gltf-validator","version":"2.0.0-dev.3.10","main":"index.js","main":"index.js"}')
        self.fixture.inputs.lock["inputs"][self.fixture.keys["validator_package"]] = self.fixture.inputs.binding(path, "host")
        self.fixture.seal()
        self.reject(self.fixture.bind, "BINDING")

    def test_metadata_not_in_package_role(self):
        def change():
            key = self.fixture.keys["validator_package"]
            self.fixture.inputs.lock["roles"]["node_packages"].remove(key)
        self.mutate(change, "PACKAGE")

    def test_entry_wrong_host_role(self):
        def change():
            key = self.fixture.keys["three_entry"]
            self.fixture.inputs.lock["roles"]["node_packages"].remove(key)
            self.fixture.inputs.lock["roles"]["shared_libraries"].append(key)
        self.mutate(change, "ROLE")

    def test_package_aliases_other_role(self):
        self.mutate(lambda: self.fixture.inputs.lock["roles"]["shared_libraries"].append(self.fixture.keys["three_entry"]), "ROLE")

    def test_globally_reachable_not_probe_dependency(self):
        self.mutate(lambda: self.fixture.inputs.lock["dependencies"][self.fixture.keys["probe"]].remove(self.fixture.keys["validator_entry"]), "GRAPH")

    def test_transitive_only_not_direct_probe_dependency(self):
        def change():
            graph, keys = self.fixture.inputs.lock["dependencies"], self.fixture.keys
            graph[keys["probe"]].remove(keys["validator_entry"])
            graph[keys["validator_package"]].append(keys["validator_entry"])
        self.mutate(change, "GRAPH")

    def test_loader_missing_three_direct_edge(self):
        self.mutate(lambda: self.fixture.inputs.lock["dependencies"][self.fixture.keys["module_loader"]].remove(self.fixture.keys["three_entry"]), "GRAPH")

    def test_gltfloader_missing_three_edge(self):
        self.mutate(lambda: self.fixture.inputs.lock["dependencies"][self.fixture.keys["gltf_loader_entry"]].remove(self.fixture.keys["three_entry"]), "GRAPH")

    def test_entry_missing_metadata_edge(self):
        self.mutate(lambda: self.fixture.inputs.lock["dependencies"][self.fixture.keys["validator_entry"]].remove(self.fixture.keys["validator_package"]), "GRAPH")

    def test_helper_only_globally_reachable(self):
        def change():
            graph, keys = self.fixture.inputs.lock["dependencies"], self.fixture.keys
            graph[keys["wrapper"]].remove(keys["binding_helper"])
            graph[self.fixture.inputs.lock["roles"]["admission_coordinator"][0]].append(keys["binding_helper"])
        self.mutate(change, "GRAPH")

    def test_wrong_helper_bytes_even_when_repinned(self):
        path = self.fixture.path("binding_helper")
        path.write_text("# Wrong source in a valid repinned fixture\n")
        self.fixture.inputs.lock["inputs"][self.fixture.keys["binding_helper"]] = self.fixture.inputs.binding(path, "repository")
        self.fixture.seal()
        self.reject(self.fixture.bind, "HELPER")

    def test_node_dependency_wrong_role(self):
        self.mutate(lambda: self.fixture.inputs.lock["dependencies"][self.fixture.keys["probe"]].append("host:shared_libraries"), "GRAPH")

    def test_node_dependency_outside_package_roots(self):
        def change():
            key = self.fixture.add("unrelated/escape.js", b"// unrelated\n", "host")
            self.fixture.inputs.lock["roles"]["node_packages"].append(key)
            self.fixture.inputs.lock["dependencies"][self.fixture.keys["validator_entry"]].append(key)
        self.mutate(change, "PATH")

    def test_changed_transitive_bytes(self):
        self.fixture.path("validator_transitive").write_text("changed\n")
        self.reject(self.fixture.bind, "BINDING")

    def test_missing_entry_file(self):
        self.fixture.path("gltf_loader_entry").unlink()
        self.reject(self.fixture.bind, "BINDING")

    def test_symlink_entry_rejected(self):
        path = self.fixture.path("three_entry")
        target = path.with_name("target.js")
        path.rename(target)
        path.symlink_to(target.name)
        self.reject(self.fixture.bind, "BINDING")

    def test_hardlink_entry_rejected(self):
        path = self.fixture.path("three_entry")
        os.link(path, path.with_name("alias.js"))
        self.reject(self.fixture.bind, "BINDING")

    def test_unsafe_input_path_rejected_by_existing_lock(self):
        key = self.fixture.keys["three_entry"]
        self.fixture.inputs.lock["inputs"][key]["path"] = "three/build/../build/three.webgpu.js"
        with self.assertRaises(tx.TransactionError):
            self.fixture.seal()


class PreparedEntryControls(EntryFixtureCase):
    def setUp(self):
        super().setUp()
        self.prepared = self.fixture.prepare()
        self.job = json.loads(self.prepared.job_bytes)
        self.pointer = Path(self.fixture.inputs.lock["stores"]["A01"]) / "state.json"
        self.original_pointer = self.pointer.read_bytes()
        self.addCleanup(lambda: self.assertEqual(self.pointer.read_bytes(), self.original_pointer))

    def reject(self, operation, code=None, state="REJECTED"):
        result = super().reject(operation, code, state)
        if hasattr(self, "pointer"):
            self.assertEqual(self.pointer.read_bytes(), self.original_pointer)
        return result

    def test_job_version_named_bindings_graph_and_false_authority(self):
        self.assertEqual(self.job["schema"], module.JOB_SCHEMA)
        entries = self.job["dependency_entries"]
        self.assertEqual(entries["schema"], module.ENTRIES_SCHEMA)
        self.assertEqual(entries["closure_sha256"], self.fixture.inputs.context.closure_sha256)
        self.assertEqual(len(entries["named"]), 9)
        self.assertEqual(entries["packages"]["three"]["revision"], "186")
        for name, row in entries["files"].items():
            self.assertEqual(row["input"], name)
            self.assertEqual(hashlib.sha256(Path(row["path"]).read_bytes()).hexdigest(), row["sha256"])
        for key in ("authenticated_execution", "node_start_authorized", "native_start_authorized",
                    "native_readiness", "admission_completed", "next_slot_authorized"):
            self.assertFalse(getattr(self.prepared, key))
            self.assertIs(self.job[key], False)
        self.assertIs(entries["ambient_imports"], False)
        self.assertIs(entries["node_resolution_authorized"], False)

    def test_inspection_returns_copy(self):
        observed = module.inspect_entry_readback_job(self.prepared)
        observed["dependency_entries"]["named"].clear()
        self.assertEqual(module.inspect_entry_readback_job(self.prepared), self.job)

    def test_job01_verifier_rejects_job02_handle(self):
        with self.assertRaises(rb.ReadbackError):
            rb.inspect_readback_job(self.prepared)
        with self.assertRaises(rb.ReadbackError):
            rb.verify_readback_result(self.prepared, process={"passed": True})
        self.assertEqual(rb.JOB_SCHEMA, "ontokin.c201.readback-job/0.1")

    def test_reconstructed_handle(self):
        self.reject(lambda: module.inspect_entry_readback_job(replace(self.prepared)), "REPLAY")

    def test_forged_bindings(self):
        self.reject(lambda: module.EntryReadbackBindings(self.fixture.native.session, None), "BINDING")

    def test_repeated_preparation(self):
        self.reject(lambda: module.prepare_entry_readback(self.fixture.bindings, "A01", accepted=self.fixture.accepted), "REPLAY")

    def test_changed_job_bytes(self):
        changed = deepcopy(self.job)
        changed["dependency_entries"]["named"]["three_entry"]["sha256"] = "0" * 64
        Path(self.job["outputs"]["job"]).write_bytes(canonical(changed))
        self.reject(lambda: module.inspect_entry_readback_job(self.prepared), "JOB")

    def test_changed_package_after_preparation(self):
        self.fixture.path("three_package").write_bytes(b'{}')
        self.reject(lambda: module.inspect_entry_readback_job(self.prepared), "BINDING")

    def test_changed_helper_after_preparation(self):
        self.fixture.path("binding_helper").write_bytes(b'# changed\n')
        self.reject(lambda: module.inspect_entry_readback_job(self.prepared), "BINDING")

    def test_stale_lock_digest(self):
        session = self.fixture.native.session
        session._context = replace(session._context, lock_sha256="0" * 64)
        self.reject(lambda: module.inspect_entry_readback_job(self.prepared), "BINDING")

    def test_stale_source_in_retained_job(self):
        changed = deepcopy(self.job)
        changed["source"]["commit"] = "0" * 40
        Path(self.job["outputs"]["job"]).write_bytes(canonical(changed))
        self.reject(lambda: module.inspect_entry_readback_job(self.prepared), "JOB")

    def test_stale_source_context(self):
        session = self.fixture.native.session
        session._context = replace(session._context, source_commit="0" * 40)
        self.reject(lambda: module.inspect_entry_readback_job(self.prepared), "BINDING")

    def test_stale_closure_context(self):
        session = self.fixture.native.session
        session._context = replace(session._context, closure_sha256="0" * 64)
        self.reject(lambda: module.inspect_entry_readback_job(self.prepared), "BINDING")

    def test_stale_validation_result(self):
        session = self.fixture.native.session
        session.validation = replace(session.validation, source_tree="0" * 40)
        self.reject(lambda: module.inspect_entry_readback_job(self.prepared), "BINDING")

    def resolve(self, importer, specifier):
        return module.resolve_entry_import(self.prepared, importer=self.fixture.keys[importer], specifier=specifier)

    def test_bare_three_exact_declared_mapping(self):
        self.assertEqual(self.resolve("gltf_loader_entry", "three"), self.job["dependency_entries"]["named"]["three_entry"])

    def test_absolute_named_probe_mapping(self):
        entry = self.job["dependency_entries"]["named"]["validator_entry"]
        self.assertEqual(self.resolve("probe", entry["path"]), entry)

    def test_relative_declared_transitive_mapping(self):
        value = self.resolve("validator_entry", "./gltf_validator.dart.js")
        self.assertEqual(value["input"], self.fixture.keys["validator_transitive"])

    def test_global_input_without_direct_edge_rejected(self):
        self.reject(lambda: self.resolve("validator_entry", "three"), "IMPORT")

    def test_ambient_bare_package_rejected(self):
        self.reject(lambda: self.resolve("probe", "gltf-validator"), "IMPORT")

    def test_package_subpath_rejected(self):
        self.reject(lambda: self.resolve("probe", "three/addons/loaders/GLTFLoader.js"), "IMPORT")

    def test_node_builtin_rejected(self):
        self.reject(lambda: self.resolve("probe", "node:fs"), "IMPORT")

    def test_file_url_rejected(self):
        self.reject(lambda: self.resolve("probe", self.fixture.path("three_entry").as_uri()), "IMPORT")

    def test_url_query_hash_or_encoding_rejected(self):
        for suffix in ("?query=1", "#fragment", "%20"):
            with self.subTest(suffix=suffix):
                self.reject(lambda: self.resolve("probe", str(self.fixture.path("three_entry")) + suffix), "IMPORT")

    def test_extension_inference_rejected(self):
        self.reject(lambda: self.resolve("validator_entry", "./gltf_validator.dart"), "IMPORT")

    def test_cross_package_relative_escape_rejected(self):
        self.reject(lambda: self.resolve("validator_entry", "../three/build/three.webgpu.js"), "IMPORT")

    def test_unknown_importer_rejected(self):
        self.reject(lambda: module.resolve_entry_import(self.prepared, importer="host:unknown", specifier="three"), "IMPORT")

    def test_noncanonical_absolute_path_rejected(self):
        path = str(self.fixture.path("three_entry").parent) + "/../build/three.webgpu.js"
        self.reject(lambda: self.resolve("probe", path), "BINDING")


class PreparationFailureControls(EntryFixtureCase):
    def prepare_failure(self, effect, state="REJECTED"):
        bindings = self.fixture.bind()
        accepted = self.fixture.native.accept("A01")
        pointer = Path(self.fixture.inputs.lock["stores"]["A01"]) / "state.json"
        original = pointer.read_bytes()
        with mock.patch.object(module.tx, "_write", side_effect=effect):
            self.reject(lambda: module.prepare_entry_readback(bindings, "A01", accepted=accepted), state=state)
        self.assertEqual(pointer.read_bytes(), original)
        self.reject(lambda: module.prepare_entry_readback(bindings, "A01", accepted=accepted), "REPLAY")
        self.reject(lambda: module.prepare_entry_readback(bindings, "A02", accepted=accepted), "REPLAY")
        return accepted

    def test_write_failure_stops_without_authority(self):
        self.prepare_failure(OSError("Synthetic write failure"))

    def test_interrupted_write_reports_unknown_and_stops(self):
        self.prepare_failure(KeyboardInterrupt(), "UNKNOWN")

    def test_unknown_after_actual_job_write_retains_exact_bytes(self):
        write = tx._write
        def interrupted(path, raw, **kwargs):
            write(path, raw, **kwargs)
            raise KeyboardInterrupt()
        self.prepare_failure(interrupted, "UNKNOWN")
        path = Path(self.fixture.inputs.lock["outputs"]["A01"]["node"]) / "job.json"
        self.assertEqual(json.loads(path.read_bytes())["schema"], module.JOB_SCHEMA)

    def test_nonempty_stage_stops_and_retains_existing_evidence(self):
        bindings = self.fixture.bind()
        accepted = self.fixture.native.accept("A01")
        path = Path(self.fixture.inputs.lock["outputs"]["A01"]["node"]) / "partial.log"
        path.write_bytes(b"retain original evidence")
        self.reject(lambda: module.prepare_entry_readback(bindings, "A01", accepted=accepted), "OUTPUT")
        self.assertEqual(path.read_bytes(), b"retain original evidence")
        self.reject(lambda: module.prepare_entry_readback(bindings, "A01", accepted=accepted), "REPLAY")


if __name__ == "__main__":
    unittest.main()
