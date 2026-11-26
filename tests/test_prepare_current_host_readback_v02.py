"""Development tests of the 0.2.0 preparer route (C271-P33, gate MI, worker W2).

These are development tests, not the independently frozen controls; an
independent author freezes those later. A control identifier such as MC02 in a
test name names the contract obligation that the test exercises.

Every input is synthetic and is built in a resolved temporary directory: small
tar.gz archives that use the official member names, and synthetic 64-bit
Mach-O header bytes that are never executed. No test starts a process; a guard
patches every process-creation call and fails the test if one is attempted.
A synthetic archive's pin reaches the preparer only through the explicit
SyntheticPins seam of install_plan_v02; the adopted pin stays a constant.

Labels: "real" marks a call of libSystem's renamex_np, "simulated" a patched
boundary. On a non-Darwin host, a test that needs renamex_np asserts the
route's documented refusal instead; nothing is skipped.

Every 0.2.0 call reads the OS identity through the observer's exported
read_os_identity (decision D-04). On Darwin that is the real reader, which only
reads the two SystemVersion.plist files. On another host the tests replace it
with a simulated identity, so the other predicates stay testable there.
"""
from __future__ import annotations

import contextlib
import ctypes
import errno
import hashlib
import io
import json
import os
from pathlib import Path
import plistlib
import shutil
import stat
import struct
import subprocess
import sys
import tarfile
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import uuid

from prototypes.static_tray_v01 import current_host_observation_v02 as observation
from tools import prepare_current_host_readback as preparer

provider = preparer.provider
DARWIN = sys.platform == "darwin"
SCHEMA = "ontokin.current-host-readback-install/0.2.0"
RESULT = "ontokin.current-host-readback-install-result/0.2.0"
CONTRACT = "ontokin.current-host-readback/0.2.0"
PROFILE = "darwin-arm64-v1"
DESIGN_REVISION = 4
AMENDMENTS = ["P33-AMENDMENT-001"]
# The confirmed shapes (decision D-11). W3's receipt rule lists the plan keys and
# the receipt keys below; D-12 adds design_revision and amendments to results.
PLAN_KEYS = {"schema", "contract", "purpose", "source_root", "archive", "destination", "root_mode", "files",
             "directories", "members", "node_source", "report"}
W3_RESULT_KEYS = {"schema", "contract", "purpose", "passed", "state", "apply_requested", "execution_counts",
                  "operations", "pins", "labels", "preparer_source", "archive", "before"}
RESULT_BASE = {"schema", "contract", "design_revision", "amendments", "purpose", "passed", "state",
               "apply_requested", "execution_counts", "operations", "pins", "labels", "preparer_source"}
RECEIPT_KEYS = RESULT_BASE | {"archive", "before"}
INSTALLED_KEYS = RECEIPT_KEYS | {"after", "publication"}
PUBLICATION_FAILURE_KEYS = RECEIPT_KEYS | {"error", "publication_error", "destination_after_error", "stage_after_error"}
LABEL_KEYS = {"executor", "contract", "profile", "design_revision", "amendments", "pins", "os"}
ARCHIVE_KEYS = {"sha256", "size_bytes", "members", "expanded_bytes", "symlinks", "member_inventory_sha256",
                "extracted_members"}
NODE_SOURCE_KEYS = {"schema", "contract", "archive", "checksum_file", "signature_check", "member_inventory_sha256",
                    "extracted"}
PREPARER_FILES = {"tools/prepare_current_host_readback.py", "prototypes/static_tray_v01/current_host_readback_v01.py",
                  "prototypes/static_tray_v01/canonical.py", "prototypes/static_tray_v01/current_host_observation_v02.py"}
# Used only on a non-Darwin host, in place of the real reader (simulated).
SIMULATED_IDENTITY = {
    "system_version": {"state": "present", "path": "/simulated/SystemVersion.plist", "sha256": "0" * 64,
                       "size_bytes": 0, "mode": "0o644", "product_name": "Simulated", "product_version": "0.0",
                       "product_build_version": "SIMULATED", "product_version_extra": None},
    "cryptex": {"state": "absent", "path": "/simulated/cryptex/SystemVersion.plist", "hops": []}}
RELEASE = "node-v24.22.1-darwin-arm64"
NODE_MEMBER = RELEASE + "/bin/node"
ADOPTED_PIN = "89c682593d76cd44233fa53b1563264e7de9cbb189cad169135c5b4fadfbc0a7"
CHECKSUM_FILE = {"url": "https://nodejs.org/dist/v24.22.1/SHASUMS256.txt",
                 "sha256": "fdfbffc969c0f604beff0124d409b33a43b53f5c681d6220f80023e0d6df9dc4", "size_bytes": 3171}
