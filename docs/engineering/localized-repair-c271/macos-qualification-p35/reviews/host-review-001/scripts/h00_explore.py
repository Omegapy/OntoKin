"""HOST review 001, script h00: structure of the frozen inputs, for reading only.

Run as: <worktree>/.venv/bin/python -I -S -B h00_explore.py --local L --worktree W --output OUT
Starts nothing (an audit hook refuses every process-creation event), imports nothing of the project,
and writes only its one absent output file (O_EXCL). Holds no machine path: every path is an argument.
"""
import argparse
import json
import os
import sys


def refuse_starts(event, args):
    if event in ("subprocess.Popen", "os.posix_spawn", "os.exec", "os.fork", "os.forkpty", "os.spawn",
                 "os.system", "os.startfile"):
        raise RuntimeError("process creation refused by the review's audit hook: " + event)


sys.addaudithook(refuse_starts)


def load(path):
    with open(path, "rb") as stream:
        return json.loads(stream.read().decode("utf-8"))


def sample(mapping, count=3):
    return {key: mapping[key] for key in sorted(mapping)[:count]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--local", required=True)
    parser.add_argument("--worktree", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    out = {"pid": os.getpid(), "ppid": os.getppid(), "executable": sys.executable,
           "flags": {"isolated": sys.flags.isolated, "no_site": sys.flags.no_site,
                     "dont_write_bytecode": sys.flags.dont_write_bytecode}}
    w2 = args.local + "/c271-p35/workers/W2-plan-001"
    py = load(w2 + "/python-inventory-001.json")
    out["python_inventory"] = {
        "top": sorted(py), "schema": py.get("schema"),
        "framework_root": py["framework"]["root"], "framework_entries": len(py["framework"]["entries"]),
        "venv_root": py["venv"]["root"], "venv_entries": len(py["venv"]["entries"]),
        "kinds": {tree: {kind: sum(1 for e in py[tree]["entries"].values() if e["kind"] == kind)
                         for kind in ("file", "symlink", "directory")} for tree in ("framework", "venv")},
        "framework_sample": sample(py["framework"]["entries"]),
        "symlinks": {tree: {k: v for k, v in py[tree]["entries"].items() if v["kind"] == "symlink"}
                     for tree in ("framework", "venv")},
        "selection_keys": sorted(py["selection"]), "closure_keys": sorted(py["closure"]),
        "images": len(py["closure"]["images"]), "external": py["closure"]["external"],
        "links": py["closure"]["links"],
    }
    images = py["closure"]["images"]
    first = sorted(images)[0]
    out["python_inventory"]["image_sample"] = {first: images[first]}
    out["python_inventory"]["image_keys"] = sorted({k for v in images.values() for k in v})
    with_spellings = {k: v.get("spellings") for k, v in images.items() if "spellings" in v}
    out["python_inventory"]["spellings"] = with_spellings
    ext = {k: v for k, v in images.items() if v["tree"] == "external"}
    out["python_inventory"]["external_images"] = ext
    pil = sorted(k for k in images if "/PIL/" in k)
    out["python_inventory"]["pil_sample"] = {k: images[k] for k in pil[:2]}
    src = load(w2 + "/source-inventory-001.json")
    out["source_inventory"] = {"top": sorted(src), "schema": src.get("schema"), "files": len(src["files"]),
                               "sample": sample(src["files"])}
    dep = load(w2 + "/dependencies-inventory-001.json")
    out["dependencies_inventory"] = {"top": sorted(dep), "schema": dep.get("schema"), "files": len(dep["files"]),
                                     "directories": dep["directories"], "archive": dep["archive"],
                                     "sample": sample(dep["files"])}
    p34 = args.local + "/c271-p34"
    for name in ("receipts/node-install-result.json", "receipts/reader-install-result.json"):
        doc = load(p34 + "/" + name)
        out[name] = {"top": sorted(doc), "state": doc.get("state"), "passed": doc.get("passed"),
                     "purpose": doc.get("purpose"), "labels": doc.get("labels"), "pins": doc.get("pins"),
                     "execution_counts": doc.get("execution_counts"), "publication": doc.get("publication")}
    for name in ("plans/node-install-plan.json", "plans/reader-install-plan.json"):
        doc = load(p34 + "/" + name)
        out[name] = {"top": sorted(doc), "purpose": doc.get("purpose"), "destination": doc.get("destination"),
                     "report": doc.get("report"), "root_mode": doc.get("root_mode"),
                     "archive": doc.get("archive"), "source_root": doc.get("source_root"),
                     "files": doc.get("files") if len(json.dumps(doc.get("files"))) < 4000 else "large",
                     "directories": doc.get("directories")}
    # The clone's object store, to decide how commit C can be read without Git.
    with open(args.worktree + "/.git", "rb") as stream:
        gitdir = stream.read().decode().strip()[len("gitdir: "):]
    with open(gitdir + "/commondir", "rb") as stream:
        common = os.path.normpath(gitdir + "/" + stream.read().decode().strip())
    objects = common + "/objects"
    loose = os.path.join(objects, "0e", "b9a5517f4e19705178a2c59b8d8d33fb87867a")
    packs = sorted(name for name in os.listdir(objects + "/pack"))
    out["git_objects"] = {"commit_loose": os.path.lexists(loose), "pack_files": packs,
                          "index_mtime_ns": os.lstat(gitdir + "/index").st_mtime_ns,
                          "has_packed_refs": os.path.lexists(common + "/packed-refs")}
    raw = json.dumps(out, sort_keys=True, indent=1).encode("utf-8")
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        os.write(fd, raw)
        os.fsync(fd)
    finally:
        os.close(fd)


if __name__ == "__main__":
    main()
