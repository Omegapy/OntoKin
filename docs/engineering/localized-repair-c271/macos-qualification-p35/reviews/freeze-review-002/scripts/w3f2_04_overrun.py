"""Freeze review 002, script 04: the overrun procedure's frozen parts against capture_probe.py's interface.

Checks the candidates against each .P, the select_shell texts against a text generated from the candidates,
every probe and stop command (argv, pairs, output, records, expect), and step 3's /targets/<k-1> pointer
against each probe's actual target order. Also simulates every select_shell over every subset of recorded
started records, by a small interpreter of the frozen text's exact grammar (no shell is started).

Run: <worktree>/.venv/bin/python -I -S -B w3f2_04_overrun.py OUTPUT.json
"""
import itertools
import json
import re
import sys

PROCESS_EVENTS = {"subprocess.Popen", "os.posix_spawn", "os.exec", "os.fork", "os.forkpty", "os.spawn", "os.system"}


def refuse(event, args):
    if event in PROCESS_EVENTS:
        raise PermissionError("no process: " + event)


sys.addaudithook(refuse)

P35 = "<local>/c271-p35"
E = P35 + "/evidence"
F2 = P35 + "/workers/W2-freeze-002/FREEZE-002.json"
WT = "<worktree>"
CAPTURE = WT + "/docs/engineering/localized-repair-c271/macos-qualification-p35/tooling/capture_probe.py"
PREFIX = ["/usr/bin/env", "-i", "LANG=C.UTF-8", "LC_ALL=C.UTF-8", "PATH=/usr/bin:/bin", "TZ=UTC", "UV_THREADPOOL_SIZE=2",
          WT + "/.venv/bin/python", "-I", "-S", "-B", CAPTURE]


def generate_select(cid, cands):
    parts = ["k=''"]
    for c in cands:
        a = c["after"]
        parts.append("if [ -e '%s' ] || [ -L '%s' ]; then k=\"${k}%d\"; fi" % (a, a, c["k"]))
    parts.append("if [ -n \"$k\" ]; then printf 'overrun-select: %%s\\n' \"%s.O$k\"; else printf 'overrun-select: none\\n'; fi" % cid)
    return "; ".join(parts)


CLAUSE = re.compile(r"if \[ -e '([^']+)' \] \|\| \[ -L '([^']+)' \]; then k=\"\$\{k\}(\d)\"; fi; ")
TAIL = re.compile(r"if \[ -n \"\$k\" \]; then printf 'overrun-select: %s\\n' \"(C\d\d)\.O\$k\"; else printf 'overrun-select: none\\n'; fi")


def simulate(text, recorded):
    """Interpret exactly the grammar of the frozen select texts; refuse anything else.

    The text must be k=''; then clauses 'if [ -e P ] || [ -L P ]; then k="${k}N"; fi; ' with the same P twice,
    then the printf tail, and nothing else: the pieces must rebuild the text byte for byte.
    """
    head = "k=''; "
    if not text.startswith(head):
        raise ValueError("unexpected start")
    pos, k, rebuilt = len(head), "", head
    while True:
        m = CLAUSE.match(text, pos)
        if not m:
            break
        if m.group(1) != m.group(2):
            raise ValueError("clause tests two different paths")
        if m.group(1) in recorded:
            k += m.group(3)
        rebuilt += m.group(0)
        pos = m.end()
    m = TAIL.match(text, pos)
    if not m or m.end() != len(text):
        raise ValueError("unexpected tail: " + text[pos:])
    rebuilt += m.group(0)
    if rebuilt != text:
        raise ValueError("pieces do not rebuild the text")
    return "overrun-select: " + (m.group(1) + ".O" + k if k else "none")


def pairs_of(argv, sub):
    i = argv.index(sub)
    rest, pairs, output = argv[i + 1:], [], None
    j = 0
    while j < len(rest):
        if rest[j] == "--pair":
            pairs.append([rest[j + 1], rest[j + 2]])
            j += 3
        elif rest[j] == "--output":
            output = rest[j + 1]
            j += 2
        else:
            raise ValueError("unexpected argument " + rest[j])
    return pairs, output


