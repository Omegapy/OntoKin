"""Provider-neutral, measured F01--F12 evidence under OK-ENG-008.

Fixture expectations are inputs. The source runner compares actual engine
states with the separately adopted corpus, including its additive errata. The
retained-evidence auditor never executes a command supplied by an evidence file.
Local execution replaces a provider, not the roles or compatibility matrix.
"""
from __future__ import annotations

import argparse
from bisect import bisect_right
from collections import Counter
import contextlib
import copy
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import importlib
import importlib.metadata
import io
import json
import math
import os
from pathlib import Path, PurePosixPath
import platform
import re
import subprocess
import struct
import sys
import time

from . import construction_conformance as construction
from . import impulse_conformance as impulse
from . import surface_conformance as surface
from .bundle import load_file_manifest
from .construction import compile_construction
from .diagnostics import OntoKinError
from .evaluator import evaluate, evaluate_prefix
from .program_diagnostics import diagnostic_dict

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "docs/language-design/force-v0.1"
MAP_PATH = FIXTURES / "conformance-local-v0.1.json"
SCHEMA = "ontokin.force-local-conformance/0.1"
EVIDENCE_SCHEMA = "ontokin.force-release-evidence/0.1"
EXECUTION_SCHEMA = "ontokin.local-execution/0.1"
SOURCE_SCHEMA = "ontokin.force-source-execution/0.1"
MAPPING_SHA256 = 'sha256:813b4e6d0ec53d5239f91737a1dc638bf1b5b9e23e0ed515c96a6b0a63202386'
SOURCE_IDS = tuple([f"P{i:02}" for i in range(1, 23)]
                   + [f"N{i:02}" for i in range(1, 23)]
                   + [f"S{i:02}" for i in range(1, 13)])
ACCEPTANCE_SHA256 = "sha256:de423575e648ea9e14d8de8d5bb9b2bbe6330ae6fb01e182e34c3cb6df9d2ba2"
REVIEWED_SHA256 = "sha256:2311dc26425cd3257df33e71e3246e2b6e14bba887da55bddc4b26915492c420"
PYTHONS = ("3.11", "3.12", "3.13")
NODE_PINS = {"three": "0.180.0", "gltf-validator": "2.0.0-dev.3.10",
             "playwright": "1.56.1", "esbuild": "0.25.10"}
POSITIVE_DESTINATIONS = tuple([f"P{i:02}" for i in range(1, 18)]
                              + ["P19", "P21", "P22", "held-out-oblique", "held-out-spin", "held-out-prefix"])
AGENT_DESTINATIONS = ("P01", "P07", "P10", "P11", "P12", "P13", "P21")
BROWSER_DESTINATIONS = ("P02", "P07", "P09", "P10", "P11", "P12", "P13", "held-out-oblique", "held-out-spin")
_SHA = re.compile(r"sha256:[0-9a-f]{64}\Z")
_COMMIT = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
_require = construction._require
implementation_identity = construction.implementation_identity
file_identity = construction.file_identity


class EvidenceError(ValueError):
    """An identified input contradicts its contract or retained bytes."""


class MissingEvidence(EvidenceError):
    """A required current execution or observation has not been supplied."""


def require(condition, message):
    if not condition:
        raise EvidenceError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")


def digest(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def json_file(path):
    path = Path(path)
    require(path.stat().st_size <= 64 * 1024 * 1024, "An evidence JSON input exceeds 64 MiB.")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "Duplicate JSON member: " + key)
            result[key] = value
        return result
    def invalid(value):
        raise EvidenceError("Nonfinite JSON number: " + value)
    def finite_float(value):
        number = float(value)
        require(math.isfinite(number), "Nonfinite JSON exponent: " + value)
        return number
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique,
                      parse_constant=invalid, parse_float=finite_float)


def relative_file(root, name):
    require(isinstance(name, str) and name and "\\" not in name,
            "Evidence paths must be nonempty relative POSIX paths.")
    require(not PurePosixPath(name).is_absolute() and
            all(part not in ("", ".", "..") for part in name.split("/")),
            "Evidence paths must not escape or contain ambiguous segments.")
    root = Path(root).resolve()
    path = root
    for part in name.split("/"):
        path = path / part
        require(not path.is_symlink(), "Evidence must not use a symlink: " + name)
    if not path.exists():
        raise MissingEvidence("Missing retained file: " + name)
    require(path.is_file(), "Evidence must identify a regular file: " + name)
    path.resolve().relative_to(root)
    return path


def identified(record, root):
    require(isinstance(record, dict) and _SHA.fullmatch(record.get("sha256", "")),
            "Every evidence file needs an exact SHA-256 identity.")
    path = relative_file(root, record.get("path"))
    require(file_identity(path) == record["sha256"], "Retained bytes changed: " + record["path"])
    require(type(record.get("byte_length")) is int and record["byte_length"] == path.stat().st_size,
            "Retained byte length changed: " + record["path"])
    return path


def file_record(path, root):
    path, root = Path(path), Path(root)
    name = path.resolve().relative_to(root.resolve()).as_posix()
    relative_file(root, name)
    return {"path": name, "sha256": file_identity(path), "byte_length": path.stat().st_size}


def eligible_path(name):
    """All current executable and normative inputs; retained reports are outputs."""
    path = PurePosixPath(name)
    parts = path.parts
    if not parts or any(p in {"node_modules", "__pycache__"} for p in parts):
        return False
    if name in {"pyproject.toml", "tools/package.json", "tools/package-lock.json", "tools/force-agent-verification-requirements.txt"}:
        return True
    if parts[0] in {"ontokin", "tests", "tools", "prototypes", "schemas"}:
        return path.suffix in {".py", ".mjs", ".js", ".json", ".html", ".ebnf"}
    if parts[:2] == (".github", "workflows"):
        return path.suffix in {".yml", ".yaml"}
    if parts[0] == "examples":
        return path.suffix == ".ok" or name in {"examples/visual/viewer.js", "examples/visual/viewer.html"}
    if parts[:2] == ("docs", "engineering"):
        return len(parts) == 3 and path.name.startswith("OK-") and path.suffix == ".md"
    if parts[:2] == ("docs", "language-design"):
        return path.suffix in {".py", ".ok", ".json", ".md", ".html", ".mjs", ".ebnf"}
    if parts[:2] == ("docs", "product"):
        return path.suffix in {".md", ".json", ".html"}
    if parts[:3] == ("docs", "maintenance", "reorganization-2026-10-17"):
        return path.name in {"verify_reorganization.py", "source-map.json"}
    return False


def evidence_inventory(root=ROOT):
    root = Path(root)
    records = []
    for directory in ("ontokin", "tests", "tools", "prototypes", "schemas", "examples", "docs/language-design",
                       "docs/product", "docs/maintenance", "docs/engineering", ".github/workflows"):
        for path in (root / directory).rglob("*"):
            name = path.relative_to(root).as_posix()
            if path.is_file() and eligible_path(name):
                require(not path.is_symlink(), "A validation input is a symlink: " + name)
                records.append({"path": name, "sha256": file_identity(path), "byte_length": path.stat().st_size})
    for name in ("pyproject.toml",):
        if (root / name).is_file():
            records.append(file_record(root / name, root))
    return sorted(records, key=lambda record: record["path"])


def git_environment():
    # Never inherit an alternate index/object store, hooks, remote URL rewrite,
    # repository override, or GIT_CONFIG_COUNT injection from the caller.
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_OPTIONAL_LOCKS="0",
               GIT_NO_REPLACE_OBJECTS="1", GIT_NO_LAZY_FETCH="1", GIT_TERMINAL_PROMPT="0")
    return env


def git(args, root=ROOT):
    result = subprocess.run(["git", "-c", "core.fsmonitor=false", "-c", "core.hooksPath=/dev/null", *args],
                            cwd=root, env=git_environment(), capture_output=True, check=False)
    require(result.returncode == 0, "Read-only Git identity failed: " + result.stderr.decode("utf-8", "replace")[:1000])
    return result.stdout


