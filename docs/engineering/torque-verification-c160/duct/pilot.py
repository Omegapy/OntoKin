"""Export and measure two sectioned ducts. With --output-dir, retain the GLBs and JSON."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys


def rows(graph, payload, index):
    accessor = graph["accessors"][index]
    view = graph["bufferViews"][accessor["bufferView"]]
    arity = {"SCALAR": 1, "VEC3": 3}[accessor["type"]]
    code = {5121: "B", 5123: "H", 5125: "I", 5126: "f"}[accessor["componentType"]]
    layout = struct.Struct("<" + str(arity) + code)
    start = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    stride = view.get("byteStride", layout.size)
    return [layout.unpack_from(payload, start + stride*i) for i in range(accessor["count"])]


def cross2(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])


def measure(raw):
    length, = struct.unpack_from("<I", raw, 12)
    graph = json.loads(raw[20:20+length])
    payload = memoryview(raw)[28+length:]
    groups = []
    for prim in graph["meshes"][0]["primitives"]:
        coords = rows(graph, payload, prim["attributes"]["POSITION"])
        if "indices" in prim:
            coords = [coords[i] for i, in rows(graph, payload, prim["indices"])]
        groups.append([coords[i:i+3] for i in range(0, len(coords), 3)])
    ends = []
    for label, axis, plane, center in (("inlet", 2, 0, (0, 0)), ("outlet", 0, 4, (0, 4))):
        areas = []
        covered = False
        for group in groups:
            for face in group:
                if any(abs(v[axis]-plane) >= 1e-6 for v in face):
                    continue
                a, b, c = [tuple(x for j, x in enumerate(v) if j != axis) for v in face]
                signs = (cross2(a, b, center), cross2(b, c, center), cross2(c, a, center))
                covered |= min(signs) >= 0 or max(signs) <= 0
                areas.append(abs(cross2(a, b, c))/2)
        ends.append(dict(port=label, plane_axis="XYZ"[axis], plane_coordinate_m=plane,
                         center_projected_m=center, triangle_count=len(areas),
                         wall_area_m2=sum(areas), center_covered=covered))
    return [len(group) for group in groups], ends


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path)
    parser.add_argument("--output-dir", type=Path, help="Create a new output directory")
    args = parser.parse_args()
    repo = args.checkout.resolve()
    sys.path.insert(0, str(repo))
    from ontokin.budget_runtime import execute_framed_loft_export
    from ontokin.bundle import ProgramBundle, SourceUnit
    from ontokin.scene import ExportOptions

    if args.output_dir:
        args.output_dir.mkdir()
    results = []
    pilot = Path(__file__).with_name("duct.ok")
    for path, expected in [(repo/"examples/framed-polygon-lofts/hollow-elbow.ok", 32), (pilot, 48)]:
        bundle = ProgramBundle(SourceUnit("entry", "shape.ok", path.read_bytes()), ())
        out = execute_framed_loft_export(bundle, options=ExportOptions(fps=2, end="1", helpers=False))
        if out.data is None:
            raise ValueError(out.report["diagnostics"])
        counts, ends = measure(out.data)
        row = dict(source=path.name, sha256=hashlib.sha256(out.data).hexdigest(),
                   bytes=len(out.data), triangles=sum(counts), primitive_triangle_counts=counts,
                   terminal_measurements=ends)
        if sum(counts) != expected or any(e["triangle_count"] != 8 or e["center_covered"]
                                           or abs(e["wall_area_m2"]-3) >= 1e-6 for e in ends):
            raise ValueError(row)
        print(json.dumps(row))
        results.append(row)
        if args.output_dir:
            (args.output_dir / path.with_suffix(".glb").name).write_bytes(out.data)
    if args.output_dir:
        (args.output_dir/"measurements.json").write_text(json.dumps(results, indent=2) + "\n")


if __name__ == "__main__":
    main()
