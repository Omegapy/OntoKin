"""W2 (freeze 001, C271-P36): the attribution files of R1 and R2 (ontokin.c271.p36-attributions/2).

Usage: python3 -I -S -B w2f_attributions.py TOOL MAIN_RESOLVED_DIR MAIN_DEFAULT_DIR MAIN_DEFAULT_TMPDIR MI_STATEMENTS OUT_DIR

TOOL is the reviewed collector and comparator (unit_log_outcomes.py at commit B). It is loaded from its file
into this process, exactly as its own tests load it, and its own functions build every statement, so that a
statement is what the comparator's record_statement makes of the record it states: collect_log reads main's
logs, Normalizer is built from the run's summary and its temporary directory, valid_statement checks each row.

* R1 (attributions/r1-attributions-001.json), each in raw form:
  - main's one not-passing test of its resolved-directory run (the last-digit fixture test);
  - D-18's two 0.1.0 driver tests, from MI's retained per-module log on this host (final-003);
  - every other not-passing record of MI's final-003 per-module logs of the branch's own modules, except
    test_RI_L07 and test_RI_L08 (their recorded ModuleNotFoundError is an artifact of the per-module
    invocation; see the author notes) and the readback class's ordinary-run setUpClass error (R2's MC22).
* R2 (attributions/r2-attributions-001.json):
  - every not-passing test of main's default-directory run, in normalized form under that run's own summary
    and temporary directory (the comparator applies R2's own normalization to R2's records);
  - D-18's two tests, raw;
  - MC22: setUpClass (test_static_tray_readback_v01.ReadbackCPUControls), raw, with the fixed reason.

TR2-03: no ID that the frozen discovery lists more than once (there is none). TR2-04: each statement's outcome
follows from its own events and subtests, checked here. It starts no process and writes only the two files.
"""
import sys

if not sys.flags.dont_write_bytecode:
    sys.stderr.write("refused: run with -B\n")
    raise SystemExit(2)
import hashlib
import importlib.util
import json
import os

tool_path, resolved_dir, default_dir, default_tmpdir, mi_path, out_dir = sys.argv[1:7]
spec = importlib.util.spec_from_file_location("w2f_unit_log_outcomes", tool_path)
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)
RECORDED = {  # INTEGRATION.json resulting_main_checks.routine_driver.runs
    "resolved": {"log": "85e372a1074d968fe6a4034067247bf09287445ba0d6e8107797170051cae5f8",
                 "summary": "f5f2c3f650a5c4e8422f1e2ab3aae79fc1051bf0ccebc90e578a4b28bbb96be4"},
    "default": {"log": "1ec8a64dbb5e2a4cb00437e543573e8cbed3d9766e337b6878cace9a05d5f959",
                "summary": "0a1e5b7e4a105798557ce7ef3a4c9831c7248cb2c5579e89c281514159e4adea"}}
D18 = ["test_current_host_readback_driver.CurrentHostDriverBindingTests.test_failed_prelaunch_is_recorded_unexecuted_even_if_later_inventory_fails",
       "test_current_host_readback_driver.CurrentHostDriverBindingTests.test_missing_explicit_selection_cannot_use_ambient_approval"]
NOT_ATTRIBUTED = ["test_current_host_required_images_v01.RequiredImageControls.test_RI_L07",
                  "test_current_host_required_images_v01.RequiredImageControls.test_RI_L08"]
MC22_ID = "setUpClass (test_static_tray_readback_v01.ReadbackCPUControls)"
ORDINARY = ("prototypes.static_tray_v01.current_host_readback_v01.CurrentHostBindingError: "
            "No approved current-host readback selection: ordinary run, not a qualification")


def read(path):
    with open(path, "rb") as stream:
        return stream.read()


def consistent(row):
    """TR2-04: the stated outcome is the one that its own events and subtests give (the collector's outcome_of)."""
    statuses = [e["status"] for e in row["events"]] + [e["status"] for e in row["failing_subtests"]] + \
               ["skipped" for _ in row["skipped_subtests"]]
    return tool.outcome_of([{"status": s} for s in statuses], []) == row["outcome"] and row["outcome"] in tool.NOT_PASSING


def run(directory, label):
    log, summary = read(os.path.join(directory, "logs/unit-tests.log")), read(os.path.join(directory, "summary.json"))
    assert hashlib.sha256(log).hexdigest() == RECORDED[label]["log"], label
    assert hashlib.sha256(summary).hexdigest() == RECORDED[label]["summary"], label
    return tool.collect_log(log), json.loads(summary)