ZERO_STARTS = {"node": 0, "ldd": 0, "checkers": 0}
# A thin 64-bit little-endian arm64 MH_EXECUTE header with no load commands,
# then inert bytes. It is data only: no test executes it.
MACHO = struct.pack("<8I", 0xFEEDFACF, 0x0100000C, 0, 2, 0, 0, 0, 0) + b"synthetic arm64 body; never executed\n"
SIGNATURE = {"status": "not_performed", "detail": "Synthetic development archive; no release signature exists."}
REAL_EXTRACTFILE = tarfile.TarFile.extractfile
TAR_TYPES = {"file": tarfile.REGTYPE, "directory": tarfile.DIRTYPE, "symlink": tarfile.SYMTYPE,
             "hardlink": tarfile.LNKTYPE, "fifo": tarfile.FIFOTYPE, "character-device": tarfile.CHRTYPE,
             "block-device": tarfile.BLKTYPE}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    """Independent canonical form: sorted keys, compact separators, ASCII only."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("ascii")


def binding(path):
    data = path.read_bytes()
    return {"sha256": sha256(data), "size_bytes": len(data), "mode": oct(stat.S_IMODE(path.lstat().st_mode))}


def entry(kind, name, mode, data=b"", target=None):
    return {"kind": kind, "name": name, "mode": mode, "data": data, "target": target}


def node_entries(executable=MACHO):
    """Synthetic stand-in for the official layout, with its three in-archive links."""
    r = RELEASE
    return [entry("directory", r, 0o755), entry("directory", r + "/bin", 0o755),
            entry("file", NODE_MEMBER, 0o755, executable),
            entry("symlink", r + "/bin/npm", 0o755, target="../lib/node_modules/npm/bin/npm-cli.js"),
            entry("symlink", r + "/bin/npx", 0o755, target="../lib/node_modules/npm/bin/npx-cli.js"),
            entry("symlink", r + "/bin/corepack", 0o755, target="../lib/node_modules/corepack/dist/corepack.js"),
            entry("directory", r + "/lib", 0o755), entry("directory", r + "/lib/node_modules", 0o755),
            entry("directory", r + "/lib/node_modules/npm", 0o755),
            entry("directory", r + "/lib/node_modules/npm/bin", 0o755),
            entry("file", r + "/lib/node_modules/npm/bin/npm-cli.js", 0o755, b"// inert synthetic npm entry\n"),
            entry("file", r + "/lib/node_modules/npm/bin/npx-cli.js", 0o755, b"// inert synthetic npx entry\n"),
            entry("directory", r + "/lib/node_modules/corepack", 0o755),
            entry("directory", r + "/lib/node_modules/corepack/dist", 0o755),
            entry("file", r + "/lib/node_modules/corepack/dist/corepack.js", 0o644, b"// inert synthetic corepack\n"),
            entry("directory", r + "/include", 0o755), entry("directory", r + "/include/node", 0o755),
            entry("file", r + "/include/node/node.h", 0o644, b"/* inert synthetic header */\n"),
            entry("file", r + "/README.md", 0o644, b"Synthetic development archive.\n")]


def write_archive(path, entries):
    with tarfile.open(path, "w:gz", format=tarfile.PAX_FORMAT) as archive:
        for item in entries:
            info = tarfile.TarInfo(item["name"])
            info.type, info.mode, info.mtime = TAR_TYPES[item["kind"]], item["mode"], 0
            if item["kind"] in ("symlink", "hardlink"):
                info.linkname = item["target"]
            if item["kind"].endswith("device"):
                info.devmajor, info.devminor = 1, 3
            if item["kind"] == "file":
                info.size = len(item["data"])
                archive.addfile(info, io.BytesIO(item["data"]))
            else:
                archive.addfile(info)
    path.chmod(0o600)
    return path


def node_inventory(entries):
    return {item["name"]: {"kind": item["kind"], "size_bytes": len(item["data"]) if item["kind"] == "file" else 0,
                           "mode": oct(item["mode"]),
                           "link_target": item["target"] if item["kind"] == "symlink" else None}
            for item in entries}


def expected_node_source(archive, inventory, executable, signature=SIGNATURE):
    """NODE-SOURCE.json bytes built here, independently of the preparer."""
    return canonical({"schema": "ontokin.current-host-readback-node-source/0.2.0", "contract": CONTRACT,
                      "archive": {"name": RELEASE + ".tar.gz", "sha256": archive["sha256"],
                                  "size_bytes": archive["size_bytes"]},
                      "checksum_file": dict(CHECKSUM_FILE), "signature_check": dict(signature),
                      "member_inventory_sha256": sha256(canonical(inventory)),
                      "extracted": {"member": NODE_MEMBER, "path": "bin/node", **executable}})


def snapshot(root):
    """Names, kinds, modes, inodes, link counts and bytes or link targets; links are never followed."""
    root = str(root)
    if not os.path.lexists(root):
        return None
    def row(path):
        info = os.lstat(path)
        kind = ("link" if stat.S_ISLNK(info.st_mode) else "dir" if stat.S_ISDIR(info.st_mode)
                else "file" if stat.S_ISREG(info.st_mode) else "other")
        detail = os.readlink(path) if kind == "link" else sha256(Path(path).read_bytes()) if kind == "file" else None
        return (os.path.relpath(path, root), kind, oct(stat.S_IMODE(info.st_mode)), info.st_ino, info.st_nlink, detail)
    rows = [row(root)]
    if os.path.isdir(root) and not os.path.islink(root):
        for parent, directories, files in os.walk(root):
            rows.extend(row(os.path.join(parent, name)) for name in directories + files)
    return sorted(rows)


def expected_os_label():
    """HOST's labels.os shape, read here with plistlib, independently of the observer's reader.

    On a non-Darwin host it is the label of the simulated identity.
    """
    if not DARWIN:
        system = SIMULATED_IDENTITY["system_version"]
        return {"product_version": system["product_version"], "product_build_version": system["product_build_version"],
                "product_version_extra": system["product_version_extra"], "cryptex": {"state": "absent"}}
    def fields(path):
        with open(path, "rb") as stream:
            value = plistlib.load(stream)
        return {"product_version": value["ProductVersion"], "product_build_version": value["ProductBuildVersion"],
                "product_version_extra": value.get("ProductVersionExtra")}
    label = fields(observation.SYSTEM_VERSION_PATH)
    cryptex = observation.CRYPTEX_SYSTEM_VERSION_PATH
    label["cryptex"] = {"state": "present", **fields(cryptex)} if os.path.exists(cryptex) else {"state": "absent"}
    return label


class PreparerCase(unittest.TestCase):
    """Resolved temporary directory, process guard and fixture builders."""

    PAYLOADS = {"validator/package/package.json": b'{"version":"synthetic-validator"}\n',
                "indexer-view/three/package.json": b'{"version":"synthetic-three"}\n'}
    PREFIX = "c195/receiving/"

    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        parent = os.path.realpath(tempfile.gettempdir())
        self.base = Path(self.stack.enter_context(tempfile.TemporaryDirectory(prefix="ontokin-w2-", dir=parent)))
        self.assertEqual(str(self.base), os.path.realpath(self.base))
        self.counter = 0
        self.process_guards = []
        for name in ("Popen", "run", "call", "check_call", "check_output"):
            self.process_guards.append(self.stack.enter_context(
                patch.object(subprocess, name, side_effect=AssertionError("process start forbidden: " + name))))
        for name in ("system", "fork", "forkpty", "posix_spawn", "posix_spawnp", "execv", "execve", "execvp", "execvpe"):
            if hasattr(os, name):
                self.process_guards.append(self.stack.enter_context(
                    patch.object(os, name, side_effect=AssertionError("process start forbidden: " + name))))
        if not DARWIN:
            # Simulated: no SystemVersion.plist exists off Darwin.
            self.stack.enter_context(patch.object(observation, "read_os_identity", return_value=SIMULATED_IDENTITY))

    def tearDown(self):
        for guard in self.process_guards:
            self.assertEqual(guard.call_count, 0, "A process start was attempted")

    def path(self, stem, suffix=""):
        self.counter += 1
        return self.base / ("%s-%d%s" % (stem, self.counter, suffix))

    def pins(self, node="0" * 64, dependencies="0" * 64, files=None):
        return preparer.SyntheticPins(node_archive_sha256=node, dependency_archive_sha256=dependencies,
                                      dependency_files=files or {"unused": {"sha256": "0" * 64, "size_bytes": 0}})

    def node_fixture(self, entries=None, *, declared=None, executable=MACHO, frozen=None, signature=SIGNATURE):
        entries = node_entries(executable) if entries is None else entries
        archive_path = write_archive(self.path("node", ".tar.gz"), entries)
        archive = {"path": str(archive_path), **binding(archive_path)}
        inventory = node_inventory(entries if declared is None else declared)
        frozen = frozen or {"sha256": sha256(executable), "size_bytes": len(executable), "mode": "0o755"}
        raw = expected_node_source(archive, inventory, frozen, signature)
        plan = {"schema": SCHEMA, "contract": CONTRACT, "purpose": "selected-node", "source_root": str(preparer.ROOT),
                "archive": archive, "destination": str(self.path("runtime")), "root_mode": "0o755",
                "files": {"bin/node": dict(frozen), "NODE-SOURCE.json": {"sha256": sha256(raw), "size_bytes": len(raw),
                                                                         "mode": "0o644"}},
                "directories": {"bin": "0o755"}, "members": inventory,
                "node_source": {"signature_check": dict(signature)}, "report": str(self.path("report", ".json"))}
        return SimpleNamespace(plan=plan, pins=self.pins(node=archive["sha256"]), raw=raw, inventory=inventory,
                               executable=executable, destination=Path(plan["destination"]),
                               report=Path(plan["report"]), archive=archive_path)

    def dependency_entries(self, mutation=None):
        items = [entry("directory", "c195", 0o755), entry("directory", "c195/receiving", 0o755)]
        for index, (name, data) in enumerate(self.PAYLOADS.items()):
            item = entry("file", self.PREFIX + name, 0o644, data)
            if index == 0:
                if mutation == "absolute":
                    item["name"] = "/outside"
                elif mutation == "traversal":
                    item["name"] = "c195/../outside"
                elif mutation in ("symlink", "hardlink"):
                    item.update(kind=mutation, data=b"", target="../outside" if mutation == "symlink" else "c195/other.txt")
                elif mutation in ("fifo", "character-device"):
                    item.update(kind=mutation, data=b"")
                elif mutation == "mode":
                    item["mode"] = 0o777
            items.append(item)
            if index == 0 and mutation == "duplicate":
                items.append(dict(item))
        items.append(entry("file", "c195/other.txt", 0o644, b"not a target\n"))
        return items

    def dependency_fixture(self, mutation=None):
        archive_path = self.path("c195", ".tar.gz")
        with tarfile.open(archive_path, "w:gz", format=tarfile.PAX_FORMAT) as archive:
            for item in self.dependency_entries(mutation):
                info = tarfile.TarInfo(item["name"])
                info.type, info.mode, info.mtime = TAR_TYPES[item["kind"]], item["mode"], 0
                if item["kind"] in ("symlink", "hardlink"):
                    info.linkname = item["target"]
                if item["kind"] == "file":
                    info.size = len(item["data"])
                    archive.addfile(info, io.BytesIO(item["data"]))
                else:
                    archive.addfile(info)
        archive_path.chmod(0o600)
        files = {name: {"sha256": sha256(data), "size_bytes": len(data), "mode": "0o644"} for name, data in self.PAYLOADS.items()}
        members = {}
        for item in self.dependency_entries():
            if item["kind"] == "directory":
                members[item["name"]] = {"kind": "directory", "size_bytes": 0, "sha256": None, "mode": "0o755", "target": None}
            else:
                target = item["name"][len(self.PREFIX):] if item["name"].startswith(self.PREFIX) else None
                members[item["name"]] = {"kind": "file", "size_bytes": len(item["data"]), "sha256": sha256(item["data"]),
                                         "mode": "0o644", "target": target}
        archive = {"path": str(archive_path), **binding(archive_path)}
        plan = {"schema": SCHEMA, "contract": CONTRACT, "purpose": "retained-dependencies", "source_root": str(preparer.ROOT),
                "archive": archive, "destination": str(self.path("dependencies")), "root_mode": "0o755", "files": files,
                "directories": {"validator": "0o755", "validator/package": "0o755", "indexer-view": "0o755",
                                "indexer-view/three": "0o755"},
                "members": members, "node_source": None, "report": str(self.path("report", ".json"))}
        pins = self.pins(dependencies=archive["sha256"],
                         files={name: {"sha256": row["sha256"], "size_bytes": row["size_bytes"]} for name, row in files.items()})
        return SimpleNamespace(plan=plan, pins=pins, destination=Path(plan["destination"]), report=Path(plan["report"]))

    def refreeze(self, fixture):
        """Freeze NODE-SOURCE.json again after a plan edit, so that only the edited rule can refuse."""
        plan = fixture.plan
        fixture.raw = expected_node_source(plan["archive"], plan["members"], plan["files"]["bin/node"],
                                           plan["node_source"]["signature_check"])
        plan["files"]["NODE-SOURCE.json"].update(sha256=sha256(fixture.raw), size_bytes=len(fixture.raw))
        return fixture

    def renew(self, fixture):
        """A fresh report path for a later call on the same fixture."""
        fixture.plan["report"] = str(self.path("report", ".json"))
        fixture.report = Path(fixture.plan["report"])
        return fixture.plan

    def exact_tree(self, fixture):
        """Build the exact planned tree by hand, independently of the preparer."""
        destination = fixture.destination
        (destination / "bin").mkdir(parents=True)
        executable = destination / "bin/node"
        executable.write_bytes(fixture.executable)
        executable.chmod(0o755)
        provenance = destination / "NODE-SOURCE.json"
        provenance.write_bytes(fixture.raw)
        provenance.chmod(0o644)
        (destination / "bin").chmod(0o755)
        destination.chmod(0o755)
        return snapshot(destination)

    def refuses(self, call, *, code="CH-INSTALL", state="REJECTED", reason=None):
        with self.assertRaises(provider.CurrentHostBindingError) as caught:
            call()
        error = caught.exception
        self.assertEqual((error.code, error.state), (code, state), error.reason)
        if reason is not None:
            self.assertIn(reason, error.reason)
        record = error.refusal_record
        self.assertEqual((record["schema"], record["contract"], record["passed"]), (RESULT, CONTRACT, False))
        self.assertEqual(record["execution_counts"], ZERO_STARTS)
        self.assertEqual(record["labels"]["executor"], "macos-arm64-local")
        return error

    def install(self, fixture, *, apply=True):
        return preparer.install_plan_v02(fixture.plan, apply=apply, synthetic_pins=fixture.pins)

    @contextlib.contextmanager
    def spies(self):
        with patch.object(tarfile, "open", wraps=tarfile.open) as opened, \
                patch.object(tempfile, "mkdtemp", wraps=tempfile.mkdtemp) as staged, \
                patch.object(tarfile.TarFile, "extractfile", autospec=True, side_effect=REAL_EXTRACTFILE) as read, \
                patch.object(preparer, "rename_exclusive", wraps=preparer.rename_exclusive) as published:
            yield SimpleNamespace(opened=opened, staged=staged, read=read, published=published)

    @staticmethod
    def read_names(spy):
        return [call.args[1].name for call in spy.read.call_args_list]

    @contextlib.contextmanager
    def no_fallback(self):
        """Fail if any other rename, move or link call is made (no fallback, no link)."""
        names = (("os.rename", os, "rename"), ("os.replace", os, "replace"), ("os.renames", os, "renames"),
                 ("shutil.move", shutil, "move"), ("0.1.0 renameat2", preparer, "rename_without_replacement"),
                 ("os.symlink", os, "symlink"), ("os.link", os, "link"))
        with contextlib.ExitStack() as stack:
            guards = [(label, stack.enter_context(patch.object(owner, name, side_effect=AssertionError(label))))
                      for label, owner, name in names]
            yield
        for label, guard in guards:
            self.assertEqual(guard.call_count, 0, "forbidden call: " + label)

    def assert_nothing_staged(self, fixture):
        self.assertIsNone(snapshot(fixture.destination))
        self.assertEqual(sorted(path.name for path in self.base.glob(".current-host-stage-*")), [])

    def assert_platform_refusal(self, fixture):
        """Non-Darwin hosts: the apply route refuses before staging (no renamex_np)."""
        with self.spies() as spy:
            self.refuses(lambda: self.install(fixture), reason="only on Darwin")
        spy.staged.assert_not_called()
        self.assert_nothing_staged(fixture)


class NodeArchivePolicy(PreparerCase):
    """Contract section 3: pin, member inventory, extraction and executable check (MC01 to MC05)."""

    def assert_refused_before_staging(self, fixture, reason, *, read=(), **options):
        """Refused in the validation pass: no stage, no destination; read lists the members whose data was hashed."""
        with self.spies() as spy:
            error = self.refuses(lambda: self.install(fixture), reason=reason, **options)
        spy.staged.assert_not_called()
        self.assertEqual(self.read_names(spy), list(read))
        self.assert_nothing_staged(fixture)
        return error, spy

    def test_MC01_changed_archive_bytes_refuse_before_any_member_is_read(self):
        """Creates one synthetic archive, then changes one byte in place; tarfile.open is never reached."""
        fixture = self.node_fixture()
        data = bytearray(fixture.archive.read_bytes())
        data[-1] ^= 0xFF
        fixture.archive.write_bytes(bytes(data))
        _, spy = self.assert_refused_before_staging(fixture, "Locked file identity differs")
        spy.opened.assert_not_called()

    def test_MC01_plan_digest_other_than_the_pin_refuses_before_the_archive_is_opened(self):
        """The plan names the archive's true digest, but the pin is another value."""
        fixture = self.node_fixture()
        fixture.pins = self.pins(node="1" * 64)
        _, spy = self.assert_refused_before_staging(fixture, "differs from the adopted pin")
        spy.opened.assert_not_called()

    def test_MC02_absolute_member_name_refuses_the_archive(self):
        fixture = self.node_fixture(node_entries() + [entry("file", "/outside", 0o644, b"x")], declared=node_entries())
        self.assert_refused_before_staging(fixture, "Unsafe archive path: /outside", read=[NODE_MEMBER])

    def test_MC02_traversing_member_name_refuses_the_archive(self):
        for name in ("../outside", RELEASE + "/../outside", RELEASE + "/bin/../../outside"):
            with self.subTest(name=name):
                fixture = self.node_fixture(node_entries() + [entry("file", name, 0o644, b"x")], declared=node_entries())
                self.assert_refused_before_staging(fixture, "Unsafe archive path", read=[NODE_MEMBER])

    def test_MC02_duplicate_member_name_refuses_the_archive(self):
        readme = entry("file", RELEASE + "/README.md", 0o644, b"Synthetic development archive.\n")
        fixture = self.node_fixture(node_entries() + [readme], declared=node_entries())
        self.assert_refused_before_staging(fixture, "Duplicate or excessive archive member", read=[NODE_MEMBER])

    def test_MC02_hard_link_member_refuses_the_archive(self):
        link = entry("hardlink", RELEASE + "/bin/node-copy", 0o755, target=NODE_MEMBER)
        declared = node_entries() + [entry("file", RELEASE + "/bin/node-copy", 0o755)]
        fixture = self.node_fixture(node_entries() + [link], declared=declared)
        self.assert_refused_before_staging(fixture, "Hard link archive members are forbidden", read=[NODE_MEMBER])

    def test_MC02_character_device_member_refuses_the_archive(self):
        device = entry("character-device", RELEASE + "/null", 0o644)
        fixture = self.node_fixture(node_entries() + [device], declared=node_entries() + [entry("file", RELEASE + "/null", 0o644)])
        self.assert_refused_before_staging(fixture, "Device archive members are forbidden", read=[NODE_MEMBER])

    def test_MC02_block_device_member_refuses_the_archive(self):
        device = entry("block-device", RELEASE + "/disk", 0o644)
        fixture = self.node_fixture(node_entries() + [device], declared=node_entries() + [entry("file", RELEASE + "/disk", 0o644)])
        self.assert_refused_before_staging(fixture, "Device archive members are forbidden", read=[NODE_MEMBER])

    def test_MC02_fifo_member_refuses_the_archive(self):
        fifo = entry("fifo", RELEASE + "/pipe", 0o644)
        fixture = self.node_fixture(node_entries() + [fifo], declared=node_entries() + [entry("file", RELEASE + "/pipe", 0o644)])
        self.assert_refused_before_staging(fixture, "FIFO archive members are forbidden", read=[NODE_MEMBER])

    def test_MC02_undeclared_member_refuses_the_archive(self):
        extra = entry("file", RELEASE + "/EXTRA.md", 0o644, b"not in the frozen inventory\n")
        fixture = self.node_fixture(node_entries() + [extra], declared=node_entries())
        self.assert_refused_before_staging(fixture, "Undeclared archive member: " + RELEASE + "/EXTRA.md", read=[NODE_MEMBER])

    def test_MC02_escaping_link_target_refuses_the_archive(self):
        """The plan declares a contained target; the archive's actual link escapes."""
        for target in ("../../outside", "../../../../etc", "/usr/bin/true", "../../" + RELEASE + "-other/bin/node"):
            with self.subTest(target=target):
                actual = [item for item in node_entries() if item["name"] != RELEASE + "/bin/npm"]
                actual.append(entry("symlink", RELEASE + "/bin/npm", 0o755, target=target))
                fixture = self.node_fixture(actual, declared=node_entries())
                self.assert_refused_before_staging(fixture, "link target", read=[NODE_MEMBER])

    def test_MC02_inventory_cannot_declare_a_forbidden_member(self):
        """Plan-level refusals: the frozen inventory itself breaks the policy; the archive is never opened.

        NODE-SOURCE.json is frozen again after each edit, so only the named rule can refuse.
        """
        def row(kind="file", size=0, target=None):
            return {"kind": kind, "size_bytes": size, "mode": "0o644", "link_target": target}
        special = "Hard links, devices, FIFOs and other special members are forbidden"
        variants = {
            "hard link kind": (lambda rows: rows.update({RELEASE + "/x": row("hardlink")}), special),
            "fifo kind": (lambda rows: rows.update({RELEASE + "/x": row("fifo")}), special),
            "device kind": (lambda rows: rows.update({RELEASE + "/x": row("character-device")}), special),
            "absolute name": (lambda rows: rows.update({"/x": row()}), "Unsafe archive path: /x"),
            "traversing name": (lambda rows: rows.update({RELEASE + "/../x": row()}), "Unsafe archive path"),
            "outside the root": (lambda rows: rows.update({"other-root/x": row()}), "Archive member outside the archive root"),
            "escaping link": (lambda rows: rows[RELEASE + "/bin/npm"].update(link_target="../../outside"), "Escaping link target"),
            "absolute link": (lambda rows: rows[RELEASE + "/bin/npm"].update(link_target="/etc/passwd"), "Absolute or malformed link target"),
            "member below a link": (lambda rows: rows.update({RELEASE + "/bin/npm/x": row()}), "Archive member below a link or file"),
            "member below a file": (lambda rows: rows.update({RELEASE + "/README.md/x": row()}), "Archive member below a link or file"),
            "file with a link target": (lambda rows: rows[RELEASE + "/README.md"].update(link_target="x"), "Only a link member has a link target"),
            "link with data": (lambda rows: rows[RELEASE + "/bin/npm"].update(size_bytes=1), "Directory and link members carry no data"),
            "mode outside 0o7777": (lambda rows: rows[RELEASE + "/README.md"].update(mode="0o10644"), "Invalid archive member mode"),
        }
        for label, (mutate, reason) in variants.items():
            with self.subTest(variant=label):
                fixture = self.node_fixture()
                mutate(fixture.plan["members"])
                self.refreeze(fixture)
                with self.spies() as spy:
                    self.refuses(lambda: self.install(fixture), reason=reason)
                spy.opened.assert_not_called()
                self.assert_nothing_staged(fixture)

    def test_MC03_declared_links_are_accepted_not_extracted_or_followed_dry_run(self):
        """Dry run on the synthetic layout with three declared links; only the Node member's data is read."""
        fixture = self.node_fixture()
        with self.spies() as spy, self.no_fallback():
            result = self.install(fixture, apply=False)
        self.assertEqual((result["state"], result["passed"]), ("DRY_RUN_READY", True))
        self.assertEqual(result["archive"]["symlinks"], 3)
        self.assertEqual(result["archive"]["extracted_members"], [NODE_MEMBER])
        self.assertEqual(self.read_names(spy), [NODE_MEMBER])
        spy.staged.assert_not_called()
        self.assert_nothing_staged(fixture)

    def test_MC04_node_member_missing_refuses(self):
        without = [item for item in node_entries() if item["name"] != NODE_MEMBER]
        with self.subTest(case="declared but absent from the archive"):
            fixture = self.node_fixture(without, declared=node_entries())
            self.assert_refused_before_staging(fixture, "Archive is missing declared members")
        with self.subTest(case="absent from archive and inventory"):
            fixture = self.node_fixture(without)
            self.assert_refused_before_staging(fixture, "The Node member must be a declared regular file")

    def test_MC04_node_member_not_a_declared_regular_file_refuses(self):
        others = [item for item in node_entries() if item["name"] != NODE_MEMBER]
        link = entry("symlink", NODE_MEMBER, 0o755, target="../lib/node_modules/npm/bin/npm-cli.js")
        with self.subTest(case="declared as a link"):
            fixture = self.node_fixture(others + [link])
            self.assert_refused_before_staging(fixture, "The Node member must be a declared regular file")
        with self.subTest(case="declared file, archive link"):
            fixture = self.node_fixture(others + [link], declared=node_entries())
            self.assert_refused_before_staging(fixture, "differs from the frozen inventory: " + NODE_MEMBER)
        with self.subTest(case="declared file, archive hard link"):
            hard = entry("hardlink", NODE_MEMBER, 0o755, target=RELEASE + "/README.md")
            fixture = self.node_fixture(others + [hard], declared=node_entries())
            self.assert_refused_before_staging(fixture, "Hard link archive members are forbidden")
        with self.subTest(case="declared file, archive directory"):
            fixture = self.node_fixture(others + [entry("directory", NODE_MEMBER, 0o755)], declared=node_entries())
            self.assert_refused_before_staging(fixture, "differs from the frozen inventory: " + NODE_MEMBER)

    def test_MC05_executable_not_thin_arm64_macho_refuses(self):
        """The plan freezes these bytes; only the header predicate refuses them."""
        variants = {
            "universal (fat) header": (struct.pack(">II", 0xCAFEBABE, 1) + bytes(24) + b"fat\n", "not a thin 64-bit"),
            "32-bit header": (struct.pack("<8I", 0xFEEDFACE, 12, 0, 2, 0, 0, 0, 0), "not a thin 64-bit"),
            "big-endian 64-bit header": (struct.pack(">8I", 0xFEEDFACF, 0x0100000C, 0, 2, 0, 0, 0, 0), "not a thin 64-bit"),
            "x86_64 cputype": (struct.pack("<8I", 0xFEEDFACF, 0x01000007, 3, 2, 0, 0, 0, 0), "not an arm64"),
            "dylib file type": (struct.pack("<8I", 0xFEEDFACF, 0x0100000C, 0, 6, 0, 0, 0, 0), "not a Mach-O executable"),
            "truncated header": (MACHO[:16], "shorter than a 64-bit Mach-O header"),
            "script": (b"#!/bin/sh\n# inert synthetic text, never executed\n", "not a thin 64-bit"),
        }
        for label, (data, reason) in variants.items():
            with self.subTest(variant=label):
                fixture = self.node_fixture(executable=data)
                with self.spies() as spy:
                    self.refuses(lambda: self.install(fixture), reason=reason)
                spy.staged.assert_not_called()
                self.assertEqual(self.read_names(spy), [NODE_MEMBER])
                self.assert_nothing_staged(fixture)

    def test_MC05_executable_digest_size_or_mode_other_than_frozen_refuses(self):
        size = len(MACHO)
        with self.subTest(case="digest"):
            fixture = self.node_fixture(frozen={"sha256": sha256(b"\0" * size), "size_bytes": size, "mode": "0o755"})
            self.assert_refused_before_staging(fixture, "Node executable bytes differ from the frozen plan", read=[NODE_MEMBER])
        with self.subTest(case="size, declared consistently"):
            declared = node_entries()
            declared[2] = entry("file", NODE_MEMBER, 0o755, MACHO + b"!")
            fixture = self.node_fixture(declared=declared, frozen={"sha256": sha256(MACHO + b"!"), "size_bytes": size + 1, "mode": "0o755"})
            self.assert_refused_before_staging(fixture, "differs from the frozen inventory: " + NODE_MEMBER)
        with self.subTest(case="size, frozen only"):
            fixture = self.node_fixture(frozen={"sha256": sha256(MACHO), "size_bytes": size + 1, "mode": "0o755"})
            self.assert_refused_before_staging(fixture, "Declared Node member size differs from the frozen executable")
        with self.subTest(case="mode"):
            fixture = self.node_fixture(frozen={"sha256": sha256(MACHO), "size_bytes": size, "mode": "0o750"})
            self.assert_refused_before_staging(fixture, "The Node executable mode must be 0o755")

    def test_MC05_staged_mode_change_refuses_before_publication(self):
        """Simulated: os.fchmod applies 0o700 to the staged executable; the exact-tree check refuses before renamex_np."""
        fixture = self.node_fixture()
        if not DARWIN:
            return self.assert_platform_refusal(fixture)
        real = os.fchmod
        with self.spies() as spy, patch.object(os, "fchmod", side_effect=lambda fd, mode: real(fd, 0o700 if mode == 0o755 else mode)):
            self.refuses(lambda: self.install(fixture), reason="Locked file identity differs")
        spy.published.assert_not_called()
        self.assertEqual(spy.staged.call_count, 1)
        self.assert_nothing_staged(fixture)

    def test_dry_run_reads_the_archive_and_creates_only_the_preflight_record(self):
        fixture = self.node_fixture()
        result = self.install(fixture, apply=False)
        self.assertEqual((result["state"], result["before"]), ("DRY_RUN_READY", {"state": "absent"}))
        self.assertEqual(result["execution_counts"], ZERO_STARTS)
        self.assertEqual(result["archive"]["member_inventory_sha256"], sha256(canonical(fixture.inventory)))
        self.assertEqual(result["archive"]["executable"]["macho"],
                         {"magic": "0xfeedfacf", "cputype": "0x0100000c", "cpusubtype": "0x00000000", "filetype": 2})
        self.assertEqual(json.loads(fixture.report.read_bytes()), result)
        self.assertTrue(fixture.report.with_name(fixture.report.name + ".preflight.json").is_file())
        self.assertFalse(fixture.report.with_name(fixture.report.name + ".publication.json").exists())
        self.assert_nothing_staged(fixture)

    def test_node_source_bytes_are_built_from_the_plan_and_must_equal_the_frozen_bytes(self):
        fixture = self.node_fixture()
        self.assertEqual(preparer.node_source_bytes_v02(fixture.plan), fixture.raw)
        differ = "NODE-SOURCE.json bytes differ from the plan's frozen digest and size"
        variants = {
            "frozen digest of other bytes": (lambda plan: plan["files"]["NODE-SOURCE.json"].update(sha256="2" * 64), differ),
            "frozen size differs": (lambda plan: plan["files"]["NODE-SOURCE.json"].update(size_bytes=len(fixture.raw) + 1), differ),
            "signature detail changed": (lambda plan: plan["node_source"]["signature_check"].update(detail="changed"), differ),
            "archive size changed": (lambda plan: plan["archive"].update(size_bytes=plan["archive"]["size_bytes"] + 1), differ),
            "signature status unknown": (lambda plan: plan["node_source"]["signature_check"].update(status="skipped"),
                                         "Unknown signature-check status"),
            "signature detail not ASCII": (lambda plan: plan["node_source"]["signature_check"].update(detail="caf\u00e9"),
                                           "bounded ASCII text"),
            "signature detail empty": (lambda plan: plan["node_source"]["signature_check"].update(detail=""),
                                       "bounded ASCII text"),
            "extra provenance key": (lambda plan: plan["node_source"].update(extra=True), "missing or unknown members"),
        }
        for label, (mutate, reason) in variants.items():
            with self.subTest(variant=label):
                candidate = self.node_fixture()
                mutate(candidate.plan)
                with self.spies() as spy:
                    self.refuses(lambda: self.install(candidate), reason=reason)
                spy.staged.assert_not_called()
                self.assert_nothing_staged(candidate)

    def test_member_inventory_digest_is_sha256_of_canonical_json(self):
        fixture = self.node_fixture()
        reordered = dict(reversed(list(fixture.inventory.items())))
        self.assertEqual(preparer.member_inventory_sha256_v02(reordered), sha256(canonical(fixture.inventory)))
        with self.assertRaises(provider.CurrentHostBindingError):
            preparer.member_inventory_sha256_v02({RELEASE + "/caf\u00e9": fixture.inventory[NODE_MEMBER]})


