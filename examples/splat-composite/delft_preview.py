"""Build a read-only, reduced display copy of the published TU Delft campus capture."""
from __future__ import annotations

import argparse
from array import array
import hashlib
import json
import math
import mmap
from pathlib import Path
import struct


SOURCE_SHA256 = "c56b1a07559312fcf1c9ef150802995005b6e3b4f8cf0c501fb96cec5d5ca45a"
SOURCE_DOI = "https://doi.org/10.17605/OSF.IO/P3CW7"
CREDIT = "Y. Yu, TU Delft Aula and Library capture (2025), CC BY 4.0"
LICENSE = "https://creativecommons.org/licenses/by/4.0/"
EXT = "KHR_gaussian_splatting"
FIELDS = ["x", "y", "z", "nx", "ny", "nz", *(f"f_dc_{i}" for i in range(3)),
          *(f"f_rest_{i}" for i in range(45)), "opacity",
          *(f"scale_{i}" for i in range(3)), *(f"rot_{i}" for i in range(4))]
RECORD = struct.Struct("<62f")
XYZ = struct.Struct("<3f")


def convert(source: Path, output: Path, max_splats=120_000, bbox=None, *, expected_sha=SOURCE_SHA256):
    """Keep ordered, equally spaced samples of eligible records, without moving their centres."""
    if not 1 <= max_splats <= 1_000_000:
        raise ValueError("max_splats must be in the range 1 to 1000000")
    if bbox is not None and (len(bbox) != 6 or not all(map(math.isfinite, bbox))
                            or any(lo >= hi for lo, hi in zip(bbox[:3], bbox[3:]))):
        raise ValueError("Expected finite, increasing XYZ crop bounds")
    with source.open("rb") as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as data:
        digest = hashlib.sha256(data).hexdigest()
        if digest != expected_sha:
            raise ValueError("Published capture SHA-256 mismatch")
        end = data.find(b"end_header\n", 0, 4096)
        if end == -1:
            raise ValueError("Missing PLY header")
        start = end + len(b"end_header\n")
        lines = data[:end].decode("ascii").splitlines()
        if (len(lines) < 3 or lines[:2] != ["ply", "format binary_little_endian 1.0"]
                or not lines[2].startswith("element vertex ")
                or lines[3:] != ["property float " + name for name in FIELDS]):
            raise ValueError("Expected the published Delft float32 vertex layout")
        count = int(lines[2].split()[2])
        if count <= 0 or start + count * RECORD.size != len(data):
            raise ValueError("PLY count and payload size disagree")
        eligible = range(count)
        if bbox is not None:
            x0, y0, z0, x1, y1, z1 = bbox
            eligible = array("I")
            for index in range(count):
                x, y, z = XYZ.unpack_from(data, start + index * RECORD.size)
                if x0 <= x <= x1 and y0 <= y <= y1 and z0 <= z <= z1:
                    eligible.append(index)
        retained = min(max_splats, len(eligible))
        if not retained:
            raise ValueError("Crop contains no splats")
        payload = bytearray()
        low, high = [math.inf] * 3, [-math.inf] * 3
        # SH0 is independent of direction. The other 45 SH components are omitted.
        layout = struct.Struct("<14f")
        for sample in range(retained):
            index = eligible[(2 * sample + 1) * len(eligible) // (2 * retained)]
            row = RECORD.unpack_from(data, start + index * RECORD.size)
            x, y, z = xyz = row[:3]
            dc = row[6:9]
            logit = row[54]
            spread = [math.exp(v) for v in row[55:58]]
            w, qx, qy, qz = row[58:62]
            length = math.hypot(w, qx, qy, qz)
            if not length or not all(map(math.isfinite, (*xyz, *dc, logit, *spread, length))):
                raise ValueError(f"Invalid splat at PLY vertex {index}")
            # Stable sigmoid for both signs of the stored opacity logit.
            tail = math.exp(-abs(logit))
            alpha = (1 if logit >= 0 else tail) / (1 + tail)
            payload.extend(layout.pack(x, y, z, qx / length, qy / length, qz / length, w / length,
                                       *spread, alpha, *dc))
            for axis, value in enumerate(xyz):
                low[axis] = min(low[axis], value)
                high[axis] = max(high[axis], value)
        source_bytes = len(data)

    specs = [("POSITION", "VEC3", 0), (EXT + ":ROTATION", "VEC4", 12),
             (EXT + ":SCALE", "VEC3", 28), (EXT + ":OPACITY", "SCALAR", 40),
             (EXT + ":SH_DEGREE_0_COEF_0", "VEC3", 44)]
    accessors = [{"bufferView": 0, "byteOffset": offset, "componentType": 5126,
                  "count": retained, "type": shape} for _, shape, offset in specs]
    accessors[0].update(min=low, max=high)
    doc = {"asset": {"version": "2.0", "copyright": CREDIT,
                     "generator": "OntoKin Delft SH0 display derivative",
                     "extras": {"source": SOURCE_DOI, "license": LICENSE, "sourceSha256": digest}},
           "scene": 0, "scenes": [{"nodes": [0]}], "nodes": [{"mesh": 0, "name": "TU Delft campus"}],
           "extensionsUsed": [EXT], "extensionsRequired": [EXT],
           "meshes": [{"primitives": [{"mode": 0, "attributes": {s[0]: i for i, s in enumerate(specs)},
                                       "extensions": {EXT: {"kernel": "ellipse",
                                                            "colorSpace": "srgb_rec709_display"}}}]}],
           "buffers": [{"byteLength": len(payload)}],
           "bufferViews": [{"buffer": 0, "byteLength": len(payload), "byteStride": layout.size,
                            "target": 34962}], "accessors": accessors}
    metadata = json.dumps(doc, separators=(",", ":"), allow_nan=False).encode("utf-8")
    metadata += b" " * (-len(metadata) % 4)
    blob = (struct.pack("<4sIII4s", b"glTF", 2, 28 + len(metadata) + len(payload), len(metadata), b"JSON")
            + metadata + struct.pack("<I4s", len(payload), b"BIN\0") + payload)
    output.write_bytes(blob)
    return {"source": SOURCE_DOI, "credit": CREDIT, "license": LICENSE, "sourceSha256": digest,
            "sourceBytes": source_bytes, "sourceSplats": count, "sourceBoundsFilter": bbox,
            "eligibleSplats": len(eligible), "maxSplats": max_splats, "retainedSplats": retained,
            "selection": "Middle source index in each equal-sized interval of eligible records.",
            "coordinates": "Original PLY XYZ, identity node transform.",
            "attributes": "Float32 XYZ and SH0 retained. Exponentiate log scales, sigmoid opacity, "
                          "normalize quaternion and reorder wxyz to xyzw. Omit SH degrees 1 to 3 and normals.",
            "positionMin": low, "positionMax": high,
            "glbBytes": len(blob), "glbSha256": hashlib.sha256(blob).hexdigest()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--max-splats", type=int, default=120_000)
    parser.add_argument("--bbox", type=float, nargs=6, metavar=("XMIN", "YMIN", "ZMIN", "XMAX", "YMAX", "ZMAX"))
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if len({p.resolve() for p in (args.source, args.output, args.report)}) != 3:
        parser.error("Use distinct input, GLB and report paths")
    try:
        report = convert(args.source, args.output, args.max_splats, args.bbox)
        args.report.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    except (ValueError, OSError, OverflowError) as exc:
        parser.exit(1, f"Delft conversion failed: {exc}\n")
