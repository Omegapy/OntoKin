"""Independent C268 controls: exact historical admission and bounded file I/O.

Run directly with --evidence-dir NEW_DIRECTORY, or through unittest discovery.
Each direct run preserves checked code, exact input identities, unique changed
bytes, actual call outcomes, and all failures. It executes no source or exporter.
"""

from __future__ import annotations

import argparse
import copy
import errno
import hashlib
import io
import json
import os
import platform
import subprocess
import sys
import tempfile
import unittest
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import endpoint_control_fixtures as fixtures

reader = fixtures.load_module("c268_public_endpoint_reader", HERE / "endpoint_reader.py")
comparison = fixtures.load_module("c268_raw_c267_comparison", HERE.parent /
    "localized-repair-c267/hinge_compare.py", fixtures.DEPENDENCIES["localized-repair-c267/hinge_compare.py"])
source_reader = fixtures.load_module("c268_raw_c265_source", HERE.parent /
    "localized-repair-c265/source_hinges.py", fixtures.DEPENDENCIES["localized-repair-c265/source_hinges.py"])
artifact_reader = fixtures.load_module("c268_raw_c261_artifact", HERE.parent /
    "localized-repair-c261/hinge_glb.py", fixtures.DEPENDENCIES["localized-repair-c261/hinge_glb.py"])

CALLS, NOTES, INPUTS = [], [], {}
UNSET = object()
REAL_OPEN, REAL_CLOSE, REAL_READ, REAL_FSTAT, REAL_STAT = os.open, os.close, os.read, os.fstat, os.stat
FAULT_CODES = {"ENDPOINT", "INPUT_PATH", "INPUT_SIZE", "HISTORICAL_BINDING", "IO_ERROR",
               "INPUT_BINDING", "UNSUPPORTED_PLATFORM", "RESOURCE_LIMIT", "MALFORMED", "FIELD_MISMATCH",
               "UNSUPPORTED_SOURCE_FORM", "UNSUPPORTED_ARTIFACT_FORM"}


def record_bytes(raw, extension):
    value = {"bytes": len(raw), "sha256": fixtures.digest(raw)}
    for name, (size, digest) in fixtures.HISTORICAL.items():
        if (len(raw), value["sha256"]) == (size, digest):
            value["frozenReference"] = fixtures.PROOF + "/" + name
            return value
    name = value["sha256"] + extension
    INPUTS.setdefault(name, raw)
    value["snapshot"] = "inputs.zip!" + name
    return value


def witnesses(value):
    if isinstance(value, dict):
        if {"file", "sha256", "startByte", "endByteExclusive"} <= set(value):
            yield value
        for child in value.values():
            yield from witnesses(child)
    elif isinstance(value, list):
        for child in value:
            yield from witnesses(child)


def pointer(document, path):
    for token in path.lstrip("/").split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        document = document[int(token)] if isinstance(document, list) else document[token]
    return document


