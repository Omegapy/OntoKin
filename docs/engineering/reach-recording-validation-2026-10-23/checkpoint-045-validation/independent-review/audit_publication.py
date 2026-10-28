#!/usr/bin/env python3
"""Independent C045 metadata/source audit; no product or archived code execution."""
import argparse
import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import traceback
import zipfile

CORE = "f2ed86eddcf37215fc134c5bb0ee9dce9bbd9d2b"
TREE = "64f80e946d8f498bfc96ad75fd010315c0a9ecc5"
PARENT = "91e8899ad90f04292dd4aee5aaec8b730b397d45"
PARENT_TREE = "11d1ce9acc2cb4fa93be44c4772a9e8e3b3270ff"
BASE = Path("docs/engineering/reach-recording-validation-2026-10-23")

def digest(b):
    return hashlib.sha256(b).hexdigest()

def object_id(kind, b):
    return hashlib.sha1(kind.encode() + b" " + str(len(b)).encode() + b"\0" + b).hexdigest()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--support", type=Path, required=True)
    p.add_argument("--retained", type=Path, required=True)
    args = p.parse_args()
    out = Path(__file__).resolve().parent
    assert out == args.repo / BASE / "checkpoint-045-validation/independent-review"
    started = datetime.now(timezone.utc)
    checks, bindings = [], []
    summary = {}
    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append(name)
    def save(name, value):
        target = out / name
        if target.exists():
            raise ValueError("Refuse to overwrite audit output: " + name)
        target.write_text(json.dumps(value, indent=2) + "\n")
    def read(path):
        b = path.read_bytes()
        bindings.append({"path": str(path), "bytes": len(b), "sha256": digest(b)})
        return b
    def load(path):
        return json.loads(read(path))
    def git(*items):
        return subprocess.check_output(["git", "-C", str(args.repo), *items],
            env={**os.environ, "GIT_OPTIONAL_LOCKS": "0", "PYTHONDONTWRITEBYTECODE": "1"})
    def records_by_path(rows):
        return {row["path"]: row for row in rows}
    def normalize_tree(rows):
        return {e["path"]: {"path": e["path"], "mode": e["mode"],
                           "bytes": e["size"], "blob": e["sha"]}
                for e in rows if e["type"] == "blob"}

    try:
        window = load(out / "audit-window.json")
        expiry = datetime.fromisoformat(re.search(r"expiring ([0-9T:.-]+Z)", window["body"]).group(1).replace("Z", "+00:00"))
        created = datetime.fromisoformat(window["created_at"].replace("Z", "+00:00"))
        check("actual independent audit starts inside exclusive window", created <= started < expiry)
        commit = load(out / "remote-core-commit.json")
        tree = load(out / "remote-core-tree.json")
        ref = load(out / "remote-owned-ref.json")
        check("independent remote core commit/tree/parent binding", commit["sha"] == CORE and commit["tree"]["sha"] == TREE
              and [x["sha"] for x in commit["parents"]] == [PARENT] and tree["sha"] == TREE and not tree["truncated"])
        check("independent owned branch read points to core", ref["object"]["sha"] == CORE)
        check("actual local Git head/tree match published core", git("rev-parse", "HEAD").decode().strip() == CORE
              and git("rev-parse", "HEAD^{tree}").decode().strip() == TREE)
        raw = read(args.support / "core.commit")
        check("actual original core commit bytes match both Git and remote", object_id("commit", raw) == CORE
              and git("cat-file", "commit", CORE) == raw)
        remote_files = normalize_tree(tree["tree"])
        parent_meta = load(args.support / "parent-tree.json")
        parent_files = normalize_tree(parent_meta["tree"])
        check("complete parent map retained unchanged in core", len(parent_files) == 2356
              and sum(x["bytes"] for x in parent_files.values()) == 490821760
              and all(remote_files.get(k) == v for k, v in parent_files.items()))
        new = sorted(set(remote_files) - set(parent_files))
        check("41 new files remain inside owned C045 scope", len(new) == 41 and all(
              name.startswith(str(BASE / "checkpoint-045")) or name == str(BASE / "HANDOFF-045.md") for name in new))
        def inventory():
            result = []
            for name in sorted(remote_files):
                e = remote_files[name]
                path = args.repo / name
                assert path.is_file() and not path.is_symlink(), name
                b = path.read_bytes()
                row = {"path": name, "mode": "100" + format(stat.S_IMODE(path.stat().st_mode), "03o"),
                       "bytes": len(b), "blob": object_id("blob", b), "sha256": digest(b)}
                assert all(row[k] == e[k] for k in e), name
                result.append(row)
            return result
        before = inventory()
        save("inputs-before.json", before)
        check("every physical core file matches remote blob/mode/size", len(before) == 2397
              and sum(x["bytes"] for x in before) == 493496287)
        current = records_by_path(before)
        parent_raw = read(args.repo / BASE / "checkpoint-045-evidence/recovery/parent.commit")
        check("original parent commit representation preserved", object_id("commit", parent_raw) == PARENT
              and parent_raw.startswith(("tree " + PARENT_TREE + "\n").encode()))
        held = load(out / "held-runtime-remote.json")
        check("all65 runtime modules independently match held C035", held["commit"] == "4ca73909f861fe4bef9694787473621c1d21c140"
              and len(held["native"]) == 65 and all(all(current[x["path"]][key] == x[key]
                  for key in ("mode", "bytes", "blob")) for x in held["native"]))

        manifest = load(args.repo / BASE / "checkpoint-045-evidence-manifest.json")
        actual_evidence = {name for name in new if name.startswith(str(BASE / "checkpoint-045-evidence") + "/")}
        claimed_evidence = {str(BASE / row["path"]) for row in manifest["members"]}
        check("C045 evidence manifest closes exact core evidence file set", len(claimed_evidence) == len(manifest["members"])
              == manifest["files"] and actual_evidence == claimed_evidence)
        for row in manifest["members"]:
            b = read(args.repo / BASE / row["path"])
            assert len(b) == row["bytes"] and digest(b) == row["sha256"], row["path"]
        check("all C045 evidence members have exact lengths and hashes", sum(x["bytes"] for x in manifest["members"]) == manifest["bytes"])
        reviews = load(args.repo / BASE / "checkpoint-045-reviews.json")
        for row in reviews["reviews"]:
            b = read(args.repo / BASE / row["path"])
            assert len(b) == row["bytes"] and digest(b) == row["sha256"]
        check("four independent-review files match indexed hashes", len(reviews["reviews"]) == 4)
        check("design participation disclosure is retained", "contributed" in reviews["independence"]["cost"])

        archive = load(args.repo / BASE / "checkpoint-044-evidence-manifest.json")
        pieces = []
        for row in archive["archive"]["parts"]:
            b = read(args.repo / BASE / row["path"])
            assert len(b) == row["bytes"] and digest(b) == row["sha256"]
            pieces.append(b)
        joined = b"".join(pieces)
        check("all nine C044 parts reconstruct original archive", len(pieces) == 9 and len(joined) == archive["archive"]["bytes"] == 6401045
              and digest(joined) == archive["archive"]["sha256"])
        expected_members = {x["path"]: x for x in archive["members"]}
        member_records = []
        with zipfile.ZipFile(io.BytesIO(joined)) as z:
            check("C044 exact member set and all CRCs verify", len(z.infolist()) == len(expected_members) == 99
                  and set(z.namelist()) == set(expected_members) and z.testzip() is None)
            for info in z.infolist():
                name = PurePosixPath(info.filename)
                assert not name.is_absolute() and ".." not in name.parts and not info.is_dir()
                row = expected_members[info.filename]
                b = z.read(info)
                assert len(b) == row["bytes"] and digest(b) == row["sha256"]
                assert stat.S_IMODE(info.external_attr >> 16) == row["mode"]
                path = args.retained / info.filename
                assert not path.is_symlink() and path.read_bytes() == b
                assert stat.S_IMODE(path.stat().st_mode) == row["mode"] and path.stat().st_mtime_ns == row["mtime_ns"]
                member_records.append({"path": info.filename, "bytes": len(b), "sha256": digest(b), "mode": row["mode"],
                                       "mtime_ns": row["mtime_ns"]})
        check("all99 actual restored members preserve bytes/modes/times", sum(x["bytes"] for x in member_records) == 49758827)
        save("c044-member-verification.json", member_records)

        analysis = load(args.repo / BASE / "checkpoint-045-evidence/analysis/analysis-002.json")
        fresh = load(args.support / "core-validation/source-data-result.json")
        check("original and published-core audits both retain49 checks", analysis["checks_passed"] == fresh["checks_passed"] == 49
              and analysis["status"] == fresh["status"] == "passed" and analysis["checks_failed"] == fresh["checks_failed"] == 0)
        independent_fields = [key for key in analysis if key not in ("started_utc", "finished_utc", "python", "platform")]
        check("fresh core source-data result agrees with first successful audit", all(analysis[key] == fresh[key] for key in independent_fields))
        actual_script = read(args.repo / BASE / "checkpoint-045-audit.py")
        executed_copy = read(args.repo / BASE / "checkpoint-045-evidence/analysis/audit-v002.py")
        check("published metadata audit matches retained executed version", actual_script == executed_copy)
        for row in analysis["inputs"]:
            path = (args.repo if row["root"] == "repo" else args.retained) / row["path"]
            b = read(path)
            assert len(b) == row["bytes"] and digest(b) == row["sha256"], row["path"]
        check("all15 actual source-data input bindings match available bytes", len(analysis["inputs"]) == 15)

        trace = load(args.retained / "c044-execution/pair-001/capture/trace.json")
        equality = load(args.retained / "c044-analysis/cache-review/attempt-001/key-equality.json")
        checkpoints = load(args.retained / "c044-analysis/cache-review/attempt-001/ordered-cache-checkpoints.json")
        census = load(args.repo / BASE / "checkpoint-044-census.json")
        keyclasses = {int(k): v for k, v in equality["key_to_equality_class"].items()}
        check("original key replay uses hash-bound identity equality classes", len(keyclasses) == 823
              and all(k == v for k, v in keyclasses.items()) and not equality["typed_alias_groups"])
        order, calls, observed, mutations, lookups = [], {}, {}, Counter(), Counter()
        for ordinal, event in enumerate(trace["events"], 1):
            assert event["event_id"] == ordinal
            if event["event"] == "cache_mutation_completed":
                op, key = event["mutation"]["operation"], event["mutation"]["key_id"]
                if op == "set":
                    if key not in order: order.append(key)
                elif op == "promote":
                    order.remove(key); order.append(key)
                elif op == "evict":
                    assert order[0] == key; order.pop(0)
                else: raise AssertionError(op)
                mutations[op] += 1
            assert len(order) == event["mark"]["cache_entries"]
            if event.get("kind") == "envelope":
                if event["event"] == "call":
                    calls[ordinal] = event["invocation_id"]
                    observed["envelope_" + str(event["invocation_id"]) + "_entry"] = list(order)
                elif event["event"] == "return":
                    observed["envelope_" + str(calls[event["call_event"]]) + "_exit"] = list(order)
            if event.get("kind") == "lookup" and event["event"] == "return":
                lookups[event["lookup_outcome"]] += 1
        check("independent original-order replay matches64 recorded boundaries", observed == checkpoints["envelopes"] and len(observed) == 64)
        check("independent original final-order and mutation totals match", order == checkpoints["final"]
              and mutations == {"set": 1219, "promote": 4190, "evict": 768} and len(trace["events"]) == 46721)
        check("original final refusal remains before membership", lookups == {"hit": 3995, "miss": 1058, "refusal_before_membership": 1}
              and trace["events"][-1]["membership_attempted"] is False)
        check("current group has32 completed cold calls at full cache", len(census["invocations"]) == 32 and all(
              r["status"] == "completed" and r["entry"]["cache_entries"] == 256
              and r["lookup"]["return_event"]["lookup_outcome"] == "miss" for r in census["invocations"]))

        # Independent symbolic width propagation from the original source AST.
        # This evaluates integer bit bounds only; no product formula or Fraction is executed.
        fast = ast.parse((args.repo / "ontokin/reach_recording_fast.py").read_text())
        target = next(x for x in fast.body if isinstance(x, ast.FunctionDef) and x.name == "recording_float_excess")
        assignments = {x.targets[0].id: x.value for x in target.body if isinstance(x, ast.Assign)
                       and len(x.targets) == 1 and isinstance(x.targets[0], ast.Name)}
        def constant(n):
            if isinstance(n, ast.Constant) and type(n.value) is int: return n.value
            if isinstance(n, ast.Name) and n.id == "MAX_RECORDING_ROTATION_STEPS": return 10000
            if isinstance(n, ast.BinOp):
                a,b=constant(n.left),constant(n.right)
                if isinstance(n.op,ast.Pow):return a**b
                if isinstance(n.op,ast.Sub):return a-b
                if isinstance(n.op,ast.LShift):return a<<b
            raise AssertionError(ast.dump(n))
        widths={"t":(2048,1),"c":(2048,1),"sq":(2048,2048),"AXIS_ERROR":(1,75),"PRODUCT_ERROR":(1,92)}
        steps=[]
        def symbol(n):
            if isinstance(n,ast.Name):return widths[n.id]
            assert isinstance(n,ast.Call) and isinstance(n.func,ast.Name),ast.dump(n)
            if n.func.id=="F":
                if len(n.args)==1 and isinstance(n.args[0],ast.Name) and n.args[0].id in ("t","c"):return widths[n.args[0].id]
                a=constant(n.args[0]);b=constant(n.args[1]) if len(n.args)>1 else 1
                return abs(a).bit_length(),abs(b).bit_length()
            assert n.func.id=="op"
            a,b= symbol(n.args[0]),symbol(n.args[1]);op=n.args[2].value
            if op=="add":v=(max(a[0]+b[1],b[0]+a[1])+1,a[1]+b[1])
            elif op=="mul":v=(a[0]+b[0],a[1]+b[1])
            else:raise AssertionError(op)
            steps.append({"operation":op,"left":a,"right":b,"bound":v})
            return v
        for name in ("source_leaves","e","g","q"):widths[name]=symbol(assignments[name])
        check("independent AST width derivation has13 prefix sites",len(steps)==13)
        check("independent AST width bounds reproduce4327 maximum",max(max(x["bound"]) for x in steps)==4327
              and [widths[n] for n in ("source_leaves","e","g","q")]==[(2050,2),(2102,94),(2157,170),(4327,2314)])
        save("independent-symbolic-widths.json",{"input_integer_field_bound":2048,"original_cap":32768,"steps":steps,
             "completed":{n:widths[n] for n in ("source_leaves","e","g","q")},"product_arithmetic_executed":False})

        ledger=load(args.repo/BASE/"checkpoint-045-cost-ledger.json")
        check("schedule-specific negative upper bound and screen are coherent",13*(32-1)==403 and 2*256==512
              and ledger["forced_admitted_route"]["saving_upper_bound"]==-109
              and ledger["screen"]["passes"] is False and ledger["rejected_route"]["prefix_reuses"]==0
              and ledger["rejected_route"]["full_entry_audit_executed"] is False
              and ledger["positive_complete_bound_established"] is False
              and ledger["universal_angular_impossibility_claimed"] is False)
        check("late sensitivity and41-call necessary threshold are correct",14*31-512==-78 and 13*39<=512<13*40)
        check("unknown entry categories remain unknown",ledger["entry_category_count"] is None and analysis["entry_category_count"] is None)
        nextscope=load(args.repo/BASE/"checkpoint-045-next-scope.json")
        check("next scope remains source-only L03 with original64-update constraint",nextscope["next_checkpoint"]=="C046"
              and "source and retained evidence only" in nextscope["immediate_mode"]
              and "64-update limit and required direct seed" in nextscope["preserve"])
        findings=load(args.repo/BASE/"checkpoint-045-evidence/preparation/attempts.json")
        check("first audit failure remains preserved", "KeyError: 'invocation_id'" in
              read(args.repo/BASE/"checkpoint-045-evidence/analysis/analysis-001.stderr").decode()
              and any(x["operation"]=="source/data audit001" and x["exit_code"]==1 for x in findings["failures"]))
        check("metadata builder failure and transcript limit remain explicit",any(x["operation"]=="core metadata builder001"
              and x["exit_code"]==1 and "tool transcript" in x["captured_log_qualification"] for x in findings["failures"]))
        pubfail=load(args.support/"publication-preparation-attempts.json")
        retry=load(args.support/"blob-upload-retry.json")
        check("publication-preparation and reconciled blob-upload failures disclosed",pubfail[0]["exit_code"]==1
              and pubfail[1]["exit_code"]==0 and "terminal blank line" in pubfail[0]["outcome"]
              and "404" in retry["error"])
        cleanup=load(args.repo/BASE/"checkpoint-045-evidence/recovery/authenticated-url-cleanup.json")
        check("all23 signed-URL input inventories remain absent",len(cleanup["removed"])==23
              and cleanup["all23_absent_after_removal"] and all(not Path(x["path"]).exists() for x in cleanup["removed"]))

        validation=load(args.support/"core-validation/result.json")
        root_before=load(args.support/"core-validation/inputs-before.json")
        root_after=load(args.support/"core-validation/inputs-after.json")
        check("actual root core-validation inputs match full current core",root_before==root_after
              and records_by_path(root_before)==current and validation["source_commit"]==CORE and validation["source_tree"]==TREE
              and validation["source_files"]==2397 and validation["source_bytes"]==493496287)
        for command in validation["commands"]:
            assert command["exit_code"]==0 and command["source_commit"]==CORE and command["source_tree"]==TREE
            for label in ("stdout","stderr"):
                b=read(args.support/"core-validation"/command[label])
                assert len(b)==command[label+"_bytes"] and digest(b)==command[label+"_sha256"]
        check("actual two command receipts bind exact logs and successful exits",len(validation["commands"])==2)
        docs=load(args.support/"core-validation/documentation.stdout")
        check("actual unchanged documentation result supports report counts",docs["status"]=="passed" and not docs["failures"]
              and docs["sources_verified"]==29 and docs["sections_verified"]==233
              and docs["links"]["documents"]==197 and docs["links"]["local_links"]==1627 and docs["links"]["anchors"]==92)
        check("documentation checker remains exact parent source",remote_files["docs/maintenance/reorganization-2026-10-17/verify_reorganization.py"]
              ==parent_files["docs/maintenance/reorganization-2026-10-17/verify_reorganization.py"])
        secret_patterns=[re.compile(rb"[?&](?:token|access_token|signature|X-Amz-Signature)=[A-Za-z0-9._~%+-]{12,}",re.I),
                         re.compile(rb"(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})")]
        check("defined credential patterns absent from41 new core files",not any(pat.search((args.repo/name).read_bytes())
              for name in new for pat in secret_patterns))

        after=inventory()
        save("inputs-after.json",after)
        check("all2397 core files remain identical throughout audit",before==after)
        check("actual core head/tree remain unchanged",git("rev-parse","HEAD").decode().strip()==CORE
              and git("rev-parse","HEAD^{tree}").decode().strip()==TREE)
        check("audit completes within exclusive window",datetime.now(timezone.utc)<expiry)
        summary={"schema":"ontokin.checkpoint045-independent-publication-audit/0.1","status":"passed",
          "reviewer":"/root/source_recovery","started_utc":started.isoformat(),"finished_utc":datetime.now(timezone.utc).isoformat(),
          "source_commit":CORE,"source_tree":TREE,"source_files":len(before),"source_bytes":sum(x["bytes"] for x in before),
          "parent_files_preserved":2356,"new_core_files":len(new),"native_modules_equal_held":65,
          "c045_manifest_members":len(manifest["members"]),"c044_archive_members":99,"c044_member_bytes":49758827,
          "original_trace_events":46721,"original_mutations":6177,"original_envelope_orders":64,
          "independent_prefix_max_bits":4327,"prefix_gross_ceiling":403,"defined_audit_charge_floor":512,
          "forced_route_saving_upper_bound":-109,"proper_screen_declines":True,
          "checks_passed":len(checks),"checks":checks,"findings":[],
          "independence_disclosure":"Reviewer performed source acquisition earlier, but did not author the C045 candidate/report, root census audit or authority/cost reviews. This final audit independently fetched remote identities and rechecked physical files, manifests, archive and original order/AST bounds.",
          "limits":["The audit checks the published core, not its future validation appendix or eventual final containing commit.",
                    "No product, runtime test, archived driver, candidate numerical replay or complete request executed.",
                    "Original key-order replay relies on C044's already reviewed native-equality mapping; it is not a new equality proof.",
                    "The negative bound is specific to the named two-admissions-per-entry schedule, not universal angular-cache impossibility.",
                    "Transcript-only preparation failures retain that qualification; no missing original log was fabricated.",
                    "Credential scan covers defined patterns in the41 new core files, not a universal secret-absence proof.",
                    "Original28 remains24/28, C035 held, and full release/GOAL gates remain open."],
          "root_documentation_command_reexecuted":False,"root_audit_script_reexecuted":False,
          "product_imports_requests_tests_or_candidate_replays":0,"remote_writes":0}
        save("result.json",summary)
        save("input-bindings.json",bindings)
        print(json.dumps({k:summary[k] for k in ("status","checks_passed","source_commit","source_files","source_bytes",
            "c044_archive_members","forced_route_saving_upper_bound")}))
    except BaseException as error:
        failure={"status":"failed","started_utc":started.isoformat(),"finished_utc":datetime.now(timezone.utc).isoformat(),
                 "checks_completed":checks,"error_type":type(error).__name__,"message":str(error),"traceback":traceback.format_exc()}
        if not (out/"failure.json").exists():save("failure.json",failure)
        raise

if __name__=="__main__":
    main()

