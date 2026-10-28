"""Independently audit checkpoint 028 from retained bytes and Git objects.

Standard library only. No product imports, tests, network, archive extraction,
archive creation, or Git mutations. The only write is a fresh external audit
JSON. Original recording failures remain failures even when this audit passes.
"""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import io
import json
import math
from pathlib import Path, PurePosixPath
import re
import stat
import statistics
import subprocess
import sys
import traceback
import zipfile
import zlib


BASE = "docs/engineering/reach-recording-validation-2026-10-23"
PRIOR = "103a9cc8f87ac68af597e39557857c100bdee7ec"
CONTROL = "f59da3cbca337cad2b436617b5a59f82348d223e"
MEASURED = "caf666e1222ba5912d88434ad71065333ca09775"
FINAL = "3a6b0751d23ab01a5cfb09405e7600f420d3070d"
TREES = {CONTROL: "5172525992364999d02391575cda02cfbe98c19a",
         MEASURED: "4bd11abfa1d74abb64ab123159872e21ac6430ec",
         FINAL: "ce1d7971b10be03ad5d9381695283fd2fe5cf79d"}
CUTS = {"83b9f2c3d65cdc7de41407da94cf4cb81de4cd0a": "6e2812b4cca4b4120f231675419d8768310a7126",
        "8cd6946e191591d529ed1f2931d4587c8c00d85b": "7c9b1c68265fed47dd5097c67790a34333d7be3a",
        MEASURED: TREES[MEASURED], FINAL: TREES[FINAL]}
CASES = [f"P{i:02d}" for i in range(1, 24)] + ["P25", "P26", "L01", "L02", "L03"]
FOCUSED = ["test_reach_certificate_term_reuse", "test_reach_certificate_zero_quarter"]
RELATED = ["test_reach_certificate_coefficients", "test_reach_certificate_thresholds",
           "test_reach_conformance", "test_reach_certificate_single_pass",
           "test_reach_reference_source_batch", "test_reach_recording_budget", *FOCUSED]
PREFIX = {"P09": (39606, 35473, 3), "P11": (66762, 60039, 10), "L03": (35660, 31427, 3)}
SOURCE_PATHS = {"ontokin/reach_conformance.py", "tests/test_reach_certificate_zero_quarter.py",
                "docs/engineering/reach-certificate-zero-quarter.md"}
RUNS = {"candidate-focused-001", "candidate-focused-002", "candidate-related-001",
        "candidate-controls-001", "candidate-original28-001"}
DRIVERS = {"reach_development_probe_v2.py": "052518bda650883f83f24dd34bc1bda9144c27ee3ad6900f72242ca74f10ddf6",
           "measure_zero_quarter.py": "673d562824000a8c5816742d908930e770aebbc4f14e02635c602c803f4cdc3d",
           "compare_original28.py": "4cf34756e490a68918331136d4576b22c92847b5ad39a0daa3ced00074faeb4d",
           "analyze_failure_stages.py": "9fa92da410a31499cfe00add630d8ceb8329e16cd5d05f3b8876f023d4da0d3b"}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def bare(value):
    return value.removeprefix("sha256:")


