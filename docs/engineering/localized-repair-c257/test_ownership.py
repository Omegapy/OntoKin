#!/usr/bin/env python3
"""Hosted standard-library controls; no product or expected-semantics imports."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
spec = importlib.util.spec_from_file_location("c257_ownership", HERE / "ownership.py")
reader = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = reader
spec.loader.exec_module(reader)
PROOF = REPO / "docs/engineering/semantic-export-c210/evidence/proof"


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


def edit_glb(change, raw=None):
    document, tail = unpack(artifact() if raw is None else raw)
    change(document)
    return repack(document, tail)


def library_edit(s, old, new):
    s = s.copy()
    old_sha = hashlib.sha256(s["hinges.ok"]).hexdigest().encode()
    s["hinges.ok"] = s["hinges.ok"].replace(old, new)
    new_sha = hashlib.sha256(s["hinges.ok"]).hexdigest().encode()
    s["main.ok"] = s["main.ok"].replace(old_sha, new_sha)
    return s


def span(raw, marker):
    """Independent fixture-only balanced block locator; markers are unique."""
    start = raw.index(marker)
    opening = raw.index(b"{", start)
    depth = 1
    for end in range(opening+1, len(raw)):
        depth += (raw[end] == ord("{")) - (raw[end] == ord("}"))
        if depth == 0:
            return start, end+1
    raise AssertionError("fixture block not found")


def moved_blades():
    s = sources()
    beginning, end = span(s["hinges.ok"], b"private part blade")
    declaration = s["hinges.ok"][beginning:end]
    s = library_edit(s, declaration, b"")
    s = library_edit(s, b"private class Blade", b"public class Blade")
    new_part = b'\n    private part blade @ "blade": mech.Blade {}\n'
    rack_end = span(s["main.ok"], b"public class Rack")[1]
    s["main.ok"] = s["main.ok"][:rack_end-1]+new_part+s["main.ok"][rack_end-1:]
    return s


def source_binding(s):
    """Implement the documented manifest rule in the fixture, not the reader."""
    units = [{"source_id": "entry", "package_id": None, "version": None,
              "filename": "main.ok", "source_revision": "sha256:"+hashlib.sha256(s["main.ok"]).hexdigest()},
             {"source_id": "package:example.hinges@1.0.0", "package_id": "example.hinges", "version": "1.0.0",
              "filename": "hinges.ok", "source_revision": "sha256:"+hashlib.sha256(s["hinges.ok"]).hexdigest()}]
    manifest = {"schema_version": "ontokin.bundle/0.1", "entry_source_id": "entry", "units": units}
    encoded = json.dumps(manifest, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    return manifest, "sha256:"+hashlib.sha256(b"ontokin.bundle/0.1\0"+encoded).hexdigest()


def coordinated_move(s):
    """Manual fixture graph: two Rack roots, eight Fingers, two Rack-owned Blades.

    Ownership expectations and source spans are not read from reader output.
    Retained geometry/relationships are deliberately unqualified by this scope.
    """
    d, tail = unpack(artifact())
    original_nodes = d["nodes"]
    templates = {n["extras"]["ontokin"]["path"]: n for n in original_nodes}
    manifest, revision = source_binding(s)
    program = d["extras"]["ontokin"]["program"]
    program.update(manifest=manifest, revision=revision, occurrences={})
    for unit in manifest["units"]:
        program["sources"][unit["source_id"]].update(unit)
    d["extras"]["ontokin"]["source"]["entry_revision"] = manifest["units"][0]["source_revision"]
    nodes = []
    for root, keys in (("first", ["lower", "middle", "upper"]),
                       ("second", ["bottom", "lower", "middle", "upper", "top"])):
        specifications = [(root, ["keyed-rack", "demo", root], None, "rack")]
        specifications += [(root+'.fingers['+json.dumps(k)+']', ["keyed-rack", "demo", root, "fingers", k], root, "finger") for k in keys]
        specifications += [(root+".blade", ["keyed-rack", "demo", root, "blade"], root, "blade")]
        for path, oid, owner, kind in specifications:
            template = path if kind != "blade" else root+'.fingers["lower"].blade'
            node = copy.deepcopy(templates[template])
            meta = node["extras"]["ontokin"]
            definition_id = (["entry", "keyed-rack"] if kind == "rack" else ["package", "example.hinges", "hinges"])+["definitions", kind]
            meta.update(path=path, element_id=oid, owner=owner, program_revision=revision, class_name="/".join(definition_id))
            node["name"] = path
            mapping = meta["source_mapping"]
            mapping.update(path=path, element_id=oid, owner_path=owner, definition_id=definition_id,
                           class_id="/".join(definition_id), root_path=root)
            markers = {"rack": (b"object "+root.encode(), b"public class Rack", "main.ok"),
                       "finger": (b"public parts fingers", b"public class Finger", "hinges.ok"),
                       "blade": (b"private part blade", b"public class Blade", "hinges.ok")}
            declaration_marker, definition_marker, definition_file = markers[kind]
            for label, filename, marker in (("declaration", "main.ok", declaration_marker),
                                            ("definition", definition_file, definition_marker)):
                a, b = span(s[filename], marker)
                mapping[label] = {"source_id": "entry" if filename == "main.ok" else "package:example.hinges@1.0.0",
                    "source_revision": "sha256:"+hashlib.sha256(s[filename]).hexdigest(), "filename": filename,
                    "start_byte": a, "end_byte": b}
            program["occurrences"][path] = copy.deepcopy(mapping)
            nodes.append(node)
    d["nodes"] = nodes
    d["scenes"][0]["nodes"] = list(range(len(nodes)))
    return repack(d, tail)


class OwnershipTests(unittest.TestCase):
    def refused(self, call, code=None):
        with self.assertRaises(reader.Fault) as caught:
            call()
        if code is not None:
            self.assertEqual(code, caught.exception.code)

    def test_bound_original_endpoints(self):
        for endpoint in ("before", "after"):
            with self.subTest(endpoint=endpoint):
                result = reader.read_bound_endpoint(REPO, endpoint)
                self.assertEqual((18, 2, 16), (result["objectCount"], result["rootCount"], result["edgeCount"]))
                self.assertTrue(result["ownershipConsistent"])
                self.assertTrue(result["historicalInputsBound"])
                self.assertFalse(result["sourceValidityQualified"])
                self.assertFalse(result["completeC255Semantic"])
                self.assertFalse(result["executionAllowed"])
                self.assertIsNone(result["realTrialSuccess"])

    def test_ownership_is_distinct_from_transform_roots(self):
        d, _ = unpack(artifact())
        self.assertEqual(18, len(d["scenes"][0]["nodes"]))
        result = reader.compare_ownership(sources(), artifact())
        expected = {"first": ["lower", "middle", "upper"],
                    "second": ["bottom", "lower", "middle", "upper", "top"]}
        rows = {r["path"]: r for r in result["records"]}
        for root, keys in expected.items():
            self.assertIsNone(rows[root]["ownerId"])
            for k in keys:
                finger = root+'.fingers['+json.dumps(k)+']'
                self.assertEqual(["keyed-rack", "demo", root], rows[finger]["ownerId"])
                self.assertEqual(rows[finger]["id"], rows[finger+".blade"]["ownerId"])
        changed = edit_glb(lambda d: d["nodes"][0].update(children=[1, 2, 3]))
        self.assertTrue(reader.compare_ownership(sources(), changed)["ownershipConsistent"])
        self.assertFalse(reader.observe_glb_ownership(changed)["transformHierarchyUsedAsOwnership"])

    def test_source_containment_move_changes_observed_graph(self):
        result = reader.observe_source_ownership(moved_blades())
        self.assertEqual((12, 2, 10), (result["objectCount"], result["rootCount"], result["edgeCount"]))
        blades = [r for r in result["records"] if r["definitionId"][-1] == "blade"]
        self.assertEqual({"first.blade", "second.blade"}, {r["path"] for r in blades})
        self.assertEqual({"first", "second"}, {r["ownerPath"] for r in blades})
        self.refused(lambda: reader.compare_ownership(moved_blades(), artifact()), "SOURCE_ARTIFACT_BINDING")

    def test_jointly_changed_ownership_is_observed_without_historical_claim(self):
        s = moved_blades()
        result = reader.compare_ownership(s, coordinated_move(s))
        self.assertEqual(10, result["edgeCount"])
        self.assertTrue(result["ownershipConsistent"])
        self.assertFalse(result["historicalInputsBound"])
        self.assertFalse(result["sourceValidityQualified"])

    def test_import_resolution_does_not_guess_or_ignore_visibility(self):
        s = moved_blades()
        s["main.ok"] = s["main.ok"].replace(b': mech.Blade {}', b': Blade {}')
        self.refused(lambda: reader.observe_source_ownership(s), "UNKNOWN_DEFINITION")
        s = library_edit(moved_blades(), b"public class Blade", b"private class Blade")
        self.refused(lambda: reader.observe_source_ownership(s), "PRIVATE_DEFINITION")

    def test_module_visibility_defaults_public(self):
        for marker in (b"public class Finger", b"public fn three_mounts"):
            with self.subTest(marker=marker):
                s = library_edit(sources(), marker, marker.removeprefix(b"public "))
                self.assertEqual(18, reader.observe_source_ownership(s)["objectCount"])

    def test_source_byte_offsets_require_integer_types(self):
        for label in ("declaration", "definition"):
            for field in ("start_byte", "end_byte"):
                for location in ("sourceMapping", "programOccurrence"):
                    with self.subTest(label=label, field=field, location=location):
                        def change(d):
                            meta = d["nodes"][0]["extras"]["ontokin"]
                            mapping = meta["source_mapping"] if location == "sourceMapping" else d["extras"]["ontokin"]["program"]["occurrences"][meta["path"]]
                            mapping[label][field] = float(mapping[label][field])
                        self.refused(lambda: reader.compare_ownership(sources(), edit_glb(change)), "SOURCE_SPAN_BINDING")

    def test_duplicate_source_authority_and_class_id_claims_must_agree(self):
        for source_id in ("entry", "package:example.hinges@1.0.0"):
            for field, value in (("source_revision", "sha256:"+"0"*64), ("module_key", "wrong"), ("filename", "wrong.ok")):
                with self.subTest(source_id=source_id, field=field):
                    def change(d):
                        d["extras"]["ontokin"]["program"]["sources"][source_id][field] = value
                    self.refused(lambda: reader.compare_ownership(sources(), edit_glb(change)), "SOURCE_METADATA_BINDING")
        for mutation in (lambda o: o["program"].update(entry_source_id="wrong"),
                         lambda o: o["source"].update(entry_source_id="wrong"),
                         lambda o: o["source"].update(entry_revision="sha256:"+"0"*64),
                         lambda o: o.update(module="Wrong"), lambda o: o.update(scene="Wrong"),
                         lambda o: o.update(profile="wrong")):
            self.refused(lambda: reader.compare_ownership(sources(), edit_glb(lambda d: mutation(d["extras"]["ontokin"]))), "SOURCE_METADATA_BINDING")
        for location in ("node", "program"):
            def change(d):
                meta = d["nodes"][0]["extras"]["ontokin"]
                mapping = meta["source_mapping"] if location == "node" else d["extras"]["ontokin"]["program"]["occurrences"][meta["path"]]
                mapping["class_id"] = "wrong/class"
            self.refused(lambda: reader.compare_ownership(sources(), edit_glb(change)), "IDENTITY_MAPPING")

    def test_changed_literal_key_is_measured(self):
        s = library_edit(sources(), b'"lower":', b'"other.part":')
        result = reader.observe_source_ownership(s)
        ids = [r["id"] for r in result["records"]]
        self.assertIn(["keyed-rack", "demo", "first", "fingers", "other.part"], ids)
        self.assertNotIn(["keyed-rack", "demo", "first", "fingers", "lower"], ids)
        self.assertIn(["keyed-rack", "demo", "second", "fingers", "lower"], ids)

    def test_utf8_comments_preserve_actual_byte_origins(self):
        s = sources(); prefix = '// café λ: part object parts are comments\n'.encode()
        s["main.ok"] = prefix+s["main.ok"]
        result = reader.observe_source_ownership(s)
        row = next(r for r in result["records"] if r["path"] == "first")
        at = row["origin"]["declaration"]
        self.assertEqual(902+len(prefix), at["startByte"])
        self.assertTrue(s["main.ok"][at["startByte"]:at["endByteExclusive"]].startswith(b"object first"))
        for record in result["records"]:
            for origin in record["origin"]["identityKeys"]:
                value = json.loads(s[origin["file"]][origin["startByte"]:origin["endByteExclusive"]])
                self.assertIn(value, record["id"])

    def test_follow_hinge_and_parent_frame_changes_do_not_reassign_owners(self):
        s = library_edit(sources(), b"parent = self.parent_frame;", b"parent = world;")
        s = library_edit(s, b"parent = self.pivot;", b"parent = self.blade.base;")
        s["main.ok"] = s["main.ok"].replace(b"parent_frame = self.frame;", b"parent_frame = world;")
        before = reader.observe_source_ownership(sources())
        after = reader.observe_source_ownership(s)
        self.assertEqual([(r["id"], r["ownerId"]) for r in before["records"]],
                         [(r["id"], r["ownerId"]) for r in after["records"]])
        self.assertNotIn("follow", after)
        self.assertNotIn("hinge", after)

    def test_duplicate_and_dynamic_keys_refuse(self):
        for old, new in ((b'"lower":', b'"middle":'), (b'"lower":', b'key_name:')):
            with self.subTest(new=new):
                s = library_edit(sources(), old, new)
                self.refused(lambda: reader.observe_source_ownership(s))

    def test_unrecognized_ownership_and_shape_override_refuse(self):
        s = sources(); s["main.ok"] = s["main.ok"].replace(b"fingers[\"middle\"].length", b"fingers[\"middle\"].mounts")
        self.refused(lambda: reader.observe_source_ownership(s), "UNSUPPORTED_SHAPE_OVERRIDE")
        s = library_edit(sources(), b"return tween", b"object hidden @ \"hidden\": Blade {} return tween")
        self.refused(lambda: reader.observe_source_ownership(s), "UNSUPPORTED_OWNERSHIP_POSITION")

    def test_cycles_and_unresolved_classes_refuse(self):
        s = library_edit(sources(), b': Blade {', b': Finger {')
        self.refused(lambda: reader.observe_source_ownership(s), "OWNERSHIP_CYCLE")
        s = sources(); s["main.ok"] = s["main.ok"].replace(b": mech.Finger for", b": mech.Missing for")
        self.refused(lambda: reader.observe_source_ownership(s), "UNKNOWN_DEFINITION")

    def test_raw_metadata_reports_mutated_claim_before_compare_rejects(self):
        def change(d):
            target = next(n for n in d["nodes"] if n["name"] == 'first.fingers["lower"].blade')
            target["extras"]["ontokin"]["owner"] = "second"
        changed = edit_glb(change)
        row = next(r for r in reader.observe_glb_ownership(changed)["records"] if r["path"] == 'first.fingers["lower"].blade')
        self.assertEqual("second", row["claims"]["nodeOwner"])
        self.refused(lambda: reader.compare_ownership(sources(), changed), "OWNERSHIP_MISMATCH")

    def test_all_owner_representations_require_agreement_and_presence(self):
        for key in ("node", "mapping", "program"):
            for missing in (False, True):
                with self.subTest(key=key, missing=missing):
                    def change(d):
                        meta = d["nodes"][0]["extras"]["ontokin"]
                        target = meta if key == "node" else meta["source_mapping"] if key == "mapping" else d["extras"]["ontokin"]["program"]["occurrences"][meta["path"]]
                        field = "owner" if key == "node" else "owner_path"
                        if missing:
                            del target[field]
                        else:
                            target[field] = "second"
                    self.refused(lambda: reader.compare_ownership(sources(), edit_glb(change)))

    def test_identity_and_source_mapping_tampering_refuse(self):
        mutations = [lambda m: m.update(element_id=["invented"]),
                     lambda m: m["source_mapping"].update(definition_id=["wrong"]),
                     lambda m: m["source_mapping"]["declaration"].update(start_byte=0),
                     lambda m: m["source_mapping"]["declaration"].update(source_id="wrong"),
                     lambda m: m["source_mapping"]["definition"].update(source_revision="sha256:"+"0"*64)]
        for index, mutation in enumerate(mutations):
            with self.subTest(index=index):
                changed = edit_glb(lambda d: mutation(d["nodes"][0]["extras"]["ontokin"]))
                self.refused(lambda: reader.compare_ownership(sources(), changed))

    def test_duplicate_identity_and_extra_occurrence_refuse(self):
        changed = edit_glb(lambda d: d["nodes"].append(copy.deepcopy(d["nodes"][0])))
        self.refused(lambda: reader.observe_glb_ownership(changed), "DUPLICATE_IDENTITY")
        def extra(d):
            p = d["extras"]["ontokin"]["program"]["occurrences"]
            p["unknown"] = copy.deepcopy(p["first"])
        self.refused(lambda: reader.observe_glb_ownership(edit_glb(extra)), "OCCURRENCE_COVERAGE")

    def test_binding_requires_actual_source_and_complete_manifest(self):
        s = sources(); s["main.ok"] += b"\n"
        self.refused(lambda: reader.compare_ownership(s, artifact()), "SOURCE_ARTIFACT_BINDING")
        changed = edit_glb(lambda d: d["extras"]["ontokin"]["program"]["manifest"]["units"][0].update(filename="other.ok"))
        self.refused(lambda: reader.compare_ownership(sources(), changed), "SOURCE_ARTIFACT_BINDING")
        s = sources(); s["hinges.ok"] += b"\n"
        self.refused(lambda: reader.observe_source_ownership(s), "IMPORT_BINDING")

    def test_malformed_shapes_are_explicit_refusals(self):
        for mutation in (lambda d: d.update(asset=[]), lambda d: d.update(nodes=[]),
                         lambda d: d["nodes"][0].update(extras=[]),
                         lambda d: d["extras"]["ontokin"].update(program=[]),
                         lambda d: d["extras"]["ontokin"]["program"].update(occurrences=[])):
            with self.subTest(mutation=mutation):
                self.refused(lambda: reader.observe_glb_ownership(edit_glb(mutation)))
        for raw in (b"", b"bad", artifact()[:-1]):
            self.refused(lambda: reader.observe_glb_ownership(raw))

    def test_resource_and_source_limits_refuse(self):
        self.refused(lambda: reader.observe_source_ownership({"main.ok": b"x"*65537, "hinges.ok": b"x"}), "SOURCE_SIZE")
        self.refused(lambda: reader.observe_glb_ownership(b"x"*(reader.MAX_GLB_BYTES+1)), "GLB_SIZE")
        s = sources(); s["main.ok"] += b";"*(reader.MAX_TOKENS+1)
        self.refused(lambda: reader.observe_source_ownership(s), "TOKEN_LIMIT")
        s = sources(); s["main.ok"] += b"("*33+b")"*33
        self.refused(lambda: reader.observe_source_ownership(s), "SOURCE_DEPTH")
        s = sources(); s["main.ok"] = s["main.ok"].replace(b'"bottom":', b'"'+b"k"*513+b'":')
        self.refused(lambda: reader.observe_source_ownership(s), "TEXT")

    def test_historical_route_rejects_changed_bytes_without_claiming_restore(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)/reader.PROOF; target.mkdir(parents=True)
            for name in ("before.main.ok", "hinges.ok", "before.glb"):
                (target/name).write_bytes((PROOF/name).read_bytes())
            self.assertTrue(reader.read_bound_endpoint(temporary, "before")["historicalInputsBound"])
            changed = bytearray(artifact()); changed[-1] ^= 1
            (target/"before.glb").write_bytes(changed)
            self.refused(lambda: reader.read_bound_endpoint(temporary, "before"), "HISTORICAL_BINDING")

    def test_public_file_api_normalizes_io_failures(self):
        self.refused(lambda: reader.read_bound_endpoint("/tmp/ontokin-c257-static-probe-"+"x"*5000, "before"), "IO")


if __name__ == "__main__":
    unittest.main(verbosity=2)
