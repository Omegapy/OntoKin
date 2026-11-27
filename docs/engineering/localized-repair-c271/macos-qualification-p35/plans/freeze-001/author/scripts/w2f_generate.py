"""W2 freeze author: generate the bound documents of operational freeze 001 and FREEZE-001.json itself.

Run with <worktree>/.venv/bin/python -I -S -B. Standard library only. It reads the bound inputs, refuses
every process creation, imports nothing of the project, and creates only absent files under OUT.
Usage: w2f_generate.py
"""
from copy import deepcopy
import hashlib
import json
import os
import stat
import sys

PROCESS_EVENTS = {"subprocess.Popen", "os.posix_spawn", "os.exec", "os.fork", "os.forkpty", "os.spawn", "os.system"}
sys.addaudithook(lambda event, args: (_ for _ in ()).throw(PermissionError(event)) if event in PROCESS_EVENTS else None)

# ---------------------------------------------------------------------------------------------------------------
# Places (on-disk spelling verified by w2f_bind.py, records/bind-001.json)
# ---------------------------------------------------------------------------------------------------------------
LOCAL = "<local>"
WT = "<worktree>"
E = LOCAL + "/c271-p35/evidence"
OUT = LOCAL + "/c271-p35/workers/W2-freeze-001"
W2P = LOCAL + "/c271-p35/workers/W2-plan-001"
W3F = LOCAL + "/c271-p35/workers/W3-freeze-001"
PY = WT + "/.venv/bin/python"
TOOLING = WT + "/docs/engineering/localized-repair-c271/macos-qualification-p35/tooling"
OBSERVER = WT + "/prototypes/static_tray_v01/current_host_observation_v02.py"
WRAPPER = LOCAL + "/c271-p35/director/run/run_once_v2.sh"
NODE = LOCAL + "/c271-macos/node-v24.22.1-darwin-arm64/bin/node"
PROBE = WT + "/prototypes/static_tray_v01/current_host_readback_v02.mjs"
PROVIDER_REL = "prototypes/static_tray_v01/current_host_readback_v02.py"
PROBE_REL = "prototypes/static_tray_v01/current_host_readback_v02.mjs"
DEPS = LOCAL + "/c271-macos/reader-c195"
LOADER = DEPS + "/tools/three_loader.mjs"
GIT = "/Library/Developer/CommandLineTools/usr/bin/git"
GIT_DIR = "<clone>/.git"
HOST = E + "/observe-001/HOST.json"
CF_FILE = "<home>/.CFUserTextEncoding"
CONTRACT_MD = WT + "/docs/engineering/localized-repair-c271/macos-contract-design-p31/CONTRACT.md"
ADOPTION = WT + "/docs/engineering/localized-repair-c271/macos-implementation-p33/ADOPTION-AMENDMENT-001.json"
ADDITIONS = WT + "/docs/engineering/localized-repair-c271/macos-implementation-p33/INVENTORY-ADDITIONS.json"
MAP_REL = "docs/engineering/localized-repair-c271/current-host-p05/mapping/MAP-EVIDENCE.zip"
CONTROLS_JSON = WT + "/docs/engineering/static-tray-mapping-c198/CONTROLS.json"
SOURCE_INVENTORY = W2P + "/source-inventory-001.json"
PYTHON_INVENTORY = W2P + "/python-inventory-001.json"
DEPENDENCIES_INVENTORY = W2P + "/dependencies-inventory-001.json"
PLAN_001 = W2P + "/observation-plan-001.json"
COMMIT_C, TREE_C = "0eb9a5517f4e19705178a2c59b8d8d33fb87867a", "ea10cd94c05a2ebbb44b3f83d4c96cb0a59baa2b"
BASE_COMMIT = "1c2f25ba224a5c3419004d1d331d29e01378ae00"
BOOT = "C90010BA-4DA9-475D-BBAB-CF1A9C40175A"
CF_VALUE = "0x1F5:0x0:0x0"
CF_ALTERED = "0x1F5:0x8000100:0x0"
ATTEMPT = "s7-001"
DECLARED = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC", "UV_THREADPOOL_SIZE": "2"}
CONFIG_ENV, DIGEST_ENV = "ONTOKIN_CURRENT_HOST_READBACK_CONFIG", "ONTOKIN_CURRENT_HOST_READBACK_CONFIG_SHA256"
GIT_LINE = "git version 2.50.1 (Apple Git-155)\n"
CONTROL_MODULE_SHA = "3b8c91b7767c2db0ac3dd5c7dd48d035eb6dd602dc8c01e08bb0e49ac21bd618"
COHORT_MODULE_SHA = "6295e0442ba7e7a1d1236fb5d9148e97ed92cc4db3e77dcd7b2993af5ef0f662"
MC37_TEST = ("tests.test_current_host_readback_controls_v02.SupervisorProcessControls."
             "test_mc37_exited_unreaped_direct_child_counts_as_present_until_it_is_reaped")
EMPTY_SHA = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
ORIGINAL_BODIES = {
    "ReadbackCoordinatorSeams.run_seam": "2f39cde2f0f4a18eb54b003e2628b22c47d49495d862d25e38223b5a056817a5",
    "ReadbackCoordinatorSeams.test_result_write_failure_leaves_predecessor_gate_blocked": "222b654a8da505965f0821be4e7b61eefeb1a5f12e767c72e6123feba909f06d",
    "ReadbackCoordinatorSeams.test_host_alarm_cannot_interrupt_supervisor_cleanup": "29665028886624307beacb4debb33b8582f91bf60951149c0160ae957ed68f98",
    "ReadbackCoordinatorSeams.test_success_finalization_uses_remaining_outer_alarm": "f4a5d8242e91d3792039b94f2f75c8002b7cc5e1b432ce3cc91d46d65d3f1f55",
    "ReadbackCoordinatorSeams.test_uncertain_marker_removal_recreates_pending": "5e3041a6f1e57db4c4c03e97927e1aa88c6d8dfe2b431e71b38319e3851b75bc",
    "ReadbackCPUControls.check_case": "53a03c60a7473af90ba88f2fddf225713036d417cf3c13a0c1e8a6a3105946a4",
    "ReadbackCPUControls.test_q01_actual_synthetic_meshes_load_in_both_libraries": "e7793b38ebedd196c228ce6841642c2546c8ef1f5db552b1b1f824a30087fd34",
    "ReadbackCPUControls.test_q03_actual_synthetic_rotations_load_in_both_libraries": "e09a9c173e4879558da9206549f085a840639a314c22e525fccabc498c7e3dd4",
    "ReadbackCPUControls.test_three_rejects_changed_synthetic_reference": "8b2de031c533e1308efeef130047b0a2b4fcfc1cb6cd2f576e7b3ef832ec05d9",
}
METHOD_IDS = sorted("test_static_tray_readback_v01." + n for n in ORIGINAL_BODIES if ".test_" in n)
NODE_FLAGS = ["--no-addons", "--max-old-space-size=256"]
LIMITS = {"maximum_checks": 12, "host_ms": 30000, "child_work_ms": 28000, "cleanup_ms": 2000,
          "glb_bytes": 8 * 1024 * 1024, "result_bytes": 4 * 1024 * 1024, "log_bytes": 4 * 1024 * 1024}
VALIDATOR_OPTIONS = {"format": "glb", "writeTimestamp": False, "maxIssues": 1000, "allowed_errors": 0,
                     "allowed_warnings": 0, "ignoredIssues": [], "external_resources": "rejected"}
THREE_OPTIONS = {"position_tolerance_m": 0.000005, "matrix_tolerance": 0.000001, "node_count": 14, "mesh_count": 12,
                 "animation_count": 0, "external_resources": "rejected"}
SCOPE = "Three original synthetic CPU cases only; twelve native slots are structural, never execution authority"
PREFIX = "ontokin.current-host-readback-"


def ep(name):
    """A direct child of the evidence parent, owned by this attempt."""
    return E + "/" + ATTEMPT + "-" + name


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def pretty(value):
    return (json.dumps(value, sort_keys=True, indent=1, ensure_ascii=True, allow_nan=False) + "\n").encode("ascii")


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def binding_of(path):
    info = os.lstat(path)
    if not stat.S_ISREG(info.st_mode):
        raise SystemExit("not a regular file: " + path)
    with open(path, "rb") as stream:
        data = stream.read()
    return {"sha256": sha_bytes(data), "size_bytes": len(data), "mode": "0o%03o" % stat.S_IMODE(info.st_mode)}


def descriptor(path):
    return {"path": path, **binding_of(path)}


WRITTEN = []


