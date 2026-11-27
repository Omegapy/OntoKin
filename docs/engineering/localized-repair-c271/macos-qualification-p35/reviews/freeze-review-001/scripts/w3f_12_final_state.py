"""W3 freeze review 001, script 12: the state after my work, and the digests of every file I reviewed.

Checks: the freeze directory against its SHA256SUMS (and the freeze's digest); the worktree outside .venv holds no
bytecode, __pycache__ or .DS_Store and no entry newer than my first file; the evidence parent holds no s7-001 path and
its S5 files are unchanged; and it records SHA-256, size and mode of every reviewed file and of my outputs so far.
Reads only; writes one record into OUT/records.
"""
import datetime
import hashlib
import json
import os
import stat
import sys

OUT = sys.argv[1]
FZD = "<local>/c271-p35/workers/W2-freeze-001"
WT = "<worktree>"
L = "<local>"
E = L + "/c271-p35/evidence"
D = WT + "/docs/engineering/localized-repair-c271"


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def desc(path):
    st = os.lstat(path)
    return {"sha256": sha(path), "size_bytes": st.st_size, "mode": "0o%03o" % stat.S_IMODE(st.st_mode)}


def label(path):
    return path.replace(WT, "<worktree>").replace(L, "<local>")


report = {}
# 1. the freeze directory
sums = {}
for line in open(FZD + "/SHA256SUMS.txt", encoding="utf-8"):
    if line.strip():
        d, n = line.rstrip("\n").split("  ", 1)
        sums[n] = d
bad = [n for n, d in sums.items() if sha(FZD + "/" + n) != d]
listed = set(sums) | {"SHA256SUMS.txt"}
present = set()
for root, ds, fs in os.walk(FZD):
    for n in fs:
        present.add(os.path.relpath(os.path.join(root, n), FZD))
report["freeze_dir"] = {"sha256sums_listed": len(sums), "bad": bad, "unlisted": sorted(present - listed),
                        "missing": sorted(listed - present), "freeze_sha256": sha(FZD + "/FREEZE-001.json"),
                        "configuration_sha256": sha(FZD + "/config/cohort-config-001.json")}
# 2. the worktree
ref = os.lstat(os.path.join(OUT, "scripts", "w3f_01_inventory.py")).st_mtime
found, newer = [], []
for root, ds, fs in os.walk(WT):
    if root == WT and ".venv" in ds:
        ds.remove(".venv")
    for n in ds + fs:
        p = os.path.join(root, n)
        if n == "__pycache__" or n.endswith((".pyc", ".pyo")) or n == ".DS_Store":
            found.append(label(p))
        try:
            if os.lstat(p).st_mtime >= ref:
                newer.append(label(p))
        except OSError:
            pass