class Publication(PreparerCase):
    """Contract section 6: staging, renamex_np with RENAME_EXCL, receipts (MC03, MC15, MC16)."""

    def test_MC03_install_publishes_exactly_bin_node_and_node_source(self):
        """Real: one install of the synthetic archive and one real renamex_np; then exact reuse."""
        fixture = self.node_fixture()
        if not DARWIN:
            return self.assert_platform_refusal(fixture)
        with self.spies() as spy, self.no_fallback():
            result = self.install(fixture)
        self.assertEqual((result["state"], result["passed"], result["execution_counts"]),
                         ("INSTALLED_EXACT", True, ZERO_STARTS))
        self.assertEqual(spy.published.call_count, 1)
        self.assertEqual(self.read_names(spy), [NODE_MEMBER, NODE_MEMBER])
        destination = fixture.destination
        self.assertEqual(sorted(row[0] for row in snapshot(destination)), [".", "NODE-SOURCE.json", "bin", "bin/node"])
        self.assertEqual([row[1] for row in snapshot(destination)], ["dir", "file", "dir", "file"])
        self.assertEqual((destination / "bin/node").read_bytes(), fixture.executable)
        self.assertEqual((destination / "NODE-SOURCE.json").read_bytes(), fixture.raw)
        self.assertEqual([oct(stat.S_IMODE(os.lstat(destination / name).st_mode)) for name in ("", "bin", "bin/node", "NODE-SOURCE.json")],
                         ["0o755", "0o755", "0o755", "0o644"])
        self.assertEqual(result["after"], {"state": "complete_exact", "files": 2, "directories": 1})
        self.assertEqual(result["publication"], {"call": "renamex_np", "library": "/usr/lib/libSystem.B.dylib",
                                                 "flag": "RENAME_EXCL", "flag_value": 4})
        self.assertEqual(result["pins"]["origin"], "synthetic-test-seam")
        self.assertEqual(json.loads(fixture.report.read_bytes()), result)
        intent = json.loads(fixture.report.with_name(fixture.report.name + ".publication.json").read_bytes())
        self.assertEqual((intent["call"], intent["mode"], intent["destination"]), ("renamex_np", "RENAME_EXCL", str(destination)))
        self.assertEqual([row["operation"] for row in result["operations"]], ["created_owned_stage"])
        self.assertEqual(sorted(path.name for path in self.base.glob(".current-host-stage-*")), [])
        before = snapshot(destination)
        with self.spies() as spy:
            reused = preparer.install_plan_v02(self.renew(fixture), apply=True, synthetic_pins=fixture.pins)
        self.assertEqual((reused["state"], reused["execution_counts"]), ("ALREADY_PRESENT_EXACT", ZERO_STARTS))
        spy.staged.assert_not_called()
        spy.published.assert_not_called()
        self.assertEqual(snapshot(destination), before)

    def test_MC15_real_renamex_np_refuses_an_existing_destination(self):
        """Real: EEXIST for an existing empty directory, a populated directory and a file; nothing replaced."""
        source = self.base / "source"
        source.mkdir()
        (source / "payload").write_bytes(b"staged")
        empty, populated, regular = self.base / "empty", self.base / "populated", self.base / "regular"
        empty.mkdir()
        populated.mkdir()
        (populated / "other").write_bytes(b"another writer")
        regular.write_bytes(b"another writer")
        if not DARWIN:
            with self.assertRaises(provider.CurrentHostBindingError):
                preparer.rename_exclusive(source, empty)
            return
        before = {path: snapshot(path) for path in (source, empty, populated, regular)}
        with self.no_fallback():
            for target in (empty, populated, regular):
                with self.subTest(target=target.name):
                    with self.assertRaises(OSError) as caught:
                        preparer.rename_exclusive(source, target)
                    self.assertEqual(caught.exception.errno, errno.EEXIST)
        self.assertEqual({path: snapshot(path) for path in before}, before)

    def test_MC15_real_conflict_destination_appears_between_staging_and_publication(self):
        """Real conflict: another writer creates the destination after staging; the real renamex_np refuses."""
        fixture = self.node_fixture()
        if not DARWIN:
            return self.assert_platform_refusal(fixture)
        real, seen = preparer.rename_exclusive, []
        def other_writer_then_publish(source, target):
            seen.append(snapshot(source))
            target.mkdir()
            (target / "other-writer").write_bytes(b"another writer's content")
            seen.append(snapshot(target))
            return real(source, target)
        with self.no_fallback(), patch.object(preparer, "rename_exclusive", side_effect=other_writer_then_publish) as published:
            error = self.refuses(lambda: self.install(fixture), reason="Publication conflict")
        self.assertEqual(published.call_count, 1)
        self.assertEqual(sorted(row[0] for row in seen[0]), [".", "NODE-SOURCE.json", "bin", "bin/node"])
        self.assertEqual(snapshot(fixture.destination), seen[1])
        record = error.refusal_record
        self.assertEqual(record["publication_error"]["errno"], errno.EEXIST)
        self.assertEqual(record["destination_after_error"]["state"], "REFUSED")
        self.assertEqual(record["stage_after_error"], {"state": "owned_stage_present"})
        self.assertEqual([row["operation"] for row in record["operations"]], ["created_owned_stage", "removed_owned_stage"])
        self.assertEqual(sorted(path.name for path in self.base.glob(".current-host-stage-*")), [])
        self.assertEqual(json.loads(fixture.report.read_bytes()), record)

    def cross_volume_parent(self):
        """The checkout's directory when it lies on another volume than the temporary directory."""
        root = preparer.ROOT
        return root if os.stat(root).st_dev != os.stat(self.base).st_dev else None

    def test_MC16_real_failing_calls_refuse_without_fallback(self):
        """Real: renamex_np into its own subtree (EINVAL), and across volumes (EXDEV) where the volumes differ.

        The cross-volume target is a fresh name in the checkout's directory; the
        failing call never creates it.
        """
        source = self.base / "staged"
        source.mkdir()
        (source / "payload").write_bytes(b"staged")
        if not DARWIN:
            with self.assertRaises(provider.CurrentHostBindingError):
                preparer.rename_exclusive(source, self.base / "target")
            return
        cases = [("EINVAL: target inside the source", source / "inside", errno.EINVAL)]
        other = self.cross_volume_parent()
        if other is not None:
            cases.append(("EXDEV: another volume", other / (".w2-never-created-" + uuid.uuid4().hex), errno.EXDEV))
        else:
            self.assertEqual(os.stat(preparer.ROOT).st_dev, os.stat(self.base).st_dev)
        before = snapshot(source)
        with self.no_fallback():
            for label, target, number in cases:
                with self.subTest(case=label):
                    with self.assertRaises(OSError) as caught:
                        preparer.rename_exclusive(source, target)
                    self.assertEqual(caught.exception.errno, number)
                    self.assertFalse(os.path.lexists(target))
                    self.assertEqual(snapshot(source), before)

    def test_MC16_real_failing_call_inside_the_flow_refuses_without_fallback(self):
        """Real kernel failures inside the install flow; the test redirects only the call's target argument."""
        if not DARWIN:
            return self.assert_platform_refusal(self.node_fixture())
        real = preparer.rename_exclusive
        redirects = [("EINVAL", lambda source, target: source / "inside", errno.EINVAL)]
        other = self.cross_volume_parent()
        if other is not None:
            redirects.append(("EXDEV", lambda source, target: other / (".w2-never-created-" + uuid.uuid4().hex), errno.EXDEV))
        for label, redirect, number in redirects:
            with self.subTest(case=label):
                fixture = self.node_fixture()
                targets = []
                def publish(source, target):
                    targets.append(redirect(source, target))
                    return real(source, targets[-1])
                with self.no_fallback(), patch.object(preparer, "rename_exclusive", side_effect=publish) as published:
                    error = self.refuses(lambda: self.install(fixture), reason="Exclusive publication failed")
                self.assertEqual(published.call_count, 1)
                self.assertFalse(os.path.lexists(targets[0]))
                record = error.refusal_record
                self.assertEqual(record["publication_error"]["errno"], number)
                self.assertEqual(record["destination_after_error"], {"state": "absent"})
                self.assertEqual(record["stage_after_error"], {"state": "owned_stage_present"})
                self.assert_nothing_staged(fixture)

    def test_MC16_simulated_enotsup_refuses_without_fallback(self):
        """Simulated: the ctypes renamex_np returns -1 with errno ENOTSUP; no other rename follows."""
        fixture = self.node_fixture()
        if not DARWIN:
            return self.assert_platform_refusal(fixture)
        flags = []
        def unsupported(source, destination, flag):
            flags.append(flag)
            ctypes.set_errno(errno.ENOTSUP)
            return -1
        with self.no_fallback(), patch.object(preparer, "_libsystem_renamex_np", return_value=unsupported):
            error = self.refuses(lambda: self.install(fixture), reason="Exclusive publication failed (ENOTSUP)")
        self.assertEqual(flags, [preparer.RENAME_EXCL])
        record = error.refusal_record
        self.assertEqual(record["publication_error"]["name"], errno.errorcode[errno.ENOTSUP])
        self.assertEqual(record["destination_after_error"], {"state": "absent"})
        self.assert_nothing_staged(fixture)

    def test_uncertain_publication_is_unknown_and_read_back_before_any_retry(self):
        """Simulated lost reply after a real renamex_np: UNKNOWN, readback recorded, one call; a later call reuses."""
        fixture = self.node_fixture()
        if not DARWIN:
            return self.assert_platform_refusal(fixture)
        real = preparer.rename_exclusive
        def lost_reply(source, target):
            real(source, target)
            raise OSError(errno.EIO, "simulated lost reply")
        with self.no_fallback(), patch.object(preparer, "rename_exclusive", side_effect=lost_reply) as published:
            error = self.refuses(lambda: self.install(fixture), state="UNKNOWN", reason="explicit reconciliation")
        self.assertEqual(published.call_count, 1)
        record = error.refusal_record
        self.assertEqual(record["destination_after_error"], {"state": "complete_exact", "files": 2, "directories": 1})
        self.assertEqual(record["stage_after_error"], {"state": "absent"})
        self.assertNotIn("cleanup_error", record)
        self.assertEqual((fixture.destination / "NODE-SOURCE.json").read_bytes(), fixture.raw)
        reused = preparer.install_plan_v02(self.renew(fixture), apply=True, synthetic_pins=fixture.pins)
        self.assertEqual(reused["state"], "ALREADY_PRESENT_EXACT")

    def test_apply_off_darwin_refuses_before_staging(self):
        """Simulated platform: the module's sys is replaced by a value whose platform is linux."""
        fixture = self.node_fixture()
        with self.spies() as spy, patch.object(preparer, "sys", SimpleNamespace(platform="linux")):
            self.refuses(lambda: self.install(fixture), reason="only on Darwin")
        spy.staged.assert_not_called()
        self.assert_nothing_staged(fixture)

    def test_rename_excl_value_and_libsystem_binding(self):
        self.assertEqual((preparer.RENAME_EXCL, preparer.LIBSYSTEM), (0x00000004, "/usr/lib/libSystem.B.dylib"))
        if DARWIN:
            function = preparer._libsystem_renamex_np()
            self.assertEqual(function.argtypes, (ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint))
            self.assertIs(function.restype, ctypes.c_int)


