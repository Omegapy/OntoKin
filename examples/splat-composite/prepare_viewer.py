"""Admit a trusted local pair of manifests to the experimental viewer."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from ontokin.composite_manifest import check_manifest


def prepare(folder):
    receipt = {"schema": "ontokin-composite-viewer/1", "manifests": {}}
    first = None
    for variant in ("baseline", "widened"):
        path = folder / f"{variant}.json"
        with path.open("rb") as stream:
            raw = stream.read(65537)
        if len(raw) > 65536:
            raise ValueError("Manifest exceeds 64 KiB")
        check = check_manifest(path)
        manifest = json.loads(raw)
        registration = (manifest["registration"], manifest["environment"])
        if first is not None and registration != first:
            raise ValueError("Both manifests must use the same registered environment")
        first = registration
        if raw != path.read_bytes():
            raise ValueError("Manifest changed during validation")
        receipt["manifests"][variant] = {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "sceneSplats": check["environment"]["scene_splat_count"],
            "storedSplats": check["environment"]["splat_count"],
        }
    (folder / "viewer-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("demo_dir", type=Path)
    try:
        prepare(parser.parse_args().demo_dir)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Viewer preflight failed: {exc}\n")
