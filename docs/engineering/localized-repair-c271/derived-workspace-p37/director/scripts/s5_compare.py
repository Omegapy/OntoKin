"""C271-P37 stage S5: compare each module's collected outcomes with MI's final-003 run of the same module.

Run as: python3 -I -S -B s5_compare.py OUT_DIR. Reads S5-RUN.json and the collections; writes S5-COMPARE.json.
Reasons are compared after masking temporary names (tmp + 8 characters) and the resolved and /var forms of the
per-user temporary directory, so only real differences remain.
"""
import hashlib, json, os, re, sys, tempfile
from pathlib import Path

OUT = Path(sys.argv[1])
run = json.loads((OUT / "S5-RUN.json").read_text(encoding="utf-8"))
tmp_real = os.path.realpath(tempfile.gettempdir())
tmp_link = tmp_real.removeprefix("/private")
MASKS = [(tmp_real, "<tmpdir>"), (tmp_link, "<tmpdir>")]


def norm(text):
    for old, new in MASKS:
        text = text.replace(old, new)
    return re.sub(r"tmp[a-z0-9_]{8}", "tmp<name>", text)


def table(path):
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = {}
    for t in doc["tests"]:
        rows[t["id"]] = {"outcome": t["outcome"], "reasons": [norm(r if isinstance(r, str) else json.dumps(r, sort_keys=True)) for r in t.get("reasons", [])],
                         "subtests": sorted(json.dumps(s, sort_keys=True) for s in t.get("failing_subtests", [])),
                         "occurrences": t.get("occurrences")}
    return doc, rows


report = {"schema": "ontokin.c271.p37-s5-compare/1", "run_sha256": hashlib.sha256((OUT / "S5-RUN.json").read_bytes()).hexdigest(),
          "modules": []}
for row in run["modules"]:
    entry = {"module": row["module"], "exit": row["exit"]}
    doc, cand = table(OUT / (row["module"] + ".collect.json"))
    entry["candidate_counts"] = doc["counts"]["by_outcome"]
    entry["candidate_not_passing"] = sorted(i for i, r in cand.items() if r["outcome"] not in ("passed",))
    base_path = OUT / (row["module"] + ".mi-final-003.collect.json")
    if base_path.exists():
        bdoc, base = table(base_path)
        entry["mi_counts"] = bdoc["counts"]["by_outcome"]
        same = [i for i in cand if i in base and cand[i] == base[i]]
        entry["unchanged"] = len(same)
        entry["added"] = [{"id": i, "outcome": cand[i]["outcome"]} for i in sorted(cand) if i not in base]
        entry["removed"] = [{"id": i, "outcome": base[i]["outcome"]} for i in sorted(base) if i not in cand]
        entry["changed"] = [{"id": i, "mi": base[i], "s5": cand[i]} for i in sorted(cand) if i in base and cand[i] != base[i]]
    else:
        entry["mi_counts"] = None
    report["modules"].append(entry)
(OUT / "S5-COMPARE.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
for e in report["modules"]:
    print(e["module"], "exit", e["exit"], e["candidate_counts"], "| mi", e["mi_counts"],
          "| added", len(e.get("added", [])), "removed", len(e.get("removed", [])), "changed", len(e.get("changed", [])),
          "| not passing", len(e["candidate_not_passing"]))
