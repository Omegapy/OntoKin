"""The adopted reach artifact inventory and bounded execution-record helpers.

This module does not execute source, create expected poses, or certify Agent
transport. Complete release acceptance remains a separate independent role.
"""
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = "docs/language-design/planar-reach-v0.1"
SOURCE_CASES = tuple(f"P{number:02d}" for number in range(1, 24)) + ("P25", "P26", "L01", "L02", "L03")
AGENT_CASES = ("P01", "P11", "P13", "P20", "P16", "P17", "L01", "L02", "L03", "L04")
SOURCE_BROWSER = ("P01", "P11", "P20", "P16", "P18", "P19", "L01", "L02", "L03")
AGENT_BROWSER = AGENT_CASES[:-1]
MAX_BYTES = 64 * 1024 * 1024


def require(condition, message):
    if not condition:
        raise ValueError(message)


def utc():
    return datetime.now(timezone.utc).isoformat()


def source_files(case_id):
    require(case_id in set(SOURCE_CASES) | set(AGENT_CASES), "Unknown adopted delivery case")
    return f"{BASE}/{'draft2-supplements/' if case_id.startswith('L') else ''}{case_id.lower()}.files.json"


def endpoint(case_id):
    source_files(case_id)
    return {"P14": "4", "P16": "4", "P17": "2", "P26": "60",
            "L01": "4", "L02": "2", "L03": "4", "L04": "0.25"}.get(case_id, "3")


def settings(case_id, *, fps=1):
    return {"end": endpoint(case_id), "fps": fps, "helpers": False,
            "position_tolerance_m": .001, "rotation_tolerance_rad": .001, "time_tolerance_s": .000001}


def check_settings(case_id, supplied):
    require(type(supplied) is dict, "Explicit artifact request settings are required")
    expected = settings(case_id)
    require(set(supplied) >= {"end", "fps", "helpers"}, "Record the actual explicit end, fps and helpers settings")
    require(type(supplied["end"]) in (str, int, float) and len(str(supplied["end"])) <= 64,
            "A bounded explicit artifact endpoint is required")
    require(Fraction(str(supplied["end"])) == Fraction(expected["end"]),
            "Artifact endpoint differs from the required complete/prefix horizon")
    require(supplied.get("helpers") is False, "This native corpus requires source carriers without visual helpers")
    result = {**expected, **supplied}
    for name in ("position_tolerance_m", "rotation_tolerance_rad", "time_tolerance_s"):
        require(type(result[name]) in (int, float) and 0 < result[name] <= expected[name],
                "An artifact tolerance is missing, invalid or weaker than the adopted default")
    require(type(result["fps"]) in (int, float) and 0 < result["fps"] <= 10000,
            "Artifact requested fps is outside the inherited supported range")
    return result


def selected_cases(kind, requested):
    required = SOURCE_CASES if kind == "source_component" else AGENT_CASES
    require(kind in ("source_component", "agent_retrieved_artifact"), "Unknown artifact source kind")
    result = tuple(requested) if requested else required
    require(len(result) == len(set(result)) and result and set(result) <= set(required),
            "Select unique required cases from the named source/Agent corpus")
    return result


def relative_name(name):
    require(type(name) is str and name and "\\" not in name and "\0" not in name,
            "A normalized relative member path is required")
    value = PurePosixPath(name)
    require(value.parts and not value.is_absolute() and str(value) == name and
            all(part not in (".", "..", "") for part in value.parts),
            "Member paths cannot be absolute, empty or contain traversal")
    return value


def contained(directory, name):
    relative = relative_name(name)
    directory = Path(directory).resolve()
    current = directory
    for part in relative.parts:
        current = current / part
        require(not current.is_symlink(), "Evidence members cannot use symlinks")
    require(current.is_file() and current.resolve().is_relative_to(directory), "Missing or escaping evidence member")
    return current


def read_bounded(path, maximum=MAX_BYTES):
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), "A regular nonsymlink input is required")
    before = path.stat()
    require(0 <= before.st_size <= maximum, "Input exceeds its byte bound")
    with path.open("rb") as stream:
        raw = stream.read(maximum + 1)
    after = path.stat()
    require(len(raw) == before.st_size == after.st_size and before.st_mtime_ns == after.st_mtime_ns,
            "Input changed while reading")
    return raw


def sha(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def descriptor(path, *, relative_to=None):
    path = Path(path)
    raw = read_bounded(path)
    return {"path": path.relative_to(relative_to).as_posix() if relative_to else path.name,
            "sha256": sha(raw), "bytes": len(raw)}


def checked_member(directory, item):
    require(type(item) is dict and set(item) >= {"path", "sha256", "bytes"}, "Incomplete member descriptor")
    path = contained(directory, item["path"])
    require(descriptor(path, relative_to=Path(directory).resolve()) ==
            {key: item[key] for key in ("path", "sha256", "bytes")}, "Member bytes differ from the recorded identity")
    return path


def decode(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "Duplicate input JSON key")
            result[key] = value
        return result
    def nonfinite(value):
        raise ValueError("Nonfinite input JSON number")
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)


def write_json(path, value):
    raw = (json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2) + "\n").encode()
    require(len(raw) <= MAX_BYTES, "Generated record exceeds its byte bound")
    with Path(path).open("xb") as stream:
        stream.write(raw)
    return descriptor(path)


def git_identity():
    def git(*args):
        return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()
    return {"commit": git("rev-parse", "HEAD"), "tree": git("rev-parse", "HEAD^{tree}"),
            "status": git("status", "--porcelain=v1", "--untracked-files=all")}


def snapshot(*, require_clean=True):
    identity = git_identity()
    if require_clean:
        require(not identity["status"], "Execute artifact evidence from a clean committed checkout")
    names = subprocess.check_output(["git", "-C", str(ROOT), "ls-files", "-z"]).decode().split("\0")
    rows = [descriptor(contained(ROOT, name), relative_to=ROOT) for name in sorted(name for name in names if name)]
    require(git_identity() == identity, "Git identity changed while input bytes were being recorded")
    return {"git": identity, "files": rows, "scope": "all_tracked_repository_file_bytes"}


def finish_inputs(output, before, report):
    """Retain final input identities even when the execution itself failed."""
    if before is None:
        return
    try:
        after = snapshot(require_clean=False)
        write_json(Path(output) / "inputs-after.json", after)
        report["inputs_stable"] = before == after
        require(report["inputs_stable"], "Tracked inputs or Git identity changed during execution")
    except Exception as error:
        report["status"] = "failed"
        report["input_verification_failure"] = {"type": type(error).__name__, "message": str(error)}


def fresh_output(path):
    original = Path(path).absolute()
    for ancestor in (original, *original.parents):
        require(not ancestor.is_symlink(), "Output paths cannot use symlink components")
    output = original.resolve()
    require(not output.exists() and not output.is_relative_to(ROOT), "Use a fresh output directory outside the checkout")
    output.mkdir(parents=True)
    return output


def frozen_cases():
    result = {}
    for name in (f"{BASE}/acceptance.json", f"{BASE}/draft2-supplements/acceptance.json"):
        corpus = decode(read_bounded(ROOT / name))
        for item in corpus["source_cases"]:
            require(item["id"] not in result, "Repeated frozen source case identity")
            result[item["id"]] = item
    return result
