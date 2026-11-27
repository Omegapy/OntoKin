"""W2 freeze author: a static replay of the checks that S7's tools and the probe apply to this freeze's inputs.

Run with <worktree>/.venv/bin/python -I -S -B. Standard library only; reads only; starts nothing; imports nothing of
the project. The E paths of the preparation do not exist yet: each is read through its frozen source in OUT (the
preparation copies), and each prepared directory counts as an existing canonical directory.

It replays, from the inspected source (prototypes/static_tray_v01/current_host_readback_v02.mjs and .py,
run_direct_probe.py, collect_outcomes.py, control_harness.py):
  * the runner's validate_rows: shapes, limits, inputs, stage entries, the supervisor error, the predicates;
  * the probe's approvedEnvelope and verifyBootstrap for every probe row, with the refusal point of each;
  * the provider's static selection checks for every configuration (Git, the Python inventory and the
    runtime's Mach-O rules excepted: S7's mc29 and the cohort run those for real);
  * the collector's unit-environment rules and the harness's selection-pair rule;
  * every command's env -i assignments against its frozen environment file, and every --*-sha256 argument.
Usage: w2f_selfcheck.py GENERATE_RECORD
"""
import ast
import hashlib
import json
import os
import platform
import re
import stat
import sys
import time

PROCESS_EVENTS = {"subprocess.Popen", "os.posix_spawn", "os.exec", "os.fork", "os.forkpty", "os.spawn", "os.system"}
sys.addaudithook(lambda event, args: (_ for _ in ()).throw(PermissionError(event)) if event in PROCESS_EVENTS else None)

WT = "<worktree>"
RESULTS = []


def ok(name, condition, detail=""):
    RESULTS.append({"check": name, "ok": bool(condition), "detail": detail})
    if not condition:
        print("FAIL", name, detail)


record = json.load(open(sys.argv[1]))
COPY = {row["target"]: row["source"]["path"] for row in record["prep_copies"]}
PREP_DIRS = set(record["prep_dirs"])


def real(path):
    return COPY.get(path, path)


def read(path):
    with open(real(path), "rb") as stream:
        return stream.read()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def binding(path):
    data = read(path)
    info = os.lstat(real(path))
    return {"sha256": sha(data), "size_bytes": len(data), "mode": "0o%03o" % stat.S_IMODE(info.st_mode)}


def is_dir(path):
    return path in PREP_DIRS or (os.path.isdir(path) and not os.path.islink(path) and os.path.realpath(path) == path)


