"""Sample native glTF playback on VTK. Compare the three previously captured browser poses."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import struct
import sys

import vtk


def matrix(actor):
    value = actor.GetMatrix()
    return [value.GetElement(i, j) for j in range(4) for i in range(4)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("glb", type=Path)
    parser.add_argument("browser_samples", type=Path)
    args = parser.parse_args()
    raw = args.glb.read_bytes()
    n, = struct.unpack_from("<I", raw, 12)
    graph = json.loads(raw[20:20+n])
    reference = json.loads(args.browser_samples.read_bytes())
    mesh_nodes = [node["name"] for node in graph["nodes"] if "mesh" in node]
    expected_counts = {node["name"]: len(graph["meshes"][node["mesh"]]["primitives"])
                       for node in graph["nodes"] if "mesh" in node}
    native = vtk.vtkGLTFImporter()
    errors = []
    native.AddObserver("ErrorEvent", lambda *args: errors.append("ErrorEvent"))
    native.SetFileName(str(args.glb.resolve()))
    native.Read()
    if errors or native.GetNumberOfAnimations() != 1:
        raise RuntimeError((errors, native.GetNumberOfAnimations()))
    native.EnableAnimation(0)
    native.UpdateTimeStep(0)
    collection = native.GetRenderer().GetActors()
    actors = list(collection)
    # At t=0 the six mesh-bearing origins are distinct. Bind once, before playing the clip.
    bindings = []
    for actor in actors:
        candidates = [name for name in mesh_nodes
                      if matrix(actor) == reference[0]["carriers"][name]["matrix"]]
        if len(candidates) != 1:
            raise ValueError(candidates)
        bindings.append(candidates[0])
    if collections.Counter(bindings) != expected_counts:
        raise ValueError((bindings, expected_counts))
    observations = []
    for sample in reference:
        native.UpdateTimeStep(sample["time"])
        matrices = [matrix(actor) for actor in actors]
        transforms = {}
        for name in mesh_nodes:
            group = [matrices[i] for i in range(len(actors)) if bindings[i] == name]
            if any(value != group[0] for value in group):
                raise ValueError(("primitive transform mismatch", name))
            expected = sample["carriers"][name]["matrix"]
            transforms[name] = {"world_matrix_column_major": group[0],
                                "max_abs_component_difference_vs_browser":
                                    max(abs(a-b) for a, b in zip(group[0], expected))}
        observations.append({"time_s": sample["time"], "mesh_carriers": transforms})
    if errors:
        raise RuntimeError(errors)
    print(json.dumps({"vtk_version": vtk.vtkVersion.GetVTKVersion(), "python": sys.version.split()[0],
                      "glb_sha256": hashlib.sha256(raw).hexdigest(),
                      "reference_sha256": hashlib.sha256(args.browser_samples.read_bytes()).hexdigest(),
                      "animation": native.GetAnimationName(0), "enabled": bool(native.IsAnimationEnabled(0)),
                      "actor_count": len(actors), "actors_per_mesh_node": expected_counts,
                      "nonmesh_nodes": [n["name"] for n in graph["nodes"] if "mesh" not in n],
                      "samples": observations}, indent=2))


if __name__ == "__main__":
    main()
