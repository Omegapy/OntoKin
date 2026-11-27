"""Freeze review 002, script 07: the timer and selection texts.

1. Each jq -r extraction in records/texts/ equals the freeze's string (plus jq's newline).
2. A token scan of the timer template and the selection texts: which programs they name, and whether any
   redirection, pipe, substitution other than $(/bin/date +%s), eval, exec, trap, kill or wait appears.
3. Synthetic timers for the tests in <OUT>/timer-test/: the frozen template with only {exit_file} and {bound}
   replaced, the exit file inside <OUT>.

Run: <worktree>/.venv/bin/python -I -S -B w3f2_07_texts.py OUTPUT.json
"""
import json
import os
import re
import sys

PROCESS_EVENTS = {"subprocess.Popen", "os.posix_spawn", "os.exec", "os.fork", "os.forkpty", "os.spawn", "os.system"}


def refuse(event, args):
    if event in PROCESS_EVENTS:
        raise PermissionError("no process: " + event)


sys.addaudithook(refuse)

P35 = "<local>/c271-p35"
OUT = P35 + "/workers/W3-freeze-002"
F2 = P35 + "/workers/W2-freeze-002/FREEZE-002.json"


def scan(text):
    """Programs and risky constructs, outside single-quoted strings."""
    unquoted = re.sub(r"'[^']*'", "''", text)
    return {
        "absolute_programs": sorted(set(re.findall(r"(?<![\w'])(/[\w/.-]+)", unquoted))),
        "command_substitutions": re.findall(r"\$\(([^)]*)\)", unquoted),
        "arithmetic": re.findall(r"\$\(\(([^)]*)\)\)", unquoted),
        "redirections": re.findall(r"[<>]", unquoted),
        "pipes_outside_case": [m for m in re.findall(r"\|\|?", unquoted)],
        "backticks": "`" in unquoted,
        "words": sorted(set(w for w in re.findall(r"(?:^|[;\s])([a-z]+)\b", unquoted)) &
                        {"eval", "exec", "trap", "kill", "wait", "source", "rm", "touch", "tee", "cat", "echo", "read"}),
    }


def main():
    with open(F2, "rb") as s:
        f = json.loads(s.read())
    out = {"script": "w3f2_07_texts.py", "extraction_mismatch": []}
    for c in f["commands"]:
        with open(OUT + "/records/texts/" + c["id"] + ".timer.sh", "rb") as s:
            if s.read() != (c["timer_shell"] + "\n").encode("utf-8"):
                out["extraction_mismatch"].append(c["id"] + ".timer")
        if "overrun" in c:
            with open(OUT + "/records/texts/" + c["id"] + ".select.sh", "rb") as s:
                if s.read() != (c["overrun"]["select_shell"] + "\n").encode("utf-8"):
                    out["extraction_mismatch"].append(c["id"] + ".select")
    template = f["launch"]["timer_template"]
    out["template"] = template
    out["template_placeholders"] = sorted(set(re.findall(r"\{[a-z_]+\}", template)))
    out["template_scan"] = scan(template.replace("{exit_file}", "/X").replace("{bound}", "600"))
    out["select_scan"] = {c["id"]: scan(c["overrun"]["select_shell"]) for c in f["commands"] if "overrun" in c}
    out["bounds"] = sorted({c["limits"]["outer_bound_s"] for c in f["commands"]})
    out["bound_by_command"] = {c["id"]: c["limits"]["outer_bound_s"] for c in f["commands"]}
    # Synthetic timers, the template's own text with an exit file inside <OUT>.
    tdir = OUT + "/timer-test"
    os.mkdir(tdir)
    cases = {"t1-exit-file-present": (tdir + "/t1.exit.txt", 5), "t2-outer-bound": (tdir + "/t2.exit.txt", 2),
             "t3-exit-file-later": (tdir + "/t3.exit.txt", 30), "t4-outer-bound-zsh-background": (tdir + "/t4.exit.txt", 3)}
    out["synthetic"] = {}
    for name, (path, bound) in cases.items():
        text = template.replace("{exit_file}", path).replace("{bound}", str(bound))
        with open(tdir + "/" + name + ".sh", "x") as s:
            s.write(text + "\n")
        out["synthetic"][name] = {"exit_file": path, "bound": bound, "text": text}
    with open(tdir + "/t1.exit.txt", "x") as s:
        s.write("0\n")
    with open(sys.argv[1], "x") as s:
        json.dump(out, s, indent=1, sort_keys=True)
        s.write("\n")
    print(json.dumps({"extraction_mismatch": out["extraction_mismatch"], "placeholders": out["template_placeholders"],
                      "template_scan": out["template_scan"], "select_scan_C17": out["select_scan"]["C17"],
                      "bounds": out["bounds"]}, sort_keys=True))


main()
