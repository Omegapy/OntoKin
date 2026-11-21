"""Independent C271 P10 ELF bytes and fault recipes, without image execution.

The oracle was frozen by /root/elf_review before production edits. Its SHA-256
is 35b8535599cc24276dfe66e57b9ed80348c12d429e9a61441c4f449a7cb4ce8a.
Fixture compression is lossless; each raw file is checked against that oracle.
ONTOKIN_ELF_RETAIN_ROOT preserves actual files and observations for the guarded
phase run. Ordinary unittest use creates temporary private files instead.
"""
from contextlib import ExitStack
import base64
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zlib

from prototypes.static_tray_v01 import current_host_inspection_v01 as inspection


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "current_host_elf_mapping_v01"
ORACLE_BYTES = (FIXTURE_ROOT / "ORACLE.json").read_bytes()
ORACLE_SHA256 = "35b8535599cc24276dfe66e57b9ed80348c12d429e9a61441c4f449a7cb4ce8a"
if hashlib.sha256(ORACLE_BYTES).hexdigest() != ORACLE_SHA256:
    raise ValueError("Independent ELF oracle identity changed")
ORACLE = json.loads(ORACLE_BYTES)
ENCODED = json.loads((FIXTURE_ROOT / "FIXTURES.json").read_text())
if ENCODED["oracle_sha256"] != ORACLE_SHA256:
    raise ValueError("ELF fixture encoding identifies a different oracle")
FILES = {row["name"]: row for row in ENCODED["files"]}
if len(FILES) != len(ENCODED["files"]):
    raise ValueError("Duplicate encoded ELF fixture")


class ELFMappingControls(unittest.TestCase):
    def run_frozen_case(self, case):
        row = FILES[case["fixture"]]
        self.assertEqual(row["encoding"], "zlib+base64")
        raw = zlib.decompress(base64.b64decode(row["data"], validate=True))
        self.assertEqual(len(raw), case["size_bytes"])
        self.assertEqual(hashlib.sha256(raw).hexdigest(), case["sha256"])
        self.assertEqual(row["sha256"], case["sha256"])
        self.assertEqual(row["size_bytes"], case["size_bytes"])
        retained = os.environ.get("ONTOKIN_ELF_RETAIN_ROOT")
        if retained:
            parent = Path(retained)
            self.assertTrue(parent.is_absolute() and parent.is_dir())
            directory = parent / case["id"]
            directory.mkdir(mode=0o700)
        else:
            temporary = tempfile.TemporaryDirectory(prefix="ontokin-elf-")
            self.addCleanup(temporary.cleanup)
            directory = Path(temporary.name)
        image = directory / "input.elf"
        image.write_bytes(raw)
        image.chmod(int(case["mode"], 8))
        fault = case["fault"]
        reads, triggered = [], []
        timeout = inspection.HostInspectionError("PLAN", "Frozen independent deadline", state="TIMEOUT")
        actual_pread = os.pread
        target = None if not fault or fault["piece_index"] is None else fault["piece_file_offsets"][fault["piece_index"]]

        def checked_read(fd, size, offset):
            data = actual_pread(fd, size, offset)
            observed = {"offset": offset, "requested": size, "returned": len(data)}
            reads.append(observed)
            if fault and offset == target and not triggered:
                triggered.append(offset)
                if fault["kind"] == "short_read":
                    data = data[:-1]
                    observed["returned"] = len(data)
                elif fault["kind"] == "mutate_after_piece":
                    with image.open("ab") as stream:
                        stream.write(b"\0")
            return data

        def check():
            if fault and (fault["kind"] == "deadline_initial" or
                          fault["kind"] == "deadline_after_piece" and triggered):
                raise timeout

        caught, observed = None, None
        try:
            with ExitStack() as stack:
                stack.enter_context(patch.object(inspection.os, "pread", side_effect=checked_read))
                value = inspection.read_elf_metadata(image, check=check, require_interpreter=case["require_interpreter"])
                observed = {"outcome": "metadata", "value": value}
        except inspection.HostInspectionError as exc:
            caught = exc
            observed = {"outcome": "refusal", "code": exc.code, "reason": exc.reason, "state": exc.state}
        except Exception as exc:
            caught = exc
            observed = {"outcome": "unexpected_exception", "type": type(exc).__name__, "reason": str(exc)}
        finally:
            final_bytes = image.read_bytes()
            evidence = {"case": case["id"], "oracle_sha256": ORACLE_SHA256,
                        "initial_sha256": hashlib.sha256(raw).hexdigest(), "initial_bytes": len(raw),
                        "expected": case["expected"], "observed": observed, "reads": reads,
                        "fault": fault, "fault_offsets_triggered": triggered,
                        "callback_exception_identity_preserved": caught is timeout,
                        "final_sha256": hashlib.sha256(final_bytes).hexdigest(), "final_bytes": len(final_bytes)}
            (directory / "OBSERVATION.json").write_text(json.dumps(evidence, indent=2) + "\n")
        if caught is not None and not isinstance(caught, inspection.HostInspectionError):
            raise caught
        self.assertEqual(observed, case["expected"])
        if fault and fault["kind"] != "deadline_initial":
            self.assertEqual(triggered, [target])
        if fault and fault["kind"].startswith("deadline_"):
            self.assertIs(caught, timeout)
        if not fault or fault["kind"] != "mutate_after_piece":
            self.assertEqual(final_bytes, raw)


def frozen_method(case):
    def test(self):
        self.run_frozen_case(case)
    test.__name__ = "test_" + case["id"]
    test.__doc__ = case["purpose"]
    return test


for _case in ORACLE["cases"]:
    setattr(ELFMappingControls, "test_" + _case["id"], frozen_method(_case))


if __name__ == "__main__":
    unittest.main()
