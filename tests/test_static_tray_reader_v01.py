"""Synthetic controls for the independent reader; no native qualification claim.

The mesh fixture uses hand-derived side tables, explicit face winding, and
direct GLB encoding. It imports no producer, compiler, constructor or helper.
"""

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


READER=Path(__file__).resolve().parents[1]/"tools"/"static_tray_reader_v01"
sys.path.insert(0,str(READER))
from corrupt import corrupt
from expected import expected_bounds, expected_case
from glb import MAX_RESULT, InvalidGLB, accessor, pack, parse
from reader import audit


PARTS=("back","base","front","left-wall","payload","right-wall")
FACES=(
    ((-1,0,0),((-1,-1,-1),(-1,-1,1),(-1,1,1),(-1,1,-1))),
    ((1,0,0),((1,-1,1),(1,-1,-1),(1,1,-1),(1,1,1))),
    ((0,-1,0),((-1,-1,1),(-1,-1,-1),(1,-1,-1),(1,-1,1))),
    ((0,1,0),((-1,1,-1),(-1,1,1),(1,1,1),(1,1,-1))),
    ((0,0,-1),((1,-1,-1),(-1,-1,-1),(-1,1,-1),(1,1,-1))),
    ((0,0,1),((-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1))),
)


def frozen_rules():
    """Hand-transcribed delivery declarations; no producer configuration import."""
    names=[]
    meshes=[]
    for side in ("left","right"):
        root="equipment-tray/pair/"+side
        names.extend([root+"/"+part for part in PARTS]+[root])
        meshes.extend(root+"/"+part+"/mesh" for part in PARTS)
    return {
        "schema":"ontokin.static-tray.delivery-rules/0.1.0",
        "node_order":names,"mesh_order":meshes,"scene_nodes":[6,13],
        "material_order":["tray","payload"],"nodes":14,"meshes":12,
        "primitives_per_mesh":1,"primitive_attributes":["NORMAL","POSITION"],
        "position_component_type":5126,"position_type":"VEC3",
        "normal_component_type":5126,"normal_type":"VEC3",
        "index_component_type":5123,"index_type":"SCALAR",
        "vertices_per_mesh":24,"triangles_per_mesh":12,
        "metallic":0.0,"roughness":0.75,"alpha_mode":"OPAQUE","double_sided":False,
        "buffer_storage":"Pinned exporter deterministic uncompressed internal storage; shared identical buffers allowed and resolved by reader",
        "raw_to_final":"Exact byte copy; no projection, metadata stripping, quantization or volatile exclusions",
        "nonsemantic_metadata":{
            "asset_generator":"Khronos glTF Blender I/O v4.5.48","scene_name":"StaticTray",
            "buffer_name_fields":"forbidden","buffer_view_name_fields":"forbidden",
            "accessor_name_fields":"forbidden"},
    }


def source_table(case,side):
    if case=="Q02":
        if side=="left":
            return {
                "base":((.014,.001,.014),(0,-.0005,0)),
                "back":((.014,.011,.001),(0,.0055,-.0065)),
                "front":((.014,.011,.001),(0,.0055,.0065)),
                "left-wall":((.001,.011,.012),(-.0065,.0055,0)),
                "right-wall":((.001,.011,.012),(.0065,.0055,0)),
                "payload":((.01,.01,.01),(0,.005,0)),
            }
        return {
            "base":((1.15,.025,1.15),(0,-.0125,0)),
            "back":((1.15,.6,.025),(0,.3,-.5625)),
            "front":((1.15,.6,.025),(0,.3,.5625)),
            "left-wall":((.025,.6,1.1),(-.5625,.3,0)),
            "right-wall":((.025,.6,1.1),(.5625,.3,0)),
            "payload":((1,.5,1),(0,.25,0)),
        }
    if side=="right":
        return {
            "base":((.178,.006,.118),(0,-.003,0)),
            "back":((.178,.06,.004),(0,.03,-.057)),
            "front":((.178,.06,.004),(0,.03,.057)),
            "left-wall":((.004,.06,.110),(-.087,.03,0)),
            "right-wall":((.004,.06,.110),(.087,.03,0)),
            "payload":((.16,.04,.10),(0,.02,0)),
        }
    width,outer,xoffset={"Q01":(.20,.218,.107),"Q03":(.20,.218,.107),
                         "Q04":(.24,.258,.127),"Q05":(.18,.198,.097)}[case]
    return {
        "base":((outer,.006,.138),(0,-.003,0)),
        "back":((outer,.08,.004),(0,.04,-.067)),
        "front":((outer,.08,.004),(0,.04,.067)),
        "left-wall":((.004,.08,.130),(-xoffset,.04,0)),
        "right-wall":((.004,.08,.130),(xoffset,.04,0)),
        "payload":((width,.06,.12),(0,.03,0)),
    }