class EndpointReaderControls(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="c268-controls-")
        self.addCleanup(self.directory.cleanup)
        self.temporary = Path(self.directory.name)
        self.repo = self.temporary / "repo"
        self.original = fixtures.originals()
        self.proof = fixtures.install(self.repo, self.original)
        self.states = {name: record_bytes(raw, ".glb" if name.endswith(".glb") else ".ok")
                       for name, raw in self.original.items()}
        self.events = []

    def replace(self, name, raw):
        (self.proof / name).write_bytes(raw)
        self.states[name] = record_bytes(raw, ".glb" if name.endswith(".glb") else ".ok")

    def remove(self, name):
        (self.proof / name).unlink()
        self.states[name] = {"missing": True}

    def selected_inputs(self, endpoint):
        if type(endpoint) is not str or endpoint not in ("before", "after"):
            return {}
        return {name: copy.deepcopy(self.states[name]) for name in
                (endpoint + ".main.ok", "hinges.ok", endpoint + ".glb")}

    def reader_call(self, endpoint="before", *, label, repo=UNSET, module=reader, expected="admitted"):
        repo = self.repo if repo is UNSET else repo
        entry = {"case": self.id(), "api": "historical-reader", "label": label,
                 "expected": expected, "endpointType": type(endpoint).__name__,
                 "endpoint": endpoint[:100] if type(endpoint) is str else None,
                 "rootType": type(repo).__name__, "inputs": self.selected_inputs(endpoint),
                 "injectedEvents": self.events}
        CALLS.append(entry)
        try:
            value = module.read_bound_endpoint(repo, endpoint)
        except module.Fault as exc:
            entry.update(outcome="typed_refusal", code=exc.code, detail=exc.detail,
                         reason=getattr(exc, "reason", None), pointer=getattr(exc, "pointer", None),
                         sourceHashes=getattr(exc, "sourceHashes", None),
                         sourceBytes=getattr(exc, "sourceBytes", None),
                         artifactSha256=getattr(exc, "artifactSha256", None),
                         artifactBytes=getattr(exc, "artifactBytes", None))
            raise
        except Exception as exc:
            entry.update(outcome="untyped_exception", exception=type(exc).__name__, detail=str(exc))
            raise
        else:
            entry.update(outcome="admitted", hingeCount=value.get("hingeCount"), siteCount=value.get("siteCount"),
                         flags={k: v for k, v in value.items() if type(v) is bool})
            return value
        finally:
            entry["inputsAfterCall"] = self.selected_inputs(endpoint)
            self.events = []

    def raw_call(self, api, sources=None, raw=None, *, label, expected="accepted"):
        module, function, arguments = {
            "raw-source": (source_reader, "observe_source_hinges", (sources,)),
            "raw-artifact": (artifact_reader, "observe_glb_hinges", (raw,)),
            "raw-comparison": (comparison, "compare_hinges", (sources, raw)),
        }[api]
        entry = {"case": self.id(), "api": api, "label": label, "expected": expected,
                 "sources": {name: record_bytes(value, ".ok") for name, value in (sources or {}).items()},
                 "artifact": record_bytes(raw, ".glb") if raw is not None else None}
        CALLS.append(entry)
        try:
            value = getattr(module, function)(*arguments)
        except module.Fault as exc:
            entry.update(outcome="typed_refusal", code=exc.code, detail=exc.detail,
                         pointer=getattr(exc, "pointer", None))
            raise
        except Exception as exc:
            entry.update(outcome="untyped_exception", exception=type(exc).__name__, detail=str(exc))
            raise
        entry.update(outcome="raw_success", historicalInputsBound=value.get("historicalInputsBound"))
        self.assertIs(value["historicalInputsBound"], False)
        for flag in ("acceptedRevisionQualified", "executionAllowed", "completeC255Semantic",
                     "sourceValidityQualified", "sitePosesEvaluated"):
            self.assertFalse(value.get(flag, False))
        return value

    def refuse(self, endpoint="before", *, label, code, reason=None, repo=UNSET, module=reader):
        with self.assertRaises(module.Fault) as caught:
            self.reader_call(endpoint, label=label, repo=repo, module=module, expected="typed_refusal")
        fault = caught.exception
        self.assertIn(fault.code, FAULT_CODES)
        self.assertEqual(fault.code, code)
        if reason is not None:
            self.assertEqual(fault.reason, reason)
        self.assertTrue(fault.detail)
        self.assertLessEqual(len(fault.detail), 1024)
        self.assertLessEqual(len(fault.pointer), 512)
        self.assertLessEqual(len(str(fault)), 2048)
        self.assertFalse(hasattr(fault, "records"), "Refusal must not publish a qualified hinge subset")
        self.assertFalse(hasattr(fault, "historicalAdmission"))
        self.assertLessEqual(set(fault.sourceHashes), {"main.ok", "hinges.ok"})
        self.assertLessEqual(set(fault.sourceBytes), {"main.ok", "hinges.ok"})
        for value in fault.sourceHashes.values():
            self.assertRegex(value, r"^[0-9a-f]{64}$")
        if fault.artifactSha256 is not None:
            self.assertRegex(fault.artifactSha256, r"^[0-9a-f]{64}$")
        return fault

    def assert_semantics(self, value, expected, sources, raw):
        self.assertEqual(value["hingeCount"], 8)
        self.assertEqual(value["siteCount"], 16)
        self.assertEqual(value["objectCount"], 18)
        self.assertEqual(len({tuple(row["definitionId"]) for row in value["records"]}), 1)
        self.assertEqual(value["sourceHashes"], {name: fixtures.digest(data) for name, data in sources.items()})
        self.assertEqual(value["sourceBytes"], {name: len(data) for name, data in sources.items()})
        self.assertEqual(value["artifactSha256"], fixtures.digest(raw))
        self.assertEqual(value["artifactBytes"], len(raw))
        manifest, revision = fixtures.program_identity(sources)
        self.assertEqual(value["sourceManifest"], manifest)
        self.assertEqual(value["programRevision"], revision)
        records = {row["path"]: row for row in value["records"]}
        self.assertEqual(len(records), len(value["records"]))
        self.assertEqual(set(records), set(expected))
        document = fixtures.decode_glb(raw)[0]
        sites = {}
        for path, want in expected.items():
            row = records[path]
            self.assertEqual(row["id"], want["id"])
            self.assertEqual(row["definitionId"], want["definitionId"])
            for key in ("id", "definitionId", "path", "name", "key", "kind", "ownerId", "ownerDefinitionId",
                        "axis", "limits", "initial"):
                self.assertEqual(row["source"][key], want[key], (path, key))
            self.assertEqual(row["source"]["axisFrame"], "parent-site")
            self.assertIs(row["source"]["sourceCompatibilityVerified"], True)
            self.assertEqual(row["artifact"]["claims"], {"path": path, "element_id": want["id"], "kind": "hinge",
                "parent_site": want["parentSite"]["path"], "child_site": want["childSite"]["path"],
                "axis": want["axis"], "limits": want["limits"], "initial": want["initial"]})
            for field, observed in row["artifact"]["claims"].items():
                self.assertEqual(pointer(document, row["artifact"]["origins"][field]), observed)
            for order, source_key in (("parent", "parentSite"), ("child", "childSite")):
                site = row["endpoints"][order]["source"]
                for key, expected_field in want[source_key].items():
                    self.assertEqual(site[key], expected_field)
                self.assertEqual(site["interface"], "hinged.part")
                self.assertEqual(site["sizeM"], 0)
                self.assertIs(site["poseEvaluated"], False)
                self.assertEqual(site["compatibilityAuthority"], "source-only")
                self.assertEqual(row["endpoints"][order]["artifactPath"], want[source_key]["path"])
                self.assertNotIn("artifactDefinitionId", row["endpoints"][order])
                self.assertNotIn("artifactSpan", row["endpoints"][order])
                self.assertNotIn("artifactPose", row["endpoints"][order])
                sites[tuple(site["id"])] = site
            for witness in witnesses(row["source"]):
                data = sources[witness["file"]]
                self.assertEqual(witness["sha256"], fixtures.digest(data))
                start, stop = witness["startByte"], witness["endByteExclusive"]
                self.assertIs(type(start), int)
                self.assertIs(type(stop), int)
                self.assertTrue(0 <= start < stop <= len(data))
                if "text" in witness:
                    self.assertEqual(witness["text"], data[start:stop].decode())
        self.assertEqual({tuple(row["id"]) for row in value["sites"]}, set(sites))
        # The original child offset is a byte witness, not a world-space result.
        child = next(row for row in value["sites"] if row["name"] == "base")
        origin = child["sourceOrigins"]["fields"]["pose"]["expression"]
        expression = sources[origin["file"]][origin["startByte"]:origin["endByteExclusive"]]
        self.assertIn(b"-self.length / 2", expression)

    def accept(self, endpoint="before", *, label, repo=UNSET, module=reader):
        result = self.reader_call(endpoint, label=label, repo=repo, module=module)
        self.assertEqual(result["schema"], "ontokin.c268.bound-hinge-endpoint/0.1")
        self.assertEqual(result["comparisonSchema"], "ontokin.c267.hinge-comparison/0.1")
        self.assertEqual(result["contract"], "ontokin.c260.hinge-declarations/0.1")
        self.assertEqual(result["endpoint"], endpoint)
        self.assertEqual(result["historicalAdmission"], fixtures.pins(endpoint))
        for flag in ("historicalInputsBound", "inputBindingVerified", "hingeComparisonVerified",
                     "hingeSetAgreementVerified", "endpointAgreementVerified"):
            self.assertIs(result[flag], True)
        for flag in ("sitePosesEvaluated", "sourceValidityQualified", "acceptedRevisionQualified",
                     "completeC255Semantic", "executionAllowed", "directSiteTableObserved",
                     "jointDefinitionOrSpanObserved"):
            self.assertIs(result[flag], False)
        self.assertIsNone(result["realTrialSuccess"])
        for flag in ("physicalValidityVerified", "endpointWorldAlignmentVerified", "rebuildQualified",
                     "invalidEditAtomicityQualified", "fullGLBValidityQualified", "comparativeAdvantageVerified",
                     "nativeBehaviorQualified"):
            self.assertFalse(result.get(flag, False))
        self.assertTrue(result["limits"])
        self.assertTrue(result["unobservedFields"])
        text = " ".join(result["limits"]).lower()
        for phrase in ("accepted revision", "edit atomicity", "rebuild", "physical validity", "native",
                       "model trial", "comparative benefit", "world-alignment", "source/glTF/C255".lower()):
            self.assertIn(phrase, text)
        self.assertNotIn("No historical byte admission, accepted revision, edit atomicity or clean rebuild",
                         result["limits"])
        sources = {"main.ok": self.original[endpoint + ".main.ok"], "hinges.ok": self.original["hinges.ok"]}
        self.assert_semantics(result, fixtures.expected_hinges(), sources, self.original[endpoint + ".glb"])
        return result

    def target_reader(self, target, callback):
        identity = target.stat()
        identity = (identity.st_dev, identity.st_ino)
        def intercepted(fd, size):
            actual = REAL_FSTAT(fd)
            if (actual.st_dev, actual.st_ino) == identity:
                self.assertGreater(size, 0)
                self.assertLessEqual(size, fixtures.HISTORICAL[target.name][0] + 1)
                return callback(fd, size)
            return REAL_READ(fd, size)
        return intercepted

    def test_fixed_control_pins_match_c260_and_c253(self):
        contract = json.loads((HERE.parent / "localized-repair-c260/INPUTS.json").read_text())
        actual = {row["path"]: (row["bytes"], row["sha256"]) for row in contract["files"]}
        for name, pin in fixtures.HISTORICAL.items():
            self.assertEqual(actual[fixtures.PROOF + "/" + name], pin)
        corpus = json.loads((HERE.parent / "localized-repair-c253/corpus.json").read_text())
        for key, entry in contract["c253MatchingPins"].items():
            self.assertEqual(corpus["files"][key], entry)

    def test_original_before_after_with_path_and_string_roots(self):
        for endpoint in ("before", "after"):
            for root in (self.repo, str(self.repo)):
                with self.subTest(endpoint=endpoint, root_type=type(root).__name__):
                    self.accept(endpoint, label="exact original " + endpoint + " " + type(root).__name__, repo=root)

    def test_relative_repository_root(self):
        previous = os.getcwd()
        try:
            os.chdir(self.temporary)
            self.accept(label="relative repository root", repo="repo")
        finally:
            os.chdir(previous)

    def test_comparison_records_and_nonclaims_preserved(self):
        for endpoint in ("before", "after"):
            sources = {"main.ok": self.original[endpoint + ".main.ok"], "hinges.ok": self.original["hinges.ok"]}
            raw = self.original[endpoint + ".glb"]
            original = self.raw_call("raw-comparison", sources, raw, label="unmodified raw comparator " + endpoint)
            admitted = self.accept(endpoint, label="compare wrapper preservation " + endpoint)
            for key in original:
                if key not in ("schema", "historicalInputsBound", "limits"):
                    self.assertEqual(admitted[key], original[key], key)
            remaining_limits = [entry for entry in original["limits"] if not entry.startswith("No historical byte admission")]
            for entry in remaining_limits:
                self.assertIn(entry, admitted["limits"])

    def test_missing_each_selected_input(self):
        for endpoint in ("before", "after"):
            for name in (endpoint + ".main.ok", "hinges.ok", endpoint + ".glb"):
                with self.subTest(endpoint=endpoint, name=name):
                    self.remove(name)
                    self.refuse(endpoint, label="missing " + name, code="IO_ERROR", reason="MISSING")
                    self.replace(name, self.original[name])

    def test_wrong_size_each_input_is_refused_before_payload_read(self):
        for endpoint in ("before", "after"):
            for name in (endpoint + ".main.ok", "hinges.ok", endpoint + ".glb"):
                for direction in ("short", "long"):
                    with self.subTest(endpoint=endpoint, name=name, direction=direction):
                        raw = self.original[name][:-1] if direction == "short" else self.original[name] + b"x"
                        self.replace(name, raw)
                        reads = []
                        def read_forbidden(fd, size):
                            reads.append(size)
                            raise AssertionError("Wrong declared size must refuse before os.read")
                        with mock.patch.object(reader.os, "read", self.target_reader(self.proof / name, read_forbidden)):
                            fault = self.refuse(endpoint, label="declared wrong size " + name + " " + direction,
                                                code="INPUT_SIZE", reason="SIZE")
                        self.assertEqual(reads, [])
                        if name.endswith(".glb"):
                            self.assertIsNone(fault.artifactSha256)
                        else:
                            logical = "hinges.ok" if name == "hinges.ok" else "main.ok"
                            self.assertNotIn(logical, fault.sourceHashes)
                        self.replace(name, self.original[name])

    def test_same_size_changed_bytes_each_input(self):
        for endpoint in ("before", "after"):
            for name in (endpoint + ".main.ok", "hinges.ok", endpoint + ".glb"):
                with self.subTest(endpoint=endpoint, name=name):
                    raw = bytearray(self.original[name])
                    raw[-1] ^= 1
                    self.replace(name, bytes(raw))
                    fault = self.refuse(endpoint, label="same-size changed bytes " + name,
                                        code="HISTORICAL_BINDING", reason="HASH")
                    if name.endswith(".glb"):
                        self.assertEqual(fault.artifactSha256, fixtures.digest(raw))
                    else:
                        logical = "hinges.ok" if name == "hinges.ok" else "main.ok"
                        self.assertEqual(fault.sourceHashes[logical], fixtures.digest(raw))
                    self.replace(name, self.original[name])

    def test_unselected_endpoint_files_are_not_required(self):
        self.remove("after.main.ok")
        self.remove("after.glb")
        self.accept(label="before requires only its selected three files")
        self.replace("after.main.ok", self.original["after.main.ok"])
        self.replace("after.glb", self.original["after.glb"])
        self.remove("before.main.ok")
        self.remove("before.glb")
        self.accept("after", label="after requires only its selected three files")

    def test_other_endpoint_bytes_do_not_authorize_selected_endpoint(self):
        self.replace("before.main.ok", self.original["after.main.ok"])
        self.refuse(label="after main bytes under before path", code="HISTORICAL_BINDING", reason="HASH")
        self.replace("before.main.ok", self.original["before.main.ok"])
        self.replace("before.glb", self.original["after.glb"])
        self.refuse(label="after GLB bytes under before path", code="INPUT_SIZE", reason="SIZE")

    def exercise_changed_pair(self, same_size):
        sources, raw, expected = fixtures.paired_change(same_size=same_size)
        source = self.raw_call("raw-source", sources, label="changed paired raw source " + str(same_size))
        artifact = self.raw_call("raw-artifact", raw=raw, label="changed paired raw artifact " + str(same_size))
        compared = self.raw_call("raw-comparison", sources, raw, label="changed paired raw comparison " + str(same_size))
        self.assertEqual(source["hingeCount"], 8)
        self.assertEqual(len(artifact["records"]), 8)
        for row in source["records"]:
            want = expected[row["path"]]
            for field in ("id", "definitionId", "axis", "limits", "initial"):
                self.assertEqual(row[field], want[field])
        for row in artifact["records"]:
            want = expected[row["claims"]["path"]]
            for field in ("axis", "limits", "initial"):
                self.assertEqual(row["claims"][field], want[field])
        self.assert_semantics(compared, expected, sources, raw)
        for logical, name in (("main.ok", "before.main.ok"), ("hinges.ok", "hinges.ok")):
            self.replace(name, sources[logical])
        self.replace("before.glb", raw)
        self.refuse(label="supported paired bytes are not historical " + str(same_size),
                    code="HISTORICAL_BINDING", reason="HASH")
        # Isolate GLB and leaf admission too; a changed main must not mask them.
        self.replace("before.main.ok", self.original["before.main.ok"])
        self.refuse(label="paired changed leaf historical boundary " + str(same_size),
                    code="HISTORICAL_BINDING" if same_size else "INPUT_SIZE",
                    reason="HASH" if same_size else "SIZE")
        self.replace("hinges.ok", self.original["hinges.ok"])
        self.refuse(label="paired changed GLB historical boundary " + str(same_size),
                    code="HISTORICAL_BINDING" if same_size else "INPUT_SIZE",
                    reason="HASH" if same_size else "SIZE")

    def test_supported_same_size_paired_axis_change_stays_raw_only(self):
        self.exercise_changed_pair(True)

    def test_supported_different_size_paired_initial_change_stays_raw_only(self):
        self.exercise_changed_pair(False)

    def test_artifact_only_initial_change_remains_visible_but_unbound(self):
        raw = self.original["before.glb"]
        self.assertEqual(raw.count(b'"initial":0.0'), 8)
        changed = raw.replace(b'"initial":0.0', b'"initial":0.5', 1)
        artifact = self.raw_call("raw-artifact", raw=changed, label="same-size GLB-only initial change")
        self.assertEqual(artifact["records"][0]["claims"]["initial"], 0.5)
        sources = {"main.ok": self.original["before.main.ok"], "hinges.ok": self.original["hinges.ok"]}
        with self.assertRaises(comparison.Fault) as caught:
            self.raw_call("raw-comparison", sources, changed, label="raw disagreement remains a field refusal",
                          expected="typed_refusal")
        self.assertEqual(caught.exception.code, "FIELD_MISMATCH")
        self.replace("before.glb", changed)
        self.refuse(label="GLB-only supported field change historical refusal", code="HISTORICAL_BINDING", reason="HASH")

    def test_no_comparison_before_all_historical_files_admitted(self):
        for name in ("before.main.ok", "hinges.ok", "before.glb"):
            self.replace(name, self.original[name][:-1] + b"x")
            with mock.patch.object(reader, "_compare_captured", side_effect=AssertionError("Premature comparison")) as call:
                self.refuse(label="historical refusal precedes comparison " + name,
                            code="HISTORICAL_BINDING", reason="HASH")
            call.assert_not_called()
            self.replace(name, self.original[name])

    def test_symbolic_link_each_input_leaf_refuses_even_exact_target(self):
        for name in ("before.main.ok", "hinges.ok", "before.glb"):
            target = self.temporary / ("outside-" + name)
            target.write_bytes(self.original[name])
            self.remove(name)
            (self.proof / name).symlink_to(target)
            self.states[name] = {"symlink": str(target), "targetBytes": record_bytes(self.original[name], ".input")}
            self.refuse(label="exact external bytes through symlink " + name, code="INPUT_PATH", reason="SYMLINK")
            (self.proof / name).unlink()
            self.replace(name, self.original[name])

    def test_symbolic_link_ancestor_inside_repository(self):
        target = self.temporary / "actual-proof"
        self.proof.rename(target)
        self.proof.symlink_to(target, target_is_directory=True)
        self.events.append({"recipe": "move proof directory outside repo, replace fixed ancestor by symlink"})
        self.refuse(label="symlink fixed-path ancestor", code="INPUT_PATH", reason="SYMLINK")

    def test_symbolic_link_repository_root(self):
        link = self.temporary / "root-link"
        link.symlink_to(self.repo, target_is_directory=True)
        self.refuse(label="repository root is symlink", repo=link, code="INPUT_PATH", reason="SYMLINK")

    def test_symbolic_link_above_repository_root(self):
        container = self.temporary / "actual-container"
        container.mkdir()
        self.repo.rename(container / "repo")
        link = self.temporary / "ancestor-link"
        link.symlink_to(container, target_is_directory=True)
        self.refuse(label="symlink above supplied root", repo=link / "repo", code="INPUT_PATH", reason="SYMLINK")

    def test_leaf_and_ancestor_symbolic_link_loops(self):
        self.remove("before.main.ok")
        leaf = self.proof / "before.main.ok"
        leaf.symlink_to(leaf.name)
        self.states[leaf.name] = {"symlinkLoop": leaf.name}
        self.refuse(label="self-referencing leaf symlink", code="INPUT_PATH", reason="SYMLINK")
        leaf.unlink()
        self.replace(leaf.name, self.original[leaf.name])
        target = self.temporary / "retained-proof"
        self.proof.rename(target)
        self.proof.symlink_to("proof", target_is_directory=True)
        self.events.append({"recipe": "fixed proof ancestor points to itself"})
        self.refuse(label="self-referencing ancestor symlink", code="INPUT_PATH", reason="SYMLINK")

    def test_invalid_endpoint_refuses_without_filesystem_access(self):
        for selector in ("", "BEFORE", "before.glb", "../before", "/before", "after/../before", None, 0,
                         True, [], {"endpoint": "before"}, "a" * 5000):
            with self.subTest(selector_type=type(selector).__name__):
                with mock.patch.object(reader.os, "open", side_effect=AssertionError("Invalid selector accessed a file")), \
                     mock.patch.object(reader.os, "stat", side_effect=AssertionError("Invalid selector inspected a file")):
                    self.refuse(selector, label="invalid selector " + type(selector).__name__, code="ENDPOINT", reason="ENDPOINT")

    def test_overlong_endpoint_refuses_before_pin_lookup(self):
        class ForbiddenPinLookup:
            def __contains__(self, key):
                raise AssertionError("Overlong selector reached the pin lookup")
        selector = "before" + "x" * 100000
        self.events.append({"operation": "PINS membership spy", "selectorCharacters": len(selector),
                            "recipe": "literal before followed by 100000 ASCII x characters",
                            "sha256": fixtures.digest(selector.encode()), "lookupMustRemainUncalled": True})
        with mock.patch.object(reader, "PINS", ForbiddenPinLookup()), \
             mock.patch.object(reader.os, "open", side_effect=AssertionError("Overlong selector accessed a file")), \
             mock.patch.object(reader.os, "stat", side_effect=AssertionError("Overlong selector inspected a file")):
            self.refuse(selector, label="overlong built-in string rejected before pin membership",
                        code="ENDPOINT", reason="ENDPOINT")

    def test_escape_invalid_root_types_and_resource_bounds_access_no_files(self):
        class HostilePath:
            def __fspath__(self):
                raise AssertionError("Arbitrary path protocol must not execute")
            def __str__(self):
                raise AssertionError("Arbitrary path object must not be stringified")
        cases = [(None, "INPUT_PATH"), (b"/tmp", "INPUT_PATH"), (0, "INPUT_PATH"), (HostilePath(), "INPUT_PATH"),
                 ("", "INPUT_PATH"), ("a\0b", "INPUT_PATH"), ("a\ud800b", "INPUT_PATH"),
                 (str(self.repo) + "/..", "INPUT_PATH"), (self.repo / "..", "INPUT_PATH"), ("../repo", "INPUT_PATH"),
                 ("//server/repo", "INPUT_PATH"), ("x" * 4097, "RESOURCE_LIMIT"),
                 ("/".join(["x"] * 129), "RESOURCE_LIMIT"), ("é" * 2049, "RESOURCE_LIMIT"),
                 ("\ud800" + "x" * 4097, "RESOURCE_LIMIT")]
        for root, code in cases:
            with self.subTest(root_type=type(root).__name__, code=code):
                with mock.patch.object(reader.os, "open", side_effect=AssertionError("Invalid root accessed a file")), \
                     mock.patch.object(reader.os, "stat", side_effect=AssertionError("Invalid root inspected a file")):
                    self.refuse(label="invalid or escaping root " + type(root).__name__, repo=root,
                                code=code)

    def test_missing_root_is_typed_io_refusal(self):
        self.refuse(label="missing repository root", repo=self.temporary / "missing-repo",
                    code="IO_ERROR", reason="MISSING")

    def test_nonregular_directory_at_each_input_path(self):
        for name in ("before.main.ok", "hinges.ok", "before.glb"):
            self.remove(name)
            (self.proof / name).mkdir()
            self.states[name] = {"type": "directory"}
            self.refuse(label="directory used as file " + name, code="INPUT_PATH", reason="NOT_REGULAR")
            (self.proof / name).rmdir()
            self.replace(name, self.original[name])

    def subprocess_refusal(self, module_path, *, label, code, reason):
        # A separate process makes a missing O_NONBLOCK failure bounded too.
        script = """import importlib.util,json,sys
spec=importlib.util.spec_from_file_location('c268_fifo_probe',sys.argv[1])
module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
try:
    value=module.read_bound_endpoint(sys.argv[2],'before')
except module.Fault as exc:
    print(json.dumps({'outcome':'typed_refusal','code':exc.code,'reason':exc.reason,'detail':exc.detail,
                      'recordsPresent':hasattr(exc,'records')}))
else:
    print(json.dumps({'outcome':'admitted','historicalInputsBound':value.get('historicalInputsBound')}))
"""
        entry = {"case": self.id(), "api": "historical-reader", "label": label, "expected": "typed_refusal",
                 "inputs": self.selected_inputs("before"), "mechanism": "subprocess with 5-second deadline",
                 "timeoutSeconds": 5, "interpreter": sys.executable,
                 "readerCode": {"bytes": module_path.stat().st_size, "sha256": fixtures.digest(module_path.read_bytes())},
                 "injectedEvents": self.events}
        CALLS.append(entry)
        self.events = []
        try:
            completed = subprocess.run([sys.executable, "-B", "-c", script, str(module_path), str(self.repo)],
                                       capture_output=True, text=True, timeout=5, check=False)
        except subprocess.TimeoutExpired as exc:
            entry.update(outcome="timeout", stdout=exc.stdout, stderr=exc.stderr)
            self.fail("FIFO reader exceeded five-second bound")
        entry.update(returncode=completed.returncode, stdout=completed.stdout, stderr=completed.stderr)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        entry.update(result)
        self.assertEqual(result["outcome"], "typed_refusal")
        self.assertEqual(result["code"], code)
        self.assertEqual(result["reason"], reason)
        self.assertIs(result["recordsPresent"], False)

    def test_fifo_input_refuses_without_hanging(self):
        self.remove("before.main.ok")
        os.mkfifo(self.proof / "before.main.ok")
        self.states["before.main.ok"] = {"type": "fifo", "producer": None}
        self.subprocess_refusal(HERE / "endpoint_reader.py", label="FIFO has no writer and cannot hang",
                                code="INPUT_PATH", reason="NOT_REGULAR")

    def test_permission_refusal_with_explicit_oserror_injection(self):
        target = self.proof / "before.main.ok"
        target.chmod(0)
        try:
            try:
                probe = REAL_OPEN(target, os.O_RDONLY | os.O_NONBLOCK)
            except PermissionError:
                actual_denial = True
                self.refuse(label="actual chmod denial", code="IO_ERROR", reason="PERMISSION")
            else:
                REAL_CLOSE(probe)
                actual_denial = False
        finally:
            target.chmod(0o600)
        NOTES.append({"case": self.id(), "permissionProbe": "mode 000 file", "actualPermissionDenial": actual_denial,
                      "effectiveUid": os.geteuid(), "deterministicCoverage": "Injected EACCES at os.open and os.read"})
        def deny_open(path, flags, *args, **kwargs):
            if os.fspath(path) == "before.main.ok":
                self.events.append({"operation": "os.open", "errno": errno.EACCES, "injected": True})
                raise PermissionError(errno.EACCES, "injected permission denial")
            return REAL_OPEN(path, flags, *args, **kwargs)
        with mock.patch.object(reader.os, "open", deny_open):
            self.refuse(label="deterministically injected open permission error", code="IO_ERROR", reason="PERMISSION")
        def deny_read(fd, size):
            self.events.append({"operation": "os.read", "errno": errno.EACCES, "injected": True})
            raise PermissionError(errno.EACCES, "injected permission denial")
        with mock.patch.object(reader.os, "read", self.target_reader(target, deny_read)):
            self.refuse(label="deterministically injected read permission error", code="IO_ERROR", reason="PERMISSION")

    def test_injected_fstat_and_read_oserrors_are_typed(self):
        target = self.proof / "before.main.ok"
        native_stat = target.stat()
        identity = (native_stat.st_dev, native_stat.st_ino)
        def fail_stat(fd):
            actual = REAL_FSTAT(fd)
            if (actual.st_dev, actual.st_ino) == identity:
                self.events.append({"operation": "os.fstat", "errno": errno.EIO, "injected": True})
                raise OSError(errno.EIO, "injected fstat error")
            return actual
        with mock.patch.object(reader.os, "fstat", fail_stat):
            self.refuse(label="injected initial fstat failure", code="IO_ERROR")
        def fail_read(fd, size):
            self.events.append({"operation": "os.read", "errno": errno.EIO, "injected": True})
            raise OSError(errno.EIO, "injected read error")
        with mock.patch.object(reader.os, "read", self.target_reader(target, fail_read)):
            self.refuse(label="injected read I/O failure", code="IO_ERROR")

    def test_truncation_after_size_check_is_bounded_and_never_compared(self):
        for name in ("before.main.ok", "before.glb"):
            reads = []
            def shrink(fd, size):
                reads.append(size)
                self.events.append({"recipe": "truncate one byte after initial stat, before read", "file": name,
                                    "readRequested": size})
                self.replace(name, self.original[name][:-1])
                return REAL_READ(fd, size)
            with mock.patch.object(reader.os, "read", self.target_reader(self.proof / name, shrink)), \
                 mock.patch.object(reader, "_compare_captured", side_effect=AssertionError("Partial comparison")) as compare:
                self.refuse(label="file shrinks after stat " + name, code="HISTORICAL_BINDING", reason="SHORT_READ")
            self.assertTrue(reads)
            compare.assert_not_called()
            self.replace(name, self.original[name])

    def test_growth_after_size_check_is_bounded_and_never_compared(self):
        for name in ("before.main.ok", "before.glb"):
            reads = []
            def grow(fd, size):
                reads.append(size)
                self.events.append({"recipe": "append one byte after initial stat, before read", "file": name,
                                    "readRequested": size})
                self.replace(name, self.original[name] + b"x")
                return REAL_READ(fd, size)
            with mock.patch.object(reader.os, "read", self.target_reader(self.proof / name, grow)), \
                 mock.patch.object(reader, "_compare_captured", side_effect=AssertionError("Growing input compared")) as compare:
                self.refuse(label="file grows after stat " + name, code="HISTORICAL_BINDING", reason="GROWN")
            self.assertTrue(reads)
            compare.assert_not_called()
            self.replace(name, self.original[name])

    def test_growth_after_read_is_detected_by_final_metadata_check(self):
        for name in ("before.main.ok", "before.glb"):
            def grow_after(fd, size):
                raw = REAL_READ(fd, size)
                self.events.append({"recipe": "append one byte after read, before final stat", "file": name})
                self.replace(name, self.original[name] + b"x")
                return raw
            with mock.patch.object(reader.os, "read", self.target_reader(self.proof / name, grow_after)), \
                 mock.patch.object(reader, "_compare_captured", side_effect=AssertionError("Changed input compared")) as compare:
                self.refuse(label="file grows after captured read " + name, code="HISTORICAL_BINDING")
            compare.assert_not_called()
            self.replace(name, self.original[name])

    def test_large_sparse_wrong_size_is_never_read_or_hashed(self):
        for name, size in (("before.main.ok", 65537), ("before.glb", 4 * 1024 * 1024 + 1)):
            with (self.proof / name).open("wb") as handle:
                handle.truncate(size)
            hasher = hashlib.sha256()
            remaining = size
            while remaining:
                chunk_size = min(remaining, 65536)
                hasher.update(b"\0" * chunk_size)
                remaining -= chunk_size
            self.states[name] = {"bytes": size, "sha256": hasher.hexdigest(),
                                 "recipe": "sparse file consisting entirely of zero bytes; SHA-256 derived from recipe",
                                 "notReadByControl": True}
            def forbidden(fd, amount):
                raise AssertionError("Oversize payload must not be read or hashed")
            with mock.patch.object(reader.os, "read", self.target_reader(self.proof / name, forbidden)):
                fault = self.refuse(label="sparse oversize declared size " + name, code="INPUT_SIZE", reason="SIZE")
            if name.endswith(".glb"):
                self.assertIsNone(fault.artifactSha256)
            else:
                self.assertNotIn("main.ok", fault.sourceHashes)
            self.replace(name, self.original[name])

    def isolated_reader(self):
        root = self.temporary / "isolated-code"
        target = root / "localized-repair-c268/endpoint_reader.py"
        target.parent.mkdir(parents=True)
        target.write_bytes((HERE / "endpoint_reader.py").read_bytes())
        for relative, pin in fixtures.DEPENDENCIES.items():
            raw = (HERE.parent / relative).read_bytes()
            self.assertEqual((len(raw), fixtures.digest(raw)), pin)
            destination = root / relative
            destination.parent.mkdir(parents=True)
            destination.write_bytes(raw)
        return root, fixtures.load_module("c268_isolated_reader_" + str(id(self)), target)

    def test_every_dependency_is_rechecked_after_prior_success(self):
        root, isolated = self.isolated_reader()
        self.accept(label="isolated exact dependency closure", module=isolated)
        for relative in fixtures.DEPENDENCIES:
            path = root / relative
            original = path.read_bytes()
            changed = original.replace(b" ", b"\t", 1)
            self.assertEqual(len(original), len(changed))
            self.assertNotEqual(original, changed)
            path.write_bytes(changed)
            self.events.append({"recipe": "first ASCII space changed to tab", "dependency": relative,
                                "changedBytes": record_bytes(changed, ".py")})
            self.refuse(label="same-size dependency mutation after prior success " + relative,
                        code="INPUT_BINDING", reason="HASH", module=isolated)
            path.write_bytes(original)

    def test_dependency_missing_wrong_size_and_symlink_refuse(self):
        root, isolated = self.isolated_reader()
        self.accept(label="dependency failure controls begin with exact success", module=isolated)
        relative = "localized-repair-c267/hinge_compare.py"
        path = root / relative
        original = path.read_bytes()
        path.unlink()
        self.events.append({"dependency": relative, "missing": True})
        self.refuse(label="missing pinned comparator", code="INPUT_BINDING", reason="MISSING", module=isolated)
        path.write_bytes(original + b"\n")
        self.events.append({"dependency": relative, "changedBytes": record_bytes(original + b"\n", ".py")})
        self.refuse(label="wrong-size pinned comparator", code="INPUT_BINDING", reason="SIZE", module=isolated)
        path.unlink()
        external = self.temporary / "external-comparison.py"
        external.write_bytes(original)
        path.symlink_to(external)
        self.events.append({"dependency": relative, "symlinkTarget": str(external)})
        self.refuse(label="exact comparator through symlink", code="INPUT_BINDING", reason="SYMLINK", module=isolated)
        path.unlink()
        path.write_bytes(original)
        moved = self.temporary / "moved-comparison-directory"
        path.parent.rename(moved)
        path.parent.symlink_to(moved, target_is_directory=True)
        self.events.append({"dependencyAncestor": str(path.parent), "symlinkTarget": str(moved)})
        self.refuse(label="comparator ancestor symlink", code="INPUT_BINDING", reason="SYMLINK", module=isolated)

    def test_fifo_dependency_refuses_without_hanging(self):
        root, isolated = self.isolated_reader()
        del isolated
        relative = "localized-repair-c267/hinge_compare.py"
        path = root / relative
        path.unlink()
        os.mkfifo(path)
        self.events.append({"dependency": relative, "type": "fifo", "producer": None})
        self.subprocess_refusal(root / "localized-repair-c268/endpoint_reader.py",
                                label="FIFO dependency cannot hang", code="INPUT_BINDING", reason="NOT_REGULAR")

    def test_comparison_refusal_is_preserved_without_partial_success(self):
        # Interpose one actual argument at the capture boundary to exercise the
        # translation of a genuine Fault from unchanged pinned C267 code.
        # This is not a claim that admitted original bytes contain a mismatch.
        changed = self.original["before.glb"].replace(b'"initial":0.0', b'"initial":0.5', 1)
        original_compare = reader._compare_captured
        def mismatched_argument(captured, sources, raw):
            self.assertEqual(raw, self.original["before.glb"])
            return original_compare(captured, sources, changed)
        self.events.append({"operation": "_compare_captured argument interposition", "injected": True,
                            "artifact": record_bytes(changed, ".glb"), "purpose": "actual C267 Fault translation"})
        with mock.patch.object(reader, "_compare_captured", mismatched_argument):
            result = self.refuse(label="actual pinned C267 field refusal translation",
                                code="FIELD_MISMATCH", reason="COMPARISON")
        self.assertEqual(result.__cause__.code, "FIELD_MISMATCH")
        self.assertTrue(result.pointer.endswith("/initial"))
        self.assertNotIsInstance(result.__cause__, reader.Fault)
        # The remaining explicitly injected categories test outer refusal
        # preservation and captured identities without manufacturing code bytes.
        for code in ("MALFORMED", "INPUT_BINDING", "RESOURCE_LIMIT",
                     "UNSUPPORTED_SOURCE_FORM", "UNSUPPORTED_ARTIFACT_FORM", "IO_ERROR"):
            fault = reader.Fault(code, "injected inherited comparison refusal", "/extras/ontokin/joints/0/axis",
                                 reason="COMPARISON")
            self.events.append({"operation": "_compare_captured", "injected": True, "code": code})
            with mock.patch.object(reader, "_compare_captured", side_effect=fault) as compare:
                result = self.refuse(label="comparison refusal propagation " + code, code=code, reason="COMPARISON")
            compare.assert_called_once()
            self.assertEqual(result.pointer, "/extras/ontokin/joints/0/axis")
            self.assertEqual(result.sourceHashes, {"main.ok": fixtures.HISTORICAL["before.main.ok"][1],
                                                   "hinges.ok": fixtures.HISTORICAL["hinges.ok"][1]})
            self.assertEqual(result.artifactSha256, fixtures.HISTORICAL["before.glb"][1])

    def test_descriptors_close_on_success_and_refusals(self):
        for mode in ("success", "size", "hash"):
            if mode == "size":
                self.replace("before.main.ok", self.original["before.main.ok"] + b"x")
            elif mode == "hash":
                self.replace("before.main.ok", self.original["before.main.ok"][:-1] + b"x")
            live = set()
            def opened(*args, **kwargs):
                fd = REAL_OPEN(*args, **kwargs)
                self.assertNotIn(fd, live)
                live.add(fd)
                return fd
            def closed(fd):
                result = REAL_CLOSE(fd)
                live.remove(fd)
                return result
            with mock.patch.object(reader.os, "open", opened), mock.patch.object(reader.os, "close", closed):
                if mode == "success":
                    self.accept(label="descriptor closure on success")
                else:
                    self.refuse(label="descriptor closure on " + mode,
                                code="INPUT_SIZE" if mode == "size" else "HISTORICAL_BINDING")
            self.assertEqual(live, set())
            self.replace("before.main.ok", self.original["before.main.ok"])


