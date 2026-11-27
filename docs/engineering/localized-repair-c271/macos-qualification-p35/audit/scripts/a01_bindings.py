"""W4 audit 001, a01: item 1, the bindings, recomputed with this auditor's own code.

Usage: a01_bindings.py FREEZE FREEZE_SHA256 OUTPUT
Reads only (no process creation: an audit hook refuses it). Writes OUTPUT by exclusive creation.

Checks:
  - FREEZE-002.json's SHA-256, then every one of its bindings (kind, SHA-256, size, mode, one link,
    canonical spelling), the host fact, and the evidence ancestors;
  - both freezes' SHA256SUMS.txt and P00's second list, line by line, and the tooling digest list;
  - every descriptor {path, sha256, size_bytes, mode} found in the cohort configuration, HOST, the
    methods and discovery documents, the dependency inventory and the per-row probe configurations;
  - the reader tree against the dependency inventory and the historical 24-file binding;
  - the source inventory, file by file, against the worktree, and its file set against the probe's
    own source rules (SOURCE_TREES, SOURCE_REQUIRED, SOURCE_OPTIONAL);
  - the Python installation inventory, entry by entry, against the framework and venv trees;
  - the inputs that each Node start of S7 used, from its records.
"""
import ast
import hashlib
import json
import os
import re
import stat
import sys


def _refuse(event, args):
    if event in ("subprocess.Popen", "os.posix_spawn", "os.exec", "os.fork", "os.forkpty", "os.spawn",
                 "os.system", "os.startfile"):
        raise PermissionError("this audit script starts no process: " + event)


sys.addaudithook(_refuse)


def sha256_file(path):
    digest = hashlib.sha256()
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        while True:
            block = os.read(fd, 1 << 20)
            if not block:
                break
            digest.update(block)
    finally:
        os.close(fd)
    return digest.hexdigest()


def mode_text(st_mode):
    return "0o%03o" % stat.S_IMODE(st_mode)


def describe(path):
    """kind, sha256, size, mode, nlink of a path, links not followed."""
    try:
        info = os.lstat(path)
    except OSError as error:
        return {"exists": False, "error": error.__class__.__name__}
    result = {"exists": True, "mode": mode_text(info.st_mode), "nlink": info.st_nlink, "size_bytes": info.st_size,
              "mtime_ns": info.st_mtime_ns}
    if stat.S_ISLNK(info.st_mode):
        result["kind"] = "symlink"
        result["target"] = os.readlink(path)
    elif stat.S_ISDIR(info.st_mode):
        result["kind"] = "directory"
    elif stat.S_ISREG(info.st_mode):
        result["kind"] = "file"
        result["sha256"] = sha256_file(path)
    else:
        result["kind"] = "special"
    return result


def spelled_on_disk(path):
    current = "/"
    for part in [p for p in path.split("/") if p]:
        try:
            if part not in os.listdir(current):
                return False
        except OSError:
            return False
        current = os.path.join(current, part)
    return True


def check_binding(row):
    path = row["path"]
    seen = describe(path)
    problems = []
    if not seen["exists"]:
        problems.append("absent")
    else:
        if os.path.realpath(path) != path or os.path.normpath(path) != path:
            problems.append("not canonical")
        if not spelled_on_disk(path):
            problems.append("not spelled as on disk")
        if seen["kind"] != row.get("kind", "file"):
            problems.append("kind " + seen["kind"])
        if seen["kind"] == "file":
            for key in ("sha256", "size_bytes", "mode"):
                if key in row and seen[key] != row[key]:
                    problems.append(key + " differs")
            if row.get("nlink_one") and seen["nlink"] != 1:
                problems.append("more than one link")
    return {"id": row.get("id"), "path": path, "ok": not problems, "problems": problems,
            "observed": {k: seen.get(k) for k in ("kind", "sha256", "size_bytes", "mode", "nlink")}}


def find_descriptors(document, where=""):
    """Every dict with path and sha256 (and optionally size_bytes and mode), with its JSON pointer."""
    found = []
    if isinstance(document, dict):
        if isinstance(document.get("path"), str) and isinstance(document.get("sha256"), str) \
                and re.fullmatch(r"[0-9a-f]{64}", document["sha256"]):
            found.append((where, document))
        for key, value in document.items():
            found.extend(find_descriptors(value, where + "/" + str(key).replace("~", "~0").replace("/", "~1")))
    elif isinstance(document, list):
        for index, value in enumerate(document):
            found.extend(find_descriptors(value, where + "/" + str(index)))
    return found