def verify_commit_inputs(commit, tree, inventory, root=ROOT):
    require(isinstance(commit, str) and _COMMIT.fullmatch(commit), "An execution must identify a full Git commit.")
    observed_tree = git(["rev-parse", commit + "^{tree}"], root).decode().strip()
    require(observed_tree == tree, "Captured commit and tree disagree.")
    objects = {}
    for item in git(["ls-tree", "-r", "-z", "--full-tree", commit], root).split(b"\0"):
        if not item:
            continue
        head, raw_name = item.split(b"\t", 1)
        mode, kind, oid = head.decode().split(" ")
        name = raw_name.decode("utf-8")
        if eligible_path(name):
            require(kind == "blob" and mode in ("100644", "100755"), "Committed validation input is not a regular blob: " + name)
            objects[name] = oid
    require(set(objects) == {r["path"] for r in inventory}, "Captured Git tree omits or adds eligible validation inputs.")
    algorithm = "sha256" if len(commit) == 64 else "sha1"
    for record in inventory:
        raw = relative_file(root, record["path"]).read_bytes()
        require(digest(raw) == record["sha256"] and len(raw) == record["byte_length"],
                "Current validation input differs from the captured inventory: " + record["path"])
        blob = hashlib.new(algorithm, b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        require(blob == objects[record["path"]], "Captured Git blob differs from current input: " + record["path"])
    return {"commit": commit, "tree": tree, "eligible_blobs": len(objects)}


def source_identity():
    inputs = evidence_inventory()
    commit = git(["rev-parse", "HEAD"]).decode().strip()
    tree = git(["rev-parse", "HEAD^{tree}"]).decode().strip()
    changes = git(["status", "--porcelain=v1", "-z", "--untracked-files=all"]).decode("utf-8", "replace").split("\0")
    issues = []
    try:
        verify_commit_inputs(commit, tree, inputs)
    except EvidenceError as error:
        issues.append(str(error))
    return {"implementation": implementation_identity(), "git": {"commit": commit, "tree": tree,
            "worktree_changes": [item for item in changes if item]}, "inputs": inputs,
            "input_inventory_sha256": digest(canonical(inputs)), "committed_inputs_match": not issues,
            "commit_issues": issues}


def stable_source(before, after):
    return (before["implementation"] == after["implementation"] and before["inputs"] == after["inputs"]
            and before["git"]["commit"] == after["git"]["commit"] and before["git"]["tree"] == after["git"]["tree"])


def load_manifest():
    require(file_identity(MAP_PATH) == MAPPING_SHA256, "The adopted local mapping bytes changed without a separately identified decision.")
    mapping = json_file(MAP_PATH)
    require(mapping["schema_version"] == "ontokin.force-local-conformance-map/0.1"
            and mapping["status"] == "predetermined_expectations_not_execution_results",
            "Unsupported or retrospective force conformance mapping.")
    require([case["id"] for case in mapping["cases"]] == [f"F{i:02}" for i in range(1, 13)],
            "The mapping must retain F01--F12 exactly once, in order.")
    require(mapping["source_case_ids"] == list(SOURCE_IDS) and mapping["python_matrix"] == list(PYTHONS),
            "The complete adopted source corpus or compatibility matrix changed.")
    require(file_identity(FIXTURES / "acceptance.json") == ACCEPTANCE_SHA256
            and file_identity(FIXTURES / "reviewed-acceptance.json") == REVIEWED_SHA256,
            "Frozen force acceptance bytes changed; preserve them and adopt a separate decision.")
    for name, expected in mapping["fixture_inputs"].items():
        require(file_identity(relative_file(FIXTURES, name)) == expected, "Adopted force input changed: " + name)
    for case in mapping["cases"]:
        require(set(case["source_case_ids"]) <= set(SOURCE_IDS), "Unknown adopted source case in a gate.")
        names = case["required_tests"]
        require(isinstance(names, list) and len(names) == len(set(names))
                and all(construction._TEST_ID.fullmatch(name) for name in names),
                "Gate tests must be literal, unique, discoverable unittest IDs.")
    return mapping


def rational(value):
    if isinstance(value, dict):
        return Fraction(int(value["numerator"]), int(value["denominator"]))
    return Fraction(str(value))


def clock(value):
    value = rational(value)
    numerator, denominator = value.numerator, value.denominator
    twos = fives = 0
    while denominator % 2 == 0:
        denominator //= 2
        twos += 1
    while denominator % 5 == 0:
        denominator //= 5
        fives += 1
    require(denominator == 1, "An adopted source clock must have an exact finite decimal representation.")
    places = max(twos, fives)
    integer = abs(numerator) * 2 ** (places - twos) * 5 ** (places - fives)
    sign = "-" if numerator < 0 else ""
    if not places:
        return sign + str(integer)
    digits = str(integer).rjust(places + 1, "0")
    return (sign + digits[:-places] + "." + digits[-places:]).rstrip("0").rstrip(".")


def close_vector(actual, expected, label, *, exact=False):
    require(isinstance(actual, list) and len(actual) == len(expected), label + " has a different dimension.")
    for observed, wanted in zip(actual, expected):
        require(type(observed) in (int, float) and math.isfinite(observed), label + " is not finite.")
        require(observed == wanted if exact else abs(observed - wanted) <= 1e-9,
                label + " differs from its adopted independent value.")


def orientation(actual, expected):
    require(len(actual) == len(expected) == 4 and all(type(x) in (int, float) and math.isfinite(x) for x in actual),
            "Orientation must be a finite quaternion.")
    require(abs(math.hypot(*actual) - 1) <= 1e-12, "Orientation is not normalized.")
    expected = [x / math.hypot(*expected) for x in expected]
    distance = min(math.dist(actual, expected), math.dist(actual, [-x for x in expected]))
    require(4 * math.asin(min(1, distance / 2)) <= 1e-9, "Orientation differs from its adopted independent value.")


class SourceCorpus:
    """Apply adopted corrections independently, checking every old-value guard."""
    def __init__(self):
        self.mapping = load_manifest()
        base = json_file(FIXTURES / "acceptance.json")
        reviewed = json_file(FIXTURES / "reviewed-acceptance.json")
        self.cases = {case["id"]: copy.deepcopy(case) for case in base["source_cases"] + reviewed["source_cases"]}
        require(tuple(self.cases) == SOURCE_IDS, "The adopted 56-case source inventory changed.")
        self.errata = json_file(FIXTURES / "source-errata.json")
        require(self.errata["schema_version"] == "ontokin.force-source-errata/0.1"
                and self.errata["status"] == "adopted-fixture-correction"
                and self.errata["original_files_preserved"] is True
                and self.errata["tolerances_unchanged"] is True,
                "Unsupported force errata or changed tolerances.")
        self.bundles = {name: load_file_manifest(FIXTURES / case["file_manifest"])
                        for name, case in self.cases.items()}
        self.applied = []
        for correction in self.errata["corrections"]:
            name = correction["id"]
            original = load_file_manifest(FIXTURES / correction["original_file_manifest"])
            updated = load_file_manifest(FIXTURES / correction["file_manifest"])
            require(original.program_revision == correction["original_program_revision"]
                    and original.entry.revision == correction["original_source_sha256"]
                    and updated.program_revision == correction["program_revision"]
                    and updated.entry.revision == correction["source_sha256"],
                    "A source erratum identifies different original or corrected bytes.")
            require(original.entry.text.count(correction["replaced_utf8"]) == 1
                    and original.entry.text.replace(correction["replaced_utf8"], correction["replacement_utf8"])
                    == updated.entry.text and original.modules == updated.modules
                    and correction["expected"] == self.cases[name]["expected"],
                    "A source correction exceeded its adopted span or changed the expected outcome.")
            self.bundles[name] = updated
            self.applied.append({"id": name, "kind": "source", "program_revision": updated.program_revision})
        for correction in self.errata["sample_corrections"]:
            candidates = [row for row in self.cases[correction["id"]]["expected_samples"]
                          if all(row[k] == correction[k] for k in ("time", "side", "target"))]
            require(len(candidates) == 1, "An adopted sample erratum is ambiguous or absent.")
            row = candidates[0]
            require(all(row[key] == value for key, value in correction["old"].items()),
                    "An adopted sample erratum old-value precondition changed.")
            row.update(copy.deepcopy(correction["new"]))
            self.applied.append({"id": correction["id"], "kind": "sample", "time": correction["time"],
                                 "side": correction["side"], "target": correction["target"]})
        for name, bundle in self.bundles.items():
            if name not in {c["id"] for c in self.errata["corrections"]}:
                require(bundle.program_revision == self.cases[name]["program_revision"],
                        "A frozen source bundle differs from its adopted program revision.")

    def literal_book(self):
        from tools.verify_force_agent_workflow import SourceBook
        book = SourceBook()
        # The supplemental reversal intentionally changes statement order. Read
        # its literal operands and byte locations directly; P19's physical
        # values are an oracle, but P19's statement order is not S01's order.
        bundle = self.bundles["S01"]
        spans = []
        for found in re.finditer(r"\bforce [^;]+;", bundle.entry.text):
            spans.append({"start_byte": len(bundle.entry.text[:found.start()].encode("utf-8")),
                          "end_byte": len(bundle.entry.text[:found.end()].encode("utf-8")), "text": found.group()})
        book.cases["S01"] = {**self.cases["S01"], "force_statements": spans}
        book.bundles["S01"] = bundle
        book.records["S01"] = book.source_records("S01")
        return book

    def compare_sample(self, sample, expected, *, exact=False, target=None, full=True):
        require(sample["time_seconds"] == clock(expected["time"]) and sample["side"] == expected["side"],
                "Source evaluation returned a different exact time or side.")
        obj = sample["objects"][target or expected["target"]]
        for actual, wanted in (("position_m", "position_m"), ("velocity_m_per_s", "velocity_m_s"),
                               ("angular_velocity_rad_per_s", "omega_world_rad_s")):
            close_vector(obj[actual], expected[wanted], actual, exact=exact)
        orientation(obj["orientation_wxyz"], expected["orientation_wxyz"])
        force = obj["forces"]
        require(type(force["started_count"]) is int and force["started_count"] == expected["started_count"]
                and type(force["completed_count"]) is int and force["completed_count"] == expected["completed_count"],
                "The complete force interval counts differ from the adopted oracle.")
        if not full:
            return
        require([r["force_key"] for r in force["active"]] == expected["active_keys"], "The active force keys differ.")
        require({r["force_key"]: r["completion_time_seconds"] for r in force["active"]}
                == {key: clock(value) for key, value in expected["active_ends"].items()}, "An exact force completion changed.")
        require(force["last_change_time_seconds"] == (None if expected["last_boundary"] is None else clock(expected["last_boundary"]))
                and [{"kind": r["kind"], "key": r["force_key"]} for r in force["last_changes"]] == expected["last_changes"],
                "A latest-boundary force history changed.")
        close_vector(force["net_force_world_n"], expected["net_force_world_n"], "net force", exact=exact)
        if expected["acceleration_world_m_s2"] is None:
            require(force["acceleration_world_m_per_s2"] is None, "A nondynamic object gained force acceleration.")
        else:
            close_vector(force["acceleration_world_m_per_s2"], expected["acceleration_world_m_s2"], "acceleration", exact=exact)
        if expected["dynamic_since"] is not None:
            require(obj["pose_authority"]["since_seconds"] == clock(expected["dynamic_since"])
                    and obj["pose_authority"]["trajectory_anchor_seconds"] == clock(expected["anchor_time"]),
                    "The dynamic origin or acceleration anchor changed.")

    def execute_case(self, name):
        case, bundle = self.cases[name], self.bundles[name]
        result = {"id": name, "name": case["name"], "program_revision": bundle.program_revision,
                  "source_manifest": bundle.manifest(), "expected_sha256": digest(canonical(case)),
                  "status": "running", "observations": [], "checks": []}
        started = time.monotonic()
        expected = case.get("expected", {})
        try:
            invalid = case.get("kind") == "negative" or case.get("outcome") == "invalid"
            code = expected.get("diagnostic_code", expected.get("code"))
            if invalid and expected["phase_group"] in ("elaboration", "support"):
                try:
                    compile_construction(bundle)
                except OntoKinError as error:
                    require(error.code == code, "Unexpected source diagnostic: " + error.code)
                    result["diagnostic"] = diagnostic_dict(error.diagnostic, bundle)
                else:
                    raise EvidenceError("Invalid adopted source was accepted.")
                result["checks"].append("exact expected compile/support rejection")
            else:
                model = compile_construction(bundle).model
                require(model.profile == "force-0.1" and model.program_revision == bundle.program_revision
                        and model.source_manifest == bundle.manifest(), "Compilation changed the actual source profile or revision.")
                if invalid:
                    if "valid_prefix" in expected:
                        short = evaluate_prefix(model, expected["valid_prefix"])
                        require(short["failure"] is None, "An adopted valid short prefix failed.")
                        result["observations"].append(short["last_valid_state"])
                    failed = evaluate_prefix(model, model.duration)
                    error = failed["failure"]
                    require(error is not None and error.code == code, "Expected evaluated failure is missing or changed.")
                    wanted_time = rational(expected.get("time", expected.get("failure_time")))
                    wanted_side = expected.get("side", expected.get("failure_side"))
                    require(error.diagnostic.time == wanted_time and error.diagnostic.side == wanted_side,
                            "Failure time/side changed.")
                    if name.startswith("N") or name == "S06":
                        require(failed["valid_until_seconds"] == clock(wanted_time) and failed["valid_until_side"] == "before",
                                "The retained boundary prefix changed.")
                    result["diagnostic"] = diagnostic_dict(error.diagnostic, bundle)
                    result["last_valid_state"] = failed["last_valid_state"]
                    result["valid_until"] = {"time_seconds": failed["valid_until_seconds"], "side": failed["valid_until_side"]}
                    if name == "N21":
                        require(failed["last_valid_state"]["joints"]["hold"]["status"] == "active", "Failed release leaked a joint change.")
                    if name == "N22":
                        require(failed["last_valid_state"]["objects"]["ball"]["forces"]["started_count"] == 0,
                                "Failed sequence leaked an accepted force.")
                    if name == "S06":
                        force = failed["last_valid_state"]["objects"]["ball"]["forces"]
                        require([r["force_key"] for r in force["active"]] == expected["retained_active_keys"]
                                and force["started_count"] == expected["retained_started_count"]
                                and force["completed_count"] == expected["retained_completed_count"],
                                "Automatic completion failure did not roll back atomically.")
                        changed = error.diagnostic.details["changed_forces"][0]
                        require(changed["force_key"] == "b" and error.diagnostic.node.start == changed["source_location"]["start_byte"],
                                "Automatic failure lost its authored provenance.")
                    result["checks"].append("exact expected failure and retained atomic prefix")
                elif "expected_samples" in case or "same_physical_samples_as" in expected:
                    rows = case.get("expected_samples", self.cases.get(expected.get("same_physical_samples_as"), {}).get("expected_samples"))
                    requests = [{"time": rational(row["time"]), "side": row["side"]} for row in rows]
                    if name == "P21":
                        samples = []
                        for request in requests:
                            prefix = evaluate_prefix(model, request["time"], side=request["side"])
                            require(prefix["failure"] is None, "The adopted valid force prefix failed.")
                            samples.append(prefix["last_valid_state"])
                    else:
                        samples = evaluate(model, requests)["samples"]
                    require(len(samples) == len(rows), "An adopted source request was omitted.")
                    for sample, row in zip(samples, rows):
                        self.compare_sample(sample, row, exact=name in {"P18", "P19", "P20", "S01"},
                                            target=expected.get("target_path"), full="expected_samples" in case)
                    # The independently authored literal-force reader checks every
                    # actual force field against raw source, not lowered events.
                    if name.startswith("P") or name == "S01":
                        book = self.literal_book()
                        for sample in samples:
                            for target, obj in sample["objects"].items():
                                book.check_projection(name, target, obj, rational(sample["time_seconds"]), sample["side"])
                    if name == "S01":
                        for sample, row in zip(samples, rows):
                            obj = sample["objects"][row["target"]]
                            require(obj["pose_authority"]["trajectory_anchor_seconds"] == clock(row["anchor_time"])
                                    and obj["pose_authority"]["since_seconds"] == clock(row["dynamic_since"]),
                                    "Reordering the final force sum changed a physical anchor.")
                    result["observations"] = samples
                    result["checks"].append("predetermined physical poses, exact interval history and independent source provenance")
                elif name == "S09":
                    end = rational(expected["completion_clock"])
                    samples = evaluate(model, [{"time": end, "side": "before"}, {"time": end, "side": "after"}])["samples"]
                    before, after = [sample["objects"]["ball"] for sample in samples]
                    require([r["force_key"] for r in before["forces"]["active"]] == ["push"]
                            and after["forces"]["active"] == [] and after["forces"]["started_count"] == 1
                            and after["forces"]["completed_count"] == 1
                            and all(obj["pose_authority"]["trajectory_anchor_seconds"] == "0"
                                    and obj["forces"]["net_force_world_n"] == [0, 0, 0] for obj in (before, after)),
                            "Smallest positive source duration was rounded away or changed the anchor.")
                    result["observations"] = samples
                    result["checks"].append("exact smallest-positive completion on both sides")
                elif name == "S11":
                    samples = evaluate(model, ["1"])["samples"]
                    require(set(samples[0]["objects"]) == {"marker"}, "Same-profile imported construction changed.")
                    force = samples[0]["objects"]["marker"]["forces"]
                    require(force["active"] == [] and force["started_count"] == force["completed_count"] == 0
                            and force["acceleration_world_m_per_s2"] is None, "Imported static object gained physical force state.")
                    result["observations"] = samples
                    result["checks"].append("same-profile import and complete empty force projection")
                elif name == "S12":
                    samples = evaluate(model, [expected["time"]])["samples"]
                    obj = samples[0]["objects"]["ball"]
                    close_vector(obj["position_m"], expected["position_m"], "reversed force position")
                    close_vector(obj["velocity_m_per_s"], expected["velocity_m_s"], "reversed force velocity")
                    force = obj["forces"]
                    require(force["completed_count"] == expected["completed_count"]
                            and force["started_count"] == expected["started_count"]
                            and force["net_force_world_n"] == expected["net_force_after_n"], "Reversed force history changed.")
                    result["observations"] = samples
                    result["checks"].append("independent reversed-force final state")
                else:
                    raise EvidenceError("No independent source checker for " + name)
            result["status"] = "passed"
        except Exception as error:
            result["status"] = "failed"
            result["error"] = f"{type(error).__name__}: {error}"
        result["elapsed_seconds"] = round(time.monotonic() - started, 6)
        result["observations"] = [retained_state(state) for state in result["observations"]]
        if "last_valid_state" in result:
            result["last_valid_state"] = retained_state(result["last_valid_state"])
        return result


def retained_state(state):
    """Wire-safe physical evidence, without private compiled geometry objects."""
    fields = ("element_id", "position_m", "orientation_wxyz", "velocity_m_per_s", "angular_velocity_rad_per_s",
              "motion", "own_mass_kg", "inertia_kg_m2", "forces", "impulses", "pose_authority")
    return {"time_seconds": state["time_seconds"], "side": state["side"],
            "objects": {name: {key: copy.deepcopy(obj[key]) for key in fields if key in obj}
                        for name, obj in state["objects"].items()},
            "joints": {name: {"status": value["status"]} for name, value in state.get("joints", {}).items()},
            "actions": {name: {"status": value["status"]} for name, value in state.get("actions", {}).items()}}


def execute_sources():
    corpus = SourceCorpus()
    before = source_identity()
    cases = [corpus.execute_case(name) for name in SOURCE_IDS]
    after = source_identity()
    passed = all(case["status"] == "passed" for case in cases) and stable_source(before, after)
    return {"schema_version": SOURCE_SCHEMA, "executed": True,
            "implementation": before["implementation"], "source_before": before, "source_after": after,
            "source_stable_during_run": stable_source(before, after), "fixture_inputs": corpus.mapping["fixture_inputs"],
            "applied_errata": corpus.applied, "cases": cases,
            "summary": {"total": len(cases), "passed": sum(c["status"] == "passed" for c in cases),
                        "failed": sum(c["status"] != "passed" for c in cases), "all_passed": passed},
            "full_product_conformance_certified": False}


def measured_tests(names):
    before = source_identity()
    execution = construction._run_tests(names)
    after = source_identity()
    return {"schema_version": "ontokin.force-unittest-execution/0.1", "executed": True,
            "implementation": before["implementation"], "source_before": before, "source_after": after,
            "source_stable_during_run": stable_source(before, after), "expected_test_ids": names,
            "test_execution": execution,
            "summary": {"total": len(names), "all_passed": surface._execution_passes(execution, names) and stable_source(before, after)},
            "full_product_conformance_certified": False}


def execution_environment():
    packages = {}
    for name in ("jsonschema", "referencing", "jsonschema-specifications", "attrs", "rpds-py", "typing-extensions"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    return {"python": platform.python_version(), "python_implementation": platform.python_implementation(),
            "python_executable": sys.executable, "platform": platform.platform(), "system": platform.system(),
            "machine": platform.machine(), "verification_packages": packages}


def verification_pins():
    result = {}
    for line in (ROOT / "tools/force-agent-verification-requirements.txt").read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.fullmatch(r"([A-Za-z0-9_.-]+)==([A-Za-z0-9.!+_-]+)", line)
        require(match is not None, "Verification requirements must retain exact installed-version pins.")
        name = re.sub(r"[-_.]+", "-", match[1]).lower()
        require(name not in result, "A verification package pin is duplicated.")
        result[name] = match[2]
    require(set(result) == {"jsonschema", "referencing", "jsonschema-specifications", "attrs", "rpds-py", "typing-extensions"},
            "The required six-package validation closure changed.")
    return result


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def execute_role(role, output, *, external_evidence=None, evidence_root=ROOT):
    """Explicit actual Python execution. Agent/full-suite roles may open SQLite."""
    output = Path(output)
    require(not output.exists(), "Execution output must be a new directory; existing evidence is immutable.")
    output.mkdir(parents=True)
    mapping = load_manifest()
    before = source_identity()
    started = timestamp()
    log = io.StringIO()
    code = 0
    report = None
    try:
        with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            if role == "source":
                report = execute_sources()
                code = 0 if report["summary"]["all_passed"] else 1
            elif role == "mapped-tests":
                report = measured_tests(sorted({name for c in mapping["cases"] for name in c["required_tests"]}))
                code = 0 if report["summary"]["all_passed"] else 1
            elif role == "regression":
                report = impulse.run_full_suite()
                code = 0 if report["summary"]["all_passed"] else 1
            elif role in {"construction", "surface", "impulse"}:
                module = {"construction": construction, "surface": surface, "impulse": impulse}[role]
                keywords = {"external_evidence": external_evidence}
                if role != "construction":
                    keywords["evidence_root"] = evidence_root
                report = module.run_conformance(**keywords)
                # Missing retained provider evidence is pending, never a failed
                # process or a fabricated legacy pass. Its original status stays.
                code = 1 if report["summary"].get("failed", 0) else 0
            elif role == "core":
                from .conformance import run_conformance
                report = run_conformance()
                code = 1 if report["summary"]["failed"] else 0
            elif role == "agent":
                from tools.run_agent_conformance import run_cases
                report = run_cases()
                code = 1 if report["summary"]["failed"] else 0
            else:
                raise EvidenceError("Unknown executable Python role: " + role)
    except Exception as error:
        code = 1
        report = {"status": "failed", "error": f"{type(error).__name__}: {error}"}
        log.write(report["error"] + "\n")
    after = source_identity()
    (output / "execution.log").write_text(log.getvalue(), encoding="utf-8")
    write_json(output / "report.json", report)
    envelope = {"schema_version": EXECUTION_SCHEMA, "role": role, "executed": True,
                "provider": {"kind": "local", "hosted_ci_claimed": False},
                "argv": [sys.executable, *sys.argv], "cwd": str(ROOT), "environment": execution_environment(),
                "started_at_utc": started, "finished_at_utc": timestamp(), "exit_code": code,
                "status": "passed" if code == 0 and stable_source(before, after) else "failed",
                "source_before": before, "source_after": after, "source_stable_during_run": stable_source(before, after),
                "log": file_record(output / "execution.log", output), "report": file_record(output / "report.json", output),
                "full_product_conformance_certified": False}
    write_json(output / "execution.json", envelope)
    return envelope


EXTERNAL_ENTRYPOINTS = {
    "source-build": "tools/build_force_demo.py",
    "force-agent-build": "tools/build_force_agent_demo.py",
    "force-agent": "tools/verify_force_agent_workflow.py",
    "force-delivery-build": "tools/build_force_delivery_demo.py",
    "force-delivery": "tools/verify_force_delivery_workflow.py",
    "force-native": "tools/verify_force_native.mjs",
    "agent-native": "tools/verify_force_native.mjs",
    "force-browser": "tools/verify_force_viewer.mjs",
    "agent-browser": "tools/verify_force_viewer.mjs",
    "legacy-visual": "tools/check_local.py",
}


def check_external_command(role, argv, *, cwd=None):
    require(role in EXTERNAL_ENTRYPOINTS and isinstance(argv, list) and len(argv) >= 2
            and all(isinstance(item, str) and item for item in argv), "Unknown or incomplete external execution command.")
    # During execution this resolves the actual current entry point. During a
    # retained audit use the captured checkout path lexically: moving evidence
    # must not require the original checkout to exist or silently rebind argv.
    captured = Path(cwd) if cwd is not None else ROOT
    require(captured.is_absolute(), "An execution must identify its absolute working directory.")
    script = Path(argv[1])
    if not script.is_absolute():
        script = captured / script
    expected = captured / EXTERNAL_ENTRYPOINTS[role]
    observed = Path(os.path.normpath(script)) if cwd is not None else script.resolve()
    expected = Path(os.path.normpath(expected)) if cwd is not None else expected.resolve()
    require(observed == expected,
            "This role must execute its current repository entry point directly, without a shell or wrapper.")
    require(not any(option in argv[2:] for option in ("--help", "-h")), "Help output is not an executed validation role.")
    if role in {"agent-native", "agent-browser"}:
        require("--agent-workflow" in argv and "--agent-audit" in argv,
                "Retrieved-byte validation must select its actual Agent workflow and independently passed audit.")
    if role in {"force-native", "force-browser"}:
        require("--agent-workflow" not in argv, "A component role cannot relabel an Agent workflow.")
    if role == "legacy-visual":
        require("--full" in argv, "The inherited visual execution must run the complete local visual role.")


def record_external(role, argv, output, report_path):
    """Execute a directly requested known entry point and retain its actual result.

    This is deliberately separate from audit. The argv comes from the explicit
    CLI invocation, never from an evidence manifest or retained execution log.
    """
    check_external_command(role, argv)
    output, report_path = Path(output), Path(report_path)
    require(not output.exists(), "Execution output must be a new directory.")
    require(not report_path.exists(), "The command's primary output must be absent before execution.")
    output.mkdir(parents=True)
    before, started = source_identity(), timestamp()
    environment = execution_environment()
    if EXTERNAL_ENTRYPOINTS[role].endswith(".py"):
        probe = subprocess.run([argv[0], "-c", "import json; from ontokin.force_conformance import execution_environment; "
                                "print(json.dumps(execution_environment()))"], cwd=ROOT, capture_output=True, check=False, text=True)
        require(probe.returncode == 0, "The actual selected Python interpreter could not identify its environment.")
        environment = json.loads(probe.stdout)
    else:
        result = subprocess.run([argv[0], "--version"], cwd=ROOT, capture_output=True, check=False, text=True)
        require(result.returncode == 0, "The selected Node interpreter could not identify itself.")
        environment["node"] = result.stdout.strip()
        environment["node_packages"] = {name: json_file(ROOT / "tools/node_modules" / name / "package.json")["version"]
                                        for name in NODE_PINS}
    with (output / "execution.log").open("wb") as stream:
        result = subprocess.run(argv, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, check=False)
    after = source_identity()
    if report_path.is_file():
        raw = report_path.read_bytes()
        (output / "report.json").write_bytes(raw)
        report_record = file_record(output / "report.json", output)
    else:
        report_record = None
    envelope = {"schema_version": EXECUTION_SCHEMA, "role": role, "executed": True,
                "provider": {"kind": "local", "hosted_ci_claimed": False}, "argv": argv, "cwd": str(ROOT),
                "environment": environment, "started_at_utc": started, "finished_at_utc": timestamp(),
                "exit_code": result.returncode,
                "status": "passed" if result.returncode == 0 and report_record and stable_source(before, after) else "failed",
                "source_before": before, "source_after": after, "source_stable_during_run": stable_source(before, after),
                "log": file_record(output / "execution.log", output), "report": report_record,
                "original_report_path": str(report_path.resolve()), "report_absent_before_execution": True,
                "full_product_conformance_certified": False}
    write_json(output / "execution.json", envelope)
    return envelope


def as_sha(value):
    if isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value):
        return "sha256:" + value
    return value


def check_execution(envelope, envelope_dir, role, current, *, python=None):
    require(envelope.get("schema_version") == EXECUTION_SCHEMA and envelope.get("executed") is True
            and envelope.get("role") == role, "A role lacks its own actual execution envelope.")
    require(envelope.get("provider") == {"kind": "local", "hosted_ci_claimed": False},
            "A local role must disclose its provider without claiming hosted CI.")
    require(type(envelope.get("exit_code")) is int and envelope["exit_code"] == 0
            and envelope.get("status") == "passed", "A required command failed or did not execute.")
    require(envelope.get("source_stable_during_run") is True
            and stable_source(envelope["source_before"], envelope["source_after"]),
            "Eligible source, test, fixture, or tool bytes changed during execution.")
    for identity in (envelope["source_before"], envelope["source_after"]):
        if identity.get("implementation") != current["implementation"] or identity.get("inputs") != current["inputs"]:
            raise MissingEvidence("Stale execution: current implementation or eligible input bytes differ.")
        require(identity["input_inventory_sha256"] == digest(canonical(identity["inputs"])),
                "Execution input inventory digest contradicts its actual entries.")
        require(identity["committed_inputs_match"] is True and not identity["commit_issues"],
                "The executed input set did not match its captured Git tree.")
        verify_commit_inputs(identity["git"]["commit"], identity["git"]["tree"], identity["inputs"])
    begin = datetime.fromisoformat(envelope["started_at_utc"])
    end = datetime.fromisoformat(envelope["finished_at_utc"])
    require(begin.tzinfo is not None and end.tzinfo is not None and begin <= end, "Execution timestamps lack ordered timezone identities.")
    env = envelope["environment"]
    require(all(isinstance(env.get(name), str) and env[name] for name in
                ("python", "python_implementation", "python_executable", "platform", "system", "machine")),
            "Execution lacks an actual interpreter/platform identity.")
    require(env.get("verification_packages") == verification_pins(),
            "The actual Python environment did not contain the complete pinned verification package closure.")
    if python is not None:
        require(env["python_implementation"] == "CPython" and ".".join(env["python"].split(".")[:2]) == python,
                "This compatibility record did not execute the required CPython " + python + ".")
    argv = envelope.get("argv")
    if role in EXTERNAL_ENTRYPOINTS:
        check_external_command(role, argv, cwd=envelope.get("cwd"))
        require(envelope.get("report_absent_before_execution") is True, "A preexisting external report cannot stand in for this execution.")
    else:
        require(isinstance(argv, list) and len(argv) >= 2 and all(isinstance(x, str) and x for x in argv)
                and Path(envelope.get("cwd", "")).is_absolute(),
                "An execution envelope does not identify the explicit current Python runner invocation.")
        script = Path(argv[1])
        script = script if script.is_absolute() else Path(envelope["cwd"]) / script
        require(Path(os.path.normpath(script)) == Path(envelope["cwd"]) / "tools/run_force_conformance.py"
                and len(argv) > 4 and argv[2] == "execute" and argv.count("--role") == 1
                and argv[argv.index("--role") + 1] == role,
                "The actual runner path, subcommand or role selection differs from this envelope.")
    identified(envelope["log"], envelope_dir)
    return identified(envelope["report"], envelope_dir)


def check_tests(report, names, *, current=None):
    require(report.get("executed") is True and report.get("expected_test_ids") == names,
            "The actual test report omits or changes the expected literal test inventory.")
    require(surface._execution_passes(report["test_execution"], names),
            "Every required unittest must actually execute and pass, with zero skips, loader errors, or fixture errors.")
    require(all(type(row.get("elapsed_seconds")) in (int, float) and math.isfinite(row["elapsed_seconds"])
                and row["elapsed_seconds"] >= 0 for row in report["test_execution"]["tests"]),
            "A test record lacks a measured finite duration.")
    require(report["summary"]["all_passed"] is True, "The test report's summary contradicts a complete pass.")
    if current:
        require(report.get("implementation") == current["implementation"], "Test report implementation changed.")
    return {"tests": len(names), "test_ids_sha256": digest(canonical(names)), "skipped": 0}


def check_source_report(report):
    corpus = SourceCorpus()
    require(report.get("schema_version") == SOURCE_SCHEMA and report.get("executed") is True
            and report.get("implementation") == implementation_identity()
            and report.get("fixture_inputs") == corpus.mapping["fixture_inputs"]
            and report.get("applied_errata") == corpus.applied
            and report.get("source_stable_during_run") is True,
            "The force source execution is unexecuted, stale, or changes the adopted correction rules.")
    require([c.get("id") for c in report["cases"]] == list(SOURCE_IDS), "All 56 adopted source cases must be retained once.")
    book = corpus.literal_book()
    observed_samples = 0
    for found in report["cases"]:
        name = found["id"]
        case, bundle = corpus.cases[name], corpus.bundles[name]
        require(found["status"] == "passed" and found.get("checks") and not found.get("error")
                and found["program_revision"] == bundle.program_revision and found["source_manifest"] == bundle.manifest()
                and found["expected_sha256"] == digest(canonical(case)), "An adopted source case failed or identifies different bytes: " + name)
        expected = case.get("expected", {})
        invalid = case.get("kind") == "negative" or case.get("outcome") == "invalid"
        if invalid:
            diagnostic = found["diagnostic"]
            require(diagnostic["code"] == expected.get("diagnostic_code", expected.get("code"))
                    and diagnostic["program_revision"] == bundle.program_revision and diagnostic.get("primary"),
                    "An adopted source rejection lost its exact diagnostic identity.")
            if expected["phase_group"] not in ("elaboration", "support"):
                require(diagnostic["time"] == {"seconds": clock(expected.get("time", expected.get("failure_time"))),
                                                 "side": expected.get("side", expected.get("failure_side"))},
                        "A source failure time/side differs from the independent oracle.")
                state = found["last_valid_state"]
                require(found["valid_until"] == {"time_seconds": state["time_seconds"], "side": state["side"]}
                        and rational(state["time_seconds"]) <= rational(diagnostic["time"]["seconds"]),
                        "Failed source lost its actually certified prefix.")
                if name.startswith("N") or name == "S06":
                    require(state["side"] == "before" and rational(state["time_seconds"]) == rational(diagnostic["time"]["seconds"]),
                            "Failed source lost its retained incoming boundary state.")
                if name == "S05":
                    require(state["time_seconds"] == "0" and state["side"] == "after",
                            "An interior failure must retain the earlier certified segment anchor.")
                if name == "N21":
                    require(state["joints"]["hold"]["status"] == "active", "A failed release leaked into retained state.")
                if name == "N22":
                    require(state["objects"]["ball"]["forces"]["started_count"] == 0, "A failed sequence leaked a force.")
                if name == "S06":
                    force = state["objects"]["ball"]["forces"]
                    require([r["force_key"] for r in force["active"]] == expected["retained_active_keys"]
                            and force["started_count"] == 2 and force["completed_count"] == 0, "Automatic completion rollback evidence changed.")
        elif "expected_samples" in case or "same_physical_samples_as" in expected:
            rows = case.get("expected_samples", corpus.cases.get(expected.get("same_physical_samples_as"), {}).get("expected_samples"))
            samples = found["observations"]
            require(len(samples) == len(rows), "The retained source run omitted a required sample.")
            for sample, wanted in zip(samples, rows):
                corpus.compare_sample(sample, wanted, exact=name in {"P18", "P19", "P20", "S01"},
                                      target=expected.get("target_path"), full="expected_samples" in case)
                if name.startswith("P") or name == "S01":
                    for target, obj in sample["objects"].items():
                        book.check_projection(name, target, obj, rational(sample["time_seconds"]), sample["side"])
                if name == "S01":
                    obj = sample["objects"][wanted["target"]]
                    require(obj["pose_authority"]["trajectory_anchor_seconds"] == clock(wanted["anchor_time"])
                            and obj["pose_authority"]["since_seconds"] == clock(wanted["dynamic_since"]),
                            "The reversed source sum changed a physical anchor.")
            observed_samples += len(samples)
        elif name == "S09":
            before, after = found["observations"]
            require(rational(before["time_seconds"]) == rational(after["time_seconds"]) == rational(expected["completion_clock"])
                    and before["side"] == "before" and after["side"] == "after", "Smallest duration completion evidence changed.")
            require([r["force_key"] for r in before["objects"]["ball"]["forces"]["active"]] == ["push"]
                    and after["objects"]["ball"]["forces"]["active"] == []
                    and after["objects"]["ball"]["forces"]["completed_count"] == 1,
                    "Smallest duration interval was rounded away.")
        elif name == "S11":
            state = found["observations"][0]
            require(set(state["objects"]) == {"marker"} and state["objects"]["marker"]["forces"]["active"] == []
                    and state["objects"]["marker"]["forces"]["acceleration_world_m_per_s2"] is None,
                    "Same-profile imported marker gained force state.")
        elif name == "S12":
            obj = found["observations"][0]["objects"]["ball"]
            close_vector(obj["position_m"], expected["position_m"], "retained reverse force position")
            close_vector(obj["velocity_m_per_s"], expected["velocity_m_s"], "retained reverse force velocity")
            require(obj["forces"]["completed_count"] == expected["completed_count"], "Reversed force completion changed.")
    require(report["summary"] == {"total": 56, "passed": 56, "failed": 0, "all_passed": True},
            "The adopted source summary contradicts the executed cases.")
    return {"source_cases": 56, "retained_physical_samples": observed_samples, "applied_errata": corpus.applied}


def check_legacy_cases(report, schema, mapping, inventory, implementation):
    require(report.get("schema_version") == schema and report.get("executed") is True
            and report.get("implementation") == report.get("implementation_after_run") == implementation
            and report.get("evidence_stable_during_run") is True and not report.get("run_issues")
            and report.get("evidence_files") == inventory, "A current inherited conformance execution is stale or incomplete.")
    names = sorted({name for case in mapping["cases"] for name in case["required_tests"]})
    require(surface._execution_passes(report["test_execution"], names), "An inherited required method was not executed and passed.")
    require([c["id"] for c in report["cases"]] == [c["id"] for c in mapping["cases"]], "An inherited adopted gate is omitted or duplicated.")
    original = []
    for actual, wanted in zip(report["cases"], mapping["cases"]):
        require(actual["required_tests"] == wanted["required_tests"] and actual["external_gates"] == wanted["external_gates"],
                "An inherited gate changed its adopted test or evidence obligations.")
        require(actual["status"] in {"passed", "pending"}, "An inherited gate has an actual failed execution.")
        require(not wanted.get("unbound_requirements"), "An inherited non-provider requirement remains unbound.")
        if not wanted["external_gates"]:
            require(actual["status"] == "passed" and not actual["pending_reasons"], "An inherited source-only gate did not pass.")
        original.append({"id": actual["id"], "status": actual["status"], "pending_reasons": actual["pending_reasons"]})
    return {"cases": len(original), "measured_tests": len(names), "original_case_statuses": original}


def check_core_agent(core, agent, implementation):
    fixture_path = ROOT / "docs/language-design/core-v0.1/validation-cases.json"
    fixtures = json_file(fixture_path)
    require(core["schema_version"] == "ontokin.conformance-report/0.1"
            and core["source_code_sha256"] == implementation["source_code_sha256"].removeprefix("sha256:")
            and core["implementation_version"] == implementation["version"]
            and core["fixture_manifest_sha256"] == file_identity(fixture_path).removeprefix("sha256:"),
            "The core conformance report does not identify current source and frozen cases.")
    from .fixtures import materialize
    observed = {case["id"]: case for case in core["cases"]}
    require(len(observed) == len(core["cases"]) and set(observed) == {c["id"] for c in fixtures["cases"]},
            "The current core source corpus is incomplete.")
    for case in fixtures["cases"]:
        actual = observed[case["id"]]
        require(actual["status"] == "passed" and actual["checks"] and all(c["passed"] is True for c in actual["checks"])
                and actual["source_revision"] == digest(materialize(case, fixture_path.parent).encode()),
                "An inherited core case failed or used different source.")
    require(core["summary"]["passed"] == core["summary"]["total"] == len(observed) and core["summary"]["failed"] == 0,
            "The core summary contradicts its actual cases.")
    from tools.run_agent_conformance import CASE_TESTS, content_identity
    files = [ROOT / "tests/test_agent.py", ROOT / "tools/run_agent_conformance.py",
             ROOT / "docs/language-design/agent-v0.1/request.schema.json",
             ROOT / "docs/language-design/agent-v0.1/response.schema.json", fixture_path,
             fixture_path.parent / "diagnostic.schema.json", *fixture_path.parent.glob("*.ok")]
    require(agent["schema_version"] == "ontokin.agent-conformance/0.1" and agent["executed"] is True
            and agent["agent_contract"] == "ontokin.agent/0.1" and agent["implementation"] == implementation
            and agent["manifest_sha256"] == file_identity(fixture_path)
            and agent["fixture_identity"] == content_identity(files), "A01--A10 evidence is stale or unexecuted.")
    cases = {case["id"]: case for case in agent["cases"]}
    require(len(cases) == len(agent["cases"]) == 10 and set(cases) == set(CASE_TESTS), "A01--A10 are not all present.")
    for name, method in CASE_TESTS.items():
        actual = cases[name]
        require(actual["passed"] is True and not actual["failures"] and actual["test_method"] == method and actual["operations"],
                "An inherited Agent case lacks its actual successful protocol observations.")
    require(agent["summary"] == {"total": 10, "passed": 10, "failed": 0}, "The A01--A10 summary changed.")
    return {"core_cases": len(observed), "agent_cases": 10}


def slerp_xyzw(left, right, fraction):
    # glTF rotation values encode unit quaternions in binary32. Normalize both
    # endpoints before measuring their angle; raw dot products include their
    # independent quantization errors, including at an endpoint fast path.
    left_norm, right_norm = math.hypot(*left), math.hypot(*right)
    require(left_norm > 0 and right_norm > 0, "A decoded rotation has zero norm.")
    left, right = [x / left_norm for x in left], [x / right_norm for x in right]
    dot = sum(a * b for a, b in zip(left, right))
    if dot < 0:
        right, dot = [-x for x in right], -dot
    if dot > 1 - 1e-12:
        result = [a + fraction * (b - a) for a, b in zip(left, right)]
    else:
        angle = math.acos(max(-1., min(1., dot)))
        scale = math.sin(angle)
        result = [(math.sin((1 - fraction) * angle) * a + math.sin(fraction * angle) * b) / scale
                  for a, b in zip(left, right)]
    norm = math.hypot(*result)
    require(norm > 0, "A decoded rotation has zero norm.")
    return [x / norm for x in result]


def binary32(value):
    return struct.unpack("<f", struct.pack("<f", value))[0]


def preflight_native_layout(document, binary, objects):
    """Bound every declared expansion before allocating any accessor values.

    These are the adopted writer's finite limits, checked independently of its
    reader. Repeated declarations count even when they alias the same bytes.
    This corpus also has fixed analytic geometry, so its declared vertex and
    regional triangle counts must match before a geometry decoder is called.
    """
    def index(items, value, label):
        require(type(value) is int and 0 <= value < len(items), "Invalid native " + label + " reference.")
        return items[value]
    def finite_tree(value):
        if isinstance(value, float):
            require(math.isfinite(value), "Native JSON contains a nonfinite exponent.")
        elif isinstance(value, dict):
            for child in value.values():
                finite_tree(child)
        elif isinstance(value, list):
            for child in value:
                finite_tree(child)
    finite_tree(document)
    nodes, accessors, views = document["nodes"], document["accessors"], document["bufferViews"]
    require(len(nodes) == len(objects) and len(document["buffers"]) == 1
            and "uri" not in document["buffers"][0], "Native carriers or embedded buffer count changed.")
    buffer_size = document["buffers"][0]["byteLength"]
    require(type(buffer_size) is int and 0 < buffer_size <= len(binary) <= 64 * 1024 * 1024
            and len(binary) - buffer_size <= 3, "Native embedded buffer size changed.")
    scenes = document["scenes"]
    require(type(document.get("scene")) is int and document["scene"] == 0 and len(scenes) == 1
            and scenes[0]["nodes"] == list(range(len(nodes))), "The selected native scene omits or repeats a world carrier.")
    require(not document.get("extensionsUsed") and not document.get("extensionsRequired")
            and not document.get("skins") and not document.get("textures") and not document.get("images"),
            "The finite native corpus gained an unsupported visual or transform authority.")
    for node in nodes:
        require(not any(key in node for key in ("matrix", "children", "skin", "weights", "extensions"))
                and node.get("scale", [1, 1, 1]) == [1, 1, 1], "A native node has an unmodeled transform authority.")
    for view in views:
        start, size = view.get("byteOffset", 0), view["byteLength"]
        require(type(view.get("buffer")) is int and view["buffer"] == 0
                and type(start) is int and type(size) is int and start >= 0 and start % 4 == 0
                and size > 0 and start + size <= buffer_size, "Native buffer view exceeds the embedded bytes.")
    components = component_bytes = 0
    for accessor in accessors:
        require(not accessor.get("sparse") and not accessor.get("normalized")
                and type(accessor.get("componentType")) is int and accessor["componentType"] in (5123, 5125, 5126)
                and accessor["type"] in ("SCALAR", "VEC3", "VEC4"), "Unsupported native accessor declaration.")
        count = accessor["count"]
        require(type(count) is int and 0 < count <= 250000, "A native accessor exceeds the fixed element budget.")
        view = index(views, accessor["bufferView"], "buffer view")
        width = {"SCALAR": 1, "VEC3": 3, "VEC4": 4}[accessor["type"]]
        size = 2 if accessor["componentType"] == 5123 else 4
        offset, stride = accessor.get("byteOffset", 0), view.get("byteStride", size * width)
        require(type(offset) is int and type(stride) is int and offset >= 0 and offset % size == 0
                and stride >= size * width and stride % size == 0
                and offset + (count - 1) * stride + size * width <= view["byteLength"],
                "A native accessor is misaligned or exceeds its actual view.")
        components += count * width
        component_bytes += count * width * size
        require(components <= 10000 + 7 * 250000 + 12 * 250000 and component_bytes <= 64 * 1024 * 1024,
                "Declared native accessors exceed the aggregate decoded allocation budget.")
    require(len(document["animations"]) == 1, "Native delivery requires exactly one recorded clip.")
    animation = document["animations"][0]
    require(len(animation["samplers"]) == len(animation["channels"]) == 2 * len(nodes),
            "Native animation declarations omit, duplicate or add carrier channels.")
    for sampler in animation["samplers"]:
        incoming = index(accessors, sampler["input"], "animation input")
        outgoing = index(accessors, sampler["output"], "animation output")
        require(incoming["componentType"] == outgoing["componentType"] == 5126 and incoming["type"] == "SCALAR"
                and outgoing["type"] in ("VEC3", "VEC4") and outgoing["count"] == incoming["count"]
                and sampler["interpolation"] == "LINEAR", "Native animation changed its declared typed clock or values.")
        require(2 <= incoming["count"] <= 10000 and incoming["count"] * len(nodes) <= 250000,
                "Native keyframe or aggregate carrier-pose allocation budget is exceeded.")
    for channel in animation["channels"]:
        sampler = index(animation["samplers"], channel["sampler"], "animation sampler")
        index(nodes, channel["target"]["node"], "animation node")
        require(channel["target"]["path"] in ("translation", "rotation")
                and accessors[sampler["output"]]["type"] == {"translation": "VEC3", "rotation": "VEC4"}[channel["target"]["path"]],
                "An animation channel targets an unsupported value type.")
    vertices = indices = 0
    for node in nodes:
        shape = objects[node["extras"]["ontokin"]["path"]]
        if "sections" not in shape:
            require("mesh" not in node, "An empty source carrier gained native geometry.")
            continue
        mesh = index(document["meshes"], node["mesh"], "mesh")
        triangles = surface._analytic_triangles(shape)
        regions = Counter(triangle[0] for triangle in triangles)
        require(len(mesh["primitives"]) == len(regions), "Native geometry changed its fixed regional count.")
        for primitive in mesh["primitives"]:
            require(set(primitive["attributes"]) == {"POSITION", "NORMAL"} and primitive.get("mode", 4) == 4
                    and not primitive.get("targets") and not primitive.get("extensions"), "Native mesh gained unsupported vertex behavior.")
            region = primitive["extras"]["ontokin"]["region_key"]
            require(region in regions, "Native primitive declares an unauthored material region.")
            for prop in ("POSITION", "NORMAL"):
                value = index(accessors, primitive["attributes"][prop], prop)
                require(value["componentType"] == 5126 and value["type"] == "VEC3"
                        and value["count"] == 3 * len(triangles), "Native vertex declarations exceed their fixed source geometry.")
            value = index(accessors, primitive["indices"], "triangle indices")
            require(value["componentType"] in (5123, 5125) and value["type"] == "SCALAR"
                    and value["count"] == 3 * regions[region], "Native index declarations exceed their fixed regional geometry.")
            index(document["materials"], primitive["material"], "material")
            indices += value["count"]
        vertices += 3 * len(triangles)
        require(vertices <= 250000 and indices <= 6 * 250000, "Native aggregate geometry allocation exceeds its fixed budget.")
    return {"declared_components": components, "declared_component_bytes": component_bytes,
            "source_vertices": vertices, "source_triangle_indices": indices}


class NativeSourceOracle:
    """Full physical reference observations from literal source and scalars.

    This checks held-out programs as well as adopted P cases. It never calls a
    compiler, evaluator, exporter, or destination decoder to predict a state.
    """
    def __init__(self, name, bundle, oracle):
        self.name, self.bundle, self.spec = name, bundle, oracle["specification"]
        self.book = SourceCorpus().literal_book()
        if name not in self.book.records:
            spans = [{"start_byte": len(bundle.entry.text[:match.start()].encode()),
                      "end_byte": len(bundle.entry.text[:match.end()].encode()), "text": match.group()}
                     for match in re.finditer(r"\bforce [^;]+;", bundle.entry.text)]
            self.book.cases[name] = {"force_statements": spans}
            self.book.bundles[name] = bundle
            self.book.records[name] = self.book.source_records(name)
        source_forces = [{"key": r["force_key"], "target": r["target_path"],
            "start_seconds": clock(r["activation_time_seconds"]), "duration_seconds": clock(r["duration_seconds"]),
            "end_seconds": clock(r["completion_time_seconds"]), "vector_n": r["force_world_n"],
            "sequence_index": r["sequence_index"]} for r in self.book.records[name].values()]
        require(source_forces == self.spec["forces"], "The retained source force operands differ from the independent scalar specification.")
        self.impulse_locations = []
        parsed = []
        number = r"([-\d.eE+]+)"
        pattern = (r"impulse (.+?) using vector\(world, " + number + r"\[N\*s\], " + number
                   + r"\[N\*s\], " + number + r"\[N\*s\]\) at point\((.+?)\.frame, " + number
                   + r"\[m\], " + number + r"\[m\], " + number + r"\[m\]\);")
        for block in re.finditer(r"\bat\s+([-\deE+.]+)\[s\]\s+sequence\s*{([^{}]*)}", bundle.entry.text):
            for sequence, part in enumerate(re.finditer(r"[^;]+;", block[2])):
                statement = part.group().strip()
                if not statement.startswith("impulse "):
                    continue
                match = re.fullmatch(pattern, statement)
                require(match is not None and match[1] == match[5], "The bounded source impulse syntax or self frame changed.")
                offset = block.start(2) + part.start() + len(part.group()) - len(part.group().lstrip())
                start = len(bundle.entry.text[:offset].encode())
                self.impulse_locations.append({"source_id": "entry", "source_revision": bundle.entry.revision,
                                                "start_byte": start, "end_byte": start + len(statement.encode())})
                parsed.append({"target": match[1], "time_seconds": clock(Fraction.from_float(float(block[1]))),
                               "vector_n_s": [float(match[i]) for i in (2, 3, 4)],
                               "point_self_m": [float(match[i]) for i in (6, 7, 8)], "sequence_index": sequence})
        require(parsed == self.spec["impulses"], "Source impulse operands or authored byte locations differ from the scalar specification.")

    @staticmethod
    def reached(event, seconds, side):
        return rational(event) < seconds or (rational(event) == seconds and side == "after")

    def kinematics(self, shape, seconds, side):
        motion, target, t = shape["motion"], shape["path"], float(seconds)
        moving_constraint = (seconds > 0 or side == "after") and (seconds < 1 or (seconds == 1 and side == "before"))
        if motion["kind"] == "fixed":
            return [0., 0., 0.], [0., 0., 0.]
        if motion["kind"] == "release_carrier":
            return ([1., 0., 0.], [0., 0., 2.]) if moving_constraint else ([0., 0., 0.], [0., 0., 0.])
        if motion.get("release_seconds") is not None:
            if not self.reached(motion["release_seconds"], seconds, side):
                angle = -2 + 2 * t
                return ([1 - math.sin(angle), math.cos(angle), 0.], [0., 0., 2.]) if moving_constraint else ([0., 0., 0.], [0., 0., 0.])
            velocity, omega = [1., 1. - 10. * (t - 1.), 0.], [0., 0., 2.]
        else:
            velocity = [float(Fraction(v) + Fraction(g) * seconds)
                        for v, g in zip(motion["velocity_m_per_s"], motion["gravity_m_per_s2"])]
            omega = [0., 0., 0.]
        for item in motion["forces"]:
            if item["target"] != target:
                continue
            elapsed = min(max(Fraction(0), seconds - rational(item["start_seconds"])), rational(item["duration_seconds"]))
            for axis in range(3):
                velocity[axis] += float(Fraction(item["vector_n"][axis]) * elapsed / Fraction(motion["mass_kg"]))
        for item in motion["impulses"]:
            if item["target"] != target or not self.reached(item["time_seconds"], seconds, side):
                continue
            for axis in range(3):
                velocity[axis] += item["vector_n_s"][axis] / motion["mass_kg"]
            x, y, z = item["point_self_m"]
            jx, jy, jz = item["vector_n_s"]
            inertia = .4 * motion["mass_kg"] * motion["radius_m"] ** 2
            for axis, torque in enumerate((y * jz - z * jy, z * jx - x * jz, x * jy - y * jx)):
                omega[axis] += torque / inertia
        return velocity, omega

    def acceleration(self, shape, seconds, side):
        motion = shape["motion"]
        active = [item for item in motion["forces"] if item["target"] == shape["path"]
                  and self.reached(item["start_seconds"], seconds, side)
                  and not self.reached(item["end_seconds"], seconds, side)]
        total = [float(sum((Fraction(item["vector_n"][i]) for item in active), Fraction())) for i in range(3)]
        return [float(Fraction(g) + Fraction(f) / Fraction(motion["mass_kg"]))
                for g, f in zip(motion["gravity_m_per_s2"], total)]

    def authority(self, shape, seconds, side):
        motion = shape["motion"]
        if motion["kind"] in ("fixed", "release_carrier"):
            active = (motion["kind"] == "release_carrier" and self.reached(0, seconds, side)
                      and not self.reached(1, seconds, side))
            return {"kind": "prescribed", "orientation_action": "turn" if active else None,
                    "translation_action": "carry" if active else None}
        since = rational(motion.get("release_seconds", "0"))
        if motion.get("release_seconds") is not None and not self.reached(since, seconds, side):
            return {"kind": "joint", "relation": "hold"}
        anchor = since
        boundaries = {rational(item[key]) for item in motion["forces"] if item["target"] == shape["path"]
                      for key in ("start_seconds", "end_seconds")}
        for boundary in sorted(boundaries):
            if self.reached(boundary, seconds, side) and boundary >= since:
                if self.acceleration(shape, boundary, "before") != self.acceleration(shape, boundary, "after"):
                    anchor = boundary
        for item in motion["impulses"]:
            if item["target"] == shape["path"] and self.reached(item["time_seconds"], seconds, side) and any(item["vector_n_s"]):
                anchor = max(anchor, rational(item["time_seconds"]))
        return {"kind": "free_sphere", "since_seconds": clock(since), "trajectory_anchor_seconds": clock(anchor)}

    def check(self, target, shape, obj, seconds, side):
        from tools.force_oracles import expected_pose
        require(set(obj) == {"element_id", "position_m", "orientation_wxyz", "velocity_m_per_s",
                "angular_velocity_rad_per_s", "own_mass_kg", "pose_authority", "forces", "impulses"}
                and obj["element_id"] == shape["element_id"], "A native source observation lost its complete carrier identity/state.")
        authority = self.authority(shape, seconds, side)
        require(obj["pose_authority"] == authority, "The retained source changed its actual pose authority, dynamic origin or anchor.")
        require(set(obj["forces"]) == {"active", "started_count", "completed_count", "last_change_time_seconds",
                "last_changes", "net_force_world_n", "acceleration_world_m_per_s2"}, "A source force projection is incomplete or extended.")
        expanded = {**obj, "motion": "dynamic" if authority["kind"] == "free_sphere" else "prescribed"}
        self.book.check_projection(self.name, target, expanded, seconds, side)
        velocity, omega = self.kinematics(shape, seconds, side)
        close_vector(obj["velocity_m_per_s"], velocity, "independent source velocity")
        close_vector(obj["angular_velocity_rad_per_s"], omega, "independent source angular velocity")
        applied = [(i, item) for i, item in enumerate(self.spec["impulses"]) if item["target"] == target
                   and self.reached(item["time_seconds"], seconds, side)]
        latest = max((rational(item["time_seconds"]) for _, item in applied), default=None)
        expected_records = []
        for i, item in applied:
            if rational(item["time_seconds"]) != latest:
                continue
            time_value = rational(item["time_seconds"])
            position, rotation = expected_pose(shape, time_value)
            before_v, before_w = self.kinematics(shape, time_value, "before")
            after_v, after_w = self.kinematics(shape, time_value, "after")
            # This independently specified finite corpus has a single impulse
            # per carrier, applied at identity orientation. Keep that asserted
            # precondition visible instead of inventing a general solver here.
            orientation(rotation, [1., 0., 0., 0.])
            x, y, z = item["point_self_m"]
            jx, jy, jz = item["vector_n_s"]
            expected_records.append({"target_path": target, "target_element_id": shape["element_id"],
                "source_location": self.impulse_locations[i], "sequence_index": item["sequence_index"],
                "impulse_world_n_s": item["vector_n_s"], "application_point_self_m": item["point_self_m"],
                "application_point_world_m": [a + b for a, b in zip(position, item["point_self_m"])],
                "lever_arm_world_m": item["point_self_m"], "angular_impulse_world_n_m_s": [y * jz - z * jy, z * jx - x * jz, x * jy - y * jx],
                "linear_velocity_before_world_m_per_s": before_v, "linear_velocity_after_world_m_per_s": after_v,
                "angular_velocity_before_world_rad_per_s": before_w, "angular_velocity_after_world_rad_per_s": after_w})
        actual = obj["impulses"]
        require(set(actual) == {"applied_count", "last_application_time_seconds", "last_applications"}
                and type(actual["applied_count"]) is int and actual["applied_count"] == len(applied)
                and actual["last_application_time_seconds"] == (None if latest is None else clock(latest))
                and len(actual["last_applications"]) == len(expected_records), "The complete source impulse history changed.")
        for observed, wanted in zip(actual["last_applications"], expected_records):
            require(set(observed) == set(wanted), "A source impulse application record is incomplete or extended.")
            for key, value in wanted.items():
                if key in {"target_path", "target_element_id", "source_location", "sequence_index"}:
                    require(observed[key] == value, "A source impulse lost its authored identity or byte location.")
                else:
                    close_vector(observed[key], value, "independent impulse " + key)


def check_raw_source_units(bundle, paths):
    expected = {"source_" + str(index): unit for index, unit in enumerate(bundle.units)}
    actual = {role: path for role, path in paths.items() if role.startswith("source_")}
    require(set(actual) == set(expected), "A native artifact omitted or duplicated a raw source-unit role.")
    for role, unit in expected.items():
        require(actual[role].name == unit.filename and actual[role].read_bytes() == unit.raw,
                "A native source filename or role identifies different authored bytes.")


class NativeArtifact:
    """Independent retained-byte decoder for the finite flat world-pose profile."""
    def __init__(self, directory, record, implementation):
        from .bundle import load_bundle
        from tools.force_oracles import oracle_for, sample_requests, expected_pose, boundary_times
        from tools.build_force_demo import fixture_bundle
        self.directory, self.record = Path(directory), record
        self.name = record["fixture"]
        paths = {}
        for role, item in record["provenance"].items():
            paths[role] = identified({"path": item["file"], "sha256": as_sha(item["sha256"]),
                                      "byte_length": item["byte_length"]}, directory)
        require({"bundle", "manifest", "glb", "export", "reference", "oracle"} <= set(paths),
                "A native artifact omits source, binary, report or independent oracle provenance.")
        self.bundle = load_bundle(json_file(paths["bundle"]))
        require(self.bundle.program_revision == record["program_revision"]
                and self.bundle.manifest() == json_file(paths["manifest"]), "Native source revision/manifest changed.")
        wanted_bundle = fixture_bundle(self.name)
        require(self.bundle.program_revision == wanted_bundle.program_revision and self.bundle.manifest() == wanted_bundle.manifest(),
                "Native source differs from its adopted or identified held-out program.")
        check_raw_source_units(self.bundle, paths)
        self.oracle = oracle_for(self.name)
        self.oracle["program_revision"] = self.bundle.program_revision
        require(json_file(paths["oracle"]) == self.oracle, "A native scalar oracle or adopted erratum was changed.")
        self.reference, self.export = json_file(paths["reference"]), json_file(paths["export"])
        self.sha = file_identity(paths["glb"])
        require(self.sha == as_sha(record["artifact_sha256"]) and record["status"] == "passed"
                and as_sha(record["exporter_source_code_sha256"]) == implementation["source_code_sha256"]
                and record["source_reference_implementation"] == implementation, "A native artifact belongs to another execution or source.")
        require(self.export["schema_version"] == "ontokin.glb-report/0.5" and self.export["target_contract"] == "ontokin.glb/0.5"
                and self.export["program_revision"] == self.bundle.program_revision and self.export["artifact"]["sha256"] == self.sha
                and self.export["validation"]["status"] == "passed"
                and as_sha(self.export["source_code_sha256"]) == implementation["source_code_sha256"], "The GLB export report is stale or failed.")
        self.tolerances = self.export["tolerances"]
        for key, maximum in (("position_m", .001), ("rotation_rad", .001), ("time_seconds", .000001)):
            require(type(self.tolerances[key]) in (int, float) and 0 < self.tolerances[key] <= maximum,
                    "Native delivery changed its adopted maximum tolerance.")
        require(self.reference["schema_version"] == "ontokin.force-native-reference/0.1"
                and self.reference["program_revision"] == self.bundle.program_revision and self.reference["source_manifest"] == self.bundle.manifest()
                and self.reference["artifact_sha256"] == self.sha and self.reference["implementation"] == implementation
                and self.reference["tolerances"] == self.tolerances, "The actual source reference is disconnected from this GLB.")
        self.document, self.binary = surface._glb(paths["glb"])
        self.metadata = self.document["extras"]["ontokin"]
        require(self.metadata["target_contract"] == "ontokin.glb/0.5" and self.metadata["profile"] == "force-0.1"
                and self.metadata["program"]["revision"] == self.bundle.program_revision
                and self.metadata["program"]["manifest"] == self.bundle.manifest()
                and self.metadata["transform_policy"] == "all_nodes_are_roots_with_baked_world_poses"
                and self.metadata["coordinates"] == {"handedness": "right", "up": "+Y", "length_unit": "m", "time_unit": "s"},
                "Actual GLB metadata changed contract, source or coordinate/motion meaning.")
        profile = self.metadata["force_profile"]
        require(profile["name"] == "force-0.1" and profile["source_impulses"] == "instantaneous_world_momentum_at_target_self_point"
                and profile["continuous_external_forces"] == "canonical_active_source_force_sum_plus_uniform_gravity"
                and profile["continuous_external_torques"] == "absent" and profile["contacts"] == "disabled"
                and profile["destination_behavior"] == "recorded_rigid_animation_without_live_force_or_impulse_execution",
                "Native metadata changed force, impulse, contact or recorded/live meaning.")
        self.objects = {shape["path"]: shape for shape in self.oracle["shapes"] + self.oracle["empty_objects"]}
        self.allocation = preflight_native_layout(self.document, self.binary, self.objects)
        self.nodes = {node["extras"]["ontokin"]["path"]: (index, node) for index, node in enumerate(self.document["nodes"])}
        require(len(self.nodes) == len(self.document["nodes"]) == len(self.objects) and set(self.nodes) == set(self.objects),
                "Native carriers omit or duplicate a source object.")
        require(all(not node.get("children") and node.get("scale", [1, 1, 1]) == [1, 1, 1] for _, node in self.nodes.values()),
                "Recorded world poses gained a second hierarchy or scale authority.")
        geometry = {row["path"]: row for row in record["geometry"]}
        require(len(geometry) == len(record["geometry"]) and set(geometry) == {s["path"] for s in self.oracle["shapes"]},
                "A source-authored shape is absent from the native geometry records.")
        for shape in self.oracle["shapes"]:
            surface._verify_geometry(self.document, self.binary, shape, geometry[shape["path"]], self.bundle.program_revision, self.bundle)
            physical = self.nodes[shape["path"]][1]["extras"]["ontokin"]["physical"]
            require(physical["mass"] == shape["body_mass_kg"] and physical["radius"] == shape["body_radius_m"],
                    "Visual geometry changed the independently authored physical body.")
        require(len(self.document["animations"]) == 1, "Native playback needs one identified recorded clip.")
        animation = self.document["animations"][0]
        require(animation["samplers"], "Native playback omitted its actual animation samplers.")
        self.times = surface._accessor(self.document, self.binary, animation["samplers"][0]["input"])
        self.end = float(self.oracle["end_seconds"])
        require(self.times[0] == 0 and self.times[-1] == binary32(self.end)
                and all(b > a for a, b in zip(self.times, self.times[1:])), "Decoded native clock changed or is not strictly increasing.")
        self.channels = {}
        for channel in animation["channels"]:
            target, sampler = channel["target"], animation["samplers"][channel["sampler"]]
            key = (target["node"], target["path"])
            require(key not in self.channels and target["path"] in {"translation", "rotation"}
                    and sampler["interpolation"] == "LINEAR"
                    and surface._accessor(self.document, self.binary, sampler["input"]) == self.times,
                    "A native transform channel is duplicated, unsupported or has another clock.")
            values = surface._accessor(self.document, self.binary, sampler["output"])
            require(len(values) == len(self.times), "A native channel omits a decoded clock key.")
            self.channels[key] = values
            if target["path"] == "rotation":
                require(all(abs(math.hypot(*q) - 1) <= 1e-5 for q in values), "A binary32 rotation is not a unit quaternion.")
            require(self.document["nodes"][target["node"]].get(target["path"]) == values[0],
                    "A native carrier's initial transform disagrees with its recorded first key.")
        require(set(self.channels) == {(i, prop) for i, _ in self.nodes.values() for prop in ("translation", "rotation")},
                "Every finite source carrier needs its complete recorded translation and rotation.")
        source_boundaries = boundary_times(self.name)
        encoded = [binary32(float(t)) for t in source_boundaries]
        require(len(encoded) == len(set(encoded)) and all(t in self.times for t in encoded)
                and all(abs(Fraction.from_float(t) - rational(source)) <= Fraction(str(self.tolerances["time_seconds"]))
                        for t, source in zip(encoded, source_boundaries)), "Exact source boundaries collapsed or disappeared from the actual binary clock.")
        samples = self.reference["samples"]
        require([{k: s[k] for k in ("time_seconds", "side")} for s in samples] == sample_requests(self.name),
                "The native reference changed its fixed source request schedule.")
        source_oracle = NativeSourceOracle(self.name, self.bundle, self.oracle)
        for sample in samples:
            require(set(sample["objects"]) == set(self.objects), "A source reference omits an empty or physical carrier.")
            for name, obj in sample["objects"].items():
                position, rotation = expected_pose(self.objects[name], rational(sample["time_seconds"]))
                close_vector(obj["position_m"], position, "independent source reference position")
                orientation(obj["orientation_wxyz"], rotation)
                source_oracle.check(name, self.objects[name], obj, rational(sample["time_seconds"]), sample["side"])
        boundaries = self.metadata["boundary_states"]
        require([rational(row["source_seconds"]) for row in boundaries] == [rational(t) for t in source_boundaries],
                "Native metadata omitted an exact source boundary.")
        for boundary in boundaries:
            matching = [s for s in samples if rational(s["time_seconds"]) == rational(boundary["source_seconds"]) and s["side"] == "after"]
            require(len(matching) == 1, "A native boundary has no actual source after-state.")
            for field, source in (("force_states_after", "forces"), ("impulse_states_after", "impulses"), ("pose_authorities_after", "pose_authority")):
                require(boundary[field] == {name: obj[source] for name, obj in matching[0]["objects"].items()},
                        "Native boundary history changed or dropped a carrier: " + field)
        khronos = record["khronos"]
        require(khronos["version"] == NODE_PINS["gltf-validator"] and khronos["errors"] == khronos["warnings"] == 0
                and all(message.get("severity") not in (0, 1) for message in khronos["messages"]), "The actual Khronos validator reported errors or warnings.")
        three = record["three_js"]
        require(str(three["version"]) == "180" and three["held_out_schedule"] == {
            "prime_denominator": 257, "includes_all_decoded_keys": True, "interior_fractions": [.25, .5, .75]},
            "The pinned Three.js version or independent dense schedule changed.")
        require([{k: s[k] for k in ("time_seconds", "side")} for s in three["samples"]] == sample_requests(self.name),
                "Three.js omitted a fixed source sample/time side.")
        probes = set(self.times)
        for left, right in zip(self.times, self.times[1:]):
            for fraction in (.25, .5, .75):
                probes.add(left + fraction * (right - left))
        probes.update(self.end * i / 257 for i in range(258))
        require([s["time_seconds"] for s in three["dense_samples"]] == sorted(probes),
                "Independent dense evidence omits actual keys, interval probes or held-out times.")
        for sample in three["samples"] + three["dense_samples"]:
            self.check_poses(sample["objects"], rational(sample["time_seconds"]))
        require(three["world_pose_comparisons"] == len(three["samples"]) * len(self.objects)
                and three["dense_pose_comparisons"] == len(three["dense_samples"]) * len(self.objects),
                "Native comparison counts contradict their actual decoded observations.")
        require(record["adversarial_checks"] and all(row["status"] == "rejected" for row in record["adversarial_checks"]),
                "The native verifier did not execute its actual adversarial checks.")

    def pose(self, name, seconds):
        index, _ = self.nodes[name]
        time_value = max(self.times[0], min(self.times[-1], float(seconds)))
        upper = min(len(self.times) - 1, max(1, bisect_right(self.times, time_value)))
        lower = upper - 1
        fraction = (time_value - self.times[lower]) / (self.times[upper] - self.times[lower])
        positions, rotations = self.channels[(index, "translation")], self.channels[(index, "rotation")]
        return {"position_m": [a + fraction * (b - a) for a, b in zip(positions[lower], positions[upper])],
                "orientation_xyzw": slerp_xyzw(rotations[lower], rotations[upper], fraction)}

    def check_poses(self, observed, seconds):
        from tools.force_oracles import expected_pose
        require(set(observed) == set(self.objects), "A decoded observation omitted an authored carrier.")
        for name, value in observed.items():
            binary_pose = self.pose(name, seconds)
            position, rotation = expected_pose(self.objects[name], seconds)
            expected = {"position_m": position, "orientation_wxyz": rotation}
            p_error, q_error = construction._pose_error(value, expected, xyzw=True)
            require(p_error <= self.tolerances["position_m"] and q_error <= self.tolerances["rotation_rad"],
                    "A retained destination observation violates its source motion tolerance.")
            close_vector(value["position_m"], binary_pose["position_m"], "retained versus independently decoded position")
            binary_p, binary_q = construction._pose_error(binary_pose, expected, xyzw=True)
            require(binary_p <= self.tolerances["position_m"] and binary_q <= self.tolerances["rotation_rad"],
                    "Independently decoded binary motion violates its unchanged source tolerance.")
            _, reader_q = construction._pose_error(value, {"position_m": binary_pose["position_m"],
                "orientation_wxyz": [binary_pose["orientation_xyzw"][3], *binary_pose["orientation_xyzw"][:3]]}, xyzw=True)
            # Three.js decomposes its binary32-derived world matrix whereas this
            # reader normalizes decoded quaternions directly. Eight binary32
            # half-ULPs bound that separate numerical comparison (observed
            # preflight maximum 7.40e-8 rad); both poses must still independently
            # meet the original source rotation tolerance above.
            require(reader_q <= min(8 * 2 ** -24, 2 * self.tolerances["rotation_rad"]),
                    "Retained and independently decoded rotations disagree beyond binary32 reader roundoff.")
            metrics = value.get("independent", value)
            if "position_error_m" in metrics:
                construction._same_metric(metrics["position_error_m"], p_error, "Retained source position error")
                construction._same_metric(metrics["rotation_error_rad"], q_error, "Retained source rotation error")
        return len(observed)


def check_visual_output(step_id, output):
    """Reject raw output contradictions even when a wrapper claims success."""
    if isinstance(output.get("summary"), dict):
        require(not output["summary"].get("failed", 0), "A retained visual process output reports failed cases.")
    require(output.get("status") not in {"failed", "running", "interrupted", "unavailable"},
            "A retained process report contradicts its passed execution step.")
    if not (step_id.endswith("-format") or step_id.endswith("-browser")):
        return
    if output.get("schema_version") == "ontokin.external-validation/0.1":
        require(isinstance(output.get("files"), list) and output["files"], "A glTF verifier retained no actual artifact results.")
        for row in output["files"]:
            require(row["validator"]["version"] == NODE_PINS["gltf-validator"]
                    and row["validator"]["errors"] == row["validator"]["warnings"] == 0
                    and str(row["three_js"]["revision"]) == "180" and row["three_js"]["loaded"] is True,
                    "A retained inherited GLB failed its pinned actual validator or decoder.")
            comparison = row["three_js"]["comparison"]
            require(comparison["status"] == "passed" and not comparison["failures"]
                    and comparison["sample_count"] > 0 and comparison["object_pose_comparisons"] > 0,
                    "An inherited recorded-motion comparison failed or retained no observations.")
    else:
        require(output.get("status") == "passed", "A native format/browser report did not actually pass.")
    def inspect(value):
        if isinstance(value, dict):
            require(value.get("status") != "failed", "A retained visual sub-result reports a failure.")
            for key, child in value.items():
                if key in {"errors", "warnings", "page_errors", "console_errors", "asset_errors", "network_requests", "failed_requests"}:
                    require(child in ([], 0), "A retained destination/browser report contains errors, warnings or network requests.")
                inspect(child)
        elif isinstance(value, list):
            for child in value:
                inspect(child)
    inspect(output)


class Auditor:
    def __init__(self, evidence, *, root=None):
        self.path = None if evidence is None else Path(evidence).resolve()
        self.root = Path(root).resolve() if root is not None else self.path.parent if self.path else ROOT
        self.mapping = load_manifest()
        self.current = source_identity()
        self.document = None if self.path is None else json_file(self.path)
        self.roles = {} if self.document is None else self.document.get("roles", {})
        self.context = {}
        self.envelopes = {}

    def file(self, record):
        return identified(record, self.root)

    def role(self, name):
        if name not in self.roles:
            raise MissingEvidence("No current " + name + " role was supplied.")
        require(isinstance(self.roles[name], dict), "A role must be an identified evidence record: " + name)
        return self.roles[name]

    def execution(self, record, role, *, python=None):
        path = self.file(record)
        key = (str(path), role, python)
        if key not in self.envelopes:
            envelope = json_file(path)
            report_path = check_execution(envelope, path.parent, role, self.current, python=python)
            self.envelopes[key] = (json_file(report_path), envelope, report_path)
        return self.envelopes[key]

    def closure(self):
        if self.document is None:
            raise MissingEvidence("No force release evidence manifest was supplied.")
        require(self.document.get("schema_version") == EVIDENCE_SCHEMA
                and self.document.get("implementation") == self.current["implementation"],
                "The release evidence belongs to another schema or implementation.")
        if self.document.get("input_inventory_sha256") != self.current["input_inventory_sha256"]:
            raise MissingEvidence("Stale release evidence: the current eligible input inventory differs.")
        records = self.document.get("files")
        require(isinstance(records, list), "A release requires an explicit retained artifact inventory.")
        if not records:
            raise MissingEvidence("No retained release artifacts have been supplied.")
        names = [record["path"] for record in records]
        require(len(names) == len(set(names)), "A retained artifact path is duplicated.")
        for record in records:
            self.file(record)
        # The manifest and this auditor's root-level output are bookkeeping.
        # Everything else in the confined final evidence root is an artifact.
        ignored = {"audit.json"}
        if self.path:
            ignored.add(self.path.relative_to(self.root).as_posix())
        found = set()
        for path in self.root.rglob("*"):
            name = path.relative_to(self.root).as_posix()
            require(not path.is_symlink(), "The retained evidence root contains a symlink: " + name)
            if path.is_file() and name not in ignored:
                require(not re.search(r"(?:\.sqlite(?:3)?|\.db)(?:-wal|-shm)?$", name),
                        "Mutable databases and WAL/SHM files are not release evidence.")
                found.add(name)
        require(found == set(names), "The final artifact inventory omits files or includes absent files.")
        require(self.current["committed_inputs_match"] is True, "Current eligible inputs do not match their captured Git tree.")
        return {"files": len(records), "bytes": sum(r["byte_length"] for r in records),
                "inventory_sha256": digest(canonical(records)), "current_git": self.current["git"]}

    def source(self):
        report, envelope, _ = self.execution(self.role("source")["execution"], "source")
        require(all(report[key] == envelope[key] for key in ("source_before", "source_after")),
                "The source report's inner input identities disagree with its measured execution.")
        result = check_source_report(report)
        self.context["source"] = report
        return result

    def mapped_tests(self):
        names = sorted({name for case in self.mapping["cases"] for name in case["required_tests"]})
        report, envelope, _ = self.execution(self.role("mapped-tests")["execution"], "mapped-tests")
        require(report.get("schema_version") == "ontokin.force-unittest-execution/0.1", "Unsupported mapped-test report schema.")
        require(all(report[key] == envelope[key] for key in ("source_before", "source_after"))
                and report["source_stable_during_run"] is True, "Mapped tests changed their input identity during execution.")
        result = check_tests(report, names, current=self.current)
        self.context["mapped-tests"] = report
        return result

    def compatibility(self):
        record = self.role("compatibility")
        require(set(record) == set(PYTHONS), "The local matrix must identify exactly CPython 3.11, 3.12 and 3.13.")
        names = surface.discover_test_ids()
        require(set(self.mapping["regression_required_test_ids"]) <= set(names), "A published regression method was removed.")
        require(set(self.mapping["additional_branch_cohort"]["test_ids"]) <= set(names),
                "A separately identified destination oracle regression method was removed.")
        results, unique = {}, set()
        for version in PYTHONS:
            report, envelope, path = self.execution(record[version], "regression", python=version)
            require(report["schema_version"] == "ontokin.unittest-execution/0.1"
                    and report["evidence_files"] == impulse.evidence_inventory()
                    and report["evidence_inventory_sha256"] == surface.inventory_identity(impulse.evidence_inventory())
                    and report["evidence_stable_during_run"] is True,
                    "A compatibility run used a different inherited input inventory.")
            results[version] = {**check_tests(report, names, current=self.current), "environment": envelope["environment"],
                                "report_sha256": file_identity(path)}
            unique.add((envelope["environment"]["python"], envelope["environment"]["python_executable"],
                        envelope["started_at_utc"], str(path)))
        require(len(unique) == 3, "Compatibility evidence must identify three actual interpreter executions.")
        self.context["compatibility"] = results
        return {"interpreters": results, "current_test_ids": names,
                "published_baseline_commit": self.mapping["regression_baseline_commit"],
                "published_baseline_tests": len(self.mapping["regression_required_test_ids"])}

    def force_agent(self, *, delivery=False):
        name = "force-delivery" if delivery else "force-agent"
        record = self.role(name)
        workflow_path = self.file(record["workflow"])
        built, _, build_path = self.execution(record["build_execution"], name + "-build")
        report, _, report_path = self.execution(record["execution"], name)
        require(file_identity(workflow_path) == file_identity(build_path), "The audited Agent workflow differs from the builder's actual new output.")
        module = importlib.import_module("tools.verify_force_delivery_workflow" if delivery else "tools.verify_force_agent_workflow")
        fresh = module.verify(workflow_path.parent)
        require(report.get("status") == fresh.get("status") == "passed", "The independently re-audited Agent workflow failed.")
        # A fresh read has a different audit timestamp; all substantive retained
        # fields must agree, including exact fixture/schema/verifier identities.
        for key, value in fresh.items():
            if key not in {"checked_at_utc", "generated_at_utc"}:
                require(report.get(key) == value, "The retained Agent audit differs from independent recovery: " + key)
        require(as_sha(report.get("workflow_sha256")) == file_identity(workflow_path), "The Agent audit identifies another workflow.")
        self.context[name] = {"workflow": workflow_path, "report": report_path, "audit": report, "built": built}
        return {"workflow_sha256": file_identity(workflow_path), "audit_sha256": file_identity(report_path),
                "independently_reaudited": True, "schema_version": report["schema_version"]}

    def legacy(self):
        record = self.role("legacy")
        implementation = self.current["implementation"]
        reports = {}
        for name in ("core", "agent", "construction", "surface", "impulse"):
            reports[name], _, _ = self.execution(record["executions"][name], name)
        results = check_core_agent(reports["core"], reports["agent"], implementation)
        cm = construction.load_manifest()
        cr = reports["construction"]
        results["construction"] = check_legacy_cases(cr, "ontokin.construction-conformance/0.1", cm,
                                                      construction._evidence_inventory(construction.DEFAULT_FIXTURES), implementation)
        require(cr["manifest"]["sha256"] == file_identity(construction.DEFAULT_FIXTURES / "validation-cases.json")
                and cr["settings"] == cm["settings"], "The construction run changed its adopted settings or mapping.")
        from .bundle import load_bundle
        bundle = load_bundle(json_file(construction.DEFAULT_FIXTURES / "01-keyed-rack/program.bundle.json"))
        c_external = self.file(record["construction_external"])
        checked = construction.verify_external_evidence(c_external, implementation=implementation,
                                                         expected_program=bundle, root=self.root)
        require(checked["status"] == "passed", "The current C20 raw workflow/destination/review is incomplete: " + "; ".join(checked["issues"]))
        results["construction"]["current_external"] = checked
        sm = surface.load_manifest()
        sr = reports["surface"]
        results["surface"] = check_legacy_cases(sr, "ontokin.surface-conformance/0.1", sm,
                                                surface.evidence_inventory(), implementation)
        require(sr["manifest"]["sha256"] == surface.MAPPING_SHA256, "The surface mapping identity changed.")
        surface_path = self.file(record["surface_external"])
        se = json_file(surface_path)
        require(se["schema_version"] == "ontokin.surface-release-evidence/0.1" and se["implementation"] == implementation,
                "The current surface raw evidence belongs to a different implementation.")
        surface_context = {}
        results["surface"]["workflow"] = surface._verify_workflow(se["workflow"], self.root, implementation, sm, surface_context)
        results["surface"]["destination"] = surface._verify_destination(se["native"], self.root, implementation, sm, surface_context)
        results["surface"]["browser"] = surface._verify_browser(se["native"], self.root, implementation, sm, surface_context)
        contract = impulse.load_manifest()
        im, ir = contract["mapping"], reports["impulse"]
        results["impulse"] = check_legacy_cases(ir, "ontokin.impulse-conformance/0.1", im,
                                                impulse.evidence_inventory(), implementation)
        require(ir["acceptance_sha256"] == impulse.ACCEPTANCE_SHA256 and ir["mapping_sha256"] == impulse.MAPPING_SHA256,
                "The impulse run changed its adopted acceptance or mapping.")
        source = ir["source_execution"]
        require(source["required_ids"] == list(impulse.SOURCE_IDS)
                and [r["id"] for r in source["cases"]] == list(impulse.SOURCE_IDS), "The inherited impulse source corpus is incomplete.")
        for actual, wanted in zip(source["cases"], contract["acceptance"]["source_cases"]):
            require(actual["executed"] is True and actual["status"] == "passed" and not actual["issues"]
                    and actual["program_revision"] == wanted["program_revision"] and actual["checks"],
                    "An inherited impulse source case did not actually pass.")
            if wanted["kind"] == "positive":
                require(len(actual["samples"]) == len(wanted["expected"]["samples"]), "An inherited impulse sample was omitted.")
                for sample, expected in zip(actual["samples"], wanted["expected"]["samples"]):
                    impulse.compare_sample(sample, expected, exact_extreme=wanted["id"] == "P12")
            else:
                require(actual["diagnostic"]["code"] == wanted["expected"]["diagnostic_code"], "An inherited impulse rejection changed.")
        impulse_path = self.file(record["impulse_external"])
        ie = json_file(impulse_path)
        require(ie["schema_version"] == "ontokin.impulse-release-evidence/0.1" and ie["implementation"] == implementation,
                "The current impulse raw evidence belongs to a different implementation.")
        impulse_context = {}
        workflow = impulse._verify_workflow(ie["workflow"], self.root, implementation, contract, impulse_context, ir["test_execution"])
        impulse_context["workflow_sha256"] = workflow["workflow_sha256"]
        results["impulse"]["workflow"] = workflow
        results["impulse"]["destination"] = impulse._verify_destination(ie["native"], self.root, implementation, contract, impulse_context)
        results["impulse"]["browser"] = impulse._verify_browser(ie["native"], self.root, implementation, contract, impulse_context)
        # New local compatibility/visual roles satisfy only provider execution.
        # The old CI-shaped inputs are neither fabricated nor overwritten.
        if "compatibility" not in self.context:
            raise MissingEvidence("Inherited provider reconciliation still requires the complete current local matrix.")
        if "legacy-visual" not in self.context:
            raise MissingEvidence("Inherited provider reconciliation still requires the complete current visual execution.")
        results["provider_reconciliation"] = {"contract": "OK-ENG-008", "historical_reports_modified": False,
                                               "replaced_role": "execution_provider", "compatibility": list(PYTHONS),
                                               "non_provider_readers_reaudited": ["C20", "M-workflow", "M-destination", "M-browser",
                                                                                  "I-workflow", "I-destination", "I-browser"]}
        return results

    def legacy_visual(self):
        record = self.role("legacy-visual")
        report, envelope, _ = self.execution(record["execution"], "legacy-visual")
        directory = self.file(record["summary"]).parent
        require(file_identity(self.file(record["summary"])) == envelope["report"]["sha256"],
                "The retained local visual summary differs from its actual process output.")
        require(report["schema_version"] == "ontokin.local-checks/0.1" and report["profile"] == "full"
                and report["status"] == "passed" and report["source_unchanged"] is True
                and report["git_revision_unchanged"] is True and not report["not_executed_steps"]
                and report["remote_checks_executed"] is False, "The complete local visual execution failed or omitted roles.")
        from tools.check_local import build_plan, inventory_records
        captured_workspace = Path(report["steps"][0]["cwd"])
        require(captured_workspace.is_absolute() and captured_workspace.name == "workspace",
                "The visual role lost its actual isolated workspace identity.")
        captured_output = captured_workspace.parent
        require(report["source_root"] == envelope["cwd"], "The complete visual driver ran against a different source checkout.")
        expected = build_plan(captured_workspace, captured_output, True,
                              python=report["environment"]["python_executable"],
                              force_agent="force-agent" in report["selected_roles"])
        require(report["planned_steps"] == [step.id for step in expected]
                and [step["id"] for step in report["steps"]] == [step.id for step in expected],
                "The visual run omitted or added a planned current role.")
        before_path = identified({"path": report["source_inventory"]["path"],
            "sha256": report["source_inventory"]["sha256"], "byte_length": report["source_inventory"]["bytes"]}, directory)
        before = json_file(before_path)
        require(before == inventory_records(before["files"])
                and before == json_file(relative_file(directory, "source-after.json")),
                "The visual driver input inventory changed or was incompletely retained.")
        eligible = [{"path": row["path"], "sha256": row["sha256"], "byte_length": row["bytes"]}
                    for row in before["files"] if eligible_path(row["path"])]
        require(eligible == self.current["inputs"], "The actual visual workspace omitted or changed a current eligible input.")
        for identity in (report["git"], report["workspace_git"], report["git_after"]):
            require(identity["available"] is True
                    and identity["local_head"] == envelope["source_before"]["git"]["commit"]
                    and identity["local_tree"] == envelope["source_before"]["git"]["tree"],
                    "The visual driver or its isolated workspace lost the executed commit/tree.")
        expected_node = next(step.argv[0] for step in expected if step.id == "node-tools")
        observed_node = next(step["argv"][0] for step in report["steps"] if step["id"] == "node-tools")
        node_versions = []
        for step, wanted in zip(report["steps"], expected):
            argv = list(wanted.argv)
            if argv[0] == expected_node:
                argv[0] = observed_node
            require(step["status"] == "passed" and step["returncode"] == 0 and step["requires"] == list(wanted.requires)
                    and type(step["duration_seconds"]) in (int, float) and math.isfinite(step["duration_seconds"])
                    and step["duration_seconds"] >= 0 and step["cwd"] == str(captured_workspace)
                    and step["argv"] == argv,
                    "A required visual execution did not actually pass.")
            require([item["path"] for item in step["reports"]] ==
                    [path.relative_to(captured_output).as_posix() for path in wanted.reports],
                    "A visual execution omitted or substituted a required raw output report.")
            log = relative_file(directory, step["log"])
            require(file_identity(log) == step["log_identity"]["sha256"] and log.stat().st_size == step["log_identity"]["bytes"],
                    "A visual process log changed.")
            for item in step["reports"]:
                path = relative_file(directory, item["path"])
                require(file_identity(path) == item["sha256"] and path.stat().st_size == item["bytes"],
                        "A required visual output report changed.")
                output = json_file(path)
                check_visual_output(step["id"], output)
                if step["id"] == "node-tools":
                    require(output["dependencies"] == NODE_PINS, "The actual visual driver did not use its pinned dependencies.")
                    node_versions.append(output.get("node", output.get("version", "")))
        require(node_versions and all(re.match(r"v?22\.", version) for version in node_versions),
                "The inherited complete visual role did not execute its adopted Node 22 runtime.")
        self.context["legacy-visual"] = report
        return {"executed_steps": len(expected), "node": node_versions, "retained_summary_sha256": file_identity(self.file(record["summary"])),
                "historical_pending_provider_reasons_preserved": report["pending_external_cases"]}

    def native(self, *, agent=False):
        name = "agent-native" if agent else "force-native"
        record = self.role(name)
        report, envelope, report_path = self.execution(record["execution"], name)
        expected_schema = "ontokin.force-delivery-destination-validation/0.1" if agent else "ontokin.force-destination-validation/0.1"
        require(report.get("schema_version") == expected_schema and report.get("status") == "passed"
                and report.get("implementation") == self.current["implementation"], "The native destination role is failed, stale or relabeled.")
        require(envelope["environment"].get("node_packages") == NODE_PINS
                and re.match(r"v?22\.", envelope["environment"].get("node", ""))
                and report["environment"]["node"] == envelope["environment"]["node"]
                and report["environment"]["three"] == NODE_PINS["three"]
                and report["environment"]["khronos_gltf_validator"] == NODE_PINS["gltf-validator"],
                "The native role did not execute the pinned decoder/validator tools.")
        for key, tool in (("verifier_sha256", "tools/verify_force_native.mjs"),
                          ("surface_verifier_sha256", "tools/verify_surface_native.mjs"),
                          ("tooling_lock_sha256", "tools/package-lock.json")):
            require(as_sha(report[key]) == file_identity(ROOT / tool), "Native verification inputs changed: " + key)
        if agent:
            if "force-delivery" not in self.context:
                raise MissingEvidence("Agent native delivery requires the independently audited actual Agent workflow first.")
            source = self.context["force-delivery"]
            workflow_path, workflow = source["workflow"], source["built"]
            require(as_sha(report["agent_audit_sha256"]) == file_identity(source["report"])
                    and report["source_kind"] == "agent_retrieved_artifact"
                    and report["workflow_schema_version"] == "ontokin.force-delivery-workflow/0.1",
                    "Native Agent bytes are not bound to their actual retrieval audit.")
            wanted = AGENT_DESTINATIONS
            require([row["case_id"] for row in workflow["deliveries"]] == list(wanted), "The actual Agent artifact corpus is incomplete.")
            fixtures = [{"fixture": row["case_id"], "directory": str(PurePosixPath(row["files"]["scene.glb"]["path"]).parent),
                         "program_revision": row["program_revision"], "artifact_sha256": row["sha256"]}
                        for row in workflow["deliveries"]]
        else:
            workflow_path = self.file(record["workflow"])
            workflow, _, build_path = self.execution(record["build_execution"], "source-build")
            require(file_identity(workflow_path) == file_identity(build_path)
                    and workflow["schema_version"] == "ontokin.force-destination-workflow/0.1"
                    and workflow["status"] == "built" and workflow["complete_component_corpus"] is True
                    and workflow["git_identity"] == workflow["git_identity_after"]
                    and workflow["builder_sha256"] == file_identity(ROOT / "tools/build_force_demo.py")
                    and workflow["oracle_sha256"] == file_identity(ROOT / "tools/force_oracles.py"),
                    "The native corpus is not the exact new source-builder result.")
            require(report["source_kind"] == "source_export" and report["agent_audit_sha256"] is None
                    and report["workflow_schema_version"] == workflow["schema_version"], "A component report changed its origin.")
            wanted, fixtures = POSITIVE_DESTINATIONS, workflow["fixtures"]
        require(workflow["implementation"] == self.current["implementation"]
                and as_sha(report["workflow_sha256"]) == file_identity(workflow_path)
                and report["fixture_inputs"] == workflow["fixture_inputs"] == self.mapping["fixture_inputs"],
                "Native source input or workflow provenance changed.")
        require([row["fixture"] for row in report["fixtures"]] == list(wanted)
                and [row["fixture"] for row in fixtures] == list(wanted), "The native result omitted or duplicated a mandatory source artifact.")
        artifacts = {}
        for result, source in zip(report["fixtures"], fixtures):
            require(result["program_revision"] == source["program_revision"]
                    and as_sha(result["artifact_sha256"]) == as_sha(source["artifact_sha256"]),
                    "A decoded artifact differs from the builder or retrieved bytes.")
            marker = relative_file(workflow_path.parent, source["directory"] + "/scene.glb")
            artifacts[result["fixture"]] = NativeArtifact(marker.parent, result, self.current["implementation"])
        if not agent:
            failures = ("P18", "P20", "P21-full-horizon", "float32-boundary-collapse", "position-key-budget")
            require([r["fixture"] for r in workflow["delivery_failures"]] == list(failures)
                    and [r["fixture"] for r in report["delivery_failures"]] == list(failures), "Predetermined unsuccessful deliveries were omitted.")
            from tools.build_force_demo import fixture_bundle
            from .bundle import load_bundle
            for source, result in zip(workflow["delivery_failures"], report["delivery_failures"]):
                directory = workflow_path.parent / source["fixture"]
                failure = relative_file(directory, "delivery-failure.json")
                expected_bundle = fixture_bundle(source["fixture"])
                actual_bundle = load_bundle(json_file(relative_file(directory, "program.bundle.json")))
                require(actual_bundle.to_payload() == expected_bundle.to_payload()
                        and json_file(relative_file(directory, "source-manifest.json")) == actual_bundle.manifest(),
                        "An unsuccessful delivery lost its exact authored source bundle and manifest.")
                require(source["source_units"] == [{"file": unit.filename, "source_id": unit.source_id,
                            "source_revision": unit.revision, "byte_length": len(unit.raw)} for unit in actual_bundle.units],
                        "An unsuccessful delivery's retained source inventory changed.")
                for unit in actual_bundle.units:
                    require(relative_file(directory, unit.filename).read_bytes() == unit.raw,
                            "An unsuccessful delivery omitted or changed a raw source unit.")
                require(json_file(failure) == source and source["artifact_written"] is False
                        and source["status"] == "expected_delivery_failure" and source["code"] in {"OKL-E-RESOURCE", "OKL-E-NUMERIC"}
                        and source["program_revision"] == actual_bundle.program_revision
                        and not list(directory.rglob("*.glb")) and result["no_artifact"] is True
                        and result["status"] == "passed" and result["diagnostic_sha256"] == file_identity(failure),
                        "A failed delivery lost its exact source/diagnostic or emitted an artifact.")
                if source["fixture"] in {"float32-boundary-collapse", "position-key-budget"}:
                    code = "OKE-E-TIMES-COLLAPSED" if source["fixture"] == "float32-boundary-collapse" else "OKE-E-KEYFRAME-BUDGET"
                    require(source["details"]["export_code"] == code, "A delivery failure changed its predetermined boundary.")
        else:
            require(report["delivery_failures"] == [], "Agent negative deliveries belong to their audited protocol evidence.")
        baseline, sibling = artifacts["P10"], 'rack.props["second"]'
        for edited in ("P11", "P12", "P13"):
            changed = artifacts[edited]
            require(baseline.bundle.modules == changed.bundle.modules and baseline.bundle.program_revision != changed.bundle.program_revision,
                    "A scoped repair changed a library or failed to create a new revision.")
            by_key = {(r["time_seconds"], r["side"]): r for r in changed.reference["samples"]}
            common = 0
            for source in baseline.reference["samples"]:
                other = by_key.get((source["time_seconds"], source["side"]))
                if other is None:
                    continue
                for field in ("element_id", "position_m", "orientation_wxyz", "velocity_m_per_s", "angular_velocity_rad_per_s", "own_mass_kg"):
                    require(source["objects"][sibling][field] == other["objects"][sibling][field],
                            "A scoped source repair changed an unrelated sibling physical state.")
                common += 1
            require(common >= 20, "Too few actual common sibling source observations were retained.")
            for left, right in zip(baseline.record["geometry"], changed.record["geometry"]):
                require(all(left[key] == right[key] for key in ("path", "positions_sha256", "topology_sha256", "regions")),
                        "A physical repair changed visible source geometry or PBR material regions.")
        require([row["after_fixture"] for row in report["source_repairs"]] == ["P11", "P12", "P13"]
                and all(row["status"] == "passed" for row in report["source_repairs"]), "The native verifier omitted its actual cross-artifact repair checks.")
        self.context[name] = {"artifacts": artifacts, "workflow": workflow_path, "report": report_path, "value": report}
        return {"fixtures": len(artifacts), "fixed_pose_observations": sum(r["three_js"]["world_pose_comparisons"] for r in report["fixtures"]),
                "dense_pose_observations": sum(r["three_js"]["dense_pose_comparisons"] for r in report["fixtures"]),
                "expected_delivery_failures": len(report["delivery_failures"]), "actual_binary_independently_redecoded": True}

    def browser(self, *, agent=False):
        name, native_name = ("agent-browser", "agent-native") if agent else ("force-browser", "force-native")
        if native_name not in self.context:
            raise MissingEvidence("Browser review requires its exact independently validated native corpus first.")
        native = self.context[native_name]
        record = self.role(name)
        report, envelope, report_path = self.execution(record["execution"], name)
        retained_path = self.file(record["report"])
        require(file_identity(retained_path) == file_identity(report_path), "The retained browser output differs from its actual executed report.")
        directory = retained_path.parent
        schema = "ontokin.force-delivery-browser-validation/0.1" if agent else "ontokin.force-browser-validation/0.1"
        require(report["schema_version"] == schema and report["status"] == "passed" and report["target_contract"] == "ontokin.glb/0.5"
                and report["implementation"] == self.current["implementation"] and report["complete_browser_corpus"] is True
                and report["workflow_sha256"] == file_identity(native["workflow"])
                and report["source_kind"] == ("agent_retrieved_artifact" if agent else "source_export")
                and report["agent_audit_sha256"] == native["value"]["agent_audit_sha256"],
                "Browser execution changed its current source, workflow or retrieval identity.")
        for field, filename in (("verifier_sha256", "tools/verify_force_viewer.mjs"),
                                ("native_verifier_sha256", "tools/verify_force_native.mjs"),
                                ("surface_verifier_sha256", "tools/verify_surface_native.mjs"),
                                ("oracle_sha256", "tools/force_oracles.py"), ("tooling_lock_sha256", "tools/package-lock.json")):
            require(report[field] == file_identity(ROOT / filename), "Browser tooling changed: " + field)
        require(report["fixture_inputs"] == self.mapping["fixture_inputs"]
                and report["harness_sha256"] == file_identity(relative_file(directory, report["harness_file"])),
                "Browser source oracle inputs or its actual rendered harness changed.")
        require(envelope["environment"].get("node_packages") == NODE_PINS
                and re.match(r"v?22\.", envelope["environment"].get("node", ""))
                and envelope["environment"]["node"] == report["environment"]["node"]
                and all(report["environment"][name] == NODE_PINS[name] for name in ("playwright", "three", "esbuild"))
                and report["browser"] and report["webgl"] and report["environment"].get("renderer"),
                "The actual browser/renderer or pinned tools were not identified.")
        require(all(report[key] == [] for key in ("page_errors", "console_errors", "failed_requests", "network_requests")),
                "The actual browser recorded an error or unaccounted network request.")
        wanted = list(AGENT_DESTINATIONS if agent else BROWSER_DESTINATIONS)
        require(report["selected_fixtures"] == wanted and [r["fixture"] for r in report["source_fixtures"]] == wanted,
                "The mandatory actual browser fixture set was changed.")
        review_path = self.file(record["visual_review"])
        review = json_file(review_path)
        require(review["schema_version"] == "ontokin.force-visual-review/0.1" and review["status"] == "reviewed"
                and review["source_kind"] == ("agent_retrieved_artifact" if agent else "source_component")
                and review["browser_report_sha256"] == file_identity(retained_path)
                and isinstance(review["reviewer"], str) and review["reviewer"].strip(), "A current identified visual review is missing.")
        reviewed_time = datetime.fromisoformat(review["reviewed_at_utc"])
        require(reviewed_time.tzinfo is not None and reviewed_time >= datetime.fromisoformat(report["generated_at_utc"].replace("Z", "+00:00")),
                "Visual review predates the actual captured browser run.")
        reviews = {row["capture_sha256"]: row for row in review["captures"]}
        require(len(reviews) == len(review["captures"]) == 3 * len(wanted), "Required visual observations are omitted or duplicated.")
        poses = captures = 0
        for source in report["source_fixtures"]:
            name = source["fixture"]
            artifact = native["artifacts"][name]
            require(source["program_revision"] == artifact.bundle.program_revision and source["artifact_sha256"] == artifact.sha
                    and source["provenance"] == artifact.record["provenance"], "The browser rendered bytes other than its validated artifact.")
            samples = [r for r in report["samples"] if r["fixture"] == name]
            require([{k: s[k] for k in ("time_seconds", "side")} for s in samples]
                    == [{k: s[k] for k in ("time_seconds", "side")} for s in artifact.reference["samples"]],
                    "A browser omitted its actual fixed pose observations.")
            front_camera = None
            for sample in samples:
                poses += artifact.check_poses(sample["objects"], rational(sample["time_seconds"]))
                camera = sample["camera"]
                require(camera["up"] == [0, 1, 0] and 0 < camera["near_m"] < camera["far_m"]
                        and camera["fit_sample_times_seconds"] == [artifact.end * i / 16 for i in range(17)]
                        and (front_camera is None or camera == front_camera), "The browser changed its Y-up motion framing while seeking.")
                front_camera = camera
            rows = [r for r in report["captures"] if r["fixture"] == name]
            expected = {("front", 0.), ("side", 0.), ("animated", .7 * artifact.end)}
            require(len(rows) == 3 and {(r["view"], float(r["time_seconds"])) for r in rows} == expected,
                    "The source, side or animated actual capture is missing.")
            for capture in rows:
                path = relative_file(directory, capture["file"])
                require(file_identity(path) == capture["sha256"] and capture["program_revision"] == artifact.bundle.program_revision
                        and capture["artifact_sha256"] == artifact.sha, "A browser PNG lost its exact artifact/source identity.")
                dimensions = surface._verify_png(path)
                viewport = report["environment"]["viewport"]
                require(dimensions["width"] == viewport["width"] and dimensions["height"] >= viewport["height"],
                        "PNG bytes do not match the actual viewport.")
                artifact.check_poses(capture["objects"], rational(capture["time_seconds"]))
                observation = reviews.get(capture["sha256"])
                require(observation is not None and observation["status"] == "reviewed" and observation["defects"] == []
                        and isinstance(observation["observation"], str) and observation["observation"].strip()
                        and all(observation[key] == capture[key] for key in ("fixture", "view", "program_revision", "artifact_sha256"))
                        and rational(observation["time_seconds"]) == rational(capture["time_seconds"]),
                        "An actual required PNG lacks a matching, concrete, accepted observation.")
                captures += 1
            playback = [r for r in report["playback"] if r["fixture"] == name]
            require(len(playback) == 1 and playback[0]["stable_across_frames"] is True and playback[0]["stopped_at_end"] is True
                    and playback[0]["started_at_seconds"] == .35 * artifact.end
                    and .35 * artifact.end < playback[0]["paused_at_seconds"] < artifact.end
                    and playback[0]["stopped_at_seconds"] == artifact.end, "The browser omitted actual play/pause/end observations.")
            artifact.check_poses(playback[0]["objects"], rational(playback[0]["paused_at_seconds"]))
        require(len(report["captures"]) == captures and report["world_pose_comparisons"] == poses,
                "Browser counts contradict the actual retained captures or observations.")
        return {"fixtures": len(wanted), "world_pose_observations": poses, "reviewed_pngs": captures,
                "browser": report["browser"], "webgl": report["webgl"], "visual_review_sha256": file_identity(review_path)}


def audit_release(evidence=None, *, root=None):
    """Read retained evidence and independently reconcile all named release roles."""
    auditor = Auditor(evidence, root=root)
    actions = (
        ("artifact-closure", auditor.closure), ("source", auditor.source), ("mapped-tests", auditor.mapped_tests),
        ("compatibility", auditor.compatibility), ("legacy-visual", auditor.legacy_visual),
        ("force-agent", auditor.force_agent), ("force-delivery", lambda: auditor.force_agent(delivery=True)),
        ("force-native", auditor.native), ("agent-native", lambda: auditor.native(agent=True)),
        ("force-browser", auditor.browser), ("agent-browser", lambda: auditor.browser(agent=True)), ("legacy", auditor.legacy),
    )
    roles = []
    for name, action in actions:
        result = {"id": name, "status": "running", "executed_external_tools": False, "issues": []}
        try:
            result["details"] = action()
            result["status"] = "passed"
        except MissingEvidence as error:
            result.update(status="pending", reason_kind="stale" if str(error).startswith("Stale") else "missing")
            result["issues"].append(str(error))
        except Exception as error:
            result.update(status="failed", reason_kind="contradictory_or_invalid")
            result["issues"].append(f"{type(error).__name__}: {error}")
        roles.append(result)
    by_role = {record["id"]: record for record in roles}
    cases = []
    for case in auditor.mapping["cases"]:
        dependencies = ["artifact-closure", *case["external_roles"]]
        if case["source_case_ids"]:
            dependencies.append("source")
        if case["required_tests"]:
            dependencies.append("mapped-tests")
        dependencies = list(dict.fromkeys(dependencies))
        relevant = [by_role[name] for name in dependencies]
        state = "failed" if any(r["status"] == "failed" for r in relevant) else "pending" if any(r["status"] != "passed" for r in relevant) else "passed"
        cases.append({**case, "status": state, "required_roles": dependencies,
                      "pending_reasons": [{"role": r["id"], "status": r["status"], "issues": r["issues"]}
                                          for r in relevant if r["status"] != "passed"]})
    after = source_identity()
    stable = stable_source(auditor.current, after)
    if not stable:
        for case in cases:
            case["status"] = "failed"
            case["pending_reasons"].append({"role": "audit_inputs", "status": "failed", "issues": ["Eligible inputs changed during audit."]})
    counts = Counter(case["status"] for case in cases)
    complete = stable and counts["passed"] == 12 and all(role["status"] == "passed" for role in roles)
    return {"schema_version": SCHEMA, "executed": True, "generated_at_utc": timestamp(),
            "status": "passed" if complete else "failed" if counts["failed"] else "pending",
            "implementation": auditor.current["implementation"], "source_before": auditor.current, "source_after": after,
            "source_stable_during_audit": stable, "mapping_sha256": file_identity(MAP_PATH),
            "evidence_manifest_sha256": None if auditor.path is None else file_identity(auditor.path),
            "profile": "force-0.1", "language_contract": "OK-LANG-005/0.1.1", "agent_contract": "ontokin.agent/0.5",
            "export_contract": "ontokin.glb/0.5", "source_case_ids": list(SOURCE_IDS), "roles": roles, "cases": cases,
            "summary": {"total": 12, "passed": counts["passed"], "failed": counts["failed"], "pending": counts["pending"],
                        "full_force_release_complete": complete, "all_required_roles_passed": all(r["status"] == "passed" for r in roles)},
            "executed_external_tools": False, "full_product_conformance_certified": False,
            "scope": "Identified finite force source, Agent and recorded delivery plus current inherited roles; broader GOAL domains and productivity baseline remain unmet.",
            "limits": ["Retained execution envelopes are reproducible local evidence, not cryptographic remote attestation.",
                       "Current Python matrix and actual browser observations cannot be inferred from one successful component.",
                       "No live destination physics, unexecuted platform, general mechanical/contact/deformation behavior or full-product acceptance is certified."]}


def evidence_template():
    current = source_identity()
    return {"schema_version": EVIDENCE_SCHEMA, "implementation": current["implementation"],
            "input_inventory_sha256": current["input_inventory_sha256"], "roles": {}, "files": [],
            "full_product_conformance_certified": False}


def seal_evidence(template, root, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    require(not output.exists(), "Sealing writes a new manifest; it must not replace retained evidence.")
    output.relative_to(root)
    document = json_file(template)
    require(document["schema_version"] == EVIDENCE_SCHEMA, "Only the separately versioned force release schema can be sealed.")
    records = []
    for path in sorted(root.rglob("*")):
        require(not path.is_symlink(), "A final evidence artifact is a symlink.")
        if path.is_file() and path != output and path.relative_to(root).as_posix() != "audit.json":
            require(not re.search(r"(?:\.sqlite(?:3)?|\.db)(?:-wal|-shm)?$", path.name),
                    "Remove mutable stores from the final evidence root before sealing.")
            records.append(file_record(path, root))
    current = source_identity()
    document.update(implementation=current["implementation"], input_inventory_sha256=current["input_inventory_sha256"],
                    files=records, full_product_conformance_certified=False)
    write_json(output, document)
    return {"manifest": str(output), "files": len(records), "manifest_sha256": file_identity(output)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="mode", required=True)
    execute = commands.add_parser("execute", help="Actually execute one named current Python role; Agent/test roles may open SQLite")
    execute.add_argument("--role", choices=("source", "mapped-tests", "regression", "core", "agent", "construction", "surface", "impulse"), required=True)
    execute.add_argument("--output-dir", type=Path, required=True)
    execute.add_argument("--external-evidence", type=Path)
    execute.add_argument("--evidence-root", type=Path, default=ROOT)
    record = commands.add_parser("record", help="Execute a directly requested current external tool and capture its new report")
    record.add_argument("--role", choices=tuple(EXTERNAL_ENTRYPOINTS), required=True)
    record.add_argument("--output-dir", type=Path, required=True)
    record.add_argument("--report", type=Path, required=True)
    record.add_argument("command", nargs=argparse.REMAINDER)
    audit = commands.add_parser("audit", help="Independently audit retained files without executing external commands")
    audit.add_argument("--evidence", type=Path)
    audit.add_argument("--evidence-root", type=Path)
    audit.add_argument("--output", type=Path, required=True)
    audit.add_argument("--allow-pending", action="store_true", help="Change only the exit policy for pending gates; never their status")
    inventory = commands.add_parser("inventory", help="Identify actual current code, Git and normative inputs")
    inventory.add_argument("--output", type=Path, required=True)
    template = commands.add_parser("template", help="Write an explicit empty/pending release manifest template")
    template.add_argument("--output", type=Path, required=True)
    seal = commands.add_parser("seal", help="Inventory an already assembled evidence root; do not synthesize results or rebase reports")
    seal.add_argument("--template", type=Path, required=True)
    seal.add_argument("--root", type=Path, required=True)
    seal.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.mode == "execute":
            result = execute_role(args.role, args.output_dir, external_evidence=args.external_evidence, evidence_root=args.evidence_root)
            print(json.dumps({"role": args.role, "status": result["status"], "output": str(args.output_dir / "execution.json")}))
            return 0 if result["status"] == "passed" else 1
        if args.mode == "record":
            command = args.command[1:] if args.command[:1] == ["--"] else args.command
            result = record_external(args.role, command, args.output_dir, args.report)
            print(json.dumps({"role": args.role, "status": result["status"], "exit_code": result["exit_code"], "output": str(args.output_dir / "execution.json")}))
            return 0 if result["status"] == "passed" else 1
        if args.mode == "audit":
            require(not args.output.exists(), "Audit output already exists; preserve the prior identified result.")
            result = audit_release(args.evidence, root=args.evidence_root)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            write_json(args.output, result)
            print(json.dumps({"status": result["status"], "summary": result["summary"], "output": str(args.output)}))
            return 0 if result["status"] == "passed" or (args.allow_pending and result["status"] == "pending") else 1
        if args.mode == "seal":
            print(json.dumps(seal_evidence(args.template, args.root, args.output)))
            return 0
        require(not args.output.exists(), "Output already exists; preserve prior identified evidence.")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        result = source_identity() if args.mode == "inventory" else evidence_template()
        write_json(args.output, result)
        print(json.dumps({"output": str(args.output), "sha256": file_identity(args.output)}))
        return 0
    except Exception as error:
        print(json.dumps({"status": "failed", "error": f"{type(error).__name__}: {error}", "full_force_release_complete": False}), file=sys.stderr)
        return 1
