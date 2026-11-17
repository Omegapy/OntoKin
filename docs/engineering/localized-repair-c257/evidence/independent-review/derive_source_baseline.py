#!/usr/bin/env python3
"""Independent source-only witnesses for the finite C210 ownership review.

This audit utility reads original .ok bytes. It imports no project module,
expected-state helper, producer sidecar, or author ownership reader.
It records lexical facts, not an accepted revision or a general parser result.
"""
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def unique(raw, pattern, group=0):
    matches = list(re.finditer(pattern, raw))
    assert len(matches) == 1, (pattern, len(matches))
    match = matches[0]
    return match.group(group).decode(), match.start(group), match.end(group)


def origin(name, raw, start, end):
    return {"file": name, "sha256": sha(raw), "startByte": start,
            "endByteExclusive": end,
            "line": raw[:start].count(b"\n") + 1,
            "text": raw[start:end].decode()}


def block(raw, declaration):
    token, start, end = unique(raw, declaration)
    opening = raw.index(b"{", end)
    depth = 0
    # Original sources have no braces within literals/comments in these blocks.
    for at in range(opening, len(raw)):
        if raw[at] == ord("{"):
            depth += 1
        elif raw[at] == ord("}"):
            depth -= 1
            if depth == 0:
                return start, at + 1
    raise AssertionError("unclosed original block")


def derive(endpoint):
    name = endpoint + ".main.ok"
    main = (HERE / name).read_bytes()
    library = (HERE / "hinges.ok").read_bytes()
    sources = {name: main, "hinges.ok": library}
    module = unique(main, rb'module KeyedRack @ "([^"]+)";', 1)
    scene = unique(main, rb'scene Demo @ "([^"]+)"', 1)
    collection = unique(main, rb'public parts fingers @ "([^"]+)": mech\.Finger for \(key, offset\) in self\.mounts', 1)
    blade = unique(library, rb'private part blade @ "([^"]+)": Blade', 1)
    collection_start, collection_end = block(main, rb'public parts fingers @ "fingers": mech\.Finger for \(key, offset\) in self\.mounts')
    blade_start, blade_end = block(library, rb'private part blade @ "blade": Blade')
    fn_start, fn_end = block(library, rb'public fn three_mounts @ "three-mounts"\(spacing: Length\) -> Keyed<Vec3<Length>>')
    second_start, second_end = block(main, rb'object second @ "second": Rack')
    mounts_start, mounts_end = block(main, rb'mounts = keyed<Vec3<Length>>')
    key_sources = {"first": ("hinges.ok", library, fn_start, fn_end),
                   "second": (name, main, mounts_start, mounts_end)}
    assert second_start < mounts_start < mounts_end < second_end
    result = {"endpoint": endpoint,
              "sourceHashes": {n: sha(r) for n, r in sources.items()},
              "moduleKey": module[0], "sceneKey": scene[0],
              "semantics": "Lexical object/part declaration ownership only; no frame, follow, joint or transform inference",
              "artifactIdentityAssociation": "pending independent actual GLB traversal",
              "occurrences": [], "excludedRelationWitnesses": []}
    for root in ["first", "second"]:
        root_token = unique(main, (rb'object ' + root.encode() + rb' @ "([^"]+)": Rack'), 1)
        root_origin = origin(name, main, root_token[1], root_token[2])
        root_path = [root]
        common = [origin(name, main, module[1], module[2]),
                  origin(name, main, scene[1], scene[2]), root_origin]
        result["occurrences"].append({"pathComponents": root_path,
                                      "ownerPathComponents": None,
                                      "sourceKeyComponents": [module[0], scene[0], root_token[0]],
                                      "sourceOrigins": common,
                                      "ownershipReason": "Object is declared directly in scene Demo"})
        key_name, key_raw, start, end = key_sources[root]
        keys = list(re.finditer(rb'"([^"]+)"\s*:\s*vec3\(', key_raw[start:end]))
        assert len(keys) == (3 if root == "first" else 5)
        for key in keys:
            value = key.group(1).decode()
            key_at = origin(key_name, key_raw, start + key.start(1), start + key.end(1))
            finger_path = root_path + ["fingers", value]
            finger_origins = common + [origin(name, main, collection_start, collection_end), key_at]
            result["occurrences"].append({"pathComponents": finger_path,
                                          "ownerPathComponents": root_path,
                                          "sourceKeyComponents": [module[0], scene[0], root_token[0], collection[0], value],
                                          "sourceOrigins": finger_origins,
                                          "ownershipReason": "Generated Finger part is declared lexically inside Rack"})
            result["occurrences"].append({"pathComponents": finger_path + ["blade"],
                                          "ownerPathComponents": finger_path,
                                          "sourceKeyComponents": [module[0], scene[0], root_token[0], collection[0], value, blade[0]],
                                          "sourceOrigins": finger_origins + [origin("hinges.ok", library, blade_start, blade_end)],
                                          "ownershipReason": "Blade part is declared lexically inside Finger"})
    for pattern in [rb'public follow mounting @ "mounting"', rb'public joint flex @ "flex": hinge']:
        start, end = block(library, pattern)
        result["excludedRelationWitnesses"].append(origin("hinges.ok", library, start, end))
    assert len(result["occurrences"]) == 18
    assert sum(x["ownerPathComponents"] is None for x in result["occurrences"]) == 2
    return result


if __name__ == "__main__":
    out = {"schema": "ontokin.c257.independent-source-baseline/1",
           "baselineMain": "23b1d2b5abafde6a5826827c30bc1bbf8552ff8e",
           "method": "Independent finite lexical inspection of original .ok declarations; no producer semantic answers",
           "endpoints": [derive("before"), derive("after")]}
    (HERE / "SOURCE-BASELINE.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({x["endpoint"]: {"occurrences": len(x["occurrences"]),
          "ownerlessRoots": sum(y["ownerPathComponents"] is None for y in x["occurrences"]),
          "ownershipEdges": sum(y["ownerPathComponents"] is not None for y in x["occurrences"])}
          for x in out["endpoints"]}, sort_keys=True))
