"""Independent synthetic package inventory for C209 CPU review only."""
from __future__ import annotations
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path

from prototypes.static_tray_admission_c201 import input_lock, transaction
from prototypes.static_tray_admission_c201.schedule import canonical
from tests.test_static_tray_admission_c201_transaction import TransactionFixture

ROOT = Path(__file__).resolve().parent
HELPERS = (
    "prototypes/static_tray_admission_c201/readback_binding.py",
    "prototypes/static_tray_admission_c201/readback_entries.py",
)
METADATA = {
    "validator": {"name": "gltf-validator", "version": "2.0.0-dev.3.10", "main": "index.js"},
    "three": {"name": "three", "version": "0.186.1", "type": "module",
              "exports": {"./webgpu": "./build/three.webgpu.js",
                          "./examples/jsm/*": "./examples/jsm/*"}},
}


class IndependentFixture:
    """All packages, gates, process records and accepted GLBs are CPU fixtures."""

    def __init__(self, root, source_root):
        self.native = TransactionFixture(root)
        self.inputs = self.native.inputs
        self.source_root = Path(source_root)
        self.named = {}
        package_files = {
            "validator_package": ("pkgs/validator/package.json", canonical(METADATA["validator"])),
            "validator_entry": ("pkgs/validator/index.js", b"// Synthetic validator entry; do not execute\n"),
            "three_package": ("pkgs/three/package.json", canonical(METADATA["three"])),
            "three_entry": ("pkgs/three/build/three.webgpu.js", b"// Synthetic Three entry; do not execute\n"),
            "gltf_loader_entry": ("pkgs/three/examples/jsm/loaders/GLTFLoader.js", b"// Synthetic GLTFLoader; do not execute\n"),
            "relative_child": ("pkgs/three/build/child.js", b"// Explicitly inventoried relative import fixture\n"),
        }
        for key, (path, raw) in package_files.items():
            self.named[key] = self.add_input("host", path, raw)
        lock = self.inputs.lock
        old_package_marker = lock["roles"]["node_packages"][0]
        del lock["inputs"][old_package_marker]
        del lock["dependencies"][old_package_marker]
        lock["roles"]["node_packages"] = [self.named[k] for k in package_files]
        for path in HELPERS:
            self.add_input("repository", path, (self.source_root / path).read_bytes())
        for key, role in (
            ("probe", "admission_node_probe"),
            ("module_loader", "node_loader"),
            ("wrapper", "admission_format_check"),
            ("node", "node_executable"),
        ):
            self.named[key] = lock["roles"][role][0]
        self.named["binding_helper"] = "repository:" + HELPERS[1]
        self.named["legacy_binding_helper"] = "repository:" + HELPERS[0]
        lock["dependencies"][self.named["probe"]] = [self.named[k] for k in (
            "validator_package", "validator_entry", "three_package", "three_entry", "gltf_loader_entry")]
        lock["dependencies"][self.named["module_loader"]] = [self.named[k] for k in (
            "three_entry", "three_package")]
        lock["dependencies"][self.named["validator_entry"]] = [self.named["validator_package"]]
        lock["dependencies"][self.named["three_entry"]] = [self.named["three_package"], self.named["relative_child"]]
        lock["dependencies"][self.named["gltf_loader_entry"]] = [
            self.named["three_entry"], self.named["three_package"]]
        lock["dependencies"][self.named["wrapper"]] = [self.named[k] for k in (
            "probe", "module_loader", "node", "binding_helper", "legacy_binding_helper")]
        self.reseal()

    def add_input(self, root, relative, raw, *, mode=0o600):
        namespace = self.inputs.repo if root == "repository" else self.inputs.host
        path = namespace / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        path.chmod(mode)
        name = root + ":" + relative
        self.inputs.lock["inputs"][name] = self.inputs.binding(path, root)
        self.inputs.lock["dependencies"][name] = []
        return name

    def path(self, name):
        binding = self.inputs.lock["inputs"][name]
        root = self.inputs.repo if binding["root"] == "repository" else self.inputs.host
        return root / binding["path"]

    def write(self, name, raw):
        path = self.path(name)
        path.write_bytes(raw)
        self.inputs.lock["inputs"][name] = self.inputs.binding(path, self.inputs.lock["inputs"][name]["root"])

    def reseal(self):
        """Explicit synthetic independent-fact reset before binding, never production."""
        f = self.inputs
        f.lock["source"]["files"] = sorted(k for k, v in f.lock["inputs"].items() if v["root"] == "repository")
        closure = input_lock.closure_digest(f.lock)
        f.context = replace(f.context, closure_sha256=closure,
                            launch_plan_sha256=input_lock.launch_plan_digest(f.lock))
        for gate, binding in f.lock["gate_receipts"].items():
            path = f.host / binding["path"]
            value = json.loads(path.read_bytes())
            value["closure_sha256"] = closure
            path.write_bytes(canonical(value))
            f.lock["gate_receipts"][gate] = f.binding(path, "host")
        f.repin()
        self.native.session = transaction.bind_transactions(f.lock_path, f.approval_path, context=f.context)

    def bind(self):
        from prototypes.static_tray_admission_c201 import readback_entries
        return readback_entries.bind_entry_readbacks(self.native.session)

    def prepare(self):
        from prototypes.static_tray_admission_c201 import readback_entries
        bindings = self.bind()
        accepted = self.native.accept("A01")
        prepared = readback_entries.prepare_entry_readback(bindings, "A01", accepted=accepted)
        return prepared

