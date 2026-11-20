"""Independently authored C267 hinge fixtures; no observer supplies expectations.

The C266 recipe helper supplies known source/object provenance. This file writes
joint fields and site identities from explicit recipe arguments and adopted
identity/unit rules. It is a finite test builder, not an OntoKin parser.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import re
import sys
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def load_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


base = load_file("c267_independent_c266_recipes",
                 HERE.parent / "localized-repair-c266/binding_control_fixtures.py")
PI64 = Fraction.from_float(float.fromhex("0x1.921fb54442d18p+1"))
DEG45 = float(Fraction(45) * PI64 / 180)


def angle(value: str, unit: str) -> float:
    """One rounding from the independently specified rational unit conversion."""
    return float(Fraction(value) * (PI64 / 180 if unit == "deg" else 1))


@dataclass
class ComparisonFixture:
    sources: dict[str, bytes]
    doc: dict
    objects: dict[str, dict]
    joints: dict[str, dict]
    binary: bytes = b""

    @property
    def raw(self):
        return base.encode_glb(self.doc, self.binary)

    def copy(self):
        return copy.deepcopy(self)


def expected_joints(objects, *, finger_key="finger", part_name="blade",
                    joint_name="flex", joint_key="flex", parent_name="pivot",
                    parent_key="pivot", child_name="base", child_key="base",
                    swapped=False, axis=(0, 0, 1), limits=(-DEG45, DEG45), initial=0):
    answer = {}
    for owner in objects.values():
        if owner["definition_id"][-1] != finger_key:
            continue
        child = objects[owner["path"] + "." + part_name]
        own_site = {"id": owner["element_id"] + [parent_key],
                    "definitionId": owner["definition_id"] + [parent_key],
                    "objectId": owner["element_id"],
                    "objectDefinitionId": owner["definition_id"],
                    "path": owner["path"] + "." + parent_name,
                    "name": parent_name, "key": parent_key}
        part_site = {"id": child["element_id"] + [child_key],
                     "definitionId": child["definition_id"] + [child_key],
                     "objectId": child["element_id"],
                     "objectDefinitionId": child["definition_id"],
                     "path": child["path"] + "." + child_name,
                     "name": child_name, "key": child_key}
        parent, endpoint_child = (part_site, own_site) if swapped else (own_site, part_site)
        path = owner["path"] + "." + joint_name
        answer[path] = {
            "id": owner["element_id"] + [joint_key],
            "definitionId": owner["definition_id"] + [joint_key],
            "path": path, "name": joint_name, "key": joint_key,
            "ownerId": owner["element_id"], "ownerDefinitionId": owner["definition_id"],
            "kind": "hinge", "axis": list(axis), "limits": list(limits), "initial": initial,
            "parentSite": parent, "childSite": endpoint_child,
        }
    return answer


def rows(joints):
    return [{"path": row["path"], "element_id": row["id"], "kind": "hinge",
             "parent_site": row["parentSite"]["path"], "child_site": row["childSite"]["path"],
             "axis": row["axis"], "limits": row["limits"], "initial": row["initial"]}
            for row in joints.values()]


def original(endpoint="before"):
    fixture = base.original(endpoint)
    return ComparisonFixture(fixture.sources, fixture.doc, fixture.expected,
                             expected_joints(fixture.expected), fixture.binary)


def synthetic(*, first_keys=("lower", "middle", "upper"), second_keys=("bottom", "top"),
              mode="helper_default", renamed=False, unicode_prefix=False, edits=(),
              joint_name="flex", joint_key="flex", parent_name="pivot", parent_key="pivot",
              child_name="base", child_key="base", swapped=False,
              source_axis="vec3(0, 0, 1)", axis=(0, 0, 1),
              source_limits="range(-45[deg], 45[deg])", limits=(-DEG45, DEG45),
              source_initial="0[rad]", initial=0):
    fixture = base.synthetic(first_keys=first_keys, second_keys=second_keys,
                             mode=mode, renamed=renamed, unicode_prefix=unicode_prefix)
    n = dict(module_name="KeyedRack", module_key="keyed-rack", package_module_name="Hinges",
             package_module_key="hinges", scene_key="demo", rack_name="Rack", rack_key="rack",
             finger_name="Finger", finger_key="finger", blade_name="Blade", blade_key="blade",
             collection_name="fingers", collection_key="fingers", part_name="blade",
             part_key="blade", input_name="mounts")
    if renamed:
        n.update(module_name="ReboundRack", module_key="rack.module-2", package_module_name="Mechanism",
                 package_module_key="parts.lib-2", scene_key="demo.scene-2", rack_name="Carrier",
                 rack_key="carrier.kind-2", finger_name="Digit", finger_key="digit.kind-2",
                 blade_name="Leaf", blade_key="leaf.kind-2", collection_name="digits",
                 collection_key="digits.set-2", part_name="leaf", part_key="leaf.part-2", input_name="anchors")
    root_names = ("alpha", "omega") if renamed else ("first", "second")
    root_keys = ("root.alpha-2", "root.omega-2") if renamed else ("first", "second")
    leaf = fixture.sources["hinges.ok"].decode("utf-8")
    changes = [("public joint flex @ \"flex\"", f'public joint {joint_name} @ "{joint_key}"'),
               ('public site pivot @ "pivot"', f'public site {parent_name} @ "{parent_key}"'),
               ('public site base @ "base"', f'public site {child_name} @ "{child_key}"'),
               ("parent = self.pivot;", "parent = self." + parent_name + ";"),
               ("child = self." + n["part_name"] + ".base;",
                "child = self." + n["part_name"] + "." + child_name + ";"),
               ("axis = vec3(0, 0, 1);", "axis = " + source_axis + ";"),
               ("limits = range(-45[deg], 45[deg]);", "limits = " + source_limits + ";"),
               ("initial = 0[rad];", "initial = " + source_initial + ";")]
    for old, new in changes:
        assert old in leaf, old
        leaf = leaf.replace(old, new)
    if swapped:
        leaf = leaf.replace("parent = self." + parent_name + ";",
                            "parent = self." + n["part_name"] + "." + child_name + ";")
        leaf = leaf.replace("child = self." + n["part_name"] + "." + child_name + ";",
                            "child = self." + parent_name + ";")
    for old, new in edits:
        assert old in leaf, old
        leaf = leaf.replace(old, new)
    sources = {"hinges.ok": leaf.encode("utf-8"), "main.ok": fixture.sources["main.ok"]}
    sources["main.ok"] = re.sub(rb'digest "sha256:[0-9a-f]{64}"',
        b'digest "sha256:' + base.digest(sources["hinges.ok"]).encode() + b'"', sources["main.ok"])
    first_location = (("main.ok", sources["main.ok"].index(b"public param"))
                      if mode == "direct_default" else ("hinges.ok", 0))
    if mode == "final_override":
        first_location = ("main.ok", sources["main.ok"].index(("object " + root_names[0]).encode()))
    second_location = (("hinges.ok", sources["hinges.ok"].index(b"public fn override_members"))
                       if mode == "helper_override" else
                       ("main.ok", sources["main.ok"].index(("object " + root_names[1]).encode())))
    objects = base.derive_recipe_maps(sources, root_names=root_names, root_keys=root_keys,
        memberships=(first_keys, second_keys), entry_locations=(first_location, second_location), **n)
    doc = base.bind_recipe_doc(sources, objects, **{k: n[k] for k in
        ("module_name", "module_key", "package_module_name", "package_module_key")})
    joints = expected_joints(objects, finger_key=n["finger_key"], part_name=n["part_name"],
        joint_name=joint_name, joint_key=joint_key, parent_name=parent_name, parent_key=parent_key,
        child_name=child_name, child_key=child_key, swapped=swapped, axis=axis, limits=limits, initial=initial)
    doc["extras"]["ontokin"]["joints"] = rows(joints)
    return ComparisonFixture(sources, doc, objects, joints)
