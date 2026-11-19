"""Independent public-API controls for finite C267 hinge comparison.

Expected hinges come from explicit source recipes and C260 rules, never an
observer, product compiler/exporter, sidecar, motion sample or expected table.
Historical admission is deliberately not an interface under test.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import io
import json
import math
import platform
import shutil
import struct
import sys
import tempfile
import unittest
import zipfile
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import comparison_control_fixtures as fixtures

comparison = fixtures.load_file("c267_public_api_under_test", HERE / "hinge_compare.py")
CALLS = []
INPUTS = {}
UNSET = object()
DEPENDENCY_PATHS = ("localized-repair-c266/hinge_binding.py", "localized-repair-c265/source_hinges.py",
                    "localized-repair-c261/hinge_glb.py", "localized-repair-c257/ownership.py")


def _record_bytes(value, extension):
    if type(value) is not bytes:
        return {"type": type(value).__name__}
    sha = hashlib.sha256(value).hexdigest()
    INPUTS.setdefault(sha + extension, value)
    return {"bytes": len(value), "sha256": sha, "snapshot": "inputs.zip!" + sha + extension}


def _pointer(document, pointer):
    value = document
    for part in pointer.lstrip("/").split("/"):
        key = part.replace("~1", "/").replace("~0", "~")
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def _witnesses(value):
    if isinstance(value, dict):
        if {"file", "sha256", "startByte", "endByteExclusive"} <= set(value):
            yield value
        for child in value.values():
            yield from _witnesses(child)
    elif isinstance(value, list):
        for child in value:
            yield from _witnesses(child)


class HingeComparisonControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.small = fixtures.synthetic()

    def call(self, sources, raw, *, label, expected, module=comparison):
        entry = {"case": self.id(), "label": label, "expected": expected,
                 "sources": {name: _record_bytes(value, ".ok") for name, value in sources.items()}
                 if type(sources) is dict else {"type": type(sources).__name__},
                 "artifact": _record_bytes(raw, ".glb")}
        CALLS.append(entry)
        try:
            result = module.compare_hinges(sources, raw)
        except module.Fault as exc:
            entry.update(outcome="typed_refusal", code=exc.code, detail=exc.detail,
                         pointer=getattr(exc, "pointer", None), origin=getattr(exc, "origin", None),
                         sourceHashes=getattr(exc, "sourceHashes", None),
                         sourceBytes=getattr(exc, "sourceBytes", None),
                         artifactSha256=getattr(exc, "artifactSha256", None),
                         artifactBytes=getattr(exc, "artifactBytes", None))
            raise
        except Exception as exc:
            entry.update(outcome="untyped_exception", exception=type(exc).__name__, detail=str(exc))
            raise
        entry.update(outcome="agreement", hingeCount=result.get("hingeCount"),
                     siteCount=result.get("siteCount"), objectCount=result.get("objectCount"),
                     flags={k: v for k, v in result.items() if isinstance(v, bool)})
        return result

    def accept(self, fixture, *, label, raw=None, module=comparison):
        raw = fixture.raw if raw is None else raw
        before = copy.deepcopy(fixture.sources)
        result = self.call(fixture.sources, raw, label=label, expected="agreement", module=module)
        self.assertEqual(before, fixture.sources)
        self.assertEqual(result["schema"], "ontokin.c267.hinge-comparison/0.1")
        self.assertEqual(result["contract"], "ontokin.c260.hinge-declarations/0.1")
        self.assertEqual(result["kind"], "source-artifact-hinge-comparison")
        self.assertEqual(result["artifactSha256"], fixtures.base.digest(raw))
        self.assertEqual(result["artifactBytes"], len(raw))
        self.assertEqual(result["sourceHashes"], {k: fixtures.base.digest(v) for k, v in fixture.sources.items()})
        self.assertEqual(result["sourceBytes"], {k: len(v) for k, v in fixture.sources.items()})
        manifest, revision = fixtures.base.program_identity(fixture.sources)
        self.assertEqual(result["sourceManifest"], manifest)
        self.assertEqual(result["programRevision"], revision)
        for flag in ("inputBindingVerified", "hingeComparisonVerified", "hingeSetAgreementVerified",
                     "endpointAgreementVerified"):
            self.assertIs(result[flag], True)
        for flag in ("historicalInputsBound", "sitePosesEvaluated", "sourceValidityQualified",
                     "acceptedRevisionQualified", "completeC255Semantic", "executionAllowed",
                     "directSiteTableObserved", "jointDefinitionOrSpanObserved"):
            self.assertIs(result[flag], False)
        self.assertIsNone(result["realTrialSuccess"])
        for flag in ("physicalValidityVerified", "endpointWorldAlignmentVerified", "rebuildQualified",
                     "invalidEditAtomicityQualified", "fullGLBValidityQualified", "comparativeAdvantageVerified"):
            self.assertFalse(result.get(flag, False))
        self.assertEqual(result["hingeCount"], len(fixture.joints))
        self.assertEqual(result["objectCount"], len(fixture.objects))
        observed = {row["path"]: row for row in result["records"]}
        self.assertEqual(len(observed), len(result["records"]))
        self.assertEqual(set(observed), set(fixture.joints))
        document, _ = fixtures.base.decode_glb(raw)
        expected_sites = {}
        for path, expected in fixture.joints.items():
            row = observed[path]
            self.assertEqual(row["id"], expected["id"])
            self.assertEqual(row["definitionId"], expected["definitionId"])
            for key in ("id", "definitionId", "path", "name", "key", "ownerId", "ownerDefinitionId",
                        "kind", "axis", "limits", "initial"):
                self.assertEqual(row["source"][key], expected[key], (path, key))
            owner = next(v for v in fixture.objects.values() if v["element_id"] == expected["ownerId"])
            self.assertEqual(row["ownerBinding"]["mapping"], owner)
            self.assertEqual(row["source"]["axisFrame"], "parent-site")
            self.assertIs(row["source"]["sourceCompatibilityVerified"], True)
            for field, value in row["artifact"]["claims"].items():
                self.assertEqual(_pointer(document, row["artifact"]["origins"][field]), value)
            self.assertEqual(row["artifact"]["claims"]["axis"], expected["axis"])
            self.assertEqual(row["artifact"]["claims"]["limits"], expected["limits"])
            self.assertEqual(row["artifact"]["claims"]["initial"], expected["initial"])
            self.assertEqual(row["artifact"]["claims"], {
                "path": expected["path"], "element_id": expected["id"], "kind": expected["kind"],
                "parent_site": expected["parentSite"]["path"], "child_site": expected["childSite"]["path"],
                "axis": expected["axis"], "limits": expected["limits"], "initial": expected["initial"]})
            for order, key in (("parent", "parentSite"), ("child", "childSite")):
                endpoint = row["endpoints"][order]
                site = expected[key]
                expected_sites[tuple(site["id"])] = site
                for k, v in site.items():
                    self.assertEqual(endpoint["source"][k], v)
                self.assertEqual(endpoint["artifactPath"], site["path"])
                self.assertEqual(_pointer(document, endpoint["artifactOrigin"]), site["path"])
                self.assertIs(endpoint["source"]["poseEvaluated"], False)
                self.assertEqual(endpoint["source"]["compatibilityAuthority"], "source-only")
                self.assertEqual(endpoint["objectBinding"]["id"], site["objectId"])
                self.assertEqual(endpoint["objectBinding"]["definitionId"], site["objectDefinitionId"])
                self.assertNotIn("artifactDefinitionId", endpoint)
                self.assertNotIn("artifactSpan", endpoint)
            witnesses = list(_witnesses(row["source"]))
            self.assertTrue(witnesses, "Every source hinge must retain actual byte witnesses")
            for origin in witnesses:
                source = fixture.sources[origin["file"]]
                self.assertEqual(origin["sha256"], fixtures.base.digest(source))
                self.assertIs(type(origin["startByte"]), int)
                self.assertIs(type(origin["endByteExclusive"]), int)
                self.assertTrue(0 <= origin["startByte"] < origin["endByteExclusive"] <= len(source))
                if "text" in origin:
                    self.assertEqual(origin["text"], source[origin["startByte"]:origin["endByteExclusive"]].decode())
        self.assertEqual(result["siteCount"], len(expected_sites))
        self.assertEqual({tuple(s["id"]) for s in result["sites"]}, set(expected_sites))
        return result

    def refuse(self, fixture=None, *, label, code=None, sources=UNSET, raw=UNSET, module=comparison):
        fixture = self.small if fixture is None else fixture
        sources = fixture.sources if sources is UNSET else sources
        raw = fixture.raw if raw is UNSET else raw
        with self.assertRaises(module.Fault) as caught:
            self.call(sources, raw, label=label, expected="refusal", module=module)
        exc = caught.exception
        self.assertIn(exc.code, {"FIELD_MISMATCH", "MALFORMED", "INPUT_BINDING", "UNSUPPORTED_SOURCE_FORM",
                                "UNSUPPORTED_ARTIFACT_FORM", "RESOURCE_LIMIT", "IO_ERROR"})
        if code is not None:
            self.assertEqual(exc.code, code)
        self.assertTrue(exc.detail)
        self.assertFalse(hasattr(exc, "records"), "A refusal must not publish qualified hinge records")
        if type(sources) is dict:
            expected = {k: fixtures.base.digest(v) for k, v in sources.items()
                        if k in ("main.ok", "hinges.ok") and type(v) is bytes and len(v) <= 65536}
            self.assertEqual(exc.sourceHashes, expected)
        if type(raw) is bytes:
            self.assertEqual(exc.artifactBytes, len(raw))
            self.assertEqual(exc.artifactSha256, fixtures.base.digest(raw) if len(raw) <= 4 * 1024 * 1024 else None)
        return exc

    def test_original_before_after_exact_bytes(self):
        for endpoint in ("before", "after"):
            with self.subTest(endpoint=endpoint):
                fixture = fixtures.original(endpoint)
                result = self.accept(fixture, label="exact original " + endpoint,
                                     raw=(fixtures.base.PROOF / (endpoint + ".glb")).read_bytes())
                self.assertEqual(result["hingeCount"], 8)
                self.assertEqual(result["siteCount"], 16)
                self.assertEqual(len({tuple(r["definitionId"]) for r in result["records"]}), 1)

    def test_initial_source_artifact_and_paired_changes(self):
        source = fixtures.synthetic(source_initial="0.25[rad]")
        self.refuse(source, label="source-only initial with rebound provenance", code="FIELD_MISMATCH")
        artifact = self.small.copy()
        artifact.doc["extras"]["ontokin"]["joints"][0]["initial"] = 0.25
        fault = self.refuse(artifact, label="artifact-only initial", code="FIELD_MISMATCH")
        self.assertTrue(fault.pointer.endswith("/initial"))
        self.accept(fixtures.synthetic(source_initial="0.25[rad]", initial=0.25), label="paired initial")

    def test_each_limit_source_artifact_and_paired_changes(self):
        for index, source_text, values in ((0, "range(-0.5[rad], 45[deg])", (-0.5, fixtures.DEG45)),
                                           (1, "range(-45[deg], 0.5[rad])", (-fixtures.DEG45, 0.5))):
            with self.subTest(index=index):
                self.refuse(fixtures.synthetic(source_limits=source_text),
                            label="source-only limit " + str(index), code="FIELD_MISMATCH")
                artifact = self.small.copy()
                artifact.doc["extras"]["ontokin"]["joints"][0]["limits"][index] = values[index]
                self.refuse(artifact, label="artifact-only limit " + str(index), code="FIELD_MISMATCH")
                self.accept(fixtures.synthetic(source_limits=source_text, limits=values),
                            label="paired limit " + str(index))

    def test_inclusive_boundary_zero_width_and_invalid_ranges(self):
        for low, high, initial in ((-1, 1, -1), (-1, 1, 1), (0, 0, 0), (0.25, 0.25, 0.25)):
            self.accept(fixtures.synthetic(source_limits=f"range({low}[rad], {high}[rad])",
                         limits=(low, high), source_initial=f"{initial}[rad]", initial=initial),
                        label=f"closed boundary {low} {high} {initial}")
        for source_limits, source_initial in (("range(1[rad], -1[rad])", "0[rad]"),
                                             ("range(-1[rad], 1[rad])", "1.001[rad]")):
            self.refuse(fixtures.synthetic(source_limits=source_limits, source_initial=source_initial),
                        label="invalid source closed range", code="MALFORMED")
        for limits, initial in (((1, -1), 0), ((-1, 1), 1.001)):
            artifact = self.small.copy()
            artifact.doc["extras"]["ontokin"]["joints"][0].update(limits=list(limits), initial=initial)
            self.refuse(artifact, label="invalid artifact closed range", code="MALFORMED")

    def test_exact_deg_rad_negative_zero_and_adjacent_values(self):
        for literal, expected in (("45[deg]", fixtures.DEG45),
                                  ("0.7853981633974483[rad]", fixtures.DEG45),
                                  ("-0[deg]", -0.0), ("0.1[deg]", fixtures.angle("0.1", "deg"))):
            self.accept(fixtures.synthetic(source_initial=literal, initial=expected), label="exact literal " + literal)
        for value in (math.nextafter(0.0, 1.0), math.nextafter(0.25, 1.0)):
            artifact = fixtures.synthetic(source_initial="0.25[rad]" if value > 0.1 else "0[rad]",
                                          initial=0.25 if value > 0.1 else 0)
            artifact.doc["extras"]["ontokin"]["joints"][0]["initial"] = value
            self.refuse(artifact, label="adjacent binary64 initial " + value.hex(), code="FIELD_MISMATCH")

    def test_six_signed_basis_axes_and_reversal(self):
        for index in range(3):
            for sign in (-1, 1):
                axis = [0, 0, 0]
                axis[index] = sign
                source = "vec3(" + ", ".join(map(str, axis)) + ")"
                self.accept(fixtures.synthetic(source_axis=source, axis=axis), label="paired basis " + repr(axis))
        self.refuse(fixtures.synthetic(source_axis="vec3(0, 0, -1)"),
                    label="source-only axis sign", code="FIELD_MISMATCH")
        artifact = self.small.copy()
        artifact.doc["extras"]["ontokin"]["joints"][0]["axis"] = [0, 0, -1]
        self.refuse(artifact, label="artifact-only axis sign", code="FIELD_MISMATCH")

    def test_unsupported_and_invalid_source_axes(self):
        for axis, code in (("vec3(0, 0, 0)", "MALFORMED"), ("vec3(0, 0, 2)", "MALFORMED"),
                           ("vec3(0.6, 0.8, 0)", "UNSUPPORTED_SOURCE_FORM")):
            self.refuse(fixtures.synthetic(source_axis=axis), label="source axis " + axis, code=code)

    def test_malformed_artifact_fields_and_strict_axis_shape(self):
        mutations = [("axis", [0, 1]), ("axis", [False, 0, 1]), ("axis", [0, 0, "1"]),
                     ("axis", [1e-300, 0, 1]), ("axis", [0, 0, float("nan")]),
                     ("axis", [0, 0, float("inf")]), ("limits", [False, fixtures.DEG45]),
                     ("limits", [0]), ("initial", True), ("initial", "0")]
        for key, value in mutations:
            with self.subTest(key=key, value=repr(value)):
                fixture = self.small.copy()
                fixture.doc["extras"]["ontokin"]["joints"][0][key] = value
                self.refuse(fixture, label="artifact malformed " + key + " " + repr(value))

    def test_computed_source_fields_do_not_use_baseline_values(self):
        for argument, value in (("source_initial", "0[rad] + 0[rad]"),
                                ("source_limits", "range(-45[deg], 45[deg] + 0[rad])"),
                                ("source_axis", "vec3(0, 0, 1 + 0)")):
            self.refuse(fixtures.synthetic(**{argument: value}), label="computed " + argument,
                        code="UNSUPPORTED_SOURCE_FORM")

    def test_joint_name_and_key_have_separate_authority(self):
        name = fixtures.synthetic(joint_name="rotation")
        result = self.accept(name, label="joint lexical rename retains key")
        self.assertTrue(all(r["id"][-1] == "flex" and r["path"].endswith(".rotation") for r in result["records"]))
        self.accept(fixtures.synthetic(joint_key="rotation.key-2"), label="joint key change retains name")
        for fixture, field, old in ((name, "path", ".flex"),
                                   (fixtures.synthetic(joint_key="rotation.key-2"), "element_id", "flex")):
            row = fixture.doc["extras"]["ontokin"]["joints"][0]
            if field == "path":
                row[field] = row[field].rsplit(".", 1)[0] + old
            else:
                row[field][-1] = old
            self.refuse(fixture, label="source joint change with stale artifact " + field, code="FIELD_MISMATCH")

    def test_site_names_and_derived_keys_remain_distinct(self):
        renamed = fixtures.synthetic(parent_name="socket", child_name="anchor")
        self.accept(renamed, label="paired endpoint lexical names")
        for field, suffix in (("parent_site", ".pivot"), ("child_site", ".base")):
            fixture = renamed.copy()
            row = fixture.doc["extras"]["ontokin"]["joints"][0]
            row[field] = row[field].rsplit(".", 1)[0] + suffix
            self.refuse(fixture, label="stale endpoint path after source rename " + field, code="FIELD_MISMATCH")
        result = self.accept(fixtures.synthetic(parent_key="pivot.key-2", child_key="base.key-2"),
                             label="site-key change has source-only identity authority")
        self.assertTrue(all(r["endpoints"]["parent"]["source"]["id"][-1] == "pivot.key-2"
                            for r in result["records"]))

    def test_ordered_endpoint_swap_wrong_object_and_same_object(self):
        self.accept(fixtures.synthetic(swapped=True), label="supported paired endpoint reversal")
        for operation in ("swap", "same", "wrong_object", "suffix_only"):
            fixture = self.small.copy()
            rows = fixture.doc["extras"]["ontokin"]["joints"]
            row = rows[0]
            if operation == "swap":
                row["parent_site"], row["child_site"] = row["child_site"], row["parent_site"]
            elif operation == "same":
                row["child_site"] = row["parent_site"]
            elif operation == "wrong_object":
                row["parent_site"] = rows[1]["parent_site"]
            else:
                row["parent_site"] = "pivot"
            self.refuse(fixture, label="artifact endpoint " + operation, code="FIELD_MISMATCH")
        self.refuse(fixtures.synthetic(edits=(("child = self.blade.base;", "child = self.pivot;"),)),
                    label="source same-object endpoints", code="MALFORMED")

    def test_endpoint_access_and_unsupported_forms(self):
        self.accept(fixtures.synthetic(edits=(('public site pivot @ "pivot"', 'private site pivot @ "pivot"'),)),
                    label="private own site and private own part public external site")
        for old, new, code in (('public site base @ "base"', 'private site base @ "base"', "MALFORMED"),
                               ("parent = self.pivot;", "parent = self.origin;", "UNSUPPORTED_SOURCE_FORM"),
                               ("child = self.blade.base;", 'child = self.blade["x"].base;', "UNSUPPORTED_SOURCE_FORM"),
                               ("child = self.blade.base;", "child = self.blade.child.base;", "UNSUPPORTED_SOURCE_FORM"),
                               ('joint flex @ "flex": hinge', 'joint flex @ "flex": slider', "UNSUPPORTED_SOURCE_FORM")):
            self.refuse(fixtures.synthetic(edits=((old, new),)), label="endpoint/source form " + new, code=code)

    def test_complete_joint_set_and_duplicate_rows(self):
        for operation in ("remove_one", "remove_all", "extra", "wrong_owner", "duplicate_id", "duplicate_path"):
            fixture = self.small.copy()
            rows = fixture.doc["extras"]["ontokin"]["joints"]
            if operation == "remove_one":
                rows.pop()
            elif operation == "remove_all":
                rows.clear()
            elif operation == "extra":
                row = copy.deepcopy(rows[0])
                row["path"] += "Extra"
                row["element_id"][-1] += "-extra"
                rows.append(row)
            elif operation == "wrong_owner":
                rows[0]["element_id"][-2] = "not-an-owner"
            elif operation == "duplicate_id":
                rows[1]["element_id"] = rows[0]["element_id"]
            else:
                rows[1]["path"] = rows[0]["path"]
            self.refuse(fixture, label="complete joint set " + operation,
                        code="MALFORMED" if operation.startswith("duplicate") else "FIELD_MISMATCH")

    def test_row_node_and_mapping_reordering_preserves_pointers(self):
        fixture = self.small.copy()
        fixture.doc["extras"]["ontokin"]["joints"].reverse()
        fixture.doc["nodes"].reverse()
        occurrence = fixture.doc["extras"]["ontokin"]["program"]["occurrences"]
        fixture.doc["extras"]["ontokin"]["program"]["occurrences"] = dict(reversed(list(occurrence.items())))
        result = self.accept(fixture, label="joint node and program row reordering")
        first_path = next(iter(fixture.joints))
        first = next(row for row in result["records"] if row["path"] == first_path)
        self.assertEqual(first["artifact"]["origins"]["path"],
                         "/extras/ontokin/joints/4/path")

    def test_complete_sets_do_not_hide_wrong_id_path_pairing(self):
        fixture = self.small.copy()
        rows = fixture.doc["extras"]["ontokin"]["joints"]
        rows[0]["element_id"], rows[1]["element_id"] = rows[1]["element_id"], rows[0]["element_id"]
        self.refuse(fixture, label="same ID/path sets with swapped identity pairing", code="FIELD_MISMATCH")

    def test_empty_source_and_artifact_hinge_sets_are_complete(self):
        original = fixtures.synthetic()
        leaf = original.sources["hinges.ok"]
        start, end = fixtures.base.block_span(leaf, 'public joint flex @ "flex"')
        exact_joint = leaf[start:end].decode()
        fixture = fixtures.synthetic(edits=((exact_joint, ""),))
        fixture.joints.clear()
        fixture.doc["extras"]["ontokin"]["joints"].clear()
        result = self.accept(fixture, label="empty complete source/artifact hinge sets")
        self.assertEqual(result["siteCount"], 0)

    def test_membership_opaque_keys_rebinding_and_byte_offsets(self):
        for mode in ("helper_default", "direct_default", "helper_override", "final_override"):
            self.accept(fixtures.synthetic(first_keys=("one.a", "two_a", "three-a"),
                         second_keys=("extra",), mode=mode, unicode_prefix=True),
                        label="membership and opaque keys " + mode)
        self.accept(fixtures.synthetic(first_keys=("single",), second_keys=("b", "a"), renamed=True),
                    label="renamed modules classes roots collection and private part")

    def test_binding_failure_cannot_be_hidden_by_equal_hinges(self):
        for mutation in ("entry", "program", "class", "span", "missing_object", "duplicate_object"):
            fixture = self.small.copy()
            meta = fixture.doc["extras"]["ontokin"]
            if mutation == "entry":
                meta["source"]["entry_revision"] = "sha256:" + "0" * 64
            elif mutation == "program":
                meta["program"]["revision"] = "sha256:" + "0" * 64
            elif mutation == "class":
                fixture.doc["nodes"][0]["extras"]["ontokin"]["class_name"] = "wrong/class"
            elif mutation == "span":
                path = 'first.fingers["middle"]'
                for mapping in fixtures.base.mapping_copies(fixture.doc, path, "both"):
                    mapping["definition"]["start_byte"] += 1
            elif mutation == "missing_object":
                fixture.doc["nodes"].pop()
            else:
                fixture.doc["nodes"].append(copy.deepcopy(fixture.doc["nodes"][0]))
            self.refuse(fixture, label="equal hinges with bad provenance " + mutation)
        fixture = self.small.copy()
        fixture.sources["hinges.ok"] += b"\n// stale import pin\n"
        self.refuse(fixture, label="source-only stale pin and program binding", code="INPUT_BINDING")

    def test_absent_direct_provenance_and_unobserved_metadata(self):
        fixture = self.small.copy()
        meta = fixture.doc["extras"]["ontokin"]
        meta["module"] = {"unobserved": "wrong"}
        meta["scene"] = ["unobserved"]
        meta["program"]["collections"] = {"unobserved": "not qualified"}
        meta["source"]["uri"] = "untrusted locator"
        meta["follow"] = [{"unobserved": "not qualified"}]
        for node in fixture.doc["nodes"]:
            node.update(name="display only", translation=[100, 200, 300])
            node["extras"]["ontokin"].update(owner="unobserved", geometry={"unobserved": True})
        result = self.accept(fixture, label="unobserved metadata remains outside finite agreement")
        self.assertTrue(result["unobservedFields"])
        self.assertFalse(hasattr(comparison, "read_bound_endpoint"))
        for field in ("sites",):
            fixture.doc["extras"]["ontokin"][field] = []
            self.refuse(fixture, label="unsupported direct-site metadata", code="UNSUPPORTED_ARTIFACT_FORM")

    def test_nontrivial_source_site_pose_is_not_evaluated(self):
        fixture = fixtures.synthetic(edits=(("vec3(0[m], 0[m], 0[m]), quat(1, 0, 0, 0)",
                                             "vec3(999[m], -123[m], 0[m]), quat(0, 1, 0, 0)"),))
        self.accept(fixture, label="site pose witness retained without world-alignment inference")

    def test_source_compatibility_fields_refuse_when_unsupported_or_inconsistent(self):
        for old, new in (('interface = "hinged.part";', 'interface = "";'),
                         ("size = 0[m];", "size = -1[m];"),
                         ("size = 0[m];", "size = 1[m] + 0[m];")):
            self.refuse(fixtures.synthetic(edits=((old, new),)), label="source site compatibility " + new)
        fixture = fixtures.synthetic()
        sources = dict(fixture.sources)
        sources["hinges.ok"] = sources["hinges.ok"].replace(b'size = 0[m];', b'size = 1[m];', 1)
        sources["main.ok"] = sources["main.ok"].replace(fixtures.base.digest(fixture.sources["hinges.ok"]).encode(),
            fixtures.base.digest(sources["hinges.ok"]).encode())
        self.refuse(sources=sources, label="source sites unequal size before provenance", code="MALFORMED")

    def test_structural_source_and_numeric_bounds_propagate(self):
        for sources in ({}, {"main.ok": b""}, dict(self.small.sources, **{"extra.ok": b""}),
                        dict(self.small.sources, **{"main.ok": "not bytes"}), None):
            self.refuse(sources=sources, label="invalid source closure " + type(sources).__name__)
        oversized = dict(self.small.sources, **{"main.ok": b" " * 65537})
        exc = self.refuse(sources=oversized, label="source byte cap", code="RESOURCE_LIMIT")
        self.assertNotIn("main.ok", exc.sourceHashes)
        for literal in ("1" * 65 + "[rad]", "1e401[rad]", "1e-401[rad]"):
            self.refuse(fixtures.synthetic(source_initial=literal), label="bounded source numeric " + literal,
                        code="RESOURCE_LIMIT")

    def test_raw_glb_structural_duplicate_json_and_size_refusals(self):
        raw = self.small.raw
        for invalid in (None, bytearray(raw), "not bytes", raw[:11], raw[:-1], b"not a GLB"):
            self.refuse(raw=invalid, label="raw structural " + type(invalid).__name__)
        self.refuse(raw=b"\0" * (4 * 1024 * 1024 + 1), label="GLB byte cap", code="RESOURCE_LIMIT")
        doc = b'{"asset":{"version":"2.0"},"asset":{"version":"2.0"}}'
        doc += b" " * (-len(doc) % 4)
        duplicate = struct.pack("<III", 0x46546C67, 2, 28 + len(doc)) + struct.pack("<II", len(doc), 0x4E4F534A)
        duplicate += doc + struct.pack("<II", 0, 0x004E4942)
        self.refuse(raw=duplicate, label="duplicate JSON key", code="MALFORMED")
        for operation in ("missing", "extra"):
            fixture = self.small.copy()
            row = fixture.doc["extras"]["ontokin"]["joints"][0]
            if operation == "missing":
                row.pop("initial")
            else:
                row["definition_id"] = ["not-directly-observed"]
            self.refuse(fixture, label="joint row field " + operation, code="MALFORMED")

    def test_dependencies_are_admitted_each_call_and_symlinks_refuse(self):
        with tempfile.TemporaryDirectory(prefix="c267-controls-") as temporary:
            root = Path(temporary)
            target = root / "localized-repair-c267/hinge_compare.py"
            target.parent.mkdir()
            shutil.copyfile(HERE / "hinge_compare.py", target)
            for relative in DEPENDENCY_PATHS:
                destination = root / relative
                destination.parent.mkdir()
                shutil.copyfile(HERE.parent / relative, destination)
            isolated = fixtures.load_file("c267_isolated_public_api", target)
            self.accept(self.small, label="exact isolated dependency bytes", module=isolated)
            for relative in DEPENDENCY_PATHS:
                destination = root / relative
                exact = destination.read_bytes()
                destination.write_bytes(exact.replace(b" ", b"\t", 1))
                self.refuse(label="same-size changed dependency " + relative,
                            code="INPUT_BINDING", module=isolated)
                destination.write_bytes(exact)
            destination = root / DEPENDENCY_PATHS[0]
            exact = destination.read_bytes()
            destination.unlink()
            self.refuse(label="missing pinned dependency", code="INPUT_BINDING", module=isolated)
            external = root / "copied-exact-binding.py"
            external.write_bytes(exact)
            destination.symlink_to(external)
            self.refuse(label="symbolic-link pinned dependency", code="INPUT_BINDING", module=isolated)


def _code_identities():
    paths = [HERE / "hinge_compare.py", Path(__file__), HERE / "comparison_control_fixtures.py",
             HERE.parent / "localized-repair-c266/binding_control_fixtures.py"]
    paths += [HERE.parent / p for p in DEPENDENCY_PATHS]
    return {p.relative_to(fixtures.ROOT).as_posix(): {"bytes": p.stat().st_size,
            "sha256": fixtures.base.digest(p.read_bytes())} for p in paths}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-dir", type=Path)
    args = parser.parse_args()
    if args.evidence_dir is not None:
        args.evidence_dir.mkdir(parents=True, exist_ok=False)
    started = datetime.now(timezone.utc).isoformat()
    identities = _code_identities()
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(HingeComparisonControls))
    output = stream.getvalue()
    stable = identities == _code_identities()
    report = {"schema": "ontokin.c267.independent-comparison-controls/0.1",
              "startedAt": started, "completedAt": datetime.now(timezone.utc).isoformat(),
              "command": [sys.executable, "-B", str(Path(__file__).resolve()), *sys.argv[1:]],
              "python": sys.version, "platform": platform.platform(), "machine": platform.machine(),
              "implementationAndControlInputs": identities, "inputCodeStableDuringRun": stable,
              "testMethods": result.testsRun,
              "failures": [{"case": str(case), "traceback": trace} for case, trace in result.failures],
              "errors": [{"case": str(case), "traceback": trace} for case, trace in result.errors],
              "skipped": list(result.skipped), "passed": result.wasSuccessful() and stable,
              "apiCalls": len(CALLS), "agreementCalls": sum(c.get("outcome") == "agreement" for c in CALLS),
              "typedRefusals": sum(c.get("outcome") == "typed_refusal" for c in CALLS), "cases": CALLS,
              "limits": ["Finite source/artifact declaration comparison only",
                         "No historical file-admission API or full H01/H03/H04/H26 historical coverage",
                         "No source execution/export, site-pose, full validity, accepted revision or physical claim",
                         "Inherited controls cover remaining parser/resource boundaries separately"]}
    if args.evidence_dir is not None:
        (args.evidence_dir / "results.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        (args.evidence_dir / "unittest.txt").write_text(output, encoding="utf-8")
        snapshots = args.evidence_dir / "checked-code"
        snapshots.mkdir()
        for name in ("hinge_compare.py", "test_hinge_compare.py", "comparison_control_fixtures.py"):
            (snapshots / name).write_bytes((HERE / name).read_bytes())
        with zipfile.ZipFile(args.evidence_dir / "inputs.zip", "w", zipfile.ZIP_DEFLATED) as archive:
            for name, raw in sorted(INPUTS.items()):
                archive.writestr(name, raw)
    print(output, end="")
    print(json.dumps({k: report[k] for k in ("passed", "testMethods", "apiCalls", "agreementCalls", "typedRefusals",
                                           "inputCodeStableDuringRun")}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
