"""W3 (C271-P37 S7): candidate C's identity from Git's files, without starting Git.

Reads the commit, its parent and both trees from the object store; lists every changed path; checks
that the worktree's bytes of those paths equal C's blobs and gives their SHA-256; applies the
provided diff to the parent's blobs and requires C's blobs as the result; checks the worktree's
index against C's tree and the worktree's files against the index (stat data, then content); and
lists files that the index does not hold, outside .git and .venv. Writes one JSON file, with labels
in place of machine paths.

Usage: python3 -I -S -B s1_candidate_identity.py WORKTREE GIT_COMMON_DIR WORKTREE_GIT_DIR DIFF OUTPUT
"""
import hashlib
import json
import os
import re
import stat
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gitstore  # noqa: E402

C = "5a3502e22d0fa4b29fbff2c867f1aab8271c4235"
C_TREE = "9249fdeb2ea3b80ac7f05c1ee3a7f0ce4d88e580"
PARENT = "2f728998456c829f3cdc13bbf72d6dd805fefa36"
DIFF_SHA256 = "862baca6d22fe3e57bbd83965974ec7c9168ab01b93771fd0b3305fc947e2a29"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def parse_diff(text):
    """{path: {"new": bool, "deleted": bool, "index": (a, b), "hunks": [(old_start, old_len, new_start, new_len, lines)]}}"""
    files, current, hunk = {}, None, None
    for line in text.split("\n"):
        if line.startswith("diff --git "):
            match = re.fullmatch(r"diff --git a/(.+) b/(.+)", line)
            current = {"new": False, "deleted": False, "index": None, "hunks": [], "no_newline": []}
            files[match.group(2)] = current
            hunk = None
            continue
        if current is None:
            continue
        if hunk is None:
            if line.startswith("new file mode"):
                current["new"] = True
            elif line.startswith("deleted file mode"):
                current["deleted"] = True
            elif line.startswith("index "):
                current["index"] = tuple(line.split()[1].split(".."))
            elif line.startswith("@@ "):
                pass
            elif line.startswith(("--- ", "+++ ")):
                continue
        if line.startswith("@@ "):
            match = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", line)
            hunk = [int(match.group(1)), int(match.group(2) or 1), int(match.group(3)), int(match.group(4) or 1), []]
            current["hunks"].append(hunk)
            continue
        if hunk is not None:
            if line.startswith("\\ No newline"):
                current["no_newline"].append(len(hunk[4]))
                continue
            if line[:1] in (" ", "+", "-"):
                hunk[4].append(line)
            elif line == "":
                hunk[4].append(line)  # possible trailing empty split element; checked by the counts
    return files


def apply(old_text, record):
    old = old_text.split("\n") if old_text else []
    # A file ending with a newline splits into a last empty element; drop it and keep the flag.
    trailing = bool(old) and old[-1] == ""
    if trailing:
        old = old[:-1]
    out, cursor = [], 0
    for old_start, old_len, new_start, new_len, lines in record["hunks"]:
        start = old_start - 1 if old_len else old_start
        out.extend(old[cursor:start])
        cursor = start
        taken_old = taken_new = 0
        for line in lines:
            if taken_old == old_len and taken_new == new_len:
                break
            tag, body = line[:1], line[1:]
            if tag == " ":
                if old[cursor] != body:
                    raise ValueError("context differs")
                out.append(body)
                cursor += 1
                taken_old += 1
                taken_new += 1
            elif tag == "-":
                if old[cursor] != body:
                    raise ValueError("removed line differs")
                cursor += 1
                taken_old += 1
            elif tag == "+":
                out.append(body)
                taken_new += 1
        if (taken_old, taken_new) != (old_len, new_len):
            raise ValueError("hunk counts differ")
    out.extend(old[cursor:])
    return "\n".join(out) + ("\n" if out else "")


