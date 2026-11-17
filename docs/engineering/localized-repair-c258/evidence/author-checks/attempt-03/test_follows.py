#!/usr/bin/env python3
"""Finite hosted controls; no product, sidecar or C255 expected-answer imports."""
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PROOF = REPO / "docs/engineering/semantic-export-c210/evidence/proof"
spec = importlib.util.spec_from_file_location("c258_follows", HERE / "follows.py")
reader = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = reader
spec.loader.exec_module(reader)


def sources(endpoint="before"):
    return {"main.ok": (PROOF / (endpoint+".main.ok")).read_bytes(),
            "hinges.ok": (PROOF / "hinges.ok").read_bytes()}


def artifact(endpoint="before"):
    return (PROOF / (endpoint+".glb")).read_bytes()


def unpack(raw):
    size = struct.unpack_from("<I", raw, 12)[0]
    return json.loads(raw[20:20+size]), raw[20+size:]


def repack(document, tail):
    chunk = json.dumps(document, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()
    chunk += b" "*((-len(chunk)) % 4)
    return struct.pack("<III", 0x46546C67, 2, 20+len(chunk)+len(tail))+struct.pack("<II", len(chunk), 0x4E4F534A)+chunk+tail


def edited(change, raw=None):
    document, tail = unpack(artifact() if raw is None else raw)
    change(document)
    return repack(document, tail)


def library_edit(s, old, new):
    s = s.copy()
    old_sha = hashlib.sha256(s["hinges.ok"]).hexdigest().encode()
    assert old in s["hinges.ok"]
    s["hinges.ok"] = s["hinges.ok"].replace(old, new)
    new_sha = hashlib.sha256(s["hinges.ok"]).hexdigest().encode()
    s["main.ok"] = s["main.ok"].replace(old_sha, new_sha)
    return s


def block_span(raw, marker):
    """Independent fixture locator: fixed markers and balanced ASCII braces."""
    start = raw.index(marker)
    opening = raw.index(b"{", start)
    depth = 1
    for end in range(opening+1, len(raw)):
        depth += (raw[end] == ord("{"))-(raw[end] == ord("}"))
        if depth == 0:
            return start, end+1
    raise AssertionError("unclosed fixture block")


def rebind(s, raw=None):
    """Rebind unchanged object identities from bytes, not reader observations.

    Geometry, motion, joints and unused property copies remain deliberately
    unqualified. Each control separately supplies its changed follow fields.
    """
    document, tail = unpack(artifact() if raw is None else raw)
    units = [{"source_id": "entry", "package_id": None, "version": None,
              "filename": "main.ok", "source_revision": "sha256:"+hashlib.sha256(s["main.ok"]).hexdigest()},
             {"source_id": "package:example.hinges@1.0.0", "package_id": "example.hinges", "version": "1.0.0",
              "filename": "hinges.ok", "source_revision": "sha256:"+hashlib.sha256(s["hinges.ok"]).hexdigest()}]
    manifest = {"schema_version": "ontokin.bundle/0.1", "entry_source_id": "entry", "units": units}
    encoded = json.dumps(manifest, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    revision = "sha256:"+hashlib.sha256(b"ontokin.bundle/0.1\0"+encoded).hexdigest()
    top = document["extras"]["ontokin"]
    program = top["program"]
    program.update(revision=revision, manifest=manifest)
    for unit in units:
        program["sources"][unit["source_id"]].update(unit)
    top["source"]["entry_revision"] = units[0]["source_revision"]
    for node in document["nodes"]:
        meta = node["extras"]["ontokin"]
        meta["program_revision"] = revision
        path = meta["path"]
        root = path.split(".", 1)[0]
        kind = "blade" if path.endswith(".blade") else "finger" if ".fingers[" in path else "rack"
        declarations = {"rack": ("main.ok", b"object "+root.encode()),
                        "finger": ("main.ok", b"public parts fingers"),
                        "blade": ("hinges.ok", b"private part blade")}
        definitions = {"rack": ("main.ok", b"public class Rack"),
                       "finger": ("hinges.ok", b"public class Finger"),
                       "blade": ("hinges.ok", b"private class Blade")}
        mapping = meta["source_mapping"]
        for label, (filename, marker) in (("declaration", declarations[kind]), ("definition", definitions[kind])):
            a, b = block_span(s[filename], marker)
            mapping[label] = {"source_id": "entry" if filename == "main.ok" else "package:example.hinges@1.0.0",
                "filename": filename, "source_revision": "sha256:"+hashlib.sha256(s[filename]).hexdigest(),
                "start_byte": a, "end_byte": b}
        program["occurrences"][path] = copy.deepcopy(mapping)
    return repack(document, tail)


def follow_rows(document):
    return document["extras"]["ontokin"]["follows"]


def set_child_property(document, path, name, value):
    node = next(n for n in document["nodes"] if n["extras"]["ontokin"]["path"] == path)
    node["extras"]["ontokin"]["properties"][name] = value


class FollowTests(unittest.TestCase):
    def refused(self, call, code=None):
        with self.assertRaises(reader.Fault) as caught:
            call()
        if code:
            self.assertEqual(code, caught.exception.code)
        return caught.exception

    def test_original_endpoint_values_and_full_identities(self):
        for endpoint in ("before", "after"):
            result = reader.read_bound_endpoint(REPO, endpoint)
            self.assertTrue(result["historicalInputsBound"])
            self.assertTrue(result["followConsistent"])
            self.assertEqual(8, result["followCount"])
            wanted = {"first": {"lower": -.6, "middle": 0, "upper": .6},
                      "second": {"bottom": -1.2, "lower": -.6, "middle": 0, "upper": .6, "top": 1.2}}
            for row in result["records"]:
                root, key = row["id"][2], row["id"][4]
                self.assertEqual(["keyed-rack", "demo", root, "fingers", key, "mounting"], row["id"])
                self.assertEqual(["package", "example.hinges", "hinges", "definitions", "finger", "mounting"], row["definitionId"])
                self.assertEqual([0, wanted[root][key], 0], row["offsetPositionM"])
                self.assertEqual([1, 0, 0, 0], row["offsetRotationWxyz"])
                self.assertEqual(["keyed-rack", "demo", root], row["parentFrame"]["objectId"])

    def test_authority_gaps_and_policy_are_explicit(self):
        result = reader.read_bound_endpoint(REPO, "before")
        for key in ("completeC255Semantic", "executionAllowed", "jointUnionQualified", "sourceValidityQualified"):
            self.assertFalse(result[key])
        for key in ("realTrialSuccess", "artifactFollowDefinitionAuthority", "artifactFollowSourceSpanAuthority"):
            self.assertIsNone(result[key])
        self.assertFalse(result["comparisonPolicy"]["exporterErrorBoundClaimed"])
        self.assertEqual(8, result["comparisonPolicy"]["componentUlps"])
        raw = reader.observe_glb_follows(artifact())
        self.assertFalse(raw["sourceAssociationVerified"])
        self.assertFalse(raw["historicalInputsBound"])

    def test_origins_use_actual_utf8_bytes_and_pointers(self):
        s = sources()
        s["main.ok"] = b"// \xc3\xa9 utf8\n"+s["main.ok"]
        s = library_edit(s, b"module Hinges", b"// \xe7\x95\x8c\nmodule Hinges")
        result = reader.compare_follows(s, rebind(s))
        for row in result["records"]:
            at = row["sourceOrigins"]["declaration"]
            fragment = s[at["file"]][at["startByte"]:at["endByteExclusive"]]
            self.assertTrue(fragment.startswith(b"public follow mounting"))
            self.assertTrue(fragment.endswith(b"}"))
            for at in row["sourceOrigins"]["identity"]:
                self.assertEqual(int, type(at["startByte"]))
                self.assertTrue(s[at["file"]][at["startByte"]:at["endByteExclusive"]].startswith(b'"'))
            self.assertTrue(row["artifactOrigins"]["parent_frame"].startswith("/extras/ontokin/follows/"))

    def test_lexical_owner_initializer_and_actual_child_default(self):
        s = sources()
        s["main.ok"] = s["main.ok"].replace(b"        parent_frame = self.frame;\n", b"")
        result = reader.observe_source_follows(s)
        self.assertTrue(all(x["parentFrame"]["kind"] == "world" for x in result["records"]))
        self.refused(lambda: reader.compare_follows(s, artifact()))
        def change(d):
            for row in follow_rows(d):
                row["parent_frame"] = "world"
                set_child_property(d, row["child_object"], "parent_frame", {"type": "FrameRef", "value": "world"})
        raw = rebind(s, edited(change))
        self.assertTrue(reader.compare_follows(s, raw)["followConsistent"])

    def test_changed_helper_is_measured_and_jointly_bound(self):
        s = sources()
        s["main.ok"] = s["main.ok"].replace(b"three_mounts(0.6[m])", b"three_mounts(0.25[m])")
        rows = reader.observe_source_follows(s)["records"]
        self.assertEqual([-.25, 0, .25], [r["offsetPositionM"][1] for r in rows if r["id"][2] == "first"])
        self.assertEqual(1.2, next(r for r in rows if r["id"][2:5] == ["second", "fingers", "top"])["offsetPositionM"][1])
        def change(d):
            for row in follow_rows(d):
                if row["element_id"][2] == "first":
                    y = {"lower": -.25, "middle": 0, "upper": .25}[row["element_id"][4]]
                    row["offset_position_m"] = [0, y, 0]
                    set_child_property(d, row["child_object"], "mount_offset", {"type": "Vec3<Length>",
                        "value": [{"type": "Length", "value": n} for n in [0, y, 0]]})
        measured = reader.observe_glb_follows(edited(change))
        self.assertEqual(-.25, measured["records"][0]["offsetPositionM"][1])
        self.refused(lambda: reader.compare_follows(s, rebind(s)))
        self.assertTrue(reader.compare_follows(s, rebind(s, edited(change)))["followConsistent"])

    def test_canonical_unit_conversion_rounds_once(self):
        baseline = reader.observe_source_follows(sources())
        for before, after in ((b"0.6[m]", b"60[cm]"), (b"0.6[m]", b"600[mm]"), (b"1.2[m]", b"1200[mm]")):
            s = sources()
            s["main.ok"] = s["main.ok"].replace(before, after)
            result = reader.observe_source_follows(s)
            self.assertEqual([r["offsetPositionM"] for r in baseline["records"]], [r["offsetPositionM"] for r in result["records"]])
            self.assertTrue(reader.compare_follows(s, rebind(s))["followConsistent"])

    def test_relation_name_and_key_are_read(self):
        s = library_edit(sources(), b'follow mounting @ "mounting"', b'follow carried @ "carrier"')
        result = reader.observe_source_follows(s)
        self.assertTrue(all(r["path"].endswith(".carried") and r["id"][-1] == "carrier" for r in result["records"]))
        def change(d):
            for row in follow_rows(d):
                row["path"] = row["child_object"]+".carried"
                row["element_id"][-1] = "carrier"
        self.assertTrue(reader.compare_follows(s, rebind(s, edited(change)))["followConsistent"])

    def test_literal_rotation_normalization_and_common_sign(self):
        s = library_edit(sources(), b"self.mount_offset, quat(1, 0, 0, 0)", b"self.mount_offset, quat(0.6, 0.8, 0, 0)")
        result = reader.observe_source_follows(s)
        self.assertEqual([.6, .8, 0, 0], result["records"][0]["offsetRotationWxyz"])
        def change(d):
            for row in follow_rows(d):
                row["offset_rotation_wxyz"] = [-.6, -.8, 0, 0]
        self.assertTrue(reader.compare_follows(s, rebind(s, edited(change)))["followConsistent"])
        negative = library_edit(s, b"quat(0.6, 0.8, 0, 0)", b"quat(-0.6, -0.8, 0, 0)")
        self.assertEqual([.6, .8, 0, 0], reader.observe_source_follows(negative)["records"][0]["offsetRotationWxyz"])

    def test_projection_handles_subnormal_and_canonical_sign(self):
        tiny = math.ulp(0.0)
        self.assertEqual([1, tiny, 0, 0], reader.normalized_quaternion([1, tiny, 0, 0]))
        self.assertEqual([0, 1, 0, 0], reader.normalized_quaternion([0, -1, 0, 0]))
        self.assertEqual([1, 0, 0, 0], reader.normalized_quaternion([1.0000000000005, 0, 0, 0]))

    def test_artifact_rotation_policy_boundary_and_no_repair(self):
        expected = [.6, .8, 0, 0]
        eight = .6
        for _ in range(8):
            eight = math.nextafter(eight, math.inf)
        self.assertTrue(reader.quaternion_agrees([eight, .8, 0, 0], expected))
        self.assertFalse(reader.quaternion_agrees([math.nextafter(eight, math.inf), .8, 0, 0], expected))
        self.assertFalse(reader.quaternion_agrees([.6, .8, math.ulp(0), 0], expected))
        self.assertFalse(reader.quaternion_agrees([.6, -.8, 0, 0], expected))
        self.refused(lambda: reader.quaternion_agrees([1.01, 0, 0, 0], [1, 0, 0, 0]), "QUATERNION_NORM")

    def test_source_and_artifact_invalid_quaternions_refuse(self):
        for tuple_ in (b"0, 0, 0, 0", b"1.0001, 0, 0, 0", b"1, 1, 0, 0"):
            s = library_edit(sources(), b"self.mount_offset, quat(1, 0, 0, 0)", b"self.mount_offset, quat("+tuple_+b")")
            self.refused(lambda: reader.observe_source_follows(s), "QUATERNION_NORM")
        for q in ([0, 0, 0, 0], [2, 0, 0, 0], [True, 0, 0, 0]):
            self.refused(lambda: reader.observe_glb_follows(edited(lambda d: follow_rows(d)[0].update(offset_rotation_wxyz=q))))

    def test_offset_frame_identity_and_follow_cycles(self):
        s = library_edit(sources(), b"offset = pose(self.parent_frame", b"offset = pose(world")
        self.refused(lambda: reader.observe_source_follows(s), "OFFSET_FRAME")
        s = library_edit(sources(), b"parent = self.parent_frame;", b"parent = self.frame;")
        s = library_edit(s, b"offset = pose(self.parent_frame", b"offset = pose(self.frame")
        self.refused(lambda: reader.observe_source_follows(s), "FOLLOW_CYCLE")
        self.refused(lambda: reader.observe_glb_follows(edited(lambda d: follow_rows(d)[0].update(
            parent_frame=follow_rows(d)[0]["child_object"]+".frame"))), "FOLLOW_CYCLE")

    def test_parameter_type_visibility_and_module_default(self):
        for before, after in ((b"public param parent_frame", b"private param parent_frame"),
                              (b"parent-frame\": FrameRef", b"parent-frame\": String"),
                              (b"public param mount_offset", b"param mount_offset")):
            s = library_edit(sources(), before, after)
            self.refused(lambda: reader.observe_source_follows(s))
        s = library_edit(sources(), b"public class Finger", b"class Finger")
        s = library_edit(s, b"public fn three_mounts", b"fn three_mounts")
        self.assertEqual(8, reader.observe_source_follows(s)["followCount"])
        private = library_edit(sources(), b"public fn three_mounts", b"private fn three_mounts")
        self.refused(lambda: reader.observe_source_follows(private))

    def test_name_key_visibility_and_binder_ambiguity(self):
        for before, after in ((b'public follow mounting @ "mounting"', b'follow mounting @ "mounting"'),
                              (b'follow mounting @ "mounting"', b'follow world @ "mounting"'),
                              (b'follow mounting @ "mounting"', b'follow mounting @ "pivot"')):
            s = library_edit(sources(), before, after)
            self.refused(lambda: reader.observe_source_follows(s))
        s = sources()
        s["main.ok"] = s["main.ok"].replace(b"for (key, offset)", b"for (offset, offset)")
        self.refused(lambda: reader.observe_source_follows(s))

    def test_follow_affecting_nested_overrides_refuse(self):
        s = sources()
        s["main.ok"] = s["main.ok"].replace(b'fingers["middle"].length = 0.65[m]', b'fingers["middle"].parent_frame = world')
        self.refused(lambda: reader.observe_source_follows(s), "UNSUPPORTED_NESTED_OVERRIDE")
        s = library_edit(sources(), b"    public param parent_frame", b'    private param ancestor @ "ancestor": FrameRef = self.parent_frame;\n    public param parent_frame')
        s = library_edit(s, b"parent = self.parent_frame;", b"parent = self.ancestor;")
        s = library_edit(s, b"offset = pose(self.parent_frame", b"offset = pose(self.ancestor")
        s["main.ok"] = s["main.ok"].replace(b'fingers["middle"].length = 0.65[m]', b'fingers["middle"].parent_frame = world')
        self.refused(lambda: reader.observe_source_follows(s), "UNSUPPORTED_NESTED_OVERRIDE")

    def test_implicit_instance_members_cannot_be_redeclared_or_assigned(self):
        for name in ("frame", "origin", "geometry", "physical", "motion", "placement"):
            s = library_edit(sources(), b'public class Finger @ "finger" {',
                             b'public class Finger @ "finger" {\n    public param '+name.encode()+
                             b' @ "fake-member": FrameRef = world;')
            self.refused(lambda: reader.observe_source_follows(s), "INSTANCE_MEMBER_COLLISION")
        s = sources()
        s["main.ok"] = s["main.ok"].replace(b'public class Rack @ "rack" {',
            b'public class Rack @ "rack" {\n public param frame @ "fake-frame": FrameRef = world;')
        self.refused(lambda: reader.observe_source_follows(s), "INSTANCE_MEMBER_COLLISION")
        for name in ("frame", "origin", "misspelled_field"):
            s = library_edit(sources(), b'public class Finger @ "finger" {',
                b'public class Finger @ "finger" {\n    '+name.encode()+b' = world;')
            self.refused(lambda: reader.observe_source_follows(s), "C257_UNSUPPORTED_MEMBER")
            s = sources()
            s["main.ok"] = s["main.ok"].replace(b"parent_frame = self.frame;", b"parent_frame = self.frame; "+name.encode()+b" = world;")
            self.refused(lambda: reader.observe_source_follows(s), "INITIALIZER_TARGET")
        for before, after in ((b"site pivot", b"site origin"), (b"follow mounting", b"follow frame")):
            s = library_edit(sources(), before, after)
            self.refused(lambda: reader.observe_source_follows(s), "INSTANCE_MEMBER_COLLISION")
        s = library_edit(sources(), b'public class Finger @ "finger" {',
            b'public class Finger @ "finger" {\n physical = no_body(); motion = prescribed;')
        s = library_edit(s, b'follow mounting @ "mounting"', b'follow mounting @ "frame"')
        self.assertEqual(8, reader.observe_source_follows(s)["followCount"])

    def test_child_admission_and_unsupported_child(self):
        for extra in (b"physical = sphere_body(1[kg], 1[m]);", b"motion = dynamic;", b"placement = pose(world, vec3(0[m], 0[m], 0[m]), quat(1,0,0,0));"):
            s = library_edit(sources(), b'public class Finger @ "finger" {', b'public class Finger @ "finger" {\n'+extra)
            self.refused(lambda: reader.observe_source_follows(s))
        s = library_edit(sources(), b"child = self;", b"child = self.blade;")
        self.refused(lambda: reader.observe_source_follows(s), "UNSUPPORTED_CHILD")

    def test_unsupported_expression_forms_and_numeric_units(self):
        for term in (b"0.6[m]+0[m]", b"0.6[s]", b"+0.6[m]", b"01[m]", b"0.6[ft]"):
            s = sources()
            s["main.ok"] = s["main.ok"].replace(b"three_mounts(0.6[m])", b"three_mounts("+term+b")")
            self.refused(lambda: reader.observe_source_follows(s))
        s = library_edit(sources(), b"parent = self.parent_frame;", b"parent = self.pivot;")
        self.refused(lambda: reader.observe_source_follows(s))

    def test_metadata_changed_translation_is_measured_then_rejected(self):
        raw = edited(lambda d: follow_rows(d)[0].update(offset_position_m=[0, -0.5, 0]))
        self.assertEqual([0, -.5, 0], reader.observe_glb_follows(raw)["records"][0]["offsetPositionM"])
        self.refused(lambda: reader.compare_follows(sources(), raw), "FOLLOW_MISMATCH")

    def test_metadata_identity_frame_missing_and_extra_rows(self):
        changes = [lambda d: follow_rows(d)[0].update(parent_frame="first.frame.other"),
                   lambda d: follow_rows(d)[0].update(child_object="unknown"),
                   lambda d: follow_rows(d)[0].update(element_id=["wrong"]),
                   lambda d: follow_rows(d)[0].update(path="wrong.mounting"),
                   lambda d: follow_rows(d)[0].update(unencoded_definition_id=["invented"]),
                   lambda d: follow_rows(d).append(copy.deepcopy(follow_rows(d)[0]))]
        for change in changes:
            self.refused(lambda: reader.observe_glb_follows(edited(change)))
        raw = edited(lambda d: follow_rows(d).pop())
        self.assertEqual(7, reader.observe_glb_follows(raw)["followCount"])
        self.refused(lambda: reader.compare_follows(sources(), raw), "FOLLOW_COVERAGE")

    def test_duplicate_property_copies_must_agree_only_when_used(self):
        def change(d):
            path = follow_rows(d)[0]["child_object"]
            set_child_property(d, path, "parent_frame", {"type": "FrameRef", "value": "world"})
        raw = edited(change)
        self.assertEqual(8, reader.observe_glb_follows(raw)["followCount"])
        self.refused(lambda: reader.compare_follows(sources(), raw), "PROPERTY_VALUE")
        raw = edited(lambda d: set_child_property(d, follow_rows(d)[0]["child_object"], "mount_offset", {"type": "Vec3<Length>", "value": []}))
        self.refused(lambda: reader.compare_follows(sources(), raw), "PROPERTY_VALUE")
        raw = edited(lambda d: set_child_property(d, follow_rows(d)[0]["child_object"], "length", {"type": "Length", "value": 999}))
        self.assertTrue(reader.compare_follows(sources(), raw)["followConsistent"])

    def test_duplicate_source_authority_and_spans_must_agree(self):
        changes = [lambda d: d["extras"]["ontokin"]["program"]["sources"]["entry"].update(source_revision="sha256:"+"0"*64),
                   lambda d: d["nodes"][2]["extras"]["ontokin"]["source_mapping"].update(class_id="wrong"),
                   lambda d: d["nodes"][2]["extras"]["ontokin"]["source_mapping"]["declaration"].update(start_byte=603.0)]
        for change in changes:
            self.refused(lambda: reader.compare_follows(sources(), edited(change)))

    def test_malformed_public_inputs_refuse(self):
        for source in (None, [], {"main.ok": b""}, {"main.ok": "not bytes", "hinges.ok": b""}):
            self.refused(lambda: reader.observe_source_follows(source))
        for raw in (None, [], b"", b"glTF", artifact()[:-1], b"x"*(4*1024*1024+1)):
            self.refused(lambda: reader.observe_glb_follows(raw))
        for bad in (None, {}, [None], [[]], [True]):
            self.refused(lambda: reader.observe_glb_follows(edited(lambda d: d["extras"]["ontokin"].update(follows=bad))))

    def test_numeric_exponent_preallocation_limits(self):
        for term in (b"1e999999999[m]", b"1e-999999999[m]", b"0e999999999[m]", b"1e309[m]", b"1e-325[m]", b"1e-324[mm]"):
            s = sources()
            s["main.ok"] = s["main.ok"].replace(b"three_mounts(0.6[m])", b"three_mounts("+term+b")")
            self.refused(lambda: reader.observe_source_follows(s), "NUMERIC_EXPONENT")

    def test_resource_limits_and_input_io(self):
        s = sources()
        s["main.ok"] += b" "*65536
        self.refused(lambda: reader.observe_source_follows(s))
        self.refused(lambda: reader.observe_glb_follows(edited(lambda d: d["extras"]["ontokin"].update(follows=[None]*129))), "FOLLOW_LIMIT")
        self.refused(lambda: reader.read_bound_endpoint("/tmp/c258-"+"x"*5000, "before"), "IO")
        self.refused(lambda: reader.read_bound_endpoint(REPO, "missing"), "ENDPOINT")

    def test_bound_api_rejects_equal_size_changed_actual_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)/"docs/engineering/semantic-export-c210/evidence/proof"
            directory.mkdir(parents=True)
            for name in ("before.main.ok", "hinges.ok", "before.glb"):
                (directory/name).write_bytes((PROOF/name).read_bytes())
            target = directory/"before.main.ok"
            target.write_bytes(target.read_bytes().replace(b"three_mounts(0.6[m])", b"three_mounts(0.5[m])"))
            self.refused(lambda: reader.read_bound_endpoint(temp, "before"), "HISTORICAL_BINDING")

    def test_hinge_and_world_motion_remain_unqualified(self):
        s = library_edit(sources(), b"axis = vec3(0, 0, 1)", b"axis = vec3(1, 0, 0)")
        rows = reader.compare_follows(s, rebind(s))
        self.assertTrue(rows["followConsistent"])
        self.assertFalse(rows["jointUnionQualified"])
        self.assertFalse(rows["completeC255Semantic"])
        self.assertEqual(8, rows["followCount"])


if __name__ == "__main__":
    unittest.main()
