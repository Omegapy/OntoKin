"""Dump each frozen command of FREEZE-001.json into its own indented JSON file (read only on the freeze)."""
import json, sys, os
freeze, outdir = sys.argv[1], sys.argv[2]
d = json.load(open(freeze, "rb"))
os.makedirs(outdir, exist_ok=True)
for c in d["commands"]:
    cid = c["id"]
    with open(os.path.join(outdir, cid + ".json"), "x") as fh:
        json.dump(c, fh, indent=1, sort_keys=False)
        fh.write("\n")
for k in ["deferred_arguments", "launch", "overrun", "stop_rules", "failure_capture", "starts",
          "expected_outcomes", "attributions", "decisions", "carried_findings", "fixed_state",
          "limits", "open_questions", "absent_paths"]:
    with open(os.path.join(outdir, "_" + k + ".json"), "x") as fh:
        json.dump(d[k], fh, indent=1)
        fh.write("\n")
with open(os.path.join(outdir, "_bindings.json"), "x") as fh:
    json.dump(d["bindings"], fh, indent=1)
    fh.write("\n")
