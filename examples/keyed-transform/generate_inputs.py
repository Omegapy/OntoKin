#!/usr/bin/env python3
"""Author C081 inputs and expectations without importing the product runtime.

Explicit C080 controls use authored values. They are separate source programs,
not values obtained by executing the new transformation.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
PROFILE = "keyed-transform-0.1"
SOURCE_VERSION = "0.14"
SOURCE_BASELINE = "2e51fc170a9db17e90cd7d97fd4c028b9afaefe9"
DEFAULT_POLICY = {"max_operations": 100000, "max_elapsed_ms": 30000}
LARGE_POLICY = {"max_operations": 400000, "max_elapsed_ms": 80000}
CASES = []


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(raw):
    return "sha256:" + sha(raw)


def write(name, value):
    path = ROOT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, bytes):
        path.write_bytes(value)
    elif isinstance(value, str):
        path.write_text(value, encoding="utf-8")
    else:
        path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    return name


def header(*, legacy=False, name="Probe", key="probe", execution=""):
    version, profile = ("0.13", "textured-surfaces-0.1") if legacy else (SOURCE_VERSION, PROFILE)
    return f'ontokin "{version}";\nmodule {name} @ "{key}";\nprofile "{profile}";\n{execution}'


def keyed(typ, entries):
    return f'keyed<{typ}> {{' + ", ".join(json.dumps(key) + ": " + value for key, value in entries) + "}"


def mapper(typ, input_, body="v", binders="k, v"):
    return f"map_keyed<{typ}>({input_}, ({binders}) -> {body})"


def probe(typ, expr, *, preamble="", members="", execution="", legacy=False):
    return header(legacy=legacy, execution=execution) + preamble + f'''
public class ProbeShape @ "probe-shape" {{
    {members}
    public derive result @ "result": Keyed<{typ}> = {expr};
    geometry = if len(self.result) >= 0 then box(vec3(1[m], 1[m], 1[m])) else empty();
    physical = no_body();
}}
scene Demo @ "demo" {{
    duration = 1[s];
    gravity = vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2]);
    object shape @ "shape": ProbeShape {{}}
}}
'''


def descriptor(source, *, filename="main.ok"):
    return {"filename": filename, "source": source}


def manifest_for(source_path, modules, assets):
    value = {"schema_version": "ontokin.files/0.2", "entry": {"filename": "main.ok", "path": source_path},
             "modules": [], "assets": []}
    for package, path in modules:
        value["modules"].append({"package_id": package, "version": "1.0.0", "filename": Path(path).name, "path": path})
    for ident in assets:
        path = "assets/" + ident + ".png"
        raw = (ROOT / path).read_bytes()
        value["assets"].append({"asset_id": ident, "sha256": digest(raw), "media_type": "image/png", "path": path})
    return value


def identity(manifest):
    units = [{"source_id": "entry", "package_id": None, "version": None,
              "filename": manifest["entry"]["filename"],
              "source_revision": digest((ROOT / manifest["entry"]["path"]).read_bytes())}]
    for module in manifest["modules"]:
        units.append({"source_id": f'package:{module["package_id"]}@{module["version"]}',
                      "package_id": module["package_id"], "version": module["version"],
                      "filename": module["filename"],
                      "source_revision": digest((ROOT / module["path"]).read_bytes())})
    values = {"schema_version": "ontokin.bundle/0.2", "entry_source_id": "entry",
              "units": sorted(units, key=lambda item: item["source_id"]),
              "assets": sorted([{"asset_id": a["asset_id"], "sha256": a["sha256"], "media_type": a["media_type"],
                                  "byte_length": (ROOT / a["path"]).stat().st_size}
                                 for a in manifest["assets"]], key=lambda item: item["asset_id"])}
    raw = json.dumps(values, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    return digest(b"ontokin.bundle/0.2\0" + raw), values


def add(name, source, *, outcome="valid", code=None, typ=None, keys=None, scalar_values=None,
        control=None, modules=(), control_modules=None, assets=(), tags=(), notes="", policy=None,
        expected=None, stage="represented"):
    source_path = write("sources/" + name + ".ok", source)
    files = manifest_for(source_path, modules, assets)
    manifest_path = write(name + ".files.json", files)
    revision, canonical = identity(files)
    case = {"id": "K" + str(len(CASES) + 1).zfill(3), "name": name, "source": source_path,
            "file_manifest": manifest_path, "expected_outcome": outcome, "expected_code": code,
            "expected_stage": stage, "tags": list(tags), "notes": notes,
            "host_policy": dict(policy or DEFAULT_POLICY), "program_revision": revision,
            "canonical_manifest": canonical}
    if typ is not None:
        case["probe"] = {"object_path": "shape", "member": "result", "type": f"Keyed<{typ}>",
                         "keys": sorted(keys or [])}
        if scalar_values is not None:
            case["probe"]["scalar_values"] = scalar_values
    if expected is not None:
        case["expected"] = expected
    if control is not None:
        control_path = write("controls/" + name + ".ok", control)
        control_files = manifest_for(control_path, modules if control_modules is None else control_modules, assets)
        control_manifest = write("control-" + name + ".files.json", control_files)
        control_revision, control_canonical = identity(control_files)
        case["explicit_c080_control"] = {"file_manifest": control_manifest,
                                         "program_revision": control_revision,
                                         "canonical_manifest": control_canonical}
    CASES.append(case)
    return case


def scalar_case(name, input_type, entries, output_type, body, results, **kwargs):
    source = probe(output_type, mapper(output_type, keyed(input_type, entries), body))
    explicit = keyed(output_type, results)
    return add(name, source, typ=output_type, keys=[k for k, _ in results],
               control=probe(output_type, explicit, legacy=True), **kwargs)


def import_line(alias, package, path):
    return (f'import {alias} @ "{alias}-import" from "{package}" version "1.0.0" '
            f'digest "{digest((ROOT / path).read_bytes())}";\n')


def seed_assets():
    source = REPO / "examples/textured-surfaces/assets/asymmetric-rgb.png"
    write("assets/label.png", source.read_bytes())


def build_scalars():
    scalar_case("empty-length", "Length", [], "Length", "v * 2", [], tags=["empty", "units"])
    scalar_case("singleton-length", "Length", [("only", "0.25[m]")], "Length", "v * 2", [("only", "0.5[m]")], scalar_values={"only": 0.5}, tags=["singleton", "units"])
    entries = [(f"k{i:03}", str(i)) for i in reversed(range(256))]
    result = [(f"k{i:03}", str(i * 2 + 1)) for i in range(256)]
    scalar_case("maximum-256", "Int", entries, "Int", "v * 2 + 1", result,
                scalar_values={f"k{i:03}": i * 2 + 1 for i in range(256)}, tags=["maximum", "ascii-order", "bounded-work"])
    entries = [("z", "3"), ("a", "2"), ("A", "1"), ("0", "0"), ("left.eye", "4")]
    scalar_case("ascii-and-punctuation-keys", "Int", entries, "String", "k",
                [(k, json.dumps(k)) for k, _ in entries], scalar_values={k: k for k, _ in entries}, tags=["key-preservation", "ascii-order"])
    scalar_case("literal-reordered", "Int", list(reversed(entries)), "String", "k",
                [(k, json.dumps(k)) for k, _ in entries], scalar_values={k: k for k, _ in entries}, tags=["source-order", "key-preservation"])
    scalar_case("int-to-real", "Int", [("a", "2"), ("z", "-3")], "Real", "v",
                [("a", "2.0"), ("z", "-3.0")], scalar_values={"a": 2.0, "z": -3.0}, tags=["per-element-conversion"])
    scalar_case("length-to-area", "Length", [("a", "3[m]"), ("b", "25[cm]")], "Quantity[m^2]", "v * 2[m]",
                [("a", "6[m^2]"), ("b", "0.5[m^2]")], scalar_values={"a": 6.0, "b": 0.5}, tags=["units", "dimension-change"])
    scalar_case("length-to-point", "Length", [("low", "1[m]"), ("high", "2[m]")], "PlanarPoint", "planar_point(v, 0[m])",
                [("low", "planar_point(1[m], 0[m])"), ("high", "planar_point(2[m], 0[m])")], tags=["typed-algorithm", "point-construction"])
    scalar_case("empty-domain-body", "Real", [], "Real", "v / 0", [], tags=["empty", "domain-not-executed"])
    for selected, empty, name in [(False, False, "unused-local-zero-branch"), (False, True, "empty-local-zero-branch"), (True, False, "selected-local-zero-branch")]:
        values = keyed("Int", [] if empty else [("a", "2")])
        body = f'if {str(selected).lower()} then v / zero_local else real(v)'
        preamble = f'public fn transform @ "transform"(zero_local: Int) -> Keyed<Real> {{ return {mapper("Real", values, body)}; }}\n'
        add(name, probe("Real", "transform(0)", preamble=preamble), outcome="invalid" if selected else "valid",
            code="OKL-E-NUMERIC" if selected else None, typ="Real", keys=[] if empty else ["a"],
            scalar_values={} if empty else {"a": 2.0},
            control=None if selected else probe("Real", keyed("Real", [] if empty else [("a", "2.0")]), legacy=True),
            tags=["abstract-body", "lazy-branch", "captured-locals"])
    inner = mapper("Real", keyed("Int", [("inner", "3")]), "real(iv)", "ik, iv")
    expr = mapper("Int", keyed("Int", [("outer", "8")]), f"v + len({inner})")
    add("nested-flat-map", probe("Int", expr), typ="Int", keys=["outer"], scalar_values={"outer": 9},
        control=probe("Int", 'keyed<Int>{"outer": 9}', legacy=True), tags=["nested-expression", "flat-output"])


def build_leaves():
    polygon = 'keyed<PolygonVertex>{"a": polygon_vertex(0, planar_point(0[m], 0[m]), "side"), "b": polygon_vertex(1, planar_point(1[m], 0[m]), "side"), "c": polygon_vertex(2, planar_point(0[m], 1[m]), "side")}'
    ring = f'polygon_ring(0, "outer", {polygon})'
    rings = f'keyed<PolygonRing>{{"outer": {ring}}}'
    image = 'png_asset("label", "' + digest((ROOT / "assets/label.png").read_bytes()) + '")'
    uv = 'planar_uv(vec3(0[m], 0[m], 0[m]), vec3(1[m^-1], 0[m^-1], 0[m^-1]), vec3(0[m^-1], 1[m^-1], 0[m^-1]), 0, 0)'
    leaves = [
        ("int", "Int", "7"), ("real", "Real", "0.5"), ("bool", "Bool", "true"),
        ("string", "String", '"unchanged"'), ("quantity", "Length", "0.25[m]"),
        ("vec3", "Vec3<Length>", "vec3(1[m], 2[m], 3[m])"),
        ("vector3", "Vector3<Length>", "vector(world, 1[m], 2[m], 3[m])"),
        ("range", "Range<Length>", "range(1[m], 2[m])"), ("frame", "FrameRef", "world"),
        ("point3", "Point3", "point(world, 1[m], 2[m], 3[m])"),
        ("rotation", "Rotation", "quat(1, 0, 0, 0)"),
        ("pose", "Pose", "pose(world, vec3(1[m], 2[m], 3[m]), quat(1, 0, 0, 0))"),
        ("color", "Color", "rgba(0.25, 0.5, 0.75, 1)"),
        ("loft-section", "LoftSection", 'loft_section(0[m], vec3(0[m], 0[m], 0[m]), 1[m], 1[m], "side")'),
        ("material", "SurfaceMaterial", "surface_material(rgba(0.25, 0.5, 0.75, 1), 0, 0.5)"),
        ("planar-point", "PlanarPoint", "planar_point(1[m], 2[m])"),
        ("polygon-vertex", "PolygonVertex", 'polygon_vertex(0, planar_point(1[m], 2[m]), "side")'),
        ("polygon-ring", "PolygonRing", ring),
        ("polygon-section", "PolygonSection", f"polygon_section(0, 1[m], {rings})"),
        ("framed-section", "FramedPolygonSection", f"framed_polygon_section(0, pose(self.frame, vec3(0[m], 0[m], 0[m]), quat(1, 0, 0, 0)), {rings})"),
        ("polygon-pocket", "PolygonPocket", f'polygon_pocket(0, {polygon}, 0.25[m], "floor")'),
        ("texture-image", "TextureImage", image), ("planar-uv", "PlanarUV", uv),
        ("texture-binding", "TextureBinding", f"texture_binding({image}, {uv})")]
    for name, typ, value in leaves:
        entries = [("kept", value)]
        scalar_case("leaf-" + name, typ, entries, typ, "v", entries,
                    assets=["label"] if name in {"texture-image", "texture-binding"} else [],
                    tags=["leaf-whitelist", "identity", name])


def build_negative():
    good = keyed("Length", [("a", "1[m]")])
    empty = keyed("Length", [])
    pairs = [
        ("empty-wrong-unit", "Length", mapper("Length", empty, "1[s]"), "OKL-E-UNIT", ["empty", "units"]),
        ("empty-wrong-type", "Length", mapper("Length", empty, '"wrong"'), "OKL-E-TYPE", ["empty", "type"]),
        ("empty-unknown-name", "Length", mapper("Length", empty, "missing"), "OKL-E-NAME", ["empty", "name"]),
        ("empty-invalid-unused-branch", "Length", mapper("Length", empty, "if true then v else missing"), "OKL-E-NAME", ["empty", "lazy-static"]),
        ("nonkeyed-input", "Length", mapper("Length", "1[m]", "v"), "OKL-E-TYPE", ["input-type"]),
        ("output-dimension-mismatch", "Time", mapper("Time", good, "v"), "OKL-E-UNIT", ["units"]),
        ("output-type-mismatch", "Bool", mapper("Bool", good, "v"), "OKL-E-TYPE", ["type"]),
        ("duplicate-binders", "Length", mapper("Length", good, "v", "v, v"), "OKL-E-NAME", ["binder"]),
        ("predefined-binder", "Length", mapper("Length", good, "v", "len, v"), "OKL-E-NAME", ["binder"]),
        ("self-binder", "Length", mapper("Length", good, "v", "self, v"), "OKL-E-NAME", ["binder"]),
        ("member-binder", "Length", mapper("Length", good, "v", "result, v"), "OKL-E-NAME", ["binder"]),
        ("class-binder", "Length", mapper("Length", good, "v", "ProbeShape, v"), "OKL-E-NAME", ["binder"]),
        ("binder-escapes-body", "Length", mapper("Length", good, "v") + '[k]', "OKL-E-NAME", ["binder", "scope"]),
        ("generated-output-reference", "Ref<Object>", mapper("Ref<Object>", good, "self"), "OKL-E-CAPABILITY-UNSUPPORTED", ["forbidden-type", "reference"]),
        ("nested-keyed-output", "Keyed<Length>", mapper("Keyed<Length>", good, 'keyed<Length>{"x": v}'), "OKL-E-CAPABILITY-UNSUPPORTED", ["forbidden-type", "nested-keyed"]),
        ("geometry-output", "Geometry", mapper("Geometry", good, "sphere(v)"), "OKL-E-CAPABILITY-UNSUPPORTED", ["forbidden-type"]),
        ("body-model-output", "BodyModel", mapper("BodyModel", good, "no_body()"), "OKL-E-CAPABILITY-UNSUPPORTED", ["forbidden-type"]),
        ("action-output", "Action", mapper("Action", good, "move(self, vector(world, 1[m/s], 0[m/s], 0[m/s]), 1[s])"), "OKL-E-CAPABILITY-UNSUPPORTED", ["forbidden-type", "effects"]),
        ("too-many-257", "Int", mapper("Int", keyed("Int", [(f"k{i:03}", str(i)) for i in range(257)])), "OKL-E-RESOURCE", ["entry-bound"]),
        ("duplicate-input-key", "Length", mapper("Length", keyed("Length", [("a", "1[m]"), ("a", "2[m]")])), "OKL-E-ID", ["key-identity"]),
        ("invalid-input-key", "Length", mapper("Length", keyed("Length", [("bad/key", "1[m]")])), "OKL-E-ID", ["key-identity"]),
        ("empty-input-key", "Length", mapper("Length", keyed("Length", [("", "1[m]")])), "OKL-E-ID", ["key-identity"]),
        ("too-long-input-key", "Length", mapper("Length", keyed("Length", [("x" * 65, "1[m]")])), "OKL-E-ID", ["key-identity"]),
        ("selected-zero-division", "Real", mapper("Real", keyed("Int", [("a", "1")]), "v / 0"), "OKL-E-NUMERIC", ["domain"]),
        ("selected-integer-overflow", "Int", mapper("Int", keyed("Int", [("a", "9223372036854775807")]), "v + 1"), "OKL-E-NUMERIC", ["domain", "integer-bound"]),
        ("invalid-vector-dimensions", "Vec3<Length>", mapper("Vec3<Length>", good, "vec3(v, 1[s], v)"), "OKL-E-UNIT", ["units", "vector"]),
    ]
    for name, typ, expr, code, tags in pairs:
        add(name, probe(typ, expr), outcome="invalid", code=code, tags=tags)
    local_source = 'public fn transform @ "transform"(v: Length) -> Keyed<Length> { return ' + mapper("Length", good) + '; }\n'
    add("outer-local-binder", probe("Length", "transform(1[m])", preamble=local_source), outcome="invalid", code="OKL-E-NAME", tags=["binder", "captured-local"])
    nested = mapper("Int", keyed("Int", [("outer", "1")]), "len(" + mapper("Int", keyed("Int", [("inner", "2")])) + ")")
    add("nested-binder-shadow", probe("Int", nested), outcome="invalid", code="OKL-E-NAME", tags=["binder", "nested-expression"])
    reserved = 'public fn map_keyed @ "old-name"(value: Length) -> Length { return value; }\n'
    add("new-profile-reserves-map-name", probe("Length", 'keyed<Length>{"a": 1[m]}', preamble=reserved), outcome="invalid", code="OKL-E-NAME", tags=["reserved-name"])


def build_imports():
    old_path = write("modules/old-helper.ok", header(legacy=True, name="OldHelper", key="old-helper") + '''
public fn map_keyed @ "retained-user-name"(value: Length) -> Length { return value * 2; }
private fn secret @ "private-helper"(value: Length) -> Length { return value; }
public fn twice @ "twice"(value: Length) -> Length { return map_keyed(value); }
''')
    imports = import_line("lib", "fixture.old-helper", old_path)
    modules = [("fixture.old-helper", old_path)]
    values = keyed("Length", [("a", "0.25[m]")])
    source = probe("Length", mapper("Length", values, "lib.twice(v)"), preamble=imports)
    add("imported-legacy-pure-helper", source, typ="Length", keys=["a"], scalar_values={"a": 0.5},
        modules=modules, control=probe("Length", 'keyed<Length>{"a": lib.twice(0.25[m])}', preamble=imports, legacy=True),
        tags=["imports", "declaring-semantics", "legacy-name"])
    source = probe("Length", mapper("Length", values, "lib.map_keyed(v)"), preamble=imports)
    add("qualified-legacy-map-name", source, typ="Length", keys=["a"], scalar_values={"a": 0.5},
        modules=modules, control=probe("Length", 'keyed<Length>{"a": lib.map_keyed(0.25[m])}', preamble=imports, legacy=True),
        tags=["imports", "qualified-name", "legacy-name"])
    add("empty-private-import-helper", probe("Length", mapper("Length", keyed("Length", []), "lib.secret(v)"), preamble=imports),
        modules=modules, outcome="invalid", code="OKL-E-ACCESS", tags=["empty", "access", "imports"])
    add("import-alias-binder", probe("Length", mapper("Length", values, "v", "lib, v"), preamble=imports),
        modules=modules, outcome="invalid", code="OKL-E-NAME", tags=["binder", "imports"])
    new_path = write("modules/new-helper.ok", header(name="NewHelper", key="new-helper") + imports +
                     'public fn widths @ "widths"(input: Keyed<Length>) -> Keyed<Length> { return ' +
                     mapper("Length", "input", "lib.twice(v)") + '; }\n')
    new_import = import_line("helper", "fixture.new-helper", new_path)
    add("imported-new-map-helper", probe("Length", f'helper.widths({values})', preamble=new_import),
        typ="Length", keys=["a"], scalar_values={"a": 0.5}, modules=[("fixture.new-helper", new_path), *modules],
        control=probe("Length", 'keyed<Length>{"a": 0.5[m]}', legacy=True), control_modules=[],
        tags=["imports", "transitive-import", "pure-helper"])
    add("older-importer-rejects-new-unit", probe("Length", f'helper.widths({values})', preamble=new_import, legacy=True),
        modules=[("fixture.new-helper", new_path), *modules], outcome="invalid", code="OKL-E-CAPABILITY-UNSUPPORTED", tags=["imports", "version-gate"])
    add("wrong-import-pin", source.replace(digest((ROOT / old_path).read_bytes()), "sha256:" + "0" * 64),
        modules=modules, outcome="invalid", code="OKL-E-REVISION", tags=["imports", "exact-pin"])


def build_provenance():
    leaf = '''public class Leaf @ "leaf" {
 public param size @ "size": Length = 0.25[m];
 geometry = sphere(self.size);
 physical = no_body();
}
'''
    def family(expr, extra=""):
        return leaf + '''public class Family @ "family" {
 public param sizes @ "sizes": Keyed<Length> = keyed<Length>{"a": 0.25[m], "z": 0.5[m]};
 ''' + extra + '''
 public parts leaves @ "leaves": Leaf for (child_key, child_value) in ''' + expr + ''' { size = child_value; }
 geometry = empty();
 physical = no_body();
}
'''
    def scene(classes, objects='object rig @ "rig": Family {}', legacy=False):
        return header(legacy=legacy, name="Dependencies", key="dependencies") + classes + '''scene Demo @ "demo" {
 duration = 1[s];
 gravity = vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2]);
 ''' + objects + "\n}\n"
    good = mapper("Length", "self.sizes", "v * 2")
    add("generated-shape-from-map", scene(family(good)), control=scene(family('keyed<Length>{"a": 0.5[m], "z": 1[m]}'), legacy=True),
        expected={"generated_keys": ["a", "z"], "radii_m": {'rig.leaves["a"]': 0.5, 'rig.leaves["z"]': 1.0}}, tags=["generated", "key-provenance"])
    unused = mapper("Length", "self.sizes", 'if true then v else self.leaves["a"].size')
    add("unused-generated-read", scene(family(unused)), control=scene(family("self.sizes"), legacy=True),
        expected={"generated_keys": ["a", "z"], "radii_m": {'rig.leaves["a"]': 0.25, 'rig.leaves["z"]': 0.5}}, tags=["provenance", "lazy-branch"])
    active = mapper("Length", "self.sizes", 'if false then v else self.leaves["a"].size')
    add("selected-generated-read", scene(family(active)), outcome="invalid", code="OKL-E-DEPENDENCY-CYCLE", tags=["provenance", "generated-dependency"])
    add("empty-map-invalid-unused-access", scene(family(mapper("Length", "keyed<Length>{}", 'if true then v else self.leaves["a"].missing'))),
        outcome="invalid", code="OKL-E-NAME", tags=["empty", "access", "lazy-branch"])
    add("generated-reference-input", scene(family(mapper("Length", "self.leaves", "v.size"))),
        outcome="invalid", code="OKL-E-CAPABILITY-UNSUPPORTED", tags=["generated-view", "forbidden-input"])
    classes = family("self.sizes") + '''public class Outer @ "outer" {
 public part family @ "family-part": Family {}
 public derive copied @ "copied": Length = self.family.leaves["a"].size;
 public parts bad @ "bad": Leaf for (child_key, child_value) in ''' + mapper("Length", 'keyed<Length>{"x": self.copied}', "v") + ''' { size = child_value; }
 geometry = empty();
 physical = no_body();
}
'''
    add("cached-generated-dependency", scene(classes, 'object rig @ "rig": Outer {}'), outcome="invalid", code="OKL-E-DEPENDENCY-CYCLE", tags=["provenance", "cached-dependency"])
    own = family(mapper("Length", "self.sizes")) + '''public class Outer @ "outer" {
 public parts families @ "families": Family for (child_key, child_value) in keyed<Length>{"first": 0.5[m]} {
  sizes = keyed<Length>{"nested": child_value};
 }
 geometry = empty();
 physical = no_body();
}
'''
    explicit = own.replace(mapper("Length", "self.sizes"), "self.sizes")
    add("nested-own-final-input", scene(own, 'object rig @ "rig": Outer {}'), control=scene(explicit, 'object rig @ "rig": Outer {}', legacy=True),
        expected={"radii_m": {'rig.families["first"].leaves["nested"]': 0.5}}, tags=["provenance", "own-input", "nested-construction"])
    recursive = 'public fn recurse @ "recurse"(input: Keyed<Length>) -> Keyed<Length> { return ' + mapper("Length", "input", 'recurse(input)[k]') + '; }\n'
    add("recursive-pure-helper", probe("Length", 'recurse(keyed<Length>{})', preamble=recursive), outcome="invalid", code="OKL-E-DEPENDENCY-CYCLE", tags=["recursion", "empty"])


def build_boundaries_and_assets():
    longest = "A" + "x" * 63
    scalar_case("maximum-key-length", "Int", [(longest, "7")], "Int", "v + 1", [(longest, "8")],
                scalar_values={longest: 8}, tags=["key-bound", "64-character-key"])
    scalar_case("lazy-boolean-body", "Int", [("a", "0"), ("b", "2")], "Bool", "v != 0 and 2 / v > 0",
                [("a", "false"), ("b", "true")], scalar_values={"a": False, "b": True}, tags=["short-circuit", "numeric-domain"])
    expr = mapper("Vector3<Length>", keyed("Vector3<Length>", [("a", "vector(world, 1[m], 0[m], 0[m])")]),
                  "v + vector(self.frame, 1[m], 0[m], 0[m])")
    add("incompatible-vector-frame", probe("Vector3<Length>", expr), outcome="invalid", code="OKL-E-FRAME", tags=["frames", "type"])
    expr = mapper("SurfaceMaterial", 'keyed<Real>{"a": 2}', "surface_material(rgba(1, 1, 1, 1), v, 0.5)")
    add("transformed-invalid-material", probe("SurfaceMaterial", expr), outcome="invalid", code="OKL-E-SURFACE-MATERIAL", tags=["constructor-bound", "material"])
    rings = 'keyed<PolygonRing>{"outer": polygon_ring(0, "outer", keyed<PolygonVertex>{"a": polygon_vertex(0, planar_point(0[m], 0[m]), "side"), "b": polygon_vertex(1, planar_point(1[m], 0[m]), "side"), "c": polygon_vertex(2, planar_point(0[m], 1[m]), "side")})}'
    expr = mapper("FramedPolygonSection", 'keyed<Int>{"a": 0}',
                  f"framed_polygon_section(v, pose(world, vec3(0[m], 0[m], 0[m]), quat(1, 0, 0, 0)), {rings})")
    add("transformed-wrong-carrier-frame", probe("FramedPolygonSection", expr), outcome="invalid", code="OKL-E-FRAMED-LOFT-FRAME", tags=["constructor-bound", "frames"])
    image_hash = digest((ROOT / "assets/label.png").read_bytes())
    image = f'png_asset("label", "{image_hash}")'
    declaration = 'public fn retained_image @ "retained-image"() -> TextureImage { return ' + image + '; }\n'
    source = probe("TextureImage", mapper("TextureImage", "keyed<Int>{}", image))
    add("empty-map-retains-image-declaration", source, typ="TextureImage", keys=[], assets=["label"],
        control=probe("TextureImage", "keyed<TextureImage>{}", preamble=declaration, legacy=True),
        expected={"declared_asset_ids": ["label"], "png_admissions_per_compilation": 1, "dynamic_body_evaluations": 0},
        tags=["empty", "png-closure", "unused-declaration"])
    add("empty-map-missing-declared-image", source, outcome="invalid", code="OKL-E-ASSET-CLOSURE", tags=["empty", "png-closure"])
    dynamic_image = f'png_asset(k, "{image_hash}")'
    add("empty-map-dynamic-image-id", probe("TextureImage", mapper("TextureImage", "keyed<Int>{}", dynamic_image)),
        outcome="invalid", code="OKL-E-ASSET-CLOSURE", assets=["label"], tags=["empty", "png-closure", "literal-declaration"])
    expr = mapper("TextureImage", 'keyed<Int>{"a": 1, "b": 2}', image)
    add("repeated-map-image-reference", probe("TextureImage", expr), typ="TextureImage", keys=["a", "b"], assets=["label"],
        control=probe("TextureImage", keyed("TextureImage", [("a", image), ("b", image)]), legacy=True),
        expected={"declared_asset_ids": ["label"], "png_admissions_per_compilation": 1, "dynamic_body_evaluations": 2},
        tags=["png-closure", "cumulative-cost", "repeated-reference"])
    expr = 'keyed<Int>{"seed": 1}'
    for index in range(140):
        expr = mapper("Int", 'keyed<Int>{"seed": 1}', "len(" + expr + ")", f"key{index}, value{index}")
    add("excessive-expression-depth", probe("Int", expr), outcome="invalid", code="OKL-E-RESOURCE",
        tags=["expression-bound", "preallocation", "host-recursion"], notes="A 140-level nested map must receive a bounded resource refusal; no promise is made about the first limiting stage.")


def panel_library(*, identity=False, legacy=False):
    image = 'png_asset("label", "' + digest((ROOT / "assets/label.png").read_bytes()) + '")'
    width_expr = 'keyed<Length>{"left": self.scale, "right": self.scale * 2}' if identity else mapper("Length", "self.coefficients", "v * self.scale")
    if identity and not legacy:
        width_expr = mapper("Length", width_expr)
    return header(legacy=legacy, name="Panels", key="panels") + f'''
public class Panel @ "panel" {{
    public param width @ "width": Length = 1[m];
    public param parent_frame @ "parent-frame": FrameRef = world;
    public param mount_x @ "mount-x": Length = 0[m];
    public follow mounting @ "mounting" {{
        parent = self.parent_frame;
        child = self;
        offset = pose(self.parent_frame, vec3(self.mount_x, 0[m], 0[m]), quat(1, 0, 0, 0));
    }}
    geometry = texture_surface(extrude(keyed<PolygonVertex> {{
        "v0": polygon_vertex(0, planar_point(0[m], 0[m]), "side"),
        "v1": polygon_vertex(10, planar_point(self.width, 0[m]), "side"),
        "v2": polygon_vertex(20, planar_point(self.width, 2[m]), "side"),
        "v3": polygon_vertex(30, planar_point(0[m], 2[m]), "side")
    }}, keyed<SurfaceMaterial> {{
        "bottom": surface_material(rgba(1, 1, 1, 1), 0, 0.7),
        "side": surface_material(rgba(0.25, 0.5, 0.75, 1), 0, 0.7),
        "top": surface_material(rgba(1, 1, 1, 1), 0, 0.7)
    }}, 0.25[m], "bottom", "top"), keyed<TextureBinding> {{
        "top": texture_binding({image}, planar_uv(vec3(0[m], 0[m], 0[m]),
            vec3(0.5[m^-1], 0[m^-1], 0[m^-1]), vec3(0[m^-1], -0.5[m^-1], 0[m^-1]), 0, 1))
    }});
    physical = no_body();
}}
public class PanelGroup @ "panel-group" {{
    public param scale @ "scale": Length = 1[m];
    public param coefficients @ "coefficients": Keyed<Real> = keyed<Real>{{"right": 2, "left": 1}};
    public param mounts @ "mounts": Keyed<Length> = keyed<Length>{{"left": 0[m], "right": 4[m]}};
    public derive widths @ "widths": Keyed<Length> = {width_expr};
    public parts panels @ "panels": Panel for (panel_key, panel_width) in self.widths {{
        width = panel_width;
        parent_frame = self.frame;
        mount_x = self.mounts[panel_key];
    }}
    geometry = empty();
    physical = no_body();
}}
'''


def assembly_source(library, *, repaired=False, legacy=False, execution=""):
    return header(legacy=legacy, name="PanelTask", key="panel-task", execution=execution) + import_line("lib", "fixture.panels", library) + f'''
scene Demo @ "demo" {{
    duration = 1[s];
    gravity = vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2]);
    object first @ "first": lib.PanelGroup {{
        placement = pose(world, vec3(-8[m], 0[m], 0[m]), quat(1, 0, 0, 0));
        scale = {"1.5" if repaired else "1"}[m];
    }}
    object sibling @ "sibling": lib.PanelGroup {{
        placement = pose(world, vec3(2[m], 0[m], 0[m]), quat(1, 0, 0, 0));
    }}
    object marker @ "marker": Object {{
        placement = pose(world, vec3(0[m], -3[m], 0[m]), quat(1, 0, 0, 0));
        geometry = extrude(keyed<PolygonVertex>{{
            "v0": polygon_vertex(0, planar_point(0[m], 0[m]), "side"),
            "v1": polygon_vertex(10, planar_point(0.5[m], 0[m]), "side"),
            "v2": polygon_vertex(20, planar_point(0.5[m], 0.5[m]), "side"),
            "v3": polygon_vertex(30, planar_point(0[m], 0.5[m]), "side")
        }}, keyed<SurfaceMaterial>{{
            "bottom": surface_material(rgba(1, 0.25, 0.1, 1), 0, 0.7),
            "side": surface_material(rgba(1, 0.25, 0.1, 1), 0, 0.7),
            "top": surface_material(rgba(1, 0.25, 0.1, 1), 0, 0.7)
        }}, 0.5[m], "bottom", "top");
        physical = no_body();
    }}
    action travel @ "travel" = move(first, vector(world, 0[m/s], 0.5[m/s], 0[m/s]), 1[s]);
    action marker_travel @ "marker-travel" = move(marker, vector(world, 0.25[m/s], 0[m/s], 0[m/s]), 1[s]);
    at 0[s] sequence {{ start travel; start marker_travel; }}
}}
'''


def panel_expectations(*, repaired=False):
    widths = {"first": {"left": 1.5 if repaired else 1.0, "right": 3.0 if repaired else 2.0},
              "sibling": {"left": 1.0, "right": 2.0}}
    objects = []
    for owner, root_x in [("first", -8), ("sibling", 2)]:
        for key, mount in [("left", 0), ("right", 4)]:
            width = widths[owner][key]
            objects.append({"path": f'{owner}.panels["{key}"]',
                            "element_id": ["panel-task", "demo", owner, "panels", key],
                            "owner": owner, "input_key": key, "width_m": width,
                            "local_bounds_m": [[0, 0, 0], [width, 2, 0.25]],
                            "raw_corner_set_m": [[x, y, z] for x in [0, width] for y in [0, 2] for z in [0, 0.25]],
                            "triangle_count": 12,
                            "volume_m3": width * 0.5,
                            "surface_area_m2": 2 * (2 * width + 0.25 * width + 0.5),
                            "material_regions": ["bottom", "side", "top"],
                            "region_triangle_counts": {"bottom": 2, "side": 8, "top": 2},
                            "materials": {"bottom": {"color": [1, 1, 1, 1], "metallic": 0, "roughness": 0.7},
                                          "side": {"color": [0.25, 0.5, 0.75, 1], "metallic": 0, "roughness": 0.7},
                                          "top": {"color": [1, 1, 1, 1], "metallic": 0, "roughness": 0.7}},
                            "top_uv_corners": [[0, 1], [width * 0.5, 1], [width * 0.5, 0], [0, 0]],
                            "poses": [{"time_s": t, "position_m": [root_x + mount, 0.5 * t if owner == "first" else 0, 0],
                                       "rotation_xyzw": [0, 0, 0, 1]} for t in [0, 0.25, 0.5, 0.75, 1]]})
    return {"object_count": 7, "generated_collection_count": 2, "generated_panel_count": 4,
            "widths_m": widths, "panels": objects,
            "marker": {"path": "marker", "family": "extrusion", "local_bounds_m": [[0, 0, 0], [0.5, 0.5, 0.5]],
                       "raw_corner_set_m": [[x, y, z] for x in [0, 0.5] for y in [0, 0.5] for z in [0, 0.5]],
                       "triangle_count": 12, "volume_m3": 0.125, "surface_area_m2": 1.5,
                       "region_triangle_counts": {"bottom": 2, "side": 8, "top": 2},
                       "materials": {key: {"color": [1, 0.25, 0.1, 1], "metallic": 0, "roughness": 0.7}
                                     for key in ["bottom", "side", "top"]},
                       "poses": [{"time_s": t, "position_m": [0.25 * t, -3, 0], "rotation_xyzw": [0, 0, 0, 1]}
                                 for t in [0, 0.25, 0.5, 0.75, 1]]},
            "own_mass_kg": 0, "aggregate_mass_kg": 0,
            "image": {"asset_id": "label", "sha256": digest((ROOT / "assets/label.png").read_bytes())},
            "mapping": {"u_per_m": [0.5, 0, 0], "v_per_m": [0, -0.5, 0], "origin_m": [0, 0, 0], "offset": [0, 1]},
            "source_geometry_tolerance_m": 1e-12, "source_pose_tolerance_m": 1e-9,
            "stream_comparison": "exact bytes for corresponding geometry, UV, PNG, material and recorded-motion streams"}


def build_panels():
    module = write("modules/panels.ok", panel_library())
    identity_module = write("modules/panels-identity.ok", panel_library(identity=True))
    control_module = write("modules/panels-c080.ok", panel_library(identity=True, legacy=True))
    for name, repaired, path in [("panel-task", False, module), ("panel-task-repaired", True, module),
                                 ("panel-identity", False, identity_module)]:
        case = add(name, assembly_source(path, repaired=repaired), modules=[("fixture.panels", path)], assets=["label"],
            control=assembly_source(control_module, repaired=repaired, legacy=True), control_modules=[("fixture.panels", control_module)],
            expected=panel_expectations(repaired=repaired), tags=["pinned-library", "generated", "two-occurrences", "destination", "texture", "motion"], stage="delivered")
        module_text = (ROOT / path).read_text()
        input_text = 'keyed<Length>{"left": self.scale, "right": self.scale * 2}' if name == "panel-identity" else "self.coefficients"
        body_text = "v" if name == "panel-identity" else "v * self.scale"
        expression = mapper("Length", input_text, body_text)
        start = module_text.index(expression)
        source_id = "package:fixture.panels@1.0.0"
        def location(offset, length):
            return {"source_id": source_id, "start_byte": offset, "end_byte": offset + length,
                    "source_revision": digest(module_text.encode())}
        input_start = start + len("map_keyed<Length>(")
        body_start = start + expression.rindex(" -> ") + 4
        entry_texts = {"left": '"left": self.scale', "right": '"right": self.scale * 2'} if name == "panel-identity" else {"left": '"left": 1', "right": '"right": 2'}
        case["expected"]["transform_provenance"] = {
            "expression": location(start, len(expression)), "input": location(input_start, len(input_text)),
            "body": location(body_start, len(body_text)),
            "input_element_kind": "Quantity" if name == "panel-identity" else "Real", "output_element_kind": "Quantity",
            "original_key_entries": {key: location(module_text.index(text, input_start if name == "panel-identity" else 0), len(text)) for key, text in entry_texts.items()},
            "read_only": True}
    invalid = assembly_source(module, repaired=True).replace("scale = 1.5[m];", "scale = -1[m];")
    add("panel-task-invalid", invalid, modules=[("fixture.panels", module)], assets=["label"],
        outcome="invalid", code="OKL-E-EXTRUSION-WINDING", tags=["repair", "invalid-geometry", "rollback"])
    request = "execution { max_operations = 400000; max_elapsed = 80[s]; }\n"
    add("panel-task-higher-budget", assembly_source(module, execution=request), modules=[("fixture.panels", module)], assets=["label"],
        control=assembly_source(control_module, legacy=True, execution=request), control_modules=[("fixture.panels", control_module)],
        expected=panel_expectations(), policy=LARGE_POLICY, tags=["source-budget", "host-authority", "destination"], stage="delivered")
    add("panel-task-ungranted-budget", assembly_source(module, execution=request), modules=[("fixture.panels", module)], assets=["label"],
        outcome="invalid", code="OKL-E-RESOURCE", tags=["source-budget", "host-authority"])


def main():
    seed_assets()
    build_scalars()
    build_leaves()
    build_negative()
    build_imports()
    build_provenance()
    build_boundaries_and_assets()
    build_panels()
    write("expected.json", {"schema_version": "ontokin.c081-independent-expected/0.1",
          "status": "predetermined_inputs_not_product_execution", "source_baseline": SOURCE_BASELINE,
          "source_version": SOURCE_VERSION, "profile": PROFILE, "agent_protocol": "ontokin.agent/0.14",
          "target_contract": "ontokin.glb/0.14", "case_count": len(CASES), "cases": CASES,
          "counts_are_not_execution_results": True,
          "independence": "Sources, scalar results, panel dimensions, UVs, volume and motion were authored from the specification; no C081 runtime output supplies expected answers."})
    print(json.dumps({"cases": len(CASES), "valid": sum(c["expected_outcome"] == "valid" for c in CASES),
                      "invalid": sum(c["expected_outcome"] == "invalid" for c in CASES)}))


if __name__ == "__main__":
    main()
