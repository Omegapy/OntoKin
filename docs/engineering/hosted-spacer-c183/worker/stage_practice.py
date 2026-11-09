"""Stage the public spacer practice and the pinned runtime under a new guest input directory."""
import argparse
import shutil
import sys
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
for field in ("practice","kit","checkout","out"):
    p.add_argument("--"+field,type=Path,required=True)
p.add_argument("--role",choices=("ontokin","blender"),required=True)
a=p.parse_args()
stage=a.out.resolve()
stage.mkdir()
shutil.copytree(a.practice/"starters"/a.role,stage/"starter")
(stage/"submission").mkdir()
for name in ("TASK.md","measure_glb.py"):
    shutil.copy2(a.practice/name,stage/name)
if a.role=="ontokin":
    sys.path.insert(0,str(a.kit.resolve()/"benchmark/operator"))
    from stage_arm import add_runtime
    add_runtime(a.checkout,stage/"job/checkout")
    launcher=stage/"job/venv/bin/python"
    launcher.parent.mkdir(parents=True)
    launcher.write_text('#!/bin/sh\nexec /opt/c181-python/bin/python3.12 "$@"\n')
    launcher.chmod(0o755)
