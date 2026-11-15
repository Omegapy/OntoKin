#!/usr/bin/env python3
"""Read-only C243 source/fixture/candidate evidence; never starts Godot.

This verifies pinned bytes and finite source facts. It is not a runtime observer,
an engine simulator, a native admission check, or a proof of installed behavior.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import stat
import struct
import sys


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def inspect(package: Path, fresh_sources: Path | None) -> dict:
    here = Path(__file__).resolve().parent
    repo = here.parents[3]
    pins_path = here / "PRIMARY-SOURCES.json"
    pins = json.loads(pins_path.read_text())
    report = {
        "schema": "ontokin.c243.static-mapping-review/0.1",
        "recordedAtUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "baseRevision": "73ef57f5a07db2c5eef5ef6dafd9305e1870f1b7",
        "scriptSha256": digest(Path(__file__).read_bytes()),
        "sourcePinsSha256": digest(pins_path.read_bytes()),
        "python": sys.version,
        "platform": list(os.uname()),
        "nativeStarts": 0,
        "productRuns": 0,
        "aggregateRuns": 0,
        "checks": [],
        "limits": [
            "Exact source-byte and source-order inspection only",
            "No Godot process, version probe, import, conversion, save or render",
            "No source-defined behavior is claimed for the mismatched installed build",
            "Passing static checks does not approve an observer or change C220",
        ],
    }

    def check(name: str, passed: bool, detail=None) -> None:
        row = {"name": name, "passed": bool(passed)}
        if detail is not None:
            row["detail"] = detail
        report["checks"].append(row)
        if not passed:
            raise ValueError(name)

    try:
        sources = {}
        source_records = []
        for item in pins["sources"]:
            path = package / item["packagePath"]
            if fresh_sources and item["packagePath"].startswith("evidence/c243/"):
                path = fresh_sources / Path(item["packagePath"]).name
            raw = path.read_bytes()
            blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
            valid = len(raw) == item["bytes"] and digest(raw) == item["sha256"] and blob == item["gitBlobSha1"]
            source_records.append({"packagePath": item["packagePath"], "bytes": len(raw), "sha256": digest(raw), "gitBlobSha1": blob, "matches": valid})
            if not valid:
                raise ValueError("Pinned upstream source drift: " + item["packagePath"])
            sources[Path(item["packagePath"]).name] = raw.decode("utf-8")
        check("nine_exact_upstream_source_blobs", len(source_records) == 9, source_records)

        input_path = repo / "docs/engineering/second-target-c220/evidence/INPUT-BINDINGS.json"
        bindings = json.loads(input_path.read_text())
        bound = []
        original = {}
        for item in bindings["items"]:
            path = package / item["packagePath"]
            raw = path.read_bytes()
            valid = len(raw) == item["bytes"] and digest(raw) == item["sha256"] and stat.S_IMODE(path.stat().st_mode) == item["mode"]
            bound.append({"packagePath": item["packagePath"], "bytes": len(raw), "sha256": digest(raw), "matches": valid})
            original[item["packagePath"]] = raw
        check("eight_original_authority_files", len(bound) == 8 and all(x["matches"] for x in bound), bound)

        contract_rows = []
        for item in pins["authorityDocuments"]:
            raw = (repo / item["path"]).read_bytes()
            contract_rows.append({"path": item["path"], "sha256": digest(raw), "matches": digest(raw) == item["sha256"]})
        check("unchanged_prior_contract_documents", all(x["matches"] for x in contract_rows), contract_rows)

        glb = original[bindings["items"][0]["packagePath"]]
        magic, version, length = struct.unpack_from("<III", glb)
        json_length, json_type = struct.unpack_from("<II", glb, 12)
        check("original_glb_header", (magic, version, length, json_type) == (0x46546C67, 2, len(glb), 0x4E4F534A))
        fixture = json.loads(glb[20:20 + json_length])
        partmap = json.loads((repo / "docs/engineering/second-target-c220/evidence/PART-MAP.json").read_text())
        nodes = fixture["nodes"]
        roots = fixture["scenes"][fixture.get("scene", 0)]["nodes"]
        check("finite_fixture_18_mesh_nodes", len(nodes) == 18 and all("mesh" in x for x in nodes) and sorted(roots) == list(range(18)) and all(not x.get("children") for x in nodes))
        check("fixture_has_no_skin_or_single_root_extension", not fixture.get("skins") and all("skin" not in x for x in nodes) and "GODOT_single_root" not in fixture.get("extensionsUsed", []), {"extensionsUsed": fixture.get("extensionsUsed", []), "skins": len(fixture.get("skins", [])), "rootIndices": roots})
        check("source_node_mesh_associations_exact", len(partmap["entries"]) == 18 and sorted(x["glbNode"] for x in partmap["entries"]) == list(range(18)) and all(nodes[x["glbNode"]]["mesh"] == x["glbMesh"] for x in partmap["entries"]), {"partCount": len(partmap["entries"]), "meshCount": len(fixture["meshes"]), "nativeMappingObserved": False})

        document = sources["gltf_document.cpp"]
        converter = sources["gltf_document_extension_convert_importer_mesh.cpp"]
        state = sources["gltf_state.cpp"]
        generation = document[document.index("Node *GLTFDocument::generate_scene("):document.index("Error GLTFDocument::append_from_scene(")]
        order = ["_generate_scene_node_tree(p_state)", "ext->import_node(", "convert_importer_mesh_instance_3d(root_importer_mesh)", "memdelete(root_importer_mesh)", "ext->import_post(", "return godot_root_node;"]
        positions = [generation.index(x) for x in order]
        check("generation_hook_conversion_return_order", positions == sorted(positions), order)
        check("fixture_default_mesh_and_source_map_construction", "ImporterMeshInstance3D *mi = memnew(ImporterMeshInstance3D);" in document and "p_state->scene_nodes.insert(p_node_index, current_node);" in document and "single_root = memnew(Node3D);" in document)
        conversion = converter[converter.index("MeshInstance3D *GLTFDocumentExtensionConvertImporterMesh::convert_importer_mesh_instance_3d("):converter.index("Error GLTFDocumentExtensionConvertImporterMesh::import_post(")]
        converter_order = ["memnew(MeshInstance3D)", "replace_by(mesh_instance_node_3d)", "_copy_meta(p_importer_mesh_instance_3d, mesh_instance_node_3d)", "importer_mesh->get_mesh()", "_copy_meta(importer_mesh.ptr(), array_mesh.ptr())"]
        check("converter_identity_and_metadata_order", [conversion.index(x) for x in converter_order] == sorted(conversion.index(x) for x in converter_order), converter_order)
        post = converter[converter.index("Error GLTFDocumentExtensionConvertImporterMesh::import_post("):]
        check("descendant_replacements_then_old_nodes_deleted", post.index("delete_queue.push_back(importer_mesh_3d)") < post.index("convert_importer_mesh_instance_3d(importer_mesh_3d)") < post.index("while (!delete_queue.is_empty())") < post.index("memdelete(node)") and "scene_nodes" not in converter, "No scene_nodes write occurs in the exact converter file")
        forward = state[state.index("Node *GLTFState::get_scene_node("):state.index("int GLTFState::get_animation_players_count(")]
        check("stored_raw_pointer_lookup", "HashMap<GLTFNodeIndex, Node *> scene_nodes;" in sources["gltf_state.h"] and "return scene_nodes[p_gltf_node_index];" in forward and "if (x.value == p_node)" in forward)
        node = sources["node.cpp"]
        replace = node[node.index("void Node::replace_by("):node.index("void Node::_replace_connections_target(")]
        check("replacement_signal_does_not_rebind_gltf_state", 'emit_signal(SNAME("replacing_by"), p_node);' in replace and "scene_nodes" not in replace and "GLTFState" not in replace and replace.index('emit_signal(SNAME("replacing_by"), p_node);') < replace.index("while (get_child_count())"))
        registration = sources["register_types.cpp"]
        check("converter_registered_for_non_editor_route", "if (!is_editor) {\n\t\t\tGLTF_REGISTER_DOCUMENT_EXTENSION(GLTFDocumentExtensionConvertImporterMesh);" in registration)
        ext = sources["gltf_document_extension.cpp"]
        check("preconversion_hooks_require_extension_and_errors_continue", "GDVIRTUAL_CALL(_import_node," in ext and "GDVIRTUAL_CALL(_import_post," in ext and "ERR_CONTINUE(err != OK);" in generation)
        bound_methods = document[document.index("void GLTFDocument::_bind_methods()"):document.index("void GLTFDocument::register_gltf_document_extension(")]
        check("selected_script_api_has_no_split_generation_binding", 'D_METHOD("generate_scene",' in bound_methods and 'D_METHOD("_generate_scene_node_tree"' not in bound_methods, "C++ internal helper declarations are not the selected caller API")

        candidate = Path("/opt/godot/4.6.3/Godot_v4.6.3-stable_linux.x86_64")
        fd = os.open(candidate, os.O_RDONLY | os.O_NOFOLLOW)
        try:
            before = os.fstat(fd)
            with os.fdopen(fd, "rb", closefd=False) as stream:
                binary = stream.read()
            after = os.fstat(fd)
        finally:
            os.close(fd)
        current = candidate.stat()
        identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_mode)
        installed = {"path": str(candidate), "bytes": len(binary), "sha256": digest(binary), "mode": stat.S_IMODE(before.st_mode), "unchangedDuringRead": identity(before) == identity(after) == identity(current), "elfMagic": binary[:4].hex(), "elfClass": binary[4], "elfMachine": struct.unpack_from("<H", binary, 18)[0]}
        check("installed_bytes_match_c220_without_execution", installed["bytes"] == 138981968 and installed["sha256"] == "f64d4ed19fc9df9440321653fcc80df8c6e365ba7b6de0a29e2cfa9fa71bfeb3" and installed["mode"] == 0o755 and installed["unchangedDuringRead"], installed)
        marker = b"7d41c59c457bd5a245092b4e7eb2d833e3b3f8c3"
        version_marker = b"Godot Engine v4.6.3.stable.official"
        check("embedded_lineage_discrepancy_retained", marker in binary and version_marker in binary and marker.decode() != pins["inspectedRevision"], {"embeddedCommitLikeValue": marker.decode(), "embeddedOffset": binary.find(marker), "versionStringOffset": binary.find(version_marker), "inspectedUpstreamCommit": pins["inspectedRevision"], "status": "UNRESOLVED_NOT_AN_AUTHENTICATED_BUILD"})
        report["passed"] = True
        report["decision"] = "BLOCKED_NO_SAFE_CALLER_CAPTURE_WINDOW_ESTABLISHED"
    except (OSError, ValueError, KeyError, IndexError, struct.error) as error:
        report["passed"] = False
        report["error"] = str(error)
    report["checkGroups"] = len(report["checks"])
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--fresh-sources", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    result = inspect(args.package, args.fresh_sources)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"passed": result["passed"], "checkGroups": result["checkGroups"], "report": str(args.report), "error": result.get("error")}))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
