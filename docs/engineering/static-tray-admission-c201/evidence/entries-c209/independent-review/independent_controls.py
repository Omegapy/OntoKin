"""Independent adversarial C209 component controls; no actual dependency runs."""
from __future__ import annotations
import argparse
from contextlib import ExitStack
from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest import mock

SOURCE_ROOT = None
from fixture_support import IndependentFixture
from prototypes.static_tray_admission_c201 import input_lock, readback_binding, transaction
from prototypes.static_tray_admission_c201 import readback_entries as entries
from prototypes.static_tray_admission_c201.schedule import canonical


class Controls(unittest.TestCase):
    observations = []

    def setUp(self):
        self.launches = []
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        def forbidden(*args, **kwargs):
            self.launches.append("attempted")
            raise AssertionError("Child start is forbidden during independent CPU controls")
        for name in ("subprocess.Popen", "os.fork", "os.system", "os.posix_spawn", "os.posix_spawnp", "os.execve"):
            if name.split(".")[0] == "os" and not hasattr(os, name.split(".")[1]):
                continue
            self.stack.enter_context(mock.patch(name, side_effect=forbidden))
        self.temp = self.stack.enter_context(tempfile.TemporaryDirectory(prefix="c209-independent-"))
        self.f = IndependentFixture(self.temp, SOURCE_ROOT)
        self.codes = []

    def tearDown(self):
        self.observations.append({"test": self.id().split(".")[-1], "diagnostics": self.codes,
                                  "attempted_child_starts": len(self.launches)})

    def reject(self, fn):
        pointers = {slot: Path(path) / "state.json" for slot, path in self.f.inputs.lock["stores"].items()}
        before = {slot: path.read_bytes() if path.exists() else None for slot, path in pointers.items()}
        try:
            fn()
        except (input_lock.InputLockError, transaction.TransactionError) as exc:
            self.codes.append(getattr(exc, "code", type(exc).__name__))
            after = {slot: path.read_bytes() if path.exists() else None for slot, path in pointers.items()}
            self.assertEqual(after, before, "Rejected entry operation changed an accepted pointer")
            return
        self.fail("An invalid binding was accepted")

    def change_metadata(self, package, mutation):
        name = self.f.named[package + "_package"]
        value = json.loads(self.f.path(name).read_bytes())
        mutation(value)
        self.f.write(name, canonical(value))
        self.f.reseal()
        self.reject(self.f.bind)

    def test_valid_named_graph(self):
        binding = self.f.bind()
        self.assertIsNotNone(binding)

    def test_validator_wrong_version(self):
        self.change_metadata("validator", lambda x: x.update(version="2.0.0-dev.3.9"))

    def test_validator_wrong_name(self):
        self.change_metadata("validator", lambda x: x.update(name="some-validator"))

    def test_validator_redirected_main(self):
        self.change_metadata("validator", lambda x: x.update(main="./other.js"))

    def test_validator_exports_override(self):
        self.change_metadata("validator", lambda x: x.update(exports="./other.js"))

    def test_validator_wrong_module_type(self):
        self.change_metadata("validator", lambda x: x.update(type="module"))

    def test_three_wrong_version(self):
        self.change_metadata("three", lambda x: x.update(version="0.186.0"))

    def test_three_wrong_name(self):
        self.change_metadata("three", lambda x: x.update(name="three-copy"))

    def test_three_wrong_type(self):
        self.change_metadata("three", lambda x: x.update(type="commonjs"))

    def test_three_changed_webgpu_selector(self):
        self.change_metadata("three", lambda x: x["exports"].update({"./webgpu": "./build/other.js"}))

    def test_three_changed_loader_selector(self):
        self.change_metadata("three", lambda x: x["exports"].update({"./examples/jsm/*": "./other/*"}))

    def test_duplicate_metadata_key(self):
        key = self.f.named["validator_package"]
        raw = b'{"name":"gltf-validator","version":"wrong","version":"2.0.0-dev.3.10","main":"index.js"}'
        self.f.write(key, raw)
        self.f.reseal()
        self.reject(self.f.bind)

    def test_metadata_non_object(self):
        key = self.f.named["three_package"]
        self.f.write(key, b'["three", "0.186.1"]')
        self.f.reseal()
        self.reject(self.f.bind)

    def test_duplicate_three_package_root_rejected(self):
        original = self.f.path(self.f.named["three_package"]).read_bytes()
        extra = self.f.add_input("host", "pkgs/duplicate-three/package.json", original)
        self.f.inputs.lock["roles"]["node_packages"].append(extra)
        self.f.reseal()
        self.reject(self.f.bind)

    def test_metadata_in_other_root_rejected(self):
        old = self.f.named["three_package"]
        original = self.f.path(old).read_bytes()
        replacement = self.f.add_input("host", "pkgs/unrelated/package.json", original)
        lock = self.f.inputs.lock
        del lock["inputs"][old]
        del lock["dependencies"][old]
        lock["roles"]["node_packages"] = [replacement if ref == old else ref for ref in lock["roles"]["node_packages"]]
        for name, refs in lock["dependencies"].items():
            lock["dependencies"][name] = [replacement if ref == old else ref for ref in refs]
        self.f.reseal()
        self.reject(self.f.bind)

    def test_missing_probe_entry_edge(self):
        probe = self.f.named["probe"]
        self.f.inputs.lock["dependencies"][probe].remove(self.f.named["validator_entry"])
        self.f.reseal()
        self.reject(self.f.bind)

    def test_missing_loader_three_edge(self):
        loader = self.f.named["module_loader"]
        self.f.inputs.lock["dependencies"][loader].remove(self.f.named["three_entry"])
        self.f.reseal()
        self.reject(self.f.bind)

    def test_missing_validator_metadata_edge(self):
        self.f.inputs.lock["dependencies"][self.f.named["validator_entry"]] = []
        self.f.reseal()
        self.reject(self.f.bind)

    def test_missing_gltf_three_edge(self):
        self.f.inputs.lock["dependencies"][self.f.named["gltf_loader_entry"]].remove(self.f.named["three_entry"])
        self.f.reseal()
        self.reject(self.f.bind)

    def test_missing_wrapper_helper_closure(self):
        self.f.inputs.lock["dependencies"][self.f.named["wrapper"]].remove(self.f.named["binding_helper"])
        # Keep it reachable from a globally valid but unrelated role.
        self.f.inputs.lock["dependencies"][self.f.inputs.lock["roles"]["python_stdlib"][0]].append(self.f.named["binding_helper"])
        self.f.reseal()
        self.reject(self.f.bind)

    def test_package_reachable_from_wrong_role_only(self):
        self.f.inputs.lock["roles"]["node_packages"].remove(self.f.named["validator_entry"])
        self.f.reseal()
        self.reject(self.f.bind)

    def test_changed_file_after_seal(self):
        self.f.path(self.f.named["validator_entry"]).write_bytes(b"changed")
        self.reject(self.f.bind)

    def test_hardlink_after_seal(self):
        path = self.f.path(self.f.named["three_entry"])
        os.link(path, Path(self.temp) / "alias")
        self.reject(self.f.bind)

    def test_symlink_after_seal(self):
        path = self.f.path(self.f.named["validator_entry"])
        original = path.read_bytes()
        path.unlink()
        target = Path(self.temp) / "redirect"
        target.write_bytes(original)
        path.symlink_to(target)
        self.reject(self.f.bind)

    def test_metadata_replacement_after_prepare(self):
        prepared = self.f.prepare()
        path = self.f.path(self.f.named["three_package"])
        path.write_bytes(path.read_bytes() + b" ")
        self.reject(lambda: entries.inspect_entry_readback_job(prepared))

    def test_explicit_three_import(self):
        prepared = self.f.prepare()
        result = entries.resolve_entry_import(prepared, importer=self.f.named["gltf_loader_entry"], specifier="three")
        self.assertIsNotNone(result)

    def test_explicit_relative_import(self):
        prepared = self.f.prepare()
        result = entries.resolve_entry_import(prepared, importer=self.f.named["three_entry"], specifier="./child.js")
        self.assertIsNotNone(result)

    def test_undeclared_relative_import(self):
        prepared = self.f.prepare()
        self.reject(lambda: entries.resolve_entry_import(prepared, importer=self.f.named["validator_entry"], specifier="../three/build/child.js"))

    def test_unknown_importer(self):
        prepared = self.f.prepare()
        self.reject(lambda: entries.resolve_entry_import(prepared, importer="host:unknown.js", specifier="three"))

    def test_bare_ambient_package(self):
        prepared = self.f.prepare()
        self.reject(lambda: entries.resolve_entry_import(prepared, importer=self.f.named["probe"], specifier="gltf-validator"))

    def test_three_subpath_not_inferred(self):
        prepared = self.f.prepare()
        self.reject(lambda: entries.resolve_entry_import(prepared, importer=self.f.named["probe"], specifier="three/webgpu"))

    def test_query_suffix_rejected(self):
        prepared = self.f.prepare()
        path = str(self.f.path(self.f.named["three_entry"]))
        self.reject(lambda: entries.resolve_entry_import(prepared, importer=self.f.named["probe"], specifier=path+"?x=1"))

    def test_fragment_suffix_rejected(self):
        prepared = self.f.prepare()
        path = str(self.f.path(self.f.named["three_entry"]))
        self.reject(lambda: entries.resolve_entry_import(prepared, importer=self.f.named["probe"], specifier=path+"#x"))

    def test_file_url_rejected(self):
        prepared = self.f.prepare()
        path = self.f.path(self.f.named["three_entry"]).as_uri()
        self.reject(lambda: entries.resolve_entry_import(prepared, importer=self.f.named["probe"], specifier=path))

    def test_encoded_path_rejected(self):
        prepared = self.f.prepare()
        path = str(self.f.path(self.f.named["three_entry"])).replace("three.webgpu.js", "%74hree.webgpu.js")
        self.reject(lambda: entries.resolve_entry_import(prepared, importer=self.f.named["probe"], specifier=path))

    def test_extension_inference_rejected(self):
        prepared = self.f.prepare()
        self.reject(lambda: entries.resolve_entry_import(prepared, importer=self.f.named["three_entry"], specifier="./child"))

    def test_wrong_edge_with_named_target_rejected(self):
        prepared = self.f.prepare()
        self.reject(lambda: entries.resolve_entry_import(prepared, importer=self.f.named["validator_entry"], specifier="three"))

    def test_new_job_authority_false(self):
        prepared = self.f.prepare()
        job = entries.inspect_entry_readback_job(prepared)
        self.assertEqual(job["schema"], "ontokin.c201.readback-job/0.2")
        for key in ("node_start_authorized", "native_readiness", "admission_completed", "next_slot_authorized"):
            self.assertIs(job[key], False)
        self.assertIs(job["dependency_entries"]["ambient_imports"], False)
        self.assertIs(job["dependency_entries"]["node_resolution_authorized"], False)
        self.assertIn("validator_package", job["dependency_entries"]["named"])
        self.assertIn("three_package", job["dependency_entries"]["named"])

    def test_new_handle_rejected_by_old_result_verifier(self):
        prepared = self.f.prepare()
        self.reject(lambda: readback_binding.verify_readback_result(prepared, process={}))

    def test_legacy_job_remains_explicit_version_one(self):
        bindings = readback_binding.bind_readbacks(self.f.native.session)
        accepted = self.f.native.accept("A01")
        prepared = readback_binding.prepare_readback(bindings, "A01", accepted=accepted)
        job = readback_binding.inspect_readback_job(prepared)
        self.assertEqual(job["schema"], "ontokin.c201.readback-job/0.1")
        self.assertNotIn("dependency_entries", job)
        self.assertEqual(set(job), {
            "schema", "purpose", "slot", "route", "case", "scope", "source",
            "protocol_sha256", "schedule_sha256", "input_lock_sha256", "approval_sha256",
            "accepted_revision", "accepted_pointer_sha256", "transaction_receipt_sha256",
            "construction_closure_sha256", "receiving_closure_sha256", "accepted_source_identity",
            "artifact", "audit", "command", "outputs", "checks", "limits",
            "node_start_authorized", "native_readiness", "admission_completed", "next_slot_authorized"})

    def test_mutating_inspected_job_does_not_mutate_retained_bindings(self):
        prepared = self.f.prepare()
        job = entries.inspect_entry_readback_job(prepared)
        before = canonical(job)
        job["dependency_entries"]["named"]["three_entry"]["sha256"] = "0" * 64
        self.assertEqual(canonical(entries.inspect_entry_readback_job(prepared)), before)

    def test_written_job_tamper_rejected(self):
        prepared = self.f.prepare()
        job = entries.inspect_entry_readback_job(prepared)
        path = Path(job["outputs"]["job"])
        mutated = deepcopy(job)
        mutated["dependency_entries"]["named"]["three_entry"]["sha256"] = "0" * 64
        path.write_bytes(canonical(mutated))
        self.reject(lambda: entries.inspect_entry_readback_job(prepared))


