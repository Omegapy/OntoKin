#!/usr/bin/env python3
"""C272 format validation of the delivered GLBs (TASK-025, REQ-022).

    .venv/bin/python docs/engineering/localized-repair-c272/validate_glbs.py \
        --run RUN_DIR --output-dir NEW_DIR --node NODE22

RUN_DIR is a qualify.py output directory. Each delivered GLB is copied, with a reference
file, into NEW_DIR/glbs. The reference's poses and primitive sizes come from C255's
independent expected state, at C255's delivery limits; only its identity fields come
from the artifact. The existing `tools/verify_gltf.mjs` is then run with the committed
Khronos validator and Three.js, and again on a deliberately truncated copy, which must
be refused. This module imports no OntoKin product module.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
import observe  # noqa: E402

ORACLE = observe.pinned("c255_oracle")
DELIVERED = {"V1-start": ("V1", "start", 0.65), "V1-final": ("V1", "retained", 0.75),
             "V2-start": ("V2", "start", 0.75), "V2-final": ("V2", "retained", 0.65),
             "N1-start": ("N1", "start", 0.65), "N1-retained": ("N1", "retained", 0.65)}


def glb_metadata(raw: bytes) -> dict:
    size = struct.unpack_from("<I", raw, 12)[0]
    return json.loads(raw[20:20 + size])["extras"]["ontokin"]


def reference(raw: bytes, length: float) -> dict:
    state = ORACLE.semantic_state(length)
    by_id = {tuple(o["id"]): o for o in state["objects"]}
    samples = []
    for t in ORACLE.TIMES:
        objects = {}
        for o in state["objects"]:
            pose = ORACLE.pose_for(o["id"], t, length)
            objects[o["path"]] = {"position_m": pose["position_m"], "orientation_wxyz": pose["rotation_wxyz"]}
        samples.append({"time_seconds": t, "objects": objects})
    meta = glb_metadata(raw)
    return {"schema_version": "ontokin.viewer-reference/0.2",
            "artifact_sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
            "program_revision": meta["program"]["revision"], "source_manifest": meta["program"]["manifest"],
            "geometry": [{"path": o["path"], "element_id": o["id"], "geometry": o["primitive"]} for o in by_id.values()],
            "samples": samples,
            "tolerances": {"position_m": ORACLE.DELIVERY_POSITION, "rotation_rad": ORACLE.DELIVERY_ANGLE},
            "independent_oracle": "C255 semantic_state and pose_for (docs/engineering/localized-repair-c255/oracle.py); "
                                  "identity fields only from the artifact"}


def run_validator(node: str, directory: Path, output: Path) -> subprocess.CompletedProcess:
    return subprocess.run([node, str(ROOT / "tools/verify_gltf.mjs"), str(directory), "--output", str(output)],
                          cwd=ROOT / "tools", capture_output=True, text=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--node", required=True, help="the Node.js 22 executable")
    args = parser.parse_args()
    out = args.output_dir.resolve()
    if out.exists() and any(out.iterdir()):
        parser.error("the output directory must be new or empty")
    glbs, truncated = out / "glbs", out / "truncated"
    glbs.mkdir(parents=True)
    truncated.mkdir()
    files = {}
    for name, (case, state, length) in DELIVERED.items():
        raw = (args.run / "delivery/cases" / case / "record/files" / state / "scene.glb").read_bytes()
        (glbs / f"{name}.glb").write_bytes(raw)
        (glbs / f"{name}.reference.json").write_text(json.dumps(reference(raw, length), indent=2) + "\n")
        files[name] = {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), "expected_length_m": length}
    first = (glbs / "V1-final.glb").read_bytes()
    cut = first[:len(first) // 2]
    (truncated / "V1-final-truncated.glb").write_bytes(cut)
    ref = reference(first, 0.75)
    ref["artifact_sha256"] = "sha256:" + hashlib.sha256(cut).hexdigest()
    (truncated / "V1-final-truncated.reference.json").write_text(json.dumps(ref, indent=2) + "\n")
    version = subprocess.run([args.node, "--version"], capture_output=True, text=True).stdout.strip()
    good = run_validator(args.node, glbs, out / "verify_gltf-report.json")
    bad = run_validator(args.node, truncated, out / "verify_gltf-truncated-report.json")
    (out / "verify_gltf.log").write_text(good.stdout + "\n--- stderr ---\n" + good.stderr)
    (out / "verify_gltf-truncated.log").write_text(bad.stdout + "\n--- stderr ---\n" + bad.stderr)
    report = json.loads((out / "verify_gltf-report.json").read_text()) if (out / "verify_gltf-report.json").exists() else None
    package = json.loads((ROOT / "tools/package.json").read_text())
    summary = {"schema": "ontokin.c272.glb-validation/1", "node": version, "files": files,
               "committed_tool_versions": package.get("devDependencies") or package.get("dependencies"),
               "validator_exit": good.returncode, "report": "verify_gltf-report.json",
               "truncated_copy_exit": bad.returncode, "truncated_copy_refused": bad.returncode != 0,
               "transport_limits": ("The GLB holds sampled, recorded motion. Live physics, collision response and the "
                                    "execution of actions in a destination are unsupported. Sites, actions and events "
                                    "travel only in the semantic sidecar, not in the GLB.")}
    if report:
        summary["per_file"] = [{"file": r["file"], "sha256": r["sha256"], "program_revision": r.get("program_revision"),
                                "khronos_validator": r["validator"],
                                "three_js": {k: v for k, v in r["three_js"].items() if k != "samples"},
                                "geometry_checked": len(r.get("geometry") or [])}
                               for r in report.get("files", [])]
        summary["report_scope"] = report.get("scope")
    (out / "SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({k: summary[k] for k in ("node", "validator_exit", "truncated_copy_refused")}))
    return 0 if good.returncode == 0 and bad.returncode != 0 else 1


if __name__ == "__main__":
    sys.exit(main())