resolved, _ = run(resolved_dir, "resolved")
default, default_summary = run(default_dir, "default")
normalize = tool.Normalizer(default_summary, [default_tmpdir])
identity = lambda text: text
mi = json.load(open(mi_path, encoding="utf-8"))
mi_rows = {row["id"]: row for row in mi["rows"]}


def statement(record_row, form, normalizer, source, note):
    body = tool.record_statement(record_row, normalizer)
    return {"id": record_row["id"], "form": form, **body, "source": source, "note": note}


def from_mi(raw_id, source, note):
    row = mi_rows[raw_id]
    return {"id": raw_id, "form": "raw", **row["statement"], "source": source,
            "note": note + " MI's ID: " + row["mi_id"] + "; MI's log SHA-256 " + row["source_log_sha256"] + "."}


r1 = []
for row in resolved["tests"]:
    if row["outcome"] in tool.NOT_PASSING:
        r1.append(statement(row, "raw", identity, "main-8e847c15-resolved-tmpdir",
                            "Main's unchanged baseline failure of its resolved-directory run (INTEGRATION.json): the "
                            "test with a last-digit fixture difference. Raw form; its first line names no run path."))
assert len(r1) == 1 and r1[0]["id"].endswith("test_original_corpus_and_author_remain_byte_identical")
for raw_id in D18:
    r1.append(from_mi(raw_id, "D-18", "MI's D-18: an S8 version of a 0.1.0 driver test that asserts the ordinary-run "
                      "refusal that S8 removes; it keeps its expectation and fails visibly; R04 classifies it. From MI's "
                      "retained per-module run on this host (final-003, commit 7b759de0), raw form."))
mi_other = []
for raw_id, row in sorted(mi_rows.items()):
    if raw_id in D18 or raw_id in NOT_ATTRIBUTED or row["kind"] != "test":
        continue
    mi_other.append(raw_id)
    r1.append(from_mi(raw_id, "MI final-003", "A 0.1.0 Linux-route test of the branch that fails on this host in MI's "
                      "retained per-module run (final-003, commit 7b759de0; MI's CHECKS.json: identical to the phase-start "
                      "baseline at 1c2f25ba; 'Modules that need Linux keep their phase-start failures'). Raw form. That run "
                      "used python -B -m unittest -v tests.<module> from the worktree; the routine runs the module from the "
                      "workspace as a top-level module, so a difference is possible and is then visible here."))
r2 = []
for row in default["tests"]:
    if row["outcome"] in tool.NOT_PASSING:
        r2.append(statement(row, "normalized", normalize, "main-8e847c15-default-tmpdir",
                            "Main's unchanged baseline failure of its default-directory run (INTEGRATION.json, 307), "
                            "normalized under that run's own summary and temporary directory (" + tool.NORMALIZATION + ")."))
assert len(r2) == 307
for raw_id in D18:
    r2.append(from_mi(raw_id, "D-18", "MI's D-18, as in R1. Its own first lines name no temporary path (by reading "
                      "tests/test_current_host_readback_driver.py:28-50 and :115-145), so R2's default directory does not "
                      "change them."))
fixture = mi_rows[MC22_ID]
assert fixture["statement"]["events"] == [{"status": "ERROR", "reason_first_line": ORDINARY}]
r2.append({"id": MC22_ID, "form": "raw", **fixture["statement"], "source": "MC22",
           "note": "Contract section 8 (S8) and MC22: in an ordinary run the readback CPU class fails at setUpClass with the "
                   "fixed reason and its three methods neither run nor are reported. Raw form. MI's retained per-module "
                   "ordinary run on this host records exactly this event (final-003, " + fixture["mi_id"] + ")."})

for name, rows in (("r1-attributions-001.json", r1), ("r2-attributions-001.json", r2)):
    ids = [row["id"] for row in rows]
    assert len(ids) == len(set(ids)), name
    for row in rows:
        assert tool.valid_statement(row) and consistent(row), row["id"]
    document = {"schema": tool.ATTRIBUTIONS_SCHEMA, "attributions": rows}
    data = (json.dumps(document, indent=1, sort_keys=True, ensure_ascii=True) + "\n").encode("ascii")
    path = os.path.join(out_dir, name)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, "wb") as stream:
        stream.write(data)
    print(name, len(rows), hashlib.sha256(data).hexdigest(), len(data))
print(json.dumps({"r1": len(r1), "r1_mi_other": len(mi_other), "r2": len(r2), "not_attributed": NOT_ATTRIBUTED}))
