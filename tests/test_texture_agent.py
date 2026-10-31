"""Exercise real durable source/image edits, exact retrieval and current authority."""
from __future__ import annotations

import base64
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ontokin.agent_cli import _decode
from ontokin.agent_protocol import ProtocolError
from ontokin.bundle import BundleError, load_bundle
from ontokin.execution_budget import HostPolicy
from ontokin.pockets_protocol import PocketsProtocol
from ontokin.program_bindings import PROGRAM_BINDINGS, PROFILE_BINDINGS
from ontokin.texture_agent import TextureAgentService
from ontokin.texture_bundle import load_texture_bundle, load_texture_file_manifest
from ontokin.texture_protocol import MAX_REQUEST_BYTES, TextureProtocol, canonical_request


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "examples/textured-surfaces"
PROTOCOL, PROFILE, TARGET = "ontokin.agent/0.13", "textured-surfaces-0.1", "ontokin.glb/0.13"
PROJECT = "textures"
SHAPE = ["texture-case", "demo", "shape"]
OPTIONS = {"fps": 4, "end": "1", "helpers": False}


def source(name="rgb-panel"):
    return load_texture_file_manifest(FIXTURES / (name + ".files.json"))


def exact_patch(program, before, after):
    offset = program.entry.raw.index(before.encode())
    return {"source_id": "entry", "source_revision": program.entry.revision,
        "element_id": ["sources", "entry"], "start_byte": offset,
        "end_byte": offset + len(before.encode()), "expected_text": before, "replacement": after}


def descriptor(asset_id, raw):
    return {"asset_id": asset_id, "sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
        "media_type": "image/png", "data_base64": base64.b64encode(raw).decode("ascii")}


class TextureAgentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from jsonschema import Draft202012Validator
        from referencing import Registry, Resource
        paths = list((ROOT / "docs/language-design/agent-v0.13").glob("*.schema.json"))
        paths += [ROOT / "docs/language-design" / name for name in (
            "textured-surfaces-v0.1/bundle.schema.json", "textured-surfaces-v0.1/files.schema.json",
            "agent-v0.2/diagnostic.schema.json", "force-v0.1/forces.schema.json",
            "impulse-v0.1/impulses.schema.json",
            "planar-reach-v0.1/schema-drafts/reach-projection.schema.json",
            "planar-reach-v0.1/schema-drafts/reach-diagnostic.schema.json",
            "planar-reach-v0.1/schema-drafts/common.schema.json")]
        schemas = [json.loads(path.read_text()) for path in paths]
        registry = Registry().with_resources((item["$id"], Resource.from_contents(item)) for item in schemas)
        for item in schemas:
            Draft202012Validator.check_schema(item)
        cls.validators = {path.name: Draft202012Validator(item, registry=registry)
                          for path, item in zip(paths, schemas)}

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="ontokin-c080-agent-")
        self.service = TextureAgentService(self.directory.name)
        self.serial = 0

    def tearDown(self):
        self.service.close()
        self.directory.cleanup()

    def request(self, operation, **fields):
        self.serial += 1
        return {"schema_version": PROTOCOL, "project_id": PROJECT,
                "request_id": f"textures-{self.serial}", "operation": operation, **fields}

    def send(self, operation, **fields):
        request = self.request(operation, **fields)
        self.validators["request.schema.json"].validate(request)
        TextureProtocol.validate_request(request)
        return self.service.handle(request)

    def success(self, response):
        self.assertEqual(response["schema_version"], PROTOCOL, response)
        self.assertEqual(response["status"], "succeeded", response)
        self.validators["response.schema.json"].validate(response)
        return response

    def error(self, response, code):
        self.assertIn(response["status"], ("rejected", "failed"), response)
        self.validators["response.schema.json"].validate(response)
        codes = [item["code"] for item in response["diagnostics"]]
        if response["protocol_error"]:
            codes.append(response["protocol_error"]["code"])
        self.assertIn(code, codes, response)
        return response

    def create(self, program=None):
        program = source() if program is None else program
        result = self.success(self.send("create", bundle=program.to_payload(),
            expected_program_revision=None, requested_level="constructed"))
        self.assertEqual(result["accepted_program_revision"], program.program_revision)
        return program

    def metadata(self, revision, *, selector=None, **fields):
        return self.success(self.send("inspect", program_revision=revision,
            selector={"kind": "texture_asset"} if selector is None else selector,
            fields=["identity", "source"], limit=fields.pop("limit", 1000), **fields))

    def image_bytes(self, revision, asset_id="label", *, count=13):
        chunks, offset = [], 0
        while True:
            response = self.metadata(revision, selector={"element_id": ["assets", asset_id]},
                                     asset_slice={"offset": offset, "max_bytes": count})
            item = response["result"]
            raw = base64.b64decode(item["data_base64"], validate=True)
            self.assertEqual(item["offset"], offset)
            self.assertEqual(item["returned_bytes"], len(raw))
            self.assertEqual(item["program_revision"], revision)
            self.assertEqual(item["element_id"], ["assets", asset_id])
            self.assertIsNone(response["next_cursor"])
            chunks.append(raw)
            if item["complete"]:
                self.assertIsNone(item["next_offset"])
                break
            self.assertEqual(item["next_offset"], offset + len(raw))
            offset = item["next_offset"]
        data = b"".join(chunks)
        self.assertEqual(len(data), item["total_bytes"])
        self.assertEqual("sha256:" + hashlib.sha256(data).hexdigest(), item["sha256"])
        return data

    def retained(self):
        with self.service._store.connection() as db:
            return {"accepted": self.service.accepted_revision(PROJECT),
                "runs": [tuple(row) for row in db.execute("SELECT * FROM runs ORDER BY id")],
                "artifacts": [tuple(row) for row in db.execute("SELECT * FROM artifacts ORDER BY id")]}

    def test_explicit_discovery_and_store_leave_previous_bindings_strict(self):
        result = self.success(self.send("discover", profile=PROFILE, limit=1000))["result"]
        current = result["textured_surfaces_interface"]
        self.assertEqual(current["operations"], sorted(TextureProtocol.OPERATIONS))
        self.assertEqual(len(current["operations"]), 12)
        self.assertEqual(current["max_request_bytes"], 8388608)
        self.assertEqual(current["defaults"], {"max_operations": 100000, "max_elapsed_ms": 30000})
        self.assertEqual(current["source_schema"], "ontokin.bundle/0.2")
        for item in result["items"]:
            if item["kind"] == "protocol":
                self.assertEqual(item["name"], PROTOCOL)
                self.assertIn("TextureAgentService", item["signature"])
            elif item["kind"] == "destination":
                self.assertEqual(item["name"], TARGET)
                self.assertEqual(item["capability"], TARGET)
        current["host_ceilings"]["max_operations"] = 1
        self.service.host_policy = HostPolicy(200000, 80000)
        fresh = self.success(self.send("discover", profile=PROFILE, limit=1000))["result"]
        self.assertEqual(fresh["textured_surfaces_interface"]["host_ceilings"], self.service.host_policy.ceilings)
        self.assertEqual(self.service.database_path.name, "texture-program-agent.sqlite3")
        self.assertEqual(self.service._store.schema_version, "ontokin.texture-program-agent-store/0.1")
        self.assertNotIn(PROTOCOL, PROGRAM_BINDINGS)
        self.assertNotIn(PROFILE, PROFILE_BINDINGS)
        with self.assertRaises(BundleError):
            load_bundle(source().to_payload())
        legacy = self.request("create", bundle=source().to_payload(),
            expected_program_revision=None, requested_level="constructed")
        legacy["schema_version"] = PocketsProtocol.SCHEMA_VERSION
        with self.assertRaises(ProtocolError):
            PocketsProtocol.validate_request(legacy)

    def test_complete_request_byte_boundary_and_old_transport_limit(self):
        request = self.request("create", bundle=source().to_payload(),
            expected_program_revision=None, requested_level="constructed")
        request["bundle"]["entry"]["source"] += "\n// "
        wire = json.dumps(request, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
        quotient, remainder = divmod(MAX_REQUEST_BYTES - len(wire), 6)
        request["bundle"]["entry"]["source"] += "\0" * quotient + " " * remainder
        self.assertLess(len(request["bundle"]["entry"]["source"].encode()), 2000000)
        normalized, wire = canonical_request(request)
        self.assertEqual(len(wire.encode()), MAX_REQUEST_BYTES)
        self.assertEqual(_decode(wire.encode(), max_request_bytes=MAX_REQUEST_BYTES), normalized)
        with self.assertRaises(ProtocolError) as old:
            _decode(wire.encode())
        self.assertEqual(old.exception.code, "OKA-E-RESOURCE")
        request["bundle"]["entry"]["source"] += " "
        with self.assertRaises(ProtocolError) as oversized:
            canonical_request(request)
        self.assertEqual(oversized.exception.code, "OKA-E-RESOURCE")
        with self.assertRaises(ProtocolError) as raw_oversized:
            _decode(wire.encode() + b" ", max_request_bytes=MAX_REQUEST_BYTES)
        self.assertEqual(raw_oversized.exception.code, "OKA-E-RESOURCE")

    def test_source_only_edit_keeps_exact_png_and_source_unit_identity_rules(self):
        program = self.create()
        updated = program.entry.text + "\n// preserved attachment\n"
        response = self.success(self.send("edit", expected_program_revision=program.program_revision,
            requested_level="constructed", patches=[exact_patch(program, program.entry.text, updated)]))
        saved = self.service.read_program(PROJECT, response["program_revision"])
        self.assertNotEqual(saved.program_revision, program.program_revision)
        self.assertEqual(saved.entry.revision, "sha256:" + hashlib.sha256(updated.encode()).hexdigest())
        self.assertEqual(saved.assets, program.assets)
        self.assertEqual(self.image_bytes(saved.program_revision), program.assets[0].raw)

    def test_asset_replacement_and_source_digest_commit_as_one_candidate(self):
        program = self.create()
        replacement = descriptor("label", (FIXTURES / "assets/asymmetric-rgba.png").read_bytes())
        change = {"operation": "replace", "asset_id": "label",
                  "expected_sha256": program.assets[0].sha256, "asset": replacement}
        before = self.retained()
        self.error(self.send("edit", expected_program_revision=program.program_revision,
            requested_level="constructed", patches=[], asset_changes=[change]), "OKL-E-ASSET-CLOSURE")
        self.assertEqual(self.retained(), before)
        self.assertEqual(self.image_bytes(program.program_revision), program.assets[0].raw)
        response = self.success(self.send("edit", expected_program_revision=program.program_revision,
            requested_level="constructed", asset_changes=[change],
            patches=[exact_patch(program, program.assets[0].sha256, replacement["sha256"])]))
        saved = self.service.read_program(PROJECT, response["program_revision"])
        self.assertEqual(saved.assets[0].sha256, replacement["sha256"])
        self.assertIn(replacement["sha256"], saved.entry.text)
        self.assertEqual(self.image_bytes(saved.program_revision), base64.b64decode(replacement["data_base64"]))

    def test_add_and_remove_require_exact_source_closure_and_restore_original_revision(self):
        program = self.create()
        candidate = source("uninstantiated-declaration")
        spare = candidate.asset_map["spare"]
        change = {"operation": "add", "asset": descriptor("spare", spare.raw)}
        added = self.success(self.send("edit", expected_program_revision=program.program_revision,
            requested_level="constructed", asset_changes=[change],
            patches=[exact_patch(program, program.entry.text, candidate.entry.text)]))
        self.assertEqual(added["program_revision"], candidate.program_revision)
        self.assertEqual(self.image_bytes(candidate.program_revision, "spare"), spare.raw)
        remove = {"operation": "remove", "asset_id": "spare", "expected_sha256": spare.sha256}
        before = self.retained()
        self.error(self.send("edit", expected_program_revision=candidate.program_revision,
            requested_level="constructed", patches=[], asset_changes=[remove]), "OKL-E-ASSET-CLOSURE")
        self.assertEqual(before, self.retained())
        removed = self.success(self.send("edit", expected_program_revision=candidate.program_revision,
            requested_level="constructed", asset_changes=[remove],
            patches=[exact_patch(candidate, candidate.entry.text, program.entry.text)]))
        self.assertEqual(removed["program_revision"], program.program_revision)
        self.assertEqual(self.image_bytes(program.program_revision), program.asset_map["label"].raw)

    def test_duplicate_stale_and_different_id_replacements_preserve_acceptance(self):
        program = self.create()
        asset = program.assets[0]
        change = {"operation": "replace", "asset_id": asset.asset_id,
            "expected_sha256": asset.sha256, "asset": descriptor(asset.asset_id, asset.raw)}
        cases = [[change, copy.deepcopy(change)],
                 [{**change, "expected_sha256": "sha256:" + "0" * 64}],
                 [{**change, "asset": descriptor("different", asset.raw)}],
                 [{"operation": "add", "asset": descriptor(asset.asset_id, asset.raw)}]]
        before = self.retained()
        for changes in cases:
            with self.subTest(changes=changes):
                rejected = self.error(self.send("edit", expected_program_revision=program.program_revision,
                    requested_level="constructed", patches=[], asset_changes=changes), "OKL-E-REVISION")
                self.assertEqual(rejected["program_revision"], program.program_revision)
                self.assertEqual(self.retained(), before)
        stale_patch = exact_patch(program, program.entry.text, program.entry.text + "\n")
        stale_patch["expected_text"] = "wrong original source bytes"
        rejected = self.error(self.send("edit", expected_program_revision=program.program_revision,
            requested_level="constructed", patches=[stale_patch]), "OKL-E-REVISION")
        self.assertEqual(rejected["program_revision"], program.program_revision)
        self.assertEqual(rejected["diagnostics"][0]["program_revision"], program.program_revision)
        self.assertEqual(self.image_bytes(program.program_revision), asset.raw)

    def test_invalid_png_candidate_retains_exact_bytes_without_validity_metadata(self):
        program = self.create()
        replacement = descriptor("label", b"retained invalid PNG bytes")
        response = self.error(self.send("edit", expected_program_revision=program.program_revision,
            requested_level="constructed",
            patches=[exact_patch(program, program.assets[0].sha256, replacement["sha256"])],
            asset_changes=[{"operation": "replace", "asset_id": "label",
                "expected_sha256": program.assets[0].sha256, "asset": replacement}]), "OKL-E-PNG")
        self.assertEqual(self.service.accepted_revision(PROJECT), program.program_revision)
        revision = response["program_revision"]
        self.assertNotEqual(revision, program.program_revision)
        metadata = self.metadata(revision)["result"]["items"][0]
        self.assertEqual(set(metadata), {"element_id", "kind", "name", "identity", "source"})
        self.assertEqual(set(metadata["source"]),
            {"asset_id", "program_revision", "sha256", "media_type", "total_bytes"})
        self.assertEqual(self.image_bytes(revision), b"retained invalid PNG bytes")
        self.assertEqual(self.image_bytes(program.program_revision), program.assets[0].raw)

    def test_slice_roundtrip_eof_exact_length_and_shape_rejections(self):
        program = self.create()
        raw = program.assets[0].raw
        self.assertEqual(self.image_bytes(program.program_revision, count=5), raw)
        eof = self.metadata(program.program_revision, selector={"element_id": ["assets", "label"]},
                            asset_slice={"offset": len(raw), "max_bytes": 65536})["result"]
        self.assertEqual((eof["returned_bytes"], eof["data_base64"], eof["complete"], eof["next_offset"]),
                         (0, "", True, None))
        self.error(self.send("inspect", program_revision=program.program_revision,
            selector={"element_id": ["assets", "label"]}, fields=["source"], limit=1,
            asset_slice={"offset": len(raw) + 1, "max_bytes": 1}), "OKA-E-REQUEST")
        ordinary = self.request("inspect", program_revision=program.program_revision,
            selector={"element_id": ["assets", "label"]}, fields=["source"], limit=1,
            asset_slice={"offset": 0, "max_bytes": 1})
        changes = [{"asset_slice": {"offset": value, "max_bytes": 1}} for value in (-1, 0.5, True)]
        changes += [{"asset_slice": {"offset": 0, "max_bytes": value}} for value in (0, 65537, 1.5, True)]
        changes += [{field: None} for field in ("cursor", "run_id", "time", "frame")]
        changes += [{"selector": {"kind": "texture_asset"}}, {"fields": ["geometry"]},
                    {"selector": {"element_id": ["assets", "label"], "kind": "texture_asset"}}]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ProtocolError):
                TextureProtocol.validate_request({**ordinary, **change})

    def test_metadata_cursor_is_revision_bound_and_can_resume_original_after_reopen(self):
        program = self.create(source("uninstantiated-declaration"))
        first = self.metadata(program.program_revision, limit=1)
        self.assertIsNotNone(first["next_cursor"])
        response = self.success(self.send("edit", expected_program_revision=program.program_revision,
            requested_level="constructed", patches=[exact_patch(program, program.entry.text,
                program.entry.text + "\n// a new immutable source revision\n")]))
        self.error(self.send("inspect", program_revision=response["program_revision"],
            selector={"kind": "texture_asset"}, fields=["identity", "source"], limit=1,
            cursor=first["next_cursor"]), "OKL-E-REVISION")
        self.service.close()
        self.service = TextureAgentService(self.directory.name)
        resumed = self.metadata(program.program_revision, limit=1, cursor=first["next_cursor"])
        self.assertEqual(resumed["result"]["items"][0]["element_id"], ["assets", "spare"])
        self.assertIsNone(resumed["next_cursor"])

    def test_attachment_reads_reauthorize_current_host_and_caller_caps(self):
        payload = source().to_payload()
        payload["entry"]["source"] = payload["entry"]["source"].replace(
            'profile "textured-surfaces-0.1";',
            'profile "textured-surfaces-0.1";\nexecution { max_operations = 200000; max_elapsed = 80[s]; }')
        program = load_texture_bundle(payload)
        self.service.host_policy = HostPolicy(200000, 80000)
        self.create(program)
        self.error(self.send("inspect", program_revision=program.program_revision,
            selector={"element_id": ["assets", "label"]}, fields=["source"], limit=1,
            asset_slice={"offset": 0, "max_bytes": 1}, budgets={"max_operations": 1}), "OKL-E-RESOURCE")
        self.service.close()
        self.service = TextureAgentService(self.directory.name)
        for extra in ({}, {"asset_slice": {"offset": 0, "max_bytes": 1}}):
            self.error(self.send("inspect", program_revision=program.program_revision,
                selector={"element_id": ["assets", "label"]}, fields=["source"], limit=1, **extra), "OKL-E-RESOURCE")
        self.assertEqual(self.service.accepted_revision(PROJECT), program.program_revision)

    def test_reopen_preserves_identical_receipt_and_refuses_changed_image_payload(self):
        program = source()
        request = self.request("create", bundle=program.to_payload(),
            expected_program_revision=None, requested_level="constructed")
        response = self.success(self.service.handle(request))
        self.service.close()
        self.service = TextureAgentService(self.directory.name)
        with patch.object(self.service, "_execute", side_effect=AssertionError("Retry executed")):
            self.assertEqual(self.service.handle(copy.deepcopy(request)), response)
        changed = copy.deepcopy(request)
        changed["bundle"]["assets"][0] = descriptor("label", b"changed request payload")
        self.error(self.service.handle(changed), "OKL-E-REQUEST-ID")
        self.assertEqual(self.image_bytes(program.program_revision), program.assets[0].raw)

    def test_store_rechecks_complete_source_and_asset_revision_on_read(self):
        program = self.create()
        altered = program.to_payload()
        altered["assets"][0] = descriptor("label", b"valid transport but different content")
        with self.service._store.transaction() as db:
            db.execute("UPDATE sources SET raw=? WHERE project_id=? AND revision=?",
                       (json.dumps(altered).encode(), PROJECT, program.program_revision))
        with self.assertRaises(ProtocolError) as caught:
            self.service.read_program(PROJECT, program.program_revision)
        self.assertEqual(caught.exception.code, "OKA-E-STORE-INTEGRITY")

    def test_surface_pages_geometry_summary_and_remaining_lifecycle_operations(self):
        program = self.create()
        self.success(self.send("validate", program_revision=program.program_revision,
                               requested_level="constructed"))
        summary = self.success(self.send("inspect", program_revision=program.program_revision,
            selector={"element_id": SHAPE}, fields=["geometry"], limit=1))["result"]["items"][0]["geometry"]["surface"]
        self.assertEqual(summary["texture_bindings"]["top"]["sha256"], program.assets[0].sha256)
        page = self.success(self.send("surface.mesh_page", program_revision=program.program_revision,
            element_id=SHAPE, count=256))["result"]
        self.assertEqual(page["profile"], PROFILE)
        self.assertEqual(len(page["texcoords_0"]), len(page["positions_m"]))
        self.assertTrue(any(value is None for value in page["texcoords_0"]))
        self.assertTrue(any(isinstance(value, list) for value in page["texcoords_0"]))
        self.success(self.send("evaluate", program_revision=program.program_revision,
                               run_id=None, until_seconds="0.5"))
        self.success(self.send("reset", program_revision=program.program_revision))
        exported = self.success(self.send("export", program_revision=program.program_revision,
                                          destination=TARGET, options=OPTIONS))
        artifact_id = exported["result"]["artifact_id"]
        read = self.success(self.send("artifact", artifact_id=artifact_id, offset=0, max_bytes=65536))
        self.assertTrue(read["result"]["data_base64"])
        status = self.success(self.send("status", target_request_id=exported["request_id"]))
        self.assertEqual(status["result"]["target_status"], "succeeded")
        cancel = self.success(self.send("cancel", target_request_id=exported["request_id"]))
        self.assertEqual(cancel["result"]["disposition"], "already_completed")

    def test_interrupted_artifact_publication_rolls_back_complete_texture_artifact(self):
        program = self.create()
        before = self.retained()
        persist = self.service._persist_task_metadata
        observed = []

        def reject_publication(db, task):
            if task.artifact is not None:
                observed.append(len(task.artifact[0]))
                raise ProtocolError("OKA-E-RESOURCE", "Injected final publication interruption.")
            return persist(db, task)

        with patch.object(self.service, "_persist_task_metadata", side_effect=reject_publication):
            self.error(self.send("export", program_revision=program.program_revision,
                destination=TARGET, options=OPTIONS), "OKA-E-RESOURCE")
        self.assertTrue(observed)
        self.assertEqual(self.retained(), before)
        self.assertEqual(self.image_bytes(program.program_revision), program.assets[0].raw)


if __name__ == "__main__":
    unittest.main()
