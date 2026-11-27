#!/usr/bin/env python3
"""Readback evidence reader for gate MR of C271-P36 (MR-PLAN section 5).

It reads, never writes into, the records that the 0.2.0 provider leaves for a qualifying run's
CPU trio, and joins them with the record of MH's numerical-audit harness for the same cohort.

  cohort  One retained cohort root: the class's setup and its manifest, the three CPU attempts
          (reservation, preflight, start, supervisor outcome and result ledgers), the three
          stages with their inputs, reports and supervisor receipts, and the cohort accounting.
          It works for both routes the provider has: the owned temporary root that
          finish_cpu_cohort preserves as <evidence root>/current-host-cpu-*-preserved-<hex>
          (PRESERVATION.json and CLEANUP.json, the original removed), and a root named by
          STATIC_TRAY_READBACK_CPU_OUTPUT, which is kept in place.

  run     A driver run: the qualifying run's summary.json, bound by SHA-256, and its
          <output>/readback-binding/ (selection.json, workspace-binding.json, source-before.json
          and workspace-inventory.json), checked against the summary and against the unit step's
          environment overrides; then everything that `cohort` checks, and the links between
          the two: the cohort's setup names the derived selection, the cohort lies inside the
          selection's evidence root, the attempts' source is the workspace.

The numerical rows are handed to MH's audit_numeric.py, which is reused unchanged: the Director
runs it on the same cohort root (python3 -I -S -B <MH tooling>/audit_numeric.py --cohort-root C
--output A), and this reader takes A, bound by --audit-sha256, and requires that A's tool is the
file whose SHA-256 --audit-tool-sha256 gives, that A read this cohort root, that its twelve input
bindings are the bytes this reader found, and that it passed. That is the adapter to the driver
layout: the provider's cohort root is exactly the layout audit_numeric reads.

Every check is a named boolean; nothing is inferred from the provider's own "passed" flags alone.
A start is established only by a started record with a positive PID (P07 section 4).

Launch:  python3 -I -S -B readback_evidence.py cohort --cohort-root C --audit A --audit-sha256 H \
             --audit-tool-sha256 H --output OUT
A start without -B refuses before any other import (N-09). Nothing is started; only OUT is written.
"""
import sys


def _missing_dash_b(flags=None):
    """N-09: every start of the framework interpreter carries -B; True when this one does not."""
    return not (sys.flags if flags is None else flags).dont_write_bytecode


if __name__ == "__main__" and _missing_dash_b():
    sys.stderr.write('{"schema": "ontokin.c271.p36-tool-refusal/1", "tool": "readback_evidence.py", '
                     '"state": "REFUSED", "refusal": {"rule": "PYTHON", "reason": "Run with -B: every start '
                     'of the framework interpreter writes no bytecode (N-09)"}}\n')
    raise SystemExit(2)

import argparse  # noqa: E402  (after the -B check on purpose)
from datetime import datetime, timezone  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import stat  # noqa: E402
import time  # noqa: E402

SCHEMA = "ontokin.c271.p36-readback-evidence/1"
REFUSAL_SCHEMA = "ontokin.c271.p36-tool-refusal/1"
FAILURE_SCHEMA = "ontokin.c271.p36-tool-failure/1"
TOOL = "readback_evidence.py"
SUMMARY_SCHEMA = "ontokin.local-checks/0.1"
AUDIT_SCHEMA = "ontokin.c271.p35-numerical-audit/2"
PREFIX, VERSION = "ontokin.current-host-readback-", "/0.2.0"
IDENTITY = {"contract": "ontokin.current-host-readback/0.2.0", "design_revision": 4, "amendments": ["P33-AMENDMENT-001"]}
CASES = {"Q01-positive": ("Q01", False), "Q03-positive": ("Q03", False), "Q01-changed-reference": ("Q01", True)}
LABEL = "synthetic-readback"
STAGE_FILES = ("job.json", "probe.json", "synthetic-audit.json", "synthetic.glb",
               LABEL + ".process.json", LABEL + ".stderr.log", LABEL + ".stdout.log")
LEDGER_FILES = ("preflight.json", "reserved.json", "result.json", "started.json", "supervisor-outcome.json")
ROOT_FILES = ("cohort.json", "setup.json", "setup.pending.json", "supplemental-cpu.json")
PRESERVED_FILES = ("CLEANUP.json", "PRESERVATION.json")
NEGATIVE_FAILURE = {"code": "OTRAY-E-BACKEND", "reason": "Child exited with status 1", "state": "REJECTED"}
INPUT_LOCK = "CPU-ONLY-SYNTHETIC-NOT-NATIVE"
CONFIG_ENV = "ONTOKIN_CURRENT_HOST_READBACK_CONFIG"
DIGEST_ENV = "ONTOKIN_CURRENT_HOST_READBACK_CONFIG_SHA256"
PROVIDER = "prototypes/static_tray_v01/current_host_readback_v02.py"
PROBE = "prototypes/static_tray_v01/current_host_readback_v02.mjs"
BINDING_FILES = ("selection.json", "source-before.json", "workspace-binding.json", "workspace-inventory.json")
AUDIT_INPUTS = {"reference": "synthetic-audit.json", "report": "probe.json", "glb": "synthetic.glb", "job": "job.json"}
DOCUMENT_LIMIT, DATA_LIMIT, INVENTORY_LIMIT = 16 * 1024 * 1024, 64 * 1024 * 1024, 64 * 1024 * 1024
FLAG_NAMES = ("debug", "inspect", "interactive", "optimize", "dont_write_bytecode", "no_user_site", "no_site",
              "ignore_environment", "verbose", "bytes_warning", "quiet", "hash_randomization", "isolated",
              "dev_mode", "utf8_mode", "warn_default_encoding", "safe_path", "int_max_str_digits")
