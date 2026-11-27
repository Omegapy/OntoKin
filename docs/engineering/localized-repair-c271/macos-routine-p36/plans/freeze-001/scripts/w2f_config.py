"""W2 (freeze 001, C271-P36): write R1's readback configuration (config/0.2.0) and the two documents it binds.

Usage: python3 -I -S -B w2f_config.py WORKTREE HOST DISCOVERY EVIDENCE_ROOT OUT_DIR

* DISCOVERY is the output of MH's discover_inventory.py discover at B (ontokin.c271.p35-runtime-discovery/2,
  COMPLETE). Its IDs, sorted and unique, become the provider's discovery document's method_ids: the complete
  default inventory, which must contain the seven readback methods.
* HOST is the reviewed HOST.json; every binding the provider cross-checks is copied from it unchanged: the
  source inventory descriptor (path included), the dependencies root and inventory descriptor, the runtime
  executable. HOST's own descriptor is computed from its bytes here and must equal the review record's
  digest, which is a constant below.
* ORIGINAL_BODIES is read from the provider's source by its AST, never by importing it.

It writes OUT_DIR/discovery-001.json, OUT_DIR/methods-001.json and OUT_DIR/readback-config-001.json, each by
exclusive creation, as JSON with sorted keys, an indent of 2 and a final line end. It starts no process.
"""
import ast
import hashlib
import json
import os
import stat
import sys

if not sys.flags.dont_write_bytecode:
    sys.stderr.write("refused: run with -B\n")
    raise SystemExit(2)
worktree, host_path, discovery_path, evidence_root, out_dir = sys.argv[1:6]
HOST_SHA256 = "858ef72a949ce7575787290601ae70d117090a460781b2e660a3b0d4f0162666"  # HOST-REVIEW-001.json /host/sha256
B = "4ca781429c5411c67c0965bc69306b42c6cc74ad"
TREE = "0935162c72fd9d804681e920da6f6d6e9066ff28"
PROVIDER = "prototypes/static_tray_v01/current_host_readback_v02.py"
CONTRACT_PATH = "docs/engineering/localized-repair-c271/macos-contract-design-p31/CONTRACT.md"
AMENDMENT_ADOPTION_PATH = "docs/engineering/localized-repair-c271/macos-implementation-p33/ADOPTION-AMENDMENT-001.json"
BASELINE_MAP = "docs/engineering/localized-repair-c271/current-host-p05/mapping/MAP-EVIDENCE.zip"
ADOPTION_EXPECTED = {"sha256": "872312ed80a63fbb196c17ace42e786b7fe757b710eff41139b125dfaa507937", "size_bytes": 5396,
                     "mode": "0o644"}  # PLAN-REVIEW-001 PR-06


def binding(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        assert stat.S_ISREG(info.st_mode) and info.st_nlink == 1, path
        digest = hashlib.sha256()
        while True:
            block = os.read(fd, 1 << 20)
            if not block:
                break
            digest.update(block)
        return {"path": path, "sha256": digest.hexdigest(), "size_bytes": info.st_size,
                "mode": oct(stat.S_IMODE(info.st_mode))}
    finally:
        os.close(fd)


def write_new(path, value):
    data = (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode("ascii")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
    with os.fdopen(fd, "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    return binding(path)


host_binding = binding(host_path)
assert host_binding["sha256"] == HOST_SHA256, "HOST differs from the review record's digest"
host = json.load(open(host_path, encoding="utf-8"))
assert host["source"]["commit"] == B and host["source"]["tree"] == TREE and host["source"]["root"] == worktree

discovery = json.load(open(discovery_path, encoding="utf-8"))
assert discovery["schema"] == "ontokin.c271.p35-runtime-discovery/2" and discovery["state"] == "COMPLETE"
ids = discovery["ids_in_discovery_order"]
assert len(ids) == len(set(ids)) == discovery["count"] == 5994

module = ast.parse(open(os.path.join(worktree, PROVIDER), "rb").read())
bodies = None
for node in module.body:
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "ORIGINAL_BODIES" for t in node.targets):
        bodies = ast.literal_eval(node.value)
assert isinstance(bodies, dict) and len(bodies) == 9
methods_ids = sorted("test_static_tray_readback_v01." + name for name in bodies if ".test_" in name)
assert len(methods_ids) == 7 and all(item in ids for item in methods_ids)

adoption = binding(os.path.join(worktree, AMENDMENT_ADOPTION_PATH))
assert {k: adoption[k] for k in ADOPTION_EXPECTED} == ADOPTION_EXPECTED, "PR-06: the adoption record's bytes differ"

discovery_document = {"schema": "ontokin.current-host-readback-discovery/0.2.0", "method_ids": sorted(ids),
                      "baseline_map": binding(os.path.join(worktree, BASELINE_MAP))}
discovery_binding = write_new(os.path.join(out_dir, "discovery-001.json"), discovery_document)
methods_document = {"schema": "ontokin.current-host-readback-methods/0.2.0",
                    "source_test": "tests/test_static_tray_readback_v01.py", "original_bodies": bodies,
                    "discovery": discovery_binding}
methods_binding = write_new(os.path.join(out_dir, "methods-001.json"), methods_document)
config = {"schema": "ontokin.current-host-readback-config/0.2.0", "contract": "ontokin.current-host-readback/0.2.0",
          "contract_source": binding(os.path.join(worktree, CONTRACT_PATH)), "amendment_adoption": adoption,
          "source": {"root": worktree, "commit": B, "tree": TREE, "inventory": host["source"]["inventory"]},
          "host": host_binding,
          "dependencies": {"root": host["dependencies"]["root"], "inventory": host["dependencies"]["inventory"]},
          "runtime": {"executable": host["runtime"]["executable"], "version": host["runtime"]["version"]},
          "methods": methods_binding, "evidence_root": evidence_root, "parent": None}
config_binding = write_new(os.path.join(out_dir, "readback-config-001.json"), config)
print(json.dumps({"discovery": discovery_binding, "methods": methods_binding, "config": config_binding}, indent=1))
