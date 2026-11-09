"""Qualify the greenhouse capture and evaluate the two predeclared OntoKin actions."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import sys

KIT = Path(__file__).resolve().parents[1]
TIMELINE = KIT / "evidence" / "timeline"
VIDEO = KIT / "capture" / "stretch_slow_static_1280x720_25fps.mp4"
REVISION = "038370794d828972cf5a06cdceac50275eda65f0"
MAP_DIGEST = "a41ce551a70d5f22f86ecf1ddeeb61adbaca8826fbfcf47a432bd43190c3994d"


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def read_frame_map(first, last):
    path = TIMELINE / "frame-map.csv"
    if hashlib.sha256(path.read_bytes()).hexdigest() != MAP_DIGEST:
        raise ValueError("Expected the measured greenhouse source-frame map")
    with path.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    return [int(row["source_frame"]) for row in rows[first:last + 1]]


# Only the pinned fitters' scientific refusals complete an experiment. Other
# nonzero exits (including a full disk or corrupt output) need investigation.
FIT_REFUSALS = {
    "root": ("Select a valid half-open frame range", "The fitted movement is smaller",
             "Constant velocity exceeds"),
    "knee": ("Expected 8 to ", "A stationary knee", "Initial knee orientation cannot define",
             "Knee excursion is smaller", "A single hinge does not fit", "Hinge replay exceeds"),
}


def evaluate_actions(observation, out, first, sources):
    # Always execute both predeclared fits. Exit 1 preserves its reason in stderr.
    fits = {}
    errors = []
    for name, operation, flags in [
        ("root", "synthesize", ["--start-frame", "0", "--stop-frame", "30", "--max-error-m", "0.025"]),
        ("knee", "articulate", ["--joint", "left_knee", "--max-error-deg", "10", "--max-phases", "16"]),
    ]:
        dest = out / (name + "-action")
        args = [sys.executable, "-B", "-m", "tools.perception", operation, str(observation), str(dest), *flags]
        with (out / (name + ".stdout")).open("w") as stdout, (out / (name + ".stderr")).open("w") as stderr:
            result = subprocess.run(args, stdout=stdout, stderr=stderr)
        detail = {"command": args, "exit_code": result.returncode}
        fits[name] = detail
        if result.returncode:
            reason = (out / (name + ".stderr")).read_text().strip()
            expected = result.returncode == 1 and any(
                reason.startswith("Observation workflow: " + prefix) for prefix in FIT_REFUSALS[name]
            )
            detail.update(outcome="refused" if expected else "execution_error", reason=reason)
            if not expected:
                errors.append(name)
            continue
        fit = json.loads((dest / "fit.json").read_text())
        detail.update(outcome=fit["outcome"], training=fit["training"], held_out=fit["held_out"],
                      counterfactual=fit["counterfactual"], fit_file=dest.name + "/fit.json")
    if fits["knee"]["exit_code"] == 0:
        # This replays the native .ok source and cross-checks the original fit metrics.
        sys.path.insert(0, str(TIMELINE))
        from knee_source_groups import replay_groups
        groups = replay_groups(observation, out / "knee-action", sources)
        write_json(out / "knee-source-groups.json", groups)
        fits["knee"]["source_disjoint_holdout"] = {
            k: v for k, v in groups["source_disjoint"].items() if k != "track_local_frames"
        }
    with (out / "fit-frame-map.csv").open("w", newline="") as stream:
        rows = csv.writer(stream)
        rows.writerow(["observation_frame", "analysis_frame_30hz", "source_frame_25hz", "source_time_s",
                       "root_split", "knee_split"])
        for i, source in enumerate(sources):
            root = ("fit" if i < 22 else "held") if i < 30 and len(sources) >= 30 else "outside"
            knee = "held" if i % 4 == 3 and i < len(sources) - 1 else "fit"
            rows.writerow([i, first + i, source, source / 25, root, knee])
    return {"status": "execution_error" if errors else "fits_evaluated", "actions": fits}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("job", type=Path, help="FlowHMR job with original receipt and raw outputs")
    parser.add_argument("output", type=Path, help="new evaluation directory")
    args = parser.parse_args()
    job, out = args.job.resolve(), args.output.absolute()
    from tools import perception
    repo = Path(perception.__file__).resolve().parents[2]
    identity = subprocess.check_output(["git", "-C", repo, "rev-parse", "HEAD"], text=True).strip()
    changes = subprocess.check_output(["git", "-C", repo, "status", "--porcelain", "--untracked-files=no"], text=True)
    if identity != REVISION or changes:
        parser.error("Use the clean, pinned OntoKin controller described in RESTORE.md")
    out.mkdir(parents=True, exist_ok=False)
    report = {"controller_commit": identity, "status": "capture_not_qualified", "actions": {}}
    try:
        capture = runpy.run_path(str(KIT / "qualification/verify-capture.py"))["verify_stretch"](job, VIDEO)
        report.update(status="evaluation_error", capture=capture)
        from tools.perception.observation import load_observation
        manifest, _ = load_observation(job / "observation")
        write_json(out / "inspection.json", manifest)
        first, last = capture["track_range_30hz_inclusive"]
        sources = read_frame_map(first, last)
        if len(sources) != capture["exported_samples"]:
            raise ValueError("Frame-map length disagrees with the qualified capture")
        report.update(evaluate_actions(job / "observation", out, first, sources))
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as error:
        report["reason"] = str(error)
    write_json(out / "evaluation.json", report)
    print(report["status"], file=sys.stdout)
    return 0 if report["status"] == "fits_evaluated" else 1


if __name__ == "__main__":
    sys.exit(main())