def object_digest(kind, raw):
    return hashlib.sha1(kind.encode() + b" " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def decode(raw):
    def unique(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate JSON key: " + key)
            result[key] = value
        return result
    def finite(value):
        raise ValueError("Nonfinite JSON number: " + value)
    def decimal(value):
        parsed = float(value)
        if not math.isfinite(parsed):
            finite(value)
        return parsed
    return json.loads(raw, object_pairs_hook=unique, parse_constant=finite, parse_float=decimal)


def function(tree, name):
    return next(node for node in tree.body
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name == name)


def ast_value(node):
    return ast.dump(node, include_attributes=False)


def changed_counts(control, candidate):
    left, right = control["counts"], candidate["counts"]
    return {key: left.get(key, 0) - right.get(key, 0)
            for key in sorted(left.keys() | right.keys()) if left.get(key, 0) != right.get(key, 0)}


class Audit:
    def __init__(self, root):
        self.root, self.count = root, 0
        self.snapshots, self.trees, self.blobs = {}, {}, {}
        self.process = None

    def check(self, condition, message):
        self.count += 1
        if not condition:
            raise ValueError(message)

    def relative(self, name):
        self.check(type(name) is str and bool(name) and "\\" not in name and "\0" not in name,
                   "Invalid relative path")
        path = PurePosixPath(name)
        self.check(bool(path.parts) and not path.is_absolute() and path.as_posix() == name
                   and all(part not in (".", "..", "") and ":" not in part for part in path.parts),
                   "Unsafe relative path: " + name)
        return path

    def regular(self, base, name):
        path = base
        for part in self.relative(name).parts:
            path = path / part
            self.check(not path.is_symlink(), "Symlink evidence: " + str(path))
        self.check(path.is_file() and path.resolve().is_relative_to(base.resolve()),
                   "Missing or escaping file: " + str(path))
        return path

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.root), *args])

    def tree(self, commit):
        self.check(re.fullmatch(r"[0-9a-f]{40}", commit) is not None, "Invalid Git commit identity")
        if commit not in self.trees:
            entries = {}
            for row in self.git("ls-tree", "-rz", commit).split(b"\0"):
                if not row:
                    continue
                metadata, name = row.split(b"\t", 1)
                mode, kind, oid = metadata.decode().split()
                name = name.decode()
                self.relative(name)
                self.check(kind == "blob" and mode in ("100644", "100755") and name not in entries,
                           "Nonregular or duplicate tracked input: " + name)
                entries[name] = {"oid": oid, "mode": mode}
            self.trees[commit] = entries
        return self.trees[commit]

    def blob_identity(self, oid):
        if oid not in self.blobs:
            if self.process is None:
                self.process = subprocess.Popen(["git", "-C", str(self.root), "cat-file", "--batch"],
                                                stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            self.process.stdin.write((oid + "\n").encode())
            self.process.stdin.flush()
            header = self.process.stdout.readline().split()
            self.check(len(header) == 3 and header[:2] == [oid.encode(), b"blob"], "Missing Git blob: " + oid)
            size = int(header[2])
            sha256 = hashlib.sha256()
            sha1 = hashlib.sha1(b"blob " + str(size).encode() + b"\0")
            remaining = size
            while remaining:
                body = self.process.stdout.read(min(remaining, 1024 * 1024))
                self.check(bool(body), "Truncated Git blob: " + oid)
                sha256.update(body)
                sha1.update(body)
                remaining -= len(body)
            self.check(self.process.stdout.read(1) == b"\n" and sha1.hexdigest() == oid,
                       "Git blob content identity mismatch: " + oid)
            self.blobs[oid] = {"bytes": size, "sha256": sha256.hexdigest()}
        return self.blobs[oid]

    def file(self, commit, name):
        oid = self.tree(commit)[name]["oid"]
        raw = self.git("cat-file", "blob", oid)
        self.check(object_digest("blob", raw) == oid, "Git file identity mismatch: " + name)
        return raw

    def close(self):
        if self.process is not None:
            self.process.stdin.close()
            self.process.stdout.close()
            self.check(self.process.wait() == 0, "Git object reader failed")
            self.process = None

    def archive(self, checkpoint):
        stem = f"checkpoint-{checkpoint:03d}"
        base = self.root / BASE
        summary_raw = self.regular(base, stem + ".json").read_bytes()
        manifest_raw = self.regular(base, stem + "-manifest.json").read_bytes()
        summary, manifest = decode(summary_raw), decode(manifest_raw)
        self.check(summary["checkpoint"] == manifest["checkpoint"] == checkpoint, "Archive checkpoint mismatch")
        archive = summary["archive"]
        parts, joined = archive["parts"], []
        self.check(bool(parts), "Missing archive parts")
        expected_parts = [f"{stem}.zip.part{i:03d}" for i in range(1, len(parts) + 1)]
        self.check([p["path"] for p in parts] == expected_parts
                   and {p.name for p in base.glob(stem + ".zip.part*")} == set(expected_parts),
                   "Archive parts are not exact, ordered and contiguous")
        for part in parts:
            raw = self.regular(base, part["path"]).read_bytes()
            self.check(len(raw) == part["bytes"] and digest(raw) == bare(part["sha256"]),
                       "Archive part identity mismatch: " + part["path"])
            joined.append(raw)
        joined = b"".join(joined)
        self.check(len(joined) == archive["bytes"] and digest(joined) == bare(archive["sha256"]),
                   "Joined archive identity mismatch")
        declared = {}
        for item in manifest["members"]:
            self.relative(item["path"])
            self.check(item["path"] not in declared, "Duplicate manifest member")
            declared[item["path"]] = item
        self.check(len(declared) == archive["member_count"], "Declared archive member count mismatch")
        payloads = {}
        with zipfile.ZipFile(io.BytesIO(joined)) as zipped:
            infos = zipped.infolist()
            self.check(len(infos) == len(declared), "ZIP member count differs from manifest")
            for info in infos:
                name = info.filename
                self.relative(name)
                self.check(name in declared and name not in payloads, "Unknown or duplicate ZIP member: " + name)
                mode = info.external_attr >> 16
                self.check(not info.is_dir() and stat.S_IFMT(mode) in (0, stat.S_IFREG)
                           and not info.flag_bits & 1, "Nonregular or encrypted ZIP member: " + name)
                raw = zipped.read(info)
                item = declared[name]
                self.check(len(raw) == info.file_size == item["bytes"]
                           and digest(raw) == bare(item["sha256"])
                           and zlib.crc32(raw) & 0xffffffff == info.CRC, "Member identity/CRC mismatch: " + name)
                payloads[name] = raw
        self.check(set(payloads) == set(declared), "Archive member closure mismatch")
        if checkpoint == 27:
            for name, raw in ((stem + ".json", summary_raw), (stem + "-manifest.json", manifest_raw)):
                self.check(raw == self.file(PRIOR, BASE + "/" + name), "Prior declaration differs from prior Git cut")
            for part in parts:
                identity = self.blob_identity(self.tree(PRIOR)[BASE + "/" + part["path"]]["oid"])
                self.check(identity == {"bytes": part["bytes"], "sha256": bare(part["sha256"])},
                           "Prior archive part differs from prior Git cut")
        info = {"checkpoint": checkpoint, "parts": len(parts), "members": len(payloads),
                "bytes": len(joined), "sha256": digest(joined),
                "uncompressed_bytes": sum(len(body) for body in payloads.values()),
                "ordered_part_hashes_member_hashes_crcs_and_safe_paths_verified": True}
        return summary, payloads, info

    def descriptor(self, payloads, prefix, row):
        self.relative(row["path"])
        raw = payloads[prefix + row["path"]]
        self.check(len(raw) == row["bytes"] and digest(raw) == bare(row["sha256"]),
                   "Output descriptor mismatch: " + prefix + row["path"])
        return raw

    def inputs(self, payloads, run, report, commit):
        prefix = "execution/" + run + "/"
        before, after = [decode(payloads[prefix + "inputs-" + phase + ".json"]) for phase in ("before", "after")]
        self.check(before == after and report["inputs_stable"] is True, "Inputs changed during " + run)
        identity = before.get("git", {"commit": before.get("git_commit"), "tree": before.get("git_tree"),
                                      "status": before.get("git_status")})
        self.check(identity == {"commit": commit, "tree": TREES[commit], "status": ""}
                   and report["source_commit"] == commit and report["source_tree"] == TREES[commit],
                   "Clean source identity mismatch: " + run)
        self.check(self.git("rev-parse", commit + "^{tree}").decode().strip() == TREES[commit]
                   and before.get("omitted_historical_archives", []) == [], "Missing or invalid source tree: " + run)
        rows, tree = before["files"], self.tree(commit)
        self.check(len(rows) == len(tree) == len({row["path"] for row in rows})
                   and {row["path"] for row in rows} == set(tree), "Incomplete tracked input inventory: " + run)
        for row in rows:
            actual = self.blob_identity(tree[row["path"]]["oid"])
            self.check(actual == {"bytes": row["bytes"], "sha256": bare(row["sha256"])},
                       "Tracked input differs from actual Git blob: " + run + "/" + row["path"])
            if "git_blob_sha1" in row:
                self.check(row["git_blob_sha1"] == tree[row["path"]]["oid"]
                           and row["mode"] == tree[row["path"]]["mode"], "Input Git fields mismatch")
        self.snapshots[run] = {"commit": commit, "tree": TREES[commit], "files": len(rows),
                               "bytes": sum(row["bytes"] for row in rows), "clean_stable_complete": True}
        return before

    def command(self, payloads, name, report, expected_exit, *, historical=False, analysis=False):
        key = "execution/" + name + ".command.json" if historical else "commands/" + name + ".json"
        receipt = decode(payloads[key])
        command, reported = receipt["command"], report["command"]
        self.check(receipt["exit_code"] == expected_exit and receipt["cwd"] == report["working_directory"],
                   "Command exit/cwd mismatch: " + name)
        def script(path):
            value = PurePosixPath(path)
            return value if value.is_absolute() else PurePosixPath(receipt["cwd"]) / value
        self.check(len(command) >= 2 and len(reported) >= 2 and script(command[1]) == script(reported[1])
                   and command[2:] == reported[2:], "Recorded command arguments differ: " + name)
        environment = report.get("analysis_environment", report.get("environment", report.get("execution")))
        self.check(environment["executable"] == reported[0]
                   and (command[0] == reported[0] or command[0] == PurePosixPath(reported[0]).name)
                   and environment["python"] and environment["platform"], "Python launcher identity mismatch: " + name)
        first = report["created_at"] if analysis else report["started_at"]
        times = [datetime.fromisoformat(value) for value in
                 (receipt["started_at"], first, report["finished_at"], receipt["finished_at"])]
        self.check(all(value.tzinfo is not None for value in times) and times == sorted(times)
                   and math.isfinite(receipt["elapsed_seconds"]) and receipt["elapsed_seconds"] > 0,
                   "Command timestamps/elapsed mismatch: " + name)
        if historical:
            stdout_key = "execution/" + name + ".command.stdout.txt"
            stderr_key = "execution/" + name + ".command.stderr.txt"
        else:
            stdout_key, stderr_key = "commands/" + name + ".stdout.txt", "commands/" + name + ".stderr.txt"
        self.check(payloads[stderr_key] == b"" and bool(payloads[stdout_key]), "Missing output or nonempty stderr: " + name)
        return receipt

    def implementation(self, commit):
        names = sorted(name for name in self.tree(commit)
                       if name.startswith("ontokin/") and name.endswith(".py") and len(PurePosixPath(name).parts) == 2)
        sha, files = hashlib.sha256(), []
        self.check(bool(names), "No implementation sources")
        for name in names:
            body = self.file(commit, name)
            sha.update(PurePosixPath(name).name.encode() + b"\0" + body + b"\0")
            files.append({"path": name, "bytes": len(body), "sha256": digest(body)})
        return {"sha256": sha.hexdigest(), "files": files,
                "algorithm": "SHA256 of sorted top-level ontokin/*.py basename, NUL, Git file bytes, NUL"}

    def tests(self, payloads, run, commit, count, modules):
        prefix = "execution/" + run + "/"
        report, tests = decode(payloads[prefix + "report.json"]), decode(payloads[prefix + "tests.json"])
        self.inputs(payloads, run, report, commit)
        self.command(payloads, run, report, 0)
        self.check(report["status"] == "passed" and report["test_count"] == report["passed_count"] == count
                   and report["test_log_complete"] is True and report["release_acceptance"] is False
                   and report["release_input_closure"] is False and report["full_product_goal_completed"] is False,
                   "Test summary or scope mismatch: " + run)
        expected_args = ["--root", report["working_directory"], "--output",
                         str(PurePosixPath(report["command"][1]).parent.parent / "execution" / run)]
        for module in modules:
            expected_args += ["--test", module]
        self.check(PurePosixPath(report["command"][1]).name == "reach_development_probe_v2.py"
                   and report["command"][2:] == expected_args, "Test cohort command mismatch: " + run)
        driver = payloads[prefix + "executed-driver.py"]
        self.check(driver == payloads["drivers/reach_development_probe_v2.py"]
                   and digest(driver) == report["driver_sha256"], "Executed test driver mismatch")
        expected = set()
        for module in modules:
            parsed = ast.parse(self.file(commit, "tests/" + module + ".py"))
            for cls in parsed.body:
                if isinstance(cls, ast.ClassDef):
                    for method in cls.body:
                        if isinstance(method, ast.FunctionDef) and method.name.startswith("test_"):
                            expected.add(module + "." + cls.name + "." + method.name)
        self.check(len(expected) == count == tests["test_count"]
                   and len(tests["started"]) == len(set(tests["started"])) == count
                   and set(tests["started"]) == expected, "Missing or duplicate started test methods: " + run)
        self.check(len(tests["results"]) == count
                   and {row["test_id"] for row in tests["results"]} == expected
                   and all(row["status"] == "passed" for row in tests["results"]), "Test result inventory mismatch")
        for key in ("failures", "errors", "skips", "expected_failures", "unexpected_successes"):
            self.check(tests[key] == 0 and report.get(key, 0) == 0, "Unexpected test outcome: " + key)
        log = payloads[prefix + "tests.log"]
        self.check(len(log) == report["test_log_bytes"] and digest(log) == report["test_log_sha256"]
                   and re.search(rb"Ran " + str(count).encode() + rb" tests in [0-9.]+s\n\nOK\n", log),
                   "Incomplete or mismatched full test log")
        for test in expected:
            self.check(log.count(("(" + test + ")").encode()) == 1, "Missing/duplicate test log identity: " + test)
        self.check(decode(payloads["commands/" + run + ".stdout.txt"]) ==
                   {key: report[key] for key in ("status", "test_count", "passed_count", "failures", "errors", "skips", "inputs_stable")},
                   "Test command stdout disagrees with complete results")
        return {"run": run, "commit": commit, "unique_methods_passed": count, "complete_log_verified": True}

    def work(self, row, shared):
        work = row["work"]
        self.check(type(work["operations"]) is int and type(shared) is int
                   and all(type(value) is int and value >= 0 for value in work["counts"].values())
                   and work["operations"] == sum(work["counts"].values())
                   and 0 <= work["operations"] <= shared and 0 <= work["cache_entries"] <= 256,
                   "Work accounting or numerical-cache mismatch")

    def controls(self, payloads, implementation):
        run = "candidate-controls-001"
        prefix = "execution/" + run + "/"
        report = decode(payloads[prefix + "report.json"])
        self.inputs(payloads, run, report, MEASURED)
        self.command(payloads, run, report, 0)
        self.check(report["status"] == "passed" and report["measurement_drivers_stable"] is True
                   and report["repetitions_per_case"] == 5 and report["selected_cases"] == list(PREFIX)
                   and report["prefix_settings"] == {"end_seconds": "1/4", "fps": 4, "helpers": False}
                   and report["control_checkpoint_commit"] == CONTROL
                   and report["expected_control_shared"] == {case: values[0] for case, values in PREFIX.items()}
                   and report["expected_zero_groups"] == {case: values[2] for case, values in PREFIX.items()}
                   and report["release_acceptance"] is False and report["original_complete_recording"] is False
                   and report["elapsed_speedup_claimed"] is False and report["timing_screen_max_median_ratio"] == 1.10,
                   "Prefix experiment declaration mismatch")
        for filename, source, hashkey in (("executed-driver.py", "measure_zero_quarter.py", "driver_sha256"),
                                         ("executed-identity-helper.py", "reach_development_probe_v2.py", "identity_helper_sha256")):
            raw = payloads[prefix + filename]
            self.check(raw == payloads["drivers/" + source] and digest(raw) == report[hashkey], "Measurement driver mismatch")
        self.check(report["control_definition"]["path"] == "tests/test_reach_certificate_zero_quarter.py"
                   and report["control_definition"]["sha256"] == digest(self.file(MEASURED, report["control_definition"]["path"])),
                   "Frozen control source hash mismatch")
        self.check(PurePosixPath(report["command"][1]).name == "measure_zero_quarter.py"
                   and report["command"][2:] == ["--root", report["working_directory"], "--output",
                   str(PurePosixPath(report["command"][1]).parent.parent / "execution" / run), "--repetitions", "5"],
                   "Prefix experiment command changed")
        rows, retained = {}, {}
        expected_order = [(case, repeat, mode) for case in PREFIX for repeat in range(1, 6)
                          for mode in (("control", "candidate") if repeat % 2 else ("candidate", "control"))]
        actual_order = [(row["case_id"], row["repetition"], row["mode"]) for row in report["rows"]]
        self.check(actual_order == expected_order and len(report["pairs"]) == 15 and len(report["comparisons"]) == 3,
                   "Prefix requests/pairs/order mismatch")
        for row in report["rows"]:
            case, repeat, mode = row["case_id"], row["repetition"], row["mode"]
            key = (case, repeat, mode)
            order = ["control", "candidate"] if repeat % 2 else ["candidate", "control"]
            self.check(row["directory"] == f"{case}-{repeat:02d}-{mode}"
                       and row == decode(payloads[prefix + row["directory"] + "/request-result.json"])
                       and row["status"] == "passed" and row["order"] == order
                       and row["order_position"] == order.index(mode) + 1, "Raw prefix row mismatch")
            self.work(row, row["shared_operations"])
            self.check(row["operations"] == row["work"]["operations"] and row["shared_operations"] <= 100000
                       and row["budget_limits"]["max_operations"] == 100000
                       and row["budget_limits"]["max_elapsed_ms"] == 30000
                       and math.isfinite(row["elapsed_ms"]) and 0 < row["elapsed_ms"] < 30000, "Prefix caps/timing mismatch")
            glb, export = [self.descriptor(payloads, prefix, row[k]) for k in ("artifact", "export_report")]
            decoded = decode(export)
            self.check(decoded["validation"]["status"] == "passed"
                       and decoded["source_code_sha256"] == implementation["sha256"], "Prefix output validation/fingerprint mismatch")
            rows[key], retained[key] = row, (glb, export)
        comparisons, flat_pairs = [], []
        for case, (shared, reach, groups) in PREFIX.items():
            matching = [row for row in report["comparisons"] if row["case_id"] == case]
            self.check(len(matching) == 1, "Missing/duplicate case comparison")
            comparison, pairs = matching[0], []
            for repeat in range(1, 6):
                control, candidate = [rows[(case, repeat, mode)] for mode in ("control", "candidate")]
                self.check(retained[(case, repeat, "control")] == retained[(case, repeat, "candidate")],
                           "Paired complete GLB/export bytes differ")
                delta = changed_counts(control["work"], candidate["work"])
                self.check(control["shared_operations"] == shared and control["operations"] == reach
                           and candidate["shared_operations"] == shared - 5 * groups
                           and candidate["operations"] == reach - 5 * groups
                           and delta == {"independent_exact_mul": 3 * groups, "independent_exact_div": 2 * groups}
                           and control["work"]["cache_entries"] == candidate["work"]["cache_entries"],
                           "Prefix exact-zero saving/category mismatch")
                pair = {"repetition": repeat, "glb_bytes_identical": True, "complete_reports_identical": True,
                        "control_shared_operations": shared, "candidate_shared_operations": shared - 5 * groups,
                        "saved_shared_operations": 5 * groups, "control_reach_operations": reach,
                        "candidate_reach_operations": reach - 5 * groups, "saved_reach_operations": 5 * groups,
                        "control_elapsed_ms": control["elapsed_ms"], "candidate_elapsed_ms": candidate["elapsed_ms"],
                        "work_category_delta": delta, "cache_entries_identical": True}
                pairs.append(pair)
                flat_pairs.append({"case_id": case, **pair})
            self.check(comparison["pairs"] == pairs and comparison["pair_count"] == 5
                       and comparison["includes_construction"] is True
                       and comparison["glb_bytes_identical"] is True and comparison["complete_reports_identical"] is True,
                       "Prefix paired summary mismatch")
            for key in ("control_shared_operations", "candidate_shared_operations", "saved_shared_operations",
                        "control_reach_operations", "candidate_reach_operations", "saved_reach_operations"):
                self.check(comparison[key] == pairs[0][key], "Prefix aggregate counter mismatch")
            medians = {}
            for mode in ("control", "candidate"):
                times = [pair[mode + "_elapsed_ms"] for pair in pairs]
                medians[mode] = statistics.median(times)
                self.check(comparison[mode + "_elapsed_ms"] == times
                           and comparison[mode + "_median_elapsed_ms"] == medians[mode]
                           and comparison[mode + "_elapsed_range_ms"] == [min(times), max(times)], "Elapsed aggregate mismatch")
            increase = 100 * (medians["candidate"] / medians["control"] - 1)
            self.check(comparison["median_elapsed_increase_ms"] == medians["candidate"] - medians["control"]
                       and comparison["median_elapsed_increase_percent"] == increase
                       and comparison["candidate_slower_pairs"] == sum(p["candidate_elapsed_ms"] > p["control_elapsed_ms"] for p in pairs)
                       and comparison["candidate_faster_pairs"] == sum(p["candidate_elapsed_ms"] < p["control_elapsed_ms"] for p in pairs)
                       and medians["candidate"] <= 1.10 * medians["control"], "Predeclared elapsed screen or summary mismatch")
            comparisons.append({"case_id": case, "pairs": 5, "saved_shared_and_reach_operations": 5 * groups,
                                "control_median_ms": medians["control"], "candidate_median_ms": medians["candidate"],
                                "median_increase_percent": increase})
        self.check(report["pairs"] == flat_pairs, "Top-level pairs differ from all raw requests")
        stdout = payloads["commands/" + run + ".stdout.txt"].decode().splitlines()
        expected_lines = [f"{case} pair {repeat}: shared {shared} -> {shared - 5 * groups}; bytes and reports identical"
                          for case, (shared, _, groups) in PREFIX.items() for repeat in range(1, 6)]
        self.check(len(stdout) == 16 and stdout[:-1] == expected_lines
                   and decode(stdout[-1]) == {"status": "passed", "inputs_stable": True,
                       "comparisons": [{key: value for key, value in row.items() if key != "pairs"}
                                       for row in report["comparisons"]]}, "Prefix stdout differs from actual retained comparisons")
        return comparisons

    def source_cuts(self, payloads):
        cut_ids = {name.split("/")[1] for name in payloads if name.startswith("source-cuts/")}
        self.check(cut_ids == set(CUTS), "Source-cut inventory mismatch")
        for commit, tree in CUTS.items():
            prefix = "source-cuts/" + commit + "/"
            identity = decode(payloads[prefix + "identity.json"])
            raw = payloads[prefix + "commit.raw"]
            self.check(identity["commit"] == commit and identity["tree"] == tree
                       and identity["base_commit"] == PRIOR and object_digest("commit", raw) == commit
                       and raw == self.git("cat-file", "commit", commit)
                       and raw.startswith(("tree " + tree + "\n").encode())
                       and self.git("rev-parse", commit + "^{tree}").decode().strip() == tree, "Preserved commit/tree mismatch")
            changed = set(self.git("diff", "--name-only", PRIOR, commit, "--").decode().splitlines())
            wanted = SOURCE_PATHS if commit != "83b9f2c3d65cdc7de41407da94cf4cb81de4cd0a" else (
                SOURCE_PATHS - {"tests/test_reach_certificate_zero_quarter.py"})
            self.check(changed == wanted == {row["path"] for row in identity["files"]}
                       and len(identity["files"]) == len(wanted), "Changed source-file closure mismatch")
            self.check(payloads[prefix + "changes.patch"] == self.git("diff", "--no-ext-diff", "--no-textconv", PRIOR, commit, "--"),
                       "Preserved source patch mismatch")
            for row in identity["files"]:
                body = payloads[prefix + row["path"]]
                self.check(len(body) == row["bytes"] and digest(body) == row["sha256"]
                           and object_digest("blob", body) == row["git_blob"] == self.tree(commit)[row["path"]]["oid"]
                           and body == self.file(commit, row["path"]), "Preserved source bytes mismatch")
        old = ast.parse(self.file(CONTROL, "ontokin/reach_conformance.py"))
        accepted = function(old, "_complete_inequality_values")
        frozen = []
        for commit in (MEASURED, FINAL):
            node = function(ast.parse(self.file(commit, "tests/test_reach_certificate_zero_quarter.py")), "_checkpoint026_complete")
            node.name = accepted.name
            self.check(ast_value(node) == ast_value(accepted), "Frozen accepted algebra differs beyond function name")
            frozen.append(ast_value(node))
        new = ast.parse(self.file(FINAL, "ontokin/reach_conformance.py"))
        before, after = function(old, "_CertificateTermReuse"), function(new, "_CertificateTermReuse")
        for name in ("create", "current", "calculate", "borrow"):
            self.check(ast_value(function(before, name)) == ast_value(function(after, name)), "Shared old helper changed: " + name)
        left, right = function(before, "__init__"), function(after, "__init__")
        self.check(len(right.body) == len(left.body) + 1
                   and [ast_value(n) for n in left.body] == [ast_value(n) for n in right.body[:-1]]
                   and ast.unparse(right.body[-1]) == "self.zero_coefficients = None", "Control initializer is not inert additive state")
        changed = self.git("diff", "--name-only", MEASURED, FINAL, "--").decode().splitlines()
        self.check(set(changed) == SOURCE_PATHS - {"ontokin/reach_conformance.py"}
                   and self.file(MEASURED, "ontokin/reach_conformance.py") == self.file(FINAL, "ontokin/reach_conformance.py"),
                   "Measured-to-final runtime changed")
        applicability = decode(payloads["reviews/measurement-applicability.json"])
        self.check(applicability["status"] == "passed" and applicability["measured_source_commit"] == MEASURED
                   and applicability["final_tested_source_commit"] == FINAL and applicability["runtime_bytes_unchanged"] is True
                   and applicability["frozen_control_ast_unchanged"] is True and applicability["measurement_reexecuted"] is False
                   and applicability["changed_paths"] == changed
                   and applicability["reader_sha256"] == digest(self.file(FINAL, "ontokin/reach_conformance.py")),
                   "Measurement applicability receipt mismatch")
        return {"measured_commit": MEASURED, "final_tested_commit": FINAL, "same_runtime_and_frozen_control": True,
                "raw_commits_trees_blobs_patches_verified": True, "preserved_source_cuts": len(CUTS)}

    def originals(self, payloads, run, commit, implementation, *, historical=False):
        prefix = "execution/" + run + "/"
        report = decode(payloads[prefix + "report.json"])
        self.inputs(payloads, run, report, commit)
        rows = report["deliveries"]
        self.check(report["required_cases"] == report["selected_cases"] == CASES
                   and [row["case_id"] for row in rows] == CASES
                   and report["source_kind"] == "source_component" and report["provider"] == "local"
                   and report["release_acceptance"] is False and report["full_product_goal_completed"] is False
                   and report["native_validation"] == report["browser_validation"] == "pending", "Original28 corpus/scope mismatch")
        self.check(PurePosixPath(report["command"][1]) == PurePosixPath(report["working_directory"]) / "tools/build_reach_source_artifacts.py"
                   and len(report["command"]) == 4 and report["command"][2] == "--output-dir"
                   and PurePosixPath(report["command"][3]).name == run, "Original28 uses altered command options")
        passed = [row["case_id"] for row in rows if row["status"] == "passed"]
        failed = [row["case_id"] for row in rows if row["status"] == "failed"]
        self.check(len(passed) + len(failed) == 28
                   and report["status"] == ("failed" if failed else "passed")
                   and report["complete_source_delivery_corpus"] is (not failed), "Original28 result was misclassified")
        self.command(payloads, run, report, int(bool(failed)), historical=historical)
        stdout_key = ("execution/" + run + ".command.stdout.txt" if historical else "commands/" + run + ".stdout.txt")
        self.check(payloads[stdout_key].decode().splitlines() ==
                   [f"{row['case_id']}: {row['status']} ({row['operations']} operations)" for row in rows],
                   "Original28 command stdout differs from all retained request outcomes")
        retained = {}
        for row in rows:
            case = row["case_id"]
            self.check(row == decode(payloads[prefix + case + "/request-result.json"]), "Raw original28 request mismatch: " + case)
            end = {"P14": "4", "P16": "4", "P17": "2", "P26": "60", "L01": "4", "L02": "2", "L03": "4"}.get(case, "3")
            self.check(row["options"] == {"end": end, "fps": 1, "helpers": False, "position_tolerance_m": .001,
                       "rotation_tolerance_rad": .001, "time_tolerance_s": .000001}
                       and row["max_operations"] == 100000 and math.isfinite(row["elapsed_seconds"])
                       and 0 < row["elapsed_seconds"] < 30, "Original settings/cap/elapsed changed: " + case)
            self.work(row, row["operations"])
            manifest_name = row["source_files"]
            manifest_raw = self.file(commit, manifest_name)
            self.check(row["source_manifest"] == {"path": manifest_name, "bytes": len(manifest_raw),
                       "sha256": "sha256:" + digest(manifest_raw)}, "Original source manifest mismatch")
            if row["status"] == "passed":
                glb, export_raw = [self.descriptor(payloads, prefix, row[key]) for key in ("artifact", "export_report")]
                export = decode(export_raw)
                self.check(row["operations"] <= 100000 and export["validation"]["status"] == "passed"
                           and export["source_code_sha256"] == implementation["sha256"], "Original output validation/fingerprint mismatch")
                manifest, units = decode(manifest_raw), []
                for entry, source_id in [(manifest["entry"], "entry")] + [
                        (module, "package:" + module["package_id"] + "@" + module["version"])
                        for module in manifest["modules"]]:
                    name = (PurePosixPath(manifest_name).parent / entry["path"]).as_posix()
                    self.relative(name)
                    body = self.file(commit, name)
                    units.append({"source_id": source_id, "bytes": len(body), "sha256": "sha256:" + digest(body)})
                self.check(row["source_units"] == units, "Original source-unit inventory mismatch")
                retained[case] = (glb, export)
            else:
                details = row["diagnostic"]["details"]
                self.check(row["operations"] == 100001 and details["budget"] == "max_operations"
                           and details["limit"] == 100000 and details["consumed"] == 100001
                           and row["failure"] == {"type": "OntoKinError", "message": "Construction exceeded max_operations."}
                           and row["diagnostic"]["code"] == "OKL-E-RESOURCE"
                           and "artifact" not in row and "export_report" not in row,
                           "Original28 failure is not the retained operation-cap refusal")
        return report, {row["case_id"]: row for row in rows}, retained

    def comparison(self, payloads, prior, old_impl, new_impl):
        old_report, old_rows, old_outputs = self.originals(prior, "control-original28", CONTROL, old_impl, historical=True)
        new_report, new_rows, new_outputs = self.originals(payloads, "candidate-original28-001", FINAL, new_impl)
        report = decode(payloads["reviews/original28-comparison.json"])
        self.command(payloads, "original28-comparison-001", report, 0, analysis=True)
        arguments = report["command"]
        self.check(len(arguments) == 10 and PurePosixPath(arguments[1]).name == "compare_original28.py"
                   and arguments[2::2] == ["--root", "--control", "--candidate", "--output"]
                   and arguments[3] == report["working_directory"]
                   and PurePosixPath(arguments[5]).name == "control-original28"
                   and PurePosixPath(arguments[7]).name == "candidate-original28-001"
                   and PurePosixPath(arguments[9]).name == "original28-comparison.json", "Comparison command options mismatch")
        self.check(report["status"] == "passed" and report["required"] == 28
                   and report["control_commit"] == CONTROL and report["candidate_commit"] == FINAL
                   and report["control_tree"] == TREES[CONTROL] and report["candidate_tree"] == TREES[FINAL]
                   and report["release_acceptance"] is False and report["full_product_goal_completed"] is False
                   and report["capped_failures_do_not_establish_complete_costs"] is True
                   and report["driver_sha256"] == digest(payloads["drivers/compare_original28.py"])
                   and report["checks"] and all(item["passed"] is True for item in report["checks"]), "Comparison scope/source/check mismatch")
        for mode, source, run, original, impl in (("control", prior, "control-original28", old_report, old_impl),
                                                  ("candidate", payloads, "candidate-original28-001", new_report, new_impl)):
            prefix = "execution/" + run + "/"
            self.check(report["execution"][mode] == original["execution"]
                       and report["implementation_source_sha256"][mode] == impl["sha256"]
                       and report["implementation_receipts"][mode] == impl, "Comparison implementation receipt mismatch")
            descriptions = [(report["input_reports"][mode], "report.json")] + [
                (report["input_receipts"][mode][phase], "inputs-" + phase + ".json") for phase in ("before", "after")]
            for description, name in descriptions:
                raw = source[prefix + name]
                self.check(description["bytes"] == len(raw) and bare(description["sha256"]) == digest(raw),
                           "Comparison input hash mismatch")
        old_files = {row["path"]: (row["bytes"], bare(row["sha256"])) for row in
                     decode(prior["execution/control-original28/inputs-before.json"])["files"]}
        new_files = {row["path"]: (row["bytes"], bare(row["sha256"])) for row in
                     decode(payloads["execution/candidate-original28-001/inputs-before.json"])["files"]}
        self.check(report["changed_input_paths"] == sorted(name for name in old_files.keys() | new_files.keys()
                   if old_files.get(name) != new_files.get(name)), "Comparison changed-input inventory mismatch")
        expected_rows, saved, failed, new_passes = [], [], [], []
        for case in CASES:
            control, candidate = old_rows[case], new_rows[case]
            for key in ("source_files", "program_revision", "source_manifest", "options"):
                self.check(control[key] == candidate[key], "Original request identity changed: " + case)
            row = {"case_id": case, "control_status": control["status"], "candidate_status": candidate["status"],
                   "control_operations": control["operations"], "candidate_operations": candidate["operations"],
                   "control_elapsed_ms": control["elapsed_seconds"] * 1000,
                   "candidate_elapsed_ms": candidate["elapsed_seconds"] * 1000, "completed_request_saving": None}
            self.check(control["status"] != "passed" or candidate["status"] == "passed", "Previously passing original request regressed")
            if control["status"] == candidate["status"] == "passed":
                left_glb, left = old_outputs[case]
                right_glb, right = new_outputs[case]
                saving = control["operations"] - candidate["operations"]
                self.check(left_glb == right_glb and left["validation"] == right["validation"]
                           and {key: value for key, value in left.items() if key != "source_code_sha256"}
                           == {key: value for key, value in right.items() if key != "source_code_sha256"}
                           and control["source_units"] == candidate["source_units"] and saving >= 0,
                           "Completed original output or work regressed: " + case)
                delta = changed_counts(control["work"], candidate["work"])
                groups, remainder = divmod(saving, 5)
                wanted = {"independent_exact_mul": 3 * groups, "independent_exact_div": 2 * groups} if groups else {}
                self.check(remainder == 0 and delta == wanted
                           and control["work"]["operations"] - candidate["work"]["operations"] == saving
                           and control["work"]["cache_entries"] == candidate["work"]["cache_entries"],
                           "Original completed work differs beyond exact-zero omissions: " + case)
                row.update(classification="preserved_pass", glb_bytes_identical=True, validation_reports_identical=True,
                           source_units_identical=True, changed_report_keys=sorted(key for key in left.keys() | right.keys()
                           if left.get(key) != right.get(key)), saved_operations=saving, completed_request_saving=saving)
                saved.append(saving)
            elif candidate["status"] == "passed":
                row.update(classification="new_pass", baseline_artifact_available=False,
                           exact_baseline_glb_comparison_possible=False, fresh_original_validation_passed=True)
                new_passes.append(case)
            else:
                self.check(control["diagnostic"] == candidate["diagnostic"]
                           and control["failure"] == candidate["failure"], "Original cap diagnostic changed")
                row.update(classification="preserved_cap_failure", diagnostic_identical=True, failure_identical=True)
                failed.append(case)
            expected_rows.append(row)
        self.check(report["rows"] == expected_rows, "Comparison rows do not equal independently derived raw outcomes")
        derived = {"passed": 28 - len(failed), "failed": failed, "new_passes": new_passes,
                   "recording_gate_status": new_report["status"], "original_recording_gate_passed": not failed,
                   "common_pass_count": len(saved), "saved_total_over_common_completed_requests": sum(saved),
                   "saved_range_over_common_completed_requests": [min(saved), max(saved)] if saved else None,
                   "all_common_passing_glb_bytes_and_validation_reports_identical": True,
                   "complete_common_export_reports_differ_only_in_verified_implementation_source_hash": True,
                   "all_remaining_failures_are_unchanged_cap_refusals": True, "no_elapsed_cap_failures": True,
                   "control_inputs_stable": True, "candidate_inputs_stable": True,
                   "maximum_candidate_elapsed_ms": max(row["candidate_elapsed_ms"] for row in expected_rows)}
        for key, value in derived.items():
            self.check(report[key] == value, "Derived original28 aggregate mismatch: " + key)
        self.check(decode(payloads["commands/original28-comparison-001.stdout.txt"]) ==
                   {key: report[key] for key in ("status", "passed", "failed", "new_passes",
                    "saved_total_over_common_completed_requests", "recording_gate_status")}, "Comparison stdout differs from derived result")
        return {**derived, "completed_requests_with_savings": sum(value > 0 for value in saved),
                "completed_request_work_category_deltas_verified": True,
                "historical_baseline_reexecuted": False, "elapsed_speedup_claimed": False}

    def recovery(self, payloads, prior_info):
        record = decode(payloads["recovery/prior027-archive.json"])
        self.check(record["status"] == "passed" and record["source_commit"] == PRIOR
                   and record["archive_sha256"] == prior_info["sha256"] and record["bytes"] == prior_info["bytes"]
                   and record["parts"] == prior_info["parts"] and record["members"] == prior_info["members"]
                   and record["all_hashes_and_crc_verified_before_extraction"] is True, "Prior recovery receipt mismatch")
        raw = payloads["recovery/observed-head.commit"]
        self.check(object_digest("commit", raw) == PRIOR and raw == self.git("cat-file", "commit", PRIOR),
                   "Recovered prior raw commit identity mismatch")
        recovered = decode(payloads["recovery/commit-recovery.json"])
        self.check(recovered["verified_sha"] == PRIOR, "Recovered prior commit declaration mismatch")
        remote = decode(payloads["recovery/remote-initial.json"])
        head = decode(remote["remote_head"]["content"])
        self.check(head["sha"] == PRIOR and head["tree"]["sha"] == "89a397d77c6ea32b4f18d3a64c9f32fbdc288a4f",
                   "Captured initial remote head mismatch")
        branches = {row["name"]: row["commit"]["sha"] for row in remote["remote_branches"]}
        self.check(branches["main"] == "2bb4588e121fcfe99b4d42c734b15b38362f3642", "Captured initial main changed")
        for name in ("pr27", "pr28"):
            row = remote[name]
            if "content" in row:
                row = decode(row["content"])
            self.check(row["state"] == "open" and row["draft"] is True and row["merged"] is False,
                       "Captured initial draft PR status mismatch")

    def publication(self, payloads, summary):
        record = decode(payloads["publication/implementation-readback.json"])
        raw = payloads["publication/implementation.commit"]
        published = record["published_commit"]
        header = raw.split(b"\n\n", 1)[0].splitlines()
        self.check(record["status"] == "passed" and record["tested_local_commit"] == FINAL
                   and record["tree"] == TREES[FINAL] and record["parent"] == PRIOR
                   and record["all_changed_file_contents_equal"] is True
                   and record["independent_commit_object_sha1_verified"] == published
                   and object_digest("commit", raw) == published
                   and [line for line in header if line.startswith(b"tree ")] == [("tree " + TREES[FINAL]).encode()]
                   and [line for line in header if line.startswith(b"parent ")] == [("parent " + PRIOR).encode()],
                   "Captured publication raw commit/tree/parent mismatch")
        self.check(len(record["files"]) == len(SOURCE_PATHS)
                   and {row["path"] for row in record["files"]} == SOURCE_PATHS, "Published changed-file inventory mismatch")
        for row in record["files"]:
            expected = self.tree(FINAL)[row["path"]]
            self.check(row["mode"] == expected["mode"] and row["type"] == "blob"
                       and row["sha"] == expected["oid"]
                       and row["bytes"] == self.blob_identity(expected["oid"])["bytes"], "Published file receipt differs from tested tree")
        self.check(record["tree_response"]["isError"] is False
                   and record["tree_response"]["structuredContent"]["sha"] == TREES[FINAL]
                   and record["commit_response"]["isError"] is False
                   and record["commit_response"]["structuredContent"]["sha"] == published
                   and record["ref_update"]["isError"] is False
                   and record["ref_update"]["structuredContent"]["success"] is True, "Captured publication action receipt mismatch")
        self.check(len(record["readbacks"]) == 3, "Missing captured publication readback")
        commit, ref = [decode(row["content"]) for row in record["readbacks"][:2]]
        self.check(commit["sha"] == published and commit["tree"]["sha"] == TREES[FINAL]
                   and [row["sha"] for row in commit["parents"]] == [PRIOR]
                   and ref["ref"] == "refs/heads/" + record["branch"]
                   and ref["object"] == {"sha": published, "type": "commit",
                       "url": "https://api.github.com/repos/Omegapy/OntoKin/git/commits/" + published}
                   and record["readbacks"][2]["workflow_runs"] == [], "Captured implementation ref/tree/workflow mismatch")
        self.check(summary["implementation"]["published_commit"] == published
                   and summary["implementation"]["source_branch"] == record["branch"]
                   and summary["implementation"]["base_commit"] == PRIOR
                   and summary["implementation"]["measured_tree"] == TREES[MEASURED]
                   and summary["implementation"]["outcome"] == "accepted_for_development_continuation"
                   and summary["publication"]["implementation_readback"] == "publication/implementation-readback.json",
                   "Checkpoint publication identity differs from captured readback")
        return {"published_commit": published, "tree": TREES[FINAL], "branch": record["branch"],
                "captured_raw_commit_ref_and_changed_file_receipts_verified": True,
                "current_remote_state_queried": False}

    def summary_claims(self, payloads, summary, original, prior_info):
        controls = decode(payloads["execution/candidate-controls-001/report.json"])
        declared = summary["controls"]
        self.check(declared["settings"] == controls["prefix_settings"]
                   and declared["timing_max_median_ratio"] == controls["timing_screen_max_median_ratio"]
                   and declared["comparisons"] == controls["comparisons"]
                   and declared["timing_screen_is_development_only"] is True
                   and declared["elapsed_speedup_claimed"] is False
                   and declared["all_bytes_and_entire_reports_identical"] is True
                   and declared["only_delta_categories"] == ["independent_exact_mul", "independent_exact_div"]
                   and declared["applicability_binding"] == "reviews/measurement-applicability.json", "Checkpoint duplicated prefix claims mismatch")
        self.check(summary["limits"] == {"max_operations": 100000, "max_elapsed_ms": 30000,
                   "max_operand_bits": 32768, "max_numerical_cache_entries": 256, "separate_native_metadata_bound": 512},
                   "Checkpoint changes accepted limits")
        paths = {"focused_initial": "execution/candidate-focused-001/report.json",
                 "focused_final": "execution/candidate-focused-002/report.json",
                 "related": "execution/candidate-related-001/report.json",
                 "controls": "execution/candidate-controls-001/report.json",
                 "original28": "execution/candidate-original28-001/report.json",
                 "comparison": "reviews/original28-comparison.json"}
        for key, name in paths.items():
            self.check(summary["execution"][key] == name, "Checkpoint execution reference mismatch: " + key)
            report = decode(payloads[name])
            environment = report.get("analysis_environment", report.get("environment", report.get("execution")))
            self.check(summary["execution"]["environment"] == environment, "Checkpoint execution environment mismatch")
        self.check(summary["execution"]["all_tracked_inputs_present_and_stable"] is True
                   and summary["execution"]["failed_original28_exit_code"] == 1,
                   "Checkpoint stable-input or failed-command claim mismatch")
        comparison = decode(payloads[paths["comparison"]])
        self.check(summary["results"]["prior_passes_preserved"] == original["common_pass_count"]
                   and summary["results"]["cheaper_completed_requests"] == original["completed_requests_with_savings"]
                   and summary["results"]["unchanged_completed_requests"] == [row["case_id"] for row in comparison["rows"]
                       if row.get("classification") == "preserved_pass" and row["saved_operations"] == 0]
                   and summary["results"]["new_recording_passes"] == original["new_passes"]
                   and summary["results"]["full_regression_executed"] is False
                   and summary["results"]["compatibility_executed"] == ["CPython 3.12.14 focused development roles only"],
                   "Checkpoint duplicated corpus/coverage result mismatch")
        baseline = summary["baseline"]
        self.check(baseline["checkpoint"] == 27 and baseline["archive_sha256"] == prior_info["sha256"]
                   and baseline["original28_member"] == "execution/control-original28/report.json"
                   and baseline["source_commit"] == CONTROL and baseline["freshly_reexecuted_in_checkpoint028"] is False
                   and baseline["archive_verified_before_extraction"] == "recovery/prior027-archive.json", "Checkpoint baseline provenance mismatch")

    def failure_analysis(self, payloads, summary):
        analysis = decode(payloads["analysis/failure-stages.json"])
        report = decode(payloads["execution/candidate-original28-001/report.json"])
        receipt = decode(payloads["commands/failure-stage-analysis-001.json"])
        driver = "analyze_failure_stages.py"
        script = str(PurePosixPath(report["working_directory"]).parent / "evidence028" / "drivers" / driver)
        self.check(receipt["exit_code"] == 0 and receipt["cwd"] == report["working_directory"]
                   and receipt["command"][1:] == [script]
                   and receipt["command"][0] in (report["execution"]["executable"],
                       PurePosixPath(report["execution"]["executable"]).name)
                   and digest(payloads["drivers/" + driver]) == DRIVERS[driver], "Failure-analysis command/driver identity mismatch")
        timestamps = [datetime.fromisoformat(value) for value in
                      (receipt["started_at"], analysis["created_at"], receipt["finished_at"])]
        self.check(all(value.tzinfo is not None for value in timestamps) and timestamps == sorted(timestamps)
                   and math.isfinite(receipt["elapsed_seconds"]) and receipt["elapsed_seconds"] > 0
                   and payloads["commands/failure-stage-analysis-001.stderr.txt"] == b""
                   and decode(payloads["commands/failure-stage-analysis-001.stdout.txt"]) ==
                       {"status": "passed", "cases": len(analysis["cases"]), "product_execution_performed": False},
                   "Failure-analysis command timing/stdout/stderr mismatch")
        self.check(analysis["status"] == "passed" and analysis["source_commit"] == FINAL
                   and analysis["product_execution_performed"] is False and analysis["full_cost_beyond_cap_known"] is False,
                   "Failure-stage analysis overstates execution or complete cost")
        failed = {row["case_id"]: row for row in report["deliveries"] if row["status"] == "failed"}
        self.check([row["case_id"] for row in analysis["cases"]] == list(failed), "Failure analysis inventory mismatch")
        directory = PurePosixPath(report["working_directory"])
        for record in analysis["cases"]:
            case = record["case_id"]
            row = failed[case]
            raw = payloads["execution/candidate-original28-001/" + case + "/request-result.json"]
            counts = row["work"]["counts"]
            self.check(record["request_sha256"] == digest(raw)
                       and record["shared_operations"] == row["operations"]
                       and record["reach_operations"] == row["work"]["operations"]
                       and record["diagnostic"] == row["diagnostic"]
                       and all(value == counts.get(key, 0) for key, value in record["observed_counts"].items())
                       and record["largest_categories"] == [[key, value] for key, value in
                           sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:10]], "Failure-stage counters/hash mismatch: " + case)
            frames = []
            for name, line, func in re.findall(r'File "([^"]+)", line (\d+), in ([^\n]+)', row["traceback"]):
                path = PurePosixPath(name)
                relative = path.relative_to(directory).as_posix() if path.is_relative_to(directory) else name
                frames.append({"file": relative, "line": int(line), "function": func.strip()})
            self.check(record["frames"] == frames, "Failure-stage frames differ from retained exception")
        next_step = summary["next_task"]
        counts = failed["P09"]["work"]["counts"]
        observation = {"retained_clock_checks": counts["independent_retained_clock"],
                       "certificate_members": counts["independent_certificate_member"],
                       "created_groups": counts["independent_certificate_group"],
                       "begun_group_checks": counts["independent_certificate_group_check"],
                       "term_admissions": counts["independent_certificate_term_admission"]}
        self.check(next_step["status"] == "unimplemented" and next_step["P09_observed"] == observation
                   and next_step["no_remaining_full_cost_or_recording_pass_inferred"] is True
                   and next_step["source_review"] == "reviews/next-task-source-review.json"
                   and next_step["current_failure_analysis"] == "analysis/failure-stages.json", "Checkpoint next-task observations mismatch")
        review = decode(payloads["reviews/next-task-source-review.json"])
        self.check(review["source_commit"] == FINAL
                   and review["observed_request"] == "execution/candidate-original28-001/P09/request-result.json"
                   and review["product_or_capture_execution_performed"] is False
                   and review["complete_remaining_cost_or_new_pass_claimed"] is False
                   and all(value == counts.get(key, 0) for key, value in review["observed_counts"].items()),
                   "Next-task source review differs from observed scope/counters")
        return {"request_hashes_counters_diagnostics_frames_verified": True, "P09_observed": observation,
                "command_exit_code": 0, "command_stdout_and_driver_verified": True,
                "driver_sha256": DRIVERS[driver],
                "remaining_complete_cost_known": False, "capture_executed": False,
                "review_prose_is_retained_source_judgment_not_an_execution_result": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root, output = args.root.resolve(), args.output.absolute()
    if output.exists() or output.is_relative_to(root) or not output.parent.is_dir():
        parser.error("Use a fresh file in an existing directory outside the repository")
    if any(path.is_symlink() for path in (output, *output.parents)):
        parser.error("Audit output path components must not be symlinks")
    audit = Audit(root)
    result = {"schema_version": "ontokin.independent-checkpoint-audit/0.1", "checkpoint": 28,
              "status": "running", "started_at": datetime.now(timezone.utc).isoformat(),
              "command": [sys.executable, *sys.argv], "root": str(root),
              "auditor_sha256": digest(Path(__file__).read_bytes()),
              "scope": "In-memory archive/raw evidence/Git inspection; no product execution or archive extraction",
              "release_acceptance": False, "full_product_goal_completed": False}
    try:
        summary, payloads, result["archive"] = audit.archive(28)
        _, prior, result["prior_archive"] = audit.archive(27)
        audit.check(payloads["drivers/audit_checkpoint028.py"] == Path(__file__).read_bytes(),
                    "Executed auditor differs from archived source")
        evidence = root.parent / "evidence028"
        if evidence.is_dir():
            actual = set()
            for path in evidence.rglob("*"):
                name = path.relative_to(evidence).as_posix()
                if "__pycache__" in path.relative_to(evidence).parts or path.suffix == ".pyc":
                    continue
                audit.check(not path.is_symlink(), "Symlink in raw evidence inventory")
                if path.is_file():
                    actual.add(name)
                    audit.check(name in payloads and audit.regular(evidence, name).read_bytes() == payloads[name],
                                "Archive differs from preserved raw evidence: " + name)
            audit.check(actual == set(payloads), "Raw evidence/member inventory closure mismatch")
            result["preserved_raw_evidence_inventory_verified"] = True
        else:
            result["preserved_raw_evidence_inventory_verified"] = False
            result["raw_inventory_note"] = "Original scratch evidence unavailable; archive closure and all Git bindings verified independently."
        commands = {PurePosixPath(name).stem for name in payloads
                    if name.startswith("commands/") and name.endswith(".json")}
        audit.check(commands == RUNS | {"original28-comparison-001", "failure-stage-analysis-001"},
                    "Actual command attempt inventory mismatch")
        execution = {name.split("/")[1] for name in payloads if name.startswith("execution/")}
        audit.check(execution == RUNS, "Execution attempt inventory mismatch")
        for name, expected in DRIVERS.items():
            audit.check(digest(payloads["drivers/" + name]) == expected, "Reviewed driver source changed: " + name)
        previous_finish = None
        for name in ("candidate-focused-001", "candidate-controls-001", "candidate-focused-002",
                     "candidate-related-001", "candidate-original28-001", "original28-comparison-001",
                     "failure-stage-analysis-001"):
            receipt = decode(payloads["commands/" + name + ".json"])
            start, finish = [datetime.fromisoformat(receipt[key]) for key in ("started_at", "finished_at")]
            audit.check(previous_finish is None or start >= previous_finish, "Recorded execution attempts overlap")
            previous_finish = finish
        audit.recovery(payloads, result["prior_archive"])
        result["sources"] = audit.source_cuts(payloads)
        result["tests"] = [audit.tests(payloads, run, commit, count, modules) for run, commit, count, modules in (
            ("candidate-focused-001", MEASURED, 60, FOCUSED),
            ("candidate-focused-002", FINAL, 61, FOCUSED),
            ("candidate-related-001", FINAL, 154, RELATED))]
        old_impl, new_impl = audit.implementation(CONTROL), audit.implementation(FINAL)
        audit.check(audit.implementation(MEASURED) == new_impl, "Measured/final implementation fingerprint differs")
        result["prefix_controls"] = audit.controls(payloads, new_impl)
        result["original28"] = audit.comparison(payloads, prior, old_impl, new_impl)
        result["captured_publication"] = audit.publication(payloads, summary)
        audit.summary_claims(payloads, summary, result["original28"], result["prior_archive"])
        result["failure_stage_analysis"] = audit.failure_analysis(payloads, summary)
        impl = summary["implementation"]
        audit.check(impl["tested_commit"] == FINAL and impl["tree"] == TREES[FINAL] and impl["measured_commit"] == MEASURED,
                    "Checkpoint implementation identities mismatch")
        facts = {"focused_initial_passed": 60, "focused_passed": 61, "related_passed": 154,
                 "prefix_pairs": 15, "prefix_requests": 30,
                 "prefix_savings": {case: 5 * values[2] for case, values in PREFIX.items()},
                 "original28_passed": result["original28"]["passed"],
                 "original28_failed": result["original28"]["failed"],
                 "original28_status": result["original28"]["recording_gate_status"],
                 "original28_completed_saved_operations": result["original28"]["saved_total_over_common_completed_requests"]}
        for key, value in facts.items():
            audit.check(summary["results"][key] == value, "Checkpoint result not supported by actual evidence: " + key)
        audit.check(summary["release_acceptance"] is False and summary["full_product_goal_completed"] is False
                    and summary.get("release_input_closure", False) is False,
                    "Checkpoint overstates release/product completion")
        result["verified_results"] = facts
        result["input_receipts"] = audit.snapshots
        audit.close()
        result["status"] = "passed"
    except BaseException as error:
        result.update(status="failed", failure={"type": type(error).__name__, "message": str(error)},
                      traceback=traceback.format_exc())
    finally:
        try:
            audit.close()
        except BaseException as error:
            result.update(status="failed", cleanup_failure={"type": type(error).__name__, "message": str(error)})
        result["checks_performed"] = audit.count
        result["finished_at"] = datetime.now(timezone.utc).isoformat()
        with output.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({key: result[key] for key in ("status", "checks_performed", "verified_results", "failure") if key in result}))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
