"""W2 freeze author: build operational freeze 002 from freeze 001, under disposition 001 of freeze review 001.

Run with <worktree>/.venv/bin/python -I -S -B. Standard library only. It refuses every process creation, imports
nothing of the project, reads freeze 001, the review's records and the disposition, and creates only absent files
under OUT2: P00's second list, FREEZE-002.json, the difference record and its own build record.
Usage: w2f2_build.py
"""
from copy import deepcopy
import hashlib
import itertools
import json
import os
import stat
import sys

PROCESS_EVENTS = {"subprocess.Popen", "os.posix_spawn", "os.exec", "os.fork", "os.forkpty", "os.spawn", "os.system"}
sys.addaudithook(lambda event, args: (_ for _ in ()).throw(PermissionError(event)) if event in PROCESS_EVENTS else None)

LOCAL = "<local>"
WT = "<worktree>"
E = LOCAL + "/c271-p35/evidence"
OUT1 = LOCAL + "/c271-p35/workers/W2-freeze-001"
OUT2 = LOCAL + "/c271-p35/workers/W2-freeze-002"
W3F = LOCAL + "/c271-p35/workers/W3-freeze-001"
DISPOSITION = LOCAL + "/c271-p35/director/reviews/FREEZE-REVIEW-DISPOSITION-001.json"
REVIEW_MD, REVIEW_JSON = W3F + "/FREEZE-REVIEW-001.md", W3F + "/FREEZE-REVIEW-001.json"
TOOLING = WT + "/docs/engineering/localized-repair-c271/macos-qualification-p35/tooling"
WRAPPER = LOCAL + "/c271-p35/director/run/run_once_v2.sh"
NODE = LOCAL + "/c271-macos/node-v24.22.1-darwin-arm64/bin/node"
GIT = "/Library/Developer/CommandLineTools/usr/bin/git"
CF_FILE = "<home>/.CFUserTextEncoding"
CF_SHA = "bd605d2eae2bc28178ba94d69e189242f971d699c5846addae706d7e52bc69fd"
BOOT = "C90010BA-4DA9-475D-BBAB-CF1A9C40175A"
ATTEMPT = "s7-001"
F1_PATH, F1_SHA, F1_SIZE = OUT1 + "/FREEZE-001.json", "a5d994ea2db61262bf851379b9289ec028242bb7943d63df1992b3f386b634e6", 884666
F1_SUMS = OUT1 + "/SHA256SUMS.txt"
F2_PATH = OUT2 + "/FREEZE-002.json"
MC11 = W3F + "/MC11-REVIEWED-LIST-001.json"
MC11_BINDING = {"sha256": "aade03ac64a506678ce7ade184ecedcd10c5f6a58077d1f01aa7d0d70db63800", "size_bytes": 344283,
                "mode": "0o644"}
OLD_PH, NEW_PH, MC11_PH = "<FREEZE-001.json SHA-256>", "<FREEZE-002.json SHA-256>", "<MC11 reviewed list SHA-256>"
P00_LIST_REL = "s7/p00-freeze-001-rebound.sha256sums.txt"
P00_LIST = OUT2 + "/" + P00_LIST_REL


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    with open(path, "rb") as stream:
        return stream.read()


def binding_of(path):
    info = os.lstat(path)
    if not stat.S_ISREG(info.st_mode):
        raise SystemExit("not a regular file: " + path)
    data = read(path)
    return {"sha256": sha_bytes(data), "size_bytes": len(data), "mode": "0o%03o" % stat.S_IMODE(info.st_mode),
            "nlink": info.st_nlink}


WRITTEN = []


