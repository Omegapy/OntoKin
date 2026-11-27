"""Focused tests of scan_mc11.py on a synthetic 24-file reader tree; children: the interpreter with -I -S -B."""
from __future__ import annotations

import contextlib
import io
import json
import os
from pathlib import Path
import sys
import unittest
from unittest import mock

import mh_support as S

BAD = r"""import { first,
  second } from './helper.js';
const cp = require('child_process');
const hidden = '\x63hild_process';
const joined = 'child_' + 'process';
const w = new Worker(url);
process.binding('spawn_sync');
process.dlopen(module, path);
const m = require(name);
const n = await import(spec);
eval('1');
const f = new Function('return 1');
const r = /x/.exec(s);
spawn('ls');
// cluster in a comment
export * from '../missing.js';
const t = `a ${ `b` } c` + typeof evaluate;
"""
# TR-11: the forms that the first scanner missed.
FORMS = r"""const a = cp['spawn'](x);
const b = (0, cp.execFile)(y);
self.require = require;
const v = (typeof __non_webpack_require__ === 'function' ? __non_webpack_require__ : require)("url");
process.binding('process_wrap');
const h = '\x73pawn_sync';
const d = require('mo' + 'dule');
const require = createRequire(import.meta.url);
"""
CLEAN = """import { helper } from './helper.js';
const value = /[a-z]+/.exec(text);
function getRenderFunction() { return null; }
export { value };
"""
# A name the wider scan finds and MI's frozen rule does not list.
WIDER_ONLY = """const wrap = 'process_wrap';
export { wrap };
"""
LOADER = """import {pathToFileURL} from 'node:url';
export async function resolve(specifier, context, nextResolve) { return nextResolve(specifier, context); }
"""


class ScanWorld:
    def __init__(self, test, files):
        self.base = S.resolved_temp(test)
        self.root = self.base + "/readers"
        contents = {"tools/three_loader.mjs": LOADER, "lib/helper.js": "export const helper = 1;\n"}
        contents.update(files)
        for index in range(24 - len(contents)):
            contents["lib/filler-%02d.js" % index] = "export const filler%d = %d;\n" % (index, index)
        for rel, text in contents.items():
            S.write(self.root + "/" + rel, text)
        self.files = sorted(contents)
        self.probe = S.write(self.base + "/source/probe.mjs",
                             "import fs from 'node:fs';\nconst validator = require(manifest.validator_entry);\n")
        self.write_inventory()

    def write_inventory(self, files=None):
        files = self.files if files is None else files
        inventory = {"schema": "ontokin.current-host-readback-dependencies/0.2.0",
                     "files": {rel: S.binding(self.root + "/" + rel) for rel in files}, "directories": {},
                     "archive": {"path": "/synthetic", "sha256": "e" * 63 + "f", "size_bytes": 1, "mode": "0o644"}}
        self.inventory = S.write(self.base + "/inventory-%d.json" % len(os.listdir(self.base)),
                                 json.dumps(inventory).encode())

    def arguments(self, output, *, reviewed=None, probe_digest=None):
        args = ["--probe", self.probe, "--probe-sha256", probe_digest or S.sha256_file(self.probe),
                "--dependencies-root", self.root, "--dependencies-inventory", self.inventory,
                "--dependencies-inventory-sha256", S.sha256_file(self.inventory), "--output", output]
        if reviewed is not None:
            args += ["--reviewed", reviewed, "--reviewed-sha256", S.sha256_file(reviewed)]
        return args

    def scan(self, **kwargs):
        output = self.base + "/scan-%d.json" % len(os.listdir(self.base))
        completed = S.run_tool("scan_mc11.py", *self.arguments(output, **kwargs), flags=("-I", "-S", "-B"))
        return completed, S.read_json(output)


def reviewed_from(record, path, drop=None, *, status="REVIEWED", reviewer="a synthetic reviewer of this test"):
    files = {}
    for key, entry in record["files"].items():
        files[key] = {"process_call_names": [[r["pattern"], r["line"], r["column"]] for r in entry["process_call_names"]],
                      "dynamic": [[r["pattern"], r["line"], r["column"]] for r in entry["dynamic"]],
                      "specifiers": [r["specifier"] for r in entry["specifiers"]],
                      "frozen_rule": {"dynamic": entry["frozen_rule"]["found"]["dynamic"],
                                      "static_specifiers": entry["frozen_rule"]["found"]["static_specifiers"]}}
    if drop is not None:
        files[drop]["dynamic"].pop()
    document = {"schema": "ontokin.c271.p35-mc11-reviewed/2", "status": status, "files": files}
    if reviewer is not None:
        document["reviewer"] = reviewer
    return S.write(path, json.dumps(document).encode())


