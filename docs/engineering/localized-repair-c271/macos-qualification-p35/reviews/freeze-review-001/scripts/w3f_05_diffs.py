"""W3 freeze review 001, script 05: JSON-level differences between the freeze's documents and their sources.

Pairs: the three MC10 plans against plan 001; every probe and MC29 configuration against the approved
cohort configuration; the two HOST copies against HOST; the four manifests against each other; the
jobs; the methods and discovery documents. Reads only; prints the differences and writes a record.
"""
import json
import os
import sys

FZD = sys.argv[1]
OUT = sys.argv[2]
L = "<local>"


def load(p):
    with open(p, "rb") as f:
        return json.loads(f.read())


def diff(a, b, path=""):
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a:
                out.append((path + "/" + k, "<absent>", b[k]))
            elif k not in b:
                out.append((path + "/" + k, a[k], "<absent>"))
            else:
                out.extend(diff(a[k], b[k], path + "/" + k))
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append((path, "list len %d" % len(a), "list len %d" % len(b)))
        for i, (x, y) in enumerate(zip(a, b)):
            out.extend(diff(x, y, path + "/" + str(i)))
    else:
        if type(a) is not type(b) or a != b:
            out.append((path, a, b))
    return out


def short(v):
    s = json.dumps(v, ensure_ascii=False)
    return s if len(s) < 260 else s[:260] + "..."


report = {}
pairs = []
plan001 = L + "/c271-p35/workers/W2-plan-001/observation-plan-001.json"
for x in "abc":
    pairs.append(("plan001 vs mc10-" + x, plan001, FZD + "/mc10/observation-plan-mc10-%s.json" % x))
cohort = FZD + "/config/cohort-config-001.json"
for r in ("h01", "h02", "mc30", "mc36"):
    pairs.append(("cohort config vs " + r, cohort, FZD + "/probe/%s/config.json" % r))
pairs.append(("cohort config vs mc29-configuration", cohort, FZD + "/config/mc29-configuration-config-001.json"))
pairs.append(("cohort config vs mc29-job-input", cohort, FZD + "/config/mc29-job-input-config-001.json"))
host = L + "/c271-p35/evidence/observe-001/HOST.json"
pairs.append(("HOST vs mc30 copy", host, FZD + "/probe/mc30/HOST.json"))
pairs.append(("HOST vs mc36 copy", host, FZD + "/probe/mc36/HOST.json"))
for r in ("h02", "mc30", "mc36"):
    pairs.append(("manifest h01 vs " + r, FZD + "/probe/h01/supplemental-cpu.json", FZD + "/probe/%s/supplemental-cpu.json" % r))
for r in ("h02", "mc30", "mc36"):
    pairs.append(("job h01 vs " + r, FZD + "/probe/h01/job.json", FZD + "/probe/%s/job.json" % r))
for name, a, b in pairs:
    d = diff(load(a), load(b))
    report[name] = [[p, short(x), short(y)] for p, x, y in d]
    print("==", name, "(%d differences)" % len(d))
    for p, x, y in d[:40]:
        print("   ", p, "|", short(x), "->", short(y))
    if len(d) > 40:
        print("    ...")

# The probe manifests: their selection, roots and slot 0, and the job digest coherence
for r in ("h01", "h02", "mc30", "mc36"):
    m = load(FZD + "/probe/%s/supplemental-cpu.json" % r)
    print("manifest", r, "selection", m["selection"], "cohort_root", m["cohort_root"], "schedule_root", m["schedule_root"])
    print("   slot0 argv", m["slots"][0]["argv"])
    print("   host", m["host"])
m = load(FZD + "/config/methods-001.json")
print("methods keys", sorted(m), "source_test", m.get("source_test"), "discovery", m.get("discovery"))
d = load(FZD + "/config/discovery-001.json")
print("discovery keys", sorted(d), "method_ids", d.get("method_ids"), "baseline_map", d.get("baseline_map"))
for name in ("mc29-configuration-config-001.json", "mc29-job-input-config-001.json"):
    c = load(FZD + "/config/" + name)
    print(name, "evidence_root", c["evidence_root"])
with open(os.path.join(OUT, "records", "05-diffs.json"), "x", encoding="utf-8") as f:
    json.dump(report, f, indent=1, ensure_ascii=False)
    f.write("\n")
