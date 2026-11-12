"""Independent C210 finite semantic-export controls; no source/artifact writes."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import platform
from pathlib import Path
import subprocess
import sys
import traceback

from independent_glb import decode, objects, geometry, animation, canonical, sha

def run(repo: Path, proof: Path, output: Path):
    sys.path.insert(0, str(repo))
    from ontokin.bundle import load_bundle
    from ontokin.semantic_export import build_semantic_manifest, verify_semantic_manifest, SemanticExportError
    from ontokin.diagnostics import OntoKinError
    from ontokin.construction import compile_construction
    from ontokin.gltf import export_glb
    from ontokin.scene import ExportOptions

    checks=[]
    def check(name, condition, **detail):
        checks.append({"name":name,"passed":bool(condition),"observed":detail})
    def rejects(name, fn, *, codes=None):
        try:
            fn()
        except Exception as exc:
            code=getattr(exc,"code",None)
            if code is None and hasattr(exc,"diagnostic"):
                code=exc.diagnostic.code
            check(name, isinstance(exc,(SemanticExportError,OntoKinError)) and (codes is None or code in codes), error_type=type(exc).__name__,code=code,message=str(exc))
        else:
            check(name,False,error="accepted unexpectedly")
    read=lambda label, suffix:json.loads((proof/(label+"."+suffix+".json")).read_text())
    before_bundle=load_bundle(read("before","program.bundle"))
    after_bundle=load_bundle(read("after","program.bundle"))
    before=read("before","semantic")
    after=read("after","semantic")
    before_bytes,before_doc,before_bin=decode(proof/"before.glb")
    after_bytes,after_doc,after_bin=decode(proof/"after.glb")
    oracle=json.loads((repo/"docs/language-design/construction-v0.1/01-keyed-rack/expected.json").read_text())
    expected_payload=json.loads((repo/"docs/language-design/construction-v0.1/01-keyed-rack/program.bundle.json").read_text())

    check("after equals frozen source bundle",after_bundle.to_payload()==expected_payload)
    check("one exact supported source replacement",before_bundle.entry.raw.replace(b"0.65[m]",b"0.75[m]")==after_bundle.entry.raw and before_bundle.entry.raw.count(b"0.65[m]")==1)
    check("dependency bytes unchanged",[(u.source_id,u.raw) for u in before_bundle.modules]==[(u.source_id,u.raw) for u in after_bundle.modules])
    check("source revisions change without dependency relabeling",before_bundle.program_revision!=after_bundle.program_revision and before_bundle.entry.revision!=after_bundle.entry.revision and [u.revision for u in before_bundle.modules]==[u.revision for u in after_bundle.modules])
    check("each sidecar verifies its actual inputs",all(verify_semantic_manifest(m,b,g,accepted_program_revision=b.program_revision)["status"]=="passed" for m,b,g in [(before,before_bundle,before_bytes),(after,after_bundle,after_bytes)]))

    a_objects,b_objects=objects(before_doc),objects(after_doc)
    expected={tuple(o["element_id"]):o for o in oracle["objects"]}
    check("18 stable identities match frozen independent oracle",len(a_objects)==18 and set(a_objects)==set(b_objects)==set(expected))
    check("ownership remains separate from root transforms",all("children" not in node for _,node,_ in b_objects.values()) and after_doc["scenes"][after_doc["scene"]]["nodes"]==list(range(len(after_doc["nodes"]))) and all(metadata["owner"]==expected[identity]["owner"] for identity,(_,node,metadata) in b_objects.items()))
    geometry_changes=[]; animation_changes=[]; geometry_errors=[]; material_changes=[]
    for identity in sorted(a_objects):
        ai,an,am=a_objects[identity];bi,bn,bm=b_objects[identity]
        ag=geometry(before_doc,before_bin,an);bg=geometry(after_doc,after_bin,bn)
        if ag["geometry_sha256"]!=bg["geometry_sha256"]: geometry_changes.append(bm["path"])
        if animation(before_doc,before_bin,ai)!=animation(after_doc,after_bin,bi): animation_changes.append(bm["path"])
        if [p["material"] for p in ag["primitives"]]!=[p["material"] for p in bg["primitives"]]: material_changes.append(bm["path"])
        want=expected[identity]["geometry"]
        bounds=bg["primitives"][0]["position_bounds"]
        full=[hi-lo for lo,hi in bounds]
        dimensions=want["size_m"] if want["kind"]=="box" else [2*want["radius_m"]]*3
        geometry_errors.append(max(abs(x-y) for x,y in zip(full,dimensions)))
        check("source identity and no-body declaration "+bm["path"],bm["source_mapping"]["definition_id"]==expected[identity]["definition_id"] and bm["physical"]=={"kind":"no_body"})
    check("only selected blade geometry changes",geometry_changes==['first.fingers["middle"].blade'],changed=geometry_changes)
    check("only selected blade recorded motion changes",animation_changes==['first.fingers["middle"].blade'],changed=animation_changes)
    check("all materials stay unchanged",not material_changes,changed=material_changes)
    check("decoded dimensions match independent frozen oracle",max(geometry_errors)<=2e-7,objects=len(geometry_errors),maximum_full_dimension_error_m=max(geometry_errors))

    before_records={tuple(o["element_id"]):o for o in before["objects"]}
    after_records={tuple(o["element_id"]):o for o in after["objects"]}
    semantic=lambda record:{k:v for k,v in record.items() if k not in ("provenance","geometry_binding","motion_binding")}
    changes=[after_records[k]["path"] for k in sorted(before_records) if semantic(before_records[k])!=semantic(after_records[k])]
    check("exactly two parameter-affected semantic records",changes==['first.fingers["middle"]','first.fingers["middle"].blade'],changed=changes)
    siblings=[k for k,v in after_records.items() if v["path"]=="second" or v["path"].startswith("second.")]
    check("all 11 sibling objects preserve meaning and geometry",len(siblings)==11 and all(semantic(before_records[k])==semantic(after_records[k]) and geometry(before_doc,before_bin,a_objects[k][1])==geometry(after_doc,after_bin,b_objects[k][1]) and animation(before_doc,before_bin,a_objects[k][0])==animation(after_doc,after_bin,b_objects[k][0]) for k in siblings),sibling_objects=len(siblings))
    stripped=lambda records:{r["path"]:{k:v for k,v in r.items() if k!="source_location"} for r in records}
    a_sites,b_sites=stripped(before["sites"]),stripped(after["sites"])
    site_changes=[k for k in sorted(a_sites) if a_sites[k]!=b_sites[k]]
    check("one declared site offset changes",len(a_sites)==34 and a_sites.keys()==b_sites.keys() and site_changes==['first.fingers["middle"].blade.base'],changed=site_changes)
    check("joint/follow declarations unchanged",len(after["joints"])==8 and len(after["follows"])==8 and stripped(before["joints"])==stripped(after["joints"]) and stripped(before["follows"])==stripped(after["follows"]))
    check("revision-bound provenance is not called unchanged semantics",before["binding"]["source_manifest"]!=after["binding"]["source_manifest"] and all(before_records[k]["element_id"]==after_records[k]["element_id"] for k in before_records))

    rejects("stale source paired with after artifact",lambda:build_semantic_manifest(before_bundle,after_bytes,accepted_program_revision=before_bundle.program_revision))
    rejects("stale sidecar paired with valid after inputs",lambda:verify_semantic_manifest(before,after_bundle,after_bytes,accepted_program_revision=after_bundle.program_revision),codes={"OKS-E-MISMATCH"})
    stale_payload=after_bundle.to_payload()
    stale_payload["entry"]["source"]+="\n// review: same geometry, new source revision\n"
    stale_bundle=load_bundle(stale_payload)
    rejects("comment-only source change cannot relabel existing GLB",lambda:build_semantic_manifest(stale_bundle,after_bytes,accepted_program_revision=stale_bundle.program_revision))
    broken=copy.deepcopy(after);broken["objects"][0]["geometry_binding"]["mesh"]=1000000
    rejects("broken mesh reference",lambda:verify_semantic_manifest(broken,after_bundle,after_bytes,accepted_program_revision=after_bundle.program_revision),codes={"OKS-E-MISMATCH"})
    wrong_accessor=copy.deepcopy(after);wrong_accessor["objects"][0]["geometry_binding"]["primitives"][0]["attributes"]["POSITION"]["accessor"]=0
    rejects("wrong in-range accessor reference",lambda:verify_semantic_manifest(wrong_accessor,after_bundle,after_bytes,accepted_program_revision=after_bundle.program_revision),codes={"OKS-E-MISMATCH"})
    wrong_dimension=copy.deepcopy(after);wrong_dimension["objects"][0]["geometry"]["size"][0]+=1
    rejects("invented semantic dimensions",lambda:verify_semantic_manifest(wrong_dimension,after_bundle,after_bytes,accepted_program_revision=after_bundle.program_revision),codes={"OKS-E-MISMATCH"})
    missing_site=copy.deepcopy(after);missing_site["sites"].pop()
    rejects("omitted declared site",lambda:verify_semantic_manifest(missing_site,after_bundle,after_bytes,accepted_program_revision=after_bundle.program_revision),codes={"OKS-E-MISMATCH"})
    wrong_loss=copy.deepcopy(after)
    next(f for f in wrong_loss["features"] if f["feature"]=="live_physics")["treatment"]="preserved"
    rejects("invented destination physics support",lambda:verify_semantic_manifest(wrong_loss,after_bundle,after_bytes,accepted_program_revision=after_bundle.program_revision),codes={"OKS-E-MISMATCH"})
    rejects("unsupported required destination physics",lambda:build_semantic_manifest(after_bundle,after_bytes,accepted_program_revision=after_bundle.program_revision,required_features=["live_physics"]),codes={"OKS-E-UNSUPPORTED"})
    rejects("consumer requirement cannot be removed by manifest",lambda:verify_semantic_manifest(after,after_bundle,after_bytes,accepted_program_revision=after_bundle.program_revision,required_features=["live_physics"]),codes={"OKS-E-UNSUPPORTED"})
    physical_payload=after_bundle.to_payload()
    physical_payload["entry"]["source"]=physical_payload["entry"]["source"].replace('object first @ "first": Rack {','object first @ "first": Rack {\n        physical = sphere_body(0.06[m], 1[kg]);')
    physical_bundle=load_bundle(physical_payload)
    rejects("declared sphere body is explicitly outside finite profile",lambda:build_semantic_manifest(physical_bundle,after_bytes,accepted_program_revision=physical_bundle.program_revision),codes={"OKS-E-PROFILE"})
    model=compile_construction(after_bundle,level="evaluated").model
    prefix=export_glb(model,options=ExportOptions(helpers=False,end="0.5"),target_contract="ontokin.glb/0.2").data
    rejects("real partial interval cannot claim full source delivery",lambda:build_semantic_manifest(after_bundle,prefix,accepted_program_revision=after_bundle.program_revision),codes={"OKS-E-PROFILE"})

    initial=json.loads((Path(__file__).parent/"initial-inventory.json").read_text())
    unchanged=[];changed=[]
    for name,wanted in initial["all_existing_ontokin_python"].items():
        observed=hashlib.sha256((repo/name).read_bytes()).hexdigest()
        (unchanged if observed==wanted else changed).append(name)
    check("all 192 existing OntoKin modules unchanged",len(unchanged)==192 and not changed,changed=changed)
    bindings={}
    relevant=[repo/"ontokin/semantic_export.py",repo/"tools/build_semantic_export_demo.py",repo/"tests/test_semantic_export.py",repo/"docs/engineering/semantic-export-c210/CONTRACT.md",Path(__file__),Path(__file__).parent/"independent_glb.py"]
    relevant.extend(proof/name for name in ["before.glb","after.glb","before.semantic.json","after.semantic.json","before.program.bundle.json","after.program.bundle.json","workflow.json","proof.json"])
    for path in relevant:
        if path.is_file():
            key=str(path.relative_to(repo)) if path.is_relative_to(repo) else str(path)
            bindings[key]={"sha256":sha(path.read_bytes()),"bytes":path.stat().st_size}
    report={"schema_version":"ontokin.c210-independent-review/0.1","status":"passed" if all(c["passed"] for c in checks) else "failed","implementation_head":subprocess.check_output(["git","-C",str(repo),"rev-parse","HEAD"],text=True).strip(),"tracked_status":subprocess.check_output(["git","-C",str(repo),"status","--porcelain"],text=True),"python":platform.python_version(),"platform":platform.platform(),"checks":checks,"summary":{"checks":len(checks),"passed":sum(c["passed"] for c in checks),"failed":sum(not c["passed"] for c in checks)},"input_bindings":bindings,"limits":["Reviewer decodes actual GLB bytes independently using Python struct/json; this is not destination execution.","No Unreal/UEFN execution, C201 admission, or general authoring advantage is established.","Acceptance authority belongs to actual Agent transcript, not accepted_program_revision caller text.","Existing core hashes are compared with retained initial inventory; new additive module reviewed separately."]}
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"status":report["status"],"summary":report["summary"],"output":str(output),"failed":[c["name"] for c in checks if not c["passed"]]},indent=2))
    return 0 if report["status"]=="passed" else 1

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--repo",type=Path,required=True);p.add_argument("--proof",type=Path,required=True);p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    raise SystemExit(run(args.repo.resolve(),args.proof.resolve(),args.output.resolve()))

