#!/usr/bin/env python3
"""Independent C268 capture, loader-equivalence and cleanup probes."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import threading
import traceback
import types
from unittest.mock import patch

def identity(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}

def load(path, name):
    m = types.ModuleType(name)
    m.__file__ = str(path)
    sys.modules[name] = m
    exec(compile(path.read_bytes(), str(path), "exec"), m.__dict__)
    return m

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    repo, out = a.repo.resolve(), a.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    eng = repo / "docs/engineering"
    reader_path = eng / "localized-repair-c268/endpoint_reader.py"
    reader = load(reader_path, "_review_c268_reader")
    direct = load(eng / "localized-repair-c267/hinge_compare.py", "_review_c268_direct")
    pinned = json.loads((eng / "localized-repair-c260/INPUTS.json").read_text())
    by_name = {Path(row["path"]).name: row for row in pinned["files"]}
    original = {}
    witness_dir = out / "input-bytes"
    witness_dir.mkdir()
    for name in ("before.main.ok", "after.main.ok", "hinges.ok", "before.glb", "after.glb"):
        row = by_name[name]
        raw = (repo / row["path"]).read_bytes()
        assert identity(raw) == {k: row[k] for k in ("bytes", "sha256")}
        original[name] = raw
        (witness_dir / name).write_bytes(raw)
    source_inputs = {name: identity((repo / name).read_bytes()) for name in (
        "docs/engineering/localized-repair-c268/endpoint_reader.py",
        "docs/engineering/localized-repair-c260/CONTRACT.md",
        "docs/engineering/localized-repair-c260/INPUTS.json",
        "docs/engineering/localized-repair-c267/hinge_compare.py",
        "docs/engineering/localized-repair-c266/hinge_binding.py",
        "docs/engineering/localized-repair-c265/source_hinges.py",
        "docs/engineering/localized-repair-c261/hinge_glb.py",
        "docs/engineering/localized-repair-c257/ownership.py",
    )}
    report = {
        "schema": "ontokin.c268.independent-review-probes/1",
        "reviewer": "/root/state_audit",
        "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip(),
        "source_tree": subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=repo, text=True).strip(),
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "probe_source": identity(Path(__file__).read_bytes()),
        "reviewed_inputs": source_inputs,
        "input_witnesses": {name: identity(raw) for name, raw in original.items()},
        "cases": [], "calls": {"public": 0, "successes": 0, "typed_refusals": 0, "unexpected": 0},
        "limits": ["Independent supplemental probes, not the full required cohort",
                   "Comparison-failure probe injects changed GLB after original admission to exercise fault translation",
                   "Concurrent calls test this finite process/environment only"],
    }
    lock = threading.Lock()
    def save():
        (out / "RESULTS.json").write_text(json.dumps(report, indent=2) + "\n")
    def public(mod, root, endpoint):
        with lock: report["calls"]["public"] += 1
        try:
            result = mod.read_bound_endpoint(root, endpoint)
        except mod.Fault:
            with lock: report["calls"]["typed_refusals"] += 1
            raise
        except Exception:
            with lock: report["calls"]["unexpected"] += 1
            raise
        with lock: report["calls"]["successes"] += 1
        return result
    def case(name, fn):
        row = {"name": name, "started_at_utc": datetime.now(timezone.utc).isoformat()}
        try:
            row["details"] = fn()
            row["passed"] = True
        except Exception as exc:
            row.update(passed=False, error_type=type(exc).__name__, error=str(exc), traceback=traceback.format_exc())
        report["cases"].append(row)
        save()
        print(json.dumps({"case": name, "passed": row["passed"]}), flush=True)
    def private():
        return sorted(n for n in sys.modules if n.startswith("_c268_"))
    def sources(endpoint):
        return {"main.ok": original[endpoint + ".main.ok"], "hinges.ok": original["hinges.ok"]}
    def normal(result):
        obj = dict(result)
        obj["schema"] = reader.COMPARISON_SCHEMA
        obj["historicalInputsBound"] = False
        for key in ("comparisonSchema", "endpoint", "historicalAdmission"): obj.pop(key)
        obj["limits"] = [reader.RAW_HISTORICAL_LIMIT if x == reader.BOUND_HISTORICAL_LIMIT else x for x in obj["limits"]]
        return obj
    def identities(exc, endpoint):
        assert exc.sourceHashes == {k: identity(v)["sha256"] for k, v in sources(endpoint).items()}
        assert exc.sourceBytes == {k: len(v) for k, v in sources(endpoint).items()}
        assert exc.artifactSha256 == identity(original[endpoint + ".glb"])["sha256"]
        assert exc.artifactBytes == len(original[endpoint + ".glb"])
        assert not any(hasattr(exc, k) for k in ("records", "sites", "hingeComparisonVerified"))
    def finite(result):
        assert result["hingeCount"] == 8 and result["siteCount"] == 16
        assert len({tuple(x["definitionId"]) for x in result["records"]}) == 1
        assert result["historicalInputsBound"] is True
        for key in ("sitePosesEvaluated", "sourceValidityQualified", "acceptedRevisionQualified",
                    "completeC255Semantic", "executionAllowed", "directSiteTableObserved", "jointDefinitionOrSpanObserved"):
            assert result[key] is False
        assert result["realTrialSuccess"] is None

    for endpoint in ("before", "after"):
        def parity(endpoint=endpoint):
            base = direct.compare_hinges(sources(endpoint), original[endpoint + ".glb"])
            modules_before = private()
            fd_before = len(os.listdir("/proc/self/fd"))
            result = public(reader, repo, endpoint)
            finite(result)
            assert normal(result) == base
            assert private() == modules_before
            assert len(os.listdir("/proc/self/fd")) == fd_before
            return {"endpoint": endpoint, "whole_comparison_equal": True, "hinges": 8, "sites": 16,
                    "private_modules_unchanged": True, "descriptors_unchanged": True}
        case("whole_result_parity_" + endpoint, parity)

    copy_eng = out / "copied-code/docs/engineering"
    copy_reader_path = copy_eng / "localized-repair-c268/endpoint_reader.py"
    copy_reader_path.parent.mkdir(parents=True)
    shutil.copyfile(reader_path, copy_reader_path)
    saved_code = {}
    for name, (relative, size, sha) in reader.DEPENDENCIES.items():
        path = copy_eng / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        code = (eng / relative).read_bytes()
        assert identity(code) == {"bytes": size, "sha256": sha}
        path.write_bytes(code)
        saved_code[name] = (path, code)
    copied = load(copy_reader_path, "_review_c268_copied")
    case("copied_closure_baseline", lambda: (finite(public(copied, repo, "before")) or {"passed": True}))

    def capture_path_swap():
        original_compare = copied._compare_captured
        calls = []
        def captured_only(code, sf, raw):
            assert set(code) == set(copied.DEPENDENCIES)
            for name, (path, content) in saved_code.items():
                path.unlink()
                path.symlink_to(out / "nonexistent-dependency")
            def forbidden(*args, **kwargs):
                calls.append(str(args[:1]))
                raise AssertionError("filesystem reopen after complete dependency capture")
            with patch("builtins.open", side_effect=forbidden), patch.object(Path, "open", side_effect=forbidden), patch.object(os, "open", side_effect=forbidden):
                return original_compare(code, sf, raw)
        with patch.object(copied, "_compare_captured", side_effect=captured_only):
            result = public(copied, repo, "before")
        finite(result)
        assert not calls and not private()
        return {"all_five_paths_replaced_after_capture": True, "filesystem_reopens": len(calls), "captured_comparison_passed": True}
    case("post_capture_all_dependency_paths_replaced", capture_path_swap)
    def reread_refusal():
        try: public(copied, repo, "before")
        except copied.Fault as exc:
            assert (exc.code, exc.reason) == ("INPUT_BINDING", "SYMLINK")
            identities(exc, "before")
            assert not private()
            return {"code": exc.code, "reason": exc.reason, "all_input_identities_retained": True}
        raise AssertionError("persistent cache bypassed per-call dependency admission")
    case("same_module_next_call_rejects_replaced_paths", reread_refusal)
    for path, code in saved_code.values():
        path.unlink()
        path.write_bytes(code)
    case("restored_paths_recover_without_reload", lambda: (finite(public(copied, repo, "after")) or {"passed": True}))

    for name, (path, code) in saved_code.items():
        def mutated(name=name, path=path, code=code):
            path.write_bytes(bytes([code[0] ^ 1]) + code[1:])
            compiled = []
            real_compile = compile
            def watched(raw, filename, *args, **kwargs):
                compiled.append(str(filename))
                return real_compile(raw, filename, *args, **kwargs)
            try:
                with patch("builtins.compile", side_effect=watched):
                    try: public(copied, repo, "before")
                    except copied.Fault as exc:
                        assert (exc.code, exc.reason, exc.pointer) == ("INPUT_BINDING", "HASH", "/dependencies/" + name)
                        identities(exc, "before")
                        assert compiled == [] and not private()
                        return {"dependency": name, "code": exc.code, "reason": exc.reason, "modules_compiled_before_refusal": 0}
                    raise AssertionError("changed pinned code was admitted")
            finally:
                path.write_bytes(code)
        case("complete_closure_before_compile_" + name, mutated)

    def fifo_dependency():
        path, code = saved_code["identity"]
        path.unlink()
        os.mkfifo(path)
        try:
            try: public(copied, repo, "after")
            except copied.Fault as exc:
                assert (exc.code, exc.reason) == ("INPUT_BINDING", "NOT_REGULAR")
                identities(exc, "after")
                assert not private()
                return {"last_dependency_fifo": True, "code": exc.code, "reason": exc.reason}
            raise AssertionError("FIFO admitted")
        finally:
            path.unlink()
            path.write_bytes(code)
    case("last_transitive_dependency_fifo_bounded_refusal", fifo_dependency)

    raw = original["before.glb"]
    length, kind = struct.unpack_from("<II", raw, 12)
    assert kind == 0x4e4f534a
    document = json.loads(raw[20:20+length])
    document["extras"]["ontokin"]["joints"][0]["initial"] = 0.125
    chunk = json.dumps(document, separators=(",", ":")).encode()
    chunk += b" " * (-len(chunk) % 4)
    tail = raw[20+length:]
    changed = struct.pack("<III", 0x46546c67, 2, 20+len(chunk)+len(tail)) + struct.pack("<II", len(chunk), kind) + chunk + tail
    (witness_dir / "changed-initial.glb").write_bytes(changed)
    report["input_witnesses"]["changed-initial.glb"] = identity(changed)
    def translated_failure():
        try: direct.compare_hinges(sources("before"), changed)
        except direct.Fault as expected:
            expected_fields = {k: getattr(expected, k) for k in ("code", "detail", "pointer", "origin")}
        else: raise AssertionError("direct comparator did not reject changed initial")
        assert expected_fields["code"] == "FIELD_MISMATCH"
        original_compare = copied._compare_captured
        def inject(code, sf, original_raw):
            return original_compare(code, sf, changed)
        fd_before = len(os.listdir("/proc/self/fd"))
        with patch.object(copied, "_compare_captured", side_effect=inject):
            try: public(copied, repo, "before")
            except copied.Fault as exc:
                assert {k: getattr(exc, k) for k in expected_fields} == expected_fields
                assert exc.reason == "COMPARISON"
                identities(exc, "before")
                assert not private() and len(os.listdir("/proc/self/fd")) == fd_before
                return {"predecessor_fields_equal": True, "fields": expected_fields,
                        "public_fault_records_original_admitted_bytes": True, "injected_changed_argument": True,
                        "no_private_module_or_fd_leak": True}
            raise AssertionError("injected comparison disagreement was lost")
    case("exact_comparison_fault_translation_and_cleanup", translated_failure)

    def concurrent():
        fd_before = len(os.listdir("/proc/self/fd"))
        endpoints = ["before", "after"] * 4
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda endpoint: public(copied, repo, endpoint), endpoints))
        for result in results: finite(result)
        assert not private() and len(os.listdir("/proc/self/fd")) == fd_before
        return {"calls": 8, "workers": 4, "all_admitted": True, "no_private_module_or_fd_leak": True}
    case("overlapping_calls_keep_private_modules_isolated", concurrent)

    report["source_revision_after"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    report["source_inputs_unchanged"] = all(identity((repo / name).read_bytes()) == expected for name, expected in source_inputs.items())
    report["private_modules_remaining"] = private()
    report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    report["passed"] = all(row["passed"] for row in report["cases"]) and report["source_inputs_unchanged"] and not private() and report["calls"]["unexpected"] == 0
    report["case_count"] = len(report["cases"])
    save()
    print(json.dumps({"passed": report["passed"], "case_count": report["case_count"], "calls": report["calls"]}), flush=True)
    return 0 if report["passed"] else 1

if __name__ == "__main__":
    raise SystemExit(main())