def write_new(path, data):
    if os.path.lexists(path):
        raise SystemExit("exists: " + path)
    os.makedirs(os.path.dirname(path), mode=0o755, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    WRITTEN.append(path)
    return {"path": path, "sha256": sha_bytes(data), "size_bytes": len(data), "mode": "0o644"}


def shell_quote(argv):
    for item in argv:
        if "'" in item or "\n" in item:
            raise SystemExit("argv element cannot be single-quoted: " + repr(item))
    return " ".join("'" + item + "'" for item in argv)


def exit_is(name, status):
    return {"file": E + "/" + name + ".exit.txt", "text_equals": "%d\n" % status}


def reorder(row, after, key, value):
    """The row with key inserted right after the key 'after' (insertion order is the JSON order)."""
    out = {}
    for k, v in row.items():
        if k == key:
            continue
        out[k] = v
        if k == after:
            out[key] = value
    if key not in out:
        out[key] = value
    return out


# -----------------------------------------------------------------------------------------------------------
# Inputs: freeze 001 (by its digest), its sums, the review, the disposition and the reviewed MC11 list
# -----------------------------------------------------------------------------------------------------------
raw1 = read(F1_PATH)
if sha_bytes(raw1) != F1_SHA or len(raw1) != F1_SIZE:
    raise SystemExit("FREEZE-001.json differs from its reviewed digest")
F1 = json.loads(raw1)
disposition_raw = read(DISPOSITION)
disposition = json.loads(disposition_raw)
review_md_raw, review_json_raw = read(REVIEW_MD), read(REVIEW_JSON)
if disposition["review"]["sha256"] != {"FREEZE-REVIEW-001.md": sha_bytes(review_md_raw),
                                       "FREEZE-REVIEW-001.json": sha_bytes(review_json_raw)}:
    raise SystemExit("the review records differ from the disposition's digests")
if disposition["freeze_001"]["sha256"] != F1_SHA:
    raise SystemExit("the disposition names another freeze 001")
mc11_disposed = disposition["mc11_reviewed_list"]
if {k: mc11_disposed[k] for k in ("sha256", "size_bytes", "mode")} != MC11_BINDING:
    raise SystemExit("the disposition's MC11 binding differs from the brief")
mc11_actual = binding_of(MC11)
if {k: mc11_actual[k] for k in ("sha256", "size_bytes", "mode")} != MC11_BINDING or mc11_actual["nlink"] != 1:
    raise SystemExit("the reviewed MC11 list differs from its disposed binding")
mc11_doc = json.loads(read(MC11))
if mc11_doc.get("schema") != "ontokin.c271.p35-mc11-reviewed/2" or mc11_doc.get("status") != "REVIEWED":
    raise SystemExit("the reviewed MC11 list is not schema /2 REVIEWED")
sums1_raw = read(F1_SUMS)
sums1 = {}
for line in sums1_raw.decode("ascii").splitlines():
    digest, rel = line.split("  ", 1)
    sums1[rel] = digest
if sums1.get("FREEZE-001.json") != F1_SHA:
    raise SystemExit("freeze 001's SHA256SUMS.txt does not hold FREEZE-001.json's digest")

ENVS = F1["environments"]
F1_ROWS = {row["id"]: row for row in F1["commands"]}
if len(F1_ROWS) != len(F1["commands"]) or F1["order"] != [row["id"] for row in F1["commands"]]:
    raise SystemExit("unexpected command list in freeze 001")

# -----------------------------------------------------------------------------------------------------------
# Deferred values (FREEZE-002's own digest stays deferred; the MC11 list is bound; C14's two stay)
# -----------------------------------------------------------------------------------------------------------
DEFERRED1 = F1["deferred_arguments"]
if set(DEFERRED1) != {OLD_PH, MC11_PH, "<current discovery SHA-256>", "<baseline discovery SHA-256>"}:
    raise SystemExit("unexpected deferred arguments in freeze 001")
DEFERRED2 = {}
for key, value in DEFERRED1.items():
    if key == MC11_PH:
        continue
    if key == OLD_PH:
        DEFERRED2[NEW_PH] = {
            "kind": "freeze_sha256",
            "description": "the SHA-256 of FREEZE-002.json as the record of freeze review 002 states it, which the "
                           "Director's disposition of that review repeats; the checker refuses any other value (it "
                           "hashes the file)"}
    else:
        DEFERRED2[key] = deepcopy(value)


def wrapper_rules(name, cwd, env_sha, argv, sources):
    """The wrapper predicates and deferred rows exactly as freeze 001's generator builds them."""
    record = E + "/" + name
    placeholders = [index for index, item in enumerate(argv) if item.startswith("<") and item.endswith(">")]
    rows, rules = [], []
    for index in placeholders:
        source = sources[argv[index]]
        rows.append({"argv_index": index, "wrapper_argv_index": index + 6, "placeholder": argv[index],
                     "source": source})
        rule = {"file": record + ".command.json", "pointer": "/argv/%d" % index}
        if source["kind"] == "freeze_sha256":
            rule["equals_freeze_sha256"] = True
        elif source["kind"] == "sha256_of_file":
            rule["equals_sha256_of"] = source["file"]
        else:
            rule["equals_from"] = {"file": source["file"], "pointer": source["pointer"]}
        rules.append(rule)
    expect = [{"file": record + ".command.json", "pointer": "/argv",
               "argv_equals_except": {"argv": argv, "indices": placeholders}}] + rules + [
        {"file": record + ".command.json", "pointer": "/cwd", "equals": cwd},
        {"file": record + ".command.json", "pointer": "/environment/sha256", "equals": env_sha},
        {"file": record + ".command.json", "pointer": "/boot/before", "equals": BOOT},
        {"file": record + ".command.json", "pointer": "/boot/after", "equals": BOOT},
        {"file": record + ".command.json", "pointer": "/retries", "equals": 0}]
    return rows, expect


# The reconstruction must reproduce every freeze 001 row before it is used to change one.
for row in F1["commands"]:
    rows, rules = wrapper_rules(row["name"], row["cwd"], row["environment"]["sha256"], row["argv"], DEFERRED1)
    if rows != row["deferred_arguments"] or row["expect"][:len(rules)] != rules:
        raise SystemExit("cannot reproduce freeze 001's wrapper predicates of " + row["id"])
    if row["wrapper_argv"] != ["/bin/sh", WRAPPER, row["name"], row["cwd"], row["environment"]["file"], "--",
                               *row["argv"]] or row["shell"] != shell_quote(row["wrapper_argv"]):
        raise SystemExit("cannot reproduce freeze 001's wrapper argv of " + row["id"])


def rewrap(row, argv):
    """A row of freeze 001 with a new argv: wrapper argv, shell, deferred rows and wrapper predicates rebuilt."""
    old_rows, old_rules = wrapper_rules(row["name"], row["cwd"], row["environment"]["sha256"], row["argv"], DEFERRED1)
    new_rows, new_rules = wrapper_rules(row["name"], row["cwd"], row["environment"]["sha256"], argv, DEFERRED2)
    full = ["/bin/sh", WRAPPER, row["name"], row["cwd"], row["environment"]["file"], "--", *argv]
    out = deepcopy(row)
    out.update(argv=argv, wrapper_argv=full, shell=shell_quote(full), deferred_arguments=new_rows,
               expect=new_rules + deepcopy(row["expect"][len(old_rules):]))
    return out


def make_row(ident, name, purpose, cwd, env_name, argv, *, outputs, expect, starts, limits, capture, classification,
             phase, control=None, absent_before=None, audit_expect=None):
    """A new row, in freeze 001's shape."""
    env = ENVS[env_name]
    full = ["/bin/sh", WRAPPER, name, cwd, env["path"], "--", *argv]
    record = E + "/" + name
    rows, rules = wrapper_rules(name, cwd, env["sha256"], argv, DEFERRED2)
    return {"id": ident, "phase": phase, "name": name, "purpose": purpose, "control": control, "cwd": cwd,
            "environment": {"name": env_name, "file": env["path"], "sha256": env["sha256"]},
            "argv": argv, "wrapper_argv": full, "shell": shell_quote(full), "deferred_arguments": rows,
            "records": {"stdout": record + ".stdout.txt", "stderr": record + ".stderr.txt",
                        "exit": record + ".exit.txt", "command": record + ".command.json"},
            "outputs_absent_before": sorted(set((absent_before or []) + outputs + [record + s for s in (
                ".stdout.txt", ".stderr.txt", ".exit.txt", ".command.json")])),
            "outputs": outputs, "expect": rules + expect, "audit_expect": audit_expect or [],
            "starts": starts, "limits": limits, "failure_capture": capture, "classification": classification}


# -----------------------------------------------------------------------------------------------------------
# The bound timer and the selection (FR-01 (b), (c)): frozen texts, shell builtins, /bin/date and /bin/sleep only
# -----------------------------------------------------------------------------------------------------------
TIMER = ("f='{exit_file}'; b={bound}; s=$(/bin/date +%s); "
         "case $s in ''|*[!0-9]*) printf 'bound-timer: no-clock file=%s\\n' \"$f\"; exit 2;; esac; "
         "while :; do "
         "if [ -e \"$f\" ]; then printf 'bound-timer: exit-file began=%s now=%s bound_s=%s file=%s\\n' "
         "\"$s\" \"$(/bin/date +%s)\" \"$b\" \"$f\"; exit 0; fi; "
         "n=$(/bin/date +%s); "
         "case $n in ''|*[!0-9]*) printf 'bound-timer: no-clock file=%s\\n' \"$f\"; exit 2;; esac; "
         "if [ \"$n\" -gt \"$((s + b))\" ]; then printf 'bound-timer: outer-bound began=%s now=%s bound_s=%s "
         "file=%s\\n' \"$s\" \"$n\" \"$b\" \"$f\"; exit 1; fi; "
         "/bin/sleep 1; done")


def timer_for(row):
    exit_file, bound = row["records"]["exit"], row["limits"]["outer_bound_s"]
    if "'" in exit_file or type(bound) is not int or bound <= 0:
        raise SystemExit("cannot freeze a timer for " + row["id"])
    return TIMER.replace("{exit_file}", exit_file).replace("{bound}", str(bound))


def select_for(parent, pairs):
    parts = ["k=''"]
    for index, (before, after) in enumerate(pairs, 1):
        if "'" in after:
            raise SystemExit("cannot quote " + after)
        parts.append("if [ -e '%s' ] || [ -L '%s' ]; then k=\"${k}%d\"; fi" % (after, after, index))
    parts.append("if [ -n \"$k\" ]; then printf 'overrun-select: %%s\\n' \"%s.O$k\"; "
                 "else printf 'overrun-select: none\\n'; fi" % parent)
    return "; ".join(parts)


# -----------------------------------------------------------------------------------------------------------
# P00 (FR-07): one wrapper call of the system's shasum on freeze 002's list and on freeze 001's lines
# -----------------------------------------------------------------------------------------------------------
rebound = sorted((row for row in F1["bindings"] if row["path"].startswith(OUT1 + "/")), key=lambda r: r["path"])
lines = ["# Operational freeze 002 of gate MH (C271-P35): P00's second list. Every document that freeze 002",
         "# rebinds from freeze 001, each line as freeze 001's SHA256SUMS.txt gives it, the path made absolute."]
for row in rebound:
    rel = os.path.relpath(row["path"], OUT1)
    if sums1.get(rel) != row["sha256"]:
        raise SystemExit("freeze 001's sums and binding differ for " + rel)
    if {k: v for k, v in binding_of(row["path"]).items() if k != "nlink"} != {
            k: row[k] for k in ("sha256", "size_bytes", "mode")}:
        raise SystemExit("a rebound document changed: " + row["path"])
    lines.append(sums1[rel] + "  " + row["path"])
p00_list = write_new(P00_LIST, ("\n".join(lines) + "\n").encode("ascii"))

P00_NAME = ATTEMPT + "-p00-shasum"
p00 = make_row(
    "P00", P00_NAME, "FR-07: the system's shasum checks every file of freeze 002 (its SHA256SUMS.txt) and every "
    "document rebound from freeze 001 (freeze 001's lines, in P00's second list), the checker among them, before the "
    "checker runs", OUT2, "runner",
    ["/usr/bin/env", "-i", "PATH=/usr/bin:/bin", "/usr/bin/shasum", "-a", "256", "--strict", "-c", "SHA256SUMS.txt",
     P00_LIST_REL],
    outputs=[], phase="precondition",
    expect=[exit_is(P00_NAME, 0), {"file": E + "/" + P00_NAME + ".stderr.txt", "text_equals": ""},
            {"file": E + "/" + P00_NAME + ".stdout.txt", "text_includes": "FREEZE-002.json: OK\n"},
            {"file": E + "/" + P00_NAME + ".stdout.txt", "text_includes": P00_LIST_REL + ": OK\n"},
            {"file": E + "/" + P00_NAME + ".stdout.txt", "text_includes": OUT1 + "/s7/w2f_s7_check.py: OK\n"},
            {"file": E + "/" + P00_NAME + ".stdout.txt", "text_excludes": "FAILED"}],
    starts={"bounded": {"node": 0, "other": 0}, "recorded_unbounded": {"shasum_perl": 1}},
    limits={"outer_bound_s": 600}, capture={"rule": "FC-K2 and FC-K3 by the wrapper; it names no output"},
    classification=[
        {"outcome": "exit 0 (the wrapper's exit file holds 0)", "class": "continue with P01; D02 evaluates P00's "
         "predicates again"},
        {"outcome": "exit 1: a listed file differs, is missing or unreadable, or a line is malformed (--strict)",
         "class": "INPUT if a document of either freeze changed, PLAN if a list of this freeze is wrong; S7 does not "
                  "begin"},
        {"outcome": "any other exit, a wrapper exit 90, 91 or 92, or an overrun", "class": "PLAN or UNKNOWN; S7 does "
         "not begin"}])

# -----------------------------------------------------------------------------------------------------------
# The commands of freeze 001, changed only where a disposition or rule requires it
# -----------------------------------------------------------------------------------------------------------
changed_argv = {}
rows2 = {}
for row in F1["commands"]:
    argv = [NEW_PH if item == OLD_PH else F2_PATH if item == F1_PATH else MC11_BINDING["sha256"] if item == MC11_PH
            else item for item in row["argv"]]
    if argv != row["argv"]:
        changed_argv[row["id"]] = [i for i, (a, b) in enumerate(zip(row["argv"], argv)) if a != b]
        rows2[row["id"]] = rewrap(row, argv)
    else:
        rows2[row["id"]] = deepcopy(row)
expected_changed = {"P01", "D02", "Q04", "C01"} | {i for i in F1_ROWS if i.endswith(".X")}
if set(changed_argv) != expected_changed:
    raise SystemExit("unexpected argv changes: " + json.dumps(sorted(set(changed_argv) ^ expected_changed)))

main_ids = [i for i in F1["order"] if F1_ROWS[i]["phase"] == "s7" and "." not in i]
node_ids = ("C16", "C17", "C19")
EVENT_POPEN = {"pointer": "/event", "equals": "subprocess.Popen"}
added = {}


def append(ident, rules, why):
    rows2[ident]["expect"] += deepcopy(rules)
    added.setdefault(ident, []).append({"why": why, "count": len(rules)})


# FR-03: every recorded process event of C06, C07 and C17 is subprocess.Popen of the bound programs.
for ident in ("C06", "C07"):
    out = rows2[ident]["outputs"][0]
    append(ident, [{"file": out, "pointer": "/process_events", "each": EVENT_POPEN},
                   {"file": out, "pointer": "/process_events", "each": {"pointer": "/argv/0", "equals": GIT}}], "FR-03")
outcomes = rows2["C17"]["outputs"][0] + "/outcomes.json"
append("C17", [{"file": outcomes, "pointer": "/process_events", "each": EVENT_POPEN},
               {"file": outcomes, "pointer": "/process_events", "each": {"pointer": "/argv/0", "one_of": [NODE, GIT]}}],
       "FR-03")
# FR-12: the CF file's content after C17 and before C19, with the predicate kinds the checker has.
append("C17", [{"file": CF_FILE, "sha256": CF_SHA}], "FR-12")
# FR-02: each main command's expect holds its .L's and .P's predicates, in full.
for ident in main_ids:
    append(ident, rows2[ident + ".L"]["expect"], "FR-02 (" + ident + ".L)")
    if ident + ".P" in rows2:
        append(ident, rows2[ident + ".P"]["expect"], "FR-02 (" + ident + ".P)")

# FR-03, FR-04, FR-06 and FR-12: the classifications (each new row before the final UNKNOWN row); FR-02's row last.
LP_CLASS = {"outcome": "a predicate of the command's .L or .P unmet (FR-02: evaluated by its .X), a .P target in any "
            "state other than absent among them", "class": "as the .L's or the .P's own classification states: the "
            "command's evidence or start is UNKNOWN; S7 stops; FC-P6 by the pair's stop command only for a target "
            "'present, identity established'"}


def replace_class(ident, outcome, new_rows):
    rows = rows2[ident]["classification"]
    index = [i for i, r in enumerate(rows) if r["outcome"] == outcome]
    if len(index) != 1:
        raise SystemExit("classification row not found in %s: %s" % (ident, outcome))
    rows[index[0]:index[0] + 1] = new_rows


replace_class("C02", "exit 1, state_equals_host false", [
    {"outcome": "exit 1, state_equals_host false, in the boot that P02 to P04 passed just before",
     "class": "IMPLEMENTATION (FR-06): the provider's host_state disagrees with the observer, whose static passed the "
              "same HOST; MH stops"},
    {"outcome": "a boot other than HOST's (the record's boot_record or the wrapper's boot)",
     "class": "HOST: a reboot ended the attempt (FC-R5); a new boot restarts S4"}])
for ident in ("C03", "C04", "C05"):
    replace_class(ident, "refused at SOURCE, PYTHON, RUNTIME, DEPENDENCY, GIT, OS or ENVIRONMENT", [
        {"outcome": "refused at SOURCE or PYTHON (P02 to P04 passed the same plans statically in this boot)",
         "class": "PLAN if the harness caused it, IMPLEMENTATION if the observer did; never an input change (FR-06); "
                  "MH stops"},
        {"outcome": "refused at RUNTIME, DEPENDENCY, GIT, OS or ENVIRONMENT",
         "class": "INPUT or HOST changed; MH stops for reconciliation (a boot change restarts S4)"}])
for ident in ("C12", "C13"):
    rows = rows2[ident]["classification"]
    index = [i for i, r in enumerate(rows) if r["outcome"].startswith("current: findings")]
    if len(index) != 1:
        raise SystemExit("C12/C13 classification changed shape")
    rows.insert(index[0] + 1, {"outcome": "current: a difference that exporting C causes, not the source (an export "
                                          "lacks the .git pointer, .venv and every ignored file)",
                               "class": "PLAN (FR-06), not IMPLEMENTATION: corrected freeze, new attempt"})
c17_rows = rows2["C17"]["classification"]
index = [i for i, r in enumerate(c17_rows) if r["outcome"].startswith("setUpClass error: SOURCE")]
if len(index) != 1:
    raise SystemExit("C17 classification changed shape")
c17_rows.insert(index[0] + 1, {"outcome": "setUpClass error: an EVIDENCE refusal (for example an existing override "
                                          "path)", "class": "PLAN (FR-06)"})
index = [i for i, r in enumerate(c17_rows) if "actual Node environment differs" in r["outcome"]]
if len(index) != 1:
    raise SystemExit("C17 classification changed shape")
c17_rows.insert(index[0] + 1, {"outcome": "a positive case's probe.json refuses at another bootstrap check (for "
                                          "example the manifest's labels or bindings)",
                               "class": "IMPLEMENTATION (FR-06): the provider wrote that manifest; MH stops"})
if not c17_rows[-1]["outcome"].startswith("an interruption"):
    raise SystemExit("C17's last classification row is not the UNKNOWN row")
c17_rows.insert(len(c17_rows) - 1, {"outcome": "any unmet case or check within C17", "class":
                                    "C17's three CPU starts are one indivisible row (FR-04, MH-PLAN section 8): the "
                                    "remaining CPU starts still run within C17; C17.X is NOT_MET, C18 and C19 do not "
                                    "run, and the first unmet case's class decides"})
c17_rows.insert(len(c17_rows) - 1, {"outcome": "a process event other than subprocess.Popen of the bound Node or the "
                                               "bound Git", "class": "IMPLEMENTATION: a start of another program (FR-03); "
                                    "MH stops before C19"})
c17_rows.insert(len(c17_rows) - 1, {"outcome": "<home>/.CFUserTextEncoding differs after C17 (C17.X)", "class":
                                    "INPUT/HOST (HR-02): N-04's same-environment assumption fails (FR-12); MH stops; "
                                    "MC36 NOT_RUN"})
for ident in ("C06", "C07"):
    rows = rows2[ident]["classification"]
    if not rows[-1]["outcome"].startswith("exit 3 or missing record"):
        raise SystemExit(ident + "'s last classification row is not the UNKNOWN row")
    rows.insert(len(rows) - 1, {"outcome": "a process event other than subprocess.Popen of the bound Git",
                                "class": "IMPLEMENTATION: a start of another program (FR-03); MH stops"})
r2 = rows2["C19"]["classification"]
index = [i for i, r in enumerate(r2) if r["outcome"].startswith("MC30-probe refuses with 'Actual input identity")]
if len(index) != 1:
    raise SystemExit("C19 classification changed shape")
r2.insert(index[0] + 1, {"outcome": "MC30-probe refuses after the environment check with a message other than "
                                    "'Actual input identity differs'",
                         "class": "PLAN unless a bound input changed (FR-06); MC36 is NOT_RUN (the runner's stop, "
                                  "rows_independent false)"})
for ident in main_ids:
    rows2[ident]["classification"].append(deepcopy(LP_CLASS))

# -----------------------------------------------------------------------------------------------------------
# The frozen capture commands (FR-01 (c)): an overrun probe for every non-empty set of candidate pairs, and one
# FC-P6 stop per candidate pair; each with its argv and its absent outputs; run only after an overrun or for FC-P6
# -----------------------------------------------------------------------------------------------------------


def pairs_of(probe_row):
    argv = probe_row["argv"]
    index = argv.index("probe") + 1
    pairs = []
    while argv[index] == "--pair":
        pairs.append((argv[index + 1], argv[index + 2]))
        index += 3
    if argv[index] != "--output" or index + 2 != len(argv):
        raise SystemExit("unexpected probe argv")
    return pairs


capture_rows = []
overrun_members = {}
for parent in node_ids:
    p_row, c_row = F1_ROWS[parent + ".P"], F1_ROWS[parent]
    pairs = pairs_of(p_row)
    prefix = p_row["argv"][:p_row["argv"].index("probe")]
    if prefix[-1] != TOOLING + "/capture_probe.py" or "-B" not in prefix:
        raise SystemExit("unexpected probe prefix")
    probes, stops = {}, {}
    for size in range(1, len(pairs) + 1):
        for combo in itertools.combinations(range(len(pairs)), size):
            digits = "".join(str(i + 1) for i in combo)
            ident, name = parent + ".O" + digits, c_row["name"] + ".overrun-probes-" + digits
            out = E + "/" + name + ".json"
            chosen = [pairs[i] for i in combo]
            capture_rows.append(make_row(
                ident, name, "FR-01 (c) step 2: one capture_probe.py probe on the recorded start pairs %s of %s, "
                "after its overrun" % (", ".join(str(i + 1) for i in combo), parent), E, "declared",
                prefix + ["probe", *[x for pair in chosen for x in ("--pair", pair[0], pair[1])], "--output", out],
                outputs=[out], phase="capture",
                expect=[exit_is(name, 0), {"file": out, "pointer": "/command", "equals": "probe"},
                        {"file": out, "pointer": "/targets", "length": len(chosen)},
                        {"file": out, "pointer": "/boot_after", "equals": BOOT},
                        {"file": out, "pointer": "/process_events", "length": 0}],
                starts={"bounded": {"node": 0, "other": 0}, "recorded_unbounded": {"python_launcher": 1},
                        "only_after_an_overrun": True},
                limits={"outer_bound_s": 120},
                capture={"rule": "FC-P3 for the selected pairs; its record is FC-K4's own; FC-K2 and FC-K3 by the "
                                 "wrapper"},
                classification=[
                    {"outcome": "exit 0", "class": "for each target in state 'present, identity established', the "
                     "Director starts that pair's stop command once (FC-P6); for any other state nothing is sent; the "
                     "attempt stays UNKNOWN"},
                    {"outcome": "exit 2 or 3, a missing record, or an overrun of this probe", "class": "UNKNOWN: the "
                     "probe could not be made, nothing is sent (FC-P4); the owner is told"}]))
            probes[digits] = ident
    for k, (before, after) in enumerate(pairs, 1):
        ident, name = parent + ".S%d" % k, c_row["name"] + ".stop-%d" % k
        out = E + "/" + name + ".json"
        capture_rows.append(make_row(
            ident, name, "FC-P6 for candidate pair %d of %s: run once, only for a target 'present, identity "
            "established' in an overrun probe or in %s.P" % (k, parent, parent), E, "declared",
            prefix + ["stop", "--pair", before, after, "--output", out], outputs=[out], phase="capture",
            expect=[exit_is(name, 0), {"file": out, "pointer": "/command", "equals": "stop"},
                    {"file": out, "pointer": "/boot_after", "equals": BOOT},
                    {"file": out, "pointer": "/process_events", "length": 0}],
            starts={"bounded": {"node": 0, "other": 0}, "recorded_unbounded": {"python_launcher": 1},
                    "only_for_fc_p6": True},
            limits={"outer_bound_s": 120},
            capture={"rule": "FC-P6; its record holds each send and probe; FC-K2 and FC-K3 by the wrapper"},
            classification=[
                {"outcome": "exit 0, /stop/state absent", "class": "the recorded group ended; the attempt stays failed "
                 "or UNKNOWN (FC-P6: ending a process never changes the outcome)"},
                {"outcome": "any other state, exit or record", "class": "UNKNOWN; nothing more is sent (FC-R1: no "
                 "retry); the owner is told"}]))
        stops[str(k)] = ident
    overrun_members[parent] = {
        "candidates": [{"k": k, "before": before, "after": after} for k, (before, after) in enumerate(pairs, 1)],
        "select_shell": select_for(parent, pairs), "probe_commands": probes, "stop_commands": stops,
        "after_exit": parent + ".L, then " + parent + ".P (all candidate pairs)"}

# -----------------------------------------------------------------------------------------------------------
# Assemble the command list: P00, freeze 001's commands (changed as above), the capture commands; every
# command with its bound timer
# -----------------------------------------------------------------------------------------------------------
pre_ids = [i for i in F1["order"] if F1_ROWS[i]["phase"] in ("precondition", "preparation")]
s7_ids = [i for i in F1["order"] if F1_ROWS[i]["phase"] == "s7"]
post_ids = [i for i in F1["order"] if F1_ROWS[i]["phase"] == "post"]
if F1["order"] != pre_ids + s7_ids + post_ids:
    raise SystemExit("unexpected phase order in freeze 001")
commands = [p00] + [rows2[i] for i in pre_ids + s7_ids + post_ids] + capture_rows
for index, row in enumerate(commands):
    row = reorder(row, "shell", "timer_shell", timer_for(row))
    if row["id"] in overrun_members:
        row = reorder(row, "classification", "overrun", overrun_members[row["id"]])
    commands[index] = row
order = ["P00"] + pre_ids + s7_ids + post_ids
names = [row["name"] for row in commands]
ids = [row["id"] for row in commands]
if len(names) != len(set(names)) or len(ids) != len(set(ids)):
    raise SystemExit("duplicate names or ids")
by_id = {row["id"]: row for row in commands}

# -----------------------------------------------------------------------------------------------------------
# The absent paths: every record and output, the prepared entries; P00's and P01's own records excepted
# -----------------------------------------------------------------------------------------------------------
prepared_paths = {row["path"] for row in F1["preparation"]["entries"]}
before_prep, after_prep = set(prepared_paths), set()
for row in commands:
    before_prep |= set(row["outputs_absent_before"])
    if row["phase"] in ("s7", "post", "capture"):
        after_prep |= set(row["outputs_absent_before"])
before_prep -= set(by_id["P00"]["outputs_absent_before"]) | set(by_id["P01"]["outputs_absent_before"])
if after_prep & prepared_paths:
    raise SystemExit("an output path is also a prepared entry")
capture_paths = set()
for row in capture_rows:
    capture_paths |= set(row["outputs_absent_before"])
if before_prep != set(F1["absent_paths"]["before_preparation"]) | capture_paths:
    raise SystemExit("before_preparation is not freeze 001's plus the capture commands' paths")
if after_prep != set(F1["absent_paths"]["after_preparation"]) | capture_paths:
    raise SystemExit("after_preparation is not freeze 001's plus the capture commands' paths")
if any(not p.startswith(E + "/") for p in before_prep | after_prep):
    raise SystemExit("an absent path outside the evidence parent")
present_now = sorted(p for p in before_prep | set(by_id["P00"]["outputs_absent_before"]) |
                     set(by_id["P01"]["outputs_absent_before"]) if os.path.lexists(p))
if present_now:
    raise SystemExit("an S7 path exists: " + present_now[0])

# -----------------------------------------------------------------------------------------------------------
# Bindings: freeze 001's, unchanged, plus the reviewed MC11 list and P00's second list
# -----------------------------------------------------------------------------------------------------------
bindings = deepcopy(F1["bindings"])
bindings.append({"id": "review001:MC11-REVIEWED-LIST-001.json", "path": MC11, "kind": "file",
                 "role": "the MC11 reviewed list, written by freeze review 001 (W3) and accepted by its disposition; "
                         "bound directly, no longer deferred; it holds only while the probe, the dependencies "
                         "inventory and the reader tree are unchanged", "nlink_one": True, **MC11_BINDING})
bindings.append({"id": "freeze002:" + P00_LIST_REL, "path": P00_LIST, "kind": "file",
                 "role": "P00's second list, written by W2: freeze 001's lines for every document freeze 002 rebinds",
                 "nlink_one": True, **{k: p00_list[k] for k in ("sha256", "size_bytes", "mode")}})
if len({row["id"] for row in bindings}) != len(bindings) or len({row["path"] for row in bindings}) != len(bindings):
    raise SystemExit("duplicate binding")

# -----------------------------------------------------------------------------------------------------------
# The document
# -----------------------------------------------------------------------------------------------------------
review = {"record": {"path": REVIEW_MD, "sha256": sha_bytes(review_md_raw), "size_bytes": len(review_md_raw)},
          "structured": {"path": REVIEW_JSON, "sha256": sha_bytes(review_json_raw), "size_bytes": len(review_json_raw)},
          "verdict": disposition["review"]["verdict"], "mandatory": disposition["review"]["mandatory"],
          "nonmandatory": disposition["review"]["nonmandatory"]}
revision_of = {
    "id": "FREEZE-001", "path": F1_PATH, "sha256": F1_SHA, "size_bytes": F1_SIZE,
    "sums": {"path": F1_SUMS, "sha256": sha_bytes(sums1_raw), "files": len(sums1)},
    "status": disposition["freeze_001"]["status"], "review": review,
    "disposition": {"path": DISPOSITION, "sha256": sha_bytes(disposition_raw), "size_bytes": len(disposition_raw),
                    "recorded_at_utc": disposition["recorded_at_utc"]},
    "rules": "W2 revised freeze 001 under the disposition's dispositions and revision_rules only. Every other change is "
             "stated with its reason in the difference record (FREEZE-002-DIFFERENCES.json, 'stated_additions'), for "
             "freeze review 002 to check."}

launch = {
    "rule": "FR-01 (a) and (b), as disposition 001 adopts them; freeze review 001, answer 8's five conditions",
    "freeze": "The Director takes FREEZE-002.json's SHA-256 from the record of freeze review 002 (deferred argument "
              "'" + NEW_PH + "') and reads each member it runs from " + F2_PATH + " only.",
    "read": {
        "shell": "/usr/bin/jq -r --arg id ID '.commands[] | select(.id == $id) | .shell' " + F2_PATH,
        "timer": "/usr/bin/jq -r --arg id ID '.commands[] | select(.id == $id) | .timer_shell' " + F2_PATH,
        "select": "/usr/bin/jq -r --arg id ID '.commands[] | select(.id == $id) | .overrun.select_shell' " + F2_PATH},
    "command": "Every command of this freeze, whatever its phase, runs as its 'shell' member alone. The Director "
               "replaces only the named placeholders (its deferred_arguments), each by its 64-hex value taken "
               "mechanically from the frozen source; they sit inside single quotes, and the values hold no quote. "
               "Nothing is prepended or appended, so that zsh -c runs one simple command and the wrapper leads its "
               "group. The string goes to the shell tool in background mode, with no tool timeout: one call per "
               "command, never retried.",
    "timer": "In the same message, the Director passes the command's 'timer_shell' member, read the same way and passed "
             "alone, to the shell tool, also in background mode with no tool timeout. It is 'timer_template' with "
             "the command's exit file (records.exit) and its limits.outer_bound_s. It exits at the first of two "
             "events: the exit file exists, or more than outer_bound_s seconds have passed since it began. It prints "
             "which: 'bound-timer: exit-file ...' with status 0, or 'bound-timer: outer-bound ...' with status 1, each "
             "with its start and current epoch seconds. It starts only shell builtins (and forks of its own shell for "
             "$(...)), /bin/date and /bin/sleep, and writes nothing.",
    "timer_template": TIMER,
    "after": "The Director goes on when the command's background task has ended and its timer has printed 'exit-file'. "
             "'outer-bound' while the command's task is still running: the overrun rule ('overrun'). 'no-clock', or "
             "any other output or status of a timer: a PLAN deviation of this freeze's own tool; the Director records "
             "it, waits for the command's task without a bound, runs the command's .L, .P and .X as frozen, and stops "
             "S7 after them. A timer line printed after the command's task ended (a wrapper exit 90, 91 or 92 leaves "
             "no exit file) is recorded and has no effect.",
    "p00": "P00's outcome is read from its wrapper's exit file alone (FR-07; stop rule 1).",
    "starts": "The Director's, recorded and not bounded: one zsh per tool call (a command, a timer, a selection); each "
              "timer's /bin/date once at its start, about once a second and once at exit-file, and its /bin/sleep "
              "about once a second; one jq per member read."}

overrun = {
    "rule": "FR-01 (b), (c) and (d), and FR-04, as disposition 001 adopts them; FAILURE-CAPTURE version 2, sections 4 "
            "to 6 and 8. It replaces freeze 001's stop rule 9.",
    "trigger": "A command has overrun when its timer prints 'bound-timer: outer-bound' while the command's background "
               "task is still running.",
    "steps": [
        "1. The Director records the overrun with its time (the timer's line, with began= and now= in epoch seconds); "
        "the command's outcome is UNKNOWN. In the same message it starts the command's timer_shell once more in the "
        "background, for step 6.",
        "2. It runs the command's frozen overrun.select_shell (C16, C17 and C19; shell builtins only; it writes "
        "nothing), which applies the selection rule and prints 'overrun-select: <ID>' or 'overrun-select: none'. It "
        "starts the named frozen probe command once, as 'launch' says: one capture_probe.py probe on every start pair "
        "the command has recorded so far. A command without candidate pairs (every other command) selects none, and "
        "nothing is probed.",
        "3. For each target of that probe's record in state 'present, identity established' (its /targets/<k-1>/state, "
        "read with jq -r), it starts that candidate pair's frozen stop command <ID>.S<k> once (FC-P6). For any other "
        "state nothing is sent.",
        "4. It sends nothing to the wrapper, the tool's task or its group: no signal, no kill, no task stop.",
        "5. It waits for the wrapper's background task to end. Then it starts the command's frozen .L (FAILURE-CAPTURE "
        "section 6, step 5: FC-K5) and, where the command has one, its frozen .P (FC-P3 on every candidate pair: "
        "section 6, step 4, for every start recorded by then), with FC-P6 by <ID>.S<k> for a target 'present, "
        "identity established' whose stop has not run; then it writes the capture record (step 6) and stops the stage "
        "(step 7). The .X is not run: the outcome is UNKNOWN, whatever the records say.",
        "6. If the wrapper's task has not ended when the second timer of step 1 prints 'outer-bound', the Director "
        "tells the owner. The attempt stays UNKNOWN; the Director keeps waiting, sends nothing, and starts nothing more "
        "for MH until the owner decides."],
    "c17": "For C17, an FC-P6 stop of one case may be followed by the remaining CPU starts within C17 (FR-04; "
           "disposition 001 (d)): the Director lets them run and sends nothing; each is bounded by its own supervisor "
           "(30 s); C17.P probes every recorded start after the wrapper exits.",
    "selection_rule": "A candidate pair is recorded when its started record, the pair's second path, exists as a file "
                      "or a link when the selection runs ([ -e ] or [ -L ]). The recorded pairs, in the frozen "
                      "candidate order, name the one probe command <ID>.O<digits>, whose digits are their 1-based "
                      "candidate numbers; no recorded pair: no probe. Every non-empty set has its frozen command, so the "
                      "rule always names one; for the runner only the sets 1, 12 and 123 can occur "
                      "(rows_independent false).",
    "candidates": {parent: overrun_members[parent]["candidates"] for parent in node_ids},
    "candidate_basis": "FAILURE-CAPTURE FC-P2's pairs, as each command's .P lists them: the runner's "
                       "<row>/intent.json and <row>/started-1.json (one supervised start per row: started-2.json is "
                       "expected absent, and no frozen pair names it), the provider's provider-ledgers/<case>/"
                       "preflight.json and started.json.",
    "commands": {parent: {"probes": overrun_members[parent]["probe_commands"],
                          "stops": overrun_members[parent]["stop_commands"]} for parent in node_ids},
    "not_taken": "The review's further option, interrupting the overrunning tool itself, is not taken (disposition "
                 "001): it needs new procedure and tooling.",
    "limits": [
        "a start recorded after the selection is probed only after the wrapper exits (by the command's .P); if the "
        "wrapper never exits, no frozen step probes it, and the owner decides",
        "a process started between its record before and its started record cannot be named (FC-P2): its absence is "
        "never established, and the outcome stays UNKNOWN",
        "the timer counts from its own start, in the same message as the command's, not from the wrapper's "
        "start_epoch_s; it polls once a second, so a command that ends at its bound may be reported as an overrun "
        "(UNKNOWN), never the reverse"]}

stop_rules = [
    "Before S7: P00 runs first and must exit 0, which the Director reads from its wrapper's exit file alone (FR-07: "
    "nothing can check the checker before the checker runs). Then P01 to P05, D01 and D02 must each end with exit 0 "
    "and their predicates met (D02 evaluates P00 to D01 again). Otherwise S7 does not begin and no Node starts.",
    "Launch (FR-01 (a), (b)): every command of this freeze, whatever its phase, runs as 'launch' states: its 'shell' "
    "member alone, read raw from the bound freeze with jq -r, with only its named placeholders replaced by their 64-hex "
    "values, in the shell tool's background mode with no tool timeout, one call per command, never retried; and in the "
    "same message its 'timer_shell', the frozen bound timer, also in background mode.",
    "Order: the commands run strictly in the order given by 'order', each exactly once, through the bound wrapper, with "
    "the frozen argv, cwd and environment file. A command's .L (FC-K5 listing), then its .P (FC-P3 probe) where it has "
    "one, then its .X (the checker's 'expect') follow it before anything else. The Director starts a command only after "
    "the previous command's task has ended and its timer has printed 'exit-file'.",
    "Continue only when the .X command ends with exit 0 and prints state MET. Each main command's 'expect' holds its "
    "own predicates and then, in full, its .L's and its .P's (FR-02), so its .X evaluates them all: a .P target in any "
    "state other than absent, or any unmet .L or .P predicate, stops S7. Any other outcome of a command, its .L, .P or "
    ".X stops S7: start no other command except FAILURE-CAPTURE section 6 steps 3 to 5 (FC-P6 only for a target "
    "'present, identity established' in the .P record, by that pair's frozen stop command <ID>.S<k>, once), write the "
    "capture record (section 8, schema ontokin.c271.p35-failure-capture/1) by exclusive creation beside the attempt, "
    "and apply the command's classification. The capture record is the Director's.",
    "Within a runner command, rows_independent is false (R1 and R2): a row that misses its predicates stops the later "
    "rows, and an unknown row stops every later row (the runner's own rule).",
    "Remaining Node starts stop at the first deviation: every Node-starting command (C16, C17, C19) requires every "
    "earlier command's expectation met (MH-PLAN section 8). C17's three CPU starts are one indivisible row (FR-04): "
    "P07 section 6 runs the complete module, so within C17 an unmet case does not stop the remaining CPU starts, and "
    "any unmet expectation of C17 stops C18 and C19. No other row or command is declared independent.",
    "MC36 runs only after the cohort's positive starts (C17) and MC30-probe (C19 row 1) met their predicates (N-04).",
    "No retry, by anyone or anything (FC-R1 to FC-R5). A reboot ends the attempt (FC-R5).",
    "TR2-01: any interruption of a runner command makes that command UNKNOWN, whatever run.json says; each row's own "
    "outcome.json is kept as written.",
    "Outer bound (FR-01 (c), (d)): a command whose timer prints 'outer-bound' while its task is still running has "
    "overrun, and 'overrun' gives the six steps. Nothing is ever sent to the wrapper, the tool's task or the command's "
    "group.",
    "Wrapper exit 90 (refused before the start: a record path exists, or the argv encoding) means the command did not "
    "run: PLAN, stop. Wrapper exit 91 or 92 (the command ran once, the record was not built or written): the command's "
    "outcome is read from its own records, the FC-K3 record is written by hand from the wrapper's printed line under a "
    "new name (as for S5's static run, HR-01), and the outcome stays UNKNOWN unless every other record agrees.",
    "After S7 ends (C19.X MET, or a stop and its capture record), and only when every wrapper started has exited, the "
    "Director runs Q01 to Q04 once, in order; they start nothing bounded. While a wrapper has not exited, Q01 to Q04 "
    "wait for the owner's decision."]

FR_TEXT = {
    "FR-01": ["launch: the background launch of the 'shell' member alone and the frozen bound timer (each command's "
              "timer_shell, from launch.timer_template)",
              "overrun: the six steps that replace stop rule 9, the candidate pairs and the selection rule (each Node "
              "command's overrun.select_shell); the capture commands C16.O*, C17.O*, C19.O* (probes) and C16.S*, "
              "C17.S*, C19.S* (FC-P6 stops), each with its argv and its absent outputs; stop rules 2, 3 and 10",
              "overrun.c17: an FC-P6 stop of one case may be followed by the remaining CPU starts (d)"],
    "FR-02": ["each main command's expect holds, after its own predicates, every predicate of its .L and its .P "
              "(C16, C17, C19), which its .X evaluates; stop rule 4; the checker is unchanged"],
    "FR-03": ["C17's expect: every /process_events item has event subprocess.Popen and argv[0] the bound Node or the "
              "bound Git; C06's and C07's: subprocess.Popen and the bound Git only"],
    "FR-04": ["stop rule 6 (MH-PLAN section 8): C17's trio is one indivisible row; C17's classification"],
    "FR-05": ["FREEZE-AUTHOR-NOTES-002.md uses 25 directories, 18 files and 43 entries; the preparation is unchanged"],
    "FR-06": ["the classifications of C02, C03 to C05, C13 (and C12's shared list), C17 (positive case and setup) and "
              "C19"],
    "FR-07": ["P00, immediately before P01; stop rule 1; launch.p00"],
    "FR-08": ["recorded for the auditor; no change (disposition 001)"],
    "FR-09": ["limits.this_freeze: the driver's default temporary-cohort path is not exercised"],
    "FR-10": ["recorded; no change (disposition 001)"],
    "FR-11": ["recorded as a risk; C09's and C11's empty-stderr predicates stay, classed PLAN (disposition 001)"],
    "FR-12": ["n04.assumption names the user and <home>/.CFUserTextEncoding; C17's expect checks the file's SHA-256 "
              "after C17 and before C19; the predicate kinds cannot express its mode, its single link or the user "
              "(limits.this_freeze)"]}
carried = deepcopy(F1["carried_findings"])
for key in sorted(FR_TEXT):
    carried.append({"id": key, "source": "FREEZE-REVIEW-001, disposition 001", "met_by": FR_TEXT[key]})

decisions = deepcopy(F1["decisions"])
item7 = [d for d in decisions if d["item"] == 7][0]
item7["decision"] = (item7["decision"].split(" The reviewer reviews every entry")[0] +
                     " Freeze review 001 reviewed every entry and wrote the REVIEWED list " + MC11 + " (SHA-256 " +
                     MC11_BINDING["sha256"] + ", 344,283 bytes, 0o644); disposition 001 accepted it. Freeze 002 binds "
                     "it directly (bindings 'review001:MC11-REVIEWED-LIST-001.json'), and C01 passes its digest. The "
                     "configuration's dependencies/0.2.0 inventory is plan 001's (3545d5f9...).")
item7["source"] += "; disposition 001 (mc11_reviewed_list)"
decisions += [
    {"item": 12, "subject": "Launch and bound (FR-01 (a), (b))", "decision": "The background launch of the shell member "
     "alone, and a frozen bound timer per command (timer_shell, inline text in this freeze rather than a file, so that "
     "it is bound with the freeze itself and needs no digest of its own); see 'launch'.", "source": "FR-01, disposition 001"},
    {"item": 13, "subject": "Overrun (FR-01 (c), (d))", "decision": "The six steps in 'overrun'; a frozen probe command "
     "for every non-empty set of candidate pairs and a frozen stop per pair; a frozen selection text; after the "
     "wrapper exits, the command's .L and .P (stated addition A-1).", "source": "FR-01, FR-04, disposition 001"},
    {"item": 14, "subject": "The .L and .P predicates (FR-02)", "decision": "The preferred route: appended to the main "
     "command's expect, evaluated by its .X; the checker unchanged.", "source": "FR-02, disposition 001"},
    {"item": 15, "subject": "P00 (FR-07)", "decision": "One wrapper call in the freeze 002 directory: /usr/bin/shasum -a "
     "256 --strict -c on freeze 002's SHA256SUMS.txt and on P00's second list, which holds freeze 001's lines for every "
     "rebound document with absolute paths; PATH-only environment.", "source": "FR-07, disposition 001"}]

limits = deepcopy(F1["limits"])
limits["this_freeze"] += [
    "MH does not exercise the driver's default temporary-cohort path (_OwnedTemporaryCohort, its preserved copy and its "
    "cleanup): STATIC_TRAY_READBACK_CPU_OUTPUT keeps every cohort in place (Q4 of freeze 001); the seven methods and "
    "every provider check are unchanged (FR-09)",
    "C17's expect checks the content of <home>/.CFUserTextEncoding after C17 and before C19 (its SHA-256); the checker's "
    "expect predicates cannot express its mode, its single link or the process's user, which P01, D02 and Q04 (mode and "
    "link) and the 0x1F5 in each admitted value (the user, at each tool's start) cover only in part (FR-12)",
    "the overrun procedure's limits ('overrun.limits')"]

n04 = deepcopy(F1["n04"])
n04["how_shown"][2] = ("By elimination, Node's process.env held the declared environment plus __CF_USER_TEXT_ENCODING "
                       "with HOST's value. The value is not read directly (T-04).")
n04 = reorder(n04, "how_shown", "assumption",
              "The elimination assumes the same environment in every start: the same bound executable, supervisor and "
              "declared environment, the same user (UID 501, the 0x1F5 of HOST's value) and an unchanged "
              "<home>/.CFUserTextEncoding (" + CF_FILE + ", 7 bytes, " + CF_SHA[:8] + "..., 0o400, one link). D02 "
              "checks the file before C17, C17.X after C17 and before C19 (its content), and Q04 after S7 (FR-12).")

totals = deepcopy(F1["totals"])
rnb = totals["recorded_not_bounded"]
rnb["python_launchers"] = sum(1 for row in commands if row["phase"] != "capture" and
                              any(item.endswith("/.venv/bin/python") for item in row["argv"]))
rnb["p00_shasum"] = 1
rnb["shell_and_env_launchers"] = ("one /bin/sh (the wrapper) and one /usr/bin/env per command (" + str(len(order)) +
                                  " commands); the prepare script's mkdir and cp; the wrapper's own jq, shasum, perl, "
                                  "date, sysctl, cut and stat; P00's shasum (/usr/bin/perl)")
rnb["director_side"] = launch["starts"]
totals["capture_commands_only_on_failure"] = {
    "probes": sum(1 for row in capture_rows if ".O" in row["id"]), "stops": sum(1 for row in capture_rows if ".S" in row["id"]),
    "rule": "each is one Python launcher start, made only after an overrun (probes) or for FC-P6 (stops); none runs in "
            "a completed S7; none starts Node"}
totals["changed_from_freeze_001"] = {
    "node": False, "other": False, "s7_bounded": totals["s7_bounded"]["node"], "mh": {"node": 9, "other": 2},
    "note": "the Node and other starts are unchanged: S7 8 and 1, MH 9 and 2 (MH-PLAN's table 8 and 2, plus MC30-probe); "
            "an FC-P6 stop in C17 followed by the remaining CPU starts stays within C17's three"}
if [r for r in totals["rows"] if r["row"] == "Expected for MH"][0] != {"row": "Expected for MH", "node": 9, "other": 2}:
    raise SystemExit("unexpected MH totals in freeze 001")

failure_capture = deepcopy(F1["failure_capture"])
failure_capture["per_command"] += (" Since freeze 002 the .L's and the .P's predicates are evaluated by the main "
                                   "command's .X (FR-02).")
failure_capture["stops"] = ("FC-P6 is frozen per candidate pair as <ID>.S<k> (C16, C17, C19), each with its argv and "
                            "absent output, each run at most once; the overrun probes as <ID>.O<digits>; see 'overrun'")

tools = deepcopy(F1["tools"])
tools["new_in_this_freeze"] = [
    "launch.timer_template, as each command's timer_shell: the bound timer (FR-01 (b)); shell builtins, /bin/date and "
    "/bin/sleep only; writes nothing; inline text bound with the freeze",
    "overrun.select_shell of C16, C17 and C19: the selection of the recorded start pairs (FR-01 (c)); shell builtins "
    "only; writes nothing",
    P00_LIST_REL + ": P00's second list (FR-07)",
    "rebound unchanged from freeze 001: s7/w2f_s7_check.py (the Director's checker; stdlib, starts nothing, writes "
    "nothing, refuses a start without -I -S -B) and s7/prepare-s7-001.sh (the frozen preparation)"]

answered_001 = []
answers = {"Q1": "Confirmed (review 001, answer 5; disposition 001's correction_recorded)",
           "Q2": "Accepted: exactness is right", "Q3": "Accepted", "Q4": "Accepted, with FR-09's limit (limits)",
           "Q5": "Accepted", "Q6": "Accepted (answer 7); freeze 002 binds the MC11 list directly, so three kinds of "
           "deferred argument remain: FREEZE-002.json's SHA-256 and C14's two discovery digests",
           "Q7": "Accepted: PLAN is the right class", "Q8": "Accepted", "Q9": "Accepted", "Q10": "Accepted",
           "Q11": "Accepted"}
for row in F1["open_questions"]:
    answered_001.append({"id": row["id"], "text": row["text"], "answer": answers[row["id"]]})
open_questions = [
    {"id": "Q2-1", "text": "Overrun step 5 adds the command's .P after the wrapper exits (stated addition A-1): "
     "FAILURE-CAPTURE section 6 step 4 asks for a probe of every recorded start, and section 8's capture record for each "
     "one's probe; FR-04 (d) lets C17 record starts after the overrun probe. The reviewer should confirm that this "
     "stays within disposition 001's step 5."},
    {"id": "Q2-2", "text": "P00 adds --strict to '-a 256 -c' (stated addition A-2): without it this shasum skips a "
     "malformed line silently, so a damaged digest field would leave its file unchecked with exit 0."},
    {"id": "Q2-3", "text": "Step 6's 'never exits' is made operational by a second run of the command's own timer "
     "from the overrun (stated addition A-3)."},
    {"id": "Q2-4", "text": "The timer is inline text per command, not a file, so it is bound with the freeze and runs "
     "before P00 without an unverified file; its digest is the freeze's. It counts strictly more than outer_bound_s "
     "seconds (-gt on whole epoch seconds) and polls once a second."},
    {"id": "Q2-5", "text": "Every non-empty set of candidate pairs has its frozen probe command (7 for C16 and C17, 3 "
     "for C19), although the runner can record only the sets 1, 12 and 123; the extra commands keep the selection total."},
    {"id": "Q2-6", "text": "P00's second list holds freeze 001's lines with absolute paths, in the freeze 002 directory, "
     "and the first list covers it; one wrapper call, cwd the freeze 002 directory, PATH-only environment (Perl reads "
     "no locale)."},
    {"id": "Q2-7", "text": "FR-12's gap: mode, link count and user of the CF file are not expressible in an expect "
     "predicate; only its content is checked between C17 and C19."},
    {"id": "Q2-8", "text": "The trees checked for bytecode and .DS_Store gain the freeze 002 directory (stated addition "
     "A-4); the W3 directory that holds the bound MC11 list is not a tree root."}]

doc = {}
for key, value in F1.items():
    doc[key] = deepcopy(value)
    if key == "status":
        doc["revision_of"] = revision_of
        doc["attempt_paths"] = ("Attempt s7-001's paths are kept from freeze 001 (revision rule 4): none exists, and "
                                "nothing of S7 has run. Freeze 002 adds only P00's records and the capture commands' "
                                "records and outputs.")
    if key == "wrapper":
        doc["launch"] = launch
doc.update(id="FREEZE-002",
           status="FROZEN_NOT_RUN: awaiting freeze review 002; nothing of it has run",
           author="W2, a Claude Code subagent in a fresh context with the session's model, the independent author of "
                  "freeze 001 and of this revision under disposition 001 of freeze review 001; it wrote none of the "
                  "tooling, the observation plan, the observer, the provider, the probe, the contract, the amendment or "
                  "MP's preparation")
doc["places"]["freeze"] = OUT2
doc["places"]["freeze_001"] = OUT1
doc["places"]["review_001"] = W3F
doc["trees"].append({"root": OUT2})
doc["bindings"] = bindings
doc["deferred_inputs"] = []
doc["deferred_arguments"] = DEFERRED2
doc["preconditions"]["conditions"][0] = ("freeze review 002 accepted this freeze without a mandatory finding (A6), and "
                                         "its record gives FREEZE-002.json's SHA-256")
doc["preconditions"]["conditions"].insert(1, "every file of freeze 002 and every document it rebinds from freeze 001 "
                                             "unchanged (P00)")
doc["preconditions"]["commands"] = ["P00"] + doc["preconditions"]["commands"]
doc["preparation"]["verification"] = doc["preparation"]["verification"].replace("P01 to D01's predicates",
                                                                                "P00 to D01's predicates")
doc["absent_paths"] = {"before_preparation": sorted(before_prep), "after_preparation": sorted(after_prep)}
doc["order"] = order
doc["commands"] = commands
doc["capture_commands"] = [row["id"] for row in capture_rows]
doc["totals"], doc["failure_capture"], doc["carried_findings"] = totals, failure_capture, carried
doc["decisions"], doc["n04"], doc["limits"], doc["tools"] = decisions, n04, limits, tools
doc["open_questions"], doc["answered_questions_001"] = open_questions, answered_001
new_doc = {}
for key, value in doc.items():
    new_doc[key] = value
    if key == "stop_rules":
        new_doc["overrun"] = overrun
new_doc["stop_rules"] = stop_rules
doc = new_doc
if "P01 to D01's predicates" in doc["preparation"]["verification"]:
    raise SystemExit("verification text not updated")
data = (json.dumps(doc, indent=1, ensure_ascii=True, allow_nan=False) + "\n").encode("ascii")
f2 = write_new(F2_PATH, data)

# -----------------------------------------------------------------------------------------------------------
# The difference record: each change, with the finding or rule that requires it, and a mechanical comparison
# -----------------------------------------------------------------------------------------------------------
F2 = json.loads(data)
cmp_commands = []
for row in F2["commands"]:
    old = F1_ROWS.get(row["id"])
    if old is None:
        cmp_commands.append({"id": row["id"], "change": "added", "phase": row["phase"]})
        continue
    fields = sorted(k for k in set(row) | set(old) if row.get(k) != old.get(k))
    entry = {"id": row["id"], "changed_fields": fields}
    if "argv" in fields:
        entry["argv_indices_changed"] = changed_argv[row["id"]]
    if "expect" in fields:
        old_rules = wrapper_rules(old["name"], old["cwd"], old["environment"]["sha256"], old["argv"], DEFERRED1)[1]
        same_prefix = row["expect"][:len(old["expect"])] == old["expect"]
        entry["expect"] = {"freeze_001": len(old["expect"]), "freeze_002": len(row["expect"]),
                           "freeze_001_rules_kept_in_order": same_prefix,
                           "appended": added.get(row["id"], []),
                           "wrapper_rules_rebuilt": "argv" in fields and not same_prefix,
                           "old_wrapper_rule_count": len(old_rules)}
    if fields != ["timer_shell"]:
        cmp_commands.append(entry)
unchanged_but_timer = [row["id"] for row in F2["commands"] if row["id"] in F1_ROWS and
                       sorted(k for k in set(row) | set(F1_ROWS[row["id"]])
                              if row.get(k) != F1_ROWS[row["id"]].get(k)) == ["timer_shell"]]
top_changed = sorted(k for k in set(F1) & set(F2) if F1[k] != F2[k])
top_added = sorted(set(F2) - set(F1))
top_removed = sorted(set(F1) - set(F2))
changes = [
    {"id": "D-01", "finding": "FR-01 (a), (b)", "what": "'launch' (new): the background launch of the shell member "
     "alone, one call per command, never retried; each command's 'timer_shell' (new member, from "
     "launch.timer_template); stop rules 2 and 3", "where": ["/launch", "/commands/*/timer_shell", "/stop_rules/1",
                                                              "/stop_rules/2"]},
    {"id": "D-02", "finding": "FR-01 (c), (d)", "what": "'overrun' (new) replaces stop rule 9 with the six steps; "
     "candidates and selection rule; C16, C17 and C19 gain an 'overrun' member (candidates, select_shell, the IDs of "
     "their probes and stops); 25 capture commands (17 probes, 8 stops), phase 'capture', each with argv and absent "
     "outputs; 'capture_commands' lists them", "where": ["/overrun", "/stop_rules/9", "/commands/C16|C17|C19/overrun",
                                                         "/capture_commands", "/commands (phase capture)"]},
    {"id": "D-03", "finding": "FR-02", "what": "every main command C01 to C19 appends its .L's expect and, for C16, C17 "
     "and C19, its .P's expect, in full, to its own expect; stop rule 4; one classification row each",
     "where": ["/commands/C*/expect", "/commands/C*/classification", "/stop_rules/3"]},
    {"id": "D-04", "finding": "FR-03", "what": "C17's expect: each process event subprocess.Popen, each argv[0] one of "
     "the bound Node and the bound Git; C06's and C07's: each subprocess.Popen, each argv[0] the bound Git; one "
     "classification row each", "where": ["/commands/C06|C07|C17/expect", "/commands/C06|C07|C17/classification"]},
    {"id": "D-05", "finding": "FR-04", "what": "stop rule 6: C17's trio is one indivisible row; C17's classification",
     "where": ["/stop_rules/5", "/commands/C17/classification"]},
    {"id": "D-06", "finding": "FR-05", "what": "the author's notes use 25 directories, 18 files and 43 entries; nothing "
     "in the freeze's JSON or the preparation changes", "where": ["FREEZE-AUTHOR-NOTES-002.md"]},
    {"id": "D-07", "finding": "FR-06", "what": "classification rows: C02 (state_equals_host false is IMPLEMENTATION; a "
     "boot change HOST), C03 to C05 (SOURCE or PYTHON is PLAN or IMPLEMENTATION), C12 and C13 (a difference that "
     "exporting C causes is PLAN), C17 (another bootstrap refusal of a positive case is IMPLEMENTATION; an EVIDENCE "
     "refusal at setUpClass is PLAN), C19 (MC30-probe refusing after the environment check with another message is "
     "PLAN; MC36 NOT_RUN)", "where": ["/commands/C02|C03|C04|C05|C12|C13|C17|C19/classification"]},
    {"id": "D-08", "finding": "FR-07", "what": "P00 (new, first in 'order', phase precondition): /usr/bin/shasum -a 256 "
     "--strict -c on freeze 002's SHA256SUMS.txt and on P00's second list (new document " + P00_LIST_REL + ", bound); "
     "stop rule 1; preconditions; D02's re-evaluation covers it; its records are not in before_preparation, as P01's",
     "where": ["/commands/P00", "/order/0", "/stop_rules/0", "/preconditions", "/preparation/verification",
               "/bindings (freeze002:...)"]},
    {"id": "D-09", "finding": "FR-09", "what": "limits.this_freeze: the default temporary-cohort path is not exercised",
     "where": ["/limits/this_freeze"]},
    {"id": "D-10", "finding": "FR-12", "what": "n04.assumption (new) names the user and the CF file; C17's expect "
     "checks the CF file's SHA-256; the gap is stated in limits.this_freeze; one classification row",
     "where": ["/n04/assumption", "/n04/how_shown/2", "/commands/C17/expect", "/limits/this_freeze"]},
    {"id": "D-11", "finding": "disposition 001 (mc11_reviewed_list); revision rule 6", "what": "the MC11 reviewed list "
     "is bound directly (bindings 'review001:MC11-REVIEWED-LIST-001.json'); deferred_inputs is empty; C01's argv holds "
     "its digest in place of the placeholder, so C01's wrapper predicates are rebuilt and its equals_sha256_of rule "
     "goes; decisions item 7", "where": ["/bindings", "/deferred_inputs", "/deferred_arguments", "/commands/C01",
                                          "/decisions/6"]},
    {"id": "D-12", "finding": "revision rules 2 and 6 (FREEZE-002.json's digest deferred)", "what": "the checker's "
     "--freeze and --freeze-sha256 arguments of P01, D02, Q04 and every .X name FREEZE-002.json and the placeholder '" +
     NEW_PH + "'; their wrapper predicates are rebuilt; deferred_arguments", "where": ["/commands/P01|D02|Q04|*.X"]},
    {"id": "D-13", "finding": "revision rules 3 and 4", "what": "every unchanged document is rebound at its "
     "W2-freeze-001 path with its digest (the 120 bindings of freeze 001, unchanged); attempt s7-001's paths are kept "
     "(attempt_paths); revision_of, places, status, id, author", "where": ["/revision_of", "/attempt_paths",
                                                                          "/places", "/status", "/id", "/author"]},
    {"id": "D-14", "finding": "the reviews' records", "what": "carried_findings gains FR-01 to FR-12; decisions gain "
     "items 12 to 15; open_questions are freeze 002's; freeze 001's questions move to answered_questions_001 with "
     "review 001's answers; tools.new_in_this_freeze; totals (P00, the capture commands, the Director's starts; Node and "
     "other unchanged); failure_capture notes", "where": ["/carried_findings", "/decisions", "/open_questions",
                                                          "/answered_questions_001", "/tools", "/totals",
                                                          "/failure_capture"]}]
stated_additions = [
    {"id": "A-1", "rule": "overrun step 5", "change": "after the wrapper exits, the command's .P runs too (with FC-P6 "
     "for an established target whose stop has not run), besides the .L of section 6 step 5", "reason": "FR-04 (d) lets "
     "C17 record starts after the overrun probe; FAILURE-CAPTURE section 6 step 4 asks for a probe of every recorded "
     "start, and section 8's capture record for each one's probe; the .P is already frozen and reviewed"},
    {"id": "A-2", "rule": "P00", "change": "--strict in shasum's argv", "reason": "this shasum (Perl, 6.02) skips an "
     "improperly formatted line without failing unless --strict is given, so a damaged digest field would leave its "
     "file unchecked with exit 0"},
    {"id": "A-3", "rule": "overrun steps 1 and 6", "change": "a second run of the command's own timer from the overrun "
     "decides when the owner is told that the wrapper has not exited", "reason": "step 6 needs an executable criterion "
     "for 'never exits'; the same frozen text, no new tool"},
    {"id": "A-4", "rule": "trees", "change": "the freeze 002 directory is a tree root (no .DS_Store)", "reason": "as "
     "freeze 001's own directory was: it now holds a bound input (P00's second list) and the freeze itself"},
    {"id": "A-5", "rule": "launch.after", "change": "a timer's 'no-clock' or other output is a PLAN deviation that stops "
     "S7 after the command's .L, .P and .X; a timer line after the command's task ended has no effect", "reason": "the "
     "timer is new tooling and the launch must say what each of its outputs means"},
    {"id": "A-6", "rule": "stop rule 12", "change": "Q01 to Q04 run only when every wrapper started has exited",
     "reason": "after an overrun whose wrapper never exits, the post checks would observe a command still running"},
    {"id": "A-7", "rule": "P00's expect", "change": "besides its exit, D02 checks P00's empty stderr, that stdout names "
     "FREEZE-002.json, the second list and the checker as OK, and holds no FAILED", "reason": "so that D02's "
     "re-evaluation shows both lists were read; the Director's decision before P01 still reads the exit file alone"}]
differences = {
    "schema": "ontokin.c271.p35-freeze-differences/1", "from": {"id": "FREEZE-001", "sha256": F1_SHA},
    "to": {"id": "FREEZE-002", "path": F2_PATH, "sha256": f2["sha256"], "size_bytes": f2["size_bytes"]},
    "rules": "disposition 001's dispositions and revision_rules; every other change in stated_additions, for freeze "
             "review 002",
    "changes": changes, "stated_additions": stated_additions,
    "mechanical": {
        "top_level": {"added": top_added, "changed": top_changed, "removed": top_removed},
        "commands": {"freeze_001": len(F1["commands"]), "freeze_002": len(F2["commands"]),
                     "added": [r["id"] for r in F2["commands"] if r["id"] not in F1_ROWS],
                     "only_timer_shell_added": unchanged_but_timer, "changed": cmp_commands},
        "bindings": {"freeze_001": len(F1["bindings"]), "freeze_002": len(F2["bindings"]),
                     "added": [r["id"] for r in F2["bindings"] if r["id"] not in {b["id"] for b in F1["bindings"]}],
                     "freeze_001_kept_unchanged": F2["bindings"][:len(F1["bindings"])] == F1["bindings"]},
        "absent_paths": {"before_preparation": [len(F1["absent_paths"]["before_preparation"]),
                                                len(F2["absent_paths"]["before_preparation"])],
                         "after_preparation": [len(F1["absent_paths"]["after_preparation"]),
                                               len(F2["absent_paths"]["after_preparation"])],
                         "added": len(capture_paths)},
        "argv_changed": changed_argv}}
diff_written = write_new(OUT2 + "/FREEZE-002-DIFFERENCES.json",
                         (json.dumps(differences, indent=1, ensure_ascii=True) + "\n").encode("ascii"))
build = {"freeze": f2, "differences": diff_written, "p00_list": p00_list, "rebound_documents": len(rebound),
         "commands": len(commands), "order": len(order), "capture_commands": len(capture_rows),
         "bindings": len(bindings), "absent": {k: len(v) for k, v in doc["absent_paths"].items()},
         "python_launchers_normal_flow": rnb["python_launchers"], "written": WRITTEN}
write_new(OUT2 + "/author/records/build-002.json", (json.dumps(build, indent=1, sort_keys=True) + "\n").encode("ascii"))
print(json.dumps({k: build[k] for k in ("commands", "order", "capture_commands", "bindings", "absent",
                                        "python_launchers_normal_flow", "rebound_documents")} |
                 {"freeze_sha256": f2["sha256"], "freeze_size": f2["size_bytes"]}, sort_keys=True))