SHA256 = re.compile(r"[0-9a-f]{64}")
EXIT_OK, EXIT_DIFFERS, EXIT_REFUSED, EXIT_UNKNOWN = 0, 1, 2, 3


# ---------------------------------------------------------------------------
# Common helpers (as in the MH tools; each tool of this directory carries its own copy)
# ---------------------------------------------------------------------------

def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


class Refusal(Exception):
    """A precondition the tool refuses, with the rule it applies."""

    def __init__(self, rule, reason, **details):
        super().__init__(reason)
        self.rule, self.reason, self.details = rule, reason, details

    def as_dict(self):
        return {"rule": self.rule, "reason": self.reason, "details": self.details}


def require_dash_b(flags=None):
    if _missing_dash_b(flags):
        raise Refusal("PYTHON", "Run with -B: every start of the framework interpreter writes no bytecode (N-09)")


def mode_text(st_mode):
    return "0o%03o" % stat.S_IMODE(st_mode)


def canonical_path(value, *, kind=None, rule="PATH"):
    """An absolute path in normal form that is its own realpath, so no component is a symbolic link."""
    if type(value) is not str or not value.startswith("/") or "\0" in value:
        raise Refusal(rule, "Expected an absolute path", path=repr(value))
    if os.path.normpath(value) != value:
        raise Refusal(rule, "The path is not in normal form", path=value)
    if os.path.realpath(value) != value:
        raise Refusal(rule, "The path is not canonical: a component is a symbolic link", path=value)
    if kind is not None:
        try:
            info = os.lstat(value)
        except OSError as exc:
            raise Refusal(rule, "The path is absent or unreadable", path=value, error=str(exc)) from exc
        if kind == "dir" and not stat.S_ISDIR(info.st_mode):
            raise Refusal(rule, "Expected a directory", path=value)
        if kind == "file" and not stat.S_ISREG(info.st_mode):
            raise Refusal(rule, "Expected a regular file", path=value)
    return value


def read_regular(path, maximum, *, rule="INPUT"):
    """The bytes and binding of a regular file, opened without following a final link; a change during the read refuses."""
    canonical_path(path, rule=rule)
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | getattr(os, "O_CLOEXEC", 0))
    except OSError as exc:
        raise Refusal(rule, "Cannot open the input", path=path, error=str(exc)) from exc
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            raise Refusal(rule, "The input is not a regular file", path=path)
        if before.st_size > maximum:
            raise Refusal(rule, "The input exceeds its byte bound", path=path, size_bytes=before.st_size,
                          maximum=maximum)
        chunks, total = [], 0
        while True:
            block = os.read(fd, min(1 << 20, maximum + 1 - total))
            if not block:
                break
            chunks.append(block)
            total += len(block)
            if total > maximum:
                raise Refusal(rule, "The input grew beyond its byte bound", path=path)
        after = os.fstat(fd)
    finally:
        os.close(fd)
    named = os.lstat(path)

    def identity(info):
        return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_mode
    if identity(before) != identity(after) or identity(after) != identity(named) or total != before.st_size:
        raise Refusal(rule, "The input changed while it was read", path=path)
    data = b"".join(chunks)
    return data, {"sha256": hashlib.sha256(data).hexdigest(), "size_bytes": total, "mode": mode_text(before.st_mode)}


def bound_input(path, expected, maximum, *, rule):
    if type(expected) is not str or SHA256.fullmatch(expected) is None:
        raise Refusal("USAGE", "Expected a lowercase SHA-256 digest for " + rule.lower(), digest=repr(expected))
    data, binding = read_regular(path, maximum, rule=rule)
    if binding["sha256"] != expected:
        raise Refusal("DIGEST", "The input differs from its supplied SHA-256", path=path, role=rule,
                      expected_sha256=expected, actual_sha256=binding["sha256"])
    return data, {"path": path, **binding}


def strict_json(raw, *, rule="INPUT", what="document"):
    """JSON with duplicate members and non-finite constants refused."""
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise Refusal(rule, "Duplicate JSON member in the " + what, member=key)
            result[key] = value
        return result

    def constant(text):
        raise Refusal(rule, "Non-finite JSON constant in the " + what, constant=text)
    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=constant)
    except Refusal:
        raise
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise Refusal(rule, "Invalid JSON in the " + what, error=str(exc)) from exc


def json_text(value):
    return (json.dumps(value, sort_keys=True, indent=1, ensure_ascii=True, allow_nan=False) + "\n").encode("ascii")


def fsync_directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def prepare_output_file(path):
    canonical_path(path, rule="OUTPUT")
    canonical_path(os.path.dirname(path), kind="dir", rule="OUTPUT")
    if os.path.lexists(path):
        raise Refusal("OUTPUT", "The output path exists; it is never replaced", path=path)
    return path