def write(path, data):
    os.makedirs(os.path.dirname(path), mode=0o755, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    WRITTEN.append(path)
    return {"path": path, "sha256": sha_bytes(data), "size_bytes": len(data), "mode": "0o644"}


def load(path):
    with open(path, "rb") as stream:
        return json.loads(stream.read())


def shell_quote(argv):
    for item in argv:
        if "'" in item or "\n" in item:
            raise SystemExit("argv element cannot be single-quoted: " + repr(item))
    return " ".join("'" + item + "'" for item in argv)


# ---------------------------------------------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------------------------------------------
host = load(HOST)
plan001 = load(PLAN_001)
source_inventory = load(SOURCE_INVENTORY)
dependencies_inventory = load(DEPENDENCIES_INVENTORY)
controls = load(CONTROLS_JSON)
if canonical(host) != open(HOST, "rb").read():
    raise SystemExit("HOST is not in canonical form")
if canonical(plan001) != open(PLAN_001, "rb").read():
    raise SystemExit("plan 001 is not in canonical form")
for rel in (PROVIDER_REL, PROBE_REL, MAP_REL):
    if source_inventory["files"][rel] != binding_of(WT + "/" + rel):
        raise SystemExit("source inventory disagrees with the file: " + rel)
slots = controls["future_qualification_native_slots"]
if len(slots) != 12 or any(slot["maximum_starts"] != 1 for slot in slots):
    raise SystemExit("unexpected native slots")
host_descriptor = descriptor(HOST)
source_descriptor = host["source"]["inventory"]
deps_descriptor = host["dependencies"]["inventory"]
if source_descriptor != descriptor(SOURCE_INVENTORY) or deps_descriptor != descriptor(DEPENDENCIES_INVENTORY):
    raise SystemExit("HOST's inventory descriptors differ from the files")
contract_descriptor = descriptor(CONTRACT_MD)
adoption_descriptor = descriptor(ADOPTION)
if adoption_descriptor != {"path": ADOPTION, "sha256": "872312ed80a63fbb196c17ace42e786b7fe757b710eff41139b125dfaa507937",
                           "size_bytes": 5396, "mode": "0o644"}:
    raise SystemExit("the adoption record differs from PR-01's binding")
if contract_descriptor["sha256"] != "42db98dc6099ee605b0963f3734f7bff2d68c019ff6c00a0ee97bd753c03fdc9":
    raise SystemExit("contract digest differs from the probe's constant")
fixtures = {name: descriptor(OUT + "/fixtures/" + name) for name in (
    "Q01/synthetic.glb", "Q01/synthetic-audit.json", "Q03/synthetic.glb", "Q03/synthetic-audit.json",
    "Q01-changed-reference/synthetic-audit.json")}

# ---------------------------------------------------------------------------------------------------------------
# The methods and discovery documents, and the configurations (config/0.2.0)
# ---------------------------------------------------------------------------------------------------------------
discovery_doc = {"schema": PREFIX + "discovery/0.2.0", "method_ids": METHOD_IDS,
                 "baseline_map": descriptor(WT + "/" + MAP_REL)}
discovery_written = write(OUT + "/config/discovery-001.json", canonical(discovery_doc))
methods_doc = {"schema": PREFIX + "methods/0.2.0", "source_test": "tests/test_static_tray_readback_v01.py",
               "original_bodies": ORIGINAL_BODIES, "discovery": discovery_written}
methods_written = write(OUT + "/config/methods-001.json", canonical(methods_doc))


def config(evidence_root, *, host_desc=host_descriptor, schema=PREFIX + "config/0.2.0"):
    return {"schema": schema, "contract": "ontokin.current-host-readback/0.2.0",
            "contract_source": contract_descriptor, "amendment_adoption": adoption_descriptor,
            "source": {"root": WT, "commit": COMMIT_C, "tree": TREE_C, "inventory": source_descriptor},
            "host": host_desc, "dependencies": {"root": DEPS, "inventory": deps_descriptor},
            "runtime": {"executable": NODE, "version": "v24.22.1"}, "methods": methods_written,
            "evidence_root": evidence_root, "parent": None}


configs = {}
configs["cohort"] = write(OUT + "/config/cohort-config-001.json", canonical(config(ep("cohort"))))
configs["mc29-configuration"] = write(OUT + "/config/mc29-configuration-config-001.json",
                                      canonical(config(ep("mc29-configuration"))))
configs["mc29-job-input"] = write(OUT + "/config/mc29-job-input-config-001.json",
                                  canonical(config(ep("mc29-job-input"))))
D0 = configs["cohort"]["sha256"]

# ---------------------------------------------------------------------------------------------------------------
# The direct-probe rows' fixtures: HOST copies, configurations, manifests and jobs
# ---------------------------------------------------------------------------------------------------------------
host_copies = {}
for name, value in (("mc30", None), ("mc36", CF_ALTERED)):
    copy = deepcopy(host)
    copy["environment"]["cf_user_text_encoding"] = value
    host_copies[name] = write(OUT + "/probe/" + name + "/HOST.json", canonical(copy))


def labels_of(host_doc):
    return {"executor": "macos-arm64-local", "contract": "ontokin.current-host-readback/0.2.0", "design_revision": 4,
            "amendments": ["P33-AMENDMENT-001"], "profile": "darwin-arm64-v1", "run_kind": "qualifying",
            "boundary": "real", "os": host_doc["labels"]["os"], "node": host_doc["labels"]["node"],
            "python_inventory_sha256": host_doc["python"]["inventory_sha256"],
            "git": {"path": host_doc["git"]["path"], "sha256": host_doc["git"]["sha256"]}}


def manifest(cfg, cfg_path, cfg_sha, cohort_root):
    """lock/0.2.0 exactly as current_host_readback_v02._manifest writes it for this selection."""
    schedule = cohort_root + "/unused-native-schedule"
    files = {DEPS + "/" + rel: dict(row) for rel, row in dependencies_inventory["files"].items()}
    for rel in (PROVIDER_REL, PROBE_REL):
        files[WT + "/" + rel] = dict(source_inventory["files"][rel])
    rows = []
    for slot in slots:
        stage = schedule + "/external-readback/" + slot["slot"]
        rows.append({"slot": slot["slot"], "case": slot["case"], "route": slot["route"], "maximum_starts": 1,
                     "stage": stage, "result": stage + "/result.json",
                     "argv": [NODE, *NODE_FLAGS, "--experimental-loader", LOADER, PROBE, "--expected-config-sha256",
                              cfg_sha, "--job", stage + "/job.json"]})
    host_doc = load(cfg["host"]["path"])
    return {"schema": PREFIX + "lock/0.2.0", "contract": "ontokin.current-host-readback/0.2.0", "design_revision": 4,
            "amendments": ["P33-AMENDMENT-001"], "labels": labels_of(host_doc), "profile": "ontokin.static-tray/0.1.0",
            "schedule_root": schedule, "cohort_root": cohort_root, "dependencies_root": DEPS, "scope": SCOPE,
            "limits": LIMITS, "environment": DECLARED, "files": files,
            "runtime": {"executable": NODE, "version": "v24.22.1", "binding": {
                k: host_doc["runtime"]["binding"][k] for k in ("sha256", "size_bytes", "mode")}},
            "validator_version": "2.0.0-dev.3.10", "three_version": "0.186.1",
            "validator_entry": DEPS + "/validator/package/index.js",
            "three_package": DEPS + "/indexer-view/three/package.json",
            "three_entry": DEPS + "/indexer-view/three/build/three.webgpu.js",
            "gltf_loader_entry": DEPS + "/indexer-view/three/examples/jsm/loaders/GLTFLoader.js",
            "module_loader": LOADER, "probe": PROBE, "validator_options": VALIDATOR_OPTIONS,
            "three_options": THREE_OPTIONS, "slots": rows, "selection": {"path": cfg_path, "sha256": cfg_sha},
            "source": cfg["source"], "host": cfg["host"], "methods": cfg["methods"], "dependencies": cfg["dependencies"]}


def job_bytes(stage, manifest_path, manifest_sha, artifact_sha, audit_sha):
    """check_case's job.json, written as json_bytes."""
    return json.dumps({"slot": "CPU-Q01-positive", "case": "Q01", "manifest": manifest_path,
                       "supplemental_manifest_sha256": manifest_sha, "input_lock_sha256": "CPU-ONLY-SYNTHETIC-NOT-NATIVE",
                       "artifact": stage + "/synthetic.glb", "artifact_sha256": artifact_sha,
                       "audit": stage + "/synthetic-audit.json", "audit_sha256": audit_sha,
                       "result": stage + "/probe.json"},
                      sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("ascii")


probe_rows = {}
for name in ("h01", "h02", "mc30", "mc36"):
    root = ep("probe-" + name)
    cohort_root = root + "/cohort"
    stage = cohort_root + "/Q01-positive"
    if name == "h02":
        cfg = config(root, schema=PREFIX + "config/0.1.0")
    elif name in ("mc30", "mc36"):
        cfg = config(root, host_desc=host_copies[name])
    else:
        cfg = config(root)
    cfg_written = write(OUT + "/probe/" + name + "/config.json", canonical(cfg))
    man = manifest(cfg, cfg_written["path"], cfg_written["sha256"], cohort_root)
    man_written = write(OUT + "/probe/" + name + "/supplemental-cpu.json", canonical(man))
    artifact_sha = EMPTY_SHA if name == "mc30" else fixtures["Q01/synthetic.glb"]["sha256"]
    job_written = write(OUT + "/probe/" + name + "/job.json",
                        job_bytes(stage, cohort_root + "/supplemental-cpu.json", man_written["sha256"], artifact_sha,
                                  fixtures["Q01/synthetic-audit.json"]["sha256"]))
    expected_digest = D0 if name == "h01" else cfg_written["sha256"]
    probe_rows[name] = {"root": root, "cohort": cohort_root, "stage": stage, "config": cfg_written,
                        "manifest": man_written, "job": job_written, "argv_digest": expected_digest,
                        "artifact_sha256": artifact_sha,
                        "host": host_copies.get(name, host_descriptor)}

# ---------------------------------------------------------------------------------------------------------------
# The frozen environments (ontokin.c271.p35-unit-environment/1)
# ---------------------------------------------------------------------------------------------------------------
UNIT_BASE = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC",
             "PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1"}
GIT_ENV = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC", "GIT_CONFIG_NOSYSTEM": "1",
           "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_TERMINAL_PROMPT": "0", "GIT_ATTR_NOSYSTEM": "1",
           "GIT_OPTIONAL_LOCKS": "0", "GIT_NO_REPLACE_OBJECTS": "1", "GIT_NO_LAZY_FETCH": "1"}
