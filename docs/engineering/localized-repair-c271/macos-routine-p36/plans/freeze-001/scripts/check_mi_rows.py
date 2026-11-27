"""W2 (freeze 001): MI-derived attribution rows equal the tool's own record_statement of MI's collected records."""
import sys
if not sys.flags.dont_write_bytecode:
    raise SystemExit(2)
import importlib.util, json, glob, os
tool_path, attr_dir, mi_dir = sys.argv[1:4]
spec = importlib.util.spec_from_file_location("w2f_tool", tool_path)
tool = importlib.util.module_from_spec(spec); spec.loader.exec_module(tool)
records = {}
for path in sorted(glob.glob(os.path.join(mi_dir, "collect-*.json"))):
    record = json.load(open(path))
    for row in record["tests"] + record["fixtures"]:
        rid = row["id"][len("tests."):] if row["id"].startswith("tests.") else row["id"].replace("(tests.", "(")
        records[rid] = row
checked, bad = 0, []
for name in ("r1-attributions-001.json", "r2-attributions-001.json"):
    for row in json.load(open(os.path.join(attr_dir, name)))["attributions"]:
        if row["source"] not in ("D-18", "MI final-003", "MC22"):
            continue
        expected = tool.record_statement(records[row["id"]], lambda t: t)
        got = {k: row[k] for k in tool.STATEMENT_KEYS}
        checked += 1
        if expected != got:
            bad.append(row["id"])
print(json.dumps({"checked": checked, "different": bad}))