def code_bytes():
    paths = [HERE / "endpoint_reader.py", Path(__file__), HERE / "endpoint_control_fixtures.py",
             HERE.parent / "localized-repair-c266/binding_control_fixtures.py",
             HERE.parent / "localized-repair-c260/CONTRACT.md", HERE.parent / "localized-repair-c260/INPUTS.json",
             HERE.parent / "localized-repair-c260/CONTROL-PLAN.md", HERE.parent / "localized-repair-c253/corpus.json"]
    paths.extend(HERE.parent / relative for relative in fixtures.DEPENDENCIES)
    return {path.relative_to(fixtures.ROOT).as_posix(): path.read_bytes() for path in paths}


def code_identities(values):
    return {name: {"bytes": len(raw), "sha256": fixtures.digest(raw)} for name, raw in values.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-dir", type=Path)
    args = parser.parse_args()
    if args.evidence_dir is not None:
        args.evidence_dir.mkdir(parents=True, exist_ok=False)
    started = datetime.now(timezone.utc).isoformat()
    before = code_bytes()
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(EndpointReaderControls))
    output = stream.getvalue()
    after = code_bytes()
    stable = before == after
    historical = sum(entry["api"] == "historical-reader" for entry in CALLS)
    admitted = sum(entry.get("outcome") == "admitted" for entry in CALLS)
    raw_success = sum(entry.get("outcome") == "raw_success" for entry in CALLS)
    refusals = sum(entry.get("outcome") == "typed_refusal" for entry in CALLS)
    unexpected = sum(entry.get("outcome") not in ("admitted", "raw_success", "typed_refusal") for entry in CALLS)
    accounting = len(CALLS) == admitted + raw_success + refusals + unexpected
    report = {"schema": "ontokin.c268.independent-endpoint-controls/0.1", "startedAt": started,
              "completedAt": datetime.now(timezone.utc).isoformat(),
              "command": [sys.executable, "-B", str(Path(__file__).resolve()), *sys.argv[1:]],
              "python": sys.version, "platform": platform.platform(), "machine": platform.machine(),
              "effectiveUid": os.geteuid(), "implementationAndControlInputs": code_identities(before),
              "inputCodeStableDuringRun": stable, "testMethods": result.testsRun,
              "failures": [{"case": str(case), "traceback": trace} for case, trace in result.failures],
              "errors": [{"case": str(case), "traceback": trace} for case, trace in result.errors],
              "skipped": list(result.skipped), "passed": result.wasSuccessful() and stable and accounting,
              "apiCalls": len(CALLS), "historicalCalls": historical, "rawCalls": len(CALLS) - historical,
              "admittedCalls": admitted, "rawSuccessfulCalls": raw_success, "successfulCalls": admitted + raw_success,
              "typedRefusals": refusals, "untypedExceptions": unexpected, "callAccountingVerified": accounting,
              "cases": CALLS, "notes": NOTES,
              "limits": ["H01/H03/H04/H26/H27 historical controls, not full H01-H28 requalification",
                         "Permission error injections and bounded filesystem race controls are labeled explicitly",
                         "No product source evaluation/export, site/world, physical, revision, rebuild, native or trial qualification",
                         "Original byte references are frozen C260 paths/hashes; only unique changed bytes are archived"]}
    if args.evidence_dir is not None:
        (args.evidence_dir / "results.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        (args.evidence_dir / "unittest.txt").write_text(output, encoding="utf-8")
        snapshots = args.evidence_dir / "checked-code"
        snapshots.mkdir()
        for name, raw in before.items():
            if name.startswith("docs/engineering/localized-repair-c268/"):
                (snapshots / Path(name).name).write_bytes(raw)
        if not stable:
            (args.evidence_dir / "post-run-code-identities.json").write_text(
                json.dumps(code_identities(after), indent=2) + "\n", encoding="utf-8")
        with zipfile.ZipFile(args.evidence_dir / "inputs.zip", "w", zipfile.ZIP_DEFLATED) as archive:
            for name, raw in sorted(INPUTS.items()):
                archive.writestr(name, raw)
    print(output, end="")
    print(json.dumps({key: report[key] for key in ("passed", "testMethods", "apiCalls", "historicalCalls", "rawCalls",
          "admittedCalls", "rawSuccessfulCalls", "successfulCalls", "typedRefusals", "untypedExceptions",
          "inputCodeStableDuringRun", "callAccountingVerified")}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
