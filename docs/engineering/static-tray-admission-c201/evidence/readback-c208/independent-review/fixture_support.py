"""Independent retained-observation fixtures; no Node or native process exists."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import tempfile

from prototypes.static_tray_admission_c201 import readback_binding as rb
from prototypes.static_tray_admission_c201 import transaction as tx
from tests.test_static_tray_admission_c201_transaction import TransactionFixture


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")


NAMING = "Three.js sanitizes Object3D.name; original names and semantic IDs remain checked without normalization"
LIMITS = {"outer_ms": 30000, "child_work_ms": 28000, "cleanup_ms": 2000,
          "glb_bytes": 8388608, "result_bytes": 4194304, "log_bytes": 4194304}


def measurements(nodes, audit):
    """Historical probe order reconstructed without calling the new validator."""
    result=[]
    def near(ident, field, actual, expected, threshold):
        result.append({"semantic_id":ident,"field":field,"actual":actual,"expected":expected,
                       "difference":abs(actual-expected),"threshold":threshold,"passed":abs(actual-expected)<=threshold})
    for ident in sorted(nodes):
        actual, reference=nodes[ident],audit["nodes"][ident]
        for i in range(4):
            for j in range(4):
                near(ident,f"matrix_{i}_{j}",actual["world_matrix"][i][j],reference["world_matrix"][i][j],
                     0.000005 if j==3 and i<3 else 0.000001)
        if "world_vertices" not in reference:continue
        for i,vertex in enumerate(actual["world_vertices"]):
            for axis in range(3):
                near(ident,f"world_vertex_{i}_{axis}",vertex[axis],reference["world_vertices"][i][axis],0.000005)
                near(ident,f"normal_{i}_{axis}",actual["normals"][i][axis],reference["normals"][i][axis],0.000001)
        observed=[[f(row[a] for row in actual["world_vertices"]) for a in range(3)] for f in (min,max)]
        wanted=[[f(row[a] for row in reference["world_vertices"]) for a in range(3)] for f in (min,max)]
        for axis in range(3):
            near(ident,f"world_min_{axis}",observed[0][axis],wanted[0][axis],0.000005)
            near(ident,f"world_max_{axis}",observed[1][axis],wanted[1][axis],0.000005)
            near(ident,f"world_size_{axis}",observed[1][axis]-observed[0][axis],wanted[1][axis]-wanted[0][axis],0.000005)
    return result


def synthetic_probe(job, job_bytes, audit):
    nodes={}
    for ident,ref in audit["nodes"].items():
        node={"original_name":ident,"importer_name":ident.replace("/",""),"extras":deepcopy(ref["extras"]),
              "world_matrix":deepcopy(ref["world_matrix"]),"children":sorted(ref["children"]),
              "parent":None if ref["extras"]["role"]=="tray-root" else "/".join(ref["extras"]["owner_id"])}
        if "world_vertices" in ref:
            for key in ("positions","normals","world_vertices","indices","material"):node[key]=deepcopy(ref[key])
            node["world_bounds"]=[[f(row[a] for row in node["world_vertices"]) for a in range(3)] for f in (min,max)]
        nodes[ident]=node
    three={"version":"0.186.1","revision":"186","passed":True,"node_count":14,"mesh_count":12,
           "animations":0,"scenes":1,"cameras":0,"findings":[],"nodes":nodes,"measurements":measurements(nodes,audit),
           "position_tolerance_m":0.000005,"matrix_tolerance":0.000001,"naming":NAMING,
           "unsupported_objects":[],"textures":[],"external_resources":[]}
    khronos={"version":"2.0.0-dev.3.10","passed":True,
             "report":{"uri":"final.glb","mimeType":"model/gltf-binary","validatorVersion":"2.0.0-dev.3.10",
                       "issues":{"numErrors":0,"numWarnings":0,"numInfos":0,"numHints":0,"messages":[],"truncated":False},
                       "info":{"version":"2.0","animationCount":0,"materialCount":2,"hasSkins":False,
                               "hasMorphTargets":False,"hasTextures":False,"hasDefaultScene":True,"drawCallCount":12,
                               "totalVertexCount":288,"totalTriangleCount":144}}}
    bound={key:deepcopy(job[key]) for key in ("purpose","slot","route","case","source","protocol_sha256",
           "schedule_sha256","input_lock_sha256","accepted_revision","accepted_pointer_sha256",
           "transaction_receipt_sha256","checks","limits","scope")}
    return {**bound,"schema":"ontokin.c201.readback-probe/0.1","state":"PASSED","passed":True,
            "job_sha256":digest(job_bytes),"artifact_sha256":job["artifact"]["sha256"],"audit_sha256":job["audit"]["sha256"],
            "node":"v24.22.1","native_starts":0,"exports":0,"input_preserved":True,"khronos":khronos,"three":three}


class Fixture:
    """Uses old CPU transaction fixtures, then the real new public binding API."""
    def __init__(self, slot="A01"):
        self.temporary=tempfile.TemporaryDirectory(prefix="c208-independent-",dir="/tmp")
        self.transactions=TransactionFixture(self.temporary.name)
        for name in ("A01","A02","A03","A04"):
            handle=self.transactions.accept(name)
            if name==slot:break
        self.accepted=handle
        self.binding=rb.bind_readbacks(self.transactions.session)
        self.prepared=rb.prepare_readback(self.binding,slot,accepted=handle)
        self.job=rb.inspect_readback_job(self.prepared)
        self.stage=Path(self.job["outputs"]["job"]).parent
        self.pointer=Path(self.transactions.inputs.lock["stores"][slot])/"state.json"
        self.pointer_before=self.pointer.read_bytes()
        self.audit=json.loads(Path(self.job["audit"]["path"]).read_bytes())
        self.probe=synthetic_probe(self.job,self.prepared.job_bytes,self.audit)
        self.stdout=b"Independent CPU fixture: no Node process was launched\n"
        self.stderr=b""
        command=deepcopy(self.job["command"])
        self.record={"argv":command["argv"],"cwd":command["cwd"],"environment":command["environment"],"label":"node",
                     "start_monotonic":100.0,"pid":23456,"process_group":23456,"returncode":0,
                     "observed_log_bytes":len(self.stdout),"retained_log_bytes":len(self.stdout),
                     "cleanup":{"passed":True,"elapsed_ms":0,"process_group_absent":True,"reaped":True},
                     "handles_closed":True,"error":None,"end_monotonic":101.0}
        self.process={"schema":tx.PROCESS_SCHEMA,"purpose":self.job["purpose"],"slot":slot,"stage":"node",
                      "input_lock_sha256":self.job["input_lock_sha256"],"command":command,"process_id":23456,
                      "started_monotonic":100.0,"completed_monotonic":101.0,"returncode":0,"handles_closed":True,
                      "cleanup":{"passed":True,"process_group_absent":True,"reaped":True},
                      "supervisor_record_sha256":"pending","requested_limits":dict(LIMITS),"effective_limits":dict(LIMITS)}
        self.emit()

    def emit(self):
        self.process["supervisor_record_sha256"]=digest(encode(self.record))
        for role,raw in (("probe",encode(self.probe)),("process",encode(self.record)),("stdout",self.stdout),("stderr",self.stderr)):
            Path(self.job["outputs"][role]).write_bytes(raw)

    def verify(self):
        return rb.verify_readback_result(self.prepared,process=self.process)

    def close(self):
        self.temporary.cleanup()