class ExistingDestination(PreparerCase):
    """Reuse of an exact tree; refusal of every other existing destination (MC35)."""

    def assert_refused_untouched(self, fixture, reason=None, *, prepare=lambda: None, restore=lambda: None):
        before = snapshot(fixture.destination)
        prepare()
        try:
            with self.spies() as spy:
                self.refuses(lambda: self.install(fixture), reason=reason)
        finally:
            restore()
        spy.staged.assert_not_called()
        spy.published.assert_not_called()
        self.assertEqual(snapshot(fixture.destination), before)
        self.assertEqual(sorted(path.name for path in self.base.glob(".current-host-stage-*")), [])

    def test_exact_existing_tree_is_reused_already_present_exact(self):
        """A hand-built exact tree; apply and dry run both reuse it without staging or publication."""
        fixture = self.node_fixture()
        before = self.exact_tree(fixture)
        for apply in (True, False):
            with self.subTest(apply=apply), self.spies() as spy:
                result = preparer.install_plan_v02(self.renew(fixture), apply=apply, synthetic_pins=fixture.pins)
                self.assertEqual((result["state"], result["passed"], result["execution_counts"]),
                                 ("ALREADY_PRESENT_EXACT", True, ZERO_STARTS))
                self.assertEqual(result["before"], {"state": "complete_exact", "files": 2, "directories": 1})
                spy.staged.assert_not_called()
                spy.published.assert_not_called()
                self.assertEqual(snapshot(fixture.destination), before)

    def test_MC35_partial_destination_refuses(self):
        for missing in ("NODE-SOURCE.json", "bin/node", "everything"):
            with self.subTest(missing=missing):
                fixture = self.node_fixture()
                self.exact_tree(fixture)
                if missing == "everything":
                    (fixture.destination / "bin/node").unlink()
                    (fixture.destination / "NODE-SOURCE.json").unlink()
                    (fixture.destination / "bin").rmdir()
                else:
                    (fixture.destination / missing).unlink()
                self.assert_refused_untouched(fixture)

    def test_MC35_changed_destination_refuses(self):
        changes = {"executable bytes": lambda d: (d / "bin/node").write_bytes(MACHO + b"changed"),
                   "provenance bytes": lambda d: (d / "NODE-SOURCE.json").write_bytes(b"{}"),
                   "executable mode": lambda d: (d / "bin/node").chmod(0o700),
                   "provenance mode": lambda d: (d / "NODE-SOURCE.json").chmod(0o600),
                   "bin mode": lambda d: (d / "bin").chmod(0o700),
                   "root mode": lambda d: d.chmod(0o700)}
        for label, change in changes.items():
            with self.subTest(change=label):
                fixture = self.node_fixture()
                self.exact_tree(fixture)
                change(fixture.destination)
                self.assert_refused_untouched(fixture)

    def test_MC35_extra_destination_entry_refuses(self):
        extras = {".DS_Store": lambda d: (d / ".DS_Store").write_bytes(b"\0"),
                  "bin/npm": lambda d: (d / "bin/npm").write_bytes(b"extra"),
                  "extra directory": lambda d: (d / "lib").mkdir()}
        for label, add in extras.items():
            with self.subTest(extra=label):
                fixture = self.node_fixture()
                self.exact_tree(fixture)
                add(fixture.destination)
                self.assert_refused_untouched(fixture)

    def test_MC35_linked_destination_refuses(self):
        def executable_symlink(fixture):
            outside = self.path("outside-node")
            outside.write_bytes(fixture.executable)
            outside.chmod(0o755)
            (fixture.destination / "bin/node").unlink()
            (fixture.destination / "bin/node").symlink_to(outside)
        def bin_symlink(fixture):
            outside = self.path("outside-bin")
            shutil.move(str(fixture.destination / "bin"), str(outside))
            (fixture.destination / "bin").symlink_to(outside)
        def executable_hard_link(fixture):
            os.link(fixture.destination / "bin/node", self.path("second-name"))
        for label, link in (("bin/node symlink", executable_symlink), ("bin symlink", bin_symlink),
                            ("bin/node hard link", executable_hard_link)):
            with self.subTest(link=label):
                fixture = self.node_fixture()
                self.exact_tree(fixture)
                link(fixture)
                self.assert_refused_untouched(fixture)
        with self.subTest(link="destination symlink to an exact tree"):
            fixture = self.node_fixture()
            real_destination = fixture.destination
            fixture.destination = self.path("exact-elsewhere")
            self.exact_tree(fixture)
            real_destination.symlink_to(fixture.destination)
            fixture.destination = real_destination
            self.assert_refused_untouched(fixture, "Symlink path component")

    def test_MC35_inaccessible_destination_refuses(self):
        for label in ("destination", "bin", "bin/node"):
            with self.subTest(inaccessible=label):
                fixture = self.node_fixture()
                self.exact_tree(fixture)
                target = fixture.destination if label == "destination" else fixture.destination / label
                mode = stat.S_IMODE(target.lstat().st_mode)
                self.assert_refused_untouched(fixture, prepare=lambda: target.chmod(0), restore=lambda: target.chmod(mode))

    def test_MC35_destination_that_is_a_file_refuses(self):
        fixture = self.node_fixture()
        fixture.destination.write_bytes(b"another writer's file")
        self.assert_refused_untouched(fixture, "Existing destination is not a directory")