def main(worktree, common, worktree_git, diff_path, output):
    store = gitstore.Store(os.path.join(common, "objects"))
    result = {"schema": "w3.c271-p37.candidate-identity/1", "labels": {"<worktree>": "the C271 worktree"}}
    with open(os.path.join(worktree_git, "HEAD"), "rb") as stream:
        head_ref = stream.read().decode().strip()
    ref = head_ref.removeprefix("ref: ")
    ref_path = os.path.join(common, ref)
    head = open(ref_path).read().strip() if os.path.exists(ref_path) else None
    result["head"] = {"ref": ref, "oid": head, "is_C": head == C}
    commit = store.commit(C)
    parent = store.commit(PARENT)
    result["commit"] = {"tree": commit["tree"], "tree_is_expected": commit["tree"] == C_TREE,
                        "parents": commit["parents"], "parent_is_declaration": commit["parents"] == [PARENT],
                        "subject": commit["message_first_line"]}
    result["parent"] = {"tree": parent["tree"], "parents": parent["parents"], "subject": parent["message_first_line"]}
    changes = store.changed(parent["tree"], commit["tree"])
    rows = []
    for path, before, after in changes:
        row = {"path": path, "before": before, "after": after}
        if after and after[0] != "160000":
            kind, data = store.read(after[1])
            local = os.path.join(worktree, path)
            info = os.lstat(local)
            worktree_bytes = (os.readlink(local).encode() if stat.S_ISLNK(info.st_mode) else open(local, "rb").read())
            row.update(c_blob_sha256=sha256(data), c_blob_bytes=len(data),
                       worktree_sha256=sha256(worktree_bytes), worktree_equals_c=worktree_bytes == data,
                       worktree_mode=oct(stat.S_IMODE(info.st_mode)))
        rows.append(row)
    result["changed_paths"] = rows
    result["changed_count"] = len(rows)

    raw_diff = open(diff_path, "rb").read()
    result["diff"] = {"sha256": sha256(raw_diff), "sha256_is_expected": sha256(raw_diff) == DIFF_SHA256,
                      "bytes": len(raw_diff)}
    parsed = parse_diff(raw_diff.decode("utf-8"))
    changed_set = {row["path"] for row in rows}
    result["diff"]["paths"] = sorted(parsed)
    result["diff"]["paths_equal_tree_changes"] = set(parsed) == changed_set
    applied = {}
    for path, record in parsed.items():
        row = next(item for item in rows if item["path"] == path)
        before_text = store.read(row["before"][1])[1].decode("utf-8") if row["before"] else ""
        after_bytes = store.read(row["after"][1])[1]
        try:
            produced = apply(before_text, record)
            ok = produced.encode("utf-8") == after_bytes
            error = None
        except (ValueError, IndexError) as exc:
            ok, error = False, str(exc)
        abbreviations = record["index"]
        index_ok = (abbreviations is not None
                    and (row["before"] is None and set(abbreviations[0]) == {"0"} or row["before"] and row["before"][1].startswith(abbreviations[0]))
                    and row["after"][1].startswith(abbreviations[1]))
        applied[path] = {"new_file": record["new"], "hunks": len(record["hunks"]), "applies_to_parent_and_gives_C": ok,
                         "error": error, "index_line_matches_blobs": bool(index_ok)}
    result["diff"]["files"] = applied

    # The worktree's index against C's tree, and the worktree's files against the index.
    flat = store.flatten(commit["tree"])
    version, index = gitstore.read_index(os.path.join(worktree_git, "index"))
    index_rows = {path: (oct(entry["mode"])[2:], entry["oid"]) for path, entry in index.items()}
    tree_rows = {path: (mode, oid) for path, (mode, oid) in flat.items()}
    result["index"] = {"version": version, "entries": len(index), "tree_entries": len(flat),
                       "index_equals_C_tree": index_rows == tree_rows,
                       "only_in_index": sorted(set(index_rows) - set(tree_rows))[:20],
                       "only_in_tree": sorted(set(tree_rows) - set(index_rows))[:20],
                       "different": sorted(p for p in set(index_rows) & set(tree_rows) if index_rows[p] != tree_rows[p])[:20],
                       "stages_other_than_zero": sorted(p for p, e in index.items() if e["stage"])[:20],
                       "flags": sorted(p for p, e in index.items() if e["assume_valid"] or e["skip_worktree"] or e["intent_to_add"])[:20]}
    index_mtime = os.stat(os.path.join(worktree_git, "index")).st_mtime_ns
    hashed, dirty = 0, []
    for path, entry in index.items():
        local = os.path.join(worktree, path)
        try:
            info = os.lstat(local)
        except FileNotFoundError:
            dirty.append([path, "deleted"])
            continue
        mode = entry["mode"]
        if stat.S_ISLNK(info.st_mode) != (mode >> 12 == 0o12):
            dirty.append([path, "type"])
            continue
        if mode >> 12 == 0o10 and bool(info.st_mode & 0o100) != bool(mode & 0o100):
            dirty.append([path, "mode"])
            continue
        seconds, nanoseconds = entry["mtime"]
        same_stat = (seconds == int(info.st_mtime_ns // 10**9) & 0xFFFFFFFF
                     and nanoseconds in (0, info.st_mtime_ns % 10**9)
                     and entry["size"] == info.st_size & 0xFFFFFFFF and entry["ino"] == info.st_ino & 0xFFFFFFFF
                     and info.st_mtime_ns < index_mtime)
        if same_stat:
            continue
        hashed += 1
        data = os.readlink(local).encode() if stat.S_ISLNK(info.st_mode) else open(local, "rb").read()
        if gitstore.blob_id(data) != entry["oid"]:
            dirty.append([path, "content"])
    result["worktree_against_index"] = {"entries": len(index), "content_hashed_after_stat_mismatch": hashed,
                                        "differences": dirty}
    tracked = set(index)
    untracked, directories = [], 0
    for parent_dir, dirnames, filenames in os.walk(worktree):
        relative_dir = os.path.relpath(parent_dir, worktree)
        relative_dir = "" if relative_dir == "." else relative_dir + "/"
        if relative_dir == "":
            dirnames[:] = [d for d in dirnames if d not in (".git", ".venv")]
        directories += 1
        names = list(filenames) + [d for d in dirnames if os.path.islink(os.path.join(parent_dir, d))]
        for name in names:
            path = relative_dir + name
            if path == ".git":
                continue
            if path not in tracked:
                untracked.append(path)
    result["worktree_untracked_candidates"] = {"outside": [".git", ".venv"], "directories_walked": directories,
                                               "names": sorted(untracked)}
    bytecode = [path for path in untracked if path.endswith((".pyc", ".pyo")) or "/__pycache__/" in "/" + path]
    result["worktree_bytecode_outside_venv"] = bytecode
    with open(output, "x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, sort_keys=True)
        stream.write("\n")


if __name__ == "__main__":
    main(*sys.argv[1:6])
