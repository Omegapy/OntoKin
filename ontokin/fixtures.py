"""Materialize the immutable language-design fixtures without editing them."""

from __future__ import annotations

import json
from pathlib import Path


DEFAULT_FIXTURES = Path(__file__).resolve().parent.parent / "docs" / "language-design" / "core-v0.1"


def load_manifest(directory: Path = DEFAULT_FIXTURES) -> dict:
    return json.loads((directory / "validation-cases.json").read_text(encoding="utf-8"))


def materialize(case: dict, directory: Path = DEFAULT_FIXTURES) -> str:
    spec = case["source"]
    if "complete_source" in spec:
        return spec["complete_source"]
    source = (directory / spec["base_file"]).read_text(encoding="utf-8")
    for edit in spec.get("edits", []):
        count = source.count(edit["find"])
        if count != 1:
            raise ValueError(f"{case['id']}: fixture edit matched {count} times; expected exactly once")
        source = source.replace(edit["find"], edit["replace"], 1)
    return source