def main():
    with open(F2, "rb") as s:
        f = json.loads(s.read())
    cmds = {c["id"]: c for c in f["commands"]}
    ov = f["overrun"]
    out = {"script": "w3f2_04_overrun.py", "commands": {}, "problems": []}

    def bad(what, **kw):
        out["problems"].append(dict({"what": what}, **kw))

    capture_ids = []
    for cid in ("C16", "C17", "C19"):
        main_cmd = cmds[cid]
        cands = main_cmd["overrun"]["candidates"]
        row = {"candidates": len(cands)}
        if cands != ov["candidates"][cid]:
            bad("per-command candidates differ from overrun.candidates", id=cid)
        P = cmds[cid + ".P"]
        ppairs, _ = pairs_of(P["argv"], "probe")
        row["P_pairs_equal_candidates_in_order"] = ppairs == [[c["before"], c["after"]] for c in cands]
        if not row["P_pairs_equal_candidates_in_order"]:
            bad(".P pairs differ from the candidates", id=cid)
        if [c["k"] for c in cands] != list(range(1, len(cands) + 1)):
            bad("candidate numbers not 1..n", id=cid)
        # The select text.
        text = main_cmd["overrun"]["select_shell"]
        row["select_equals_generated"] = text == generate_select(cid, cands)
        if not row["select_equals_generated"]:
            bad("select_shell differs from the generated text", id=cid)
        # Every subset of recorded started records, through the interpreter.
        sim = {}
        for r in range(len(cands) + 1):
            for subset in itertools.combinations(range(1, len(cands) + 1), r):
                recorded = {cands[k - 1]["after"] for k in subset}
                got = simulate(text, recorded)
                want = "overrun-select: " + (cid + ".O" + "".join(map(str, subset)) if subset else "none")
                sim["".join(map(str, subset)) or "none"] = got
                if got != want:
                    bad("selection maps a set wrongly", id=cid, subset=subset, got=got)
        row["selection_by_subset"] = sim
        # The probe and stop maps.
        probes, stops = main_cmd["overrun"]["probe_commands"], main_cmd["overrun"]["stop_commands"]
        if {"probes": probes, "stops": stops} != ov["commands"][cid]:
            bad("per-command maps differ from overrun.commands", id=cid)
        subsets = ["".join(map(str, s)) for r in range(1, len(cands) + 1) for s in itertools.combinations(range(1, len(cands) + 1), r)]
        if sorted(probes) != sorted(subsets):
            bad("probe map does not cover every non-empty subset", id=cid, have=sorted(probes))
        mapping = {}
        for digits, pid in probes.items():
            c = cmds[pid]
            capture_ids.append(pid)
            pairs, output = pairs_of(c["argv"], "probe")
            want_pairs = [[cands[int(d) - 1]["before"], cands[int(d) - 1]["after"]] for d in digits]
            if c["argv"][:len(PREFIX)] != PREFIX or c["argv"][len(PREFIX)] != "probe":
                bad("probe argv prefix", id=pid)
            if pairs != want_pairs:
                bad("probe pairs differ from its digits' candidates", id=pid)
            if output != E + "/" + main_cmd["name"] + ".overrun-probes-" + digits + ".json" or c["outputs"] != [output]:
                bad("probe output", id=pid, output=output)
            if c["name"] != main_cmd["name"] + ".overrun-probes-" + digits:
                bad("probe name", id=pid)
            if c["cwd"] != E or c["environment"]["name"] != "declared" or c["phase"] != "capture":
                bad("probe cwd/env/phase", id=pid)
            exp = {json.dumps(r, sort_keys=True) for r in c["expect"]}
            if json.dumps({"file": output, "pointer": "/targets", "length": len(digits)}, sort_keys=True) not in exp:
                bad("probe expect lacks /targets length", id=pid)
            # Step 3's pointer: /targets/<k-1> for candidate k, against the actual position of candidate k.
            for j, d in enumerate(digits):
                k = int(d)
                mapping.setdefault(pid, []).append({"target_index": j, "candidate_k": k, "step3_pointer": "/targets/%d" % (k - 1),
                                                    "pointer_correct": j == k - 1})
        row["step3_pointer_by_probe"] = mapping
        row["probes_where_step3_pointer_is_wrong"] = sorted(p for p, rows in mapping.items() if not all(x["pointer_correct"] for x in rows))
        for k, sid in stops.items():
            c = cmds[sid]
            capture_ids.append(sid)
            pairs, output = pairs_of(c["argv"], "stop")
            cand = cands[int(k) - 1]
            if c["argv"][:len(PREFIX)] != PREFIX or c["argv"][len(PREFIX)] != "stop":
                bad("stop argv prefix", id=sid)
            if pairs != [[cand["before"], cand["after"]]]:
                bad("stop pair differs from its candidate", id=sid)
            if output != E + "/" + main_cmd["name"] + ".stop-" + k + ".json" or c["outputs"] != [output]:
                bad("stop output", id=sid)
            if c["cwd"] != E or c["environment"]["name"] != "declared" or c["phase"] != "capture":
                bad("stop cwd/env/phase", id=sid)
        if sorted(stops) != [str(i) for i in range(1, len(cands) + 1)]:
            bad("stop map does not cover every candidate", id=cid)
        out["commands"][cid] = row
    out["capture_commands_equal"] = sorted(capture_ids) == sorted(f["capture_commands"])
    out["capture_counts"] = {"probes": sum(1 for i in capture_ids if ".O" in i), "stops": sum(1 for i in capture_ids if ".S" in i)}
    out["capture_bounds"] = sorted({cmds[i]["limits"]["outer_bound_s"] for i in capture_ids})
    out["absent_outputs_of_capture"] = sum(len(cmds[i]["outputs_absent_before"]) for i in capture_ids)
    out["capture_all_in_absent_before"] = all(p in set(f["absent_paths"]["before_preparation"])
                                              for i in capture_ids for p in cmds[i]["outputs_absent_before"])
    with open(sys.argv[1], "x") as s:
        json.dump(out, s, indent=1, sort_keys=True)
        s.write("\n")
    print(json.dumps({"problems": out["problems"], "capture_equal": out["capture_commands_equal"], "counts": out["capture_counts"],
                      "bounds": out["capture_bounds"], "absent": out["absent_outputs_of_capture"],
                      "wrong_step3": {c: out["commands"][c]["probes_where_step3_pointer_is_wrong"] for c in out["commands"]},
                      "select_ok": {c: out["commands"][c]["select_equals_generated"] for c in out["commands"]}}, sort_keys=True))


main()