def stable(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


class Refused(Exception):
    pass


def require_value(condition, message):
    if not condition:
        raise Refused("Current-host binding: " + message)


def require_selection(condition, message):
    if not condition:
        raise Refused("CH-SELECTION: " + message)


CONTRACT = "ontokin.current-host-readback/0.2.0"
CONFIG_KEYS = sorted("schema contract contract_source amendment_adoption source host dependencies runtime methods "
                     "evidence_root parent".split())
MANIFEST_KEYS = sorted("schema contract design_revision amendments labels profile schedule_root cohort_root "
                       "dependencies_root scope limits environment files runtime validator_version three_version "
                       "validator_entry three_package three_entry gltf_loader_entry module_loader probe validator_options "
                       "three_options slots selection source host methods dependencies".split())
HOST_KEYS = sorted("schema contract design_revision amendments profile executor observed_at_utc plan observer platform os "
                   "environment python runtime git dependencies source inspections starts labels claims".split())
JOB_KEYS = sorted("slot case manifest supplemental_manifest_sha256 input_lock_sha256 artifact artifact_sha256 audit "
                  "audit_sha256 result".split())
ENVIRONMENT = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC", "UV_THREADPOOL_SIZE": "2"}
LIMITS = {"maximum_checks": 12, "host_ms": 30000, "child_work_ms": 28000, "cleanup_ms": 2000, "glb_bytes": 8388608,
          "result_bytes": 4194304, "log_bytes": 4194304}
VALIDATOR_OPTIONS = {"format": "glb", "writeTimestamp": False, "maxIssues": 1000, "allowed_errors": 0, "allowed_warnings": 0,
                     "ignoredIssues": [], "external_resources": "rejected"}
THREE_OPTIONS = {"position_tolerance_m": 0.000005, "matrix_tolerance": 0.000001, "node_count": 14, "mesh_count": 12,
                 "animation_count": 0, "external_resources": "rejected"}
SCOPE = "Three original synthetic CPU cases only; twelve native slots are structural, never execution authority"
NODE_FLAGS = ["--no-addons", "--max-old-space-size=256"]
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
SOURCE_TREES = ["ontokin", "tests", "prototypes/static_tray_v01", "tools/static_tray_reader_v01"]
SOURCE_OPTIONAL = ["prototypes/__init__.py", "tools/__init__.py", "tests/__init__.py"]
MAP_RELATIVE = "docs/engineering/localized-repair-c271/current-host-p05/mapping/MAP-EVIDENCE.zip"
CONTRACT_RELATIVE = "docs/engineering/localized-repair-c271/macos-contract-design-p31/CONTRACT.md"
ADOPTION_RELATIVE = "docs/engineering/localized-repair-c271/macos-implementation-p33/ADOPTION-AMENDMENT-001.json"
SOURCE_REQUIRED = ["tools/check_local.py", "tools/prepare_current_host_readback.py", "tools/storage_identity.py",
                   "tools/force-agent-verification-requirements.txt", "tools/native-reader-verification-linux-cp312.lock",
                   "tools/native-reader-verification-macos-arm64-cp312.lock", "pyproject.toml",
                   "docs/engineering/static-tray-mapping-c198/CONTROLS.json",
                   "docs/engineering/static-tray-qualification-c199/EXTERNAL-INPUTS.json",
                   "docs/engineering/localized-repair-c271/current-host-p05/CONTRACT.md",
                   "docs/engineering/localized-repair-c271/current-host-p05/CONTRACT.json",
                   "docs/engineering/localized-repair-c271/current-host-p05/ADOPTION.json", MAP_RELATIVE, CONTRACT_RELATIVE,
                   "docs/engineering/localized-repair-c271/macos-contract-design-p31/CONTRACT.json",
                   "docs/engineering/localized-repair-c271/macos-contract-design-p31/ADOPTION.json"]
ORIGINAL_BODIES = json.load(open(record["methods"]["path"]))["original_bodies"]
METHOD_IDS = sorted("test_static_tray_readback_v01." + n for n in ORIGINAL_BODIES if ".test_" in n)
CF_HOST = "0x1F5:0x0:0x0"
NODE_ENV_PRESENT = dict(ENVIRONMENT, __CF_USER_TEXT_ENCODING=CF_HOST)
NODE_ENV_ABSENT = dict(ENVIRONMENT)


def file_bytes(path, maximum, expected=None):
    require_value(os.path.isabs(path) and os.path.normpath(path) == path, "file path is not an absolute normalized path")
    data = read(path)
    require_value(len(data) <= maximum, "file exceeds its bound: " + path)
    if expected is not None:
        actual = binding(path)
        require_value(actual["size_bytes"] == expected["size_bytes"] and actual["mode"] == expected["mode"],
                      "file size or mode differs: " + path)
        require_value(actual["sha256"] == expected["sha256"], "file hash differs: " + path)
    return data


def bound_json(descriptor, maximum):
    require_value(set(descriptor) == {"path", "sha256", "size_bytes", "mode"}, "file binding has unknown fields")
    return json.loads(file_bytes(descriptor["path"], maximum, descriptor))


def environment_admitted(observed, declared, recorded):
    if "__CF_USER_TEXT_ENCODING" in declared:
        return False
    if stable(observed) == stable(declared):
        return True
    return isinstance(recorded, str) and recorded != "" and stable(observed) == stable(
        dict(declared, __CF_USER_TEXT_ENCODING=recorded))


def walk_files(root, rel_root):
    files, directories = {}, {}
    for parent, dirs, names in os.walk(os.path.join(root, rel_root)):
        dirs.sort()
        for name in sorted(dirs + names):
            full = os.path.join(parent, name)
            rel = os.path.relpath(full, root)
            require_value("__pycache__" not in rel.split("/") and not re.search(r"\.py[co]$", rel),
                          "unbound source bytecode/cache")
            info = os.lstat(full)
            require_value(not stat.S_ISLNK(info.st_mode), "symlink in complete file inventory")
            if stat.S_ISDIR(info.st_mode):
                directories[rel] = "0o%o" % stat.S_IMODE(info.st_mode)
            else:
                require_value(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, "nonregular or hardlinked inventory input")
                files[rel] = full
    return files, directories


def verify_source(config):
    require_value(config["source"]["root"] == WT, "probe is outside its bound checkout")
    inventory = bound_json(config["source"]["inventory"], 16 << 20)
    actual = {}
    for tree in SOURCE_TREES:
        actual.update(walk_files(WT, tree)[0])
    for rel in SOURCE_REQUIRED + [p for p in SOURCE_OPTIONAL if os.path.lexists(os.path.join(WT, p))]:
        actual[rel] = os.path.join(WT, rel)
    require_value(sorted(actual) == sorted(inventory["files"]), "complete source file inventory differs")
    for rel, row in inventory["files"].items():
        file_bytes(actual[rel], row["size_bytes"], row)
    cs = config["contract_source"]
    require_value(cs["path"] == os.path.join(WT, CONTRACT_RELATIVE)
                  and cs["sha256"] == "42db98dc6099ee605b0963f3734f7bff2d68c019ff6c00a0ee97bd753c03fdc9",
                  "adopted contract source differs")
    file_bytes(cs["path"], 1 << 20, cs)
    require_value({k: cs[k] for k in ("sha256", "size_bytes", "mode")} == inventory["files"][CONTRACT_RELATIVE],
                  "contract source inventory binding differs")
    aa = config["amendment_adoption"]
    require_value(aa["path"] == os.path.join(WT, ADOPTION_RELATIVE)
                  and aa["sha256"] == "872312ed80a63fbb196c17ace42e786b7fe757b710eff41139b125dfaa507937",
                  "adopted amendment record differs")
    file_bytes(aa["path"], 1 << 20, aa)
    return inventory


def verify_dependencies(config, source_inventory):
    root = config["dependencies"]["root"]
    require_value(is_dir(root) and not root.startswith(WT + "/"), "dependencies are not external")
    inventory = bound_json(config["dependencies"]["inventory"], 1 << 20)
    require_value(inventory["schema"] == "ontokin.current-host-readback-dependencies/0.2.0", "wrong dependency schema")
    require_value(inventory["archive"]["sha256"] == "b1e54a6cfef133f7004b1988c90bc718fc954409843c2bcac3772d42e904a0c9",
                  "dependency archive identity differs")
    file_bytes(inventory["archive"]["path"], inventory["archive"]["size_bytes"], inventory["archive"])
    historical_rel = "docs/engineering/static-tray-qualification-c199/EXTERNAL-INPUTS.json"
    historical = json.loads(file_bytes(os.path.join(WT, historical_rel), 1 << 20, source_inventory["files"][historical_rel]))
    expected = {k[len(historical["dependencies_root"]) + 1:]: v for k, v in historical["files"].items()
                if k.startswith(historical["dependencies_root"] + "/")}
    require_value(len(expected) == 24, "historical dependency inventory is not exactly 24 files")
    require_value(sorted(inventory["files"]) == sorted(expected), "exact retained dependency paths")
    files, directories = walk_files(root, "")
    require_value(sorted(files) == sorted(expected), "installed dependency files")
    require_value(stable(directories) == stable(inventory["directories"]), "installed dependency directory paths and modes")
    for rel, row in inventory["files"].items():
        require_value(row["sha256"] == expected[rel]["sha256"] and row["size_bytes"] == expected[rel]["size_bytes"],
                      "retained dependency bytes changed")
        file_bytes(os.path.join(root, rel), row["size_bytes"], row)
    for rel, version in (("validator/package/package.json", "2.0.0-dev.3.10"), ("indexer-view/three/package.json", "0.186.1")):
        require_value(json.loads(read(os.path.join(root, rel)))["version"] == version, "dependency package version differs")
    return inventory


def verify_host(config, node_env):
    host = bound_json(config["host"], 8 << 20)
    require_value(sorted(host) == HOST_KEYS, "host has unknown, missing or extra fields")
    require_value(host["schema"] == "ontokin.current-host-readback-host/0.2.0" and host["contract"] == CONTRACT
                  and host["design_revision"] == 4 and host["amendments"] == ["P33-AMENDMENT-001"]
                  and host["profile"] == "darwin-arm64-v1" and host["executor"] == "macos-arm64-local",
                  "invalid host schema/contract/design revision/time")
    require_value(stable(host["environment"]["declared"]) == stable(ENVIRONMENT), "host environment differs")
    recorded = host["environment"]["cf_user_text_encoding"]
    require_value(recorded is None or (isinstance(recorded, str) and recorded), "recorded __CF_USER_TEXT_ENCODING is malformed")
    require_value(environment_admitted(node_env, ENVIRONMENT, recorded), "actual Node environment differs")
    uname = os.uname()
    require_value(host["platform"]["system"] == "Darwin" == uname.sysname and host["platform"]["release"] == uname.release
                  and host["platform"]["machine"] == "arm64" == uname.machine, "actual host platform differs")
    require_value(host["runtime"]["executable"] == config["runtime"]["executable"]
                  and host["runtime"]["version"] == "v24.22.1", "selected Node build differs")
    file_bytes(host["runtime"]["archive"]["path"], host["runtime"]["archive"]["size_bytes"], host["runtime"]["archive"])
    file_bytes(config["runtime"]["executable"], host["runtime"]["binding"]["size_bytes"], host["runtime"]["binding"])
    for key in ("git_version", "node_version"):
        bound_json(host["inspections"][key], 8 << 20)
    return host


def verify_methods(config, source_inventory):
    methods = bound_json(config["methods"], 1 << 20)
    require_value(methods["schema"] == "ontokin.current-host-readback-methods/0.2.0"
                  and methods["source_test"] == "tests/test_static_tray_readback_v01.py", "wrong method source/schema")
    require_value(stable(methods["original_bodies"]) == stable(ORIGINAL_BODIES), "nine original method/helper body identities")
    discovery = bound_json(methods["discovery"], 8 << 20)
    require_value(discovery["schema"] == "ontokin.current-host-readback-discovery/0.2.0", "invalid discovery schema/IDs")
    require_value(discovery["method_ids"] == sorted(set(discovery["method_ids"])), "sorted unique discovery IDs")
    require_value(all(item in discovery["method_ids"] for item in METHOD_IDS), "missing original method identity")
    require_value(discovery["baseline_map"]["path"] == os.path.join(WT, MAP_RELATIVE), "baseline map belongs to an unbound source")
    require_value({k: discovery["baseline_map"][k] for k in ("sha256", "size_bytes", "mode")}
                  == source_inventory["files"][MAP_RELATIVE], "baseline source-map identity")
    file_bytes(discovery["baseline_map"]["path"], discovery["baseline_map"]["size_bytes"], discovery["baseline_map"])
    return methods


def expected_labels(host):
    return {"executor": "macos-arm64-local", "contract": CONTRACT, "design_revision": 4, "amendments": ["P33-AMENDMENT-001"],
            "profile": "darwin-arm64-v1", "os": host["labels"]["os"], "node": host["labels"]["node"],
            "python_inventory_sha256": host["python"]["inventory_sha256"],
            "git": {"path": host["git"]["path"], "sha256": host["git"]["sha256"]}, "run_kind": "qualifying",
            "boundary": "real"}


def probe(argv, cwd, node_env):
    """approvedEnvelope, then the try block up to the first refusal: (where, message)."""
    node, probe_path = argv[0], argv[5]
    args = argv[6:]
    try:
        require_selection(len(args) == 4 and args[0] == "--expected-config-sha256" and args[2] == "--job",
                          "expected exactly --expected-config-sha256 DIGEST --job FILE")
        expected = args[1]
        require_selection(SHA_RE.match(expected) is not None, "externally selected configuration digest is not a lowercase SHA-256")
        job_path = args[3]
        job = json.loads(file_bytes(job_path, 32768))
        require_value(sorted(job) == JOB_KEYS, "job has unknown, missing or extra fields")
        for key in ("supplemental_manifest_sha256", "artifact_sha256", "audit_sha256"):
            require_value(SHA_RE.match(job[key]) is not None, "job digest is not a lowercase SHA-256")
        manifest_bytes = file_bytes(job["manifest"], 1 << 20)
        require_value(sha(manifest_bytes) == job["supplemental_manifest_sha256"], "job manifest bytes differ")
        manifest = json.loads(manifest_bytes)
        require_value(sorted(manifest["selection"]) == ["path", "sha256"], "manifest selection has unknown fields")
        require_selection(manifest["selection"]["sha256"] == expected, "manifest digest is not external approval")
        config_path = manifest["selection"]["path"]
        config_bytes = file_bytes(config_path, 1 << 20)
        require_selection(sha(config_bytes) == expected, "configuration is not approved by the external digest")
        config = json.loads(config_bytes)
        require_value(sorted(config) == CONFIG_KEYS, "configuration has unknown, missing or extra fields")
        require_value(config["schema"] == "ontokin.current-host-readback-config/0.2.0" and config["contract"] == CONTRACT,
                      "wrong configuration contract/schema")
        output_root = config["evidence_root"]
        require_value(is_dir(output_root), "directory is absent, aliased or unsafe: " + output_root)
        require_value(output_root != WT and not output_root.startswith(WT + "/"), "evidence is not external")
        cohort = manifest["cohort_root"]
        require_value(is_dir(cohort) and cohort.startswith(output_root + "/"), "cohort escapes its bound parent")
        routes = {"CPU-Q01-positive": ["Q01", "Q01-positive"], "CPU-Q03-positive": ["Q03", "Q03-positive"],
                  "CPU-Q01-changed-reference": ["Q01", "Q01-changed-reference"]}
        require_value(job["slot"] in routes, "job is not an admitted synthetic CPU case")
        case, label = routes[job["slot"]]
        stage = cohort + "/" + label
        require_value(is_dir(stage), "directory is absent, aliased or unsafe: " + stage)
        require_value(job["case"] == case and job["input_lock_sha256"] == "CPU-ONLY-SYNTHETIC-NOT-NATIVE"
                      and job_path == stage + "/job.json" and cwd == stage and job["artifact"] == stage + "/synthetic.glb"
                      and job["audit"] == stage + "/synthetic-audit.json" and job["result"] == stage + "/probe.json"
                      and os.path.dirname(job["manifest"]) == cohort and not os.path.lexists(job["result"]),
                      "job paths, case, output freshness or actual stage differ")
    except Refused as exc:
        return "approvedEnvelope", str(exc)
    try:
        require_value(manifest["schema"] == "ontokin.current-host-readback-lock/0.2.0", "Wrong supplemental manifest")
        require_selection(sha(read(config_path)) == expected, "configuration changed after selection")
        require_value(sorted(manifest) == MANIFEST_KEYS, "manifest has unknown, missing or extra fields")
        require_value(manifest["contract"] == CONTRACT and manifest["profile"] == "ontokin.static-tray/0.1.0"
                      and manifest["scope"] == SCOPE, "manifest schema/profile/scope differs")
        require_selection(stable(manifest["selection"]) == stable({"path": config_path, "sha256": expected}),
                          "manifest approval selection differs")
        for field in ("source", "host", "methods", "dependencies"):
            require_value(stable(manifest[field]) == stable(config[field]), "manifest " + field + " differs")
        require_value(stable(manifest["limits"]) == stable(LIMITS), "manifest limits differs")
        require_value(stable(manifest["environment"]) == stable(ENVIRONMENT), "manifest environment differs")
        require_value(stable(manifest["validator_options"]) == stable(VALIDATOR_OPTIONS), "validator options differs")
        require_value(stable(manifest["three_options"]) == stable(THREE_OPTIONS), "Three options differs")
        require_value(sorted(config["runtime"]) == ["executable", "version"] and config["runtime"]["version"] == "v24.22.1",
                      "unsupported configured Node version")
        source_inventory = verify_source(config)
        require_value(config["parent"] is None, "derived configuration")
        dependencies = verify_dependencies(config, source_inventory)
        host = verify_host(config, node_env)
        verify_methods(config, source_inventory)
        expected_files = {config["dependencies"]["root"] + "/" + rel: row for rel, row in dependencies["files"].items()}
        for rel in ("prototypes/static_tray_v01/current_host_readback_v02.py", "prototypes/static_tray_v01/current_host_readback_v02.mjs"):
            expected_files[WT + "/" + rel] = source_inventory["files"][rel]
        require_value(stable(manifest["files"]) == stable(expected_files), "manifest complete executable-file bindings differs")
        require_value(stable(manifest["runtime"]) == stable({"executable": config["runtime"]["executable"], "version": "v24.22.1",
                                                            "binding": host["runtime"]["binding"]}), "manifest runtime differs")
        require_value(manifest["design_revision"] == 4 and manifest["amendments"] == ["P33-AMENDMENT-001"],
                      "manifest design revision or amendments differ")
        require_value(stable(manifest["labels"]) == stable(expected_labels(host)), "manifest labels differs")
        require_value(manifest["dependencies_root"] == config["dependencies"]["root"] and manifest["probe"] == probe_path
                      and manifest["validator_version"] == "2.0.0-dev.3.10" and manifest["three_version"] == "0.186.1",
                      "manifest runtime/dependency identity differs")
        roles = {"validator_entry": "validator/package/index.js", "three_package": "indexer-view/three/package.json",
                 "three_entry": "indexer-view/three/build/three.webgpu.js",
                 "gltf_loader_entry": "indexer-view/three/examples/jsm/loaders/GLTFLoader.js",
                 "module_loader": "tools/three_loader.mjs"}
        for role, rel in roles.items():
            require_value(manifest[role] == config["dependencies"]["root"] + "/" + rel and manifest[role] in manifest["files"],
                          "unbound executable role: " + role)
        require_value(argv[1:5] == [*NODE_FLAGS, "--experimental-loader", manifest["module_loader"]], "actual Node flags/loader differs")
        require_value(argv[0] == config["runtime"]["executable"] and probe_path == WT + "/prototypes/static_tray_v01/current_host_readback_v02.mjs",
                      "actual process argv source differs")
        require_value(manifest["schedule_root"] == manifest["cohort_root"] + "/unused-native-schedule"
                      and not os.path.lexists(manifest["schedule_root"]), "native schedule exists or differs")
        controls = json.loads(read(WT + "/docs/engineering/static-tray-mapping-c198/CONTROLS.json"))
        slots = controls["future_qualification_native_slots"]
        require_value(len(slots) == 12 and len(manifest["slots"]) == 12, "original twelve structural slots differ")
        for slot, row in zip(slots, manifest["slots"]):
            stage_n = manifest["schedule_root"] + "/external-readback/" + slot["slot"]
            want = {"slot": slot["slot"], "case": slot["case"], "route": slot["route"], "maximum_starts": slot["maximum_starts"],
                    "stage": stage_n, "result": stage_n + "/result.json",
                    "argv": [config["runtime"]["executable"], *NODE_FLAGS, "--experimental-loader", manifest["module_loader"],
                             probe_path, "--expected-config-sha256", expected, "--job", stage_n + "/job.json"]}
            require_value(stable(row) == stable(want), "exact ordered manifest slot differs")
        require_value(argv == manifest["slots"][0]["argv"][:-1] + [job_path], "actual checker argv differs")
        glb, audit = read(job["artifact"]), read(job["audit"])
        require_value(sha(glb) == job["artifact_sha256"] and sha(audit) == job["audit_sha256"], "Actual input identity differs")
        audit_doc = json.loads(audit)
        require_value(audit_doc["passed"] is True and audit_doc["artifact_sha256"] == sha(glb) and audit_doc["case"] == job["case"],
                      "Independent passed audit does not bind this actual GLB")
    except Refused as exc:
        return "try", str(exc)
    return "readers", "would import the readers and run the scientific body"


# ---- the runner's rows --------------------------------------------------------------------------------------------
DECLARED = ENVIRONMENT
for key in ("r1", "r2"):
    path = record["rows_files"][key]["path"]
    doc = json.load(open(path))
    ok(key + ": rows document binding", binding(path) == {k: record["rows_files"][key][k] for k in ("sha256", "size_bytes", "mode")})
    ok(key + ": rows schema", set(doc) == {"schema", "rows_independent", "rows"} and doc["schema"] == "ontokin.c271.p35-direct-probe-rows/2"
       and doc["rows_independent"] is False)
    stages = set()
    for row in doc["rows"]:
        ident = row["id"]
        ok(key + " " + ident + ": keys", set(row) == {"id", "argv", "stage", "label", "environment", "total_ms", "stage_ms",
                                                     "inputs", "stage_entries", "expected"})
        ok(key + " " + ident + ": stage prepared, not shared", row["stage"] in PREP_DIRS and row["stage"] not in stages)
        stages.add(row["stage"])
        ok(key + " " + ident + ": environment", row["environment"] == DECLARED)
        ok(key + " " + ident + ": limits", 0 < row["stage_ms"] <= row["total_ms"] - 2000 and row["total_ms"] <= 30000)
        ok(key + " " + ident + ": label", re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", row["label"]) is not None)
        exp = row["expected"]
        want = None if exp["returncode"] == 0 else {"code": "OTRAY-E-BACKEND", "reason": "Child exited with status %d" % exp["returncode"],
                                                    "state": "REJECTED"}
        ok(key + " " + ident + ": supervisor error implied by the status", exp["supervisor_error"] == want)
        paths = {item["path"] for item in row["inputs"]}
        for item in row["inputs"]:
            ok(key + " " + ident + ": input " + item["path"], binding(item["path"]) == {k: item[k] for k in ("sha256", "size_bytes", "mode")})
        staged = {target for target in COPY if os.path.dirname(target) == row["stage"]}
        ok(key + " " + ident + ": stage entries are exactly the prepared files",
           sorted(e["path"] for e in row["stage_entries"]) == sorted(os.path.basename(t) for t in staged)
           and all(e["kind"] == "file" for e in row["stage_entries"]))
        ok(key + " " + ident + ": every stage file is an input", all(t in paths for t in staged))
        targets = set(exp["present_paths"]) | set(exp["file_includes"]) | set(exp["json_members"])
        ok(key + " " + ident + ": predicate targets absent", not any(os.path.lexists(t) for t in targets))
        if ident == "probe-syntax-check":
            ok(key + ": syntax argv", row["argv"][-2:] == ["--check", "<worktree>/prototypes/static_tray_v01/current_host_readback_v02.mjs"])
            continue
        ok(key + " " + ident + ": probe argv shape", len(row["argv"]) == 10 and row["argv"][9] == row["stage"] + "/job.json")
        absent = probe(row["argv"], row["stage"], NODE_ENV_PRESENT)
        absent2 = probe(row["argv"], row["stage"], NODE_ENV_ABSENT)
        print(key, ident, "with the variable:", absent, "| without it:", absent2)
        if ident == "P06-H01":
            ok("P06-H01 refusal point", absent == ("approvedEnvelope", "CH-SELECTION: manifest digest is not external approval")
               and absent2 == absent)
            ok("P06-H01 stderr predicate", exp["stderr_includes"] == ["CH-SELECTION: manifest digest is not external approval"])
        elif ident == "P06-H02":
            ok("P06-H02 refusal point", absent == ("approvedEnvelope", "Current-host binding: wrong configuration contract/schema")
               and absent2 == absent)
        elif ident == "MC30-probe":
            ok("MC30-probe refusal with the variable", absent == ("try", "Current-host binding: actual Node environment differs"))
            ok("MC30-probe refusal without it", absent2 == ("try", "Current-host binding: Actual input identity differs"))
        elif ident == "MC36":
            ok("MC36 refusal with the variable", absent == ("try", "Current-host binding: actual Node environment differs"))
            ok("MC36 without the variable reaches the readers (why it waits for MC30-probe)", absent2[0] == "readers")

# ---- the provider's static selection checks, for every configuration --------------------------------------------
host_doc = json.load(open(record["bindings"][[b["id"] for b in record["bindings"]].index("host:HOST.json")]["path"]))
for name in ("cohort", "mc29-configuration", "mc29-job-input"):
    cfg_path = record["configs"][name]["path"]
    cfg = json.load(open(cfg_path))
    ok(name + ": keys and schema", sorted(cfg) == CONFIG_KEYS and cfg["schema"] == "ontokin.current-host-readback-config/0.2.0"
       and cfg["contract"] == CONTRACT and cfg["parent"] is None)
    ok(name + ": canonical", read(cfg_path) == json.dumps(cfg, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode())
    ok(name + ": source root and outside it", cfg["source"]["root"] == WT and not cfg_path.startswith(WT + "/"))
    ok(name + ": evidence root prepared and external", cfg["evidence_root"] in PREP_DIRS and not cfg["evidence_root"].startswith(WT))
    ok(name + ": cross bindings", host_doc["source"]["root"] == WT and host_doc["source"]["commit"] == cfg["source"]["commit"]
       and host_doc["source"]["tree"] == cfg["source"]["tree"] and host_doc["source"]["inventory"] == cfg["source"]["inventory"]
       and host_doc["dependencies"]["root"] == cfg["dependencies"]["root"]
       and host_doc["dependencies"]["inventory"] == cfg["dependencies"]["inventory"] and host_doc["dependencies"]["files"] == 24)
    host_path = "<local>/c271-p35/evidence/observe-001/HOST.json"
    ok(name + ": HOST descriptor", cfg["host"] == {"path": host_path, **binding(host_path)})
    ok(name + ": observer binding", {k: host_doc["observer"][k] for k in ("sha256", "size_bytes", "mode")}
       == json.load(open(cfg["source"]["inventory"]["path"]))["files"]["prototypes/static_tray_v01/current_host_observation_v02.py"])
    try:
        verify_methods(cfg, json.load(open(cfg["source"]["inventory"]["path"])))
        ok(name + ": methods and discovery", True)
    except Refused as exc:
        ok(name + ": methods and discovery", False, str(exc))
source = open(WT + "/tests/test_static_tray_readback_v01.py", "rb").read()
bodies = {}
for group in ast.parse(source).body:
    if isinstance(group, ast.ClassDef):
        for node in group.body:
            key = group.name + "." + getattr(node, "name", "")
            if key in ORIGINAL_BODIES and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                bodies[key] = hashlib.sha256(ast.dump(ast.Module(body=node.body, type_ignores=[]), include_attributes=False).encode()).hexdigest()
ok("original bodies equal the source (AST, this interpreter)", bodies == ORIGINAL_BODIES)
ok("interpreter", platform.python_version() == host_doc["python"]["interpreter"]["version"]
   and sys.version == host_doc["python"]["interpreter"]["build_string"])

# ---- environments, the collector's rules and every command's arguments ---------------------------------------------
REMOVED = ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP", "PYTHONINSPECT", "PYTHONBREAKPOINT", "PYTHONUSERBASE",
           "PYTHONPYCACHEPREFIX", "LD_PRELOAD", "LD_LIBRARY_PATH", "NODE_OPTIONS", "NODE_PATH", "__PYVENV_LAUNCHER__",
           "PYTHONEXECUTABLE")
envs = record["environments"]
for name, row in envs.items():
    doc = json.load(open(row["path"]))
    ok("env " + name + ": document", set(doc) == {"schema", "environment"} and doc["schema"] == "ontokin.c271.p35-unit-environment/1"
       and "HOME" not in doc["environment"] and binding(row["path"])["sha256"] == row["sha256"])
cohort_env = envs["cohort"]["environment"]
ok("cohort env: driver rules", not any(n in REMOVED or n.startswith("DYLD_") for n in cohort_env)
   and cohort_env.get("PYTHONDONTWRITEBYTECODE") == "1" and cohort_env.get("PYTHONNOUSERSITE") == "1"
   and not any(n.startswith("GIT_") for n in cohort_env))
ok("cohort env: selection pair", cohort_env["ONTOKIN_CURRENT_HOST_READBACK_CONFIG"] == record["configs"]["cohort"]["path"]
   and cohort_env["ONTOKIN_CURRENT_HOST_READBACK_CONFIG_SHA256"] == record["configs"]["cohort"]["sha256"] == record["D0"])
ok("cohort env: override absent and inside the evidence root",
   cohort_env["STATIC_TRAY_READBACK_CPU_OUTPUT"].startswith(json.load(open(record["configs"]["cohort"]["path"]))["evidence_root"] + "/"))
for case in ("configuration", "job-input"):
    env = envs["mc29-" + case]["environment"]
    ok("mc29 " + case + ": selection pair is the copy", env["ONTOKIN_CURRENT_HOST_READBACK_CONFIG"] == record["mc29_copy"][case]
       and env["ONTOKIN_CURRENT_HOST_READBACK_CONFIG_SHA256"] == record["configs"]["mc29-" + case]["sha256"])
ok("mc37 env: no selection", not any(n.startswith("ONTOKIN_") for n in envs["mc37"]["environment"]))
binding_by_path = {row["path"]: row for row in record["bindings"]}
prepared_by_path = {row["path"]: row for row in record["prepared_entries"]}
for command in record["pre_commands"] + record["commands"] + record["post_commands"]:
    argv = command["argv"]
    env_doc = json.load(open(command["environment"]["file"]))["environment"]
    if argv[:2] == ["/usr/bin/env", "-i"]:
        assignments = []
        for item in argv[2:]:
            if "=" in item and not item.startswith("/") and not item.startswith("-"):
                assignments.append(item)
            else:
                break
        ok(command["id"] + ": env -i assignments equal the frozen file",
           dict(a.split("=", 1) for a in assignments) == env_doc, json.dumps(assignments))
        program = argv[2 + len(assignments)]
        if program.endswith("/python"):
            flags = argv[3 + len(assignments)]
            ok(command["id"] + ": -B on the command line", "-B" in argv[3 + len(assignments):6 + len(assignments)])
    for index, item in enumerate(argv):
        if item.endswith("-sha256") and index + 1 < len(argv) and not argv[index + 1].startswith("<"):
            target = argv[index - 1]
            if item == "--module-sha256":
                target = WT + ("/tests/test_static_tray_readback_v01.py" if "cohort" in argv else
                               "/tests/test_current_host_readback_controls_v02.py")
            known = binding_by_path.get(target) or prepared_by_path.get(target)
            if known is None and os.path.isfile(target):
                known = binding(target)
            if command["id"] == "C06" or command["id"] == "C07":
                pass
            ok(command["id"] + ": digest of " + target, known is not None and known["sha256"] == argv[index + 1],
               argv[index + 1])
    for out in command["outputs"]:
        ok(command["id"] + ": output outside the worktree and the freeze", not out.startswith(WT + "/") and "W2-freeze-001" not in out)
        parent = os.path.dirname(out)
        ok(command["id"] + ": output parent exists or is prepared", os.path.isdir(parent) or parent in PREP_DIRS, out)

# ---- plans, the preparation and the absent paths ------------------------------------------------------------------
plan001 = json.load(open("<local>/c271-p35/workers/W2-plan-001/observation-plan-001.json"))
for row in record["mc10"]:
    plan = json.load(open(row["plan"]["path"]))
    diffs = sorted(k for k in plan if plan[k] != plan001[k])
    ok("mc10 " + row["key"] + ": plan differs from plan 001 only in evidence and commands", diffs == ["commands", "evidence"])
    ok("mc10 " + row["key"] + ": attempt absent", not os.path.lexists(row["attempt"]) and os.path.dirname(row["attempt"]) == plan["evidence"]["parent"])
    ok("mc10 " + row["key"] + ": canonical", read(row["plan"]["path"]) == json.dumps(plan, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode())
before = set(record["absent_paths"]["before_preparation"])
after = set(record["absent_paths"]["after_preparation"])
ok("absent paths now absent", not [p for p in before if os.path.lexists(p)], [p for p in before if os.path.lexists(p)][:5])
ok("prepared entries not in the after list", not (after & set(prepared_by_path)))
ok("prepared sources", all(binding(row["copied_from"]) == {k: row[k] for k in ("sha256", "size_bytes", "mode")}
                           for row in record["prepared_entries"] if row["kind"] == "file"))
script = open(record["prep_script"]["path"]).read()
for row in record["prepared_entries"]:
    ok("prep script creates " + row["path"], ("'" + row["path"] + "'") in script)
failed = [r for r in RESULTS if not r["ok"]]
print(json.dumps({"checks": len(RESULTS), "failed": len(failed)}, sort_keys=True))
