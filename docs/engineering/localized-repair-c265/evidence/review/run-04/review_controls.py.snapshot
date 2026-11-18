#!/usr/bin/env python3
"""Independent public-API adversarial checks for the C265 source interface."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import re
import sys
import traceback


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def substitute(raw, old, new):
    old, new = old.encode(), new.encode()
    assert old in raw, old
    return raw.replace(old, new, 1)


def fixture(repo, endpoint="before"):
    proof = repo / "docs/engineering/semantic-export-c210/evidence/proof"
    return {"main.ok": (proof / f"{endpoint}.main.ok").read_bytes(),
            "hinges.ok": (proof / "hinges.ok").read_bytes()}


def changed(files, filename, old, new):
    files = dict(files)
    files[filename] = substitute(files[filename], old, new)
    if filename == "hinges.ok":
        pin = b'digest "sha256:' + digest(files["hinges.ok"]).encode() + b'"'
        files["main.ok"], count = re.subn(rb'digest "sha256:[0-9a-f]{64}"', pin, files["main.ok"])
        assert count == 1
    return files


def cases(repo):
    original = fixture(repo)
    yield "original_before", "pass", original
    yield "original_after", "pass", fixture(repo, "after")
    for name, old, new in [
        ("quoted_vec3_constructor", "axis = vec3(0, 0, 1)", 'axis = "vec3"(0, 0, 1)'),
        ("quoted_range_constructor", "limits = range(-45[deg], 45[deg])", 'limits = "range"(-45[deg], 45[deg])'),
        ("quoted_self", "parent = self.pivot", 'parent = "self".pivot'),
        ("quoted_part", "child = self.blade.base", 'child = self."blade".base'),
        ("quoted_site", "parent = self.pivot", 'parent = self."pivot"'),
        ("quoted_joint_kind", ': hinge {', ': "hinge" {'),
        ("quoted_unit", "initial = 0[rad]", 'initial = 0["rad"]'),
        ("quoted_field", "initial = 0[rad]", '"initial" = 0[rad]'),
        ("quoted_assignment_operator", "initial = 0[rad]", 'initial "=" 0[rad]'),
        ("nested_joint_in_method", "return tween(self.flex, angle, duration);", 'public joint hidden @ "hidden": hinge { parent = self.pivot; child = self.blade.base; axis = vec3(0,0,1); limits = range(0[rad],0[rad]); initial = 0[rad]; } return tween(self.flex, angle, duration);'),
        ("constructor_member_shadow", 'public param length @ "length": Length = 0.6[m];', 'public param vec3 @ "vec3-member": Length = 0.6[m];'),
        ("implicit_origin_member_key", 'public site pivot @ "pivot"', 'public site pivot @ "origin"'),
        ("implicit_frame_member_key", 'public site pivot @ "pivot"', 'public site pivot @ "frame"'),
        ("joint_part_key_collision", 'public joint flex @ "flex"', 'public joint flex @ "blade"'),
        ("part_site_field_override", "length = self.length;", 'base.size = 1[mm]; length = self.length;'),
        ("quoted_helper_return", "return keyed<Vec3<Length>>", '"return" keyed<Vec3<Length>>'),
    ]:
        yield name, "refuse", changed(original, "hinges.ok", old, new)

    for name, old, new in [
        ("nested_joint_initial_override", 'fingers["middle"].length = 0.65[m];', 'fingers["middle"].flex.initial = 0[rad];'),
        ("nested_site_size_override", 'fingers["middle"].length = 0.65[m];', 'fingers["middle"].pivot.size = 0[m];'),
        ("deep_site_interface_override", 'fingers["middle"].length = 0.65[m];', 'fingers["middle"].blade.base.interface = "hinged.part";'),
        ("direct_joint_override", 'length = self.finger_length;', 'flex = 0[rad]; length = self.finger_length;'),
        ("direct_site_override", 'length = self.finger_length;', 'pivot = 0[m]; length = self.finger_length;'),
        ("nested_constructor_shadow_binder", 'for (key, offset) in self.mounts', 'for (vec3, offset) in self.mounts'),
        ("nested_self_shadow_binder", 'for (key, offset) in self.mounts', 'for (self, offset) in self.mounts'),
        ("invalid_authored_import_key", 'mech @ "mechanics"', 'mech @ "bad/key"'),
        ("import_definition_key_collision", 'mech @ "mechanics"', 'mech @ "rack"'),
        ("scene_root_action_name_collision", 'action flex @ "flex"', 'action first @ "flex"'),
        ("scene_root_action_key_collision", 'action flex @ "flex"', 'action flex @ "first"'),
        ("nested_joint_in_action_body", 'start flex;', 'public joint hidden @ "hidden": hinge { parent = first.origin; child = second.origin; axis = vec3(0,0,1); limits = range(0[rad],0[rad]); initial = 0[rad]; } start flex;'),
        ("quoted_membership_type", ": Keyed<Vec3<Length>>", ': "Keyed"<Vec3<Length>>'),
        ("quoted_membership_type_separator", ": Keyed<Vec3<Length>>", ': Keyed"<"Vec3<Length>>'),
        ("quoted_helper_call_opening", "mech.three_mounts(0.6[m])", 'mech.three_mounts"("0.6[m])'),
    ]:
        yield name, "refuse", changed(original, "main.ok", old, new)

    alias = dict(original)
    alias["main.ok"] = alias["main.ok"].replace(b"import mech ", b"import range ").replace(b"mech.", b"range.")
    yield "constructor_import_alias_shadow", "refuse", alias

    # The same opaque key in distinct instance namespaces is legal.
    yield "same_site_keys_on_distinct_classes", "pass", changed(original, "hinges.ok", 'site base @ "base"', 'site base @ "pivot"')
    # Ignored pose content remains a witness; no execution or world-pose claim.
    yield "nontrivial_unevaluated_pose", "pass", changed(original, "hinges.ok", "pose = pose(self.frame, vec3(-self.length / 2, 0[m], 0[m]), quat(1, 0, 0, 0));", "pose = pose(self.frame, vec3(-self.length / 3, 7[m], 0[m]), quat(0, 1, 0, 0));")
    # Reserved spelling inside literal data is not declaration syntax.
    files = dict(original)
    files["hinges.ok"] = files["hinges.ok"].replace(b'"hinged.part"', b'"joint"')
    pin = b'digest "sha256:' + digest(files["hinges.ok"]).encode() + b'"'
    files["main.ok"] = re.sub(rb'digest "sha256:[0-9a-f]{64}"', pin, files["main.ok"])
    yield "joint_spelling_in_string_data", "pass", files
    # Unicode comments shift UTF-8 source offsets without changing declarations.
    yield "unicode_comment_shift", "pass", changed(original, "hinges.ok", 'module Hinges @ "hinges";', '// comment café α😀\nmodule Hinges @ "hinges";')
    # C257's unchanged comment lexer cannot safely observe the valid bare-CR
    # terminator. Explicit refusal preserves complete-set authority.
    yield "bare_cr_comment_hidden_joint", "refuse:UNSUPPORTED_SOURCE_FORM", changed(
        original, "hinges.ok", '    public joint flex @ "flex": hinge {',
        '    // comment\rpublic joint hidden @ "hidden": hinge { parent = self.pivot; child = self.blade.base; axis = vec3(0,0,1); limits = range(0[rad],0[rad]); initial = 0[rad]; }\n    public joint flex @ "flex": hinge {')
    crlf = {name: raw.replace(b"\n", b"\r\n") for name, raw in original.items()}
    pin = b'digest "sha256:' + digest(crlf["hinges.ok"]).encode() + b'"'
    crlf["main.ok"] = re.sub(rb'digest "sha256:[0-9a-f]{64}"', pin, crlf["main.ok"])
    yield "ordinary_crlf_comment", "pass", crlf
    for name, axis, category in [
        ("invalid_nonunit_axis", "vec3(2, 0, 0)", "MALFORMED"),
        ("invalid_short_axis", "vec3(0.5, 0, 0)", "MALFORMED"),
        ("valid_unsupported_nonbasis_axis", "vec3(0.6, 0.8, 0)", "UNSUPPORTED_SOURCE_FORM"),
        ("valid_unsupported_nearunit_axis", "vec3(1.0000000000001, 0, 0)", "UNSUPPORTED_SOURCE_FORM"),
        ("invalid_axis_outside_unit_condition", "vec3(1.00000001, 0, 0)", "MALFORMED"),
    ]:
        yield name, "refuse:" + category, changed(original, "hinges.ok", "vec3(0, 0, 1)", axis)


def witnesses(value):
    if isinstance(value, dict):
        if {"file", "startByte", "endByteExclusive"} <= value.keys():
            yield value
        for child in value.values():
            yield from witnesses(child)
    elif isinstance(value, list):
        for child in value:
            yield from witnesses(child)


def check_pass(report, files):
    assert isinstance(report, dict)
    assert len(report["records"]) == 8
    for flag in ("artifactAgreementQualified", "historicalInputsBound", "sourceValidityQualified", "sitePosesQualified", "executionAllowed", "completeC255Semantic"):
        assert not report.get(flag), flag
    count = 0
    for witness in witnesses(report):
        name, start, end = witness["file"], witness["startByte"], witness["endByteExclusive"]
        assert name in files
        assert type(start) is int and type(end) is int and 0 <= start < end <= len(files[name])
        files[name][start:end].decode("utf-8")
        if "sha256" in witness:
            assert witness["sha256"] == digest(files[name])
        count += 1
    assert count > 0, "no source witnesses"
    return count


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[5])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    path = args.repo / "docs/engineering/localized-repair-c265/source_hinges.py"
    raw = path.read_bytes()
    (args.out / "source_hinges.py.snapshot").write_bytes(raw)
    (args.out / "review_controls.py.snapshot").write_bytes(Path(__file__).read_bytes())
    spec = importlib.util.spec_from_file_location("c265_independent_review_candidate", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    results = []
    for name, expected, files in cases(args.repo):
        record = {"case": name, "expected": expected,
                  "inputs": {n: {"bytes": len(b), "sha256": digest(b)} for n, b in files.items()}}
        directory = args.out / "inputs" / name
        directory.mkdir(parents=True)
        for filename, content in files.items():
            (directory / filename).write_bytes(content)
        try:
            result = module.observe_source_hinges(files)
            record.update(actual="pass", passed=expected == "pass")
            if expected == "pass":
                record["checked_witnesses"] = check_pass(result, files)
            else:
                record["unexpected_hinge_count"] = len(result.get("records", []))
        except module.Fault as exc:
            accepted = expected == "refuse" or expected == "refuse:" + exc.code
            record.update(actual="refuse", passed=accepted, code=exc.code, detail=str(exc))
        except Exception as exc:
            record.update(actual="unexpected_exception", passed=False, exception=type(exc).__name__, detail=str(exc))
        results.append(record)
    summary = {"schema": "ontokin.c265.independent-review-controls/1", "reviewer": "/root/independent_review",
               "observed_at": datetime.now(timezone.utc).isoformat(),
               "python": sys.version, "platform": platform.platform(), "implementation_sha256": digest(raw),
               "control_sha256": digest(Path(__file__).read_bytes()),
               "cases": len(results), "passed": sum(x["passed"] for x in results),
               "failed": sum(not x["passed"] for x in results), "results": results}
    (args.out / "RESULTS.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({k: summary[k] for k in ("implementation_sha256", "control_sha256", "cases", "passed", "failed")}, indent=2))
    for result in results:
        if not result["passed"]:
            print(json.dumps(result, indent=2))
    return bool(summary["failed"])


if __name__ == "__main__":
    raise SystemExit(main())
