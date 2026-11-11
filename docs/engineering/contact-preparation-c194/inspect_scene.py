"""C194 case-only wrapper around the unchanged C193 saved-scene inspector."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import CASES, C193, digest, load_module, verify_freeze

verify_freeze()
inspector = load_module("c194_inherited_scene_inspector", C193 / "independent/inspect_scene.py")
inspector.CASES.update(CASES)
inspector.STOPS.update({key: case["left_stop_near_face_mm"] for key, case in CASES.items()})
inspector.main()