def synthetic(case="Q01",strided=False,metadata="frozen"):
    # The fixed exporter string is test data, not evidence that Blender ran.
    doc={"asset":{"version":"2.0","generator":"Khronos glTF Blender I/O v4.5.48"},
         "scene":0,"scenes":[{"nodes":[6,13],"name":"StaticTray"}],"nodes":[],"meshes":[],
         "materials":[],"accessors":[],"bufferViews":[],"buffers":[{"byteLength":0}]}
    if metadata=="historical-synthetic":
        doc["asset"]["generator"]="Independent synthetic reader control"
        del doc["scenes"][0]["name"]
    elif metadata!="frozen":
        raise ValueError("Unknown synthetic metadata fixture")
    binary=bytearray()
    for name,color in (("tray",[.25,.5,.75,1]),("payload",[.75,.5,.25,1])):
        doc["materials"].append({"name":name,"pbrMetallicRoughness":{
            "baseColorFactor":color,"metallicFactor":0,"roughnessFactor":.75},
            "alphaMode":"OPAQUE","doubleSided":False})
    def add(values,kind):
        binary.extend(b"\0"*((-len(binary))%4))
        offset=len(binary)
        if kind!="indices":
            binary.extend(b"\0"*4)
        for v in values:
            binary.extend(struct.pack("<H",v) if kind=="indices" else struct.pack("<fff",*v))
            if strided and kind!="indices":
                binary.extend(b"test")
        view={"buffer":0,"byteOffset":offset,"byteLength":len(binary)-offset,
              "target":34963 if kind=="indices" else 34962}
        if strided and kind!="indices":
            view["byteStride"]=16
        doc["bufferViews"].append(view)
        a={"bufferView":len(doc["bufferViews"])-1,"componentType":5123 if kind=="indices" else 5126,
           "count":len(values),"type":"SCALAR" if kind=="indices" else "VEC3"}
        if kind!="indices":
            a["byteOffset"]=4
        if kind=="POSITION":
            rounded=[struct.unpack("<fff",struct.pack("<fff",*v)) for v in values]
            a["min"]=[min(v[i] for v in rounded) for i in range(3)]
            a["max"]=[max(v[i] for v in rounded) for i in range(3)]
        doc["accessors"].append(a)
        return len(doc["accessors"])-1
    for side in ("left","right"):
        identity=["equipment-tray","pair",side]
        rootname="/".join(identity)
        child_ids=[]
        for part in PARTS:
            size,offset=source_table(case,side)[part]
            vertices,normals,indices=[],[],[]
            for normal,corners in FACES:
                first=len(vertices)
                vertices.extend(tuple(c[i]*size[i]/2 for i in range(3)) for c in corners)
                normals.extend([normal]*4)
                indices.extend([first,first+1,first+2,first,first+2,first+3])
            p,n,i=add(vertices,"POSITION"),add(normals,"NORMAL"),add(indices,"indices")
            name=rootname+"/"+part
            doc["meshes"].append({"name":name+"/mesh","primitives":[{
                "attributes":{"POSITION":p,"NORMAL":n},"indices":i,
                "material":int(part=="payload"),"mode":4}]})
            child_ids.append(len(doc["nodes"]))
            doc["nodes"].append({"name":name,"mesh":len(doc["meshes"])-1,"translation":list(offset),
                                 "extras":{"semantic_id":identity+[part],
                                           "role":"payload-proxy" if part=="payload" else part,
                                           "owner_id":identity,"follow_id":identity+["follow-"+part],
                                           "follow_parent_id":identity}})
        if case=="Q02":
            translation=[-10]*3 if side=="left" else [10]*3
            quaternion=[0,0,0,1]
        elif case=="Q03":
            translation=[-.3,.2,.1] if side=="left" else [.3,.1,-.2]
            quaternion=[.5,.5,.5,.5] if side=="left" else [.5,-.5,.5,.5]
        else:
            translation=[-.3 if side=="left" else .3,0,0]
            quaternion=[0,0,0,1]
        doc["nodes"].append({"name":rootname,"children":child_ids,"translation":translation,
                             "rotation":quaternion,"extras":{"semantic_id":identity,"role":"tray-root",
                                                                    "owner_id":["equipment-tray","pair"]}})
    doc["buffers"][0]["byteLength"]=len(binary)
    return pack(doc,binary)


class StaticTrayReaderTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.path=self.root/"source.glb"
        self.path.write_bytes(synthetic())

    def tearDown(self):
        self.temp.cleanup()

    def classes(self,result):
        return {x["classification"] for x in result["findings"]}

    def test_hand_derived_baseline_measurements(self):
        result=audit(self.path)
        self.assertTrue(result["passed"],result["findings"])
        measured={("/".join(x["semantic_id"]),x["name"]):x for x in result["measurements"]}
        for side,width,depth,height in (("left",.210,.130,.080),("right",.170,.110,.060)):
            name="equipment-tray/pair/"+side
            for label,wanted in (("cavity_width_m",width),("cavity_depth_m",depth),("cavity_height_m",height)):
                self.assertEqual(measured[(name,label)]["expected"],wanted)
                self.assertLess(abs(measured[(name,label)]["measured"]-wanted),.000005)
        self.assertEqual(len(result["nodes"]),14)
        self.assertEqual(len(result["right_closure"]),7)

    def test_all_frozen_geometry_controls(self):
        baseline=audit(self.path)
        for case in ("Q01","Q02","Q03","Q04","Q05"):
            with self.subTest(case=case):
                path=self.root/(case+".glb")
                path.write_bytes(synthetic(case))
                result=audit(path,case,baseline if case in ("Q04","Q05") else None,delivery_rules=frozen_rules())
                self.assertTrue(result["passed"],result["findings"])

    def test_bounded_offset_and_stride_decoding(self):
        self.path.write_bytes(synthetic(strided=True))
        result=audit(self.path)
        self.assertTrue(result["passed"],result["findings"])

    def test_uint16_indices_allow_component_aligned_two_byte_offset(self):
        doc,binary=parse(self.path.read_bytes())
        binary=bytearray(binary)
        primitive=doc["meshes"][0]["primitives"][0]
        indices,_=accessor(doc,binary,primitive["indices"],"indices")
        binary.extend(b"\0\0")
        offset=len(binary)
        binary.extend(struct.pack("<"+"H"*len(indices),*indices))
        view={"buffer":0,"byteOffset":offset,"byteLength":2*len(indices),"target":34963}
        doc["bufferViews"].append(view)
        doc["accessors"].append({"bufferView":len(doc["bufferViews"])-1,"componentType":5123,
                                 "count":len(indices),"type":"SCALAR"})
        primitive["indices"]=len(doc["accessors"])-1
        doc["buffers"][0]["byteLength"]=len(binary)
        self.path.write_bytes(pack(doc,binary))
        result=audit(self.path)
        self.assertTrue(result["passed"],result["findings"])

    def test_delivered_corruption_findings_and_input_preservation(self):
        original=self.path.read_bytes()
        baseline=audit(self.path)
        for case,wanted in (("D01","CLEARANCE"),("D02","IDENTITY"),("D03","SIBLING"),
                            ("D04","TOPOLOGY"),("D05","FRAME"),("D06","IDENTITY"),
                            ("D07","UNSUPPORTED")):
            with self.subTest(case=case):
                source=self.path
                expect="Q01"
                if case=="D05":
                    source=self.root/"composition.glb"
                    source.write_bytes(synthetic("Q03"))
                    expect="Q03"
                output=self.root/(case+".glb")
                mutation=corrupt(case,source,output)
                result=audit(output,expect,baseline if case in ("D02","D03") else None,delivery_rules=frozen_rules())
                self.assertFalse(result["passed"])
                self.assertIn(wanted,self.classes(result),result["findings"])
                self.assertTrue(mutation["changed_ranges"])
                self.assertTrue(mutation["input_preserved"])
                self.assertNotIn("STRUCTURE",self.classes(result))
                if case=="D02":
                    self.assertEqual(sum(k.startswith("equipment-tray/pair/left") for k in result["nodes"]),7)
        self.assertEqual(self.path.read_bytes(),original)

    def test_d08_copy_and_reordered_json(self):
        baseline=audit(self.path)
        for variant in ("copy","reordered"):
            output=self.root/(variant+".glb")
            mutation=corrupt("D08",self.path,output,variant)
            result=audit(output,baseline_right=baseline,delivery_rules=frozen_rules())
            self.assertTrue(result["passed"],result["findings"])
            self.assertEqual(mutation["input_sha256"]==mutation["output_sha256"],variant=="copy")
            self.assertEqual(result["right_closure"],baseline["right_closure"])

    def test_sibling_baseline_is_required_for_scoped_repair(self):
        self.path.write_bytes(synthetic("Q04"))
        result=audit(self.path,"Q04")
        self.assertFalse(result["passed"])
        self.assertIn("SIBLING",self.classes(result))

    def test_exact_identity_rejects_global_hash_and_unknown_metadata(self):
        doc,binary=parse(self.path.read_bytes())
        doc["nodes"][6]["extras"]["record_hash"]="sha256:"+"0"*64
        self.path.write_bytes(pack(doc,binary))
        self.assertIn("IDENTITY",self.classes(audit(self.path)))

    def test_position_data_overrides_falsified_accessor_bounds(self):
        output=self.root/"wide.glb"
        corrupt("D01",self.path,output)
        doc,binary=parse(output.read_bytes())
        node=next(n for n in doc["nodes"] if n["name"].endswith("left/payload"))
        ai=doc["meshes"][node["mesh"]]["primitives"][0]["attributes"]["POSITION"]
        doc["accessors"][ai]["min"]=[-.1,-.03,-.06]
        doc["accessors"][ai]["max"]=[.1,.03,.06]
        output.write_bytes(pack(doc,binary))
        result=audit(output)
        self.assertIn("CLEARANCE",self.classes(result))

    def test_topology_rejects_inverted_duplicate_and_interior_triangles(self):
        for variant in ("inverted","duplicate","interior"):
            doc,binary=parse(self.path.read_bytes())
            binary=bytearray(binary)
            primitive=doc["meshes"][1]["primitives"][0]
            values,info=accessor(doc,binary,primitive["indices"],"indices")
            if variant=="inverted":
                values[0],values[1]=values[1],values[0]
            elif variant=="duplicate":
                values[3:6]=values[0:3]
            else:
                values[0:3]=[0,8,16]
            for v,offset in zip(values,info["offsets"]):
                struct.pack_into("<H",binary,offset,v)
            target=self.root/(variant+".glb")
            target.write_bytes(pack(doc,binary))
            with self.subTest(variant=variant):
                self.assertIn("TOPOLOGY",self.classes(audit(target)))

    def test_structural_negative_controls(self):
        original=self.path.read_bytes()
        variants={}
        variants["header"]=b"BAD!"+original[4:]
        variants["truncated"]=original[:-1]
        doc,binary=parse(original)
        external=deepcopy(doc)
        external["buffers"][0]["uri"]="https://example.invalid/never-fetch"
        variants["external"]=pack(external,binary)
        sparse=deepcopy(doc)
        sparse["accessors"][0]["sparse"]={"count":1}
        variants["sparse"]=pack(sparse,binary)
        outofbounds=deepcopy(doc)
        outofbounds["accessors"][0]["byteOffset"]=8000000
        variants["bounds"]=pack(outofbounds,binary)
        cycle=deepcopy(doc)
        cycle["nodes"][0]["children"]=[6]
        variants["cycle"]=pack(cycle,binary)
        unused=deepcopy(doc)
        unused["accessors"].append({"componentType":5126,"count":1,"type":"VEC3",
                                     "sparse":{"count":1}})
        variants["unused_sparse"]=pack(unused,binary)
        badmaterial=deepcopy(doc)
        badmaterial["materials"][0]=[]
        variants["material_type"]=pack(badmaterial,binary)
        nonunit=deepcopy(doc)
        nonunit["nodes"][6]["rotation"]=[0,0,0,0]
        variants["nonunit_quaternion"]=pack(nonunit,binary)
        for name,data in variants.items():
            target=self.root/(name+".glb")
            target.write_bytes(data)
            with self.subTest(name=name):
                self.assertFalse(audit(target)["passed"])

    def test_strict_json_duplicate_and_nonfinite_members(self):
        data=self.path.read_bytes()
        jlength=struct.unpack_from("<I",data,12)[0]
        jsonbytes=data[20:20+jlength].rstrip(b" ")
        binarychunk=data[20+jlength:]
        for extra in (b'"scene":0,',b'"illegal":NaN,'):
            modified=b'{'+extra+jsonbytes[1:]
            modified+=b' '*((-len(modified))%4)
            output=(struct.pack("<III",0x46546c67,2,20+len(modified)+len(binarychunk))+
                    struct.pack("<II",len(modified),0x4e4f534a)+modified+binarychunk)
            target=self.root/("duplicate.glb" if extra.startswith(b'"scene') else "nan.glb")
            target.write_bytes(output)
            self.assertIn("STRUCTURE",self.classes(audit(target)))

    def test_material_values_are_fixed(self):
        doc,binary=parse(self.path.read_bytes())
        doc["materials"][0]["pbrMetallicRoughness"]["roughnessFactor"]=.7
        self.path.write_bytes(pack(doc,binary))
        self.assertIn("MATERIAL",self.classes(audit(self.path)))

    def test_delivery_declarations_are_complete_known_and_fixed(self):
        rules=frozen_rules()
        result=audit(self.path,delivery_rules=rules)
        self.assertTrue(result["passed"],result["findings"])
        for key,value in rules.items():
            changed=deepcopy(rules)
            if type(value) is bool:
                changed[key]=not value
            elif type(value) in (int,float):
                changed[key]=value+1
            elif type(value) is str:
                changed[key]=value+" changed"
            else:
                changed[key]=list(reversed(value))
            with self.subTest(rule=key):
                self.assertIn("LAYOUT",self.classes(audit(self.path,delivery_rules=changed)))
        variants=[{},[],{**rules,"unknown_constraint":True}]
        for key in rules:
            changed=deepcopy(rules)
            del changed[key]
            variants.append(changed)
        changed=deepcopy(rules)
        changed["scene_nodes"]=[6.0,13.0]
        variants.append(changed)
        changed=deepcopy(rules)
        changed["metallic"]=False
        variants.append(changed)
        for rules in variants:
            self.assertIn("LAYOUT",self.classes(audit(self.path,delivery_rules=rules)))

    def test_geometry_equivalent_layout_changes_are_detected(self):
        source=self.path.read_bytes()
        for kind in ("nodes","meshes","materials","uint8_indices","triangle_vertices"):
            doc,binary=parse(source)
            binary=bytearray(binary)
            if kind=="nodes":
                doc["nodes"]=list(reversed(doc["nodes"]))
                for node in doc["nodes"]:
                    if "children" in node:
                        node["children"]=[13-i for i in node["children"]]
                doc["scenes"][0]["nodes"]=[13-i for i in doc["scenes"][0]["nodes"]]
            elif kind=="meshes":
                doc["meshes"][0],doc["meshes"][1]=doc["meshes"][1],doc["meshes"][0]
                for node in doc["nodes"]:
                    if node.get("mesh") in (0,1):
                        node["mesh"]=1-node["mesh"]
            elif kind=="materials":
                doc["materials"].reverse()
                for mesh in doc["meshes"]:
                    mesh["primitives"][0]["material"]=1-mesh["primitives"][0]["material"]
            else:
                primitive=doc["meshes"][0]["primitives"][0]
                indices,_=accessor(doc,binary,primitive["indices"],"indices")
                def add(values,typ,components):
                    binary.extend(b"\0"*((-len(binary))%4))
                    start=len(binary)
                    fmt={5121:"B",5123:"H",5126:"f"}[typ]
                    for value in values:
                        row=(value,) if components==1 else value
                        binary.extend(struct.pack("<"+fmt*components,*row))
                    doc["bufferViews"].append({"buffer":0,"byteOffset":start,"byteLength":len(binary)-start})
                    doc["accessors"].append({"bufferView":len(doc["bufferViews"])-1,"componentType":typ,
                        "count":len(values),"type":"SCALAR" if components==1 else "VEC3"})
                    return len(doc["accessors"])-1
                if kind=="uint8_indices":
                    primitive["indices"]=add(indices,5121,1)
                else:
                    for attribute in ("POSITION","NORMAL"):
                        values,_=accessor(doc,binary,primitive["attributes"][attribute],attribute)
                        primitive["attributes"][attribute]=add([values[i] for i in indices],5126,3)
                    primitive["indices"]=add(list(range(len(indices))),5123,1)
                doc["buffers"][0]["byteLength"]=len(binary)
            target=self.root/(kind+".glb")
            target.write_bytes(pack(doc,binary))
            with self.subTest(layout=kind):
                measured=audit(target)
                self.assertTrue(measured["passed"],measured["findings"])
                frozen=audit(target,delivery_rules=frozen_rules())
                self.assertFalse(frozen["passed"])
                self.assertEqual(self.classes(frozen),{"LAYOUT"},frozen["findings"])

    def test_nonsemantic_metadata_cannot_embed_provenance(self):
        for place in ("generator","scene","buffer","view","accessor","unused-accessor"):
            for value in ("whole_record_sha256="+"a"*64+"; route=python","arbitrary label"):
                doc,binary=parse(self.path.read_bytes())
                if place=="generator":
                    doc["asset"]["generator"]=value
                elif place=="scene":
                    doc["scenes"][0]["name"]=value
                elif place=="buffer":
                    doc["buffers"][0]["name"]=value
                elif place=="view":
                    doc["bufferViews"][0]["name"]=value
                elif place=="accessor":
                    doc["accessors"][0]["name"]=value
                else:
                    doc["accessors"].append({**doc["accessors"][0],"name":value})
                target=self.root/(place+".glb")
                target.write_bytes(pack(doc,binary))
                for rules in (None,frozen_rules()):
                    with self.subTest(place=place,value=value,rules=rules is not None):
                        result=audit(target,delivery_rules=rules)
                        self.assertIn("UNSUPPORTED",self.classes(result))
                        self.assertNotIn("STRUCTURE",self.classes(result))
                        self.assertEqual(len(result["nodes"]),14)
                        self.assertTrue(result["measurements"])
        for key in frozen_rules()["nonsemantic_metadata"]:
            rules=frozen_rules()
            rules["nonsemantic_metadata"][key]="weakened"
            self.assertIn("LAYOUT",self.classes(audit(self.path,delivery_rules=rules)))

    def test_historical_synthetic_metadata_is_measurement_only(self):
        self.path.write_bytes(synthetic(metadata="historical-synthetic"))
        measured=audit(self.path)
        self.assertTrue(measured["passed"],measured["findings"])
        frozen=audit(self.path,delivery_rules=frozen_rules())
        self.assertEqual(self.classes(frozen),{"LAYOUT"})

    def test_exact_lock_and_isolated_cli(self):
        files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in READER.glob("*.py")}
        lock=self.root/"lock.json"
        lock.write_text(json.dumps({"independent_reader":{"files":files,"delivery_rules":frozen_rules()}}))
        result=self.root/"result.json"
        cmd=[sys.executable,"-IB",str(READER/"audit.py"),"--artifact",str(self.path),
             "--expected","Q01","--lock",str(lock),"--result",str(result)]
        run=subprocess.run(cmd,capture_output=True,text=True,timeout=30)
        self.assertEqual(run.returncode,0,run.stderr+run.stdout)
        self.assertTrue(json.loads(result.read_text())["passed"])
        value=json.loads(lock.read_text())
        value["independent_reader"]["files"]["reader.py"]="0"*64
        lock.write_text(json.dumps(value))
        blocked=subprocess.run(cmd,capture_output=True,text=True,timeout=30)
        self.assertEqual(blocked.returncode,2)
        self.assertIn("lock mismatch",blocked.stderr)

    def test_entry_scripts_reject_unbound_bytecode_before_helper_import(self):
        for script in ("audit.py","corrupt.py"):
            for cache in ("__pycache__","glb.pyc","legacy.pyo"):
                directory=self.root/(script+"-"+cache)
                directory.mkdir()
                for file in READER.glob("*.py"):
                    (directory/file.name).write_bytes(file.read_bytes())
                # A cache failure must happen before this helper can execute.
                (directory/"glb.py").write_text('raise RuntimeError("helper was imported")\n')
                if cache=="__pycache__":
                    (directory/cache).mkdir()
                else:
                    (directory/cache).write_bytes(b"synthetic unbound bytecode")
                run=subprocess.run([sys.executable,"-IB",str(directory/script),"--help"],
                                   capture_output=True,text=True,timeout=30)
                with self.subTest(script=script,cache=cache):
                    self.assertNotEqual(run.returncode,0)
                    self.assertIn("Unbound independent reader bytecode",run.stderr)
                    self.assertNotIn("helper was imported",run.stderr)

    def test_auxiliary_json_paths_are_bounded_regular_files(self):
        baseline=audit(self.path)
        fixture_path=self.root/"expected.json"
        baseline_path=self.root/"baseline.json"
        fixture_path.write_text(json.dumps(expected_case("Q01")))
        baseline_path.write_text(json.dumps(baseline))
        original=Path.read_bytes
        def no_unbounded_auxiliary_read(path):
            if path in (fixture_path,baseline_path):
                raise AssertionError("Auxiliary JSON attempted an unbounded read")
            return original(path)
        with patch.object(Path,"read_bytes",no_unbounded_auxiliary_read):
            result=audit(self.path,str(fixture_path),str(baseline_path))
        self.assertTrue(result["passed"],result["findings"])
        for auxiliary in (fixture_path,baseline_path):
            before=auxiliary.read_bytes()
            auxiliary.write_bytes(b" "*(MAX_RESULT+1))
            result=audit(self.path,str(fixture_path),str(baseline_path))
            self.assertIn("RESOURCE",self.classes(result))
            auxiliary.write_bytes(before)
        link=self.root/"baseline-link.json"
        link.symlink_to(baseline_path)
        self.assertIn("BINDING",self.classes(audit(self.path,baseline_right=link)))

    def test_camera_bounds_come_from_independent_intent(self):
        self.assertEqual(expected_bounds("Q01"),[[-.409,-.006,-.069],[.389,.08,.069]])

    def test_corruption_never_overwrites_an_existing_output(self):
        with self.assertRaises(ValueError):
            corrupt("D01",self.path,self.path)


if __name__=="__main__":
    unittest.main()
