"""Construction semantics against fixed source/pose and scoped-edit oracles.

These tests use real bundle/link/type/expansion/evaluation paths. In particular,
the Rack expected states were committed in the adopted contract before this
compiler existed; expected dimensions and transforms are not exporter output.
"""

import json
from pathlib import Path
import unittest

from ontokin.bundle import load_bundle
from ontokin.construction import compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.evaluator import evaluate
from ontokin.scene import rotation_error
from ontokin.syntax import parse
from ontokin.validator import validate


ROOT = Path(__file__).resolve().parents[1]
RACK = ROOT / "docs/language-design/construction-v0.1/01-keyed-rack"


def bundle(source):
    return load_bundle({"schema_version": "ontokin.bundle/0.1",
                        "entry": {"filename": "main.ok", "source": source}, "modules": []})


def source(classes="", objects='object rig @ "rig": Object {}', extra="", duration="2"):
    return f'''ontokin "0.2";
module ConstructionTest @ "construction-test";
profile "construction-0.1";
{classes}
scene Demo @ "demo" {{
 duration = {duration}[s];
 gravity = vector(world, 0[m/s^2], -10[m/s^2], 0[m/s^2]);
 {objects}
 {extra}
}}
'''


LEAF = '''class Leaf @ "leaf" {
 public param size @ "size": Length = 0.2[m];
 geometry = sphere(self.size);
}'''


RELEASE_SOURCE = source('''class Payload @ "payload" {
 public param radius @ "radius": Length = 0.1[m];
 public param carrier_site @ "carrier-site": SiteRef = self.origin;
 geometry = sphere(self.radius);
 physical = sphere_body(self.radius, 1[kg]);
 public joint hold @ "hold": grip { parent = self.carrier_site; child = self.origin; }
}
class Rig @ "rig-class" {
 geometry = box(vec3(0.3[m], 0.3[m], 0.3[m]));
 public site tip @ "tip" {
  pose = pose(self.frame, vec3(0.5[m], 0[m], 0[m]), quat(1, 0, 0, 0));
  interface = "rigid.origin"; size = 0[m];
 }
 public parts balls @ "balls": Payload for (key, radius) in keyed<Length>{"one": 0.1[m], "two": 0.2[m]} {
  radius = radius; carrier_site = self.tip;
 }
}''', '''object rig @ "rig": Rig {
 placement = pose(world, vec3(0[m], 2[m], 0[m]), quat(1, 0, 0, 0));
}''', '''action travel @ "travel" = move(rig, vector(world, 1[m/s], 0[m/s], 0[m/s]), 2[s]);
at 0[s] sequence { start travel; }
at 1[s] sequence { release rig.balls["one"].hold using incoming; }''')


def family(entries='"a": 0.2[m], "b": 0.3[m]', *, generated_body="size = size;",
           input_expression="self.sizes", members=""):
    return LEAF + f'''
class Family @ "family" {{
 public param sizes @ "sizes": Keyed<Length> = keyed<Length>{{{entries}}};
 {members}
 public parts leaves @ "leaves": Leaf for (key, size) in {input_expression} {{
  {generated_body}
 }}
}}'''