def check_descriptor(descriptor):
    seen = describe(descriptor["path"])
    problems = []
    if not seen["exists"]:
        problems.append("absent")
    elif seen["kind"] != "file":
        problems.append("kind " + seen["kind"])
    else:
        if seen["sha256"] != descriptor["sha256"]:
            problems.append("sha256 differs")
        if "size_bytes" in descriptor and seen["size_bytes"] != descriptor["size_bytes"]:
            problems.append("size differs")
        if "mode" in descriptor and seen["mode"] != descriptor["mode"]:
            problems.append("mode differs")
    return {"path": descriptor["path"], "ok": not problems, "problems": problems, "observed_sha256": seen.get("sha256")}


def check_document_descriptors(path, label):
    with open(path, "rb") as handle:
        document = json.loads(handle.read())
    rows = []
    for pointer, descriptor in find_descriptors(document):
        rows.append(dict(check_descriptor(descriptor), pointer=pointer))
    return {"document": path, "label": label, "count": len(rows), "failed": [r for r in rows if not r["ok"]],
            "rows": rows}


def parse_sums(path, base):
    rows = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            match = re.fullmatch(r"([0-9a-f]{64}) [ *](.+)", line)
            if not match:
                rows.append({"line": line, "ok": False, "reason": "malformed"})
                continue
            digest, name = match.groups()
            target = name if name.startswith("/") else os.path.join(base, name)
            seen = describe(target)
            ok = seen["exists"] and seen["kind"] == "file" and seen["sha256"] == digest
            rows.append({"name": name, "ok": ok, "expected": digest, "observed": seen.get("sha256")})
    return rows


def walk_tree(root, exclude=()):
    """Relative path -> describe(), links not followed; excluded absolute paths are skipped."""
    entries = {}
    stack = [root]
    while stack:
        current = stack.pop()
        for name in sorted(os.listdir(current)):
            full = os.path.join(current, name)
            if full in exclude:
                continue
            rel = os.path.relpath(full, root)
            seen = describe(full)
            entries[rel] = seen
            if seen["kind"] == "directory":
                stack.append(full)
    return entries


