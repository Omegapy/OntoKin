#!/usr/bin/env python3
"""Independent exact-byte C270 fixture review; no OntoKin execution or imports."""
from __future__ import annotations

import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
CONTROL = HERE.parents[1] / "control"
BASE = "254e481351239b536394c182b6761ec4c8662764"
FROZEN = {
    "main.ok": (1708, "f7e22c5bb8c42dadc475b970d16c1ce0503dc2333ed359387d85e5e6638b584d"),
    "hinges.ok": (1998, "dd5b49760121c0fe8ee5e707fe60e1d269be954896951f991887f195b0686e97"),
    "EXPECTED.json": (8605, "aa73df1e9ffb4d76bc589a7239f454be28e4cd6ae4ee523b208dbf66860ef4a7"),
    "SOURCE-VALIDITY.md": (7901, "0a966b5c8acd6bec75445199992babe0023fadb37d36bcd0d37fc36bf4257eb2"),
    "build_control.py": (9479, "f92eaf3e1ffeaf722fa8d71dbfda3a6961eb944f4dd85ab3426c4b51c7ad748d"),
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def identity(path):
    raw = path.read_bytes()
    return {"path": path.relative_to(REPO).as_posix(), "bytes": len(raw), "sha256": digest(raw)}


def main():
    checks = []

    def check(name, value, detail=None):
        checks.append({"name": name, "passed": bool(value), "detail": detail})

    raws = {name: (CONTROL / name).read_bytes() for name in FROZEN}
    expected = json.loads(raws["EXPECTED.json"])
    for name, raw in raws.items():
        check("independently reviewed freeze: " + name, (len(raw), digest(raw)) == FROZEN[name])
    for collection in ("original_inputs", "supplied_sources", "reference_identities"):
        for record in expected[collection]:
            raw = (REPO / record["path"]).read_bytes()
            check(collection + ": " + record["path"],
                  len(raw) == record["bytes"] and digest(raw) == record["sha256"])
            if collection != "supplied_sources":
                baseline = subprocess.check_output(["git", "show", BASE + ":" + record["path"]], cwd=REPO)
                check("exact baseline preservation: " + record["path"], raw == baseline)

    old_leaf = (REPO / "docs/engineering/semantic-export-c210/evidence/proof/hinges.ok").read_bytes()
    old_main = (REPO / "docs/engineering/semantic-export-c210/evidence/proof/before.main.ok").read_bytes()
    declaration = b'    private param parent_site_ref @ "parent-site-ref": SiteRef = self.pivot;\n'
    new_parent = b'        parent = self.parent_site_ref;\n'
    old_parent = b'        parent = self.pivot;\n'
    leaf = raws["hinges.ok"]
    check("exactly one new private typed declaration", leaf.count(declaration) == 1)
    check("exactly one changed parent assignment", leaf.count(new_parent) == 1)
    restored_leaf = leaf.replace(declaration, b"", 1).replace(new_parent, old_parent, 1)
    check("reverse only two declared edits recovers entire original leaf", restored_leaf == old_leaf)
    new_pin = ("sha256:" + digest(leaf)).encode("ascii")
    old_pin = ("sha256:" + digest(old_leaf)).encode("ascii")
    check("exact dependency pin", raws["main.ok"].count(new_pin) == 1)
    check("reverse only pin recovers entire original main", raws["main.ok"].replace(new_pin, old_pin, 1) == old_main)
    check("name/key absent in baseline", b"parent_site_ref" not in old_leaf and b"parent-site-ref" not in old_leaf)
    check("parameter has declaration and one same-class read", leaf.count(b"parent_site_ref") == 2)
    check("stable key is unique", leaf.count(b'"parent-site-ref"') == 1)
    check("declaration adjacent to existing class joint", declaration + b'    public joint flex @ "flex": hinge {' in leaf)
    check("no new callable source form", b"site(" not in leaf)
    check("new key satisfies adopted grammar", re.fullmatch(rb"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", b"parent-site-ref") is not None)
    check("reference uses valid UTF-8 bytes", leaf.decode("utf-8").encode("utf-8") == leaf)
    check("expected new import pin", expected["import"]["new_digest"].encode("ascii") == new_pin)
    hashes = {name: digest(raws[name]) for name in ("main.ok", "hinges.ok")}
    for api in ("observe_source_hinges", "compare_hinges"):
        oracle = expected["expected"][api]
        check(api + " independent exact category", oracle["exact_code"] == "UNSUPPORTED_SOURCE_FORM")
        check(api + " typed refusal required", oracle["outcome"] == "typed_refusal")
        check(api + " exact source identities", oracle["input_source_hashes_retained"] == hashes)
        check(api + " reason required", oracle["nonempty_reason_required"] is True)
        check(api + " partial qualified set forbidden", oracle["partial_qualified_set_allowed"] is False)
        check(api + " no qualified hinges/sites", oracle["qualified_hinge_count"] == 0 and oracle["qualified_site_count"] == 0)
    check("MALFORMED is explicitly not equivalent", expected["expected"]["observe_source_hinges"]["malformed_is_not_acceptable"] is True)
    check("source success forbidden", expected["expected"]["observe_source_hinges"]["source_success_allowed"] is False)
    check("comparison agreement forbidden", expected["expected"]["compare_hinges"]["agreement_allowed"] is False)
    check("comparison failure must originate in source", expected["expected"]["compare_hinges"]["source_failure_origin_required"] is True)
    artifact = expected["comparison_input"]
    raw_artifact = (REPO / artifact["path"]).read_bytes()
    check("unchanged artifact identity", artifact["sha256"] == digest(raw_artifact) and artifact["bytes"] == len(raw_artifact))
    check("stale provenance explicitly disclosed", artifact["source_matched"] is False and artifact["provenance_rebound"] is False and artifact["agreement_expected"] is False)
    check("expected artifact identity matches supplied raw", expected["expected"]["compare_hinges"]["input_artifact_sha256_retained"] == digest(raw_artifact))

    reference = expected["program_identity_reference"]
    manifest = {"schema_version": "ontokin.bundle/0.1", "entry_source_id": "entry", "units": [
        {"source_id": "entry", "package_id": None, "version": None, "filename": "main.ok", "source_revision": "sha256:" + hashes["main.ok"]},
        {"source_id": "package:example.hinges@1.0.0", "package_id": "example.hinges", "version": "1.0.0", "filename": "hinges.ok", "source_revision": "sha256:" + hashes["hinges.ok"]},
    ]}
    check("independent canonical manifest", reference["manifest"] == manifest)
    canonical = json.dumps(manifest, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
    check("independent program revision", reference["program_revision"] == "sha256:" + digest(b"ontokin.bundle/0.1\0" + canonical))

    builder = ast.parse(raws["build_control.py"].decode("utf-8"))
    imports = set()
    for node in ast.walk(builder):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add(node.module)
    check("builder imports only reviewed stdlib modules", imports == {"__future__", "argparse", "hashlib", "json", "pathlib"}, sorted(imports))
    check("builder has no dynamic execution/import calls", not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"eval", "exec", "__import__"} for node in ast.walk(builder)))
    report = {
        "schema": "ontokin.c270.independent-fixture-checks/1", "reviewer": "/root/reconcile",
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(), "baseline": BASE,
        "command": [sys.executable, *sys.argv], "environment": {"python": sys.version, "platform": platform.platform()},
        "script": identity(Path(__file__).resolve()), "fixture_identities": [identity(CONTROL / name) for name in FROZEN],
        "checks": checks, "check_count": len(checks), "passed": all(c["passed"] for c in checks),
        "failed_checks": [c["name"] for c in checks if not c["passed"]],
        "execution_limits": {"observer_calls": 0, "product_parser_evaluator_exporter_calls": 0, "native_or_model_calls": 0},
        "semantic_review": "Manual adopted-rule proof approved for this exact two-edit source transformation; byte assertions do not substitute for semantic reasoning or establish product validation.",
    }
    destination = HERE / "PREEXEC-FIXTURE-CHECKS.json"
    if destination.exists():
        raise FileExistsError("Do not overwrite an earlier review run")
    destination.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": report["passed"], "checks": len(checks), "failed": report["failed_checks"], "output": str(destination.relative_to(REPO))}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
