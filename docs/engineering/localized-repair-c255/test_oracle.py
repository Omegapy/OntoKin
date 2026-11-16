#!/usr/bin/env python3
"""Authored inert fault controls; independent review has its own raw-derived fixtures."""
from copy import deepcopy
import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path
import random
import subprocess
import shutil
import ast
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("c255_oracle_under_test", HERE / "oracle.py")
O = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = O
SPEC.loader.exec_module(O)
REPO = HERE.parents[2]


def outward(vertices, triangle):
    a, b, c = [vertices[i] for i in triangle]
    u, v = [b[i]-a[i] for i in range(3)], [c[i]-a[i] for i in range(3)]
    normal = [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]]
    if sum(normal[i]*(a[i]+b[i]+c[i]) for i in range(3)) < 0:
        triangle = [triangle[0], triangle[2], triangle[1]]
    return triangle


def box(size):
    vertices = [list(v) for v in itertools.product(*[(-x/2, x/2) for x in size])]
    triangles = []
    for axis in range(3):
        for sign in (-1, 1):
            face = [i for i, v in enumerate(vertices) if v[axis] == sign * size[axis]/2]
            # Binary corner order gives a perimeter by swapping the last pair.
            a, b, d, c = face
            triangles.extend([outward(vertices, [a, b, c]), outward(vertices, [a, c, d])])
    return vertices, triangles


def sphere(radius):
    vertices = [[0.0, radius, 0.0]]
    for lat in range(1, 16):
        phi = math.pi * lat / 16
        for lon in range(32):
            theta = math.tau * lon / 32
            vertices.append([radius*math.sin(phi)*math.cos(theta), radius*math.cos(phi), radius*math.sin(phi)*math.sin(theta)])
    vertices.append([0.0, -radius, 0.0])
    triangles = []
    for lon in range(32):
        j = (lon+1) % 32
        triangles.append([0, 1+lon, 1+j])
        for lat in range(14):
            a, b, c, d = 1+32*lat+lon, 1+32*lat+j, 1+32*(lat+1)+lon, 1+32*(lat+1)+j
            triangles.extend([[a, b, d], [a, d, c]])
        triangles.append([481, 449+j, 449+lon])
    return vertices, [outward(vertices, t) for t in triangles]


def raw_matrix(position, q):
    # Test fixture uses the axis-angle Rodrigues form, separate from matrix_for.
    norm = math.hypot(*q)
    w, x, y, z = [v/norm for v in q]
    angle = 2*math.atan2(math.hypot(x, y, z), w)
    length = math.hypot(x, y, z)
    axis = [0, 0, 1] if length == 0 else [x/length, y/length, z/length]
    x, y, z = axis
    c, s, v = math.cos(angle), math.sin(angle), 1-math.cos(angle)
    return [c+x*x*v, x*y*v-z*s, x*z*v+y*s, position[0],
            y*x*v+z*s, c+y*y*v, y*z*v-x*s, position[1],
            z*x*v-y*s, z*y*v+x*s, c+z*z*v, position[2], 0, 0, 0, 1]


def origin(state, location):
    return {"artifact": "scene.bin", "sha256": hashlib.sha256(state["artifacts"]["scene.bin"]).hexdigest(), "location": location, "programRevision": state["programRevision"]}


def provenance(state):
    return {"acceptedRevision": state["acceptedRevision"], "programRevision": state["programRevision"],
            "sourceHashes": {k: hashlib.sha256(v).hexdigest() for k, v in state["sourceFiles"].items()},
            "artifactHashes": {k: hashlib.sha256(v).hexdigest() for k, v in state["artifacts"].items()},
            "semanticOrigin": origin(state, "/metadata/semantic")}