def patterns(entry, key):
    return sorted((row["pattern"], row["line"], row.get("view", "raw")) for row in entry[key])


class ScanTests(unittest.TestCase):
    def test_every_pattern_is_found_with_its_line_and_view(self):
        world = ScanWorld(self, {"lib/bad.js": BAD})
        completed, record = world.scan()
        self.assertEqual(completed.returncode, 1)
        self.assertFalse(record["none_found"])
        bad = record["files"]["lib/bad.js"]
        self.assertEqual(patterns(bad, "process_creation"),
                         [("Worker", 6, "raw"), ("child_process", 3, "raw"), ("child_process", 4, "decoded"),
                          ("child_process", 5, "joined"), ("cluster", 15, "raw"), ("dlopen", 8, "raw"),
                          ("process.binding", 7, "raw"), ("spawn_sync", 7, "raw")])
        self.assertEqual([row["context"] for row in bad["process_creation"] if row["pattern"] == "cluster"], ["comment"])
        calls = sorted((row["pattern"], row["line"], row["method_call"]) for row in bad["process_call_names"])
        self.assertEqual(calls, [("exec", 13, True), ("spawn", 14, False)])
        dynamic = sorted((row["pattern"], row["line"], row.get("classification")) for row in bad["dynamic"])
        self.assertIn(("require-computed", 9, None), dynamic)
        self.assertIn(("import-computed", 10, None), dynamic)
        self.assertIn(("eval", 11, "word"), dynamic)
        self.assertIn(("eval", 17, "identifier-substring"), dynamic)
        self.assertIn(("Function", 12, "constructor-call"), dynamic)
        specifiers = {(row["specifier"], row["line"]): row["resolution"] for row in bad["specifiers"]}
        self.assertEqual(specifiers[("./helper.js", 2)], "reader-file:lib/helper.js")
        self.assertEqual(specifiers[("child_process", 3)], "bare")
        self.assertEqual(specifiers[("../missing.js", 16)], "unresolved:missing.js")
        self.assertEqual(record["unresolved_relative_specifiers"], ["unresolved:missing.js"])
        self.assertEqual(record["files"]["tools/three_loader.mjs"]["role"], "module loader")
        self.assertEqual(record["files"]["<probe>"]["role"], "probe")
        self.assertIn("cannot exclude every dynamic route", record["limit"])

    def test_the_forms_of_review_001_are_found_on_every_view(self):
        """TR-11: binding names, bracket and parenthesized forms, every require that is not a plain call."""
        world = ScanWorld(self, {"lib/forms.js": FORMS})
        completed, record = world.scan()
        self.assertEqual(completed.returncode, 1)
        forms = record["files"]["lib/forms.js"]
        self.assertEqual(patterns(forms, "process_creation"),
                         [("process.binding", 5, "raw"), ("process_wrap", 5, "raw"), ("spawn_sync", 6, "decoded")])
        calls = [(row["pattern"], row["line"], row["parenthesized"]) for row in forms["process_call_names"]]
        self.assertEqual(calls, [("execFile", 2, True)])
        dynamic = patterns(forms, "dynamic")
        for item in (("bracket-access", 1, "raw"), ("require-reference", 3, "raw"), ("require-reference", 4, "raw"),
                     ("non-webpack-require", 4, "raw"), ("require-computed", 7, "raw"),
                     ("require-literal", 7, "joined"), ("createRequire", 8, "raw")):
            self.assertIn(item, dynamic)
        self.assertEqual(len([row for row in forms["dynamic"] if row["pattern"] == "require-reference"]), 3,
                         "self.require, = require and the parenthesized callee; not the declaration on line 8")
        self.assertEqual([(row["pattern"], row["specifier"]) for row in forms["specifiers"]
                          if row["pattern"] == "require-parenthesized"], [("require-parenthesized", "url")])

    def test_a_clean_tree_with_its_reviewed_list_is_none_found(self):
        world = ScanWorld(self, {"lib/clean.js": CLEAN})
        completed, record = world.scan()
        self.assertEqual(completed.returncode, 1, "without a reviewed list, the dynamic constructs await review")
        self.assertTrue(record["none_found"])
        self.assertFalse(record["frozen_rule"]["passed"], "the frozen rule needs the reviewed list too")
        reviewed = reviewed_from(record, world.base + "/reviewed.json")
        completed, record = world.scan(reviewed=reviewed)
        self.assertEqual(completed.returncode, 0, completed.stderr.decode())
        self.assertTrue(record["reviewed_list_matches"])
        self.assertTrue(record["frozen_rule"]["passed"])
        self.assertEqual(record["inputs"]["reviewed"]["reviewer"], "a synthetic reviewer of this test")
        incomplete = reviewed_from(record, world.base + "/reviewed-2.json", drop="<probe>")
        completed, record = world.scan(reviewed=incomplete)
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(record["files"]["<probe>"]["review"]["dynamic"]["unreviewed"], [["require-computed", 2, 19]])

    def test_the_frozen_rules_verdict_is_reported_separately(self):
        """TR-12: MC11 is decided by MI's frozen rule; the wider scan is reported beside it."""
        world = ScanWorld(self, {"lib/clean.js": CLEAN, "lib/wider.js": WIDER_ONLY})
        _, record = world.scan()
        completed, record = world.scan(reviewed=reviewed_from(record, world.base + "/reviewed.json"))
        self.assertEqual(completed.returncode, 1)
        self.assertTrue(record["frozen_rule"]["passed"])
        self.assertTrue(record["frozen_rule"]["decides_mc11"])
        self.assertFalse(record["wider_scan"]["none_found"])
        self.assertEqual(patterns(record["files"]["lib/wider.js"], "process_creation"), [("process_wrap", 1, "raw")])
        world = ScanWorld(self, {"lib/bad.js": BAD})
        _, record = world.scan()
        frozen = record["files"]["lib/bad.js"]["frozen_rule"]
        self.assertEqual(sorted(kind for kind, _ in frozen["found"]["process_creation"]),
                         ["child_process", "cluster", "process.dlopen"])
        self.assertFalse(frozen["verdict"]["process_creation_none"])
        self.assertFalse(record["frozen_rule"]["process_creation_none"])
        self.assertEqual(frozen["found"]["static_specifiers"], ["child_process", "../missing.js"],
                         "the frozen rule lists one-line specifiers only: not the import of lines 1 and 2")

    def test_a_list_that_is_not_reviewed_or_names_no_reviewer_refuses(self):
        """TR-12: an unreviewed candidate list cannot decide MC11."""
        world = ScanWorld(self, {"lib/clean.js": CLEAN})
        _, record = world.scan()
        for name, kwargs in (("candidate", {"status": "CANDIDATE, NOT REVIEWED"}), ("no reviewer", {"reviewer": None}),
                             ("empty reviewer", {"reviewer": " "})):
            with self.subTest(name):
                listed = reviewed_from(record, world.base + "/reviewed-%s.json" % name.replace(" ", "-"), **kwargs)
                completed, refused = world.scan(reviewed=listed)
                self.assertEqual(completed.returncode, 2)
                self.assertEqual(refused["refusal"]["rule"], "REVIEWED")

    def test_the_tree_and_the_bindings_are_checked_before_any_scan(self):
        world = ScanWorld(self, {"lib/clean.js": CLEAN})
        completed, record = world.scan(probe_digest="0" * 63 + "1")
        self.assertEqual((completed.returncode, record["refusal"]["rule"]), (2, "DIGEST"))
        S.write(world.root + "/lib/.DS_Store", b"")
        completed, record = world.scan()
        self.assertEqual((completed.returncode, record["refusal"]["rule"]), (2, "TREE"))
        os.remove(world.root + "/lib/.DS_Store")
        os.symlink(world.root + "/lib/helper.js", world.root + "/lib/alias.js")
        completed, record = world.scan()
        self.assertEqual((completed.returncode, record["refusal"]["rule"]), (2, "TREE"))
        os.remove(world.root + "/lib/alias.js")
        Path(world.root + "/lib/clean.js").write_text(CLEAN + "// changed\n")
        completed, record = world.scan()
        self.assertEqual((completed.returncode, record["refusal"]["rule"]), (2, "TREE"))
        world.write_inventory(world.files[:-1])
        completed, record = world.scan()
        self.assertEqual((completed.returncode, record["refusal"]["rule"]), (2, "INVENTORY"))

    def test_a_start_without_dash_b_refuses(self):
        """TR-17, in this process with sys.flags as a start without -B shows them; nothing is started."""
        tool = S.load_module("mh_scan_under_test", str(S.TOOLING / "scan_mc11.py"))
        world = ScanWorld(self, {"lib/clean.js": CLEAN})
        output = world.base + "/scan-without-b.json"
        with mock.patch.object(sys, "flags", S.FlagsWithoutB()), contextlib.redirect_stderr(io.StringIO()):
            code = tool.main(world.arguments(output))
        self.assertEqual(code, 2)
        self.assertEqual(S.read_json(output)["refusal"]["rule"], "PYTHON")


if __name__ == "__main__":
    unittest.main()
