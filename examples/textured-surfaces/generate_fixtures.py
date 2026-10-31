#!/usr/bin/env python3
"""Author independent C080 inputs without importing or executing OntoKin.

The PNG writer starts from explicit pixels. UV expectations use Fraction on
authored binary64 numbers, with one final binary64 then binary32 conversion.
No production mesh, parser, decoder, exporter or validation result is an oracle.
Run only while preparing a separately reviewed input freeze, never to repair a
frozen expectation after a failed product run.
"""
from __future__ import annotations

import base64
from collections import Counter
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import struct
import zlib

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
ADOPTION_COMMIT = "36a3bf43d3b5f798b78e271598810e56fd377a91"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
ASSETS = {}
CASES = []


def sha(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def save(name, data):
    path = ROOT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data.encode("utf-8") if isinstance(data, str) else data)
    path.chmod(0o644)
    return name


def save_json(name, value):
    return save(name, json.dumps(value, indent=2, ensure_ascii=False,
                                 allow_nan=False) + "\n")


def chunk(kind, payload, *, bad_crc=False):
    crc = zlib.crc32(kind + payload) & 0xffffffff
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", crc ^ bool(bad_crc))


def ihdr(width, height, *, channels=3, depth=8, color_type=None,
         compression=0, filter_method=0, interlace=0):
    return struct.pack(">IIBBBBB", width, height, depth,
                       color_type if color_type is not None else {3: 2, 4: 6}[channels],
                       compression, filter_method, interlace)


def paeth(left, above, upper_left):
    prediction = left + above - upper_left
    distances = [abs(prediction - x) for x in (left, above, upper_left)]
    return (left, above, upper_left)[distances.index(min(distances))]


def filtered_rows(width, height, channels, pixels, filters):
    result = bytearray()
    stride = width * channels
    for y in range(height):
        row = pixels[y * stride:(y + 1) * stride]
        previous = pixels[(y - 1) * stride:y * stride] if y else bytes(stride)
        method = filters[y % len(filters)]
        result.append(method)
        for x, value in enumerate(row):
            left = row[x - channels] if x >= channels else 0
            above = previous[x]
            upper_left = previous[x - channels] if x >= channels else 0
            prediction = (0, left, above, (left + above) // 2,
                          paeth(left, above, upper_left))[method]
            result.append((value - prediction) & 255)
    return bytes(result)


