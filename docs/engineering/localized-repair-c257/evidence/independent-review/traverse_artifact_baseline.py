#!/usr/bin/env python3
"""Independent GLB container/ownership traversal; no OntoKin imports."""
import hashlib
import json
from pathlib import Path
import re
import struct

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1] / "OntoKin"
PROOF = REPO / "docs/engineering/semantic-export-c210/evidence/proof"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def path_text(parts):
    out = parts[0]
    if len(parts) > 1:
        out += "." + parts[1] + "[" + json.dumps(parts[2]) + "]"
    if len(parts) > 3:
        out += "." + parts[3]
    return out


def keyed(raw, pattern):
    matches = list(re.finditer(pattern, raw))
    assert len(matches) == 1
    return matches[0].group(1).decode()


def traverse(endpoint, source_observations):
    raw = (PROOF / (endpoint + ".glb")).read_bytes()
    magic, version, size = struct.unpack_from("<4sII", raw)
    assert (magic, version, size) == (b"glTF", 2, len(raw))
    chunks = []
    offset = 12
    while offset < len(raw):
        count, kind = struct.unpack_from("<I4s", raw, offset)
        assert count % 4 == 0 and offset + 8 + count <= len(raw)
        chunks.append({"type": kind.decode("ascii", "backslashreplace"),
                       "headerByte": offset, "contentByte": offset + 8,
                       "contentBytes": count})
        offset += 8 + count
    assert offset == len(raw) and len(chunks) == 2
    assert chunks[0]["type"] == "JSON" and chunks[1]["type"] == "BIN" + chr(0)
    chunk = chunks[0]
    doc = json.loads(raw[chunk["contentByte"]:chunk["contentByte"] + chunk["contentBytes"]])
    (HERE / (endpoint + ".actual-glb-json.json")).write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
    metadata = doc["extras"]["ontokin"]
    program = metadata["program"]
    source_map = {"main.ok": (PROOF / (endpoint + ".main.ok")).read_bytes(),
                  "hinges.ok": (PROOF / "hinges.ok").read_bytes()}
    for name, actual in source_map.items():
        saved = HERE / (endpoint + ".main.ok" if name == "main.ok" else name)
        assert actual == saved.read_bytes()
    module = source_observations["moduleKey"]
    library_module = keyed(source_map["hinges.ok"], rb'module Hinges @ "([^"]+)";')
    class_keys = {"Rack": keyed(source_map["main.ok"], rb'public class Rack @ "([^"]+)"'),
                  "Finger": keyed(source_map["hinges.ok"], rb'public class Finger @ "([^"]+)"'),
                  "Blade": keyed(source_map["hinges.ok"], rb'private class Blade @ "([^"]+)"')}
    source_by_path = {path_text(row["pathComponents"]): row
                      for row in source_observations["occurrences"]}
    assert len(source_by_path) == 18
    seen = set()
    records = []
    for index, node in enumerate(doc["nodes"]):
        claim = node["extras"]["ontokin"]
        path = claim["path"]
        assert path not in seen
        seen.add(path)
        source = source_by_path[path]
        owner_parts = source["ownerPathComponents"]
        owner_path = None if owner_parts is None else path_text(owner_parts)
        owner_id = None if owner_path is None else source_by_path[owner_path]["sourceKeyComponents"]
        mapping = claim["source_mapping"]
        occurrence = program["occurrences"][path]
        assert claim["element_id"] == mapping["element_id"] == source["sourceKeyComponents"]
        assert node["name"] == mapping["path"] == path
        assert claim["owner"] == mapping["owner_path"] == occurrence["owner_path"] == owner_path
        assert mapping == occurrence
        if len(source["pathComponents"]) == 1:
            definition = ["entry", module, "definitions", class_keys["Rack"]]
        else:
            cls = "Finger" if len(source["pathComponents"]) == 3 else "Blade"
            definition = ["package", "example.hinges", library_module, "definitions", class_keys[cls]]
        assert mapping["definition_id"] == definition
        assert claim["class_name"] == mapping["class_id"] == "/".join(definition)
        spans = {}
        for field in ["declaration", "definition"]:
            span = mapping[field]
            source_raw = source_map[span["filename"]]
            assert span["source_revision"] == "sha256:" + digest(source_raw)
            start, end = span["start_byte"], span["end_byte"]
            assert type(start) is int and type(end) is int and 0 <= start < end <= len(source_raw)
            spans[field] = {**span, "actualText": source_raw[start:end].decode()}
        records.append({"path": path, "id": claim["element_id"], "definitionId": definition,
                        "ownerPath": owner_path, "ownerId": owner_id,
                        "node": index, "nodeOwnerOrigin": f"/nodes/{index}/extras/ontokin/owner",
                        "mappingOwnerOrigin": f"/nodes/{index}/extras/ontokin/source_mapping/owner_path",
                        "programOwnerOrigin": "/extras/ontokin/program/occurrences/" + path.replace("~", "~0").replace("/", "~1") + "/owner_path",
                        "actualSourceSpans": spans,
                        "sourceBaselinePathComponents": source["pathComponents"]})
    assert seen == set(source_by_path) == set(program["occurrences"])
    assert sorted(doc["scenes"][0]["nodes"]) == list(range(18))
    assert all("children" not in node for node in doc["nodes"])
    assert metadata["transform_policy"] == "all_nodes_are_roots_with_baked_world_poses"
    return {"endpoint": endpoint, "artifactPath": str(PROOF / (endpoint + ".glb")),
            "artifactBytes": len(raw), "artifactSha256": digest(raw),
            "sourceHashes": {name: digest(content) for name, content in source_map.items()},
            "chunks": chunks, "observedProgramRevision": program["revision"],
            "programRevisionQualification": "metadata label recorded; no accepted-revision authority inferred",
            "nodeCount": len(records), "sourceOwnerlessRoots": sum(x["ownerPath"] is None for x in records),
            "sourceOwnershipEdges": sum(x["ownerPath"] is not None for x in records),
            "glbSceneRootCount": len(doc["scenes"][0]["nodes"]),
            "allOwnershipClaimsAgreeWithIndependentSource": True, "records": records}


if __name__ == "__main__":
    baseline = json.loads((HERE / "SOURCE-BASELINE.json").read_text())
    out = {"schema": "ontokin.c257.independent-artifact-baseline/1",
           "baselineMain": baseline["baselineMain"],
           "method": "Direct GLB chunk/JSON traversal joined to independent original source witnesses; no producer sidecar or project module",
           "endpoints": [traverse(x["endpoint"], x) for x in baseline["endpoints"]]}
    (HERE / "ARTIFACT-BASELINE.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({x["endpoint"]: {k: x[k] for k in ["artifactBytes", "artifactSha256", "nodeCount", "sourceOwnerlessRoots", "sourceOwnershipEdges", "glbSceneRootCount", "allOwnershipClaimsAgreeWithIndependentSource"]} for x in out["endpoints"]}, sort_keys=True))
