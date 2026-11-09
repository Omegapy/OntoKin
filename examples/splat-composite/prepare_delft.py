"""Bind a vetted Delft fit to the two existing service-entrance recordings."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_demo import SERVICE, asset, write_json
from delft_preview import CREDIT, SOURCE_DOI
from prepare_viewer import prepare
from ontokin.composite_manifest import check_manifest
from ontokin.landmark_registration import register


def assemble(controls, glb, plan, picks, output):
    if output.exists() or output.is_symlink():
        raise ValueError("Select a new output directory")
    fit = register(plan, picks, glb)
    if fit["environment"]["sha256"] != "3f749b56cb5399292dcd8b6c014042529e6772cb7ac37bf5797146cc72347fad":
        raise ValueError("Expected the published 140,000-splat Delft display derivative")
    if not fit["passesTolerance"] or not fit["holdout"]["count"]:
        raise ValueError("Delft requires a passing fit and at least one passing held-out landmark")
    with tempfile.TemporaryDirectory(dir=output.parent) as temp:
        demo = Path(temp) / "demo"
        demo.mkdir()
        name = "delft.glb"
        shutil.copyfile(glb, demo / name)
        env = {"name": "Delft Aula and Library", **asset(demo, demo / name),
               "requiredExtension": "KHR_gaussian_splatting", "authority": "visual-only",
               "provenance": f"{CREDIT}. Reduced, view-independent GLB derived from {SOURCE_DOI}."}
        if env["sha256"] != fit["environment"]["sha256"]:
            raise ValueError("Environment changed after fitting")
        summary = {}
        for case, width, gap in (("baseline", .58, .46), ("widened", .90, .30)):
            path = controls / (case + ".json")
            check_manifest(path)
            manifest = json.loads(path.read_bytes())
            shutil.copytree(controls / case, demo / case)
            manifest.update(environment=env, registration=fit["registration"])
            target = demo / path.name
            write_json(target, manifest)
            write_json(demo / case / "manifest-check.json", check_manifest(target))
            run = subprocess.run([sys.executable, "-IB", str(SERVICE / "checks/check_passage.py"),
                                  str(demo / case / "main.ok"), str(demo / case / "accepted-bundle.json"),
                                  str(demo / case / "sliding-gate.glb"), "--width", str(width)],
                                 capture_output=True, text=True, check=True)
            passage = json.loads(run.stdout)
            measured = passage["crossing"]["minimum_lateral_clearance_m"]
            if passage["result"] != "PASS" or any(abs(measured[k] - gap) > 1e-6 for k in ("panel", "post")):
                raise ValueError(f"Unexpected cart clearance for {case}")
            write_json(demo / case / "passage.json", passage)
            summary[case] = {"manifest": path.name, "cartWidthM": width, "clearanceM": measured,
                             "environmentSha256": env["sha256"]}
        write_json(demo / "results.json", summary)
        write_json(demo / "fit.json", fit)
        prepare(demo)
        demo.rename(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("controls", "glb", "plan", "picks", "output"):
        parser.add_argument(key, type=Path)
    args = parser.parse_args()
    try:
        assemble(args.controls, args.glb, args.plan, args.picks, args.output)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Cannot assemble the measured site: {error}\n")
