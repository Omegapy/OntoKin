#!/usr/bin/env python3
"""Reproduce the one C270 input and pre-observation oracle using stdlib only.

This is a byte-copy/edit and hashing tool, not an OntoKin parser or evaluator.
It never imports an observer, compiler, exporter, or prior expected hinge rows.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


BASE_REVISION = "254e481351239b536394c182b6761ec4c8662764"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
RELATIVE_CONTROL = "docs/engineering/localized-repair-c270/control"
ORIGINAL = "docs/engineering/semantic-export-c210/evidence/proof"
ORIGINAL_IDENTITIES = {
    "before.main.ok": (1708, "73c95c6509363e492084d7b6959356fe1955f4e78086a72b507167a271a33123"),
    "hinges.ok": (1911, "1516e53179a7b9deecf593ab48afdcd72fba8124ea77868327c25a28a654681a"),
    "before.glb": (185276, "d009d9dba6c69bb8e8e6decdfa9d7e1e92f819e3b59013d481cd30101c973534"),
}
DECLARATION = b'    private param parent_site_ref @ "parent-site-ref": SiteRef = self.pivot;\n'
JOINT_ANCHOR = b'    public joint flex @ "flex": hinge {\n'
OLD_PARENT = b'        parent = self.pivot;\n'
NEW_PARENT = b'        parent = self.parent_site_ref;\n'


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def record(path: str, raw: bytes) -> dict:
    return {"path": path, "bytes": len(raw), "sha256": digest(raw)}


def replace_once(raw: bytes, old: bytes, new: bytes) -> bytes:
    if raw.count(old) != 1:
        raise ValueError(f"Expected exactly one byte anchor: {old!r}")
    return raw.replace(old, new, 1)


def construct() -> dict[str, bytes]:
    originals = {}
    for name, (size, sha256) in ORIGINAL_IDENTITIES.items():
        raw = (REPO / ORIGINAL / name).read_bytes()
        if (len(raw), digest(raw)) != (size, sha256):
            raise ValueError(f"Original input identity changed: {name}")
        originals[name] = raw

    hinges = replace_once(originals["hinges.ok"], JOINT_ANCHOR, DECLARATION + JOINT_ANCHOR)
    hinges = replace_once(hinges, OLD_PARENT, NEW_PARENT)
    original_pin = ("sha256:" + ORIGINAL_IDENTITIES["hinges.ok"][1]).encode("ascii")
    new_pin = ("sha256:" + digest(hinges)).encode("ascii")
    main = replace_once(originals["before.main.ok"], original_pin, new_pin)
    sources = [
        {"filename": "main.ok", "source_id": "entry", **record(f"{RELATIVE_CONTROL}/main.ok", main)},
        {"filename": "hinges.ok", "source_id": "package:example.hinges@1.0.0", **record(f"{RELATIVE_CONTROL}/hinges.ok", hinges)},
    ]
    manifest = {
        "schema_version": "ontokin.bundle/0.1",
        "entry_source_id": "entry",
        "units": [
            {"source_id": "entry", "package_id": None, "version": None, "filename": "main.ok", "source_revision": "sha256:" + digest(main)},
            {"source_id": "package:example.hinges@1.0.0", "package_id": "example.hinges", "version": "1.0.0", "filename": "hinges.ok", "source_revision": "sha256:" + digest(hinges)},
        ],
    }
    canonical = json.dumps(manifest, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
    program_revision = "sha256:" + digest(b"ontokin.bundle/0.1\0" + canonical)
    reference_paths = [
        "docs/language-design/OK-LANG-001-core-language-specification.md",
        "docs/language-design/OK-LANG-002-pinned-modules-and-keyed-assembly-construction.md",
        "docs/language-design/construction-v0.1/ontokin-construction.ebnf",
        "docs/engineering/localized-repair-c260/CONTRACT.md",
        "docs/engineering/localized-repair-c260/CONTROL-PLAN.md",
        "docs/engineering/localized-repair-c260/INPUTS.json",
        "docs/engineering/localized-repair-c269/COVERAGE.json",
        "docs/engineering/localized-repair-c269/NEXT-TASK.md",
    ]
    source_expectation = {
        "outcome": "typed_refusal",
        "exact_code": "UNSUPPORTED_SOURCE_FORM",
        "malformed_is_not_acceptable": True,
        "nonempty_reason_required": True,
        "reason_scope": "The declared SiteRef parameter used by flex.parent is outside the finite endpoint form; no exact English message is prescribed by C260.",
        "input_source_hashes_retained": {s["filename"]: s["sha256"] for s in sources},
        "qualified_hinge_count": 0,
        "qualified_site_count": 0,
        "partial_qualified_set_allowed": False,
        "source_success_allowed": False,
    }
    comparison_expectation = {
        "outcome": "typed_refusal",
        "exact_code": "UNSUPPORTED_SOURCE_FORM",
        "source_refusal_code_and_reason_preserved": True,
        "source_failure_origin_required": True,
        "nonempty_reason_required": True,
        "input_source_hashes_retained": {s["filename"]: s["sha256"] for s in sources},
        "input_artifact_sha256_retained": ORIGINAL_IDENTITIES["before.glb"][1],
        "qualified_hinge_count": 0,
        "qualified_site_count": 0,
        "partial_qualified_set_allowed": False,
        "agreement_allowed": False,
    }
    expected = {
        "schema": "ontokin.c270.h16-siteref-expectation/0.1",
        "case_id": "H16.02-declared-private-siteref",
        "scope": "Exactly one declared SiteRef parameter input and its source-refusal propagation",
        "source_revision": BASE_REVISION,
        "author": {"worker": "/root/fixture", "role": "independent fixture investigator"},
        "construction_order": "Source bytes and this literal oracle were authored before any C270 observer execution and before this author read C265/C267 implementation.",
        "original_inputs": [record(f"{ORIGINAL}/{name}", originals[name]) for name in ORIGINAL_IDENTITIES],
        "supplied_sources": sources,
        "import": {"alias": "mech", "package_id": "example.hinges", "version": "1.0.0", "old_digest": original_pin.decode(), "new_digest": new_pin.decode()},
        "program_identity_reference": {"manifest": manifest, "program_revision": program_revision, "method": "Independent byte hashing under OK-LANG-002 section 3.2; not an evaluated or accepted program."},
        "mutation": {
            "added_declaration": DECLARATION.decode().strip(),
            "declaration_owner": "example.hinges@1.0.0 / Hinges / Finger",
            "changed_joint": "Finger.flex",
            "old_parent_assignment": OLD_PARENT.decode().strip(),
            "new_parent_assignment": NEW_PARENT.decode().strip(),
            "other_source_changes": "Only main.ok's exact companion digest changes. All remaining original source bytes are retained.",
        },
        "comparison_input": {
            **record(f"{ORIGINAL}/before.glb", originals["before.glb"]),
            "purpose": "Source-refusal propagation only",
            "source_matched": False,
            "provenance_rebound": False,
            "agreement_expected": False,
            "isolation_requirement": "Retain the actual source failure and its propagation; stale artifact provenance or field disagreement cannot satisfy this control.",
        },
        "expected": {"observe_source_hinges": source_expectation, "compare_hinges": comparison_expectation},
        "rule_basis": [
            {"path": reference_paths[0], "sections": ["5.1 / LANG-003", "6.1 / LANG-007", "6.2 / LANG-008", "6.3 / LANG-009", "7.2 / LANG-012", "7.3 / LANG-013", "10.2 / LANG-022"]},
            {"path": reference_paths[1], "sections": ["1", "3.1", "3.2"]},
            {"path": reference_paths[2], "productions": ["member", "property_decl", "type", "assignment", "postfix"]},
            {"path": reference_paths[3], "sections": ["1", "3.3", "6"]},
            {"path": reference_paths[4], "control": "H16"},
            {"path": reference_paths[6], "subcase": "H16.02"},
        ],
        "reference_identities": [record(path, (REPO / path).read_bytes()) for path in reference_paths],
        "not_run_by_author": ["C265 observer", "C267 comparator", "product parser/compiler", "evaluator", "exporter", "native/model trial"],
        "nonclaims": [
            "No accepted or evaluated source revision is asserted.",
            "No source/artifact agreement or historical admission is expected.",
            "No site pose, world alignment, motion, physics, broader H16 cases, H20, H22, H24, or whole-product qualification follows.",
            "A mismatching outcome must be retained; this oracle is not changed to match implementation.",
        ],
    }
    return {"main.ok": main, "hinges.ok": hinges, "EXPECTED.json": (json.dumps(expected, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Compare reconstructed bytes with frozen files without writing")
    args = parser.parse_args()
    outputs = construct()
    for name, raw in outputs.items():
        path = HERE / name
        if args.check:
            if path.read_bytes() != raw:
                raise ValueError(f"Frozen control differs from construction: {name}")
        else:
            if path.exists() and path.read_bytes() != raw:
                raise ValueError(f"Refusing to overwrite different frozen bytes: {name}")
            path.write_bytes(raw)
    print(json.dumps({"operation": "check" if args.check else "construct", "observer_executed": False, "files": [record(f"{RELATIVE_CONTROL}/{name}", raw) for name, raw in outputs.items()]}, indent=2))


if __name__ == "__main__":
    main()