def write_new(path, data):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0), 0o644)
    try:
        view = memoryview(data)
        while view:
            view = view[os.write(fd, view):]
        os.fsync(fd)
    finally:
        os.close(fd)
    fsync_directory(os.path.dirname(path))
    return {"path": path, "sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data)}


def tool_record():
    path = os.path.realpath(__file__)
    with open(path, "rb") as stream:
        data = stream.read()
    return {"path": path, "sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data),
            "mode": mode_text(os.stat(path).st_mode)}


def invocation_record():
    return {"argv": list(sys.argv), "orig_argv": list(getattr(sys, "orig_argv", [])), "cwd": os.getcwd(),
            "pid": os.getpid(),
            "python": {"implementation": sys.implementation.name, "version": "%d.%d.%d" % sys.version_info[:3],
                       "build_string": sys.version, "executable": sys.executable,
                       "flags": {name: getattr(sys.flags, name) for name in FLAG_NAMES}}}


# ---------------------------------------------------------------------------
# The reading
# ---------------------------------------------------------------------------

class Checks:
    """Named boolean checks with their observed details; a missing or unreadable file fails its checks."""

    def __init__(self):
        self.rows = {}

    def add(self, name, passed, **details):
        if name in self.rows:
            raise AssertionError("check named twice: " + name)
        self.rows[name] = {"passed": bool(passed), **({"details": details} if details else {})}
        return bool(passed)

    def failed(self):
        return sorted(name for name, row in self.rows.items() if not row["passed"])


def plain(binding):
    return {key: binding[key] for key in ("sha256", "size_bytes", "mode")} if binding else None


def element(value, *path):
    for step in path:
        if isinstance(step, int):
            if not isinstance(value, list) or not 0 <= step < len(value):
                return None
        elif not isinstance(value, dict) or step not in value:
            return None
        value = value[step]
    return value


def identity_of(document):
    return {key: element(document, key) for key in IDENTITY}


def inside(path, parent):
    return type(path) is str and type(parent) is str and path != parent and path.startswith(parent.rstrip("/") + "/")


class Tree:
    """Every entry under one root, links never followed, each regular file read once and bound."""

    def __init__(self, root):
        self.root = root
        self.files, self.directories, self.others = {}, [], {}
        self.data = {}
        for directory, names, files in os.walk(root, followlinks=False):
            names.sort()
            for name in list(names):
                path = os.path.join(directory, name)
                if os.path.islink(path):
                    self.others[os.path.relpath(path, root)] = "symbolic link"
                    names.remove(name)
                else:
                    self.directories.append(os.path.relpath(path, root))
            for name in sorted(files):
                path = os.path.join(directory, name)
                relative = os.path.relpath(path, root)
                info = os.lstat(path)
                if not stat.S_ISREG(info.st_mode):
                    self.others[relative] = "symbolic link" if stat.S_ISLNK(info.st_mode) else "special file"
                    continue
                data, binding = read_regular(path, DATA_LIMIT, rule="COHORT")
                self.files[relative] = binding
                self.data[relative] = data

    def document(self, relative, checks, name):
        """The strict JSON value of a file of the tree, or None (failing the named check) when absent or invalid."""
        if relative not in self.files:
            checks.add(name + "_readable", False, path=relative, reason="absent")
            return None
        try:
            value = strict_json(self.data[relative], rule="COHORT", what=relative)
        except Refusal as exc:
            checks.add(name + "_readable", False, path=relative, reason=exc.reason)
            return None
        checks.add(name + "_readable", True)
        return value


def read_cohort(root, checks):
    """The checks of one retained cohort root; returns the facts other readings link to."""
    tree = Tree(root)
    preserved = "PRESERVATION.json" in tree.files
    facts = {"cohort_root": root, "route": "preserved" if preserved else "kept_in_place", "files": len(tree.files),
             "bindings": tree.files}
    checks.add("cohort_no_link_or_special_file", not tree.others, entries=tree.others)
    original = root
    if preserved:
        preservation = tree.document("PRESERVATION.json", checks, "preservation")
        cleanup = tree.document("CLEANUP.json", checks, "cleanup")
        original = element(preservation, "original_root") if type(element(preservation, "original_root")) is str else None
        listed = element(preservation, "files") if isinstance(element(preservation, "files"), dict) else {}
        kept = {name: plain(binding) for name, binding in tree.files.items() if name not in PRESERVED_FILES}
        checks.add("preservation_schema", element(preservation, "schema") == PREFIX + "preserved-cohort" + VERSION
                   and identity_of(preservation) == IDENTITY)
        checks.add("preservation_names_this_root", element(preservation, "retained_root") == root)
        checks.add("preservation_original_is_a_sibling", type(original) is str
                   and os.path.dirname(original) == os.path.dirname(root)
                   and os.path.basename(root).startswith(os.path.basename(original) + "-preserved-"))
        checks.add("preservation_lists_exactly_the_retained_files", listed == kept,
                   missing=sorted(set(kept) - set(listed)), extra=sorted(set(listed) - set(kept)),
                   differing=sorted(name for name in set(kept) & set(listed) if kept[name] != listed[name]))
        checks.add("cleanup_removed_the_original", element(cleanup, "owned_temporary_root") == original
                   and element(cleanup, "removed") is True)
        checks.add("original_root_absent_now", type(original) is str and not os.path.lexists(original))
    facts["original_root"] = original
    expected_files = set(ROOT_FILES) | (set(PRESERVED_FILES) if preserved else set())
    expected_files |= {label + "/" + name for label in CASES for name in STAGE_FILES}
    expected_files |= {"provider-ledgers/" + label + "/" + name for label in CASES for name in LEDGER_FILES}
    expected_directories = {"provider-ledgers"} | set(CASES) | {"provider-ledgers/" + label for label in CASES}
    checks.add("cohort_holds_exactly_the_expected_files", set(tree.files) == expected_files,
               missing=sorted(expected_files - set(tree.files)), extra=sorted(set(tree.files) - expected_files))
    checks.add("cohort_holds_exactly_the_expected_directories", set(tree.directories) == expected_directories,
               missing=sorted(expected_directories - set(tree.directories)),
               extra=sorted(set(tree.directories) - expected_directories))
    checks.add("no_finalization_failure_marker", not any(name.endswith("finalization.failed.json") for name in tree.files))
    checks.add("unused_native_schedule_absent", not os.path.lexists(os.path.join(root, "unused-native-schedule")))

    setup = tree.document("setup.json", checks, "setup")
    pending = tree.document("setup.pending.json", checks, "setup_pending")
    manifest = tree.document("supplemental-cpu.json", checks, "manifest")
    cohort = tree.document("cohort.json", checks, "cohort")
    manifest_binding = tree.files.get("supplemental-cpu.json")
    config_path, config_sha256 = element(setup, "config_path"), element(setup, "config_sha256")
    facts.update(setup_config_path=config_path, setup_config_sha256=config_sha256,
                 setup_source_root=element(setup, "source_root"), boot=element(setup, "boot"),
                 labels=element(setup, "labels"))
    checks.add("setup_schema_and_identity", element(setup, "schema") == PREFIX + "setup" + VERSION
               and identity_of(setup) == IDENTITY)
    checks.add("setup_passed_qualifying_without_error", element(setup, "passed") is True
               and element(setup, "run_kind") == "qualifying" and element(setup, "checker_starts") == 0
               and "error" not in (setup or {"error": None}))
    checks.add("setup_labels_real_and_qualifying", element(setup, "labels", "boundary") == "real"
               and element(setup, "labels", "run_kind") == "qualifying")
    checks.add("setup_binds_the_manifest", manifest_binding is not None
               and element(setup, "manifest_sha256") == manifest_binding["sha256"])
    checks.add("setup_names_a_selection", type(config_path) is str and type(config_sha256) is str
               and SHA256.fullmatch(config_sha256) is not None)
    checks.add("setup_pending_is_the_initial_record", element(pending, "schema") == PREFIX + "setup" + VERSION
               and element(pending, "passed") is False and element(pending, "checker_starts") == 0)
    boot = element(setup, "boot", "boot_session_uuid")
    checks.add("setup_boot_observed", type(boot) is str and bool(boot))

    checks.add("manifest_schema_and_identity", element(manifest, "schema") == PREFIX + "lock" + VERSION
               and identity_of(manifest) == IDENTITY)
    checks.add("manifest_cohort_and_schedule_roots", element(manifest, "cohort_root") == original
               and element(manifest, "schedule_root") == (original or "") + "/unused-native-schedule")
    checks.add("manifest_names_the_setup_selection", element(manifest, "selection") == {"path": config_path,
                                                                                       "sha256": config_sha256})
    slots = element(manifest, "slots") if isinstance(element(manifest, "slots"), list) else []
    checks.add("manifest_twelve_structural_slots", len(slots) == 12)
    template = element(slots, 0, "argv")
    facts["runtime_executable"] = element(manifest, "runtime", "executable")
    facts["probe"] = element(manifest, "probe")

    checks.add("cohort_schema_and_identity", element(cohort, "schema") == PREFIX + "cohort" + VERSION
               and identity_of(cohort) == IDENTITY)
    checks.add("cohort_passed_with_three_starts", element(cohort, "passed") is True
               and element(cohort, "actual_checker_starts") == 3 and "error" not in (cohort or {"error": None}))
    checks.add("cohort_expected_cases", element(cohort, "expected_cases") == sorted(CASES))
    checks.add("cohort_labels_real_and_qualifying", element(cohort, "labels", "boundary") == "real"
               and element(cohort, "labels", "run_kind") == "qualifying")
    attempts = element(cohort, "attempts") if isinstance(element(cohort, "attempts"), dict) else {}
    checks.add("cohort_accounts_the_three_attempts", sorted(attempts) == sorted(CASES))

    starts, cases = [], {}
    for label, (case, negative) in CASES.items():
        prefix = "case_" + label.replace("-", "_") + "_"
        ledger = "provider-ledgers/" + label + "/"
        stage = original + "/" + label if original else None
        result = tree.document(ledger + "result.json", checks, prefix + "result")
        reserved = tree.document(ledger + "reserved.json", checks, prefix + "reserved")
        preflight = tree.document(ledger + "preflight.json", checks, prefix + "preflight")
        started = tree.document(ledger + "started.json", checks, prefix + "started")
        outcome = tree.document(ledger + "supervisor-outcome.json", checks, prefix + "supervisor_outcome")
        receipt = tree.document(label + "/" + LABEL + ".process.json", checks, prefix + "receipt")
        job = tree.document(label + "/job.json", checks, prefix + "job")
        report = tree.document(label + "/probe.json", checks, prefix + "report")
        process = element(result, "process")
        result_binding = tree.files.get(ledger + "result.json")
        descriptor = attempts.get(label) if isinstance(attempts.get(label), dict) else {}
        checks.add(prefix + "cohort_descriptor_binds_the_result",
                   descriptor.get("path") == (original or "") + "/" + ledger + "result.json"
                   and result_binding is not None and plain(descriptor) == plain(result_binding))
        checks.add(prefix + "result_schema_and_identity", element(result, "schema") == PREFIX + "attempt" + VERSION
                   and identity_of(result) == IDENTITY)
        checks.add(prefix + "result_state", element(result, "state") == ("SUPERVISOR_REFUSAL" if negative else "COMPLETED"))
        checks.add(prefix + "result_one_start", element(result, "actual_checker_starts") == 1
                   and element(result, "expected_checker_starts") == 1)
        checks.add(prefix + "result_no_provider_failure", element(result, "provider_failure") is None)
        checks.add(prefix + "result_supervisor_failure", element(result, "supervisor_failure") ==
                   (NEGATIVE_FAILURE if negative else None))
        checks.add(prefix + "result_preflight_equals_postflight", preflight is not None
                   and element(result, "preflight") == preflight == element(result, "postflight"))
        checks.add(prefix + "result_labels_real_and_qualifying", element(result, "labels", "boundary") == "real"
                   and element(result, "labels", "run_kind") == "qualifying")
        checks.add(prefix + "result_boot_unchanged", type(boot) is str
                   and element(result, "boot_before", "boot_session_uuid") == boot
                   and element(result, "boot_after", "boot_session_uuid") == boot)
        pid = element(process, "pid")
        checks.add(prefix + "receipt_exit_status", element(process, "returncode") == (1 if negative else 0))
        checks.add(prefix + "receipt_cleanup_and_handles", element(process, "cleanup", "passed") is True
                   and element(process, "handles_closed") is True)
        checks.add(prefix + "receipt_error", element(process, "error") == (NEGATIVE_FAILURE if negative else None))
        checks.add(prefix + "receipt_positive_pid_own_group", type(pid) is int and pid > 0
                   and element(process, "process_group") == pid)
        checks.add(prefix + "receipt_label_and_stage", element(process, "label") == LABEL
                   and element(process, "cwd") == stage)
        expected_argv = (template[:-1] + [stage + "/job.json"]) if isinstance(template, list) and template and stage else None
        checks.add(prefix + "argv_is_the_manifest_template", expected_argv is not None
                   and element(process, "argv") == expected_argv == element(result, "expected_argv"))
        checks.add(prefix + "argv_carries_the_selection_digest", isinstance(element(process, "argv"), list)
                   and element(process, "argv")[-4:-2] == ["--expected-config-sha256", config_sha256])
        checks.add(prefix + "runtime_is_the_manifest_runtime", element(process, "argv", 0) == facts["runtime_executable"]
                   and facts["runtime_executable"] is not None)
        checks.add(prefix + "supervisor_receipt_file_equals_the_ledger", receipt is not None and receipt == process)
        checks.add(prefix + "supervisor_outcome_equals_the_ledger", element(outcome, "process") == process
                   and element(outcome, "failure") == element(result, "supervisor_failure")
                   and element(outcome, "actual_checker_starts") == 1)
        started_record = element(started, "process")
        start_established = (type(element(started_record, "pid")) is int and element(started_record, "pid") > 0
                             and element(started, "actual_checker_starts") == 1)
        checks.add(prefix + "start_established_by_a_positive_pid", start_established)
        checks.add(prefix + "started_record_is_this_start", element(started_record, "pid") == pid
                   and element(started_record, "argv") == element(process, "argv")
                   and element(started_record, "start_monotonic") == element(process, "start_monotonic")
                   and element(started_record, "returncode") is None)
        checks.add(prefix + "reserved_is_the_initial_ledger", element(reserved, "schema") == PREFIX + "attempt" + VERSION
                   and element(reserved, "state") == "PENDING" and element(reserved, "actual_checker_starts") == 0)
        glb, audit = tree.files.get(label + "/synthetic.glb"), tree.files.get(label + "/synthetic-audit.json")
        job_binding = tree.files.get(label + "/job.json")
        checks.add(prefix + "job_names_its_stage", element(job, "slot") == "CPU-" + label and element(job, "case") == case
                   and element(job, "input_lock_sha256") == INPUT_LOCK
                   and element(job, "artifact") == (stage or "") + "/synthetic.glb"
                   and element(job, "audit") == (stage or "") + "/synthetic-audit.json"
                   and element(job, "result") == (stage or "") + "/probe.json"
                   and element(job, "manifest") == (original or "") + "/supplemental-cpu.json")
        checks.add(prefix + "job_binds_its_inputs_and_manifest", glb is not None and audit is not None
                   and manifest_binding is not None
                   and element(job, "artifact_sha256") == glb["sha256"] and element(job, "audit_sha256") == audit["sha256"]
                   and element(job, "supplemental_manifest_sha256") == manifest_binding["sha256"])
        checks.add(prefix + "preflight_binds_the_job_inputs_and_selection", job_binding is not None
                   and element(preflight, "job") == job and element(preflight, "job_binding") == plain(job_binding)
                   and element(preflight, "inputs", "artifact") == plain(glb)
                   and element(preflight, "inputs", "audit") == plain(audit)
                   and element(preflight, "manifest_sha256") == (manifest_binding or {}).get("sha256")
                   and element(preflight, "config_sha256") == config_sha256)
        after = element(result, "artifacts_after") if isinstance(element(result, "artifacts_after"), dict) else {}
        actual = {name[len(label) + 1:]: plain(value) for name, value in tree.files.items()
                  if name.startswith(label + "/") and name.count("/") == 1}
        checks.add(prefix + "artifacts_after_are_the_retained_bytes", after == actual,
                   differing=sorted(name for name in set(after) | set(actual) if after.get(name) != actual.get(name)))
        checks.add(prefix + "report_outcome", element(report, "passed") is (not negative)
                   and element(report, "artifact_sha256") == (glb or {}).get("sha256")
                   and element(report, "input_preserved") is True and element(report, "slot") == "CPU-" + label)
        if start_established:
            starts.append({"case": label, "pid": element(started_record, "pid"),
                           "process_group": element(started_record, "process_group"),
                           "executable": element(started_record, "argv", 0)})
        cases[label] = {"stage": stage, "returncode": element(process, "returncode"), "state": element(result, "state"),
                        "pid": pid, "inputs": {key: tree.files.get(label + "/" + name) for key, name in AUDIT_INPUTS.items()},
                        "preflight_source": element(preflight, "source")}
    checks.add("exactly_three_starts_established", len(starts) == 3, starts=starts)
    facts.update(starts=starts, cases=cases)
    return facts


def join_audit(audit_path, audit_sha256, tool_sha256, facts, checks):
    """MH's numerical-audit record for this cohort root: its tool, its inputs and its verdict."""
    if type(tool_sha256) is not str or SHA256.fullmatch(tool_sha256) is None:
        raise Refusal("USAGE", "Expected a lowercase SHA-256 digest for --audit-tool-sha256")
    raw, binding = bound_input(audit_path, audit_sha256, DATA_LIMIT, rule="AUDIT")
    audit = strict_json(raw, rule="AUDIT", what="numerical-audit record")
    checks.add("audit_schema", element(audit, "schema") == AUDIT_SCHEMA)
    checks.add("audit_tool_is_the_bound_harness", element(audit, "tool", "sha256") == tool_sha256
               and str(element(audit, "tool", "path")).endswith("/audit_numeric.py"))
    checks.add("audit_ran_with_dash_b", element(audit, "invocation", "python", "flags", "dont_write_bytecode") == 1)
    checks.add("audit_read_this_cohort_root", element(audit, "cohort_root") == facts["cohort_root"])
    checks.add("audit_all_three_cases", element(audit, "all_three_cases") is True
               and sorted(element(audit, "cases") or {}) == sorted(CASES))
    rows = {}
    for label in CASES:
        prefix = "audit_" + label.replace("-", "_") + "_"
        inputs = element(audit, "cases", label, "inputs") or {}
        expected = {key: {"path": facts["cohort_root"] + "/" + label + "/" + name, **(plain(facts["cases"][label]["inputs"][key]) or {})}
                    for key, name in AUDIT_INPUTS.items()}
        checks.add(prefix + "inputs_are_the_bytes_read_here", inputs == expected,
                   differing=sorted(key for key in AUDIT_INPUTS if inputs.get(key) != expected[key]))
        checks.add(prefix + "passed", element(audit, "cases", label, "passed") is True)
        counts = element(audit, "cases", label, "counts") or {}
        rows[label] = {"counts": counts, "negative_row": element(audit, "cases", label, "negative_row"),
                       "failed_checks": sorted(name for name, value in (element(audit, "cases", label, "checks") or {}).items()
                                               if value is not True)}
    checks.add("audit_negative_fixture_passed", element(audit, "negative_fixture", "passed") is True)
    checks.add("audit_passed", element(audit, "passed") is True)
    return {"input": binding, "tool": element(audit, "tool"), "expected_tool_sha256": tool_sha256, "cases": rows,
            "negative_fixture": element(audit, "negative_fixture"), "passed": element(audit, "passed")}


def read_driver_run(summary_path, summary_sha256, facts_out, checks):
    """The qualifying run's summary and its readback binding, before the cohort is read."""
    raw, binding = bound_input(summary_path, summary_sha256, DOCUMENT_LIMIT, rule="SUMMARY")
    summary = strict_json(raw, rule="SUMMARY", what="summary")
    if type(summary) is not dict or summary.get("schema_version") != SUMMARY_SCHEMA:
        raise Refusal("SUMMARY", "The summary is not a " + SUMMARY_SCHEMA + " document")
    output = os.path.dirname(summary_path)
    selection = summary.get("readback_selection") if isinstance(summary.get("readback_selection"), dict) else {}
    derived = selection.get("derived") if isinstance(selection.get("derived"), dict) else {}
    original_sha256 = selection.get("config_sha256")
    checks.add("summary_run_kind_qualifying_and_workspace_bound", selection.get("run_kind") == "qualifying"
               and selection.get("status") == "workspace_bound")
    checks.add("summary_selection_digest_supplied_and_observed", type(original_sha256) is str
               and selection.get("expected_config_sha256") == original_sha256
               and element(selection, "observed_identity", "sha256") == "sha256:" + str(original_sha256))
    steps = summary.get("steps") if isinstance(summary.get("steps"), list) else []
    unit = next((step for step in steps if isinstance(step, dict) and step.get("id") == "unit-tests"), None)
    workspace = element(unit, "cwd")
    checks.add("summary_workspace_is_the_output_workspace", workspace == output + "/workspace")
    directory = output + "/readback-binding"
    files = {}
    try:
        names = sorted(os.listdir(directory))
    except OSError as exc:
        names = []
        checks.add("readback_binding_directory_readable", False, error=str(exc))
    else:
        checks.add("readback_binding_directory_readable", True)
    checks.add("readback_binding_holds_exactly_four_files", names == sorted(BINDING_FILES), names=names)
    documents = {}
    for name in BINDING_FILES:
        path = directory + "/" + name
        if name not in names or not os.path.isfile(path) or os.path.islink(path):
            continue
        data, file_binding = read_regular(path, INVENTORY_LIMIT, rule="BINDING")
        files[name] = {"path": path, **file_binding}
        try:
            documents[name] = strict_json(data, rule="BINDING", what=name)
        except Refusal as exc:
            checks.add("binding_" + name.replace(".", "_").replace("-", "_") + "_valid_json", False, reason=exc.reason)
    derived_path, derived_sha256 = derived.get("config_path"), derived.get("config_sha256")
    checks.add("derived_selection_is_the_binding_file", derived_path == directory + "/selection.json"
               and "selection.json" in files and files["selection.json"]["sha256"] == derived_sha256)
    checks.add("derived_workspace_binding_is_the_binding_file",
               derived.get("workspace_binding_path") == directory + "/workspace-binding.json"
               and "workspace-binding.json" in files
               and files["workspace-binding.json"]["sha256"] == derived.get("workspace_binding_sha256"))
    checks.add("derived_parent_is_the_original_selection", derived.get("parent_config_sha256") == original_sha256)
    config = documents.get("selection.json")
    binding_document = documents.get("workspace-binding.json")
    parent = element(config, "parent") if isinstance(element(config, "parent"), dict) else {}
    checks.add("selection_schema", element(config, "schema") == PREFIX + "config" + VERSION
               and element(config, "contract") == IDENTITY["contract"])
    checks.add("selection_parent_names_the_original", element(parent, "config", "path") == selection.get("config_path")
               and element(parent, "config", "sha256") == original_sha256
               and parent.get("source_root") == summary.get("source_root"))
    try:
        _, original_binding = read_regular(canonical_path(str(selection.get("config_path")), rule="BINDING"),
                                           DOCUMENT_LIMIT, rule="BINDING")
        checks.add("original_selection_file_unchanged", isinstance(parent.get("config"), dict)
                   and plain(original_binding) == plain(parent["config"]))
    except Refusal as exc:
        checks.add("original_selection_file_unchanged", False, reason=exc.reason)
    checks.add("selection_parent_binds_the_workspace_binding", "workspace-binding.json" in files
               and parent.get("workspace_binding") == {key: files["workspace-binding.json"][key]
                                                       for key in ("path", "sha256", "size_bytes", "mode")})
    checks.add("selection_source_is_the_workspace", element(config, "source", "root") == workspace
               and workspace is not None)
    evidence = element(config, "evidence_root")
    checks.add("output_inside_the_evidence_root", inside(output, evidence) or output == evidence)
    checks.add("workspace_binding_schema_and_identity", element(binding_document, "schema") == PREFIX + "workspace" + VERSION
               and identity_of(binding_document) == IDENTITY
               and re.fullmatch(r"[0-9a-f]{32}", str(element(binding_document, "identity"))) is not None)
    git = summary.get("git") if isinstance(summary.get("git"), dict) else {}
    checks.add("workspace_binding_roles", element(binding_document, "parent_config") == parent.get("config")
               and element(binding_document, "source_root") == summary.get("source_root")
               and element(binding_document, "workspace_root") == workspace
               and element(binding_document, "commit") == git.get("local_head") == element(config, "source", "commit")
               and element(binding_document, "tree") == git.get("local_tree") == element(config, "source", "tree")
               and element(binding_document, "provider") == (workspace or "") + "/" + PROVIDER
               and element(binding_document, "probe") == (workspace or "") + "/" + PROBE)
    for key, name in (("source_before", "source-before.json"), ("workspace_inventory", "workspace-inventory.json")):
        checks.add("workspace_binding_binds_" + key, name in files and element(binding_document, key) ==
                   {field: files[name][field] for field in ("path", "sha256", "size_bytes", "mode")})
    driver_before = None
    inventory = summary.get("source_inventory") if isinstance(summary.get("source_inventory"), dict) else {}
    try:
        data, driver_binding = read_regular(output + "/source-before.json", INVENTORY_LIMIT, rule="BINDING")
        driver_before = strict_json(data, rule="BINDING", what="driver source-before.json")
        checks.add("driver_source_before_is_the_summary_inventory", "sha256:" + driver_binding["sha256"] ==
                   inventory.get("sha256") and element(driver_before, "sha256") == inventory.get("inventory_sha256"))
    except Refusal as exc:
        checks.add("driver_source_before_is_the_summary_inventory", False, reason=exc.reason)
    checks.add("provider_inventories_equal_the_driver_inventory", driver_before is not None
               and documents.get("source-before.json") == driver_before == documents.get("workspace-inventory.json"))
    overrides = element(unit, "environment_overrides") if isinstance(element(unit, "environment_overrides"), dict) else {}
    checks.add("unit_step_received_the_derived_selection", overrides.get(CONFIG_ENV) == derived_path
               and overrides.get(DIGEST_ENV) == derived_sha256 and overrides.get("PYTHONNOUSERSITE") == "1"
               and overrides.get("PYTHONDONTWRITEBYTECODE") == "1")
    checks.add("unit_step_started", element(unit, "process_started") is True)
    facts_out.update(summary=binding, output=output, workspace=workspace, evidence_root=evidence,
                     derived=derived, original_selection={"path": selection.get("config_path"), "sha256": original_sha256},
                     unit_step={"status": element(unit, "status"), "returncode": element(unit, "returncode"),
                                "test_execution": element(unit, "test_execution"),
                                "removed_injection_environment_names": element(unit, "removed_injection_environment_names")},
                     binding_files=files, selection_source=element(config, "source"))


def link_run_and_cohort(run, cohort, checks):
    checks.add("cohort_setup_names_the_derived_selection", cohort["setup_config_path"] == run["derived"].get("config_path")
               and cohort["setup_config_sha256"] == run["derived"].get("config_sha256"))
    checks.add("cohort_setup_source_is_the_workspace", cohort["setup_source_root"] == run["workspace"]
               and run["workspace"] is not None)
    checks.add("cohort_inside_the_evidence_root", inside(cohort["cohort_root"], run["evidence_root"])
               and inside(cohort["original_root"], run["evidence_root"]))
    checks.add("attempt_sources_are_the_selection_source", all(row["preflight_source"] == run["selection_source"]
                                                              for row in cohort["cases"].values()))
    checks.add("probe_is_the_workspace_probe", cohort["probe"] == (run["workspace"] or "") + "/" + PROBE)


def run_reader(args):
    started, monotonic = utc_now(), time.monotonic()
    checks = Checks()
    run = None
    if args.command == "run":
        run = {}
        read_driver_run(canonical_path(args.summary, kind="file", rule="SUMMARY"), args.summary_sha256, run, checks)
    root = canonical_path(args.cohort_root, kind="dir", rule="COHORT")
    cohort = read_cohort(root, checks)
    audit = join_audit(canonical_path(args.audit, kind="file", rule="AUDIT"), args.audit_sha256, args.audit_tool_sha256,
                       cohort, checks)
    if run is not None:
        link_run_and_cohort(run, cohort, checks)
    failed = checks.failed()
    record = {"schema": SCHEMA, "tool": tool_record(), "invocation": invocation_record(), "started_at_utc": started,
              "command": args.command, "state": "READ", "loaded_project_files": [],
              "driver_run": run, "cohort": {key: cohort[key] for key in ("cohort_root", "route", "original_root", "files",
                                                                         "setup_config_path", "setup_config_sha256",
                                                                         "setup_source_root", "boot", "runtime_executable",
                                                                         "probe", "starts", "cases")},
              "cohort_bindings": cohort["bindings"], "numerical_audit": audit,
              "starts": {"established": len(cohort["starts"]), "expected": 3, "rows": cohort["starts"]},
              "checks": checks.rows, "failed_checks": failed, "passed": not failed,
              "limits": ["It reads the provider's records and the audit record; it re-derives no numerical row itself.",
                         "A start that leaves no started record with a positive PID is not counted here; the audit "
                         "hook and the freeze's start accounting cover the routes it cannot see."]}
    record.update(finished_at_utc=utc_now(), elapsed_s=time.monotonic() - monotonic)
    write_new(args.output, json_text(record))
    sys.stderr.write("READBACK-EVIDENCE " + json.dumps({"passed": not failed, "failed_checks": failed,
                                                         "starts": len(cohort["starts"])}, sort_keys=True) + "\n")
    return EXIT_OK if not failed else EXIT_DIFFERS


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Refusal("USAGE", "Invalid arguments: " + message)


def build_parser():
    parser = _Parser(prog=TOOL, allow_abbrev=False, description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True, parser_class=_Parser)
    for name in ("cohort", "run"):
        command = commands.add_parser(name, allow_abbrev=False)
        if name == "run":
            command.add_argument("--summary", required=True)
            command.add_argument("--summary-sha256", required=True)
        command.add_argument("--cohort-root", required=True)
        command.add_argument("--audit", required=True)
        command.add_argument("--audit-sha256", required=True)
        command.add_argument("--audit-tool-sha256", required=True)
        command.add_argument("--output", required=True)
    return parser


def main(argv=None):
    output = None
    try:
        args = build_parser().parse_args(argv)
        output = prepare_output_file(args.output)
        require_dash_b()
        return run_reader(args)
    except Refusal as exc:
        return report_end(output, {"schema": REFUSAL_SCHEMA, "tool": TOOL, "state": "REFUSED",
                                   "refusal": exc.as_dict()}, EXIT_REFUSED)
    except BaseException as exc:  # an unexpected failure is reported as unknown, never as a result
        return report_end(output, {"schema": FAILURE_SCHEMA, "tool": TOOL, "state": "UNKNOWN",
                                   "error": {"type": type(exc).__name__, "reason": str(exc)}}, EXIT_UNKNOWN)


def report_end(output, document, code):
    document.update(finished_at_utc=utc_now(), invocation=invocation_record())
    sys.stderr.write(json.dumps(document, sort_keys=True) + "\n")
    if output is not None and not os.path.lexists(output):
        try:
            write_new(output, json_text(document))
        except OSError:
            pass
    return code


if __name__ == "__main__":
    raise SystemExit(main())