class RetainedDependencies(PreparerCase):
    """The C195 reader archive under P05 section 5's rules (MC34)."""

    def test_MC34_unsafe_entries_refuse_before_extraction(self):
        for mutation in ("absolute", "traversal", "duplicate", "symlink", "hardlink", "fifo", "character-device", "mode"):
            with self.subTest(mutation=mutation):
                fixture = self.dependency_fixture(mutation)
                with self.spies() as spy, self.no_fallback():
                    self.refuses(lambda: self.install(fixture))
                spy.staged.assert_not_called()
                self.assertIsNone(snapshot(fixture.destination))

    def test_MC34_inventory_cannot_declare_links_special_entries_or_unexpected_modes(self):
        forbidden = "Links and special archive members are forbidden"
        variants = {"link kind": (lambda rows, name: rows[name].update(kind="symlink"), forbidden),
                    "fifo kind": (lambda rows, name: rows[name].update(kind="fifo"), forbidden),
                    "world-writable mode": (lambda rows, name: rows[name].update(mode="0o777"), "Group/world-writable"),
                    "privileged mode": (lambda rows, name: rows[name].update(mode="0o4755"), "Invalid extraction mode"),
                    "node-route row shape": (lambda rows, name: rows.update({name: {"kind": "file", "size_bytes": 0, "mode": "0o644",
                                                                                     "link_target": None}}),
                                             "missing or unknown members")}
        for label, (mutate, reason) in variants.items():
            with self.subTest(variant=label):
                fixture = self.dependency_fixture()
                mutate(fixture.plan["members"], self.PREFIX + "validator/package/package.json")
                with self.spies() as spy:
                    self.refuses(lambda: self.install(fixture), reason=reason)
                spy.opened.assert_not_called()

    def test_dependency_targets_must_equal_the_pinned_files(self):
        fixture = self.dependency_fixture()
        fixture.pins = self.pins(dependencies=fixture.pins.dependency_archive_sha256,
                                 files={"validator/package/package.json": {"sha256": "3" * 64, "size_bytes": 1},
                                        "indexer-view/three/package.json": dict(fixture.pins.dependency_files["indexer-view/three/package.json"])})
        self.refuses(lambda: self.install(fixture), reason="Retained dependency bytes differ")

    def test_adopted_dependency_pin_is_the_c195_archive(self):
        fixture = self.dependency_fixture()
        with self.assertRaises(provider.CurrentHostBindingError) as caught:
            preparer.validate_plan_v02(fixture.plan)
        self.assertIn("Retained dependency archive differs", caught.exception.reason)

    def test_dependency_install_and_exact_reuse(self):
        """Real on Darwin: one install and one real renamex_np; then ALREADY_PRESENT_EXACT."""
        fixture = self.dependency_fixture()
        dry = self.install(fixture, apply=False)
        self.assertEqual((dry["state"], dry["archive"]["members"], dry["archive"]["symlinks"]), ("DRY_RUN_READY", 5, 0))
        if not DARWIN:
            fixture.plan["report"] = str(self.path("report", ".json"))
            return self.refuses(lambda: self.install(fixture), reason="only on Darwin")
        fixture.plan["report"] = str(self.path("report", ".json"))
        with self.no_fallback():
            result = self.install(fixture)
        self.assertEqual((result["state"], result["execution_counts"]), ("INSTALLED_EXACT", ZERO_STARTS))
        self.assertEqual(sorted(row[0] for row in snapshot(fixture.destination) if row[1] == "file"), sorted(self.PAYLOADS))
        for name, data in self.PAYLOADS.items():
            self.assertEqual((fixture.destination / name).read_bytes(), data)
        before = snapshot(fixture.destination)
        fixture.plan["report"] = str(self.path("report", ".json"))
        reused = self.install(fixture)
        self.assertEqual(reused["state"], "ALREADY_PRESENT_EXACT")
        self.assertEqual(snapshot(fixture.destination), before)