def png_bytes(width, height, channels, pixels, *, filters=(0,), idat_chunks=1,
              compressed=None, header=None, extras=()):
    data = zlib.compress(filtered_rows(width, height, channels, pixels, filters), 9) if compressed is None else compressed
    pieces = [data[len(data) * n // idat_chunks:len(data) * (n + 1) // idat_chunks]
              for n in range(idat_chunks)]
    return (PNG_SIGNATURE + chunk(b"IHDR", header or ihdr(width, height, channels=channels))
            + b"".join(chunk(kind, value) for kind, value in extras)
            + b"".join(chunk(b"IDAT", part) for part in pieces) + chunk(b"IEND", b""))


def asset(name, raw, *, width=None, height=None, channels=None, pixels=None,
          filters=None, description="", expected_valid=True):
    filename = save("assets/" + name + ".png", raw)
    record = {"path": filename, "sha256": sha(raw), "byte_length": len(raw),
              "expected_png_valid": expected_valid, "description": description}
    if pixels is not None:
        probes = sorted({(0, 0), (width - 1, 0), (0, height - 1),
                         (width - 1, height - 1), (width // 2, height // 2)})
        record.update(width=width, height=height, channels=channels,
                      decoded_bytes=len(pixels), decoded_sha256=sha(pixels),
                      filtered_bytes=height * (1 + width * channels),
                      row_filters=list(filters or [0]),
                      pixel_probes=[{"xy": [x, y], "channels": list(pixels[(y * width + x) * channels:(y * width + x + 1) * channels])}
                                    for x, y in probes],
                      row_sha256=[sha(pixels[y * width * channels:(y + 1) * width * channels]) for y in range(height)])
        if width * height <= 40:
            record["complete_pixels_top_to_bottom"] = [list(pixels[y * width * channels:(y + 1) * width * channels]) for y in range(height)]
    ASSETS[name] = record
    return name


def make_images():
    rgb = bytes([
        255, 0, 0,  0, 255, 0,  0, 0, 255,  255, 255, 0,
        0, 255, 255,  255, 0, 255,  128, 128, 128,  10, 11, 12,
        255, 255, 255,  0, 0, 0,  40, 80, 160,  255, 128, 0,
    ])
    rgba = bytes(channel for y in range(4) for x in range(3)
                 for channel in ((x * 101 + y * 17) % 256,
                                 (x * 29 + y * 71) % 256,
                                 (x * 43 + y * 53) % 256, 255))
    asset("asymmetric-rgb", png_bytes(4, 3, 3, rgb), width=4, height=3,
          channels=3, pixels=rgb, description="Literal 4 by 3 RGB array with twelve distinct texels")
    asset("asymmetric-rgba", png_bytes(3, 4, 4, rgba, filters=(4, 3, 2, 1)), width=3,
          height=4, channels=4, pixels=rgba, filters=(4, 3, 2, 1),
          description="Non-square opaque RGBA array; Paeth, average, up and sub rows")
    for f in range(5):
        asset("filter-" + str(f), png_bytes(4, 3, 3, rgb, filters=(f,)), width=4, height=3,
              channels=3, pixels=rgb, filters=(f,), description="Same pixels encoded using PNG filter " + str(f))
    asset("idat-64", png_bytes(4, 3, 3, rgb, idat_chunks=64), width=4, height=3,
          channels=3, pixels=rgb, description="Exactly 64 contiguous IDAT chunks; zero-length chunks retained")
    asset("one-pixel", png_bytes(1, 1, 3, b"\x80\x20\xf0"), width=1, height=1,
          channels=3, pixels=b"\x80\x20\xf0", description="Minimum dimensions")

    # Pixel glyphs are authored here; no host font or image library participates.
    glyphs = {"C": ["11111", "10000", "10000", "10000", "10000", "10000", "11111"],
              "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
              "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
              "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
              "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
              "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
              "N": ["10001", "11001", "11001", "10101", "10011", "10011", "10001"]}
    label = bytearray([255, 220, 0] * (128 * 64))
    def pixel(x, y, color):
        label[(y * 128 + x) * 3:(y * 128 + x + 1) * 3] = bytes(color)
    for letter_no, letter in enumerate("CAUTION"):
        for gy, line in enumerate(glyphs[letter]):
            for gx, bit in enumerate(line):
                if bit == "1":
                    for dy in range(2):
                        for dx in range(2):
                            pixel(22 + letter_no * 12 + gx * 2 + dx, 20 + gy * 2 + dy, (0, 0, 0))
    for y in range(44, 48):
        for x in range(24, 100):
            pixel(x, y, (0, 0, 0))
    for dx in range(10):
        for dy in range(-dx, dx + 1):
            pixel(109 - dx, 46 + dy, (0, 0, 0))
    for ox, oy, color in [(0, 0, (255, 0, 0)), (120, 0, (0, 255, 0)),
                           (0, 56, (0, 0, 255)), (120, 56, (255, 255, 255))]:
        for y in range(oy, oy + 8):
            for x in range(ox, ox + 8):
                pixel(x, y, color)
    asset("caution-label", png_bytes(128, 64, 3, label, filters=(0, 1, 2, 3, 4)),
          width=128, height=64, channels=3, pixels=bytes(label), filters=(0, 1, 2, 3, 4),
          description="CAUTION glyphs and right arrow; red/green/blue/white corner markers")
    maximum = bytes(channel for y in range(256) for x in range(256)
                    for channel in (x, y, (x * 73 + y * 151) % 256, 255))
    asset("maximum-rgba", png_bytes(256, 256, 4, maximum, filters=(0, 1, 2, 3, 4)),
          width=256, height=256, channels=4, pixels=maximum, filters=(0, 1, 2, 3, 4),
          description="Maximum decoded size, 262144 channel bytes")

    # Empty nonfinal stored DEFLATE blocks deliberately approach encoded-byte
    # limits without unbounded output. Five IDAT chunks make the total exact.
    scanline = b"\x00\x80\x20\xf0"
    compressed = (b"\x78\x01" + b"\x00\x00\x00\xff\xff" * 59976
                  + b"\x01\x04\x00\xfb\xff" + scanline
                  + struct.pack(">I", zlib.adler32(scanline) & 0xffffffff))
    padded = png_bytes(1, 1, 3, b"\x80\x20\xf0", compressed=compressed, idat_chunks=5)
    assert len(padded) == 300000
    assert zlib.decompress(compressed) == scanline
    asset("encoded-limit", padded, width=1, height=1, channels=3, pixels=b"\x80\x20\xf0",
          description="Exactly 300000 encoded bytes, one complete zlib stream, five IDAT chunks")
    header = ihdr(4, 3)
    rows = filtered_rows(4, 3, 3, rgb, (0,))
    data = zlib.compress(rows, 9)
    normal = PNG_SIGNATURE + chunk(b"IHDR", header) + chunk(b"IDAT", data) + chunk(b"IEND", b"")
    bad = {
        "bad-signature": b"badPNG!!" + normal[8:],
        "bad-ihdr-crc": PNG_SIGNATURE + chunk(b"IHDR", header, bad_crc=True) + normal[33:],
        "bad-idat-crc": PNG_SIGNATURE + chunk(b"IHDR", header) + chunk(b"IDAT", data, bad_crc=True) + chunk(b"IEND", b""),
        "bad-iend-crc": normal[:-12] + chunk(b"IEND", b"", bad_crc=True),
        "duplicate-ihdr": normal[:33] + chunk(b"IHDR", header) + normal[33:],
        "idat-before-ihdr": PNG_SIGNATURE + chunk(b"IDAT", data) + chunk(b"IHDR", header) + chunk(b"IEND", b""),
        "missing-idat": normal[:33] + chunk(b"IEND", b""),
        "missing-iend": normal[:-12],
        "nonempty-iend": normal[:-12] + chunk(b"IEND", b"x"),
        "trailing-png-byte": normal + b"x",
        "truncated-chunk": normal[:-5],
        "ancillary-chunk": normal[:33] + chunk(b"tEXt", b"author\x00independent fixture") + normal[33:],
        "critical-chunk": normal[:33] + chunk(b"ABCD", b"x") + normal[33:],
        "noncontiguous-idat": normal[:33] + chunk(b"IDAT", data[:3]) + chunk(b"tEXt", b"x") + chunk(b"IDAT", data[3:]) + chunk(b"IEND", b""),
        "idat-65": png_bytes(4, 3, 3, rgb, idat_chunks=65),
        "bad-zlib-checksum": png_bytes(4, 3, 3, rgb, compressed=data[:-1] + bytes([data[-1] ^ 1])),
        "truncated-zlib": png_bytes(4, 3, 3, rgb, compressed=data[:-2]),
        "trailing-zlib-byte": png_bytes(4, 3, 3, rgb, compressed=data + b"x"),
        "second-zlib-stream": png_bytes(4, 3, 3, rgb, compressed=data + zlib.compress(b"")),
        "decoded-one-extra": png_bytes(4, 3, 3, rgb, compressed=zlib.compress(rows + b"x")),
        "decoded-one-short": png_bytes(4, 3, 3, rgb, compressed=zlib.compress(rows[:-1])),
        "bad-filter-5": png_bytes(4, 3, 3, rgb, compressed=zlib.compress(b"\x05" + rows[1:])),
        "oversized-encoded": padded + b"x",
        "nonopaque-alpha": png_bytes(1, 1, 4, b"\x10\x20\x30\xfe"),
    }
    for name, changes in [("width-zero", {"width": 0}), ("width-257", {"width": 257}),
                          ("height-zero", {"height": 0}), ("height-257", {"height": 257}),
                          ("depth-16", {"depth": 16}), ("indexed-color", {"color_type": 3}),
                          ("grayscale", {"color_type": 0}), ("interlaced", {"interlace": 1}),
                          ("compression-method", {"compression": 1}), ("filter-method", {"filter_method": 1})]:
        bad[name] = png_bytes(4, 3, 3, rgb, header=ihdr(**{"width": 4, "height": 3, **changes}))
    dictionary = zlib.compressobj(zdict=b"fixture dictionary")
    bad["zlib-dictionary"] = png_bytes(4, 3, 3, rgb, compressed=dictionary.compress(rows) + dictionary.flush())
    for name, raw in bad.items():
        asset(name, raw, expected_valid=False, description="Deliberate hostile input: " + name)


def n(value):
    return str(value)


def vector(values, unit):
    return "vec3(" + ", ".join(n(value) + "[" + unit + "]" for value in values) + ")"


def mapping(origin=(0, 0, 0), u=(0.25, 0, 0), v=(0, -0.5, 0), offset=(0, 1)):
    return {"origin_m": list(origin), "u_per_m": list(u), "v_per_m": list(v), "offset": list(offset)}


def mapping_source(m):
    return "planar_uv(" + ", ".join([vector(m["origin_m"], "m"), vector(m["u_per_m"], "m^-1"),
                                    vector(m["v_per_m"], "m^-1"), *map(n, m["offset"])]) + ")"


def image_ref(name, image_id="label"):
    return 'png_asset(' + json.dumps(image_id) + ', ' + json.dumps(ASSETS[name]["sha256"]) + ')'


def palette(keys=("bottom", "side", "top", "floor", "inner", "unused"), color=(1, 1, 1, 1)):
    return "keyed<SurfaceMaterial> {\n" + ",\n".join(
        '        "' + key + '": surface_material(rgba(' + ", ".join(map(n, color)) + '), 0.0, 0.7)'
        for key in keys) + "\n    }"


def outline(points=((0, 0), (4, 0), (4, 2), (0, 2)), region="side"):
    return "keyed<PolygonVertex> {\n" + ",\n".join(
        '        "v' + str(i) + '": polygon_vertex(' + str(i * 10) + ", planar_point("
        + str(x) + "[m], " + str(y) + '[m]), "' + region + '")'
        for i, (x, y) in enumerate(points)) + "\n    }"


def base_geometry(family="extrusion", points=((0, 0), (4, 0), (4, 2), (0, 2)), color=(1, 1, 1, 1)):
    outer = outline(points)
    pal = palette(color=color)
    if family == "extrusion":
        return "extrude(" + outer + ", " + pal + ', 0.25[m], "bottom", "top")'
    if family == "pockets":
        pocket = outline(((1, 0.5), (1, 1.5), (3, 1.5), (3, 0.5)), "inner")
        return ("extrude_pockets(" + outer + ', keyed<PolygonPocket> { "recess": polygon_pocket(10, '
                + pocket + ', 0.5[m], "floor") }, ' + pal + ', 2[m], "bottom", "top")')
    if family == "holes":
        hole = outline(((1, 0.5), (1, 1.5), (3, 1.5), (3, 0.5)), "inner")
        return ('extrude_rings(keyed<PolygonRing> { "outer": polygon_ring(10, "outer", ' + outer
                + '), "hole": polygon_ring(20, "hole", ' + hole + ') }, ' + pal + ', 0.25[m], "bottom", "top")')
    if family in ("ring_loft", "framed_loft"):
        rings = 'keyed<PolygonRing> { "outer": polygon_ring(10, "outer", ' + outer + ') }'
        if family == "ring_loft":
            sections = 'keyed<PolygonSection> { "s0": polygon_section(0, 0[m], ' + rings + '), "s1": polygon_section(10, 1[m], ' + rings + ') }'
            return 'loft_rings(' + sections + ', ' + pal + ', "bottom", "top")'
        sections = ('keyed<FramedPolygonSection> { "s0": framed_polygon_section(0, pose(self.frame, vec3(0[m], 0[m], 0[m]), quat(1, 0, 0, 0)), '
                    + rings + '), "s1": framed_polygon_section(10, pose(self.frame, vec3(0[m], 0[m], 1[m]), quat(1, 0, 0, 0)), ' + rings + ') }')
        return 'loft_framed_rings(' + sections + ', ' + pal + ', "bottom", "top")'
    if family == "loft":
        return ('loft(keyed<LoftSection> { "lower": loft_section(0[m], vec3(0[m], 0[m], 0[m]), 1[m], 1[m], "side"), '
                + '"upper": loft_section(1[m], vec3(0[m], 0[m], 0[m]), 1[m], 1[m], "side") }, ' + pal + ', 4, "flat")')
    raise ValueError(family)


SCENE = '''scene Demo @ "demo" {
    duration = 1[s];
    gravity = vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2]);
    object shape @ "shape": Shape {
        placement = pose(world, vec3(0[m], 0[m], 0[m]), quat(1, 0, 0, 0));
    }
    action travel @ "travel" = move(shape, vector(world, 0[m/s], 0.5[m/s], 0[m/s]), 1[s]);
    at 0[s] sequence { start travel; }
}
'''


def program(*, image="asymmetric-rgb", image_id="label", m=None, bindings=None,
            family="extrusion", points=((0, 0), (4, 0), (4, 2), (0, 2)),
            color=(1, 1, 1, 1), geometry=None, placed=False, high=False,
            extra_definitions="", extra_members="", no_texture=False):
    m = m or mapping()
    geometry = geometry or base_geometry(family, points, color)
    bindings = bindings if bindings is not None else [("top" if family != "loft" else "side", image, image_id, m)]
    if not no_texture:
        pairs = [json.dumps(region) + ': texture_binding(' + image_ref(a, identity) + ', ' + mapping_source(mp) + ')'
                 for region, a, identity, mp in bindings]
        geometry = "texture_surface(" + geometry + ", keyed<TextureBinding> { " + ", ".join(pairs) + " })"
    if placed:
        geometry = "placed(" + geometry + ", pose(self.frame, vec3(2[m], -3[m], 1[m]), quat(0.5, 0.5, 0.5, 0.5)))"
    return ('ontokin "0.13";\nmodule TextureCase @ "texture-case";\nprofile "textured-surfaces-0.1";\n\n'
            + ('execution { max_operations = 2000000; max_elapsed = 80[s]; }\n\n' if high else '')
            + extra_definitions + '\npublic class Shape @ "shape" {\n' + extra_members
            + '    geometry = ' + geometry + ';\n    physical = no_body();\n}\n\n' + SCENE)


def manifest_for(source_path, attachments, modules=()):
    return {"schema_version": "ontokin.files/0.2",
            "entry": {"filename": "main.ok", "path": source_path},
            "modules": [{"package_id": p, "version": "1.0.0", "filename": Path(path).name, "path": path}
                        for p, path in modules],
            "assets": [{"asset_id": identity, "sha256": ASSETS[name]["sha256"], "media_type": "image/png", "path": ASSETS[name]["path"]}
                       for identity, name in attachments]}


def independent_revision(manifest):
    units = [{"source_id": "entry", "package_id": None, "version": None,
              "filename": manifest["entry"]["filename"],
              "source_revision": sha((ROOT / manifest["entry"]["path"]).read_bytes())}]
    for module in manifest["modules"]:
        units.append({"source_id": "package:" + module["package_id"] + "@" + module["version"],
                      "package_id": module["package_id"], "version": module["version"],
                      "filename": module["filename"], "source_revision": sha((ROOT / module["path"]).read_bytes())})
    canonical = {"schema_version": "ontokin.bundle/0.2", "entry_source_id": "entry",
                 "units": sorted(units, key=lambda x: x["source_id"]),
                 "assets": sorted([{"asset_id": x["asset_id"], "media_type": x["media_type"],
                                    "sha256": x["sha256"], "byte_length": len((ROOT / x["path"]).read_bytes())}
                                   for x in manifest["assets"]], key=lambda x: x["asset_id"])}
    raw = json.dumps(canonical, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()
    return {"program_revision": sha(b"ontokin.bundle/0.2\0" + raw), "canonical_manifest": canonical}


def case(name, source, attachments=(("label", "asymmetric-rgb"),), *, outcome="valid",
         code=None, stage="delivered", notes="", bindings=None, family="extrusion",
         modules=(), high=False, companion=True, tags=()):
    source_path = save("sources/" + name + ".ok", source)
    manifest = manifest_for(source_path, attachments, modules)
    manifest_path = save_json(name + ".files.json", manifest)
    record = {"id": "T" + str(len(CASES) + 1).zfill(3), "name": name,
              "source": source_path, "file_manifest": manifest_path,
              "expected_outcome": outcome, "expected_code": code,
              "expected_stage": stage, "notes": notes, "tags": list(tags),
              "host_policy": {"max_operations": 2000000, "max_elapsed_ms": 80000} if high else
                             {"max_operations": 100000, "max_elapsed_ms": 30000},
              "family": family, **independent_revision(manifest)}
    if bindings is None and outcome == "valid" and attachments and not modules:
        identity, image = attachments[0]
        bindings = [("side" if family == "loft" else "top", image, identity, mapping())]
    if bindings is not None:
        record["texture_bindings"] = [{"region": region, "asset_id": identity, "image": a, "mapping": m}
                                      for region, a, identity, m in bindings]
    CASES.append(record)
    return record


def invalid_source(name, source, code, *, stage="represented", attachments=(("label", "asymmetric-rgb"),), notes=""):
    return case(name, source, attachments, outcome="source_rejected", code=code, stage=stage,
                notes=notes, companion=False)


def make_sources():
    base = program()
    case("rgb-panel", base, bindings=[("top", "asymmetric-rgb", "label", mapping())], tags=["orientation", "rgb", "motion"])
    case("rgba-panel", program(image="asymmetric-rgba"), (("label", "asymmetric-rgba"),),
         bindings=[("top", "asymmetric-rgba", "label", mapping())], tags=["rgba", "non-square"])
    case("warning-panel", program(image="caution-label"), (("label", "caution-label"),),
         bindings=[("top", "caution-label", "label", mapping())], tags=["label", "browser"])
    for f in range(5):
        image = "filter-" + str(f)
        case(image, program(image=image), (("label", image),), tags=["png-row-filter"])
    for image in ("idat-64", "one-pixel", "encoded-limit"):
        case(image, program(image=image), (("label", image),), tags=["png-boundary"])
    for name, m in [
        ("offset-clamp", mapping(offset=(-0.5, 1.5))),
        ("reflection", mapping(u=(-0.25, 0, 0), offset=(1, 1))),
        ("shear", mapping(u=(0.25, 0.125, 0), v=(0, -0.5, 0))),
        ("origin-boundary", mapping(origin=(256, -256, 256))),
        ("basis-and-uv-boundary", mapping(u=(1024, 0, 0), v=(0, 1024, 0), offset=(0, 0))),
        ("offset-boundary", mapping(offset=(1024, -1024))),
        ("exact-rank-no-epsilon", mapping(u=(1, 0, 0), v=(1, 5e-324, 0), offset=(0, 0))),
        ("uv-binary32-underflow", mapping(u=(5e-324, 0, 0), v=(0, 1, 0), offset=(0, 0))),
    ]:
        case(name, program(m=m), bindings=[("top", "asymmetric-rgb", "label", m)], tags=["mapping"])
    witness = mapping(origin=(-0.2, 0, 0), u=(1, 0, 0), v=(0, 1, 0), offset=(-0.3, 0))
    case("exact-rational-uv", program(m=witness, points=((0.1, 0), (4, 0), (4, 2), (0.1, 2))),
         bindings=[("top", "asymmetric-rgb", "label", witness)],
         notes="At x=0.1, exact complete U=2^-55; intermediate rounded subtraction incorrectly gives 2^-54.", tags=["exact-arithmetic"])
    case("placed-mapping", program(placed=True), bindings=[("top", "asymmetric-rgb", "label", mapping())],
         notes="Authored mapping stays in raw unplaced coordinates under cyclic rigid visual placement.", tags=["placement"])
    case("color-factor", program(color=(0.5, 0.25, 0.75, 1)), tags=["color-transfer"])
    wall = mapping(u=(0.25, 0, 0), v=(0, 0, -0.5), offset=(0, 1))
    floor = mapping(origin=(1, 0.5, 0), u=(0.5, 0, 0), v=(0, -1, 0), offset=(0, 1))
    pocket_bindings = [("floor", "caution-label", "label", floor), ("inner", "asymmetric-rgba", "wall", wall)]
    case("marked-tray", program(family="pockets", bindings=pocket_bindings),
         (("label", "caution-label"), ("wall", "asymmetric-rgba")), bindings=pocket_bindings,
         family="pockets", tags=["pocket-floor", "pocket-walls", "browser"])
    case("uv-line-projection", program(bindings=[("side", "asymmetric-rgb", "label", mapping())]),
         bindings=[("side", "asymmetric-rgb", "label", mapping())], tags=["allowed-uv-degeneracy"])
    unused = [("unused", "asymmetric-rgb", "label", mapping(u=(1024, 0, 0), v=(0, 1024, 0), offset=(1024, 1024)))]
    case("unused-palette-binding", program(bindings=unused), bindings=unused,
         notes="No region corners are referenced. Image is validated/inspectable; GLB has zero embedded images/textures.", tags=["unused-palette"])
    extra = 'public fn spare @ "spare"() -> TextureImage { return ' + image_ref("asymmetric-rgba", "spare") + '; }\n'
    case("uninstantiated-declaration", program(extra_definitions=extra),
         (("label", "asymmetric-rgb"), ("spare", "asymmetric-rgba")), tags=["closure", "unused-definition"])
    same = 'public fn spare @ "spare"() -> TextureImage { return ' + image_ref("asymmetric-rgb") + '; }\n'
    case("repeated-same-declaration", program(extra_definitions=same), tags=["closure"])
    aliases = [("top", "asymmetric-rgb", "label", mapping()), ("bottom", "asymmetric-rgb", "alias", mapping())]
    case("same-bytes-distinct-ids", program(bindings=aliases), (("label", "asymmetric-rgb"), ("alias", "asymmetric-rgb")),
         bindings=aliases, notes="Two declared IDs require two GLB images even though exact byte payloads match.", tags=["identity"])
    case("empty-assets-untextured", program(no_texture=True), (), tags=["empty-closure"])
    identity_max = "a" * 64
    case("asset-id-maximum", program(image_id=identity_max), ((identity_max, "asymmetric-rgb"),), tags=["identity-boundary"])
    sixteen_keys = ["bottom", "side", "top", *["unused" + str(i) for i in range(13)]]
    sixteen_geometry = base_geometry().replace(palette(), palette(sixteen_keys))
    sixteen_bindings = [(key, "asymmetric-rgb", "label", mapping()) for key in sixteen_keys]
    case("sixteen-bindings", program(geometry=sixteen_geometry, bindings=sixteen_bindings),
         bindings=sixteen_bindings, tags=["binding-boundary", "unused-palette"])
    for family in ("holes", "ring_loft", "framed_loft", "loft"):
        region = "side" if family == "loft" else "top"
        case("inherited-" + family, program(family=family), family=family,
             bindings=[(region, "asymmetric-rgb", "label", mapping())], tags=["inherited-family"])
    maximum = case("maximum-decoded-one", program(image="maximum-rgba", high=True), (("label", "maximum-rgba"),),
                   high=True, tags=["decoded-limit", "explicit-budget"])
    for image, name, high in [("maximum-rgba", "maximum-decoded-four", True), ("encoded-limit", "maximum-encoded-four", False)]:
        bindings = [(region, image, "image" + str(i), mapping()) for i, region in enumerate(("top", "bottom", "side", "unused"))]
        case(name, program(bindings=bindings, high=high), tuple(("image" + str(i), image) for i in range(4)),
             high=high, bindings=bindings, tags=["aggregate-boundary"])
    case("maximum-decoded-default-budget", program(image="maximum-rgba"), (("label", "maximum-rgba"),),
         outcome="resource_rejected", code="OKL-E-RESOURCE", stage="represented",
         notes="262144 reconstructed channel-byte debits alone exceed the unchanged 100000 default.", tags=["default-budget"])

    for name, m in [("origin-one-over", mapping(origin=(math.nextafter(256, math.inf), 0, 0))),
                    ("basis-one-over", mapping(u=(math.nextafter(1024, math.inf), 0, 0))),
                    ("offset-one-over", mapping(offset=(math.nextafter(1024, math.inf), 0))),
                    ("rank-zero", mapping(u=(0, 0, 0))),
                    ("rank-dependent", mapping(u=(1, 2, 3), v=(2, 4, 6)))]:
        invalid_source(name, program(m=m), "OKL-E-TEXTURE-MAPPING")
    invalid_source("uv-one-over", program(m=mapping(u=(1024, 0, 0), v=(0, 1, 0), offset=(0, 0)),
                                         points=((0, 0), (4.000000000000001, 0), (4.000000000000001, 2), (0, 2))),
                   "OKL-E-TEXTURE-MAPPING", stage="constructed")
    invalid_source("wrong-origin-unit", base.replace("vec3(0[m], 0[m], 0[m]), vec3(0.25", "vec3(0[s], 0[s], 0[s]), vec3(0.25"), "OKL-E-TYPE")
    invalid_source("wrong-basis-unit", base.replace("0.25[m^-1]", "0.25[m]"), "OKL-E-TYPE")
    invalid_source("wrong-binding-type", base.replace("texture_binding(" + image_ref("asymmetric-rgb"), "texture_binding(7"), "OKL-E-TYPE", attachments=())
    invalid_source("unknown-region", program(bindings=[("absent", "asymmetric-rgb", "label", mapping())]), "OKL-E-TEXTURE-REGION")
    invalid_source("empty-wrapper", program(bindings=[]), "OKL-E-TEXTURE-REGION", attachments=())
    invalid_source("nonopaque-material", program(color=(1, 1, 1, 0.5)), "OKL-E-TEXTURE-REGION")
    invalid_source("primitive-wrapper", program(geometry="sphere(1[m])"), "OKL-E-TEXTURE-REGION")
    raw = base_geometry()
    placed = "placed(" + raw + ", pose(self.frame, vec3(0[m], 0[m], 0[m]), quat(1, 0, 0, 0)))"
    invalid_source("already-placed-wrapper", program(geometry=placed), "OKL-E-TEXTURE-REGION")
    inner = "texture_surface(" + raw + ', keyed<TextureBinding> { "top": texture_binding(' + image_ref("asymmetric-rgb") + ', ' + mapping_source(mapping()) + ') })'
    invalid_source("nested-wrapper", program(geometry=inner), "OKL-E-TEXTURE-REGION")
    invalid_source("missing-attachment", base, "OKL-E-ASSET-CLOSURE", attachments=())
    invalid_source("extra-attachment", base, "OKL-E-ASSET-CLOSURE", attachments=(("label", "asymmetric-rgb"), ("extra", "asymmetric-rgba")))
    invalid_source("wrong-source-digest", base, "OKL-E-ASSET-CLOSURE", attachments=(("label", "asymmetric-rgba"),))
    conflict = 'public fn spare @ "spare"() -> TextureImage { return ' + image_ref("asymmetric-rgba") + '; }\n'
    invalid_source("conflicting-declaration", program(extra_definitions=conflict), "OKL-E-ASSET-CLOSURE")
    dynamic = program(extra_members='    public param image_id @ "image-id": String = "label";\n')
    invalid_source("nonliteral-image-id", dynamic.replace('png_asset("label",', 'png_asset(self.image_id,'), "OKL-E-ASSET-CLOSURE")
    digest = ASSETS["asymmetric-rgb"]["sha256"]
    dynamic = program(extra_members='    public param image_digest @ "image-digest": String = ' + json.dumps(digest) + ';\n')
    invalid_source("nonliteral-image-digest", dynamic.replace('png_asset("label", ' + json.dumps(digest) + ')', 'png_asset("label", self.image_digest)'), "OKL-E-ASSET-CLOSURE")
    comment = '// png_asset("ghost", "not-a-digest")\npublic fn text @ "text"() -> String { return "png_asset(ghost, not-a-digest)"; }\n'
    case("comments-and-strings", program(extra_definitions=comment), tags=["closure-lexing"])

    for name, record in list(ASSETS.items()):
        if not record["expected_png_valid"] and name != "oversized-encoded":
            invalid_source("png-" + name, program(image=name), "OKL-E-PNG", attachments=(("label", name),))
    make_modules()
    return base


def make_modules():
    base = base_geometry()
    module = ('ontokin "0.13";\nmodule LabelParts @ "label-parts";\nprofile "textured-surfaces-0.1";\n\n'
              + 'public fn second_image @ "second-image"() -> TextureImage { return ' + image_ref("asymmetric-rgba", "alternate") + '; }\n'
              + 'public class Shape @ "shape" {\n    public param offset_u @ "offset-u": Real = 0;\n'
              + '    public param image @ "image": TextureImage = ' + image_ref("asymmetric-rgb") + ';\n'
              + '    geometry = texture_surface(' + base + ', keyed<TextureBinding> { "top": texture_binding(self.image, '
              + 'planar_uv(vec3(0[m], 0[m], 0[m]), vec3(0.25[m^-1], 0[m^-1], 0[m^-1]), vec3(0[m^-1], -0.5[m^-1], 0[m^-1]), self.offset_u, 1)) });\n'
              + '    physical = no_body();\n}\n')
    path = save("modules/label-parts.ok", module)
    pin = sha(module.encode())
    header = ('ontokin "0.13";\nmodule Assembly @ "assembly";\nprofile "textured-surfaces-0.1";\n'
              + 'import lib @ "label-library" from "fixture.label-parts" version "1.0.0" digest "' + pin + '";\n\n')
    assembly = header + '''scene Demo @ "demo" {
    duration = 1[s];
    gravity = vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2]);
    object first @ "first": lib.Shape {
        placement = pose(world, vec3(-5[m], 0[m], 0[m]), quat(1, 0, 0, 0));
        offset_u = 0.0;
    }
    object sibling @ "sibling": lib.Shape {
        placement = pose(world, vec3(5[m], 0[m], 0[m]), quat(1, 0, 0, 0));
    }
    action travel @ "travel" = move(first, vector(world, 0[m/s], 0.5[m/s], 0[m/s]), 1[s]);
    at 0[s] sequence { start travel; }
}
'''
    attachments = (("label", "asymmetric-rgb"), ("alternate", "asymmetric-rgba"))
    modules = (("fixture.label-parts", path),)
    case("assembly", assembly, attachments, modules=modules, tags=["pinned-library", "siblings"])
    case("assembly-mapping-repaired", assembly.replace("offset_u = 0.0;", "offset_u = 0.25;"), attachments,
         modules=modules, tags=["source-only-repair", "sibling-preservation"])
    case("assembly-image-repaired", assembly.replace("offset_u = 0.0;", "offset_u = 0.0;\n        image = lib.second_image();"),
         attachments, modules=modules, tags=["image-selection-repair", "sibling-preservation"])
    case("assembly-invalid", assembly.replace("offset_u = 0.0;", "offset_u = 1025;"), attachments,
         modules=modules, outcome="source_rejected", code="OKL-E-TEXTURE-MAPPING", stage="represented", tags=["atomic-rollback"])
    generated = header + '''public class Mounted @ "mounted" extends lib.Shape {
    public param parent_frame @ "parent-frame": FrameRef = world;
    public param mount_x @ "mount-x": Length = 0[m];
    public follow mounting @ "mounting" {
        parent = self.parent_frame;
        child = self;
        offset = pose(self.parent_frame, vec3(self.mount_x, 0[m], 0[m]), quat(1, 0, 0, 0));
    }
}
public class Array @ "array-type" {
    public param offsets @ "offsets": Keyed<Real> = keyed<Real> { "left": 0.0, "middle": 0.25, "right": 0.5 };
    geometry = empty();
    physical = no_body();
    public parts panels @ "panels": Mounted for (key, value) in self.offsets {
        parent_frame = self.frame;
        mount_x = value * 20[m];
        offset_u = value;
    }
}
scene Demo @ "demo" {
    duration = 1[s];
    gravity = vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2]);
    object array @ "array": Array { placement = pose(world, vec3(-5[m], 0[m], 0[m]), quat(1, 0, 0, 0)); }
    action travel @ "travel" = move(array, vector(world, 0[m/s], 0.5[m/s], 0[m/s]), 1[s]);
    at 0[s] sequence { start travel; }
}
'''
    case("generated", generated, attachments, modules=modules, tags=["generation", "mapping-cache-isolation"])
    case("generated-repaired", generated.replace('"middle": 0.25', '"middle": 0.375'), attachments,
         modules=modules, tags=["generated-instance-repair"])
    legacy = '''ontokin "0.12";
module Legacy @ "legacy";
profile "polygon-pockets-0.1";
public fn png_asset @ "legacy-name"(name: String, digest: String) -> Real { return 0.25; }
public fn old_call @ "old-call"() -> Real { return png_asset("ghost", "not-a-digest"); }
'''
    legacy_path = save("modules/legacy-name.ok", legacy)
    declaration = 'import old @ "old" from "fixture.legacy-name" version "1.0.0" digest "' + sha(legacy.encode()) + '";\n'
    legacy_source = program(no_texture=True).replace('\n\n\npublic class', '\n\n' + declaration + '\npublic class')
    legacy_source = legacy_source.replace('    geometry = ', '    public derive control @ "control": Real = old.old_call();\n    public derive qualified @ "qualified": Real = old.png_asset("ghost", "not-a-digest");\n    geometry = ', 1)
    assert declaration in legacy_source
    case("older-user-function-png-asset", legacy_source, (), modules=(("fixture.legacy-name", legacy_path),),
         tags=["declaring-profile", "lexical-compatibility"], notes="Earlier user function and qualified calls are not asset declarations.")


def inline_payload(manifest):
    return {"schema_version": "ontokin.bundle/0.2",
            "entry": {"filename": manifest["entry"]["filename"], "source": (ROOT / manifest["entry"]["path"]).read_text()},
            "modules": [{"package_id": x["package_id"], "version": x["version"], "filename": x["filename"],
                         "source": (ROOT / x["path"]).read_text()} for x in manifest["modules"]],
            "assets": [{"asset_id": x["asset_id"], "sha256": x["sha256"], "media_type": x["media_type"],
                        "data_base64": base64.b64encode((ROOT / x["path"]).read_bytes()).decode()} for x in manifest["assets"]]}


def make_transport_cases():
    base = inline_payload(json.loads((ROOT / "rgb-panel.files.json").read_bytes()))
    transport = []
    def add(name, mutate, code="OKA-E-REQUEST", note=""):
        value = json.loads(json.dumps(base))
        mutate(value)
        path = save_json("transport/" + name + ".bundle.json", value)
        transport.append({"id": "B" + str(len(transport) + 1).zfill(3), "name": name,
                          "payload": path, "expected_outcome": "transport_rejected", "expected_code": code,
                          "expected_stage": "bundle_sealing", "notes": note})
    add("duplicate-id", lambda p: p["assets"].append(dict(p["assets"][0])))
    add("invalid-id-uppercase", lambda p: p["assets"][0].update(asset_id="Label"))
    add("invalid-id-traversal", lambda p: p["assets"][0].update(asset_id="../label"))
    add("invalid-id-length", lambda p: p["assets"][0].update(asset_id="a" * 65))
    add("bad-media-type", lambda p: p["assets"][0].update(media_type="image/jpeg"))
    add("bad-digest-syntax", lambda p: p["assets"][0].update(sha256="sha256:" + "A" * 64))
    add("wrong-byte-digest", lambda p: p["assets"][0].update(sha256="sha256:" + "0" * 64))
    add("base64-whitespace", lambda p: p["assets"][0].update(data_base64=" " + p["assets"][0]["data_base64"]))
    add("base64-missing-padding", lambda p: p["assets"][0].update(data_base64=p["assets"][0]["data_base64"].rstrip("=")),
        note="Remove the existing required terminal padding; do not substitute a new canonical final quartet.")
    add("base64-illegal-alphabet", lambda p: p["assets"][0].update(data_base64="_" + p["assets"][0]["data_base64"][1:]))
    add("asset-unknown-field", lambda p: p["assets"][0].update(filename="image.png"))
    add("assets-not-array", lambda p: p.update(assets={}))
    add("missing-assets-field", lambda p: p.pop("assets"))
    add("fifth-image", lambda p: p.update(assets=[{**p["assets"][0], "asset_id": "image" + str(i)} for i in range(5)]), "OKA-E-RESOURCE")
    oversized = (ROOT / ASSETS["oversized-encoded"]["path"]).read_bytes()
    add("encoded-one-over", lambda p: p["assets"][0].update(sha256=sha(oversized), data_base64=base64.b64encode(oversized).decode()), "OKA-E-RESOURCE")
    save_json("transport-cases.json", {"schema_version": "ontokin.c080-independent-transport-cases/0.1", "cases": transport})
    manifest = json.loads((ROOT / "rgb-panel.files.json").read_bytes())
    file_cases = []
    for name, replacement in [("parent-traversal", "../outside.png"), ("absolute-path", "/tmp/outside.png"),
                              ("network-url", "https://example.invalid/image.png")]:
        value = json.loads(json.dumps(manifest)); value["assets"][0]["path"] = replacement
        path = save_json("file-path-" + name + ".files.json", value)
        file_cases.append({"name": name, "file_manifest": path, "expected_code": "OKA-E-REQUEST", "expected_stage": "file_transport"})
    reordered = json.loads((ROOT / "same-bytes-distinct-ids.files.json").read_bytes())
    reordered["assets"].reverse()
    save_json("reordered-assets.files.json", reordered)
    save_json("file-transport-cases.json", {"schema_version": "ontokin.c080-independent-file-transport-cases/0.1",
                                          "cases": file_cases, "additional_isolated_probes": [
        {"name": "symlink-asset", "expected_code": "OKA-E-REQUEST", "expected_stage": "file_transport", "setup": "Create a symlink only in a fresh verification directory; no symlink belongs to the frozen corpus."},
        {"name": "input-overwritten-by-output", "expected_code": "OKA-E-REQUEST", "expected_stage": "cli_output_admission", "setup": "Request a CLI output path equal to any supplied source/image path; all input hashes must remain unchanged."},
        {"name": "mutable-file-during-read", "expected_code": "OKA-E-REQUEST", "expected_stage": "file_transport", "setup": "Mutate an isolated explicitly supplied file during bounded read; unstable bytes cannot be accepted."}]})


def make_companions():
    """Author actual untextured .12 source controls, without compiling them."""
    controls = {}
    def old_header(source):
        return source.replace('ontokin "0.13";', 'ontokin "0.12";', 1).replace(
            'profile "textured-surfaces-0.1";', 'profile "polygon-pockets-0.1";', 1)
    def control(name, source, modules=()):
        path = save("controls/" + name + ".ok", old_header(source))
        manifest = {"schema_version": "ontokin.files/0.1",
                    "entry": {"filename": "main.ok", "path": path},
                    "modules": [{"package_id": package, "version": "1.0.0", "filename": Path(module_path).name,
                                 "path": module_path} for package, module_path in modules]}
        manifest_path = save_json("control-" + name + ".files.json", manifest)
        controls[name] = {"source": path, "file_manifest": manifest_path,
                          "source_revision": sha((ROOT / path).read_bytes()),
                          "expected_source_profile": "polygon-pockets-0.1", "expected_destination": "ontokin.glb/0.12"}
    control("panel", program(no_texture=True))
    control("placed", program(no_texture=True, placed=True))
    control("color", program(no_texture=True, color=(0.5, 0.25, 0.75, 1)))
    control("rational", program(no_texture=True, points=((0.1, 0), (4, 0), (4, 2), (0.1, 2))))
    for family in ("pockets", "holes", "ring_loft", "framed_loft", "loft"):
        control(family, program(no_texture=True, family=family))
    keys = ["bottom", "side", "top", *["unused" + str(i) for i in range(13)]]
    control("sixteen", program(no_texture=True, geometry=base_geometry().replace(palette(), palette(keys))))
    plain_module = ('ontokin "0.12";\nmodule LabelControl @ "label-control";\nprofile "polygon-pockets-0.1";\n'
                    + 'public class Shape @ "shape" {\n    public param offset_u @ "offset-u": Real = 0;\n'
                    + '    geometry = ' + base_geometry() + ';\n    physical = no_body();\n}\n')
    module_path = save("controls/label-control.ok", plain_module)
    original_pin = sha((ROOT / "modules/label-parts.ok").read_bytes())
    control_pin = sha(plain_module.encode())
    for record in CASES:
        if record["expected_outcome"] != "valid":
            continue
        name = record["name"]
        selected = {"placed-mapping": "placed", "color-factor": "color", "exact-rational-uv": "rational",
                    "marked-tray": "pockets", "sixteen-bindings": "sixteen"}.get(name, "panel")
        if name.startswith("inherited-"):
            selected = record["family"]
        if name.startswith("assembly") or name.startswith("generated"):
            source = (ROOT / record["source"]).read_text().replace('"fixture.label-parts"', '"fixture.label-control"').replace(original_pin, control_pin)
            source = source.replace('        image = lib.second_image();\n', '')
            control(name, source, (("fixture.label-control", module_path),))
            selected = name
        if name == "older-user-function-png-asset":
            control(name, (ROOT / record["source"]).read_text(), (("fixture.legacy-name", "modules/legacy-name.ok"),))
            selected = name
        record["untextured_control"] = controls[selected]
    save_json("geometry-controls.json", {"schema_version": "ontokin.c080-independent-untextured-controls/0.1",
                                         "controls": controls,
                                         "scope": "Actual independently authored .12 source companions for all valid source cases; no output is pre-assumed or product executed."})


def rational_uv(point, m):
    delta = [Fraction(float(p)) - Fraction(float(o)) for p, o in zip(point, m["origin_m"])]
    exact = [sum((Fraction(float(c)) * d for c, d in zip(row, delta)), Fraction(float(offset)))
             for row, offset in zip((m["u_per_m"], m["v_per_m"]), m["offset"])]
    binary64 = list(map(float, exact))
    binary32 = [struct.unpack("<f", struct.pack("<f", value))[0] for value in binary64]
    return {"position_m": list(point), "uv_exact": [{"numerator": str(x.numerator), "denominator": str(x.denominator)} for x in exact],
            "uv_binary64": binary64, "uv_binary64_hex": [x.hex() for x in binary64],
            "uv_binary32": binary32, "uv_binary32_le_hex": [struct.pack("<f", x).hex() for x in binary64]}


def make_expectations():
    for record in CASES:
        name = record["name"]
        if name.startswith("assembly") and record["expected_outcome"] == "valid":
            record["occurrences"] = [
                {"object_key": "first", "initial_world_position_m": [-5, 0, 0],
                 "velocity_m_per_s": [0, 0.5, 0],
                 "texture_region": "top", "asset_id": "alternate" if name == "assembly-image-repaired" else "label",
                 "mapping": mapping(offset=(0.25 if name == "assembly-mapping-repaired" else 0, 1))},
                {"object_key": "sibling", "initial_world_position_m": [5, 0, 0],
                 "velocity_m_per_s": [0, 0, 0], "texture_region": "top", "asset_id": "label", "mapping": mapping()}]
        if name.startswith("generated") and record["expected_outcome"] == "valid":
            offsets = [("left", 0), ("middle", 0.375 if name == "generated-repaired" else 0.25), ("right", 0.5)]
            record["occurrences"] = [{"root_object_key": "array", "part_slot_key": "panels", "instance_key": key,
                                       "initial_world_position_m": [-5 + 20 * offset, 0, 0],
                                       "velocity_m_per_s": [0, 0.5, 0], "texture_region": "top", "asset_id": "label",
                                       "mapping": mapping(offset=(offset, 1))} for key, offset in offsets]
        record["expected_material_factors"] = {"baseColorFactor": [0.5, 0.25, 0.75, 1] if name == "color-factor" else [1, 1, 1, 1],
                                               "metallicFactor": 0, "roughnessFactor": 0.7}
        for binding in record.get("texture_bindings", []):
            points = [(0, 0, 0.25), (4, 0, 0.25), (4, 2, 0.25), (0, 2, 0.25)]
            if binding["region"] == "bottom":
                points = [(x, y, 0) for x, y, _ in points]
            if record["name"] == "exact-rational-uv":
                points = [(0.1, 0, 0.25), (4, 0, 0.25), (4, 2, 0.25), (0.1, 2, 0.25)]
            if record["name"] == "marked-tray":
                points = [(1, 0.5, 1.5), (1, 1.5, 1.5), (3, 1.5, 1.5), (3, 0.5, 1.5)] if binding["region"] == "floor" else [(1, 0.5, 1.5), (1, 1.5, 1.5), (1, 0.5, 2), (1, 1.5, 2)]
            if binding["region"] == "unused":
                points = []
            if binding["region"].startswith("unused"):
                points = []
            if record["family"] in ("loft", "ring_loft", "framed_loft", "holes"):
                # Family geometry preservation is checked against the source
                # companion; these are mapping probes, not invented mesh rows.
                binding["probe_role"] = "analytic_mapping_probe_not_claim_of_emitted_corner"
            else:
                binding["probe_role"] = "authored_region_boundary_corners"
            binding["uv_probes"] = [rational_uv(p, binding["mapping"]) for p in points]
    values = []
    for sample in (0, 10, 11, 128, 255):
        c = sample / 255
        linear = c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
        values.append({"sample_byte": sample, "normalized": c, "linear": linear,
                       "factor_rgb": [0.5, 0.25, 0.75], "multiplied_linear_rgb": [linear * x for x in (0.5, 0.25, 0.75)]})
    expectations = {"schema_version": "ontokin.c080-independent-expected/0.1", "adoption_commit": ADOPTION_COMMIT,
                    "status": "predetermined_inputs_not_product_execution", "cases": CASES,
                    "images": ASSETS, "color_probes": values, "color_comparison_absolute_tolerance": 1e-12,
                    "glb_invariants": {
        "sampler": {"magFilter": 9728, "minFilter": 9728, "wrapS": 33071, "wrapT": 33071},
        "uv": "Exact authored binary64 rationals; complete dot/sum once to binary64 then binary32. Full regional accessor length equals position count; nonregional rows are positive zeros.",
        "image": "Exact original PNG bytes and SHA256, one embedded image per used asset ID; unused declared IDs remain inspectable without dangling GLB resources.",
        "material": "Existing linear baseColorFactor, metallic, roughness and back-face behavior unchanged; sRGB image decode precedes linear factor multiplication.",
        "legacy_accessor_bytes": ["POSITION", "NORMAL", "indices", "animation input", "animation translation output", "animation rotation output"],
        "raw_stream_rule": "Match the corresponding untextured source under .12, by occurrence/region and accessor role rather than accessor index. Append UV/image data after existing streams.",
        "motion": {"scope": "Single-object Demo/shape cases. Assembly/generated occurrence records override initial pose and velocity.", "duration_seconds": 1, "velocity_m_per_s": [0, 0.5, 0], "times_seconds": [0, 0.25, 0.5, 0.75, 1], "y_translation_m": [0, 0.125, 0.25, 0.375, 0.5]},
        "precision_boundary": "No guaranteed UV detail resolution. UV underflow, coincidence and line projection are accepted appearance outcomes."},
                    "analytic_geometry": {
        "panel": {"dimensions_m": [4, 2, 0.25], "volume_m3": 2, "surface_area_m2": 19, "triangles": 12},
        "tray": {"exterior_m": [4, 2, 2], "opening_m": [2, 1], "depth_m": 0.5, "floor_z_m": 1.5, "volume_m3": 15, "surface_area_m2": 43, "triangles": 28}},
                    "aggregate_boundary_reasoning": {
        "encoded": "With at most four assets and each at most 300000 bytes, an isolated >1200000 aggregate satisfying both prior bounds is impossible.",
        "decoded": "With at most four assets and each at most 262144 reconstructed bytes, an isolated >1048576 aggregate satisfying both prior bounds is impossible.",
        "coverage": "Exact aggregate boundary cases plus distinct fifth-image and individual one-over refusals; no fictional isolated aggregate witness."}}
    save_json("expected.json", expectations)


def make_workflow_controls():
    controls = {
        "schema_version": "ontokin.c080-independent-workflow-controls/0.1",
        "required_operations": ["discover", "create", "edit", "validate", "inspect", "surface.mesh_page", "evaluate", "reset", "export", "artifact", "status", "cancel"],
        "sequences": [
            {"id": "A01", "name": "source-mapping-repair", "base": "assembly", "candidate": "assembly-mapping-repaired", "expected": "Only first offset_u changes; library, both assets, sibling UVs, all geometry and both motion streams remain exact."},
            {"id": "A02", "name": "image-selection-repair", "base": "assembly", "candidate": "assembly-image-repaired", "expected": "Only first image selection changes; declared asset set and bytes, library, sibling, geometry and motion remain exact."},
            {"id": "A03", "name": "invalid-candidate-rollback", "base": "assembly", "candidate": "assembly-invalid", "expected_code": "OKL-E-TEXTURE-MAPPING", "expected_stage": "edit_candidate_validation", "expected": "Accepted revision and all accepted asset bytes remain unchanged."},
            {"id": "A04", "name": "generated-occurrence-repair", "base": "generated", "candidate": "generated-repaired", "expected": "Only middle mapping and its explicitly coupled mount_x change; left/right library/assets/mapping/motion remain exact. This case does not claim unchanged middle geometry placement."},
            {"id": "A05", "name": "stale-asset-replace", "expected_code": "OKL-E-REVISION", "expected_stage": "edit_preconditions", "request_recipe": "Replace label with a descriptor whose expected_sha256 differs from the original; accepted revision unchanged."},
            {"id": "A06", "name": "atomic-asset-replacement", "expected_stage": "edit_candidate_validation", "request_recipe": "Starting rgb-panel, replace label bytes with asymmetric-rgba and patch the exact source digest in the same candidate; both effects commit together. Omitting the digest patch fails OKL-E-ASSET-CLOSURE."},
            {"id": "A07", "name": "duplicate-asset-change", "expected_code": "OKL-E-REVISION", "expected_stage": "edit_preconditions", "request_recipe": "Touch one original asset ID twice in one candidate; no accepted source/asset changes."},
            {"id": "A08", "name": "asset-slice-roundtrip", "expected_stage": "inspect", "request_recipe": "Read one accepted asset through exact asset selector in small chunks, include EOF request; concatenate decoded slices and match original PNG SHA/length. No cursor/run/time/frame allowed with asset_slice."},
            {"id": "A09", "name": "fresh-host-reauthorization", "base": "maximum-decoded-one", "expected_code": "OKL-E-RESOURCE", "expected_stage": "current_authorization", "request_recipe": "Accept under matching 2000000/80000 policy, reopen under ordinary host ceilings and request inspect/asset slice/export. Retained acceptance grants no authority."},
            {"id": "A10", "name": "caller-reduces-budget", "base": "rgb-panel", "expected_code": "OKL-E-RESOURCE", "expected_stage": "request_work", "request_recipe": "Give a caller operation cap of 1 to an otherwise ordinary accepted request; cap cannot enlarge source authority."},
            {"id": "A11", "name": "cancel-png-or-export", "expected_stage": "cancelled_request", "request_recipe": "Cancel after accepted request during metered PNG reconstruction or texture export; preserve prior accepted state and commit no partial artifact. Use actual protocol cancel and retained request/store evidence."},
            {"id": "A12", "name": "reopen-retry-and-changed-payload", "expected_stage": "durable_request_identity", "request_recipe": "Reopen identical database and retry identical request ID/payload; recover same outcome. Change image bytes under that request ID and reject the changed payload with the inherited request-conflict diagnostic."},
            {"id": "A13", "name": "stale-mapping-page", "expected_code": "OKL-E-REVISION", "expected_stage": "surface_mesh_page", "request_recipe": "Use pre-repair page cursor against repaired program/mapping or sibling query; never return mixed revision UVs."},
            {"id": "A14", "name": "interrupted-publication", "expected_stage": "artifact_publication", "request_recipe": "Interrupt durable publication after bytes prepare but before commit; reopen and reconcile actual request/store outcome. No successful partial PNG-bearing artifact."},
            {"id": "A15", "name": "reordered-transport", "base": "same-bytes-distinct-ids", "candidate_file_manifest": "reordered-assets.files.json", "expected": "Exact program revision and every source/image byte remain the same."},
            {"id": "A16", "name": "successful-asset-add", "base": "rgb-panel", "candidate": "uninstantiated-declaration", "expected_stage": "edit_candidate_validation", "request_recipe": "Insert the exact spare() source declaration from the candidate and add the spare/asymmetric-rgba attachment in one transaction. Verify both commit, the spare asset is inspectable, existing label/source geometry/motion remain unchanged, and the unused spare adds no GLB image."},
            {"id": "A17", "name": "successful-asset-remove", "base": "uninstantiated-declaration", "candidate": "rgb-panel", "expected_stage": "edit_candidate_validation", "request_recipe": "Remove the exact spare() declaration and remove spare using its original SHA256 in the same transaction. The complete accepted revision returns exactly to rgb-panel; label bytes remain exact. Removing the asset without removing its source declaration fails OKL-E-ASSET-CLOSURE and preserves the old accepted revision."},
            {"id": "A18", "name": "stale-asset-metadata-cursor", "base": "assembly", "candidate": "assembly-mapping-repaired", "expected_code": "OKL-E-REVISION", "expected_stage": "inspect_cursor_binding", "request_recipe": "Request texture_asset metadata with a one-item page, retain its cursor, accept the mapping repair, and attempt to use the old cursor against the repaired revision. Refuse mixed-revision metadata. Reopening the unchanged store/implementation and resuming the original revision's exact query remains valid."},
        ],
        "request_envelope_boundaries": [
            {"name": "agent-request-exact-8mib", "serialized_utf8_bytes": 8388608,
             "expected_stage": "agent_json_transport", "expected": "The envelope byte gate admits the exact boundary; later source or execution diagnostics remain separate and do not count as byte-gate failures."},
            {"name": "agent-request-one-over-8mib", "serialized_utf8_bytes": 8388609,
             "expected_stage": "agent_json_transport", "expected_code": "OKA-E-RESOURCE",
             "expected": "The envelope byte gate refuses before source/PNG execution and commits no candidate or request effects."}],
        "request_envelope_boundary_construction": "Start with the actual valid .13 rgb-panel create envelope. Append a newline and a // comment marker to entry.source. Serialize with sorted keys, compact separators and ensure_ascii=True. Let remaining=target-current_serialized_byte_length, q,r=divmod(remaining,6). Append q U+0000 characters followed by r spaces inside the comment; JSON escaping adds exactly 6*q+r bytes. Assert actual serialized UTF-8 length equals the target and aggregate source UTF-8 bytes remain below 2000000. Submit these exact serialized bytes through the CLI/transport path. This isolates the envelope gate; no claim that later source validation accepts control characters is required.",
        "asset_slice_boundary_probes": [
            {"name": "offset-zero", "offset": 0, "max_bytes": 1, "expected_stage": "inspect", "expected": "Exactly the first original PNG byte, matching metadata and program revision."},
            {"name": "maximum-chunk", "offset": 0, "max_bytes": 65536, "base": "encoded-limit", "expected_stage": "inspect", "expected": "Exactly 65536 original bytes; next_offset=65536 and complete=false."},
            {"name": "exact-eof", "offset": "total_bytes", "max_bytes": 65536, "expected_stage": "inspect", "expected": "Empty exact base64 slice, returned_bytes=0, complete=true and no later offset."},
            *[{"name": name, "offset": offset, "max_bytes": size, "expected_code": "OKA-E-REQUEST", "expected_stage": "inspect_request_admission"}
              for name, offset, size in [("negative-offset", -1, 1), ("offset-one-after-eof", "total_bytes+1", 1),
                                        ("fractional-offset", 0.5, 1), ("boolean-offset", True, 1),
                                        ("zero-count", 0, 0), ("count-one-over", 0, 65537),
                                        ("fractional-count", 0, 1.5), ("boolean-count", 0, True)]],
            *[{"name": "slice-with-" + field, "extra_field": field, "expected_code": "OKA-E-REQUEST", "expected_stage": "inspect_request_admission"}
              for field in ["cursor", "run_id", "time", "frame"]],
            {"name": "slice-with-kind-only-selector", "selector": {"kind": "texture_asset"}, "expected_code": "OKA-E-REQUEST", "expected_stage": "inspect_request_admission"}],
        "supplied_glb_adversaries": [
            {"mutation": x, "expected_code": "OKE-E-TEXTURE", "expected_stage": "supplied_glb_validation"}
            for x in ["change one referenced UV", "swap U and V", "invert V orientation", "use placed/world coordinates for UVs",
                      "nonzero unreferenced UV row", "wrong UV accessor count/type/component type", "replace embedded PNG with different valid bytes",
                      "alter embedded PNG CRC", "external image URI", "wrong image MIME", "swap material image references",
                      "change minFilter or wrapS", "drop TEXCOORD_0", "change texCoord set", "omit baseColorTexture",
                      "change baseColorFactor", "remove image provenance", "merge distinct mapping UV accessors incorrectly",
                      "add dangling unused image or texture"]],
        "runtime_execution_performed": False,
        "limits": "These are prescribed cases, not observed passes. Runtime/schema/store-specific envelopes remain an executable verifier's responsibility; inherited diagnostic families must be bound before claiming execution."
    }
    save_json("workflow-controls.json", controls)


def write_docs_and_freeze():
    counts = dict(Counter(c["expected_outcome"] for c in CASES))
    save("AUTHORING.md", '''# Independent C080 fixture authoring

These files were authored after the published texture/asset decision and before runtime implementation. The generator uses Python's standard library only. It does not import OntoKin, read product outputs, triangulate production meshes or execute product tests.

PNG inputs start from literal pixels or the stated pixel formulas. The writer applies each standard filter in the forward direction and builds chunk lengths, CRCs and a complete zlib stream. Exact decoded-pixel and per-row hashes, asymmetric texel probes and known glyphs are predetermined. Malformed files change one identified layer where practical. The encoded-limit file deliberately contains empty DEFLATE blocks, not a decompression bomb; its output is one four-byte scanline.

UV expectations interpret authored binary64 inputs with Fraction. The complete affine sum is rounded once to binary64, then packed to binary32. The decimal cancellation witness distinguishes exact complete evaluation from intermediate binary64 subtraction. Probe records explicitly distinguish authored region corners from general analytic probes; a probe is never proof of emitted triangulation.

Program revisions are calculated directly from the adopted canonical source/asset manifest and domain prefix. They do not invoke a product bundle loader. Existing source SHA256 values retain their original meaning. Exact geometry/motion preservation is a required comparison against a corresponding source-only .12 control, not an assumed property of screenshots.

No verification pass is reported by this freeze. Stage labels locate expected refusal authority: transport before candidate revision, represented closure/image/constructor admission, constructed referenced UV bounds, current request authorization, or supplied artifact validation. An implementation must not replace a required geometry/image refusal with unrelated resource exhaustion. Maximum decoded cases explicitly request higher limits with independent host policy; the ordinary-budget maximum image intentionally fails by its channel-byte debit lower bound.

An isolated aggregate-one-over image case satisfying every count and individual bound is impossible because both aggregate ceilings equal four times their individual maxima. Exact aggregate cases and separate count/individual failures cover those boundaries without inventing a witness.

All old fixtures remain unchanged. New work must preserve this freeze and failed runs; fix implementation defects or publish a separate reviewed contract/fixture revision instead of changing frozen answers.

The first unpublished preparation is retained as commit e1ce1c14d4029c5c529af3fe56b655bda92d91f1. Static review found its missing-padding payload replaced padding with A, which remained canonical base64 and reached the wrong-digest refusal instead. Before freeze publication, this preparation removes the required padding only and adds explicit envelope, asset-slice, successful attachment add/remove and metadata-cursor probes. No runtime result drove the correction.
''')
    save("README.md", f'''# Textured native surfaces: independent C080 inputs

The [adopted C080 decision](../../docs/language-design/textured-surfaces-v0.1/ADOPTION.md) selects source .13, bundle/files .2, Agent .13 and recorded GLB .13. This corpus freezes input and expected behavior before runtime implementation.

The source corpus has {len(CASES)} cases: {counts}. Separate transport cases, file-path cases, Agent workflows and hostile supplied-GLB controls remain separately counted. None is an executed pass.

Start with `rgb-panel.files.json`, `warning-panel.files.json` and `marked-tray.files.json`. Each manifest supplies exact source and image bytes under this folder. `expected.json` records source/asset revisions, mapping equations and probes, image pixels and hashes, geometry/motion invariants and finite limits. `workflow-controls.json` prescribes the actual Agent lifecycle and supplied-artifact adversaries.

The pinned library examples cover independent siblings, source-only mapping and image-selection repair, generated occurrences and rollback. The legacy-name control preserves an earlier user function called `png_asset`; textual name matching must not turn it into a .13 asset declaration.

`maximum-decoded-one` and `maximum-decoded-four` require explicit independent host ceilings of 2000000 operations / 80000 ms. Defaults elsewhere remain 100000 operations / 30000 ms. Asset limits and geometry/motion contracts remain separate from runtime grants.

See [AUTHORING.md](AUTHORING.md) for independent methods. `acceptance-freeze.json` binds the exact source/assets/expectations and the published decision. Full appearance/product release, Unreal import, live physics and inherited incomplete gates are not established here.
''')
    files = []
    for path in sorted(ROOT.rglob("*")):
        if path.is_file() and path.name != "acceptance-freeze.json":
            raw = path.read_bytes()
            files.append({"path": str(path.relative_to(ROOT)), "size": len(raw), "mode": "100644", "sha256": hashlib.sha256(raw).hexdigest()})
    adopted = []
    for name in ("ADOPTION.md", "ontokin-textures.ebnf", "diagnostics.json"):
        path = REPO / "docs/language-design/textured-surfaces-v0.1" / name
        raw = path.read_bytes()
        adopted.append({"path": str(path.relative_to(REPO)), "size": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
    freeze = {"schema_version": "ontokin.c080-independent-input-freeze/0.1", "checkpoint": "C080",
              "published_adoption_commit": ADOPTION_COMMIT, "adoption_files": adopted,
              "case_count": len(CASES), "outcome_counts": counts, "image_input_count": len(ASSETS),
              "files": files, "file_count": len(files), "bytes": sum(x["size"] for x in files),
              "independent_authorship": True, "product_imports": 0, "product_executions": 0,
              "product_tests": 0, "runtime_acceptance": False, "release_acceptance": False,
              "self_manifest_rule": "The inventory excludes only this freeze document; its final hash is recorded by the publishing checkpoint."}
    save_json("acceptance-freeze.json", freeze)
    print(json.dumps({"cases": len(CASES), "outcomes": counts, "image_inputs": len(ASSETS),
                      "frozen_files_excluding_manifest": len(files), "frozen_bytes": freeze["bytes"]}, indent=2))


def main():
    make_images()
    make_sources()
    make_transport_cases()
    make_companions()
    make_expectations()
    make_workflow_controls()
    write_docs_and_freeze()


if __name__ == "__main__":
    main()
