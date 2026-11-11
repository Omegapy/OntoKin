"""C194 frozen-input verification and independent case-map extensions."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
C193 = REPO / "docs/engineering/guide-repair-c193"
CONTRACT = REPO / "docs/language-design/guided-contact-v0.2"
BACKEND_SHA = "9ce64fd758b4e7f659ddd9d4bb3bcf7a0faa6a1883cc018c673e10536fe0aefe"
BLENDER_SHA = "5e15447670804c855fef6033ac9b8fd82696b762095becf0df79b1c2f8034397"
SOURCE_BINDING = "c193-experimental-0.1"
CASES = {row["id"]: row for row in json.loads((HERE / "frozen/expectations.json").read_text())["cases"]}


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def write(path, value, exclusive=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x" if exclusive else "w") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def verify_inputs():
    manifest = json.loads((HERE / "INPUTS.json").read_text())
    for row in manifest["files"]:
        path = REPO / row["path"]
        require(path.is_file() and path.stat().st_size == row["bytes"] and digest(path) == row["sha256"],
                "Frozen input differs: " + row["path"])
    require(set(CASES) == {"G", "H"}, "Only the two C194 target cases are admitted")
    require(digest(CONTRACT / "backend.json") == BACKEND_SHA, "Adopted backend differs")
    return {"passed": True, "files": len(manifest["files"]), "input_manifest_sha256": digest(HERE / "INPUTS.json")}


def verify_freeze():
    result = verify_inputs()
    seal = json.loads((HERE / "FREEZE.json").read_text())
    require(seal["approved_for_execution"] is True, "Preparation is not approved")
    require(seal["native_builds_before_freeze"] == 0, "Freeze must precede native execution")
    require(seal["input_manifest_sha256"] == result["input_manifest_sha256"], "Freeze input identity differs")
    require(digest(HERE / "PREPARATION-REVIEW.json") == seal["review_sha256"], "Review receipt differs")
    review = json.loads((HERE / "PREPARATION-REVIEW.json").read_text())
    require(review["passed"] is True, "Independent preparation review did not pass")
    require(review["input_manifest_sha256"] == result["input_manifest_sha256"], "Review did not bind frozen inputs")
    result["freeze_sha256"] = digest(HERE / "FREEZE.json")
    return result


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def artifact_reader():
    reader = load_module("c194_inherited_artifact_reader", C193 / "independent/check_artifact.py")
    reader.CASES.update(CASES)
    return reader