def main():
    freeze_path, freeze_sha, output = sys.argv[1], sys.argv[2], sys.argv[3]
    report = {"schema": "w4-audit-001.a01-bindings/1"}
    observed_freeze = sha256_file(freeze_path)
    report["freeze"] = {"path": freeze_path, "expected": freeze_sha, "observed": observed_freeze,
                        "ok": observed_freeze == freeze_sha, "size_bytes": os.lstat(freeze_path).st_size}
    with open(freeze_path, "rb") as handle:
        freeze = json.loads(handle.read())
    places = freeze["places"]
    wt, local = places["worktree"], places["local"]

    # 1. The 122 bindings and the host fact.
    rows = [check_binding(row) for row in freeze["bindings"]]
    report["bindings"] = {"count": len(rows), "ids_unique": len({r["id"] for r in rows}) == len(rows),
                          "failed": [r for r in rows if not r["ok"]], "rows": rows}
    report["host_facts"] = [check_binding(row) for row in freeze["host_facts"]]
    ancestors = []
    current = freeze["evidence"]["parent"]
    while True:
        info = os.lstat(current)
        ancestors.append({"path": current, "device": info.st_dev, "inode": info.st_ino, "mode": mode_text(info.st_mode),
                          "is_link": stat.S_ISLNK(info.st_mode)})
        if current == "/":
            break
        current = os.path.dirname(current)
    ancestors.sort(key=lambda row: row["path"])
    frozen_ancestors = sorted(freeze["evidence"]["ancestors"], key=lambda row: row["path"])
    report["evidence_ancestors"] = {"ok": [{k: a[k] for k in ("path", "device", "inode", "mode")} for a in ancestors]
                                    == frozen_ancestors and not any(a["is_link"] for a in ancestors),
                                    "observed": ancestors}

    # 2. Digest lists.
    f2 = places["freeze"]
    f1 = places["freeze_001"]
    sums = {}
    sums["W2-freeze-002/SHA256SUMS.txt"] = parse_sums(os.path.join(f2, "SHA256SUMS.txt"), f2)
    sums["W2-freeze-002/s7/p00-freeze-001-rebound.sha256sums.txt"] = parse_sums(
        os.path.join(f2, "s7/p00-freeze-001-rebound.sha256sums.txt"), f2)
    sums["W2-freeze-001/SHA256SUMS.txt"] = parse_sums(os.path.join(f1, "SHA256SUMS.txt"), f1)
    tooling_sums = os.path.join(wt, "docs/engineering/localized-repair-c271/macos-qualification-p35/authoring/TOOLING-SHA256SUMS.txt")
    tooling_base = os.path.join(wt, "docs/engineering/localized-repair-c271/macos-qualification-p35/tooling")
    sums["authoring/TOOLING-SHA256SUMS.txt"] = parse_sums(tooling_sums, tooling_base)
    report["digest_lists"] = {name: {"lines": len(value), "failed": [r for r in value if not r["ok"]]}
                              for name, value in sums.items()}
    # Every file of each freeze directory listed, and none newer than its list.
    unlisted = {}
    for name, base in (("W2-freeze-002", f2), ("W2-freeze-001", f1)):
        listed = {r["name"] for r in sums[name + "/SHA256SUMS.txt"] if "name" in r}
        sums_mtime = os.lstat(os.path.join(base, "SHA256SUMS.txt")).st_mtime_ns
        tree = walk_tree(base)
        files = {rel for rel, seen in tree.items() if seen["kind"] == "file"}
        newer = sorted(rel for rel, seen in tree.items() if seen.get("mtime_ns", 0) > sums_mtime)
        unlisted[name] = {"files": len(files), "unlisted": sorted(files - listed - {"SHA256SUMS.txt"}),
                          "listed_missing": sorted(listed - files), "newer_than_sums": newer,
                          "links": sorted(rel for rel, seen in tree.items() if seen["kind"] == "symlink")}
    report["freeze_directories"] = unlisted
    tool_rows = {r["name"]: r for r in sums["authoring/TOOLING-SHA256SUMS.txt"] if "name" in r}
    tool_bindings = []
    for row in freeze["bindings"]:
        if row["id"].startswith("tool:"):
            name = row["id"][5:]
            listed = tool_rows.get(name)
            tool_bindings.append({"id": row["id"], "ok": listed is not None and listed["expected"] == row["sha256"]})
    report["tool_bindings_vs_tooling_list"] = tool_bindings

    # 3. Descriptors inside the configuration documents and HOST.
    configs = freeze["configurations"]
    documents = [(configs["approved_cohort"]["path"], "cohort configuration"),
                 (configs["methods"]["path"], "methods document"),
                 (configs["discovery"]["path"], "discovery document"),
                 (freeze["host"]["HOST"]["path"], "HOST"),
                 (configs["mc29_sources"]["configuration"]["path"], "MC29 configuration case, frozen source"),
                 (configs["mc29_sources"]["job-input"]["path"], "MC29 job-input case, frozen source")]
    for key, row in configs["probe_rows"].items():
        documents.append((row["config"]["path"], "probe row " + key + " configuration"))
        documents.append((row["job"]["path"], "probe row " + key + " job (frozen)"))
    for key, row in configs["host_copies"].items():
        documents.append((row["path"], "HOST copy " + key))
    plan_dir = os.path.dirname(freeze["host"]["HOST"]["path"])
    report["descriptor_documents"] = [check_document_descriptors(path, label) for path, label in documents]
    cohort_config = json.load(open(configs["approved_cohort"]["path"]))
    report["cohort_configuration"] = {
        "sha256": sha256_file(configs["approved_cohort"]["path"]),
        "expected": configs["approved_cohort"]["sha256"],
        "schema": cohort_config["schema"], "contract": cohort_config["contract"],
        "parent_is_null": cohort_config["parent"] is None,
        "commit_equals_fixed": cohort_config["source"]["commit"] == freeze["fixed_state"]["commit"],
        "tree_equals_fixed": cohort_config["source"]["tree"] == freeze["fixed_state"]["tree"],
        "root_is_worktree": cohort_config["source"]["root"] == wt,
        "runtime": cohort_config["runtime"],
        "evidence_root": cohort_config["evidence_root"],
        "keys": sorted(cohort_config),
    }

    # 4. Methods: the frozen original bodies against the probe's and the provider's constants.
    methods = json.load(open(configs["methods"]["path"]))
    probe_path = os.path.join(wt, "prototypes/static_tray_v01/current_host_readback_v02.mjs")
    probe_text = open(probe_path, encoding="utf-8").read()
    block = probe_text[probe_text.index("const ORIGINAL_BODIES = {"):]
    block = block[:block.index("};")]
    probe_bodies = dict(re.findall(r"'([A-Za-z_.0-9]+)':'([0-9a-f]{64})'", block))
    provider_bodies = {}
    for provider in ("current_host_readback_v02.py", "current_host_readback_v01.py"):
        tree = ast.parse(open(os.path.join(wt, "prototypes/static_tray_v01", provider), "rb").read())
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "ORIGINAL_BODIES" for t in node.targets):
                provider_bodies[provider] = ast.literal_eval(node.value)
    report["original_bodies_declarations"] = {
        "methods_document_equals_probe_constant": methods["original_bodies"] == probe_bodies,
        "methods_document_equals_provider_v02_constant": methods["original_bodies"] == provider_bodies.get("current_host_readback_v02.py"),
        "methods_document_equals_provider_v01_constant": methods["original_bodies"] == provider_bodies.get("current_host_readback_v01.py"),
        "count": len(methods["original_bodies"]),
    }
    discovery = json.load(open(configs["discovery"]["path"]))
    ids = discovery["method_ids"]
    report["discovery_document"] = {"count": len(ids), "sorted_unique": ids == sorted(set(ids)),
                                    "ids": ids}

    # 5. The reader tree: the dependency inventory, the historical binding, the actual tree.
    dependencies_inventory = json.load(open(cohort_config["dependencies"]["inventory"]["path"]))
    reader_root = cohort_config["dependencies"]["root"]
    actual = walk_tree(reader_root)
    files = {rel: seen for rel, seen in actual.items() if seen["kind"] == "file"}
    directories = {rel: seen["mode"] for rel, seen in actual.items() if seen["kind"] == "directory"}
    other = {rel: seen["kind"] for rel, seen in actual.items() if seen["kind"] not in ("file", "directory")}
    historical = json.load(open(os.path.join(wt, "docs/engineering/static-tray-qualification-c199/EXTERNAL-INPUTS.json")))
    expected_hist = {}
    for name, binding in historical["files"].items():
        if name.startswith(historical["dependencies_root"] + "/"):
            expected_hist[name[len(historical["dependencies_root"]) + 1:]] = binding
    mismatches = []
    for rel, binding in dependencies_inventory["files"].items():
        seen = files.get(rel)
        if seen is None or seen["sha256"] != binding["sha256"] or seen["size_bytes"] != binding["size_bytes"] \
                or seen["mode"] != binding["mode"] or seen["nlink"] != 1:
            mismatches.append(rel)
        hist = expected_hist.get(rel)
        if hist is None or hist["sha256"] != binding["sha256"] or hist["size_bytes"] != binding["size_bytes"]:
            mismatches.append("historical:" + rel)
    report["reader_tree"] = {
        "root": reader_root, "inventory_files": len(dependencies_inventory["files"]),
        "historical_files": len(expected_hist), "actual_files": len(files),
        "same_file_set": sorted(files) == sorted(dependencies_inventory["files"]) == sorted(expected_hist),
        "directories_equal": directories == dependencies_inventory["directories"],
        "non_regular_entries": other, "ds_store": [r for r in actual if r.endswith(".DS_Store")],
        "mismatches": mismatches,
        "archive": check_descriptor(dependencies_inventory["archive"]),
    }

    # 6. The source inventory, file by file, and its set against the probe's rules.
    source_inventory_path = cohort_config["source"]["inventory"]["path"]
    source_inventory = json.load(open(source_inventory_path))
    trees_block = re.search(r"const SOURCE_TREES = \[([^\]]*)\]", probe_text).group(1)
    optional_block = re.search(r"const SOURCE_OPTIONAL = \[([^\]]*)\]", probe_text).group(1)
    required_block = re.search(r"const SOURCE_REQUIRED = \[(.*?)\];", probe_text, re.S).group(1)
    source_trees = re.findall(r"'([^']+)'", trees_block)
    source_optional = re.findall(r"'([^']+)'", optional_block)
    source_required = re.findall(r"'([^']+)'", required_block)
    constants = {"MAP_RELATIVE": "docs/engineering/localized-repair-c271/current-host-p05/mapping/MAP-EVIDENCE.zip",
                 "CONTRACT_RELATIVE": "docs/engineering/localized-repair-c271/macos-contract-design-p31/CONTRACT.md"}
    for name, value in constants.items():
        if name in required_block:
            source_required.append(value)
    actual_set = {}
    bytecode = []
    for tree_rel in source_trees:
        for rel, seen in walk_tree(os.path.join(wt, tree_rel)).items():
            full_rel = tree_rel + "/" + rel
            if "__pycache__" in full_rel.split("/") or full_rel.endswith((".pyc", ".pyo")):
                bytecode.append(full_rel)
            if seen["kind"] == "file":
                actual_set[full_rel] = seen
            elif seen["kind"] != "directory":
                actual_set[full_rel] = seen
    for rel in source_required:
        actual_set[rel] = describe(os.path.join(wt, rel))
    for rel in source_optional:
        seen = describe(os.path.join(wt, rel))
        if seen["exists"]:
            actual_set[rel] = seen
    differing = []
    for rel, binding in source_inventory["files"].items():
        seen = actual_set.get(rel) or describe(os.path.join(wt, rel))
        if not seen.get("exists") or seen.get("kind") != "file" or seen["sha256"] != binding["sha256"] \
                or seen["size_bytes"] != binding["size_bytes"] or seen["mode"] != binding["mode"] or seen["nlink"] != 1:
            differing.append(rel)
    report["source_inventory"] = {
        "path": source_inventory_path, "sha256": sha256_file(source_inventory_path),
        "schema": source_inventory["schema"], "files": len(source_inventory["files"]),
        "actual_files_by_probe_rules": len(actual_set),
        "missing_from_inventory": sorted(set(actual_set) - set(source_inventory["files"])),
        "missing_from_worktree": sorted(set(source_inventory["files"]) - set(actual_set)),
        "differing": differing, "bytecode_in_source_trees": bytecode,
        "source_trees": source_trees, "required": len(source_required), "optional": source_optional,
    }
    q02 = os.path.join(freeze["evidence"]["parent"], "s7-001-q02-source-inventory.json")
    report["source_inventory"]["q02_output_equal_bytes"] = open(q02, "rb").read() == open(source_inventory_path, "rb").read()

    # 7. The Python installation inventory, entry by entry.
    host = json.load(open(freeze["host"]["HOST"]["path"]))
    python_inventory_path = host["python"]["inventory"]["path"]
    python_inventory = json.load(open(python_inventory_path))
    python_report = {"path": python_inventory_path, "sha256": sha256_file(python_inventory_path),
                     "host_inventory_sha256": host["python"]["inventory_sha256"]}
    q01 = os.path.join(freeze["evidence"]["parent"], "s7-001-q01-python-inventory.json")
    python_report["q01_output_equal_bytes"] = open(q01, "rb").read() == open(python_inventory_path, "rb").read()
    for tree_name in ("framework", "venv"):
        section = python_inventory[tree_name]
        root = section["root"]
        observed = walk_tree(root)
        expected = section["entries"]
        mismatched = []
        for rel, entry in expected.items():
            seen = observed.get(rel)
            if seen is None:
                mismatched.append((rel, "absent"))
                continue
            if entry["kind"] != seen["kind"]:
                mismatched.append((rel, "kind"))
                continue
            if entry["kind"] == "file" and (entry["sha256"] != seen["sha256"] or entry["size_bytes"] != seen["size_bytes"]
                                            or entry["mode"] != seen["mode"]):
                mismatched.append((rel, "file"))
            if entry["kind"] == "directory" and entry.get("mode") != seen["mode"]:
                mismatched.append((rel, "directory mode"))
            if entry["kind"] == "symlink" and entry.get("target") != seen.get("target"):
                mismatched.append((rel, "link target"))
        extra = sorted(set(observed) - set(expected))
        python_report[tree_name] = {"entries": len(expected), "observed": len(observed), "mismatched": mismatched[:50],
                                    "mismatched_count": len(mismatched), "extra": extra[:50], "extra_count": len(extra),
                                    "bytecode_extra": [p for p in extra if p.endswith((".pyc", ".pyo")) or "__pycache__" in p][:50]}
    external = python_inventory["closure"]["external"]
    python_report["closure_external"] = {"count": len(external),
                                         "failed": [p for p, b in external.items() if describe(p).get("sha256") != b["sha256"]]}
    report["python_inventory"] = python_report

    # 8. The inputs that each Node start used, from its records.
    evidence = freeze["evidence"]["parent"]
    starts = []
    def job_chain(argv, cwd, label):
        node, probe, loader = argv[0], argv[5], argv[4]
        expected_digest, job_path = argv[7], argv[9]
        job = json.load(open(job_path))
        manifest = json.load(open(job["manifest"]))
        selection = manifest["selection"]
        return {
            "label": label, "argv0": node, "node_sha256": sha256_file(node), "probe": probe,
            "probe_sha256": sha256_file(probe), "loader_sha256": sha256_file(loader), "cwd": cwd,
            "expected_config_sha256": expected_digest, "job": job_path, "job_sha256": sha256_file(job_path),
            "manifest": job["manifest"], "manifest_sha256": sha256_file(job["manifest"]),
            "job_manifest_sha256": job["supplemental_manifest_sha256"],
            "manifest_selection": selection, "configuration_sha256": sha256_file(selection["path"]),
            "manifest_host": manifest["host"], "manifest_host_sha256_now": sha256_file(manifest["host"]["path"]),
            "artifact_sha256": sha256_file(job["artifact"]) if os.path.exists(job["artifact"]) else None,
            "job_artifact_sha256": job["artifact_sha256"], "audit_sha256": sha256_file(job["audit"]),
            "job_audit_sha256": job["audit_sha256"],
            "argv_digest_equals_manifest_selection": expected_digest == selection["sha256"],
            "manifest_selection_equals_configuration_bytes": selection["sha256"] == sha256_file(selection["path"]),
        }
    for run in ("s7-001-r1", "s7-001-r2"):
        run_doc = json.load(open(os.path.join(evidence, run, "run.json")))
        for row in run_doc["rows"]:
            outcome = json.load(open(os.path.join(evidence, run, row["id"], "outcome.json")))
            argv = outcome["process"]["argv"]
            if "--check" in argv:
                starts.append({"label": run + "/" + row["id"], "argv0": argv[0], "node_sha256": sha256_file(argv[0]),
                               "probe": argv[-1], "probe_sha256": sha256_file(argv[-1]), "flags": argv[1:-1],
                               "cwd": outcome["process"]["cwd"]})
            else:
                starts.append(job_chain(argv, outcome["process"]["cwd"], run + "/" + row["id"]))
    cohort_root = freeze["audit_inputs"]["cohort_root"]
    for case in ("Q01-positive", "Q03-positive", "Q01-changed-reference"):
        ledger = json.load(open(os.path.join(cohort_root, "provider-ledgers", case, "result.json")))
        chain = job_chain(ledger["process"]["argv"], ledger["process"]["cwd"], "C17/" + case)
        chain["ledger_job_binding_sha256"] = ledger["preflight"]["job_binding"]["sha256"]
        chain["ledger_manifest_sha256"] = ledger["preflight"]["manifest_sha256"]
        chain["ledger_config_sha256"] = ledger["preflight"]["config_sha256"]
        chain["ledger_postflight_equal_preflight"] = ledger["preflight"] == ledger["postflight"]
        starts.append(chain)
    report["node_start_inputs"] = starts

    data = json.dumps(report, indent=1, sort_keys=True).encode()
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    # Summary on stdout.
    print("freeze ok", report["freeze"]["ok"])
    print("bindings", report["bindings"]["count"], "failed", len(report["bindings"]["failed"]), "unique", report["bindings"]["ids_unique"])
    for row in report["bindings"]["failed"]:
        print("  FAILED", row["id"], row["problems"])
    print("host facts", [(r["id"], r["ok"], r["problems"]) for r in report["host_facts"]])
    print("ancestors ok", report["evidence_ancestors"]["ok"])
    for name, value in report["digest_lists"].items():
        print("list", name, value["lines"], "failed", len(value["failed"]), [r.get("name", r.get("line")) for r in value["failed"]][:5])
    print("freeze directories", json.dumps(report["freeze_directories"]))
    print("tool bindings vs list", all(r["ok"] for r in tool_bindings), len(tool_bindings))
    for doc in report["descriptor_documents"]:
        print("descriptors", doc["label"], doc["count"], "failed", [(r["pointer"], r["problems"]) for r in doc["failed"]])
    print("cohort configuration", json.dumps(report["cohort_configuration"]))
    print("original bodies", json.dumps(report["original_bodies_declarations"]))
    print("discovery", report["discovery_document"]["count"], report["discovery_document"]["sorted_unique"])
    print("reader tree", json.dumps({k: v for k, v in report["reader_tree"].items() if k != "archive"}), report["reader_tree"]["archive"]["ok"])
    print("source inventory", json.dumps({k: v for k, v in report["source_inventory"].items() if k not in ("source_trees",)}))
    print("python inventory", json.dumps(report["python_inventory"])[:3000])
    for start in starts:
        print("start", json.dumps(start)[:2000])


main()
