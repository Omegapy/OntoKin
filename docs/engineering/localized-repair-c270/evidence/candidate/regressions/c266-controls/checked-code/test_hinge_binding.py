"""Independent public-API controls for the C266 input-binding prerequisite.

Expected source/program/object maps come from binding_control_fixtures.py and
the adopted construction rules. This suite never calls implementation-private
helpers or a producer/parser/exporter/sidecar/C257 comparator. No complete
C260 H group or hinge comparison is qualified by these controls.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import io
import json
import platform
import struct
import sys
import unittest
import zipfile
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent


def load_file(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


fixtures = load_file("c266_independent_fixtures", HERE / "binding_control_fixtures.py")
binding = load_file("c266_public_binding_under_test", HERE / "hinge_binding.py")
CALLS = []
INPUTS = {}


def _record_bytes(raw, extension: str):
    if not isinstance(raw, bytes):
        return {"type": type(raw).__name__}
    value = hashlib.sha256(raw).hexdigest()
    INPUTS.setdefault(value + extension, raw)
    return {"bytes": len(raw), "sha256": value, "snapshot": "inputs.zip!" + value + extension}


def _leaves(value, path=()):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _leaves(child, path + (key,))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _leaves(child, path + (index,))
    else:
        yield path, value


def _containers(value, path=()):
    if isinstance(value, (dict, list)):
        yield path, value
        children = value.items() if isinstance(value, dict) else enumerate(value)
        for key, child in children:
            yield from _containers(child, path + (key,))


def _set(value, path, replacement):
    for key in path[:-1]:
        value = value[key]
    value[path[-1]] = replacement


def _get(value, path):
    for key in path:
        value = value[key]
    return value


def _different(value):
    if value is None:
        return "contradictory-null"
    if isinstance(value, bool):
        return not value
    if isinstance(value, int):
        return value + 1
    if isinstance(value, str):
        return value + "-different"
    raise AssertionError("Unexpected independently authored leaf")


class BindingControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.small = fixtures.synthetic()

    def call(self, source_files, raw, *, label: str, expected: str):
        entry = {"case": self.id(), "label": label, "expected": expected,
                 "sourceInputs": {name: _record_bytes(value, ".ok") for name, value in source_files.items()}
                 if isinstance(source_files, dict) else {"type": type(source_files).__name__},
                 "artifactInput": _record_bytes(raw, ".glb")}
        CALLS.append(entry)
        try:
            result = binding.bind_hinge_inputs(source_files, raw)
        except binding.Fault as exc:
            entry.update(outcome="typed_refusal", code=exc.code,
                         detail=getattr(exc, "detail", str(exc)), pointer=getattr(exc, "pointer", None),
                         sourceHashes=getattr(exc, "sourceHashes", None),
                         sourceBytes=getattr(exc, "sourceBytes", None),
                         artifactSha256=getattr(exc, "artifactSha256", None),
                         artifactBytes=getattr(exc, "artifactBytes", None))
            raise
        except Exception as exc:
            entry.update(outcome="untyped_exception", exception=type(exc).__name__, detail=str(exc))
            raise
        entry.update(outcome="bound", objectCount=result.get("objectCount"),
                     programRevision=result.get("programRevision"),
                     flags={key: value for key, value in result.items() if isinstance(value, bool)})
        return result

    def accept(self, fixture, *, label="supported fixture", raw=None):
        supplied_raw = fixture.raw if raw is None else raw
        sources_before = copy.deepcopy(fixture.sources)
        result = self.call(fixture.sources, supplied_raw, label=label, expected="binding")
        self.assertEqual(fixture.sources, sources_before, "Public API mutated supplied source mapping")
        self.assertEqual(result["objectCount"], len(fixture.expected))
        self.assertEqual(result["artifactBytes"], len(supplied_raw))
        self.assertEqual(result["artifactSha256"], fixtures.digest(supplied_raw))
        self.assertEqual(result["sourceHashes"], {k: fixtures.digest(v) for k, v in fixture.sources.items()})
        self.assertEqual(result["sourceBytes"], {k: len(v) for k, v in fixture.sources.items()})
        manifest, revision = fixtures.program_identity(fixture.sources)
        self.assertEqual(result["sourceManifest"], manifest)
        self.assertEqual(result["programRevision"], revision)
        self.assertIs(result["inputBindingVerified"], True)
        for key in ("hingeComparisonVerified", "hingeSetAgreementVerified", "endpointAgreementVerified",
                    "historicalInputsBound"):
            self.assertIs(result[key], False)
        for key in ("executionAllowed", "completeC255Semantic", "acceptedRevisionVerified",
                    "sitePosesEvaluated", "physicalValidityVerified"):
            self.assertFalse(result.get(key, False))
        self.assertNotIn("hinges", result)
        self.assertNotIn("qualifiedHinges", result)
        records = {row["path"]: row for row in result["records"]}
        self.assertEqual(set(records), set(fixture.expected))
        self.assertEqual(len(records), len(result["records"]))
        for path, expected in fixture.expected.items():
            self.assertEqual(records[path]["id"], expected["element_id"])
            self.assertEqual(records[path]["definitionId"], expected["definition_id"])
            self.assertEqual(records[path]["mapping"], expected)
        return result

    def refuse(self, fixture=None, *, label, source_files=None, raw=None, code=None):
        fixture = self.small if fixture is None else fixture
        sources = fixture.sources if source_files is None else source_files
        artifact = fixture.raw if raw is None else raw
        with self.assertRaises(binding.Fault) as caught:
            self.call(sources, artifact, label=label, expected="refusal")
        exc = caught.exception
        self.assertIn(exc.code, {"MALFORMED", "INPUT_BINDING", "UNSUPPORTED_SOURCE_FORM",
                               "UNSUPPORTED_ARTIFACT_FORM", "RESOURCE_LIMIT", "IO_ERROR"})
        if code is not None:
            self.assertEqual(exc.code, code)
        self.assertIsInstance(exc.detail, str)
        self.assertTrue(exc.detail)
        return exc

    def test_original_before_and_after_all_objects(self):
        for endpoint in ("before", "after"):
            with self.subTest(endpoint=endpoint):
                fixture = fixtures.original(endpoint)
                self.assertEqual(len(fixture.expected), 18)
                self.assertEqual(fixture.expected,
                    fixture.doc["extras"]["ontokin"]["program"]["occurrences"])
                raw = (fixtures.PROOF / (endpoint + ".glb")).read_bytes()
                self.accept(fixture, label="exact original " + endpoint, raw=raw)

    def test_changed_membership_and_opaque_keys(self):
        cases = [(("one",), ("two",)),
                 (("k.z", "k_z", "k-z"), ("alpha", "omega", "extra")),
                 (("upper", "lower", "middle"), ("top", "bottom")),
                 (("a", "b", "c", "d"), ("last",))]
        for first, second in cases:
            with self.subTest(first=first, second=second):
                self.accept(fixtures.synthetic(first_keys=first, second_keys=second),
                            label="independent membership " + repr((first, second)))

    def test_direct_helper_and_final_override_memberships(self):
        for mode in ("helper_default", "direct_default", "helper_override", "final_override"):
            with self.subTest(mode=mode):
                self.accept(fixtures.synthetic(mode=mode), label=mode)

    def test_renamed_names_separate_from_punctuation_keys(self):
        self.accept(fixtures.synthetic(renamed=True, first_keys=("a.b", "a_b", "a-b")),
                    label="renamed modules/classes/members/roots and punctuation keys")

    def test_unicode_offsets_are_utf8_bytes(self):
        for mode in ("helper_default", "direct_default", "helper_override", "final_override"):
            with self.subTest(mode=mode):
                fixture = fixtures.synthetic(unicode_prefix=True, renamed=True, mode=mode)
                self.accept(fixture, label="Unicode before all spans " + mode)
                first = next(iter(fixture.expected))
                mapping = fixture.expected[first]
                start = mapping["declaration"]["start_byte"]
                self.assertNotEqual(start, len(fixture.sources["main.ok"][:start].decode("utf-8")))

    def test_every_repeated_provenance_leaf_node_program_and_both(self):
        representatives = ("first", 'first.fingers["middle"]', 'first.fingers["middle"].blade')
        for path in representatives:
            for leaf_path, original in _leaves(self.small.expected[path]):
                for copies in ("node", "program", "both"):
                    label = f"{path} {copies} {leaf_path}"
                    with self.subTest(label=label):
                        fixture = self.small.copy()
                        for mapping in fixtures.mapping_copies(fixture.doc, path, copies):
                            _set(mapping, leaf_path, _different(original))
                        self.refuse(fixture, label=label)

    def test_every_mapping_member_is_required_in_each_copy(self):
        path = 'first.fingers["middle"]'
        for container_path, container in _containers(self.small.expected[path]):
            if not isinstance(container, dict):
                continue
            for field in container:
                for copies in ("node", "program", "both"):
                    label = f"missing {copies} {container_path + (field,)}"
                    with self.subTest(label=label):
                        fixture = self.small.copy()
                        for mapping in fixtures.mapping_copies(fixture.doc, path, copies):
                            del _get(mapping, container_path)[field]
                        self.refuse(fixture, label=label)

    def test_unknown_mapping_members_refuse_at_every_dictionary(self):
        path = 'first.fingers["middle"]'
        for container_path, container in _containers(self.small.expected[path]):
            if not isinstance(container, dict):
                continue
            for copies in ("node", "program", "both"):
                label = f"unknown {copies} {container_path}"
                with self.subTest(label=label):
                    fixture = self.small.copy()
                    for mapping in fixtures.mapping_copies(fixture.doc, path, copies):
                        _get(mapping, container_path)["unrecognized_authority"] = "must not be silently admitted"
                    self.refuse(fixture, label=label)

    def test_mapping_containers_require_their_actual_types(self):
        path = 'first.fingers["middle"]'
        for container_path, container in _containers(self.small.expected[path]):
            for copies in ("node", "program", "both"):
                label = f"wrong container {copies} {container_path}"
                with self.subTest(label=label):
                    fixture = self.small.copy()
                    for mapping in fixtures.mapping_copies(fixture.doc, path, copies):
                        if container_path:
                            _set(mapping, container_path, [] if isinstance(container, dict) else {})
                        else:
                            mapping.clear()
                    self.refuse(fixture, label=label)

    def test_python_numeric_equality_does_not_admit_wrong_json_types(self):
        path = 'first.fingers["middle"]'
        for leaf_path, original in _leaves(self.small.expected[path]):
            if not isinstance(original, (int, bool)):
                continue
            wrong = int(original) if isinstance(original, bool) else float(original)
            for copies in ("node", "program", "both"):
                label = f"type equality {copies} {leaf_path}"
                with self.subTest(label=label):
                    fixture = self.small.copy()
                    for mapping in fixtures.mapping_copies(fixture.doc, path, copies):
                        _set(mapping, leaf_path, wrong)
                    self.refuse(fixture, label=label)

    def test_full_input_entry_span_cannot_be_replaced_with_key_token(self):
        for mode in ("helper_default", "direct_default", "helper_override", "final_override"):
            with self.subTest(mode=mode):
                fixture = fixtures.synthetic(mode=mode, key_tokens=True)
                self.refuse(fixture, label="full entry shortened to key token " + mode)

    def test_nested_root_and_owner_paths_are_not_display_hints(self):
        path = 'first.fingers["middle"].blade'
        for field, wrong in (("root_path", "second"), ("owner_path", "first"),
                             ("generated_ancestor", 'second.fingers["bottom"]')):
            with self.subTest(field=field):
                fixture = self.small.copy()
                for mapping in fixtures.mapping_copies(fixture.doc, path, "both"):
                    mapping[field] = wrong
                self.refuse(fixture, label="both copies forged " + field)

    def test_all_program_manifest_and_source_unit_claims(self):
        program = self.small.doc["extras"]["ontokin"]["program"]
        for section in ("manifest", "sources"):
            for leaf_path, value in _leaves(program[section]):
                label = section + repr(leaf_path)
                with self.subTest(label=label):
                    fixture = self.small.copy()
                    _set(fixture.doc["extras"]["ontokin"]["program"][section], leaf_path, _different(value))
                    self.refuse(fixture, label="canonical program/source leaf " + label)

    def test_sparse_and_unknown_program_manifest_source_units(self):
        for section in ("manifest", "sources"):
            original = self.small.doc["extras"]["ontokin"]["program"][section]
            for path, value in _containers(original):
                if not isinstance(value, dict):
                    continue
                for field in value:
                    with self.subTest(section=section, path=path, field=field):
                        fixture = self.small.copy()
                        target = fixture.doc["extras"]["ontokin"]["program"][section]
                        del _get(target, path)[field]
                        self.refuse(fixture, label="missing source manifest member " + repr((section, path, field)))
                fixture = self.small.copy()
                target = fixture.doc["extras"]["ontokin"]["program"][section]
                _get(target, path)["unknown"] = "not canonical"
                self.refuse(fixture, label="unknown source manifest member " + repr((section, path)))

    def test_program_manifest_unit_order_is_canonical(self):
        fixture = self.small.copy()
        fixture.doc["extras"]["ontokin"]["program"]["manifest"]["units"].reverse()
        self.refuse(fixture, label="noncanonical unit array order")

    def test_entry_and_program_revisions_and_source_ids(self):
        for section, field in (("source", "entry_source_id"), ("source", "entry_revision"),
                               ("program", "entry_source_id"), ("program", "revision")):
            for operation in ("stale", "missing", "wrong_type"):
                with self.subTest(section=section, field=field, operation=operation):
                    fixture = self.small.copy()
                    target = fixture.doc["extras"]["ontokin"][section]
                    if operation == "missing":
                        del target[field]
                    else:
                        target[field] = "stale" if operation == "stale" else False
                    self.refuse(fixture, label="entry/program " + repr((section, field, operation)))

    def test_every_node_scalar_claim_against_source(self):
        path = 'first.fingers["middle"]'
        for field in ("path", "element_id", "class_name", "program_revision"):
            with self.subTest(field=field):
                fixture = self.small.copy()
                claim = fixtures.node_claim(fixture.doc, path)
                claim[field] = ["wrong"] if field == "element_id" else "wrong"
                self.refuse(fixture, label="node scalar " + field)

    def test_missing_object_from_both_artifact_tables(self):
        fixture = self.small.copy()
        path = 'first.fingers["middle"].blade'
        fixture.doc["nodes"] = [n for n in fixture.doc["nodes"] if n["extras"]["ontokin"]["path"] != path]
        del fixture.doc["extras"]["ontokin"]["program"]["occurrences"][path]
        self.refuse(fixture, label="missing source object from both tables")

    def test_extra_object_in_both_artifact_tables(self):
        fixture = self.small.copy()
        node = copy.deepcopy(fixture.doc["nodes"][0])
        claim = node["extras"]["ontokin"]
        claim["path"] = "phantom"
        claim["element_id"] = ["keyed-rack", "demo", "phantom"]
        claim["source_mapping"]["path"] = "phantom"
        claim["source_mapping"]["element_id"] = claim["element_id"]
        fixture.doc["nodes"].append(node)
        fixture.doc["extras"]["ontokin"]["program"]["occurrences"]["phantom"] = copy.deepcopy(claim["source_mapping"])
        self.refuse(fixture, label="extra artifact object in both tables")

    def test_duplicate_object_id_and_path(self):
        for duplicate in ("element_id", "path"):
            fixture = self.small.copy()
            first = fixture.doc["nodes"][0]["extras"]["ontokin"]
            second = fixture.doc["nodes"][1]["extras"]["ontokin"]
            second[duplicate] = copy.deepcopy(first[duplicate])
            self.refuse(fixture, label="duplicate node " + duplicate)

    def test_consistent_renaming_of_claimed_path_without_source_refuses(self):
        fixture = self.small.copy()
        old, new = "first", "impostor"
        claim = fixtures.node_claim(fixture.doc, old)
        claim["path"] = new
        claim["source_mapping"]["path"] = new
        occurrences = fixture.doc["extras"]["ontokin"]["program"]["occurrences"]
        occurrences[new] = occurrences.pop(old)
        occurrences[new]["path"] = new
        self.refuse(fixture, label="both tables agree on unbacked rename")

    def test_node_and_mapping_order_do_not_define_identity(self):
        fixture = self.small.copy()
        fixture.doc["nodes"].reverse()
        program = fixture.doc["extras"]["ontokin"]["program"]
        program["occurrences"] = dict(reversed(list(program["occurrences"].items())))
        program["sources"] = dict(reversed(list(program["sources"].items())))
        result = self.accept(fixture, label="node/occurrence/source-map insertion order reversed")
        positions = {n["extras"]["ontokin"]["path"]: i for i, n in enumerate(fixture.doc["nodes"])}
        for record in result["records"]:
            self.assertEqual(record["node"], positions[record["path"]])

    def test_stale_source_bytes_and_dependency_pin(self):
        fixture = self.small.copy()
        changed = dict(fixture.sources)
        changed["main.ok"] += b"\n// changed actual source\n"
        self.refuse(fixture, source_files=changed, label="changed entry with stale artifact")
        changed = dict(fixture.sources)
        changed["hinges.ok"] += b"\n// changed dependency\n"
        self.refuse(fixture, source_files=changed, label="changed dependency with stale import pin")
        changed["main.ok"] = changed["main.ok"].replace(
            fixtures.digest(fixture.sources["hinges.ok"]).encode(), fixtures.digest(changed["hinges.ok"]).encode())
        self.refuse(fixture, source_files=changed, label="re-pinned dependency with stale artifact")

    def test_duplicate_owner_override_remains_a_refusal(self):
        fixture = fixtures.synthetic(mode="final_override")
        sources = dict(fixture.sources)
        marker = b'object first @ "first": Rack {'
        sources["main.ok"] = sources["main.ok"].replace(
            marker, marker + b' mounts = keyed<Vec3<Length>> {"duplicate": vec3(0[m], 0[m], 0[m])};')
        self.refuse(fixture, source_files=sources, label="duplicate same-scope owner override", code="MALFORMED")

    def test_crossed_original_endpoint_provenance_refuses(self):
        fixture = fixtures.original("before")
        raw = (fixtures.PROOF / "after.glb").read_bytes()
        self.refuse(fixture, raw=raw, label="before source against after artifact")

    def test_changed_hinge_fields_can_still_bind(self):
        for field, value in (("initial", 0.25), ("axis", [0, 0, -1]),
                             ("limits", [-1, 1]), ("parent_site", "unassociated.path"),
                             ("child_site", "another.path"), ("path", "different.hinge"),
                             ("element_id", ["different", "hinge"])):
            with self.subTest(field=field):
                fixture = fixtures.original()
                fixture.doc["extras"]["ontokin"]["joints"][0][field] = value
                self.accept(fixture, label="unqualified hinge field " + field)

    def test_omitted_added_and_reordered_hinges_can_still_bind(self):
        for operation in ("remove_one", "remove_all", "add_unassociated", "reverse"):
            fixture = fixtures.original()
            rows = fixture.doc["extras"]["ontokin"]["joints"]
            if operation == "remove_one":
                rows.pop()
            elif operation == "remove_all":
                rows.clear()
            elif operation == "reverse":
                rows.reverse()
            else:
                new = copy.deepcopy(rows[0])
                new["path"] = "unassociated.new_hinge"
                new["element_id"] = ["unassociated", "new-hinge"]
                rows.append(new)
            self.accept(fixture, label="unqualified hinge membership " + operation)

    def test_unobserved_metadata_cannot_be_promoted_to_authority(self):
        fixture = self.small.copy()
        ontokin = fixture.doc["extras"]["ontokin"]
        ontokin["module"] = {"invented": "unobserved"}
        ontokin["scene"] = ["unobserved"]
        ontokin["program"]["collections"] = {"invented": "unobserved"}
        ontokin["source"]["uri"] = "untrusted locator"
        ontokin["source"]["provenance"] = "not independent truth"
        for node in fixture.doc["nodes"]:
            node["name"] = "display only"
            node["translation"] = [42, 31, 17]
            claim = node["extras"]["ontokin"]
            claim["owner"] = "unobserved ownership"
            claim["geometry"] = {"kind": "unobserved"}
        self.accept(fixture, label="top-level and unrelated metadata explicitly unobserved")

    def test_sparse_object_mapping_is_not_partial_success(self):
        fixture = self.small.copy()
        path = 'first.fingers["middle"]'
        for mapping in fixtures.mapping_copies(fixture.doc, path, "both"):
            mapping.clear()
        self.refuse(fixture, label="empty repeated object maps")

    def test_bounded_available_identity_retained_on_binding_refusal(self):
        fixture = self.small.copy()
        fixture.doc["extras"]["ontokin"]["source"]["entry_revision"] = "sha256:" + "0" * 64
        raw = fixture.raw
        exc = self.refuse(fixture, raw=raw, label="identity on stale binding refusal")
        self.assertEqual(exc.sourceHashes, {k: fixtures.digest(v) for k, v in fixture.sources.items()})
        self.assertEqual(exc.sourceBytes, {k: len(v) for k, v in fixture.sources.items()})
        self.assertEqual(exc.artifactSha256, fixtures.digest(raw))
        self.assertEqual(exc.artifactBytes, len(raw))

    def test_source_and_artifact_size_limits_remain_bounded(self):
        oversized = b" " * (65536 + 1)
        sources = dict(self.small.sources, **{"main.ok": oversized})
        exc = self.refuse(source_files=sources, label="source byte limit", code="RESOURCE_LIMIT")
        self.assertNotEqual((getattr(exc, "sourceHashes", {}) or {}).get("main.ok"), fixtures.digest(oversized))
        raw = b"\0" * (4 * 1024 * 1024 + 1)
        exc = self.refuse(raw=raw, label="GLB byte limit", code="RESOURCE_LIMIT")
        self.assertIsNone(getattr(exc, "artifactSha256", None))
        self.assertEqual(exc.artifactBytes, len(raw))

    def test_missing_extra_and_nonbyte_sources_refuse(self):
        for source in ({}, {"main.ok": self.small.sources["main.ok"]},
                       dict(self.small.sources, **{"extra.ok": b""}),
                       dict(self.small.sources, **{"main.ok": "text, not bytes"}), []):
            with self.subTest(source_type=type(source).__name__):
                self.refuse(source_files=source, label="invalid supplied source closure " + repr(type(source)))

    def test_nonbyte_artifact_and_structural_failures_are_typed(self):
        raw = self.small.raw
        for value in (bytearray(raw), "not bytes", raw[:11], raw[:-1], b"not a GLB"):
            with self.subTest(value_type=type(value).__name__, size=len(value)):
                self.refuse(raw=value, label="invalid raw GLB " + repr((type(value).__name__, len(value))))

    def test_unsupported_source_and_raw_profile_are_not_bypassed(self):
        fixture = self.small.copy()
        sources = dict(fixture.sources)
        sources["hinges.ok"] = sources["hinges.ok"].replace(b"initial = 0[rad]", b"initial = 1[rad] + 0[rad]")
        sources["main.ok"] = sources["main.ok"].replace(
            fixtures.digest(fixture.sources["hinges.ok"]).encode(), fixtures.digest(sources["hinges.ok"]).encode())
        self.refuse(source_files=sources, label="unsupported source expression")
        fixture.doc["extras"]["ontokin"]["sites"] = []
        self.refuse(fixture, label="raw direct-site extension unsupported")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-dir", type=Path)
    args = parser.parse_args()
    if args.evidence_dir is not None:
        args.evidence_dir.mkdir(parents=True, exist_ok=False)
    stream = io.StringIO()
    started = datetime.now(timezone.utc).isoformat()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(BindingControls))
    output = stream.getvalue()
    print(output, end="")
    identities = {}
    for path in (HERE / "hinge_binding.py", Path(__file__), HERE / "binding_control_fixtures.py",
                 HERE.parent / "localized-repair-c265/source_hinges.py",
                 HERE.parent / "localized-repair-c261/hinge_glb.py",
                 HERE.parent / "localized-repair-c257/ownership.py"):
        raw = path.read_bytes()
        identities[str(path.relative_to(fixtures.ROOT))] = {"bytes": len(raw), "sha256": fixtures.digest(raw)}
    report = {"schema": "ontokin.c266.independent-input-binding-controls/0.1",
              "startedAt": started, "completedAt": datetime.now(timezone.utc).isoformat(),
              "command": [sys.executable, "-B", str(Path(__file__).resolve()), *sys.argv[1:]],
              "python": sys.version, "platform": platform.platform(), "machine": platform.machine(),
              "implementationAndControlInputs": identities, "testMethods": result.testsRun,
              "failures": [{"case": str(case), "traceback": trace} for case, trace in result.failures],
              "errors": [{"case": str(case), "traceback": trace} for case, trace in result.errors],
              "skipped": list(result.skipped), "passed": result.wasSuccessful(),
              "apiCalls": len(CALLS), "boundCalls": sum(c["outcome"] == "bound" for c in CALLS),
              "typedRefusals": sum(c["outcome"] == "typed_refusal" for c in CALLS),
              "cases": CALLS,
              "limits": ["Input-binding prerequisite only", "No complete C260 H group qualified",
                         "No hinge-set, field or endpoint agreement", "No source execution/export performed",
                         "No historical admission, site-pose, full validity, accepted-revision or physical claim"]}
    if args.evidence_dir is not None:
        (args.evidence_dir / "results.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        (args.evidence_dir / "unittest.txt").write_text(output, encoding="utf-8")
        snapshots = args.evidence_dir / "checked-code"
        snapshots.mkdir()
        for name in ("hinge_binding.py", "test_hinge_binding.py", "binding_control_fixtures.py"):
            (snapshots / name).write_bytes((HERE / name).read_bytes())
        with zipfile.ZipFile(args.evidence_dir / "inputs.zip", "w", zipfile.ZIP_DEFLATED) as archive:
            for name, raw in sorted(INPUTS.items()):
                archive.writestr(name, raw)
    print(json.dumps({k: report[k] for k in ("passed", "testMethods", "apiCalls", "boundCalls", "typedRefusals")}))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
