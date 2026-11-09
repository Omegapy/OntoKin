"""Create the small, deterministic appearance fixture for the composite viewer."""

import json
from pathlib import Path
import struct


def generate():
    # Coordinates are metres in the service entrance's +Y-up frame.
    positions = []
    colors = []
    scales = []

    def add(x, y, z, color, scale):
        positions.append((x, y, z))
        colors.append(color)
        scales.append(scale)

    for ix in range(-16, 17):
        for iz in range(-14, 15):
            tint = ((ix + iz) % 5) / 65
            add(ix * 0.14, -0.055, iz * 0.14, (0.26 + tint, 0.33 + tint, 0.36 + tint),
                (0.10, 0.012, 0.10))
    for ix in range(-16, 17):
        for iy in range(13):
            tint = (iy % 4) / 70
            add(ix * 0.14, iy * 0.14, -2.04, (0.33 + tint, 0.40 + tint, 0.42 + tint),
                (0.095, 0.095, 0.018))
    # Striped screen for observing the cart crossing its depth plane.
    for ix in range(-2, 3):
        for iy in range(6):
            color = (0.62, 0.28, 0.30) if iy % 3 else (0.88, 0.58, 0.45)
            add(ix * 0.10, 0.01 + iy * 0.10, -0.34, color, (0.072, 0.072, 0.015))

    extension = "KHR_gaussian_splatting"
    count = len(positions)
    payload = bytearray()
    views = []
    accessors = []
    attributes = {}

    def attribute(name, shape, width, rows, bounds=False):
        start = len(payload)
        for row in rows:
            payload.extend(struct.pack("<" + "f" * width, *row))
        index = len(views)
        views.append({"buffer": 0, "byteOffset": start, "byteLength": len(payload) - start,
                      "target": 34962})
        accessor = {"bufferView": index, "componentType": 5126, "count": count, "type": shape}
        if bounds:
            accessor.update(min=list(map(min, zip(*positions))), max=list(map(max, zip(*positions))))
        accessors.append(accessor)
        attributes[name] = index

    attribute("POSITION", "VEC3", 3, positions, bounds=True)
    attribute(extension + ":ROTATION", "VEC4", 4, [(0, 0, 0, 1)] * count)
    attribute(extension + ":SCALE", "VEC3", 3, scales)
    attribute(extension + ":OPACITY", "SCALAR", 1, [(0.89,)] * count)
    attribute(extension + ":SH_DEGREE_0_COEF_0", "VEC3", 3,
              [tuple((channel - 0.5) / 0.2820947917738781 for channel in rgb) for rgb in colors])
    doc = {"asset": {"version": "2.0", "generator": "OntoKin synthetic registration screen"},
           "extensionsUsed": [extension], "extensionsRequired": [extension], "scene": 0,
           "scenes": [{"nodes": [0]}], "nodes": [{"mesh": 0, "name": "Synthetic room and screen"}],
           "meshes": [{"primitives": [{"mode": 0, "attributes": attributes, "extensions": {
               extension: {"kernel": "ellipse", "colorSpace": "srgb_rec709_display"}}}]}],
           "buffers": [{"byteLength": len(payload)}], "bufferViews": views, "accessors": accessors}
    text = bytearray(json.dumps(doc, separators=(",", ":")).encode())
    text.extend(b" " * (-len(text) % 4))
    return (struct.pack("<4sII", b"glTF", 2, 28 + len(text) + len(payload)) +
            struct.pack("<I4s", len(text), b"JSON") + text +
            struct.pack("<I4s", len(payload), b"BIN\0") + payload)


if __name__ == "__main__":
    Path(__file__).with_name("registration-screen.glb").write_bytes(generate())