class ConstructionTests(unittest.TestCase):
    def error(self, text, code=None, **kwargs):
        with self.assertRaises(OntoKinError) as caught:
            compile_construction(bundle(text), **kwargs)
        error = caught.exception
        if code is not None:
            self.assertEqual(error.code, code, error.diagnostic.message)
        return error

    def test_frozen_rack_all_126_independent_world_poses(self):
        expected = json.loads((RACK / "expected.json").read_text())
        sealed = load_bundle(json.loads((RACK / "program.bundle.json").read_text()))
        compiler = compile_construction(sealed, level="evaluated")
        model = compiler.model
        self.assertEqual(model.program_revision, expected["program_revision"])
        self.assertEqual(model.profile, "construction-0.1")
        self.assertEqual(len(model.objects), 18)
        self.assertEqual(len(model.follows), 8)
        self.assertEqual(len(model.joints), 8)
        for record in expected["objects"]:
            obj = model.objects[record["path"]]
            self.assertEqual(list(obj.element_id), record["element_id"])
            self.assertEqual(obj.owner, record["owner"])
            self.assertEqual(list(compiler.definition_id(obj.class_name)), record["definition_id"])
            self.assertEqual(obj.mass, 0)
            self.assertEqual(model.owned_mass(obj.path), 0)
            geometry = record["geometry"]
            self.assertEqual(obj.geometry["kind"], geometry["kind"])
            if geometry["kind"] == "sphere":
                self.assertAlmostEqual(obj.geometry["radius"], geometry["radius_m"], delta=1e-12)
            else:
                for actual, wanted in zip(obj.geometry["size"], geometry["size_m"]):
                    self.assertAlmostEqual(actual, wanted, delta=1e-12)
        samples = evaluate(model, [sample["seconds"] for sample in expected["samples"]])["samples"]
        comparisons = 0
        for actual, wanted in zip(samples, expected["samples"]):
            self.assertEqual(set(actual["objects"]), {o["path"] for o in wanted["objects"]})
            for obj in wanted["objects"]:
                pose = actual["objects"][obj["path"]]
                self.assertLessEqual(max(abs(a - b) for a, b in zip(pose["position_m"], obj["position_m"])), 1e-9)
                self.assertLessEqual(rotation_error(pose["orientation_wxyz"], obj["rotation_wxyz"]), 1e-9)
                comparisons += 1
        self.assertEqual(comparisons, 126)
        for owner, keys in expected["canonical_keys"].items():
            self.assertEqual(compiler.collections[owner + ".fingers"]["ordered_keys"], keys)

    def test_generated_provenance_and_precise_public_repair_target(self):
        compiler = compile_construction(load_bundle(json.loads((RACK / "program.bundle.json").read_text())))
        path = 'first.fingers["middle"]'
        record = compiler.occurrence_provenance[path]
        self.assertEqual(record["declaration_node"].source_id, "entry")
        self.assertEqual(record["definition_node"].source_id, "package:example.hinges@1.0.0")
        self.assertEqual(record["generated"]["input_entry_node"].source_id, "package:example.hinges@1.0.0")
        target = compiler.initializer_target(path, "length")
        self.assertTrue(target["available"])
        self.assertEqual(target["rendered_path"], 'fingers["middle"].length')
        self.assertEqual([s.kind for s in target["parameter_path"]], ["member", "key", "member"])
        node = target["assignment_node"]
        self.assertEqual(compiler.source_for(node).raw[node.start:node.end].decode(), 'fingers["middle"].length = 0.75[m];')
        self.assertIsNone(compiler.initializer_target('second.fingers["middle"]', "length")["assignment_node"])
        self.assertFalse(compiler.initializer_target(path + ".blade", "length")["available"])
        self.assertEqual(compiler.model.source_provenance["entry"]["source_revision"], compiler.bundle.entry.revision)

    def test_rack_matches_separately_authored_ordinary_assembly(self):
        explicit = validate(parse((ROOT / "tests/fixtures/rack_explicit.ok").read_text()), level="evaluated")
        keyed = compile_construction(load_bundle(json.loads((RACK / "program.bundle.json").read_text()))).model
        mapping = {"first": "first", "second": "second"}
        for owner, keys in (("first", ("lower", "middle", "upper")),
                            ("second", ("bottom", "lower", "middle", "top", "upper"))):
            for key in keys:
                mapping[f'{owner}.fingers["{key}"]'] = f"{owner}.{key}"
                mapping[f'{owner}.fingers["{key}"].blade'] = f"{owner}.{key}.blade"
        self.assertEqual(set(mapping), set(keyed.objects))
        self.assertEqual(set(mapping.values()), set(explicit.objects))
        for generated, ordinary in mapping.items():
            a, b = keyed.objects[generated], explicit.objects[ordinary]
            self.assertEqual(a.geometry["kind"], b.geometry["kind"])
            if a.geometry["kind"] == "box":
                for x, y in zip(a.geometry["size"], b.geometry["size"]):
                    self.assertAlmostEqual(x, y, delta=1e-12)
            else:
                self.assertEqual(a.geometry, b.geometry)
            self.assertEqual(a.appearance, b.appearance)
            self.assertEqual(a.mass, b.mass)
            self.assertEqual(mapping.get(a.owner), b.owner)
            self.assertEqual(keyed.owned_mass(generated), explicit.owned_mass(ordinary))
        times = [0, .25, .5, .75, 1, 1.5, 2]
        for a, b in zip(evaluate(keyed, times)["samples"], evaluate(explicit, times)["samples"]):
            for generated, ordinary in mapping.items():
                x, y = a["objects"][generated], b["objects"][ordinary]
                self.assertLessEqual(max(abs(v - w) for v, w in zip(x["position_m"], y["position_m"])), 1e-9)
                self.assertLessEqual(rotation_error(x["orientation_wxyz"], y["orientation_wxyz"]), 1e-9)

    def test_stable_keys_order_insert_remove_and_dot_key(self):
        original = compile_construction(bundle(source(family('"left.eye": 0.2[m], "right": 0.3[m]'),
                                                      'object rig @ "rig": Family {}')))
        reordered = compile_construction(bundle(source(family('"right": 0.3[m], "left.eye": 0.2[m]'),
                                                       'object rig @ "rig": Family {}')))
        changed = compile_construction(bundle(source(family('"new": 0.5[m], "left.eye": 0.2[m]'),
                                                     'object rig @ "rig": Family {}')))
        path = 'rig.leaves["left.eye"]'
        for compiler in (original, reordered, changed):
            self.assertEqual(compiler.model.objects[path].element_id,
                             ("construction-test", "demo", "rig", "leaves", "left.eye"))
            self.assertEqual(compiler.model.objects[path].owner, "rig")
            self.assertEqual(compiler.model.objects[path].geometry["radius"], .2)
        self.assertNotEqual(original.model.program_revision, reordered.model.program_revision)
        self.assertEqual(set(original.model.objects), set(reordered.model.objects))
        self.assertNotIn('rig.leaves["right"]', changed.model.objects)
        self.assertIn('rig.leaves["new"]', changed.model.objects)

    def test_empty_singleton_have_no_collection_body_or_frame(self):
        for entries, count in (("", 0), ('"one": 0.3[m]', 1)):
            compiler = compile_construction(bundle(source(family(entries), 'object rig @ "rig": Family {}')))
            self.assertEqual(len(compiler.model.objects), 1 + count)
            self.assertEqual(len(compiler.model.sites), 1 + count)
            self.assertNotIn("rig.leaves", compiler.model.objects)
            self.assertEqual(compiler.model.owned_mass("rig"), 0)

    def test_empty_body_still_type_access_and_recursive_composition_checked(self):
        self.error(source(family("", generated_body="size = 1[s];"), 'object rig @ "rig": Family {}'), "OKL-E-UNIT")
        self.error(source(family("", generated_body="missing = 1[m];"), 'object rig @ "rig": Family {}'), "OKL-E-NAME")
        private = family("", generated_body="size = 1[m];").replace("public param size @", "private param size @")
        self.error(source(private, 'object rig @ "rig": Family {}'), "OKL-E-ACCESS")
        recursive = '''class Loop @ "loop" {
 public parts children @ "children": Loop for (k, v) in keyed<Length>{} {}
}'''
        self.error(source(recursive, 'object rig @ "rig": Loop {}'), "OKL-E-RECURSIVE-COMPOSITION")

    def test_keyed_literal_coercion_is_per_entry_and_collection_is_invariant(self):
        classes = '''class Values @ "values" {
 public param input @ "input": Keyed<Real> = keyed<Real>{"x": 1};
 public derive selected @ "selected": Real = self.input["x"];
 public derive count @ "count": Int = len(self.input);
}'''
        compiler = compile_construction(bundle(source(classes, 'object rig @ "rig": Values {}')))
        self.assertEqual(compiler.model.objects["rig"].properties["selected"].value, 1.0)
        self.assertEqual(compiler.model.objects["rig"].properties["count"].value, 1)
        self.error(source(classes.replace('keyed<Real>{"x": 1}', 'keyed<Int>{"x": 1}'),
                          'object rig @ "rig": Values {}'), "OKL-E-TYPE")

    def test_no_keyed_operators_or_nested_reference_inputs(self):
        for op in ("==", "!=", "+", "<"):
            text = family(members=f'public derive invalid @ "invalid": Bool = self.sizes {op} self.sizes;')
            self.error(source(text, 'object rig @ "rig": Family {}'), "OKL-E-TYPE")
        for typ in ("Keyed<Length>", "Ref<Object>", "Geometry", "BodyModel", "Action"):
            classes = f'class Bad @ "bad" {{ public param data @ "data": Keyed<{typ}> = keyed<{typ}>{{}}; }}'
            self.error(source(classes, 'object rig @ "rig": Bad {}'), "OKL-E-CAPABILITY-UNSUPPORTED")

    def test_duplicate_invalid_missing_and_wrong_dimension_keys(self):
        for entries, code in (('"x": 0.2[m], "x": 0.3[m]', "OKL-E-ID"),
                              ('"bad/key": 0.2[m]', "OKL-E-ID"),
                              ('"x": 1[s]', "OKL-E-UNIT")):
            self.error(source(family(entries), 'object rig @ "rig": Family {}'), code)
        self.error(source(family(), 'object rig @ "rig": Family { leaves["missing"].size = 0.5[m]; }'), "OKL-E-NAME")
        self.error(source(family(members='public derive bad @ "bad": Length = self.sizes["missing"];'),
                          'object rig @ "rig": Family {}'), "OKL-E-NAME")

    def test_per_key_scope_precedence_and_duplicate_write(self):
        objects = '''object first @ "first": Family { leaves["a"].size = 0.7[m]; }
object second @ "second": Family {}'''
        compiler = compile_construction(bundle(source(family(), objects)))
        self.assertEqual(compiler.model.objects['first.leaves["a"]'].geometry["radius"], .7)
        self.assertEqual(compiler.model.objects['first.leaves["b"]'].geometry["radius"], .3)
        self.assertEqual(compiler.model.objects['second.leaves["a"]'].geometry["radius"], .2)
        self.error(source(family(), objects.replace('leaves["a"].size = 0.7[m];',
                                                    'leaves["a"].size = 0.7[m]; leaves["a"].size = 0.8[m];')), "OKL-E-NAME")
        self.error(source(family(), 'object rig @ "rig": Family { leaves["a"].geometry = sphere(1[m]); }'), "OKL-E-NAME")

    def test_final_keyed_override_replaces_shape_before_registration(self):
        classes = family() + '''class Outer @ "outer" {
 public part family @ "family": Family { sizes = keyed<Length>{"inner": 0.4[m]}; }
}'''
        compiler = compile_construction(bundle(source(classes, '''object rig @ "rig": Outer {
 family.sizes = keyed<Length>{"final": 0.8[m]}; family.leaves["final"].size = 0.9[m];
}''')))
        self.assertEqual(set(compiler.model.objects), {"rig", "rig.family", 'rig.family.leaves["final"]'})
        self.assertEqual(compiler.model.objects['rig.family.leaves["final"]'].geometry["radius"], .9)
        self.error(source(classes, '''object rig @ "rig": Outer {
 family.sizes = keyed<Length>{"final": 0.8[m]}; family.leaves["inner"].size = 0.9[m];
}'''), "OKL-E-NAME")

    def test_generated_child_own_final_input_drives_nested_shape(self):
        classes = family() + '''class Outer @ "outer" {
 public parts families @ "families": Family for (key, input) in keyed<Length>{"one": 0.6[m]} {
  sizes = keyed<Length>{"body": input};
 }
}'''
        compiler = compile_construction(bundle(source(classes, '''object rig @ "rig": Outer {
 families["one"].sizes = keyed<Length>{"final": 0.8[m]};
 families["one"].leaves["final"].size = 0.9[m];
}''')))
        leaf = 'rig.families["one"].leaves["final"]'
        self.assertEqual(set(compiler.model.objects), {"rig", 'rig.families["one"]', leaf})
        self.assertEqual(compiler.model.objects[leaf].geometry["radius"], .9)
        self.assertEqual(compiler.model.objects[leaf].element_id,
                         ("construction-test", "demo", "rig", "families", "one", "leaves", "final"))

    def test_deeper_generated_parent_lexical_self_inputs_feed_child_shape(self):
        classes = family() + '''class Parent @ "parent" {
 public param mounts @ "mounts": Keyed<Length> = keyed<Length>{"final": 0.4[m]};
 public parts children @ "children": Family for (k,v) in keyed<Int>{"child": 1, "sibling": 2} {
  sizes = self.mounts;
 }
}
class Outer @ "outer" {
 public parts parents @ "parents": Parent for (k,v) in keyed<Int>{"parent": 1} {}
}'''
        compiler = compile_construction(bundle(source(classes, 'object rig @ "rig": Outer {}')))
        leaf = 'rig.parents["parent"].children["child"].leaves["final"]'
        self.assertIn(leaf, compiler.model.objects)
        self.assertEqual(compiler.model.objects[leaf].geometry["radius"], .4)
        tainted = classes.replace('sizes = self.mounts;', 'sizes = keyed<Length>{"copied": self.children["sibling"].leaves["final"].size};')
        self.error(source(tainted, 'object rig @ "rig": Outer {}'), "OKL-E-DEPENDENCY-CYCLE")

    def test_cached_generated_scalar_and_true_derived_cycle_remain_invalid(self):
        classes = family(members='public derive copied @ "copied": Length = self.leaves["a"].size;')
        compiler = compile_construction(bundle(source(classes, 'object rig @ "rig": Family {}')))
        self.assertEqual(compiler.field("rig", "copied").value, .2)
        self.assertIn(("rig", "copied"), compiler.memo)
        self.assertTrue(compiler.generated_dependencies[("rig", "copied")])
        # The property is already memoized. A later shape-read checkpoint must
        # still reject its retained dependency; no expression is re-executed.
        compiler._shape_stack.append("rig")
        try:
            with self.assertRaises(OntoKinError) as caught:
                compiler.field("rig", "copied")
            self.assertEqual(caught.exception.code, "OKL-E-DEPENDENCY-CYCLE")
        finally:
            compiler._shape_stack.pop()
        cyclic = '''class Cycle @ "cycle" {
 public derive a @ "a": Length = self.b;
 public derive b @ "b": Length = self.a;
}'''
        self.error(source(cyclic, 'object rig @ "rig": Cycle {}'), "OKL-E-DEPENDENCY-CYCLE")

    def test_helper_preserves_lexical_self_origin_through_base_ref_coercion(self):
        classes = family() + '''class Inputs @ "inputs" {
 public param mounts @ "mounts": Keyed<Length> = keyed<Length>{"final": 0.4[m]};
}
fn mounts @ "get-mounts"(p: Ref<Inputs>) -> Keyed<Length> { return p.mounts; }
class Parent @ "parent" extends Inputs {
 public parts children @ "children": Family for (k,v) in keyed<Int>{"child": 1} {
  sizes = mounts(self);
 }
}
class Outer @ "outer" {
 public parts parents @ "parents": Parent for (k,v) in keyed<Int>{"parent": 1} {}
}'''
        compiler = compile_construction(bundle(source(classes, 'object rig @ "rig": Outer {}')))
        leaf = 'rig.parents["parent"].children["child"].leaves["final"]'
        self.assertEqual(compiler.model.objects[leaf].geometry["radius"], .4)
        tainted = family() + '''class Inputs @ "inputs" {
 public param mounts @ "mounts": Keyed<Length> = keyed<Length>{"final": 0.4[m]};
}
fn mounts @ "get-mounts"(p: Ref<Inputs>) -> Keyed<Length> { return p.mounts; }
class Parent @ "parent" extends Inputs {}
class Outer @ "outer" {
 public parts parents @ "parents": Parent for (k,v) in keyed<Int>{"parent": 1} {}
 public parts children @ "children": Family for (k,v) in keyed<Int>{"child": 1} {
  sizes = mounts(self.parents["parent"]);
 }
}'''
        self.error(source(tainted, 'object rig @ "rig": Outer {}'), "OKL-E-DEPENDENCY-CYCLE")

    def test_tainted_copy_does_not_poison_shared_untainted_keyed_input(self):
        classes = family(members='''public derive copied @ "copied": Keyed<Length> =
 if len(self.leaves) > 0 then self.sizes else keyed<Length>{};''')
        compiler = compile_construction(bundle(source(classes, 'object rig @ "rig": Family {}')))
        original, copied = compiler.field("rig", "sizes"), compiler.field("rig", "copied")
        self.assertIs(original.value, copied.value)
        self.assertIsNot(original, copied)
        compiler._shape_stack.append("rig")
        try:
            self.assertEqual(compiler.field("rig", "sizes").value, original.value)
            with self.assertRaises(OntoKinError):
                compiler.field("rig", "copied")
        finally:
            compiler._shape_stack.pop()

    def test_shape_forbids_generated_views_len_and_cached_derivation(self):
        for expression in ('keyed<Length>{"x": self.leaves["a"].size}',
                           'if len(self.leaves) == 0 then self.sizes else self.sizes'):
            self.error(source(family(input_expression=expression), 'object rig @ "rig": Family {}'), "OKL-E-DEPENDENCY-CYCLE")
        classes = family() + '''class Other @ "other" {
 public param sizes @ "sizes": Keyed<Length> = keyed<Length>{};
 public parts leaves @ "leaves": Leaf for (k, v) in self.sizes { size = v; }
}'''
        objects = '''object first @ "first": Family {}
object second @ "second": Other { sizes = keyed<Length>{"copied": first.leaves["a"].size}; }'''
        self.error(source(classes, objects), "OKL-E-DEPENDENCY-CYCLE")
        # Pure result memoization cannot erase a generated lookup. A regular
        # field is forced while another sibling input is evaluated, then reused.
        classes = family() + '''class Outer @ "outer" {
 public part family @ "family": Family {}
 public derive copied @ "copied": Length = self.family.leaves["a"].size;
 public parts bad @ "bad": Leaf for (k,v) in keyed<Length>{"x": self.copied} { size = v; }
}'''
        self.error(source(classes, 'object rig @ "rig": Outer {}'), "OKL-E-DEPENDENCY-CYCLE")

    def test_tainted_body_assignment_cannot_become_own_nested_input(self):
        classes = family() + '''class Outer @ "outer" {
 public part originals @ "originals": Family {}
 public parts families @ "families": Family for (key, input) in keyed<Length>{"one": 0.6[m]} {
  sizes = keyed<Length>{"copied": self.originals.leaves["a"].size};
 }
}'''
        self.error(source(classes, 'object rig @ "rig": Outer {}'), "OKL-E-DEPENDENCY-CYCLE")

    def test_lazy_unused_generated_read_branch_is_typechecked_only(self):
        classes = family(input_expression='if true then self.sizes else keyed<Length>{"x": self.leaves["a"].size}')
        compiler = compile_construction(bundle(source(classes, 'object rig @ "rig": Family {}')))
        self.assertEqual(len(compiler.model.objects), 3)
        self.error(source(classes.replace('self.leaves["a"].size', 'self.leaves["a"].missing'),
                          'object rig @ "rig": Family {}'), "OKL-E-NAME")

    def test_all_generated_sibling_shells_exist_before_body_fields(self):
        classes = LEAF + '''class Family @ "family" {
 public parts leaves @ "leaves": Leaf for (k,v) in keyed<Length>{"a": 0.2[m], "z": 0.4[m]} {
 size = if k == "a" then self.leaves["z"].size else v;
 }
}'''
        compiler = compile_construction(bundle(source(classes, 'object rig @ "rig": Family {}')))
        self.assertEqual(compiler.model.objects['rig.leaves["a"]'].geometry["radius"], .4)
        self.assertEqual(compiler.model.objects['rig.leaves["z"]'].geometry["radius"], .4)

    def test_nonzero_own_and_aggregate_mass_has_no_collection_contribution(self):
        classes = family().replace('geometry = sphere(self.size);',
                                    'geometry = sphere(self.size); physical = sphere_body(self.size, 2[kg]);')
        compiler = compile_construction(bundle(source(classes, 'object rig @ "rig": Family {}')))
        self.assertEqual(compiler.model.owned_mass("rig"), 4)
        self.assertEqual(compiler.model.owned_mass('rig.leaves["a"]'), 2)
        self.assertEqual(compiler.model.objects["rig"].mass, 0)

    def test_generated_grip_release_inherits_world_motion_then_gravity(self):
        compiler = compile_construction(bundle(RELEASE_SOURCE), level="evaluated")
        model = compiler.model
        self.assertEqual(len(model.objects), 3)
        self.assertEqual(len(model.joints), 2)
        self.assertEqual(model.owned_mass("rig"), 2)
        self.assertEqual(model.objects['rig.balls["one"]'].owner, "rig")
        requests = [{"time_seconds": "1", "side": "before"},
                    {"time_seconds": "1", "side": "after"}, "1.5", "2"]
        samples = evaluate(model, requests)["samples"]
        for sample in samples:
            t = float(sample["time_seconds"])
            tau = max(0, t - 1)
            first = sample["objects"]['rig.balls["one"]']
            second = sample["objects"]['rig.balls["two"]']
            self.assertEqual(first["position_m"], [t + .5, 2 - 5 * tau * tau, 0])
            self.assertEqual(second["position_m"], [t + .5, 2, 0])
            self.assertEqual(first["velocity_m_per_s"], [1, -10 * tau, 0])
            self.assertEqual(first["own_mass_kg"], 1)
        self.assertEqual(samples[0]["objects"]['rig.balls["one"]']["motion"], "prescribed")
        self.assertEqual(samples[1]["objects"]['rig.balls["one"]']["motion"], "dynamic")

    def test_key_count_256_and_257_boundary(self):
        entries = ",".join(f'"k{i}": 0.2[m]' for i in range(256))
        compiler = compile_construction(bundle(source(family(entries), 'object rig @ "rig": Family {}')))
        self.assertEqual(len(compiler.model.objects), 257)
        self.error(source(family(entries + ',"extra": 0.2[m]'), 'object rig @ "rig": Family {}'), "OKL-E-RESOURCE")

    def test_1000_objects_and_one_over(self):
        objects = "\n".join(f'object p{i} @ "p{i}": Object {{}}' for i in range(1000))
        compiler = compile_construction(bundle(source(objects=objects)))
        self.assertEqual(len(compiler.model.objects), 1000)
        self.error(source(objects=objects + '\nobject extra @ "extra": Object {}'), "OKL-E-RESOURCE")

    def test_1000_total_generated_objects_and_one_over(self):
        def text(last):
            collections = []
            for name, count in (("a", 256), ("b", 256), ("c", 256), ("d", last)):
                entries = ",".join(f'"k{i}": {i}' for i in range(count))
                collections.append(f'public parts {name} @ "{name}": Object for (k,v) in keyed<Int>{{{entries}}} {{}}')
            return source('class Generated @ "generated" {' + "\n".join(collections) + '}',
                          'object rig @ "rig": Generated {}')
        compiler = compile_construction(bundle(text(231)))
        self.assertEqual(len(compiler.model.objects), 1000)
        self.assertEqual(sum(len(c["ordered_keys"]) for c in compiler.collections.values()), 999)
        error = self.error(text(232), "OKL-E-RESOURCE")
        self.assertEqual(error.diagnostic.details["budget"], "max_objects")

    def test_repeated_generated_reference_views_charge_logical_values(self):
        entries = ",".join(f'"k{i}": 0.2[m]' for i in range(128))
        reads = "\n".join(f'public derive n{i} @ "n{i}": Int = len(self.leaves);' for i in range(210))
        error = self.error(source(family(entries, members=reads), 'object rig @ "rig": Family {}'), "OKL-E-RESOURCE")
        self.assertEqual(error.diagnostic.details["budget"], "max_value_entries")

    def test_ownership_depth64_and65_before_host_recursion(self):
        def chain(depth):
            classes = "\n".join(f'class C{i} @ "c{i}" {{ public part next @ "next": C{i+1} {{}} }}'
                                for i in range(depth))
            classes += f'\nclass C{depth} @ "c{depth}" {{}}'
            return source(classes, 'object rig @ "rig": C0 {}')
        compiler = compile_construction(bundle(chain(64)))
        self.assertEqual(len(compiler.model.objects), 65)
        self.error(chain(65), "OKL-E-RESOURCE")

    def test_generated_collection_steps_add_no_ownership_depth(self):
        def chain(depth):
            classes = "\n".join(f'class C{i} @ "c{i}" {{ public parts next @ "next": C{i+1} '
                                'for (k,v) in keyed<Int>{"one": 1} {} }'
                                for i in range(depth))
            classes += f'\nclass C{depth} @ "c{depth}" {{}}'
            return source(classes, 'object rig @ "rig": C0 {}')
        compiler = compile_construction(bundle(chain(64)))
        leaf = 'rig' + '.next["one"]' * 64
        self.assertEqual(len(compiler.model.objects), 65)
        self.assertEqual(compiler.occurrence_provenance[leaf]["ownership_depth"], 64)
        self.assertEqual(len(compiler.model.objects[leaf].element_id), 3 + 2 * 64)
        error = self.error(chain(65), "OKL-E-RESOURCE")
        self.assertEqual(error.diagnostic.details["budget"], "ownership_depth")

    def test_work_value_and_encoded_byte_budgets(self):
        text = source(family(), 'object rig @ "rig": Family {}')
        self.error(text, "OKL-E-RESOURCE", budgets={"max_operations": 10})
        self.error(text, "OKL-E-RESOURCE", budgets={"max_value_entries": 10})
        huge = "a" * 18000
        classes = f'''class Leaf @ "leaf" {{ public param text @ "text": String = ""; }}
class Family @ "family" {{
 public param text @ "text": String = "{huge}";
 public parts leaves @ "leaves": Leaf for (k,v) in keyed<Int>{{{','.join(f'"k{i}": {i}' for i in range(256))}}} {{ text = self.text; }}
}}'''
        error = self.error(source(classes, 'object rig @ "rig": Family {}'), "OKL-E-RESOURCE")
        self.assertEqual(error.diagnostic.details["budget"], "encoded_json_bytes")

    def test_check_callback_cancels_real_work(self):
        calls = 0
        class Cancel(Exception):
            pass
        def check():
            nonlocal calls
            calls += 1
            if calls == 50:
                raise Cancel()
        with self.assertRaises(Cancel):
            compile_construction(bundle(source(family(), 'object rig @ "rig": Family {}')), check=check)
        self.assertEqual(calls, 50)


if __name__ == "__main__":
    unittest.main()