environments = {
    "declared": dict(DECLARED),
    "runner": {"PATH": "/usr/bin:/bin"},
    "plain": {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC"},
    "git": dict(GIT_ENV),
    "git-worktree": dict(GIT_ENV, GIT_CEILING_DIRECTORIES="<worktrees>"),
    "host-state": dict(UNIT_BASE),
    "cohort": dict(UNIT_BASE, TMPDIR=ep("tmp-cohort"), **{CONFIG_ENV: configs["cohort"]["path"],
                                                          DIGEST_ENV: configs["cohort"]["sha256"]},
                   STATIC_TRAY_READBACK_CPU_OUTPUT=ep("cohort") + "/run"),
    "mc37": dict(UNIT_BASE, TMPDIR=ep("tmp-mc37")),
    "discovery-baseline": dict(UNIT_BASE, TMPDIR=ep("tmp-discovery-baseline")),
    "discovery-current": dict(UNIT_BASE, TMPDIR=ep("tmp-discovery-current")),
}
MC29_COPY = {"configuration": ep("mc29-inputs") + "/configuration-config.json",
             "job-input": ep("mc29-inputs") + "/job-input-config.json"}
for case in ("configuration", "job-input"):
    environments["mc29-" + case] = dict(UNIT_BASE, TMPDIR=ep("tmp-mc29-" + case),
                                        **{CONFIG_ENV: MC29_COPY[case], DIGEST_ENV: configs["mc29-" + case]["sha256"]},
                                        STATIC_TRAY_READBACK_CPU_OUTPUT=ep("mc29-" + case) + "/run")
environment_files = {}
for name, mapping in environments.items():
    if "HOME" in mapping:
        raise SystemExit("HOME in a frozen environment")
    document = {"schema": "ontokin.c271.p35-unit-environment/1", "environment": mapping}
    environment_files[name] = dict(write(OUT + "/env/" + name + ".environment.json", canonical(document)),
                                   names=sorted(mapping), environment=mapping)


def env_assignments(name):
    mapping = environments[name]
    return [key + "=" + mapping[key] for key in sorted(mapping)]


# ---------------------------------------------------------------------------------------------------------------
# MC10: one observation plan per case, each with its own absent attempt (derived from plan 001)
# ---------------------------------------------------------------------------------------------------------------
COMMAND_IDS, LABELS = ("git_version", "node_version"), {"git_version": "host-git-version",
                                                         "node_version": "host-node-version"}


def output_paths(attempt):
    outputs = {key: attempt + "/" + key + ".json" for key in ("reserved", "preflight", "result", "completion", "failure")}
    outputs["host"] = attempt + "/HOST.json"
    for name in COMMAND_IDS:
        stage, label = attempt + "/" + name, LABELS[name]
        outputs[name] = {"stage": stage, "intent": stage + "/intent.json", "started": stage + "/started.json",
                         "inspection": stage + "/inspection.json", "postflight": stage + "/postflight.json",
                         "failure": stage + "/failure.json", "stdout": stage + "/" + label + ".stdout.log",
                         "stderr": stage + "/" + label + ".stderr.log", "process": stage + "/" + label + ".process.json"}
    return outputs


def plan_for(attempt):
    plan = deepcopy(plan001)
    plan["evidence"]["attempt"] = attempt
    plan["evidence"]["outputs"] = output_paths(attempt)
    plan["commands"][0]["cwd"] = attempt + "/git_version"
    plan["commands"][1]["cwd"] = attempt + "/node_version"
    return plan


if canonical(plan_for(E + "/observe-001")) != open(PLAN_001, "rb").read():
    raise SystemExit("the plan derivation does not reproduce plan 001")
MC10_CASES = [
    {"key": "a", "case": "node-v24-22-0", "node_stdout": "v24.22.0\n", "expect": "refused-output"},
    {"key": "b", "case": "node-v24-22-1-without-newline", "node_stdout": "v24.22.1", "expect": "refused-output"},
    {"key": "c", "case": "node-v24-22-1", "node_stdout": "v24.22.1\n", "expect": "accepted"}]
for row in MC10_CASES:
    row["attempt"] = ep("mc10-" + row["case"])
    row["plan"] = write(OUT + "/mc10/observation-plan-mc10-" + row["key"] + ".json", canonical(plan_for(row["attempt"])))
    row["output"] = ep("mc10-" + row["case"]) + ".json"

# ---------------------------------------------------------------------------------------------------------------
# The direct-probe rows documents (ontokin.c271.p35-direct-probe-rows/2)
# ---------------------------------------------------------------------------------------------------------------
STATUS_1 = {"code": "OTRAY-E-BACKEND", "reason": "Child exited with status 1", "state": "REJECTED"}


def expected(**overrides):
    base = {"returncode": 0, "supervisor_error": None, "stdout_exact": None, "stderr_exact": None,
            "stdout_includes": [], "stdout_excludes": [], "stderr_includes": [], "stderr_excludes": [],
            "absent_paths": [], "present_paths": [], "file_includes": {}, "json_members": {}}
    base.update(overrides)
    return base


def stage_inputs(name):
    row = probe_rows[name]
    stage = row["stage"]
    inputs = [
        {"path": stage + "/job.json", **{k: row["job"][k] for k in ("sha256", "size_bytes", "mode")}},
        {"path": stage + "/synthetic.glb", **{k: fixtures["Q01/synthetic.glb"][k] for k in ("sha256", "size_bytes", "mode")}},
        {"path": stage + "/synthetic-audit.json",
         **{k: fixtures["Q01/synthetic-audit.json"][k] for k in ("sha256", "size_bytes", "mode")}},
        {"path": row["cohort"] + "/supplemental-cpu.json",
         **{k: row["manifest"][k] for k in ("sha256", "size_bytes", "mode")}},
        dict(row["config"]), dict(row["host"]), dict(methods_written), dict(discovery_written),
        dict(source_descriptor), dict(deps_descriptor), dict(contract_descriptor), dict(adoption_descriptor)]
    return inputs


STAGE_ENTRIES = [{"path": "job.json", "kind": "file"}, {"path": "synthetic-audit.json", "kind": "file"},
                 {"path": "synthetic.glb", "kind": "file"}]


def probe_argv(name):
    row = probe_rows[name]
    return [NODE, *NODE_FLAGS, "--experimental-loader", LOADER, PROBE, "--expected-config-sha256", row["argv_digest"],
            "--job", row["stage"] + "/job.json"]


def env_refusal_members(name):
    row = probe_rows[name]
    return [{"pointer": "/schema", "equals": "ontokin.current-host-readback-result/0.2.0"},
            {"pointer": "/passed", "equals": False},
            {"pointer": "/error/code", "equals": "OTRAY-E-DELIVERY"},
            {"pointer": "/error/message", "equals": "Current-host binding: actual Node environment differs"},
            {"pointer": "/khronos", "absent": True}, {"pointer": "/three", "absent": True},
            {"pointer": "/input_preserved", "absent": True},
            {"pointer": "/slot", "equals": "CPU-Q01-positive"}, {"pointer": "/case", "equals": "Q01"},
            {"pointer": "/artifact_sha256", "equals": row["artifact_sha256"]},
            {"pointer": "/audit_sha256", "equals": fixtures["Q01/synthetic-audit.json"]["sha256"]},
            {"pointer": "/supplemental_manifest_sha256", "equals": row["manifest"]["sha256"]},
            {"pointer": "/input_lock_sha256", "equals": "CPU-ONLY-SYNTHETIC-NOT-NATIVE"},
            {"pointer": "/node", "equals": "v24.22.1"}, {"pointer": "/native_starts", "equals": 0},
            {"pointer": "/exports", "equals": 0}]


def env_refusal_stdout(name):
    row = probe_rows[name]
    return json.dumps({"passed": False, "slot": "CPU-Q01-positive", "artifact_sha256": row["artifact_sha256"]},
                      separators=(",", ":")) + "\n"


rows_r1 = {"schema": "ontokin.c271.p35-direct-probe-rows/2", "rows_independent": False, "rows": [
    {"id": "probe-syntax-check", "argv": [NODE, *NODE_FLAGS, "--check", PROBE], "stage": ep("probe-syntax"),
     "label": "probe-syntax-check", "environment": dict(DECLARED), "total_ms": 30000, "stage_ms": 28000,
     "inputs": [], "stage_entries": [],
     "expected": expected(returncode=0, supervisor_error=None, stdout_exact="", stderr_exact="")},
    {"id": "P06-H01", "argv": probe_argv("h01"), "stage": probe_rows["h01"]["stage"], "label": "p06-h01",
     "environment": dict(DECLARED), "total_ms": 30000, "stage_ms": 28000, "inputs": stage_inputs("h01"),
     "stage_entries": STAGE_ENTRIES,
     "expected": expected(returncode=1, supervisor_error=STATUS_1, stdout_exact="",
                          stderr_includes=["CH-SELECTION: manifest digest is not external approval"],
                          stderr_excludes=["Current-host binding: wrong configuration contract/schema"],
                          absent_paths=[probe_rows["h01"]["stage"] + "/probe.json"])},
    {"id": "P06-H02", "argv": probe_argv("h02"), "stage": probe_rows["h02"]["stage"], "label": "p06-h02",
     "environment": dict(DECLARED), "total_ms": 30000, "stage_ms": 28000, "inputs": stage_inputs("h02"),
     "stage_entries": STAGE_ENTRIES,
     "expected": expected(returncode=1, supervisor_error=STATUS_1, stdout_exact="",
                          stderr_includes=["Current-host binding: wrong configuration contract/schema"],
                          stderr_excludes=["CH-SELECTION: manifest digest is not external approval"],
                          absent_paths=[probe_rows["h02"]["stage"] + "/probe.json"])}]}
rows_r2 = {"schema": "ontokin.c271.p35-direct-probe-rows/2", "rows_independent": False, "rows": []}
for name, ident in (("mc30", "MC30-probe"), ("mc36", "MC36")):
    rows_r2["rows"].append({
        "id": ident, "argv": probe_argv(name), "stage": probe_rows[name]["stage"], "label": ident.lower(),
        "environment": dict(DECLARED), "total_ms": 30000, "stage_ms": 28000, "inputs": stage_inputs(name),
        "stage_entries": STAGE_ENTRIES,
        "expected": expected(returncode=1, supervisor_error=STATUS_1, stdout_exact=env_refusal_stdout(name),
                             stderr_excludes=["CH-SELECTION", "Current-host binding"],
                             json_members={probe_rows[name]["stage"] + "/probe.json": env_refusal_members(name)})})
rows_files = {"r1": write(OUT + "/probe/rows-r1.json", pretty(rows_r1)),
              "r2": write(OUT + "/probe/rows-r2.json", pretty(rows_r2))}

# ---------------------------------------------------------------------------------------------------------------
# The preparation script (the Director's frozen preparation, run once through the wrapper)
# ---------------------------------------------------------------------------------------------------------------
prep_dirs = [ep("tmp-cohort"), ep("tmp-mc37"), ep("tmp-discovery-baseline"), ep("tmp-discovery-current"),
             ep("tmp-mc29-configuration"), ep("tmp-mc29-job-input"), ep("cohort"), ep("mc29-configuration"),
             ep("mc29-job-input"), ep("mc29-inputs"), ep("export-" + BASE_COMMIT[:8]), ep("export-" + COMMIT_C[:8]),
             ep("probe-syntax")]
prep_copies = [(configs["mc29-configuration"], MC29_COPY["configuration"]),
               (configs["mc29-job-input"], MC29_COPY["job-input"])]
for name in ("h01", "h02", "mc30", "mc36"):
    row = probe_rows[name]
    prep_dirs += [row["root"], row["cohort"], row["stage"]]
    prep_copies += [(row["manifest"], row["cohort"] + "/supplemental-cpu.json"), (row["job"], row["stage"] + "/job.json"),
                    (fixtures["Q01/synthetic.glb"], row["stage"] + "/synthetic.glb"),
                    (fixtures["Q01/synthetic-audit.json"], row["stage"] + "/synthetic-audit.json")]
lines = ["#!/bin/sh",
         "# Operational freeze 001 of gate MH (C271-P35): the Director's frozen preparation for attempt " + ATTEMPT + ".",
         "# Run once, through the wrapper, as: /usr/bin/env -i PATH=... /bin/sh <this file>. It creates only absent",
         "# paths, in this order, and stops at the first refusal or failure (an explicit exit 1, or set -e on a failed",
         "# mkdir or cp); it never replaces, repairs or removes anything (FC-K1). Afterwards D02",
         "# (w2f_s7_check.py prepared) verifies every entry. Written by W2, the author of the freeze.",
         "set -eu", "umask 022",
         "absent() { if [ -e \"$1\" ] || [ -L \"$1\" ]; then echo \"prepare-s7-001: present $1\" >&2; exit 1; fi; }"]
for path in prep_dirs:
    lines.append("absent '%s'; /bin/mkdir -m 0700 '%s'" % (path, path))
for source, target in prep_copies:
    lines.append("absent '%s'; /bin/cp -n '%s' '%s'" % (target, source["path"], target))
lines.append("echo 'prepare-s7-001: done'")
prep_script = write(OUT + "/s7/prepare-s7-001.sh", ("\n".join(lines) + "\n").encode("ascii"))
checker = descriptor(OUT + "/s7/w2f_s7_check.py")

# ---------------------------------------------------------------------------------------------------------------
# Bindings: every input that a command or the checker reads
# ---------------------------------------------------------------------------------------------------------------
bindings = []


def bind(ident, path, role, *, nlink_one=True):
    bindings.append({"id": ident, "path": path, "kind": "file", "role": role, "nlink_one": nlink_one, **binding_of(path)})


for name in ("FAILURE-CAPTURE.md", "README.md", "audit_numeric.py", "capture_probe.py", "collect_outcomes.py",
             "control_harness.py", "discover_inventory.py", "run_direct_probe.py", "scan_mc11.py"):
    bind("tool:" + name, TOOLING + "/" + name, "MH tooling at commit C (TOOLING-SHA256SUMS.txt, revision 3)")
for rel in ("prototypes/__init__.py", "prototypes/static_tray_v01/__init__.py", "prototypes/static_tray_v01/supervisor.py",
            "prototypes/static_tray_v01/supervisor_darwin_v01.py", "prototypes/static_tray_v01/current_host_observation_v02.py",
            "prototypes/static_tray_v01/current_host_readback_v01.py", PROVIDER_REL, PROBE_REL,
            "prototypes/static_tray_v01/format_check.py", "prototypes/static_tray_v01/canonical.py",
            "tests/test_static_tray_readback_v01.py", "tests/test_current_host_readback_controls_v02.py",
            "tests/test_static_tray_reader_v01.py", "tools/check_local.py",
            "tools/native-reader-verification-macos-arm64-cp312.lock",
            "docs/engineering/localized-repair-c271/macos-contract-design-p31/CONTRACT.md",
            "docs/engineering/localized-repair-c271/macos-implementation-p33/ADOPTION-AMENDMENT-001.json",
            "docs/engineering/localized-repair-c271/macos-implementation-p33/INVENTORY-ADDITIONS.json",
            "docs/engineering/localized-repair-c271/macos-implementation-p33/CONTROLS-FROZEN.json",
            "docs/engineering/localized-repair-c271/macos-implementation-p33/CONTROLS-REFREEZE-002.json",
            MAP_REL, "docs/engineering/static-tray-mapping-c198/CONTROLS.json",
            "docs/engineering/static-tray-qualification-c199/EXTERNAL-INPUTS.json",
            "docs/engineering/ownership-recovery-c195/evidence/recorded-evidence.tar.xz", ".git"):
    bind("source:" + rel, WT + "/" + rel, "commit C, in the clean worktree (also in the source inventory where listed)")
for ident, path in (("host:HOST.json", HOST), ("host:completion.json", E + "/observe-001/completion.json"),
                    ("host:result.json", E + "/observe-001/result.json"),
                    ("host:git_version/inspection.json", E + "/observe-001/git_version/inspection.json"),
                    ("host:node_version/inspection.json", E + "/observe-001/node_version/inspection.json")):
    bind(ident, path, "M0 and M1 (attempt observe-001), accepted by HOST review 001 (HR-04)")
for ident, path in (("plan001:observation-plan-001.json", PLAN_001), ("plan001:source-inventory-001.json", SOURCE_INVENTORY),
                    ("plan001:python-inventory-001.json", PYTHON_INVENTORY),
                    ("plan001:dependencies-inventory-001.json", DEPENDENCIES_INVENTORY)):
    bind(ident, path, "S4, accepted by plan review 001; bound by HOST")
for ident, path in (("mp:node", NODE), ("mp:NODE-SOURCE.json", LOCAL + "/c271-macos/node-v24.22.1-darwin-arm64/NODE-SOURCE.json"),
                    ("mp:node-archive", LOCAL + "/c271-p34/downloads/node/node-v24.22.1-darwin-arm64.tar.gz"),
                    ("mp:node-install-plan", plan001["runtime"]["install"]["plan"]["path"]),
                    ("mp:node-install-result", plan001["runtime"]["install"]["result"]["path"]),
                    ("mp:reader-install-plan", plan001["dependencies"]["install"]["plan"]["path"]),
                    ("mp:reader-install-result", plan001["dependencies"]["install"]["result"]["path"])):
    bind(ident, path, "MP's prepared inputs, retained unchanged")
for rel, row in sorted(dependencies_inventory["files"].items()):
    bind("reader:" + rel, DEPS + "/" + rel, "the 24 reader files (dependencies-inventory-001.json)")
    if binding_of(DEPS + "/" + rel) != {k: row[k] for k in ("sha256", "size_bytes", "mode")}:
        raise SystemExit("reader file differs from the inventory: " + rel)
bind("git", GIT, "the developer tools' Git that HOST binds (N-07)")
bind("wrapper:run_once_v2.sh", WRAPPER, "the Director's single-run wrapper (HR-01); epoch fields authoritative")
for path in sorted(WRITTEN):
    bind("freeze:" + os.path.relpath(path, OUT), path, "a document of this freeze, written by W2")
for path in sorted(fixtures):
    bind("freeze:fixtures/" + path, fixtures[path]["path"], "an original synthetic input, built by the project's own builders")
bind("freeze:s7/w2f_s7_check.py", checker["path"], "the Director's S7 checker, part of this freeze")
bind("freeze:mc11/MC11-CANDIDATE-LIST-001.json", OUT + "/mc11/MC11-CANDIDATE-LIST-001.json",
     "the MC11 candidate list (status CANDIDATE, NOT REVIEWED)")
ids = [row["id"] for row in bindings]
if len(ids) != len(set(ids)):
    raise SystemExit("duplicate binding ids")

# ---------------------------------------------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------------------------------------------
commands = []
order = []


def tool_python(env_name, flags, script, *arguments, assignments=None):
    return ["/usr/bin/env", "-i", *(assignments if assignments is not None else env_assignments(env_name)), PY, *flags,
            script, *arguments]


FREEZE_SHA_PLACEHOLDER = "<FREEZE-001.json SHA-256>"
DEFERRED_SOURCES = {}


def add(ident, name, purpose, cwd, env_name, argv, *, outputs, expect, audit_expect=None, starts, limits,
        capture, classification, control=None, deferred=None, absent_before=None, phase="s7"):
    full = ["/bin/sh", WRAPPER, name, cwd, environment_files[env_name]["path"], "--", *argv]
    record = E + "/" + name
    placeholders = [index for index, item in enumerate(argv) if item.startswith("<") and item.endswith(">")]
    deferred_rows = []
    argv_rules = []
    for index in placeholders:
        source = DEFERRED_SOURCES[argv[index]]
        deferred_rows.append({"argv_index": index, "wrapper_argv_index": index + 6, "placeholder": argv[index],
                              "source": source})
        rule = {"file": record + ".command.json", "pointer": "/argv/%d" % index}
        if source["kind"] == "freeze_sha256":
            rule["equals_freeze_sha256"] = True
        elif source["kind"] == "sha256_of_file":
            rule["equals_sha256_of"] = source["file"]
        else:
            rule["equals_from"] = {"file": source["file"], "pointer": source["pointer"]}
        argv_rules.append(rule)
    wrapper_expect = [
        {"file": record + ".command.json", "pointer": "/argv",
         "argv_equals_except": {"argv": argv, "indices": placeholders}}] + argv_rules + [
        {"file": record + ".command.json", "pointer": "/cwd", "equals": cwd},
        {"file": record + ".command.json", "pointer": "/environment/sha256", "equals": environment_files[env_name]["sha256"]},
        {"file": record + ".command.json", "pointer": "/boot/before", "equals": BOOT},
        {"file": record + ".command.json", "pointer": "/boot/after", "equals": BOOT},
        {"file": record + ".command.json", "pointer": "/retries", "equals": 0}]
    if deferred is not None:
        raise SystemExit("deferred arguments are declared through DEFERRED_SOURCES placeholders")
    row = {"id": ident, "phase": phase, "name": name, "purpose": purpose, "control": control, "cwd": cwd,
           "environment": {"name": env_name, "file": environment_files[env_name]["path"],
                           "sha256": environment_files[env_name]["sha256"]},
           "argv": argv, "wrapper_argv": full, "shell": shell_quote(full),
           "deferred_arguments": deferred_rows,
           "records": {"stdout": record + ".stdout.txt", "stderr": record + ".stderr.txt", "exit": record + ".exit.txt",
                       "command": record + ".command.json"},
           "outputs_absent_before": sorted(set((absent_before or []) + outputs + [record + s for s in (
               ".stdout.txt", ".stderr.txt", ".exit.txt", ".command.json")])),
           "outputs": outputs, "expect": wrapper_expect + expect, "audit_expect": audit_expect or [],
           "starts": starts, "limits": limits, "failure_capture": capture, "classification": classification}
    commands.append(row)
    order.append(ident)
    return row


DECL_TOOL = ("declared", ("-I", "-S", "-B"))


def exit_is(name, status):
    return {"file": E + "/" + name + ".exit.txt", "text_equals": "%d\n" % status}


def listing_command(parent, name, dirs, paths, *, purpose=None):
    output = E + "/" + name + ".readback.json"
    argv = tool_python("declared", ("-I", "-S", "-B"), TOOLING + "/capture_probe.py", "listing",
                       *[item for d in dirs for item in ("--dir", d)], *[item for p in paths for item in ("--path", p)],
                       "--output", output)
    lname = name + ".readback-listing"
    add(parent + ".L", lname, purpose or ("FC-K5 readback of " + parent), E, "declared", argv, outputs=[output],
        expect=[exit_is(lname, 0), {"file": output, "pointer": "/command", "equals": "listing"},
                {"file": output, "pointer": "/boot_before", "equals": BOOT},
                {"file": output, "pointer": "/boot_after", "equals": BOOT},
                {"file": output, "pointer": "/process_events", "length": 0},
                {"file": output, "pointer": "/tool/sha256", "equals": binding_of(TOOLING + "/capture_probe.py")["sha256"]}],
        starts={"bounded": {"node": 0, "other": 0}, "recorded_unbounded": {"python_launcher": 1}},
        limits={"outer_bound_s": 600}, capture={"rule": "FC-K5's own record; FC-K2 and FC-K3 by the wrapper"},
        classification=[{"outcome": "exit 0", "class": "COMPLETED"},
                        {"outcome": "exit 2 or 3, or a missing record", "class": "UNKNOWN for " + parent + "'s evidence; "
                         "stop S7 and apply FAILURE-CAPTURE section 6; no retry of the listing (FC-R1)"}])
    return output


def probe_command(parent, name, pairs):
    output = E + "/" + name + ".probes.json"
    argv = tool_python("declared", ("-I", "-S", "-B"), TOOLING + "/capture_probe.py", "probe",
                       *[item for pair in pairs for item in ("--pair", pair[0], pair[1])], "--output", output)
    pname = name + ".probes"
    add(parent + ".P", pname, "FC-P3 probe of every recorded start of " + parent, E, "declared", argv, outputs=[output],
        expect=[exit_is(pname, 0), {"file": output, "pointer": "/command", "equals": "probe"},
                {"file": output, "pointer": "/targets", "length": len(pairs)},
                {"file": output, "pointer": "/targets", "each": {"pointer": "/state", "equals": "absent"}},
                {"file": output, "pointer": "/boot_after", "equals": BOOT},
                {"file": output, "pointer": "/process_events", "length": 0}],
        starts={"bounded": {"node": 0, "other": 0}, "recorded_unbounded": {"python_launcher": 1}},
        limits={"outer_bound_s": 600}, capture={"rule": "FC-P3; FC-P6 only for a state 'present, identity established'"},
        classification=[
            {"outcome": "every target absent", "class": "COMPLETED"},
            {"outcome": "a target 'present, identity established'", "class": "UNKNOWN: run FC-P6 (capture_probe.py stop "
             "--pair BEFORE AFTER --output <name>.stop.json) for that pair only; the attempt stays failed or unknown"},
            {"outcome": "a target 'present, identity not established' or 'unknown'", "class":
             "UNKNOWN: nothing is sent (FC-P6, TR2-04: an exited unreaped process cannot be told from such a process)"}])
    return output


DEFERRED_SOURCES[FREEZE_SHA_PLACEHOLDER] = {
    "kind": "freeze_sha256",
    "description": "the SHA-256 of FREEZE-001.json as the record of freeze review 001 states it, which the Director's "
                   "disposition of that review repeats; the checker refuses any other value (it hashes the file)"}


def expect_command(parent, name):
    ename = name + ".expect"
    argv = tool_python("declared", ("-I", "-S", "-B"), checker["path"], "--freeze", OUT + "/FREEZE-001.json",
                       "--freeze-sha256", FREEZE_SHA_PLACEHOLDER, "expect", "--command", parent)
    add(parent + ".X", ename, "the frozen predicates of " + parent + " (the stop rule)", E, "declared", argv, outputs=[],
        expect=[exit_is(ename, 0), {"file": E + "/" + ename + ".stdout.txt", "text_includes": '"state": "MET"'}],
        starts={"bounded": {"node": 0, "other": 0}, "recorded_unbounded": {"python_launcher": 1}},
        limits={"outer_bound_s": 120}, capture={"rule": "FC-K2 and FC-K3 by the wrapper; it writes nothing"},
        classification=[{"outcome": "exit 0, state MET", "class": "continue with the next command"},
                        {"outcome": "exit 1, state NOT_MET", "class": "stop S7; apply " + parent + "'s classification"},
                        {"outcome": "exit 2", "class": "PLAN: the checker or the freeze digest; stop"}])


# ---- C01: MC11 ------------------------------------------------------------------------------------------------
MC11_REVIEWED = W3F + "/MC11-REVIEWED-LIST-001.json"
DEFERRED_SOURCES["<MC11 reviewed list SHA-256>"] = {
    "kind": "sha256_of_file", "file": MC11_REVIEWED,
    "description": "the SHA-256 of the reviewed list that freeze review 001 writes at this path (status REVIEWED, the "
                   "reviewer's identity, every candidate entry reviewed), as the Director's disposition of that review "
                   "records it; P01 reports the file's digest, and C01.X checks that the argument is that file's digest"}
name = ATTEMPT + "-c01-mc11-scan"
mc11_out = ep("mc11-scan.json")
add("C01", name, "MC11: the reviewed static scan of the probe, the module loader and the 24 reader files", E, "declared",
    tool_python("declared", ("-I", "-S", "-B"), TOOLING + "/scan_mc11.py", "--probe", PROBE, "--probe-sha256",
                binding_of(PROBE)["sha256"], "--dependencies-root", DEPS, "--dependencies-inventory", DEPENDENCIES_INVENTORY,
                "--dependencies-inventory-sha256", deps_descriptor["sha256"], "--reviewed", MC11_REVIEWED,
                "--reviewed-sha256", "<MC11 reviewed list SHA-256>", "--output", mc11_out),
    control="MC11", outputs=[mc11_out],
    expect=[exit_is(name, 0), {"file": mc11_out, "pointer": "/frozen_rule/passed", "equals": True},
            {"file": mc11_out, "pointer": "/frozen_rule/process_creation_none", "equals": True},
            {"file": mc11_out, "pointer": "/frozen_rule/dynamic_hits", "equals": 587},
            {"file": mc11_out, "pointer": "/frozen_rule/unreviewed_dynamic_hits", "equals": 0},
            {"file": mc11_out, "pointer": "/none_found", "equals": True},
            {"file": mc11_out, "pointer": "/reviewed_list_matches", "equals": True},
            {"file": mc11_out, "pointer": "/unresolved_relative_specifiers", "length": 0},
            {"file": mc11_out, "pointer": "/totals/process_creation", "equals": 0},
            {"file": mc11_out, "pointer": "/inputs/reviewed/status", "equals": "REVIEWED"}],
    audit_expect=[{"file": mc11_out, "pointer": "/totals/dynamic", "equals": 628},
                  {"file": mc11_out, "pointer": "/totals/process_call_names", "equals": 23},
                  {"file": mc11_out, "pointer": "/totals/specifiers", "equals": 53}],
    starts={"bounded": {"node": 0, "other": 0}, "recorded_unbounded": {"python_launcher": 1}, "tool_refuses_processes": True},
    limits={"outer_bound_s": 600, "expected_wall_s": 3},
    capture={"listing": "C01.L", "probe": None},
    classification=[
        {"outcome": "exit 0", "class": "COMPLETED: MC11 met"},
        {"outcome": "exit 1 with a process-creation hit in any view or the frozen rule's process_creation_none false",
         "class": "CONTRACT: the no-descendant property of contract section 5 fails for the bound code; MH stops"},
        {"outcome": "exit 1 with unreviewed or reviewed-but-absent hits, unequal specifiers or an unresolved relative specifier",
         "class": "PLAN: the reviewed list or this expectation is wrong; corrected freeze and list, reviewed, new attempt"},
        {"outcome": "exit 2 DIGEST or TREE on the probe, the inventory or a reader file",
         "class": "INPUT changed (or a wrong frozen digest, then PLAN); MH stops for reconciliation"},
        {"outcome": "exit 2 REVIEWED", "class": "PLAN: the reviewed list is malformed or unreviewed"},
        {"outcome": "exit 3, an interruption or a missing record", "class": "UNKNOWN"}])
listing_command("C01", name, [], [mc11_out])
expect_command("C01", name)

# ---- C02: F-04, the provider's real host_state ---------------------------------------------------------------
name = ATTEMPT + "-c02-host-state"
hs_out = ep("host-state.json")
add("C02", name, "F-04: the provider's real host_state against HOST, with nothing substituted", WT, "host-state",
    tool_python("host-state", ("-B",), TOOLING + "/control_harness.py", "host-state", "--root", WT, "--host", HOST,
                "--host-sha256", host_descriptor["sha256"], "--output", hs_out),
    control="F-04 (MC09's real reader)", outputs=[hs_out],
    expect=[exit_is(name, 0), {"file": hs_out, "pointer": "/state", "equals": "EXPECTED"},
            {"file": hs_out, "pointer": "/checks/boundary_real", "equals": True},
            {"file": hs_out, "pointer": "/checks/state_equals_host", "equals": True},
            {"file": hs_out, "pointer": "/checks/zero_process_starts", "equals": True},
            {"file": hs_out, "pointer": "/boot_record/boot_session_uuid", "equals": BOOT},
            {"file": hs_out, "pointer": "/substituted", "length": 0}],
    starts={"bounded": {"node": 0, "other": 0}, "recorded_unbounded": {"python_launcher": 1}, "tool_refuses_processes": True},
    limits={"outer_bound_s": 120, "expected_wall_s": 1}, capture={"listing": "C02.L", "probe": None},
    classification=[
        {"outcome": "exit 0", "class": "COMPLETED"},
        {"outcome": "exit 1, state_equals_host false", "class": "HOST: the boot, kernel or OS identity changed since HOST; "
         "the attempt ends (FC-R5); a new boot restarts S4"},
        {"outcome": "exit 1, boundary_real false or a process event", "class": "IMPLEMENTATION; MH stops"},
        {"outcome": "exit 2", "class": "PLAN (a frozen argument) or INPUT (HOST changed); stop"},
        {"outcome": "exit 3 or missing record", "class": "UNKNOWN"}])
listing_command("C02", name, [], [hs_out])
expect_command("C02", name)

# ---- C03-C05: MC10 --------------------------------------------------------------------------------------------
OBS_BINDS = ["prototypes/__init__.py", "prototypes/static_tray_v01/__init__.py", "prototypes/static_tray_v01/supervisor.py",
             "prototypes/static_tray_v01/current_host_observation_v02.py"]
for index, row in enumerate(MC10_CASES):
    ident = "C%02d" % (3 + index)
    name = ATTEMPT + "-c%02d-mc10-%s" % (3 + index, row["case"])
    out = row["output"]
    argv = tool_python("declared", ("-I", "-S", "-B"), TOOLING + "/control_harness.py", "mc10", "--root", WT,
                       "--plan", row["plan"]["path"], "--plan-sha256", row["plan"]["sha256"],
                       *[item for rel in OBS_BINDS for item in ("--bind", rel + "=" + binding_of(WT + "/" + rel)["sha256"])],
                       "--git-stdout-hex", GIT_LINE.encode("ascii").hex(),
                       "--node-stdout-hex", row["node_stdout"].encode("ascii").hex(), "--expect", row["expect"],
                       "--output", out)
    common = [exit_is(name, 0), {"file": out, "pointer": "/state", "equals": "EXPECTED"},
              {"file": out, "pointer": "/checks/zero_process_starts", "equals": True},
              {"file": out, "pointer": "/checks/both_commands_reached_the_boundary", "equals": True},
              {"file": out, "pointer": "/checks/only_the_harness_row_excluded", "equals": True},
              {"file": out, "pointer": "/checks/labelled_mocked", "equals": True},
              {"file": out, "pointer": "/excluded_loaded_module_rows", "each": {"pointer": "/name", "equals": "__main__"}},
              {"file": out, "pointer": "/excluded_loaded_module_rows", "each": {
                  "pointer": "/file", "equals": TOOLING + "/control_harness.py"}},
              {"file": out, "pointer": "/process_events", "length": 0},
              {"file": out, "pointer": "/tool/sha256", "equals": binding_of(TOOLING + "/control_harness.py")["sha256"]}]
    if row["expect"] == "refused-output":
        specific = [{"file": out, "pointer": "/checks/refused_with_output", "equals": True},
                    {"file": out, "pointer": "/checks/no_host", "equals": True},
                    {"file": out, "pointer": "/checks/not_observed", "equals": True},
                    {"file": out, "pointer": "/checks/not_finalized", "equals": True},
                    {"file": out, "pointer": "/checks/no_host_or_completion_file", "equals": True},
                    {"file": row["attempt"] + "/HOST.json", "exists": False},
                    {"file": row["attempt"] + "/completion.json", "exists": False}]
    else:
        specific = [{"file": out, "pointer": "/checks/accepted", "equals": True},
                    {"file": out, "pointer": "/checks/host_labelled_mocked", "equals": True},
                    {"file": out, "pointer": "/checks/host_runtime_version", "equals": True},
                    {"file": row["attempt"] + "/completion.json", "pointer": "/state", "equals": "OBSERVED_UNAPPROVED"},
                    {"file": row["attempt"] + "/HOST.json", "pointer": "/labels/boundary", "equals": "mocked"}]
    add(ident, name, "MC10 (F-01): the observer's real observe_host with M0's real static bindings; the command boundary "
        "answers Node stdout %r and HOST's Git line; expected %s" % (row["node_stdout"], row["expect"]), E, "declared", argv,
        control="MC10", outputs=[out], absent_before=[row["attempt"]], expect=common + specific,
        starts={"bounded": {"node": 0, "other": 0}, "simulated_at_the_command_boundary": 2,
                "recorded_unbounded": {"python_launcher": 1}, "tool_refuses_processes": True},
        limits={"outer_bound_s": 600, "expected_wall_s": 5, "observer_limits": "plan 001's limits (static_ms 60000)"},
        capture={"listing": ident + ".L", "probe": None},
        classification=[
            {"outcome": "exit 0", "class": "COMPLETED"},
            {"outcome": "refused at PYTHON-MODULE for a row other than the excluded __main__", "class":
             "PLAN (tooling limit, T-01): MC10 stays NOT_RUN in a corrected freeze with the finding recorded"},
            {"outcome": "refused at PLAN, PATH or EVIDENCE-FRESH", "class": "PLAN: the mc10 plan or its attempt"},
            {"outcome": "refused at SOURCE, PYTHON, RUNTIME, DEPENDENCY, GIT, OS or ENVIRONMENT", "class":
             "INPUT or HOST changed; MH stops for reconciliation (a boot change restarts S4)"},
            {"outcome": "a process event, or the accepted case refused at OUTPUT, or a refused case accepted",
             "class": "IMPLEMENTATION; MH stops"},
            {"outcome": "exit 3 or missing record", "class": "UNKNOWN"}])
    planned = []
    for key, value in sorted(output_paths(row["attempt"]).items()):
        planned += sorted(value.values()) if isinstance(value, dict) else [value]
    listing_command(ident, name, [row["attempt"]], [out] + sorted(planned))
    expect_command(ident, name)

# ---- C06-C07: MC29 with the real detectors ---------------------------------------------------------------------
MC29_EXPECT = {"configuration": ("CH-SELECTION", "CH-SELECTION", "Configuration differs from the independently supplied "
                                 "expected digest", "Configuration differs from the independently supplied expected digest", 15),
               "job-input": ("CH-JOB", "CH-EVIDENCE", "Actual CPU input digest differs",
                             "Completed cohort is missing or has extra checker attempts", 25)}
for index, case in enumerate(("configuration", "job-input")):
    ident = "C%02d" % (6 + index)
    name = ATTEMPT + "-c%02d-mc29-%s" % (6 + index, case)
    out = ep("mc29-" + case + ".json")
    attempt_code, finish_code, attempt_reason, finish_reason, git_reads = MC29_EXPECT[case]
    env_name = "mc29-" + case
    run_root = ep("mc29-" + case) + "/run"
    argv = tool_python(env_name, ("-B",), TOOLING + "/control_harness.py", "mc29", "--root", WT,
                       "--config", MC29_COPY[case], "--config-sha256", configs["mc29-" + case]["sha256"],
                       "--glb", fixtures["Q01/synthetic.glb"]["path"], "--glb-sha256", fixtures["Q01/synthetic.glb"]["sha256"],
                       "--audit", fixtures["Q01/synthetic-audit.json"]["path"],
                       "--audit-sha256", fixtures["Q01/synthetic-audit.json"]["sha256"],
                       "--environment", environment_files[env_name]["path"],
                       "--environment-sha256", environment_files[env_name]["sha256"], "--change", case,
                       "--expect-code", attempt_code, "--output", out)
    expect_rows = [exit_is(name, 0), {"file": out, "pointer": "/state", "equals": "EXPECTED"}] + [
        {"file": out, "pointer": "/checks/" + key, "equals": True} for key in (
            "setup_passed", "change_applied_once", "attempt_refused_by_the_provider", "zero_supervisor_calls",
            "zero_on_started_calls", "zero_node_process_events", "refusal_counts_zero_starts",
            "ledger_zero_starts_not_completed", "ledger_labelled_mocked", "accounting_refused",
            "detectors_are_the_providers_own", "refusal_code")] + [
        {"file": out, "pointer": "/attempt_error/code", "equals": attempt_code},
        {"file": out, "pointer": "/attempt_error/reason", "equals": attempt_reason},
        {"file": out, "pointer": "/finish_error/code", "equals": finish_code},
        {"file": out, "pointer": "/finish_error/reason", "equals": finish_reason},
        {"file": out, "pointer": "/refusal_record/schema", "equals": PREFIX + "refusal/0.2.0"},
        {"file": out, "pointer": "/cohort_root", "equals": run_root},
        {"file": out, "pointer": "/boundary_before", "equals": "real"},
        {"file": out, "pointer": "/boundary_during", "equals": "mocked"},
        {"file": out, "pointer": "/node_process_events", "length": 0},
        {"file": out, "pointer": "/environment/admitted_cf_user_text_encoding", "equals": CF_VALUE},
        {"file": run_root + "/setup.json", "pointer": "/passed", "equals": True},
        {"file": run_root + "/cohort.json", "pointer": "/schema", "equals": PREFIX + "cohort/0.2.0"},
        {"file": run_root + "/cohort.json", "pointer": "/passed", "equals": False},
        {"file": run_root + "/cohort.json", "pointer": "/error/code", "equals": finish_code},
        {"file": run_root + "/provider-ledgers/Q01-positive/result.json", "pointer": "/actual_checker_starts", "equals": 0},
        {"file": run_root + "/provider-ledgers/Q01-positive/started.json", "exists": False}]
    add(ident, name, "MC29 (F-03): the 0.2.0 provider's real detectors, one real %s change after preflight.json; "
        "the supervisor is a recorder that starts nothing" % case, WT, env_name, argv, control="MC29", outputs=[out],
        absent_before=[run_root], expect=expect_rows,
        audit_expect=[{"file": out, "pointer": "/git_process_events", "equals": git_reads},
                      {"file": out, "pointer": "/process_events", "count_where": {"pointer": "/argv/0", "equals": GIT},
                       "equals": git_reads}],
        starts={"bounded": {"node": 0, "other": 0}, "recorded_unbounded": {"provider_git_reads": git_reads,
                                                                           "python_launcher": 1},
                "note": "the provider's bound Git reads are recorded by the harness's audit hook, not bounded (TR-14)"},
        limits={"outer_bound_s": 600, "expected_wall_s": 15, "provider_clock": "the attempt's Clock(total_ms=30000), "
                "stage_end = started + 28 s"},
        capture={"listing": ident + ".L", "probe": None,
                 "note": "zero starts: no started record exists, so FC-P3 has no pair; the Git reads have no record"},
        classification=[
            {"outcome": "exit 0 and every predicate", "class": "COMPLETED"},
            {"outcome": "setup_passed false with a SCHEMA or SELECTION refusal of this configuration copy",
             "class": "PLAN: corrected configuration, reviewed, new attempt"},
            {"outcome": "setup_passed false with SOURCE, HOST, RUNTIME, DEPENDENCY or EVIDENCE",
             "class": "INPUT or HOST changed (worktree, HOST, Python trees, runtime, reader tree); MH stops"},
            {"outcome": "the attempt not refused, a supervisor call, an on_started call or a Node event",
             "class": "IMPLEMENTATION: a missed time-of-use detection; MH stops"},
            {"outcome": "another refusal code or reason, or finish_error other than frozen", "class":
             "PLAN if the recorded reason names a file this freeze binds wrongly; otherwise IMPLEMENTATION; MH stops"},
            {"outcome": "exit 2 (ENVIRONMENT, SELECTION, INPUT, PROVIDER-PRECONDITION, USAGE)",
             "class": "PLAN (this command or its copy) unless a bound input changed; zero starts"},
            {"outcome": "exit 3 or missing record", "class": "UNKNOWN"}])
    listing_command(ident, name, [ep("mc29-" + case), ep("mc29-inputs"), ep("tmp-mc29-" + case)], [out])
    expect_command(ident, name)

# ---- C08-C11: MC28's two exports (the Director's Git reads, then tar) ------------------------------------------
for index, (commit, label) in enumerate(((BASE_COMMIT, "1c2f25ba"), (COMMIT_C, "0eb9a551"))):
    ident_export, ident_extract = "C%02d" % (8 + 2 * index), "C%02d" % (9 + 2 * index)
    tar = ep("export-" + label + ".tar")
    target = ep("export-" + label)
    name = ATTEMPT + "-c%02d-export-%s" % (8 + 2 * index, label)
    argv = ["/usr/bin/env", "-i", *env_assignments("git"), GIT, "--git-dir=" + GIT_DIR, "-c", "core.fsmonitor=false",
            "archive", "--format=tar", "--output=" + tar, commit]
    add(ident_export, name, "MC28: the Director's read-only export of commit %s's tree (git archive), with docs/ (T-06)" % commit,
        E, "git", argv, control="MC28", outputs=[tar],
        expect=[exit_is(name, 0), {"file": E + "/" + name + ".stdout.txt", "text_equals": ""},
                {"file": E + "/" + name + ".stderr.txt", "text_equals": ""}, {"file": tar, "exists": True}],
        starts={"bounded": {"node": 0, "other": 0}, "recorded_unbounded": {"director_git_read": 1}},
        limits={"outer_bound_s": 600, "expected_wall_s": 10},
        capture={"listing": ident_export + ".L", "probe": None,
                 "note": "the tar's SHA-256 is recorded by the listing, not predicted"},
        classification=[{"outcome": "exit 0, empty streams", "class": "COMPLETED"},
                        {"outcome": "any other", "class": "PLAN: the export as frozen did not run; stop"}])
    listing_command(ident_export, name, [], [tar])
    expect_command(ident_export, name)
    name = ATTEMPT + "-c%02d-extract-%s" % (9 + 2 * index, label)
    argv = ["/usr/bin/env", "-i", *env_assignments("plain"), "/usr/bin/tar", "-x", "-f", tar, "-C", target]
    add(ident_extract, name, "MC28: extract the export into its prepared empty directory", E, "plain", argv, control="MC28",
        outputs=[], expect=[exit_is(name, 0), {"file": E + "/" + name + ".stdout.txt", "text_equals": ""},
                            {"file": E + "/" + name + ".stderr.txt", "text_equals": ""},
                            {"file": target + "/tools/check_local.py", "exists": True},
                            {"file": target + "/tests", "exists": True}, {"file": target + "/docs", "exists": True}],
        starts={"bounded": {"node": 0, "other": 0}, "recorded_unbounded": {"tar": 1}},
        limits={"outer_bound_s": 600, "expected_wall_s": 10}, capture={"listing": ident_extract + ".L", "probe": None},
        classification=[{"outcome": "exit 0, empty streams", "class": "COMPLETED"},
                        {"outcome": "any other", "class": "PLAN; stop"}])
    listing_command(ident_extract, name, [target], [])
    expect_command(ident_extract, name)

# ---- C12-C14: MC28 discovery and comparison --------------------------------------------------------------------
DISCOVERY_FIGURES = {
    "baseline": {"root": ep("export-1c2f25ba"), "count": 5587, "modules": 382,
                 "sha": "bcc36ee7fce24c05e1f3515cabf2830ab734328005042d7ddb0cdf2ada5e854f", "env": "discovery-baseline"},
    "current": {"root": ep("export-0eb9a551"), "count": 5994, "modules": 388,
                "sha": "32b2b8618464fc10a1ac0b8aa2dad35dfaebd945e9aa5341a31001d1fefe3c1b", "env": "discovery-current"}}
discovery_outputs = {}
for index, which in enumerate(("baseline", "current")):
    ident = "C%02d" % (12 + index)
    figures = DISCOVERY_FIGURES[which]
    name = ATTEMPT + "-c%02d-discovery-%s" % (12 + index, which)
    out = ep("discovery-" + which + ".json")
    discovery_outputs[which] = (ident, name, out)
    argv = tool_python(figures["env"], ("-B",), TOOLING + "/discover_inventory.py", "discover", "--root", figures["root"],
                       "--environment", environment_files[figures["env"]]["path"],
                       "--environment-sha256", environment_files[figures["env"]]["sha256"], "--output", out)
    add(ident, name, "MC28: the default unittest inventory of the %s export, as the unit stage discovers it" % which, E,
        figures["env"], argv, control="MC28", outputs=[out],
        expect=[exit_is(name, 0), {"file": out, "pointer": "/state", "equals": "COMPLETE"},
                {"file": out, "pointer": "/count", "equals": figures["count"]},
                {"file": out, "pointer": "/unique_count", "equals": figures["count"]},
                {"file": out, "pointer": "/failed_imports", "length": 0},
                {"file": out, "pointer": "/process_events", "length": 0},
                {"file": out, "pointer": "/bytecode_present", "length": 0},
                {"file": out, "pointer": "/duplicates", "length": 0},
                {"file": out, "pointer": "/environment/admitted_cf_user_text_encoding", "equals": CF_VALUE}],
        audit_expect=[{"file": out, "pointer": "/module_count", "equals": figures["modules"]},
                      {"file": out, "pointer": "/sorted_sha256", "equals": figures["sha"]},
                      {"file": out, "pointer": "/unit_stage/interpreter_flags_added_by_build_plan", "equals": ["-B"]}],
        starts={"bounded": {"node": 0, "other": 0}, "recorded_unbounded": {"python_launcher": 1},
                "tool_refuses_processes": True},
        limits={"outer_bound_s": 600, "expected_wall_s": 5},
        capture={"listing": ident + ".L", "probe": None},
        classification=[
            {"outcome": "exit 0 and the predicates", "class": "COMPLETED"},
            {"outcome": "baseline: findings or another count", "class": "PLAN: this freeze predicted the baseline from "
             "MI's export (5,587); a fresh export that differs needs a corrected freeze"},
            {"outcome": "current: findings (import failure, process event, duplicate, bytecode) or another count",
             "class": "IMPLEMENTATION: the qualifying source's default inventory is not clean or not the approved one; MH stops"},
            {"outcome": "exit 2 UNIT-STAGE, ENVIRONMENT or PYTHON", "class": "PLAN; stop"},
            {"outcome": "exit 3 or missing record", "class": "UNKNOWN"}])
    listing_command(ident, name, [ep("tmp-discovery-" + which)], [out])
    expect_command(ident, name)
name = ATTEMPT + "-c14-discovery-compare"
out = ep("discovery-compare.json")
base_listing = E + "/" + discovery_outputs["baseline"][1] + ".readback.json"
current_listing = E + "/" + discovery_outputs["current"][1] + ".readback.json"
argv = tool_python("declared", ("-I", "-S", "-B"), TOOLING + "/discover_inventory.py", "compare",
                   "--current", discovery_outputs["current"][2], "--current-sha256", "<current discovery SHA-256>",
                   "--baseline", discovery_outputs["baseline"][2], "--baseline-sha256", "<baseline discovery SHA-256>",
                   "--additions", ADDITIONS, "--additions-sha256", binding_of(ADDITIONS)["sha256"], "--output", out)


def listing_pointer(path):
    return "/paths/" + path.replace("~", "~0").replace("/", "~1") + "/sha256"


DEFERRED_SOURCES["<current discovery SHA-256>"] = {
    "kind": "value_from", "file": current_listing, "pointer": listing_pointer(discovery_outputs["current"][2]),
    "description": "the SHA-256 that C13's FC-K5 readback (capture_probe.py listing) records for the current discovery"}
DEFERRED_SOURCES["<baseline discovery SHA-256>"] = {
    "kind": "value_from", "file": base_listing, "pointer": listing_pointer(discovery_outputs["baseline"][2]),
    "description": "the SHA-256 that C12's FC-K5 readback (capture_probe.py listing) records for the baseline discovery"}
add("C14", name, "MC28: the current inventory against the baseline plus exactly the 407 approved additions", E, "declared",
    argv, control="MC28", outputs=[out],
    expect=[exit_is(name, 0), {"file": out, "pointer": "/exact_match", "equals": True},
            {"file": out, "pointer": "/missing", "length": 0}, {"file": out, "pointer": "/extra", "length": 0},
            {"file": out, "pointer": "/expected_count", "equals": 5994},
            {"file": out, "pointer": "/current_count", "equals": 5994},
            {"file": out, "pointer": "/baseline/count", "equals": 5587},
            {"file": out, "pointer": "/additions/added", "equals": 407},
            {"file": out, "pointer": "/additions_already_in_baseline", "length": 0}] + [
        {"file": out, "pointer": "/consistency/" + key, "equals": True} for key in (
            "added_unique", "added_count_matches", "removed_count_matches", "added_by_module_matches",
            "baseline_count_matches_base_count", "candidate_count_matches", "additions_not_in_baseline",
            "removals_in_baseline")],
    starts={"bounded": {"node": 0, "other": 0}, "recorded_unbounded": {"python_launcher": 1}},
    limits={"outer_bound_s": 120, "expected_wall_s": 1}, capture={"listing": "C14.L", "probe": None},
    classification=[{"outcome": "exit 0", "class": "COMPLETED: MC28 met"},
                    {"outcome": "missing or extra IDs", "class": "IMPLEMENTATION: an unapproved change of the default "
                     "inventory (MC28, MI F-05); MH stops"},
                    {"outcome": "a consistency check false", "class": "PLAN; stop"},
                    {"outcome": "exit 2 DIGEST or SCHEMA", "class": "PLAN (a deferred digest copied wrongly); stop"},
                    {"outcome": "exit 3", "class": "UNKNOWN"}])
listing_command("C14", name, [], [out])
expect_command("C14", name)

# ---- C15: MC37 again ----------------------------------------------------------------------------------------
name = ATTEMPT + "-c15-mc37"
out_dir = ep("mc37-outcomes")
argv = tool_python("mc37", ("-B",), TOOLING + "/collect_outcomes.py", "controls", "--root", WT,
                   "--environment", environment_files["mc37"]["path"], "--environment-sha256", environment_files["mc37"]["sha256"],
                   "--module-sha256", CONTROL_MODULE_SHA, "--test", MC37_TEST, "--output-dir", out_dir)
add("C15", name, "MC37 again (AMENDMENT-001): MI's frozen control on this host; one Python child", WT, "mc37", argv,
    control="MC37", outputs=[out_dir],
    expect=[exit_is(name, 0), {"file": out_dir + "/outcomes.json", "pointer": "/state", "equals": "ALL_PASSED"},
            {"file": out_dir + "/outcomes.json", "pointer": "/tests", "length": 1},
            {"file": out_dir + "/outcomes.json", "pointer": "/tests/0/raw_id", "equals": MC37_TEST},
            {"file": out_dir + "/outcomes.json", "pointer": "/tests/0/outcome", "equals": "pass"},
            {"file": out_dir + "/outcomes.json", "pointer": "/class_level_events", "length": 0},
            {"file": out_dir + "/outcomes.json", "pointer": "/unplanned_events", "length": 0},
            {"file": out_dir + "/outcomes.json", "pointer": "/module/sha256", "equals": CONTROL_MODULE_SHA},
            {"file": out_dir + "/outcomes.json", "pointer": "/process_events", "length": 1},
            {"file": out_dir + "/outcomes.json", "pointer": "/process_events/0/event", "equals": "subprocess.Popen"},
            {"file": out_dir + "/outcomes.json", "pointer": "/process_events/0/argv/0", "equals": PY},
            {"file": out_dir + "/outcomes.json", "pointer": "/process_events/0/argv/1", "equals": "-I"},
            {"file": out_dir + "/outcomes.json", "pointer": "/environment/admitted_cf_user_text_encoding", "equals": CF_VALUE},
            {"file": E + "/" + name + ".stderr.txt", "text_includes": 'CONTROL-EVIDENCE {"case": "MC37", "raw_reaped": "ESRCH"'}],
    starts={"bounded": {"node": 0, "other": 1}, "recorded_unbounded": {"python_launcher": 1},
            "note": "the one other start is the test's own Python child (sys.executable -I -S -B -c ...), counted by the "
                    "collector's audit event; it has no started record, so FC-P3 has no pair (stated limit)"},
    limits={"outer_bound_s": 300, "expected_wall_s": 5}, capture={"listing": "C15.L", "probe": None},
    classification=[{"outcome": "exit 0", "class": "COMPLETED: MC37 met on this host"},
                    {"outcome": "the test fails: the unreaped child counted absent, or ESRCH while unreaped",
                     "class": "CONTRACT: P33-AMENDMENT-001's group-probe premise fails on this host; MH stops"},
                    {"outcome": "the test errors, or another start", "class": "IMPLEMENTATION; MH stops"},
                    {"outcome": "exit 2", "class": "PLAN; zero starts; stop"},
                    {"outcome": "exit 3 or missing record", "class": "UNKNOWN"}])
listing_command("C15", name, [out_dir, ep("tmp-mc37")], [])
expect_command("C15", name)

# ---- C16: R1 (probe syntax check, P06-H01, P06-H02) -----------------------------------------------------------
RUNNER_BINDS = ["prototypes/__init__.py", "prototypes/static_tray_v01/__init__.py", "prototypes/static_tray_v01/supervisor.py",
                "prototypes/static_tray_v01/supervisor_darwin_v01.py"]


def runner(ident, label, rows_key, rows_doc, extra_dirs):
    name = ATTEMPT + "-%s-direct-probe-%s" % (ident.lower(), label)
    out_dir = ep(label)
    argv = tool_python("runner", ("-I", "-S", "-B"), TOOLING + "/run_direct_probe.py", "--root", WT,
                       *[item for rel in RUNNER_BINDS for item in ("--bind", rel + "=" + binding_of(WT + "/" + rel)["sha256"])],
                       "--rows", rows_files[rows_key]["path"], "--rows-sha256", rows_files[rows_key]["sha256"],
                       "--node", NODE, "--node-sha256", binding_of(NODE)["sha256"], "--probe", PROBE,
                       "--probe-sha256", binding_of(PROBE)["sha256"], "--loader", LOADER,
                       "--loader-sha256", binding_of(LOADER)["sha256"], "--output-dir", out_dir)
    n = len(rows_doc["rows"])
    rules = [exit_is(name, 0), {"file": out_dir + "/run.json", "pointer": "/state", "equals": "ALL_ROWS_MET"},
             {"file": out_dir + "/run.json", "pointer": "/node_starts/exact", "equals": n},
             {"file": out_dir + "/run.json", "pointer": "/rows", "length": n},
             {"file": out_dir + "/run.json", "pointer": "/rows", "each": {"pointer": "/state", "equals": "COMPLETED"}},
             {"file": out_dir + "/run.json", "pointer": "/rows", "each": {"pointer": "/expectation_met", "equals": True}},
             {"file": out_dir + "/run.json", "pointer": "/rows", "each": {"pointer": "/start_count_state",
                                                                          "equals": "OBSERVED_ONE"}},
             {"file": out_dir + "/run.json", "pointer": "/interrupted", "equals": False},
             {"file": out_dir + "/run.json", "pointer": "/rows_independent", "equals": False},
             {"file": out_dir + "/run.json", "pointer": "/own_main_admitted/path", "equals": TOOLING + "/run_direct_probe.py"},
             {"file": out_dir + "/run.json", "pointer": "/boot_session_uuid_before_rows", "equals": BOOT},
             {"file": out_dir + "/run.json", "pointer": "/boot_session_uuid_after_rows", "equals": BOOT},
             {"file": out_dir + "/run.json", "pointer": "/process_events", "length": n}]
    for row in rows_doc["rows"]:
        outcome = out_dir + "/" + row["id"] + "/outcome.json"
        rules += [{"file": outcome, "pointer": "/state", "equals": "COMPLETED"},
                  {"file": outcome, "pointer": "/expectation_met", "equals": True},
                  {"file": outcome, "pointer": "/boot_unchanged", "equals": True},
                  {"file": outcome, "pointer": "/cleanup_complete", "equals": True},
                  {"file": outcome, "pointer": "/receipt_file_matches_record", "equals": True},
                  {"file": outcome, "pointer": "/process/returncode", "equals": row["expected"]["returncode"]},
                  {"file": out_dir + "/" + row["id"] + "/started-1.json", "exists": True},
                  {"file": out_dir + "/" + row["id"] + "/started-2.json", "exists": False}]
    add(ident, name, "the direct-probe runner: " + ", ".join(r["id"] for r in rows_doc["rows"]) +
        " (one Node start each, through the Darwin supervisor, not through the provider's parent guard)", E, "runner", argv,
        control=", ".join(r["id"] for r in rows_doc["rows"]), outputs=[out_dir], expect=rules,
        starts={"bounded": {"node": n, "other": 0}, "recorded_unbounded": {"python_launcher": 1},
                "rows": [r["id"] for r in rows_doc["rows"]]},
        limits={"outer_bound_s": 300, "per_row_ms": {"total_ms": 30000, "stage_ms": 28000, "cleanup_ms": 2000},
                "timing_evidence": "HOST review 001 HR-07: M1's first execution of bin/node took 1,109.748 ms of its "
                                   "3,000 ms; the rows keep P07 section 6's 30,000/28,000/2,000 ms clock"},
        capture={"listing": ident + ".L", "probe": ident + ".P",
                 "tr2_01": "an interrupted runner command is UNKNOWN whatever run.json says; each row's own outcome.json "
                           "is kept as written"},
        classification=runner_classes[label])
    pairs = [(out_dir + "/" + r["id"] + "/intent.json", out_dir + "/" + r["id"] + "/started-1.json") for r in rows_doc["rows"]]
    listing_command(ident, name, [out_dir] + extra_dirs, [])
    probe_command(ident, name, pairs)
    expect_command(ident, name)


runner_classes = {
    "r1": [
        {"outcome": "exit 0, ALL_ROWS_MET", "class": "COMPLETED"},
        {"outcome": "probe-syntax-check: non-zero exit or any stdout or stderr", "class":
         "IMPLEMENTATION: the bound probe does not parse cleanly on the bound Node; MH stops"},
        {"outcome": "P06-H01 refused before the selection check (stderr names job, manifest bytes, a path or a key)",
         "class": "PLAN: a fixture of this freeze; corrected freeze, new attempt"},
        {"outcome": "P06-H01 passed the selection check (no CH-SELECTION text), or wrote probe.json", "class":
         "IMPLEMENTATION: the probe accepted an unapproved manifest; MH stops"},
        {"outcome": "P06-H02 refused before the schema check (CH-SELECTION, keys, paths)", "class": "PLAN"},
        {"outcome": "P06-H02 accepted the schema", "class": "IMPLEMENTATION; MH stops"},
        {"outcome": "a supervisor error other than the status's (descendant, staged output, deadline, log ceiling)",
         "class": "IMPLEMENTATION or CONTRACT (the Darwin lifecycle); MH stops"},
        {"outcome": "exit 2 before any start (ROWS, ROW-INPUT, ROW-STAGE, ROW-TARGET, BINDING, SUPERVISOR)",
         "class": "PLAN (this freeze or its preparation) unless a bound input changed; zero starts"},
        {"outcome": "an interruption, exit 3 or a missing record", "class": "UNKNOWN (TR2-01); no retry"}],
    "r2": [
        {"outcome": "exit 0, ALL_ROWS_MET", "class": "COMPLETED: MC30's probe part and MC36 met"},
        {"outcome": "MC30-probe refuses with 'Actual input identity differs' in probe.json", "class":
         "CONTRACT (D-16 at the variable level): __CF_USER_TEXT_ENCODING did not reach Node's process.env; MC36 is "
         "NOT_RUN by the runner's stop (rows_independent false) and waits for an amendment of D-16 (N-04); not a plan error"},
        {"outcome": "MC30-probe or MC36 refuses at another check before the environment binding", "class":
         "PLAN: a fixture of this freeze; corrected freeze for R2, new attempt"},
        {"outcome": "MC36 passes the environment binding under the altered value", "class":
         "IMPLEMENTATION: the probe admitted a value other than the recorded one; MH stops"},
        {"outcome": "a supervisor error other than the status's", "class": "IMPLEMENTATION or CONTRACT; MH stops"},
        {"outcome": "exit 2 before any start", "class": "PLAN unless a bound input changed; zero starts"},
        {"outcome": "an interruption, exit 3 or a missing record", "class": "UNKNOWN (TR2-01); no retry"}]}
runner("C16", "r1", "r1", rows_r1, [ep("probe-syntax"), ep("probe-h01"), ep("probe-h02")])

# ---- C17: the cohort -----------------------------------------------------------------------------------------
name = ATTEMPT + "-c17-cohort"
out_dir = ep("cohort-outcomes")
run_root = ep("cohort") + "/run"
argv = tool_python("cohort", ("-B",), TOOLING + "/collect_outcomes.py", "cohort", "--root", WT,
                   "--environment", environment_files["cohort"]["path"],
                   "--environment-sha256", environment_files["cohort"]["sha256"],
                   "--module-sha256", COHORT_MODULE_SHA, "--output-dir", out_dir)
outcomes = out_dir + "/outcomes.json"
cohort_expect = [exit_is(name, 0), {"file": outcomes, "pointer": "/state", "equals": "ALL_PASSED"},
                 {"file": outcomes, "pointer": "/tests", "length": 7},
                 {"file": outcomes, "pointer": "/tests", "each": {"pointer": "/outcome", "equals": "pass"}},
                 {"file": outcomes, "pointer": "/required_methods", "length": 7},
                 {"file": outcomes, "pointer": "/required_methods", "each": {"pointer": "/outcome", "equals": "pass"}},
                 {"file": outcomes, "pointer": "/class_level_events", "length": 0},
                 {"file": outcomes, "pointer": "/unplanned_events", "length": 0},
                 {"file": outcomes, "pointer": "/loader_errors", "length": 0},
                 {"file": outcomes, "pointer": "/bytecode_present", "length": 0},
                 {"file": outcomes, "pointer": "/module_unchanged", "equals": True},
                 {"file": outcomes, "pointer": "/module/sha256", "equals": COHORT_MODULE_SHA},
                 {"file": outcomes, "pointer": "/environment/admitted_cf_user_text_encoding", "equals": CF_VALUE},
                 {"file": outcomes, "pointer": "/selection/configuration/sha256", "equals": D0},
                 {"file": outcomes, "pointer": "/selection/venv_is_root_venv", "equals": True},
                 {"file": outcomes, "pointer": "/process_events", "count_where": {"pointer": "/argv/0", "equals": NODE},
                  "equals": 3},
                 {"file": run_root + "/setup.json", "pointer": "/passed", "equals": True},
                 {"file": run_root + "/setup.json", "pointer": "/labels/boundary", "equals": "real"},
                 {"file": run_root + "/setup.json", "pointer": "/boot/boot_session_uuid", "equals": BOOT},
                 {"file": run_root + "/setup.json", "pointer": "/config_sha256", "equals": D0},
                 {"file": run_root + "/cohort.json", "pointer": "/passed", "equals": True},
                 {"file": run_root + "/cohort.json", "pointer": "/actual_checker_starts", "equals": 3},
                 {"file": run_root + "/cohort.json", "pointer": "/labels/boundary", "equals": "real"},
                 {"file": run_root + "/unused-native-schedule", "exists": False}]
for case, state, code in (("Q01-positive", "COMPLETED", 0), ("Q03-positive", "COMPLETED", 0),
                          ("Q01-changed-reference", "SUPERVISOR_REFUSAL", 1)):
    ledger = run_root + "/provider-ledgers/" + case + "/result.json"
    cohort_expect += [{"file": ledger, "pointer": "/actual_checker_starts", "equals": 1},
                      {"file": ledger, "pointer": "/state", "equals": state},
                      {"file": ledger, "pointer": "/provider_failure", "equals": None},
                      {"file": ledger, "pointer": "/process/returncode", "equals": code},
                      {"file": ledger, "pointer": "/process/cleanup/passed", "equals": True},
                      {"file": ledger, "pointer": "/labels/boundary", "equals": "real"},
                      {"file": ledger, "pointer": "/boot_before/boot_session_uuid", "equals": BOOT},
                      {"file": ledger, "pointer": "/boot_after/boot_session_uuid", "equals": BOOT},
                      {"file": run_root + "/provider-ledgers/" + case + "/finalization.failed.json", "exists": False},
                      {"file": run_root + "/" + case + "/probe.json", "pointer": "/passed", "equals": code == 0}]
cohort_audit = [{"file": outcomes, "pointer": "/process_events", "count_where": {"pointer": "/argv/0", "equals": GIT},
                 "equals": 60},
                {"file": outcomes, "pointer": "/process_events", "length": 63},
                {"file": outcomes, "pointer": "/original_bodies", "length": 9}]
for case, glb, audit in (("Q01-positive", "Q01/synthetic.glb", "Q01/synthetic-audit.json"),
                         ("Q03-positive", "Q03/synthetic.glb", "Q03/synthetic-audit.json"),
                         ("Q01-changed-reference", "Q01/synthetic.glb", "Q01-changed-reference/synthetic-audit.json")):
    cohort_audit += [{"file": run_root + "/" + case + "/synthetic.glb", "sha256": fixtures[glb]["sha256"]},
                     {"file": run_root + "/" + case + "/synthetic-audit.json", "sha256": fixtures[audit]["sha256"]}]
add("C17", name, "the qualifying cohort: the complete module tests.test_static_tray_readback_v01 (MC24, MC25, MC26; "
    "MC30's positive starts; F-04's own reads)", WT, "cohort", argv, control="MC24, MC25, MC26, MC30 (positive), F-04",
    outputs=[out_dir], absent_before=[run_root], expect=cohort_expect, audit_expect=cohort_audit,
    starts={"bounded": {"node": 3, "other": 0}, "recorded_unbounded": {"provider_git_reads": 60, "python_launcher": 1},
            "note": "12 selection checks x 5 bound Git reads (W5-PROVIDER section 9; TR-14), recorded by the collector's "
                    "audit hook, not bounded"},
    limits={"outer_bound_s": 600, "expected_wall_s": 60, "clocks": "check_case's Clock(total_ms=30000), stage_end = "
            "started + 28 s, 2,000 ms cleanup reserve (P07 section 6); no outer test timeout extends them"},
    capture={"listing": "C17.L", "probe": "C17.P"},
    classification=[
        {"outcome": "exit 0, ALL_PASSED and the predicates", "class": "COMPLETED: MC24, MC25, MC26 met; the positive "
         "starts accepted HOST's recorded __CF_USER_TEXT_ENCODING"},
        {"outcome": "exit 2 ENVIRONMENT, SELECTION, TARGET or PROVIDER-PRECONDITION", "class":
         "PLAN (the frozen environment or configuration) unless a bound input changed; zero starts"},
        {"outcome": "setUpClass error: a SCHEMA or SELECTION refusal of the configuration", "class": "PLAN"},
        {"outcome": "setUpClass error: SOURCE, HOST, RUNTIME or DEPENDENCY", "class": "INPUT or HOST changed; MH stops"},
        {"outcome": "a positive case's probe.json refuses with 'actual Node environment differs'", "class":
         "CONTRACT (S10/D-16): Node's environment is not HOST's recorded one; MH stops; MC36 NOT_RUN"},
        {"outcome": "a CPU method fails scientifically (a row, a finding, the negative's matrix_0_3)", "class":
         "IMPLEMENTATION or the Node-behaviour assumption (contract section 12); MH stops"},
        {"outcome": "a coordinator seam fails", "class": "IMPLEMENTATION; MH stops"},
        {"outcome": "an interruption, exit 3 or a missing record", "class": "UNKNOWN; no retry"}])
pairs = [(run_root + "/provider-ledgers/" + case + "/preflight.json", run_root + "/provider-ledgers/" + case + "/started.json")
         for case in ("Q01-positive", "Q03-positive", "Q01-changed-reference")]
listing_command("C17", name, [ep("cohort"), out_dir, ep("tmp-cohort")], [])
probe_command("C17", name, pairs)
expect_command("C17", name)

# ---- C18: the numerical audit harness -------------------------------------------------------------------------
name = ATTEMPT + "-c18-audit-numeric"
out = ep("audit-numeric.json")
add("C18", name, "P07 section 6: the independent numerical recomputation of the three cases (1e-9 bound for 'about "
    "0.001', T-10); the S8 auditor recomputes again", E, "declared",
    tool_python("declared", ("-I", "-S", "-B"), TOOLING + "/audit_numeric.py", "--cohort-root", run_root, "--output", out),
    control="P07 section 6 numerical audit", outputs=[out],
    expect=[exit_is(name, 0), {"file": out, "pointer": "/passed", "equals": True},
            {"file": out, "pointer": "/all_three_cases", "equals": True}],
    starts={"bounded": {"node": 0, "other": 0}, "recorded_unbounded": {"python_launcher": 1}},
    limits={"outer_bound_s": 300, "expected_wall_s": 5}, capture={"listing": "C18.L", "probe": None},
    classification=[{"outcome": "exit 0", "class": "COMPLETED"},
                    {"outcome": "exit 1", "class": "IMPLEMENTATION (the report disagrees with the recomputation) or a "
                     "tooling limit; MH stops before R2"},
                    {"outcome": "exit 2", "class": "PLAN (the cohort root) or an incomplete cohort (UNKNOWN); stop"}])
listing_command("C18", name, [], [out])
expect_command("C18", name)

# ---- C19: R2 (MC30-probe, then MC36) --------------------------------------------------------------------------
runner("C19", "r2", "r2", rows_r2, [ep("probe-mc30"), ep("probe-mc36")])

# ---------------------------------------------------------------------------------------------------------------
# Preconditions and the preparation, and the post checks
# ---------------------------------------------------------------------------------------------------------------
pre_commands = []


def pre(ident, name, purpose, cwd, env_name, argv, expect, classification):
    row = add(ident, name, purpose, cwd, env_name, argv, outputs=[], expect=[exit_is(name, 0)] + expect,
              starts={"bounded": {"node": 0, "other": 0}, "recorded_unbounded": {"launcher_or_read": 1}},
              limits={"outer_bound_s": 600}, capture={"rule": "FC-K2 and FC-K3 by the wrapper; it names no output"},
              classification=classification, phase="preparation" if ident.startswith("D") else "precondition")
    pre_commands.append(commands.pop())
    order.pop()
    return row


CHECK = lambda phase: tool_python("declared", ("-I", "-S", "-B"), checker["path"], "--freeze", OUT + "/FREEZE-001.json",
                                  "--freeze-sha256", FREEZE_SHA_PLACEHOLDER, phase)
pre("P01", ATTEMPT + "-p01-check-pre", "every binding, host fact, the boot, the ancestors, the umask, no bytecode or "
    ".DS_Store, the reviewed MC11 list, and every S7 path absent", E, "declared", CHECK("pre"),
    [{"file": E + "/" + ATTEMPT + "-p01-check-pre.stdout.txt", "text_includes": '"state": "MET"'}],
    [{"outcome": "NOT_MET", "class": "a binding or host fact differs (INPUT/HOST), or a path exists: S7 does not begin"}])
for key, ident in (("a", "P02"), ("b", "P03"), ("c", "P04")):
    row = [r for r in MC10_CASES if r["key"] == key][0]
    pname = ATTEMPT + "-%s-static-mc10-%s" % (ident.lower(), key)
    pre(ident, pname, "the observer's static with MC10 plan " + key + " (zero starts): HR-03's inventory recheck, the "
        "source, runtime, reader tree, Git binding, boot and ancestors, the plan's shape and its absent attempt",
        E, "declared", tool_python("declared", ("-I", "-S", "-B"), OBSERVER, "static", "--plan", row["plan"]["path"],
                                   "--plan-sha256", row["plan"]["sha256"]),
        [{"file": E + "/" + pname + ".stdout.txt", "text_includes": "STATIC_READY"},
         {"file": E + "/" + pname + ".stderr.txt", "text_equals": ""}],
        [{"outcome": "not STATIC_READY", "class": "the refusal's category decides: PLAN for PLAN/PATH; INPUT or HOST for "
          "SOURCE, PYTHON, RUNTIME, DEPENDENCY, GIT, OS, BOOT; S7 does not begin"}])
pre("P05", ATTEMPT + "-p05-git-status", "the Director's read-only status of the worktree (GIT_OPTIONAL_LOCKS=0)", WT,
    "git-worktree", ["/usr/bin/env", "-i", *env_assignments("git-worktree"), GIT, "-c", "core.fsmonitor=false", "-C", WT,
                     "status", "--porcelain=v1", "--untracked-files=all"],
    [{"file": E + "/" + ATTEMPT + "-p05-git-status.stdout.txt", "text_equals": ""},
     {"file": E + "/" + ATTEMPT + "-p05-git-status.stderr.txt", "text_equals": ""}],
    [{"outcome": "any output", "class": "INPUT: the worktree is not clean at C; S7 does not begin"}])
pre("D01", ATTEMPT + "-d01-prepare", "the Director's frozen preparation: create the absent directories and copy the "
    "frozen fixture files (prepare-s7-001.sh)", E, "plain", ["/usr/bin/env", "-i", *env_assignments("plain"), "/bin/sh",
                                                           prep_script["path"]],
    [{"file": E + "/" + ATTEMPT + "-d01-prepare.stdout.txt", "text_equals": "prepare-s7-001: done\n"},
     {"file": E + "/" + ATTEMPT + "-d01-prepare.stderr.txt", "text_equals": ""}],
    [{"outcome": "non-zero exit", "class": "PLAN or an unexpected existing path: the attempt's preparation is partial; it "
      "is kept (FC-K1), reconciled, and a new attempt ID is needed"}])
pre("D02", ATTEMPT + "-d02-check-prepared", "every prepared entry exactly as frozen, the bindings again, every output "
    "still absent", E, "declared", CHECK("prepared"),
    [{"file": E + "/" + ATTEMPT + "-d02-check-prepared.stdout.txt", "text_includes": '"state": "MET"'}],
    [{"outcome": "NOT_MET", "class": "PLAN or INPUT; S7 does not begin"}])
post_commands = []
for ident, pname, purpose, env_name, argv, exp, outputs in (
        ("Q01", ATTEMPT + "-q01-python-inventory", "the Python installation inventory after S7 (MC32, HR-03)", "declared",
         tool_python("declared", ("-I", "-S", "-B"), OBSERVER, "python-inventory", "--venv", WT + "/.venv",
                     "--framework", host["python"]["framework"], "--output", ep("q01-python-inventory.json")),
         [{"file": ep("q01-python-inventory.json"), "sha256": "c277bdd3ac6aa73105df3924707a271a402a0dc7c722be27a6834f2c78605633"}],
         [ep("q01-python-inventory.json")]),
        ("Q02", ATTEMPT + "-q02-source-inventory", "the source inventory after S7", "declared",
         tool_python("declared", ("-I", "-S", "-B"), OBSERVER, "source-inventory", "--root", WT,
                     "--output", ep("q02-source-inventory.json")),
         [{"file": ep("q02-source-inventory.json"), "sha256": source_descriptor["sha256"]}], [ep("q02-source-inventory.json")]),
        ("Q03", ATTEMPT + "-q03-git-status", "the worktree's status after S7 (the Director's read)", "git-worktree",
         ["/usr/bin/env", "-i", *env_assignments("git-worktree"), GIT, "-c", "core.fsmonitor=false", "-C", WT,
          "status", "--porcelain=v1", "--untracked-files=all"],
         [{"file": E + "/" + ATTEMPT + "-q03-git-status.stdout.txt", "text_equals": ""}], []),
        ("Q04", ATTEMPT + "-q04-check-post", "the bindings of every input, the boot, no bytecode, every prepared input "
         "unchanged (the consumed MC29 configuration copy excepted), and Q01 to Q03's predicates", "declared",
         CHECK("post"), [{"file": E + "/" + ATTEMPT + "-q04-check-post.stdout.txt", "text_includes": '"state": "MET"'}],
         [])):
    add(ident, pname, purpose, E if ident != "Q03" else WT, env_name, argv, outputs=outputs,
        expect=[exit_is(pname, 0)] + exp,
        starts={"bounded": {"node": 0, "other": 0}, "recorded_unbounded": {"launcher_or_read": 1}},
        limits={"outer_bound_s": 600}, capture={"rule": "FC-K2 and FC-K3 by the wrapper"},
        classification=[{"outcome": "not met", "class": "a change during S7: kept and recorded; the Director and the "
                         "auditor reconcile it with S7's outcome (no retry)"}], phase="post")
    post_commands.append(commands.pop())
    order.pop()

prepared_entries = []
children = {}
for path in prep_dirs:
    children.setdefault(os.path.dirname(path), []).append(os.path.basename(path))
for source, target in prep_copies:
    children.setdefault(os.path.dirname(target), []).append(os.path.basename(target))
for path in prep_dirs:
    prepared_entries.append({"id": "prepared:" + os.path.relpath(path, E), "path": path, "kind": "directory",
                             "mode": "0o700", "entries": sorted(children.get(path, []))})
for source, target in prep_copies:
    prepared_entries.append({"id": "prepared:" + os.path.relpath(target, E), "path": target, "kind": "file",
                             "sha256": source["sha256"], "size_bytes": source["size_bytes"], "mode": "0o644",
                             "nlink_one": True, "copied_from": source["path"]})
consumed = ["prepared:" + os.path.relpath(MC29_COPY["configuration"], E)]
p01_records = set(pre_commands[0]["outputs_absent_before"])
before_prep = set()
for row in pre_commands + commands + post_commands:
    before_prep |= set(row["outputs_absent_before"])
before_prep |= {row["path"] for row in prepared_entries}
before_prep -= p01_records
after_prep = set()
for row in commands + post_commands:
    after_prep |= set(row["outputs_absent_before"])
if after_prep & {row["path"] for row in prepared_entries}:
    raise SystemExit("an output path is also a prepared entry")
names = [row["name"] for row in pre_commands + commands + post_commands]
if len(names) != len(set(names)):
    raise SystemExit("duplicate wrapper names")
all_commands = pre_commands + commands + post_commands
result = {
    "all_commands": all_commands,
    "prepared_entries": prepared_entries, "consumed": consumed,
    "absent_paths": {"before_preparation": sorted(before_prep), "after_preparation": sorted(after_prep)},
    "deferred_sources": DEFERRED_SOURCES, "mc11_reviewed": MC11_REVIEWED,
    "commands": commands, "pre_commands": pre_commands, "post_commands": post_commands, "bindings": bindings,
    "environments": environment_files, "configs": configs, "probe_rows": probe_rows, "rows_files": rows_files,
    "mc10": MC10_CASES, "prep_script": prep_script, "prep_dirs": prep_dirs,
    "prep_copies": [{"source": s, "target": t} for s, t in prep_copies], "checker": checker,
    "methods": methods_written, "discovery": discovery_written, "host_copies": host_copies, "fixtures": fixtures,
    "D0": D0, "mc29_copy": MC29_COPY, "written": WRITTEN}
write(OUT + "/author/records/generate-001.json", pretty(result))
print(json.dumps({"commands": len(commands), "pre": len(pre_commands), "post": len(post_commands),
                  "bindings": len(bindings), "written": len(WRITTEN), "D0": D0}, sort_keys=True))