class VersionSeparation(PreparerCase):
    """Dispatch on the plan's schema; each version's entry refuses the other's plans."""

    def v01_plan(self):
        payload = self.base / "payload.txt"
        payload.write_bytes(b"inert fixture\n")
        archive = self.path("v01", ".tar")
        with tarfile.open(archive, "w", format=tarfile.USTAR_FORMAT) as handle:
            info = tarfile.TarInfo("payload.txt")
            info.mode, info.size, info.mtime = 0o644, len(payload.read_bytes()), 0
            handle.addfile(info, io.BytesIO(payload.read_bytes()))
        archive.chmod(0o600)
        row = {"sha256": sha256(payload.read_bytes()), "size_bytes": len(payload.read_bytes()), "mode": "0o644"}
        return {"schema": preparer.SCHEMA, "purpose": "isolated-control", "source": None,
                "archive": {"path": str(archive), **binding(archive)}, "destination": str(self.path("installed")),
                "root_mode": "0o755", "files": {"payload.txt": row}, "directories": {},
                "members": {"payload.txt": {"kind": "file", **row, "target": "payload.txt"}},
                "report": str(self.path("report", ".json"))}

    def write_plan(self, plan):
        path = self.path("plan", ".json")
        path.write_bytes(canonical(plan))
        path.chmod(0o600)
        return path, sha256(path.read_bytes())

    def cli(self, argv):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = preparer.main(argv)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_v02_entry_refuses_a_v01_plan(self):
        plan = self.v01_plan()
        self.assertEqual(preparer.SCHEMA, "ontokin.current-host-readback-install/0.1.0")
        with self.spies() as spy:
            self.refuses(lambda: preparer.install_plan_v02(plan, apply=True, synthetic_pins=self.pins()),
                         reason="refuses a plan of another schema version")
        spy.opened.assert_not_called()
        self.assertIsNone(snapshot(Path(plan["destination"])))

    def test_v01_entry_refuses_a_v02_plan(self):
        fixture = self.node_fixture()
        with self.spies() as spy:
            with self.assertRaises(provider.CurrentHostBindingError) as caught:
                preparer.install_plan(fixture.plan, apply=True)
        self.assertEqual((caught.exception.code, caught.exception.refusal_record["schema"]),
                         ("CH-INSTALL", "ontokin.current-host-readback-install-result/0.1.0"))
        spy.opened.assert_not_called()
        self.assertIsNone(snapshot(fixture.destination))
        with self.assertRaises(provider.CurrentHostBindingError):
            preparer._plan_shape(fixture.plan)

    def test_v02_plan_naming_another_contract_or_purpose_is_refused(self):
        for key, value, reason in (("contract", "ontokin.current-host-readback/0.1.0", "another contract"),
                                   ("purpose", "isolated-control", "Unknown 0.2.0 installation purpose")):
            with self.subTest(key=key):
                fixture = self.node_fixture()
                fixture.plan[key] = value
                self.refuses(lambda: self.install(fixture), reason=reason)

    def test_v02_plan_paths_bind_this_checkout_and_stay_outside_it(self):
        """Refused paths are never written: not in the checkout, not over an existing report.

        Dry runs only, so even a regression could not stage or publish a tree in
        the checkout. The names inside the checkout are unique per run; a cleanup
        removes such a file only if a regression created it.
        """
        inside = preparer.ROOT / (".w2-never-created-" + uuid.uuid4().hex)
        names = (inside, inside.with_name(inside.name + ".json"), inside.with_name(inside.name + ".json.preflight.json"))
        for name in names:
            self.addCleanup(lambda name=name: name.unlink() if name.is_file() and not name.is_symlink() else None)
        mutations = {"other checkout": ("source_root", lambda fixture: str(self.base), "another source checkout"),
                     "destination inside source": ("destination", lambda fixture: str(inside), "Installed inputs must be outside source"),
                     "report inside source": ("report", lambda fixture: str(names[1]), "Fresh report must be outside"),
                     "report inside destination": ("report", lambda fixture: str(fixture.destination / "report.json"), "Fresh report must be outside"),
                     "report parent missing": ("report", lambda fixture: str(self.base / "missing" / "report.json"), "Fresh report must be outside"),
                     "existing report": ("report", None, "Fresh report must be outside")}
        for label, (key, value, reason) in mutations.items():
            with self.subTest(case=label):
                fixture = self.node_fixture()
                if value is None:
                    fixture.report.write_bytes(b"earlier report")
                else:
                    fixture.plan[key] = value(fixture)
                self.refuses(lambda: self.install(fixture, apply=False), reason=reason)
                self.assertEqual([name for name in names if os.path.lexists(name)], [])
                self.assertFalse(os.path.lexists(self.base / "missing"))
                if value is None:
                    self.assertEqual(fixture.report.read_bytes(), b"earlier report")
                    self.assertFalse(fixture.report.with_name(fixture.report.name + ".preflight.json").exists())
                self.assertIsNone(snapshot(fixture.destination))

    def test_cli_dispatches_a_v02_plan_to_the_v02_route_with_the_adopted_pin_only(self):
        """The CLI cannot pass SyntheticPins, so a synthetic archive meets the adopted pin and refuses."""
        self.assertEqual(preparer.NODE_ARCHIVE_SHA256_V02, ADOPTED_PIN)
        fixture = self.node_fixture()
        path, digest = self.write_plan(fixture.plan)
        for extra in ([], ["--apply"]):
            with self.subTest(apply=bool(extra)):
                code, stdout, stderr = self.cli(["--plan", str(path), "--plan-sha256", digest, *extra])
                self.assertEqual((code, stdout), (1, ""))
                output = json.loads(stderr)
                self.assertIn("differs from the adopted pin", output["error"]["reason"])
                record = output["refusal_record"]
                self.assertEqual((record["schema"], record["pins"]["origin"]), (RESULT, "adopted-contract"))
                self.assertIsNone(snapshot(fixture.destination))

    def test_cli_v02_digest_mismatch_has_a_v02_refusal_record(self):
        fixture = self.node_fixture()
        path, _ = self.write_plan(fixture.plan)
        code, _, stderr = self.cli(["--plan", str(path), "--plan-sha256", "4" * 64])
        output = json.loads(stderr)
        self.assertEqual(code, 1)
        self.assertIn("independently frozen expected digest", output["error"]["reason"])
        self.assertEqual(output["refusal_record"]["schema"], RESULT)
        self.assertFalse(fixture.report.exists())

    def test_cli_keeps_the_v01_route_for_v01_plans(self):
        plan = self.v01_plan()
        path, digest = self.write_plan(plan)
        code, _, stderr = self.cli(["--plan", str(path), "--plan-sha256", digest, "--apply"])
        output = json.loads(stderr)
        self.assertEqual(code, 1)
        self.assertEqual(output["error"]["reason"], "Isolated controls cannot install operational inputs through the CLI")
        self.assertIsNone(snapshot(Path(plan["destination"])))

    def test_seam_accepts_only_synthetic_pins(self):
        fixture = self.node_fixture()
        for value in ({"node_archive_sha256": fixture.pins.node_archive_sha256}, "pins"):
            with self.subTest(value=type(value).__name__):
                self.refuses(lambda: preparer.install_plan_v02(fixture.plan, apply=False, synthetic_pins=value),
                             reason="only SyntheticPins")


