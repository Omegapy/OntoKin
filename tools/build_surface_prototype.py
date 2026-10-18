"""Generate one independent surface-prototype GLB for Khronos/Three.js checks.

This uses Python dataclass inputs, *not* the OntoKin .ok compiler. The
output is intentionally labeled an experimental format, not GLB/0.3.
"""

import argparse
import hashlib
import json
from pathlib import Path

from prototypes.surface_v01.mesh import LoftSection, SurfaceMaterial, triangulate_loft
from prototypes.surface_v01.glb import export_loft_prototype

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output-dir",type=Path,required=True)
    args=parser.parse_args()
    sections=(
      LoftSection("z-start",0.0,(0.,0.,0.),0.5,0.3,"base"),
      LoftSection("a-middle",0.8,(0.25,0.1,0.),0.4,0.2,"middle"),
      LoftSection("b-end",2.0,(0.4,0.15,0.),0.1,0.1,"tip")
    )
    materials=(
      SurfaceMaterial("base",(0.6,0.3,0.2,1.),0.,0.8),
      SurfaceMaterial("middle",(0.1,0.4,0.8,1.),0.2,0.4),
      SurfaceMaterial("tip",(0.8,0.8,0.8,1.),0.5,0.5)
    )
    mesh=triangulate_loft(sections,materials,16,"flat")
    output=export_loft_prototype(mesh,name="Offset tapered shell")
    args.output_dir.mkdir(parents=True,exist_ok=True)
    path=args.output_dir/"offset-taper.glb"
    path.write_bytes(output.data)
    sha=hashlib.sha256(output.data).hexdigest()
    print(json.dumps({
        "scope":"isolated geometry-only research prototype, NOT a compiled .ok program",
        "artifact":str(path),"sha256":"sha256:"+sha,
        "facets":mesh.facets,"section_keys":mesh.section_keys,
        "primitives":output.primitives,"triangles":output.triangles,
        "max_local_float32_error_m":output.max_vertex_error_m
    },indent=2))

if __name__=="__main__":
    main()
