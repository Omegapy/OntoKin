"""Check one trusted, pinned FlowHMR worker job against its input and tracked output."""
import argparse
import json
from pathlib import Path
import re
import sys

import numpy as np

from tools.perception import flowhmr
from tools.perception.observation import digest, load_observation


REVISION = "87ebb483ce9da32be72c67971bc8fd76f27251f3"
CHECKPOINT = "b7eb06b119feaf5ad7287bafdb2fff38d42dfc22ea9d256f8cdd2ada26dfc53a"
STRETCH_SHA256 = "2005ac3b8c994d6cfebbb53d52a2262e4167686d757731b6f8a2347f276ea535"
STRETCH_TRANSCODE_FRAMES = 300
PRIOR_OUTPUTS = {
    "f70e90e2acc5b938a5dab9d3bbafa0f2098a7f9cf1d44d26172f1cc316954e39",  # published capture
    "42191c6d2b435fb7f314be88836b0c0cd248b798e1510abbfc7b081af2234d0d",  # zero-feature control
}


def require(condition, detail):
    if not condition:
        raise ValueError(detail)


def one(pattern, log):
    matches = re.findall(pattern, log, flags=re.MULTILINE)
    require(len(matches) == 1, f"Expected one matching worker record for {pattern}")
    return matches[0]


def track_record(log, samples, alias):
    # The controller reserves a new alias for each job. Match it across the log and receipt.
    input_path = one(r"^\[1/1\] (.+)$", log)
    require(input_path == alias, "Logged input differs from this job's reserved video alias")
    stem = Path(alias).stem
    require("WARN no_tracks" not in log, "No person track. Upstream used its full-image fallback.")
    require("skip (exists)" not in log and "using cached transcoded video" not in log,
            "The worker reused a previous preprocessing stage")
    transcode = one(r"^>>> video transcoding done \(encoder: (?:libx264|h264_nvenc|mpeg4|libx265)\): (.+)$", log)
    require(Path(transcode).name == stem + "_30fps.mp4", "Transcode belongs to another input")
    one(r"^\s*=== Step 2: Static Camera ===\s*$", log)
    track = one(r"\[bbox\] track (\d+): length=(\d+) frame_range=\[(\d+),(\d+)\] / total=(\d+)", log)
    track_id, detections, first, last, total = map(int, track)
    gen = one(r"\[gen\] T=(\d+), range=\[(\d+),(\d+)\], seed=0, cfg=1\.0(?:\s|$)", log)
    feat_path, features = one(r"\[sam\] saved -> (.+?_sam3d_feat_static\.pt) +\(shape=\((\d+), 3072\)\)", log)
    require(Path(feat_path).name == stem + "_sam3d_feat_static.pt", "SAM features belong to another input")
    one(r"^=== Done \| ok=1 failed=0 ===\s*$", log)
    require(0 <= first <= last < total and 0 < detections <= samples, "Invalid tracked range or length")
    require(samples == last - first + 1 == int(features) and tuple(map(int, gen)) == (samples, first, last),
            "Track, fresh SAM features, generation and exported sample count disagree")
    return {"track_id": track_id, "detected_frames": detections, "transcoded_frames": total,
            "track_range_30hz_inclusive": [first, last], "first_exported_time_on_30hz_grid_s": first / 30}


def verify(job, video):
    receipt = json.loads((job / "worker.json").read_text())
    require(receipt.get("status") == "complete", "Worker did not complete")
    require((receipt["schema"], receipt["adapter"], receipt["revision"]) ==
            ("ontokin.perception_worker/1", "flowhmr", REVISION), "Wrong worker or revision")
    capture = digest(video)
    require(receipt["capture"]["kind"] == "video" and receipt["capture"]["sha256"] == capture,
            "Video hash differs from the worker input")
    require(receipt["checkpoint"]["sha256"] == CHECKPOINT, "Released FlowHMR checkpoint hash required")
    checkpoint_path = receipt["checkpoint"]["path"]
    command = receipt["command"]
    require(len(command) == 6 and command[:2] == [receipt["python"], "run_v2m_demo_generation.py"]
            and command[3:] == ["--ckpt", checkpoint_path, "--static_camera"],
            "Expected the pinned raw-video command in fixed-camera mode")
    require(type(receipt["timeout_s"]) is int and 1 <= receipt["timeout_s"] <= 86400, "Missing finite timeout")

    raw_rel = Path("raw") / (Path(checkpoint_path).stem + ".npz")
    require(receipt["raw_npz"] == str(raw_rel) and receipt["observation"] == "observation", "Unexpected output path")
    raw = job / raw_rel
    raw_hash = digest(raw)
    require(raw_hash not in PRIOR_OUTPUTS, "C170 control or published example supplied as a fresh result")
    require(raw_hash == receipt["raw_sha256"], "Raw capture digest mismatch")
    manifest, arrays = load_observation(job / "observation")
    require(manifest["adapter"] == "flowhmr" and manifest["writer_contract_revision"] == REVISION,
            "Wrong observation adapter")
    require(manifest["source"] == {"name": raw.name, "kind": "provided", "sha256": raw_hash,
                                   "capture": "sha256:" + capture, "checkpoint": "sha256:" + CHECKPOINT},
            "Observation source differs from receipt")
    meta, decoded = flowhmr.adapt(raw)
    require(meta == manifest["observation"] and arrays.keys() == decoded.keys()
            and all(np.array_equal(value, decoded[key]) for key, value in arrays.items()),
            "Normalized observation differs from a fresh decode of the raw capture")
    require(meta["fps"] == 30 and meta["units"] == "m" and meta["coordinate_system"] == "flowhmr_export_y_up",
            "Unexpected stored frame rate, length unit or axes")
    samples = meta["sample_count"]
    require(samples == receipt["sample_count"], "Observation sample count differs from receipt")
    log = job / "worker.log"
    track = track_record(log.read_text(errors="replace"), samples, command[2])
    return {"result": "worker_evidence_consistent", "upstream_revision": REVISION, "capture_sha256": capture,
            "checkpoint_sha256": CHECKPOINT, "raw_sha256": raw_hash, "worker_log_sha256": digest(log),
            "stored_fps": 30, "exported_samples": samples, "units": meta["translation_convention"],
            "rotations": meta["rotation_convention"], "contact_scores_present": "foot_contact_scores" in arrays,
            **track}


def verify_stretch(job, video):
    report = verify(job, video)
    require(report["capture_sha256"] == STRETCH_SHA256,
            "Expected the bundled fixed-camera stretch video")
    require(report["transcoded_frames"] == STRETCH_TRANSCODE_FRAMES,
            "The bundled video must have 300 analysis frames at 30 Hz")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("job", type=Path)
    parser.add_argument("video", type=Path)
    parser.add_argument("--stretch", action="store_true", help="Require the bundled stretch clip and its measured timeline")
    args = parser.parse_args()
    try:
        verify_job = verify_stretch if args.stretch else verify
        print(json.dumps(verify_job(args.job, args.video), indent=2))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Capture check refused: {error}", file=sys.stderr)
        sys.exit(1)