report["worktree"] = {"bytecode_or_ds_store": found, "entries_newer_than_my_first_file": newer[:20], "newer_count": len(newer)}
# 3. the evidence parent
st = os.lstat(E)
entries = sorted(os.listdir(E))
report["evidence_parent"] = {
    "mtime_utc": datetime.datetime.fromtimestamp(st.st_mtime, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "inode": st.st_ino, "entries": len(entries), "s7_001_paths": [n for n in entries if n.startswith("s7-001")],
    "w3_paths": [n for n in entries if "W3" in n or "w3" in n],
    "host": desc(E + "/observe-001/HOST.json"), "completion": desc(E + "/observe-001/completion.json"),
    "result": desc(E + "/observe-001/result.json")}
# 4. every file I reviewed
reviewed = []
for root, ds, fs in os.walk(FZD):
    for n in sorted(fs):
        reviewed.append(os.path.join(root, n))
fixed = [
    D + "/macos-qualification-p35/MH-PLAN.md", D + "/macos-qualification-p35/PHASE.json",
    D + "/macos-qualification-p35/authoring/TOOLING-AUTHOR-NOTES.md", D + "/macos-qualification-p35/authoring/TOOLING-SHA256SUMS.txt",
    D + "/macos-qualification-p35/n34m/N34-M-DISPOSITION.json",
    D + "/macos-contract-design-p31/CONTRACT.md", D + "/host-inspection-p07/QUALIFICATION-PLAN.md",
    D + "/macos-implementation-p33/CONTROLS-FROZEN.json", D + "/macos-implementation-p33/CONTROLS-REFREEZE-001.json",
    D + "/macos-implementation-p33/CONTROLS-REFREEZE-002.json", D + "/macos-implementation-p33/INVENTORY-ADDITIONS.json",
    D + "/macos-implementation-p33/ADOPTION-AMENDMENT-001.json", D + "/macos-implementation-p33/AMENDMENT-001.md",
    D + "/macos-implementation-p33/OUTCOME.json", D + "/macos-implementation-p33/DIRECTOR-DECISIONS.md",
    WT + "/prototypes/static_tray_v01/current_host_readback_v02.mjs", WT + "/prototypes/static_tray_v01/current_host_readback_v02.py",
    WT + "/prototypes/static_tray_v01/current_host_readback_v01.py", WT + "/prototypes/static_tray_v01/supervisor.py",
    WT + "/prototypes/static_tray_v01/supervisor_darwin_v01.py", WT + "/prototypes/static_tray_v01/current_host_observation_v02.py",
    WT + "/tests/test_static_tray_readback_v01.py", WT + "/tests/test_current_host_readback_controls_v02.py",
    WT + "/tools/check_local.py", WT + "/.gitattributes",
    L + "/c271-p35/director/run/run_once_v2.sh", L + "/c271-macos/reader-c195/tools/three_loader.mjs",
    L + "/c271-p35/workers/W2-plan-001/observation-plan-001.json", L + "/c271-p35/workers/W2-plan-001/dependencies-inventory-001.json",
    E + "/observe-001/HOST.json", E + "/observe-001/completion.json", E + "/observe-001/result.json"]
for n in ("FAILURE-CAPTURE.md", "README.md", "audit_numeric.py", "capture_probe.py", "collect_outcomes.py", "control_harness.py",
          "discover_inventory.py", "run_direct_probe.py", "scan_mc11.py"):
    fixed.append(D + "/macos-qualification-p35/tooling/" + n)
for n in ("W5-PROVIDER.md", "W4-DRIVER.md", "W3-OBSERVER.md", "W1-SUPERVISOR.md"):
    fixed.append(D + "/macos-implementation-p33/interfaces/" + n)
for n in sorted(os.listdir(D + "/macos-qualification-p35/reviews")):
    fixed.append(D + "/macos-qualification-p35/reviews/" + n)
for n in sorted(os.listdir(L + "/c271-p35/director/reviews")):
    fixed.append(L + "/c271-p35/director/reviews/" + n)
reviewed += fixed
report["reviewed_files"] = {label(p): desc(p) for p in reviewed if os.path.isfile(p)}
report["reviewed_missing"] = [label(p) for p in reviewed if not os.path.isfile(p)]
# 5. my outputs so far
mine = {}
for root, ds, fs in os.walk(OUT):
    if "prep-test" in root.split(os.sep) or "checker-test" in root.split(os.sep):
        continue
    for n in sorted(fs):
        p = os.path.join(root, n)
        mine[os.path.relpath(p, OUT)] = desc(p)
report["my_outputs"] = mine
with open(os.path.join(OUT, "records", "12-final-state.json"), "x", encoding="utf-8") as f:
    json.dump(report, f, indent=1, sort_keys=True)
    f.write("\n")
print(json.dumps({k: report[k] for k in ("freeze_dir", "worktree", "evidence_parent")}, indent=1)[:4000])
print("reviewed files", len(report["reviewed_files"]), "missing", report["reviewed_missing"], "my outputs", len(mine))
