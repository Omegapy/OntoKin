"""Check frozen data integrity and declared construction; never invoke product."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import stat
import struct
import sys


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root, repo = Path(args.candidate), Path(args.repo)
    checks = []

    def require(value, name):
        checks.append({"name": name, "passed": bool(value)})
        if not value:
            raise AssertionError(name)

    controls = json.loads((root / "CONTROLS.json").read_text())
    expectations = json.loads((root / "EXPECTATIONS.json").read_text())
    manifest = json.loads((root / "FIXTURE-MANIFEST.json").read_text())
    construction = json.loads((root / "CONSTRUCTION.json").read_text())
    ids = [row["id"] for row in controls["cases"]]
    require(len(ids) == len(set(ids)) == 73, "73 unique controls")
    require(set(ids) == set(expectations["cases"]), "exact expectation coverage")
    paths = [row["path"] for row in manifest["files"]]
    actual_paths = sorted(str(p.relative_to(root)) for directory in ("elf", "fixture_inputs")
                          for p in (root / directory).rglob("*") if p.is_file())
    require(len(paths) == len(set(paths)) == 120 and sorted(paths) == actual_paths, "exact 120-fixture inventory")
    require(len(construction["images"]) == 47, "47 declared ELF constructions")
    for row in manifest["files"]:
        path = root / row["path"]
        info = path.lstat()
        data = path.read_bytes()
        require(stat.S_ISREG(info.st_mode) and stat.S_IMODE(info.st_mode) == 0o600, "inert regular mode: " + row["path"])
        require(len(data) == row["size_bytes"] and sha(data) == row["sha256"], "exact fixture bytes: " + row["path"])
    for row in controls["cases"]:
        raw = (root / row["input"]).read_bytes()
        context = json.loads(raw)
        want = (json.dumps(context, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False) + "\n").encode()
        require(raw == want, "canonical control context: " + row["id"])
        require(context["case_id"] == row["id"] and context["route"] == row["route"] and context["operational"] is False,
                "nonoperational context identity: " + row["id"])
        expected = expectations["cases"][row["id"]]
        require(expected["current_execution"] == "not_run" and expected["operational_plan_accepted"] is False
                and expected["host_qualified"] is False, "unexecuted scope: " + row["id"])
        require(all(expected[key] == 0 for key in ("expected_node_starts", "expected_ldd_starts", "expected_direct_loader_starts")),
                "no target-start expectation: " + row["id"])
        if expected["outcome"] == "metadata_returned":
            require(set(expected["metadata"]) == {"class", "endian", "machine", "type", "interpreter", "needed", "soname", "rpath", "runpath"},
                    "unchanged expected metadata shape: " + row["id"])
    for relative, layout in construction["images"].items():
        data = (root / relative).read_bytes()
        header = struct.unpack_from("<16sHHIQQQIHHHHHH", data, 0)
        require(len(data) == layout["file_bytes"] == 2048 and data[:7] == b"\x7fELF\x02\x01\x01", "ELF envelope: " + relative)
        require((header[1], header[2], header[5], header[9], header[10]) ==
                (layout["header"]["elf_type"], layout["header"]["machine"], 64, 56, layout["header"]["program_count"]),
                "declared header fields: " + relative)
        actual_programs = [list(struct.unpack_from("<IIQQQQQQ", data, offset)) for offset in (64, 120)]
        require(actual_programs == layout["program_headers"], "declared segment bytes: " + relative)
        actual_entries = [list(struct.unpack_from("<qQ", data, offset))
                          for offset in range(layout["dynamic_offset"], layout["dynamic_offset"] + layout["dynamic_size"], 16)]
        require(actual_entries == layout["dynamic_entries"], "declared dynamic bytes: " + relative)
        strings = bytes.fromhex(layout["stored_string_hex"])
        require(data[1536:1536 + len(strings)] == strings, "declared string bytes: " + relative)
    require(expectations["cases"]["P02_opaque_zero_values"]["metadata"] == expectations["cases"]["P03_opaque_u64_max_values"]["metadata"]
            == expectations["cases"]["P04_opaque_inconsistent_values"]["metadata"], "opaque edges share literal output; no behavioral execution")
    n16 = construction["images"]["elf/N16_flags_0x18_preserved.bin"]["dynamic_entries"]
    require([value for tag, value in n16 if tag == 30] == [0x18]
            and expectations["cases"]["N16_flags_0x18_preserved"]["reason"] == "Unsupported dynamic flags", "frozen synthetic 0x18 control")
    p01 = root / "elf/P01_opaque_p15_values.bin"
    require(sha(p01.read_bytes()) != "9792e3cbb541c8f44c7acf5f14f4022ea62998ecc787d326bed4d8b6547dfd92", "synthetic bytes are not the selected libc")
    for row in json.loads((root / "PROTECTED-SOURCES.json").read_text())["files"]:
        data = (repo / row["path"]).read_bytes()
        require(len(data) == row["size_bytes"] and sha(data) == row["sha256"], "protected input unchanged: " + row["path"])
    require(not any(name == "prototypes" or name.startswith("prototypes.") or name == "ontokin" or name.startswith("ontokin.")
                    for name in sys.modules), "no product module imported")
    result = {"schema": "ontokin.c271.p16-author-integrity-audit/1", "scope": "static fixture/source identity only; no product behavior",
              "command": [sys.executable, "-I", "-B", str(Path(__file__).resolve()), *sys.argv[1:]],
              "script_sha256": sha(Path(__file__).read_bytes()), "python_version": sys.version, "platform": sys.platform, "os_name": os.name,
              "controls": len(ids), "elf_images": len(construction["images"]), "fixture_files": len(paths),
              "input_hashes": {name: sha((root / name).read_bytes()) for name in ("CONTROLS.json", "EXPECTATIONS.json", "CONSTRUCTION.json", "FIXTURE-MANIFEST.json", "PROTECTED-SOURCES.json")},
              "checks": checks, "all_passed": all(row["passed"] for row in checks), "product_imported": False,
              "product_parser_called": False, "product_tests_run": False, "target_started": False, "current_host_inputs_read": False}
    with Path(args.output).open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    Path(args.output).chmod(0o600)
    print(json.dumps({"output": args.output, "checks_passed": len(checks), "controls": len(ids), "fixtures": len(paths), "all_passed": result["all_passed"]}))


if __name__ == "__main__":
    main()