class ResultShapes(PreparerCase):
    """Decisions D-11, D-03, D-12, D-04 and D-02: closed shapes, revision, amendments and labels."""

    def assert_shape(self, record, keys):
        self.assertEqual(set(record), keys)
        self.assertEqual((record["schema"], record["contract"], record["design_revision"], record["amendments"]),
                         (RESULT, CONTRACT, DESIGN_REVISION, AMENDMENTS))
        self.assertEqual(record["execution_counts"], ZERO_STARTS)
        self.assertIsInstance(record["operations"], list)
        labels = record["labels"]
        self.assertEqual(set(labels), LABEL_KEYS)
        self.assertEqual({key: labels[key] for key in ("executor", "contract", "profile", "design_revision", "amendments")},
                         {"executor": "macos-arm64-local", "contract": CONTRACT, "profile": PROFILE,
                          "design_revision": DESIGN_REVISION, "amendments": AMENDMENTS})
        if record["pins"] is not None:
            self.assertEqual(set(record["pins"]), {"origin", "node_archive_sha256", "dependency_archive_sha256"})
        if record["preparer_source"] is not None:
            self.assertEqual(set(record["preparer_source"]), {"root", "files_at_start"})
            self.assertEqual(set(record["preparer_source"]["files_at_start"]), PREPARER_FILES)
        if "error" in record:
            self.assertEqual(set(record["error"]), {"code", "reason", "state", "cause"})
        return record

    def preflight(self, fixture):
        return json.loads(fixture.report.with_name(fixture.report.name + ".preflight.json").read_bytes())

    def test_D11_plan_keys_are_closed_and_equal_the_receipt_rule(self):
        self.assertEqual(set(preparer.PLAN_KEYS_V02), PLAN_KEYS)
        self.assertEqual(set(observation.INSTALL_PLAN_KEYS), PLAN_KEYS)
        for label, mutate in (("extra key", lambda plan: plan.update(extra=None)),
                              ("missing key", lambda plan: plan.pop("node_source"))):
            with self.subTest(case=label):
                fixture = self.node_fixture()
                mutate(fixture.plan)
                self.refuses(lambda: self.install(fixture, apply=False), reason="missing or unknown members")

    def test_D11_result_keys_are_closed_by_state_without_publication(self):
        """Dry run, reuse, and refusals before and after the report path is bound; no renamex_np."""
        self.assertEqual(RECEIPT_KEYS, W3_RESULT_KEYS | {"design_revision", "amendments"})
        self.assertTrue(W3_RESULT_KEYS <= set(observation.INSTALL_RECEIPT_KEYS["ALREADY_PRESENT_EXACT"]) <= RECEIPT_KEYS)
        with self.subTest(state="DRY_RUN_READY"):
            fixture = self.node_fixture()
            dry = self.assert_shape(self.install(fixture, apply=False), RECEIPT_KEYS)
            self.assertEqual((dry["state"], dry["passed"], dry["before"]), ("DRY_RUN_READY", True, {"state": "absent"}))
            self.assertEqual(set(dry["archive"]), ARCHIVE_KEYS | {"executable"})
            self.assertEqual(set(dry["archive"]["executable"]), {"member", "path", "sha256", "size_bytes", "mode", "macho"})
            self.assertEqual(set(dry["archive"]["executable"]["macho"]), {"magic", "cputype", "cpusubtype", "filetype"})
            self.assertEqual(self.preflight(fixture), {**dry, "state": "PREFLIGHT_RECORDED", "passed": False})
        with self.subTest(state="ALREADY_PRESENT_EXACT"):
            fixture = self.node_fixture()
            self.exact_tree(fixture)
            reused = self.assert_shape(self.install(fixture), RECEIPT_KEYS)
            self.assertEqual((reused["state"], reused["before"]), ("ALREADY_PRESENT_EXACT",
                                                                    {"state": "complete_exact", "files": 2, "directories": 1}))
            self.assertEqual(json.loads(fixture.report.read_bytes()), reused)
        with self.subTest(state="DRY_RUN_READY, retained-dependencies"):
            fixture = self.dependency_fixture()
            dry = self.assert_shape(self.install(fixture, apply=False), RECEIPT_KEYS)
            self.assertEqual(set(dry["archive"]), ARCHIVE_KEYS)
        with self.subTest(state="REJECTED before the report path"):
            fixture = self.node_fixture()
            fixture.plan["contract"] = "ontokin.current-host-readback/0.1.0"
            record = self.assert_shape(self.refuses(lambda: self.install(fixture)).refusal_record, RESULT_BASE | {"error"})
            self.assertEqual((record["purpose"], record["labels"]["pins"]), (None, None))
            self.assertFalse(fixture.report.exists())
        with self.subTest(state="REJECTED after the archive pass"):
            fixture = self.node_fixture()
            self.exact_tree(fixture)
            (fixture.destination / "bin/node").write_bytes(MACHO + b"changed")
            record = self.assert_shape(self.refuses(lambda: self.install(fixture)).refusal_record,
                                       RESULT_BASE | {"archive", "error"})
            self.assertEqual(json.loads(fixture.report.read_bytes()), record)
        with self.subTest(state="REJECTED by the seam"):
            fixture = self.node_fixture()
            record = self.refuses(lambda: preparer.install_plan_v02(fixture.plan, synthetic_pins="pins")).refusal_record
            self.assert_shape(record, RESULT_BASE | {"error"})
            self.assertEqual((record["pins"], record["preparer_source"], record["labels"]["os"]), (None, None, None))

    def test_D11_result_keys_are_closed_by_state_with_publication(self):
        """Real on Darwin: an install, a conflict (EEXIST), and a simulated lost reply after a real call."""
        if not DARWIN:
            return self.assert_platform_refusal(self.node_fixture())
        with self.subTest(state="INSTALLED_EXACT"):
            fixture = self.node_fixture()
            installed = self.assert_shape(self.install(fixture), INSTALLED_KEYS)
            self.assertEqual(set(installed["after"]), {"state", "files", "directories"})
            self.assertEqual(set(installed["publication"]), {"call", "library", "flag", "flag_value"})
            self.assertEqual(json.loads(fixture.report.read_bytes()), installed)
            preflight = self.preflight(fixture)
            self.assertEqual((set(preflight), preflight["state"], preflight["passed"]),
                             (RECEIPT_KEYS, "PREFLIGHT_RECORDED", False))
            intent = json.loads(fixture.report.with_name(fixture.report.name + ".publication.json").read_bytes())
            self.assertEqual(set(intent), {"contract", "design_revision", "amendments", "source", "destination",
                                           "owned_stage", "call", "mode", "state"})
            self.assertEqual((intent["contract"], intent["design_revision"], intent["amendments"], intent["state"]),
                             (CONTRACT, DESIGN_REVISION, AMENDMENTS, "INTENT_RECORDED"))
        real = preparer.rename_exclusive
        def conflict(source, target):
            target.mkdir()
            (target / "other-writer").write_bytes(b"another writer")
            return real(source, target)
        def lost_reply(source, target):
            real(source, target)
            raise OSError(errno.EIO, "simulated lost reply")
        for state, publish, after in (("REJECTED", conflict, "REFUSED"), ("UNKNOWN", lost_reply, "complete_exact")):
            with self.subTest(state=state + " at publication"):
                fixture = self.node_fixture()
                with patch.object(preparer, "rename_exclusive", side_effect=publish):
                    record = self.refuses(lambda: self.install(fixture), state=state).refusal_record
                self.assert_shape(record, PUBLICATION_FAILURE_KEYS)
                self.assertEqual(set(record["publication_error"]), {"errno", "name", "reason"})
                self.assertEqual(record["destination_after_error"]["state"], after)
                self.assertEqual(set(record["stage_after_error"]), {"state"})
                self.assertEqual(json.loads(fixture.report.read_bytes()), record)

    def test_D12_every_written_result_carries_the_revision_and_amendments(self):
        """The CLI's digest-mismatch record too; it reads no OS identity."""
        fixture = self.node_fixture()
        path = self.path("plan", ".json")
        path.write_bytes(canonical(fixture.plan))
        path.chmod(0o600)
        stderr = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(stderr):
            self.assertEqual(preparer.main(["--plan", str(path), "--plan-sha256", "5" * 64]), 1)
        record = self.assert_shape(json.loads(stderr.getvalue())["refusal_record"], RESULT_BASE | {"error"})
        self.assertIsNone(record["labels"]["os"])

    def test_D12_node_source_keeps_the_plan_4_2_keys(self):
        """NODE-SOURCE.json is not a result: its keys stay those of plan section 4.2, as the observer checks them."""
        fixture = self.node_fixture()
        self.assertEqual(set(json.loads(preparer.node_source_bytes_v02(fixture.plan))), NODE_SOURCE_KEYS)
        self.assertEqual(set(observation.NODE_SOURCE_KEYS), NODE_SOURCE_KEYS)

    def test_D04_labels_carry_identity_pins_and_os_identity_only(self):
        """The real reader on Darwin, checked against an independent plistlib read; no Python or Git label."""
        node = self.node_fixture()
        labels = self.install(node, apply=False)["labels"]
        self.assertEqual(labels["pins"], {"origin": "synthetic-test-seam", "node_archive_sha256": node.plan["archive"]["sha256"],
                                          "node_executable": node.plan["files"]["bin/node"]})
        self.assertEqual(labels["os"], expected_os_label())
        self.assertEqual(set(labels["os"]), {"product_version", "product_build_version", "product_version_extra", "cryptex"})
        self.assertEqual([key for key in labels if "python" in key or "git" in key or "inventory" in key], [])
        dependencies = self.dependency_fixture()
        labels = self.install(dependencies, apply=False)["labels"]
        self.assertEqual(labels["pins"], {"origin": "synthetic-test-seam",
                                          "dependency_archive_sha256": dependencies.plan["archive"]["sha256"]})
        self.assertEqual(labels["os"], expected_os_label())

    def test_D04_unreadable_os_identity_refuses_before_the_archive_is_read(self):
        """Simulated: the observer's read_os_identity raises its own refusal."""
        fixture = self.node_fixture()
        def unreadable(**options):
            raise observation.ObservationError("OS", "simulated unreadable OS identity")
        with patch.object(observation, "read_os_identity", side_effect=unreadable), self.spies() as spy:
            error = self.refuses(lambda: self.install(fixture), reason="The OS identity is unreadable")
        self.assertEqual(error.cause["code"], "CHO-OS")
        self.assertIsNone(error.refusal_record["labels"]["os"])
        spy.opened.assert_not_called()
        spy.staged.assert_not_called()
        self.assert_nothing_staged(fixture)

    def test_D02_failed_signature_check_is_recorded_not_refused(self):
        """Real on Darwin: the install publishes NODE-SOURCE.json with the recorded failed status."""
        signature = {"status": "failed", "detail": "Synthetic development record: the release-key check failed."}
        fixture = self.node_fixture(signature=signature)
        self.assertEqual(self.install(fixture, apply=False)["state"], "DRY_RUN_READY")
        self.assertEqual(json.loads(preparer.node_source_bytes_v02(fixture.plan))["signature_check"], signature)
        if DARWIN:
            self.assertEqual(preparer.install_plan_v02(self.renew(fixture), apply=True,
                                                       synthetic_pins=fixture.pins)["state"], "INSTALLED_EXACT")
            self.assertEqual(json.loads((fixture.destination / "NODE-SOURCE.json").read_bytes())["signature_check"],
                             signature)

    def test_report_write_failure_is_unknown_and_never_passed(self):
        """Simulated: the final report write fails after a passing dry run."""
        fixture = self.node_fixture()
        real = provider._write_new
        def failing(path, value):
            if Path(path) == fixture.report:
                raise provider.CurrentHostBindingError("EVIDENCE", "simulated report write failure", state="UNKNOWN")
            return real(path, value)
        with patch.object(provider, "_write_new", side_effect=failing):
            error = self.refuses(lambda: self.install(fixture, apply=False), code="CH-EVIDENCE", state="UNKNOWN")
        record = self.assert_shape(error.refusal_record, RECEIPT_KEYS | {"error", "report_error"})
        self.assertEqual((record["passed"], record["state"], record["error"]["code"]), (False, "UNKNOWN", "CH-EVIDENCE"))
        self.assertFalse(fixture.report.exists())


if __name__ == "__main__":
    unittest.main()
