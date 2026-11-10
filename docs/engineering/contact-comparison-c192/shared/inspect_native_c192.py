"""Dispatch the unchanged independent native inspector with C192 stop inputs."""
import json
from pathlib import Path
import sys

args = sys.argv[sys.argv.index("--") + 1:]
i = args.index("--repo")
repo = Path(args[i + 1])
del args[i:i + 2]
sys.argv = [sys.argv[0], "--", *args]
sys.path.insert(0, str(repo / "docs/engineering/guided-contact-c191/independent/checker"))
import inspect_native

targets = json.loads((Path(__file__).resolve().parents[1] / "frozen/targets.json").read_text())
inspect_native.STOPS.update({case["id"]: case["left_stop_near_face_mm"] for case in targets["cases"]})
inspect_native.main()