def main():
    global SOURCE_ROOT
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--candidate", required=True)
    options = parser.parse_args()
    SOURCE_ROOT = Path(options.source).resolve()
    out = Path(options.output).resolve()
    out.mkdir(parents=True, exist_ok=True)
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Controls)
    started = time.monotonic()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    elapsed = time.monotonic()-started
    (out/"controls.log").write_text(stream.getvalue())
    value = {"schema":"ontokin.c209.independent-cpu-controls/0.1", "candidate":options.candidate,
             "source_root":str(SOURCE_ROOT), "tests":result.testsRun, "failures":len(result.failures),
             "errors":len(result.errors), "skips":len(result.skipped), "passed":result.wasSuccessful(),
             "elapsed_seconds":elapsed, "observations":Controls.observations,
             "attempted_child_starts":sum(x["attempted_child_starts"] for x in Controls.observations),
             "native_starts":0, "receiving_starts":0, "node_starts":0, "lifecycle_starts":0, "timed_author_starts":0,
             "limitations":["Synthetic host-package bytes and fixture approvals only",
                            "No Node imports, runtime dependency verification or native readiness"]}
    (out/"RESULT.json").write_text(json.dumps(value, indent=2)+"\n")
    print(json.dumps({k:value[k] for k in ("tests","failures","errors","skips","passed","elapsed_seconds")}))
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    raise SystemExit(main())