def make_case(corpus, case="V1", layer="delivery"):
    # Author fixtures deliberately remain inert. Scientific independence is a
    # separate reviewer obligation and is not claimed for this convenience builder.
    start_key, candidate_key = O.CASE_KEYS[case]
    final_key = start_key if case == "N1" else candidate_key
    def state(key, revision):
        return {"acceptedRevision": revision, "programRevision": O.PROGRAMS[key],
                "sourceFiles": {"main.ok": corpus.sources[key], "hinges.ok": corpus.sources["hinges"]},
                "artifacts": {"scene.bin": ("inert fixture bytes " + key).encode()}}
    start = state(start_key, "accepted-start")
    final = deepcopy(start) if case == "N1" else state(final_key, "accepted-final")
    candidate = {"candidateId": "candidate-1", "parentAcceptedRevision": start["acceptedRevision"],
                 "sourceFiles": {"main.ok": corpus.sources[candidate_key], "hinges.ok": corpus.sources["hinges"]},
                 "artifacts": {} if case == "N1" else deepcopy(final["artifacts"])}
    decision = {"status": "rejected" if case == "N1" else "accepted", "candidateId": "candidate-1",
                "parentAcceptedRevision": "accepted-start", "acceptedRevision": final["acceptedRevision"],
                "boundary": "staged-before-accepted-replacement", "invalidEverAccepted": False,
                "diagnostic": {"code": "incompatible-dimension", "expectedDimension": "length", "receivedDimension": "mass", "mechanism": "compiler", "message": "length cannot receive mass"} if case == "N1" else None}
    authority = {"schema": O.AUTHORITY_SCHEMA, "attemptId": "opaque-control", "caseId": case,
                 "start": start, "candidate": candidate, "retained": final,
                 "rebuild": {"sourceFiles": deepcopy(final["sourceFiles"]), "artifacts": deepcopy(final["artifacts"]), "cleanWorkspace": True, "declaredInputs": ["hinges.ok", "main.ok"], "determinism": "byte-exact"},
                 "decision": decision}
    expected = O.expected_state(corpus, case)
    geometry = []
    for obj in expected["semantic"]["objects"]:
        p = obj["primitive"]
        vertices, triangles = box(p["size_m"]) if p["kind"] == "box" else sphere(p["radius_m"])
        geometry.append({"id": obj["id"], "vertices_m": vertices, "triangles": triangles, "origin": origin(final, "/mesh/" + obj["path"])})
    poses = deepcopy(expected["poses"])
    for row in poses:
        row["matrix"] = raw_matrix(row["position_m"], row["rotation_wxyz"])
        row["origin"] = origin(final, "/nodes/" + "/".join(row["id"]) + "/at/" + str(row["time_s"]))
    observation = {"schema": O.SCHEMA, "attemptId": "opaque-control", "caseId": case, "layer": layer,
                   "semantic": expected["semantic"], "geometry": geometry, "poses": poses,
                   "provenance": provenance(final), "decision": deepcopy(decision)}
    observation["rebuild"] = deepcopy({k: observation[k] for k in ("semantic", "geometry", "poses", "provenance")})
    return observation, authority


def boundary(center, tolerance):
    value = center + tolerance
    while value-center > tolerance:
        value = math.nextafter(value, center)
    while math.nextafter(value, math.inf)-center <= tolerance:
        value = math.nextafter(value, math.inf)
    return value


class OracleControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = O.load_corpus(REPO)
        cls.fixtures = {case: make_case(cls.corpus, case) for case in ("V1", "V2", "N1")}

    def case(self, case="V1"):
        return deepcopy(self.fixtures[case])

    def passes(self, observation, authority, case="V1"):
        result = O.evaluate(self.corpus, case, observation, authority)
        self.assertTrue(result["componentPass"], result)
        self.assertIsNone(result["realTrialSuccess"])
        self.assertFalse(result["executionAllowed"])
        self.assertFalse(result["artifactReaderQualified"])
        self.assertEqual((result["observedObjects"], result["observedPoses"]), (18, 126))

    def rejects(self, observation, authority, case="V1", code=None):
        result = O.evaluate(self.corpus, case, observation, authority)
        self.assertFalse(result["componentPass"], result)
        self.assertTrue(result["faults"])
        if code:
            self.assertEqual(result["faults"][0]["code"], code, result)

    def test_valid_both_directions_and_invalid_retention(self):
        for case in ("V1", "V2", "N1"):
            with self.subTest(case=case): self.passes(*self.case(case), case=case)

    def test_reference_layer_uses_same_independent_family(self):
        obs, auth = self.case(); obs["layer"] = "reference"
        self.passes(obs, auth)

    def test_permuted_records_triangle_and_vertex_order(self):
        obs, auth = self.case()
        rng = random.Random(255)
        for records in (obs, obs["rebuild"]):
            for k in ("objects", "sites", "hinges", "follows", "actions"): rng.shuffle(records["semantic"][k])
            rng.shuffle(records["poses"]); rng.shuffle(records["geometry"])
            for mesh in records["geometry"]:
                rng.shuffle(mesh["triangles"])
                order = list(range(len(mesh["vertices_m"]))); rng.shuffle(order)
                remap = {old: new for new, old in enumerate(order)}
                mesh["vertices_m"] = [mesh["vertices_m"][old] for old in order]
                mesh["triangles"] = [[remap[i] for i in triangle] for triangle in mesh["triangles"]]
        self.passes(obs, auth)

    def test_duplicated_box_face_vertices(self):
        obs, auth = self.case()
        mesh = obs["geometry"][0]
        raw = mesh["vertices_m"]
        mesh["vertices_m"] = [raw[i] for t in mesh["triangles"] for i in t]
        mesh["triangles"] = [[3*i,3*i+1,3*i+2] for i in range(12)]
        self.passes(obs, auth)

    def test_quaternion_sign_equivalence(self):
        obs, auth = self.case()
        for row in obs["poses"] + obs["rebuild"]["poses"]: row["rotation_wxyz"] = [-v for v in row["rotation_wxyz"]]
        self.passes(obs, auth)

    def test_legitimate_revision_and_artifact_changes(self):
        obs, auth = self.case()
        auth["retained"]["acceptedRevision"] = "legitimate-different-record"
        auth["decision"]["acceptedRevision"] = "legitimate-different-record"
        obs["decision"] = deepcopy(auth["decision"])
        new = {"scene.bin": b"different retained artifact bytes with same inert meaning"}
        for name in ("retained", "candidate", "rebuild"): auth[name]["artifacts"] = deepcopy(new)
        for data in (obs, obs["rebuild"]):
            data["provenance"] = provenance(auth["retained"])
            for row in data["geometry"] + data["poses"]:
                row["origin"] = origin(auth["retained"], row["origin"]["location"])
        self.passes(obs, auth)

    def test_inclusive_source_dimension_boundary_and_next_float(self):
        obs, auth = self.case(); row = obs["semantic"]["objects"][4]["primitive"]["size_m"]
        row[0] = boundary(0.75, 1e-12); self.passes(obs, auth)
        row[0] = math.nextafter(row[0], math.inf); self.rejects(obs, auth, code="TOLERANCE")

    def test_pose_position_boundaries_reference_and_delivery(self):
        for layer, tolerance in (("reference",1e-9),("delivery",.001)):
            with self.subTest(layer=layer):
                obs, auth = self.case(); obs["layer"] = layer
                row = obs["poses"][0]
                row["position_m"][1] = tolerance; row["matrix"][7] = tolerance
                self.passes(obs, auth)
                row["position_m"][1] = math.nextafter(tolerance, math.inf)
                self.rejects(obs, auth, code="TOLERANCE")

    def test_time_boundary_and_exact_reference_times(self):
        obs, auth = self.case(); obs["poses"][0]["time_s"] = 1e-6; self.passes(obs, auth)
        obs["poses"][0]["time_s"] = math.nextafter(1e-6, math.inf); self.rejects(obs, auth, code="POSE_TIME")
        obs, auth = self.case(); obs["layer"] = "reference"; obs["poses"][0]["time_s"] = 1e-20
        self.rejects(obs, auth, code="POSE_TIME")

    def test_rotation_boundaries_and_no_raw_secondary_tolerance(self):
        for layer, tolerance in (("reference",1e-9),("delivery",.001)):
            with self.subTest(layer=layer):
                obs, auth = self.case(); obs["layer"] = layer; row = obs["poses"][0]
                q = [math.cos(tolerance/2),0,0,math.sin(tolerance/2)]
                row["rotation_wxyz"] = q; row["matrix"] = raw_matrix(row["position_m"],q)
                self.passes(obs, auth)
                outside = tolerance + (1e-13 if layer == "reference" else 1e-7)
                row["matrix"] = raw_matrix(row["position_m"],[math.cos(outside/2),0,0,math.sin(outside/2)])
                self.rejects(obs, auth, code="RAW_ROTATION")
                row["rotation_wxyz"] = [math.cos(outside/2),0,0,math.sin(outside/2)]
                self.rejects(obs, auth, code="POSE_ROTATION")

    def test_raw_angle_cannot_hide_inside_allowed_matrix_residual(self):
        for layer, angle, outside, stretch in (("delivery", .001, .0010000001, 1.0000005),
                                               ("reference", 1e-9, 1e-9+1e-22, 1.0000000000005)):
            with self.subTest(layer=layer):
                obs, auth = self.case(); obs["layer"] = layer
                row = obs["poses"][0]
                row["rotation_wxyz"] = [math.cos(angle/2),0,0,math.sin(angle/2)]
                row["matrix"] = raw_matrix(row["position_m"], [math.cos(outside/2),0,0,math.sin(outside/2)])
                for i in (0,1,2,4,5,6,8,9,10): row["matrix"][i] *= stretch
                self.rejects(obs,auth,code="RAW_ROTATION")

    def test_blank_and_control_character_artifact_reference(self):
        for value in ("   ", "\t", "native\x00path", "native\x7fpath"):
            with self.subTest(value=value):
                obs,auth=self.case();obs["geometry"][0]["origin"]["location"]=value
                self.rejects(obs,auth,code="ARTIFACT_LOCATION")

    def test_wrong_length_target_global_default_and_sibling(self):
        for index, field, value in [(4,"primitive",{"kind":"box","size_m":[.65,.08,.08]}),(2,"primitive",{"kind":"box","size_m":[.75,.08,.08]}),(0,"parameters",None)]:
            with self.subTest(index=index):
                obs, auth = self.case()
                if value is None:obs["semantic"]["objects"][index][field]["finger_length"]["value"] = .75
                else:obs["semantic"]["objects"][index][field] = value
                self.rejects(obs, auth)

    def test_source_mutations_and_dependency_changes(self):
        for mode in ("global", "sibling", "kg", "pin", "dependency", "missing", "extra"):
            with self.subTest(mode=mode):
                obs, auth = self.case(); files = auth["candidate"]["sourceFiles"]
                if mode == "global":files["main.ok"] = files["main.ok"].replace(b'finger_length @ "finger-length": Length = 0.6[m]', b'finger_length @ "finger-length": Length = 0.75[m]')
                if mode == "sibling":files["main.ok"] = files["main.ok"].replace(b'fingers["middle"].length',b'fingers["upper"].length')
                if mode == "kg":files["main.ok"] = self.corpus.sources["invalid_mass"]
                if mode == "pin":files["main.ok"] = files["main.ok"].replace(b'1516e531',b'00000000')
                if mode == "dependency":files["hinges.ok"] += b'\n'
                if mode == "missing":files.pop("hinges.ok")
                if mode == "extra":files["ambient.ok"] = b'undeclared'
                self.rejects(obs, auth)

    def test_identity_membership_and_full_keys(self):
        for mode in ("missing","extra","duplicate","same_path_new_id","same_id_new_path","definition"):
            with self.subTest(mode=mode):
                obs, auth = self.case(); rows = obs["semantic"]["objects"]
                if mode == "missing":rows.pop()
                if mode == "extra":x=deepcopy(rows[0]);x["id"][-1]="extra";rows.append(x)
                if mode == "duplicate":rows[1]["id"] = rows[0]["id"][:]
                if mode == "same_path_new_id":rows[0]["id"][-1] = "renamed"
                if mode == "same_id_new_path":rows[0]["path"] = "renamed"
                if mode == "definition":rows[1]["definitionId"][-1]="blade"
                self.rejects(obs, auth)

    def test_every_semantic_relationship_collection(self):
        changes = [("objects",0,"owner",["keyed-rack","demo","second"]), ("follows",0,"parentFrame",["keyed-rack","demo","second"]),
                   ("hinges",0,"axis",[1,0,0]), ("hinges",0,"initial_rad",.01), ("hinges",0,"limits_rad",[-1,1]),
                   ("sites",0,"interface","wrong"), ("sites",0,"size_m",1e-20), ("actions",1,"duration_s",1),
                   ("actions",1,"velocity_mps",[0,.3,0])]
        for collection,index,key,value in changes:
            with self.subTest(collection=collection,key=key):
                obs, auth = self.case();obs["semantic"][collection][index][key]=value;self.rejects(obs, auth)
        obs, auth = self.case();obs["semantic"]["events"][0]["operations"].reverse();self.rejects(obs, auth)

    def test_exact_mass_units_material_and_selected_sphere(self):
        for mode in ("tiny_mass","units","frame","material","sphere","selected_position"):
            with self.subTest(mode=mode):
                obs, auth=self.case();s=obs["semantic"]
                if mode=="tiny_mass":s["objects"][0]["matter"]["own_mass_kg"]=1e-30
                if mode=="units":s["objects"][3]["parameters"]["length"]["unit"]="kg"
                if mode=="frame":s["frame"]["up"]="+Z"
                if mode=="material":s["objects"][0]["appearance"][0]=.46
                if mode=="sphere":s["objects"][3]["primitive"]["radius_m"]=.07
                if mode=="selected_position":obs["poses"][3]["position_m"][0]+=.01
                self.rejects(obs,auth)

    def test_geometry_not_metadata(self):
        for mode in ("wrong_size","bounding_box_only","inverted_triangle","duplicate_triangle","missing_vertex","empty","missing_sphere_ring"):
            with self.subTest(mode=mode):
                obs,auth=self.case();g=obs["geometry"][4]
                if mode=="wrong_size":g["vertices_m"]=[[v[0]*2,v[1],v[2]] for v in g["vertices_m"]]
                if mode=="bounding_box_only":g["vertices_m"]=[[-.375,-.04,-.04],[.375,.04,.04]]
                if mode=="inverted_triangle":g["triangles"][0].reverse()
                if mode=="duplicate_triangle":g["triangles"][0]=g["triangles"][1][:]
                if mode=="missing_vertex":g["vertices_m"].pop()
                if mode=="empty":g["triangles"]=[]
                if mode=="missing_sphere_ring":obs["geometry"][3]["vertices_m"][20]=[0,0,0]
                self.rejects(obs,auth)

    def test_pose_inventory_and_wrong_motion(self):
        for mode in ("missing","duplicate","extra","wrong_id","wrong_time","wrong_side","motion"):
            with self.subTest(mode=mode):
                obs,auth=self.case();p=obs["poses"]
                if mode=="missing":p.pop()
                if mode=="duplicate":p[-1]=deepcopy(p[0])
                if mode=="extra":p.append(deepcopy(p[0]))
                if mode=="wrong_id":p[0]["id"][-1]="other"
                if mode=="wrong_time":p[0]["time_s"] =.01
                if mode=="wrong_side":p[0]["side"] ="before"
                if mode=="motion":p[4+18*4]["position_m"][1]=0
                self.rejects(obs,auth)

    def test_nonfinite_boolean_and_zero_quaternion(self):
        for value in (True,float("nan"),float("inf"),-float("inf")):
            for location in ("position","dimension","time","matrix","vertex"):
                with self.subTest(value=value,location=location):
                    obs,auth=self.case()
                    if location=="position":obs["poses"][0]["position_m"][1]=value
                    if location=="dimension":obs["semantic"]["objects"][0]["primitive"]["size_m"][0]=value
                    if location=="time":obs["poses"][0]["time_s"]=value
                    if location=="matrix":obs["poses"][0]["matrix"][0]=value
                    if location=="vertex":obs["geometry"][0]["vertices_m"][0][0]=value
                    self.rejects(obs,auth)
        obs,auth=self.case();obs["poses"][0]["rotation_wxyz"]=[0,0,0,0];self.rejects(obs,auth,code="QUATERNION_NORM")

    def test_raw_scale_shear_reflection_and_decomposition(self):
        for mode in ("scale","shear","reflection","translation","homogeneous","q_norm","explicit_scale"):
            with self.subTest(mode=mode):
                obs,auth=self.case();r=obs["poses"][0]
                if mode=="scale":r["matrix"][0]=1.01
                if mode=="shear":r["matrix"][1]=.01
                if mode=="reflection":r["matrix"][0]=-1
                if mode=="translation":r["matrix"][7]=.01
                if mode=="homogeneous":r["matrix"][15]=2
                if mode=="q_norm":r["rotation_wxyz"]=[2,0,0,0]
                if mode=="explicit_scale":r["scale"]=[1.00001,1,1]
                self.rejects(obs,auth)

    def test_stale_mismatched_and_false_provenance(self):
        for mode in ("parent","accepted","source_hash","artifact_hash","origin_hash","origin_revision","origin_location","fake_acceptance","candidate_bytes"):
            with self.subTest(mode=mode):
                obs,auth=self.case()
                if mode=="parent":auth["candidate"]["parentAcceptedRevision"]="stale"
                if mode=="accepted":obs["provenance"]["acceptedRevision"]="accepted-start"
                if mode=="source_hash":obs["provenance"]["sourceHashes"]["main.ok"]="0"*64
                if mode=="artifact_hash":obs["provenance"]["artifactHashes"]["scene.bin"]="0"*64
                if mode=="origin_hash":obs["poses"][0]["origin"]["sha256"]="0"*64
                if mode=="origin_revision":obs["geometry"][0]["origin"]["programRevision"]=auth["start"]["programRevision"]
                if mode=="origin_location":obs["geometry"][0]["origin"]["location"]=""
                if mode=="fake_acceptance":obs["decision"]["acceptedRevision"]="author-says-accepted"
                if mode=="candidate_bytes":auth["candidate"]["artifacts"]["scene.bin"]+=b'changed'
                self.rejects(obs,auth)

    def test_n1_promotion_and_retained_byte_mutations(self):
        for mode in ("transient","status","source","dependency","artifact","revision","harness_only","fixed_to_metres","boundary","message"):
            with self.subTest(mode=mode):
                obs,auth=self.case("N1")
                if mode=="transient":auth["decision"]["invalidEverAccepted"]=True
                if mode=="status":auth["decision"]["status"]="accepted"
                if mode=="source":auth["retained"]["sourceFiles"]["main.ok"]+=b'\n'
                if mode=="dependency":auth["retained"]["sourceFiles"]["hinges.ok"]+=b'\n'
                if mode=="artifact":auth["retained"]["artifacts"]["scene.bin"]+=b'changed'
                if mode=="revision":auth["retained"]["acceptedRevision"]="new"
                if mode=="harness_only":auth["decision"]["diagnostic"]["mechanism"]="common_harness"
                if mode=="fixed_to_metres":auth["candidate"]["sourceFiles"]["main.ok"]=self.corpus.sources["target_075"]
                if mode=="boundary":auth["decision"]["boundary"]="after-acceptance"
                if mode=="message":auth["decision"]["diagnostic"]["message"]=""
                self.rejects(obs,auth,case="N1")

    def test_rebuild_difference_and_undeclared_input(self):
        for mode in ("source","artifact","semantic","pose","geometry","ambient","dirty","changed_policy"):
            with self.subTest(mode=mode):
                obs,auth=self.case()
                if mode=="source":auth["rebuild"]["sourceFiles"]["main.ok"]+=b'\n'
                if mode=="artifact":auth["rebuild"]["artifacts"]["scene.bin"]+=b'changed'
                if mode=="semantic":obs["rebuild"]["semantic"]["objects"][0]["appearance"][0]=0
                if mode=="pose":obs["rebuild"]["poses"][0]["position_m"][1]=1
                if mode=="geometry":obs["rebuild"]["geometry"][0]["vertices_m"][0][0]=2
                if mode=="ambient":auth["rebuild"]["declaredInputs"].append("ambient.ok")
                if mode=="dirty":auth["rebuild"]["cleanWorkspace"]=False
                if mode=="changed_policy":auth["rebuild"]["determinism"]="normalize-later"
                self.rejects(obs,auth)

    def test_no_tolerance_overrides(self):
        obs,auth=self.case();obs["tolerance"]=100;self.rejects(obs,auth,code="SHAPE")

    def test_no_mutation_of_inputs(self):
        obs,auth=self.case();before=deepcopy((obs,auth));self.passes(obs,auth)
        self.assertEqual((obs,auth),before)

    def test_denominators_retain_all_started_failures(self):
        for case in ("V1","V2","N1"):
            for outcome in ("missing_output","timeout","crash","infrastructure_incident","abstained","budget_exhausted"):
                with self.subTest(case=case,outcome=outcome):
                    r=O.classify_attempt(case,True,True,outcome,True)
                    self.assertFalse(r["inertOutcomePass"])
                    self.assertEqual(r["primaryDenominator"]+r["negativeDenominator"],1)
                    self.assertEqual(r["negativeDenominator"],int(case=="N1"))
            r=O.classify_attempt(case,False,False,"unavailable_before_start")
            self.assertEqual(r["primaryDenominator"]+r["negativeDenominator"],0)
            with self.assertRaises(O.Fault):O.classify_attempt(case,True,True,"unavailable_before_start")
        with self.assertRaises(O.Fault):O.classify_attempt("V1",1,True,"completed")

    def test_frozen_authority_and_coordinated_source_tampering(self):
        manifest = json.loads((REPO / "docs/engineering/localized-repair-c253/corpus.json").read_text())
        paths = set(O.SOURCE_PINS) | {row["path"] for row in manifest["files"].values()}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for relative in paths:
                target = root / relative; target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(REPO / relative, target)
            O.load_corpus(root)
            corpus_path = root / "docs/engineering/localized-repair-c253/corpus.json"
            original = corpus_path.read_bytes()
            changed = deepcopy(manifest)
            changed["oracle"]["originalTolerances"]["delivery_position_component_tolerance_m"] = 1
            corpus_path.write_text(json.dumps(changed))
            with self.assertRaises(O.Fault) as failure: O.load_corpus(root)
            self.assertEqual(failure.exception.code, "CORPUS_AUTHORITY")
            corpus_path.write_bytes(original)
            source = root / manifest["files"]["hinges"]["path"]
            source.write_bytes(source.read_bytes() + b"\n")
            changed = deepcopy(manifest)
            changed["files"]["hinges"]["sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
            changed["files"]["hinges"]["bytes"] += 1
            corpus_path.write_text(json.dumps(changed))
            with self.assertRaises(O.Fault) as failure: O.load_corpus(root)
            self.assertEqual(failure.exception.code, "CORPUS_AUTHORITY")
            corpus_path.write_bytes(original)
            with self.assertRaises(O.Fault) as failure: O.load_corpus(root)
            self.assertEqual(failure.exception.code, "CORPUS_SOURCE")

    def test_imports_remain_standard_library_and_no_execution_primitives(self):
        tree = ast.parse((HERE / "oracle.py").read_text())
        modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import): modules.update(x.name.split(".")[0] for x in node.names)
            if isinstance(node, ast.ImportFrom): modules.add(node.module.split(".")[0])
        self.assertTrue(modules <= set(sys.stdlib_module_names), modules)
        self.assertFalse(modules & {"ontokin", "subprocess", "socket", "ctypes", "multiprocessing"})

    def test_duplicate_json_and_nonfinite_transport(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"bad.json"
            for content in ('{"a":1,"a":2}','{"a":NaN}'):
                p.write_text(content)
                with self.assertRaises(O.Fault):O.read_json(p)

    def test_cli_positive_and_malformed_envelope(self):
        obs,auth=self.case()
        for state in ("start","candidate","retained","rebuild"):
            for field in ("sourceFiles","artifacts"):
                auth[state][field]={k:{"encoding":"hex","data":v.hex()} for k,v in auth[state][field].items()}
        with tempfile.TemporaryDirectory() as tmp:
            op,ap=Path(tmp)/"observation.json",Path(tmp)/"authority.json"
            op.write_text(json.dumps(obs));ap.write_text(json.dumps(auth))
            args=[sys.executable,"-IB",str(HERE/"oracle.py"),"--repo",str(REPO),"--case","V1","--observation",str(op),"--authority",str(ap)]
            r=subprocess.run(args,capture_output=True,text=True,check=False)
            self.assertEqual(r.returncode,0,r.stdout+r.stderr)
            self.assertTrue(json.loads(r.stdout)["componentPass"])
            auth["candidate"]["sourceFiles"]["main.ok"]["data"]="GG";ap.write_text(json.dumps(auth))
            r=subprocess.run(args,capture_output=True,text=True,check=False)
            self.assertEqual(r.returncode,1)
            self.assertFalse(json.loads(r.stdout)["componentPass"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
