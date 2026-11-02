#!/usr/bin/env python3
"""Independent stdlib-only reader for frozen C088 source/native observations.

No production parser, evaluator, budget helper or geometry function is imported.
Expected facts come only from the exact freeze and original source byte spans.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from keyed_membership_evidence import (
    Freeze, MEMBERSHIP_STAGES, PREDECESSOR_COMMIT, STAGES, canonical, inventory,
    jsonl_reader, read, save, sha, stamp, standalone_bundle_identity,
)


class Reader:
    def __init__(self, freeze):
        self.freeze = freeze
        self.checks = 0
        self.failures = []
        self.case = "startup"

    def require(self, condition, label, actual=None, expected=None):
        self.checks += 1
        if not condition:
            def serial(value):
                if isinstance(value, bytes):
                    return {"bytes": len(value), "sha256": sha(value)}
                if isinstance(value, (set, frozenset)):
                    return sorted(serial(item) for item in value)
                if isinstance(value, (tuple, list)):
                    return [serial(item) for item in value]
                if isinstance(value, dict):
                    return {key: serial(item) for key, item in value.items()}
                return value
            self.failures.append({"case": self.case, "check": label,
                                  "actual": serial(actual), "expected": serial(expected)})

    def equal(self, actual, expected, label):
        self.require(actual == expected, label, actual, expected)

    def diagnostic(self, actual, goal, *, raw=None, control_raw=None):
        self.equal(actual.get("code"), goal["diagnostic_code"], "diagnostic code")
        for suffix in ("message", "phase", "category", "details", "related"):
            key = "diagnostic_" + suffix
            if key in goal:
                self.equal(actual.get(suffix), goal[key], "diagnostic " + suffix)
        for key, value in goal.get("required_details", {}).items():
            self.equal(actual.get("details", {}).get(key), value, "required diagnostic detail " + key)
        if "diagnostic_span" in goal:
            wanted = goal["diagnostic_span"]
            start, end = wanted["start_byte"], wanted["end_byte"]
            if control_raw is not None:
                needle = raw[start:end]
                start = control_raw.find(needle)
                self.require(start >= 0 and control_raw.find(needle, start + 1) == -1,
                             "inherited control error span has one exact original role")
                end = start + len(needle)
            primary = actual.get("primary") or {}
            self.equal({key: primary.get(key) for key in ("source_id", "start_byte", "end_byte")},
                       {"source_id": wanted["source_id"], "start_byte": start, "end_byte": end},
                       "whole-call or inherited child primary span")

    def execution(self, actual, goal, *, membership=True, literal=False):
        self.equal(actual.get("stage_codes"), list(STAGES), "actual stage-code dictionary")
        self.equal(actual.get("unterminated_profile_frames"), 0, "complete helper call/return observation")
        events, calls = actual.get("events", []), actual.get("calls", [])
        previous = -1
        for stage, before in events:
            self.require(type(stage) is int and 0 <= stage < len(STAGES), "known stage code")
            self.require(type(before) is int and before >= previous, "monotone original cumulative counter")
            previous = before
        membership_calls = [c for c in calls if c["helper"] == "has_key"]
        concat_calls = [c for c in calls if c["helper"] == "concat_strings"]
        for call in membership_calls:
            steps = events[call["event_start"]:call["event_end"]]
            names = [STAGES[code] for code, counter in steps]
            keys, query = call["input_keys"], call["query"]
            self.require(type(keys) is list and len(keys) <= 256, "bounded source collection")
            self.equal(keys, sorted(keys), "canonical source keys")
            self.equal(len(keys), len(set(keys)), "unique source keys")
            self.equal(call["string_bytes_before"], call["string_bytes_after"], "membership reserves no String bytes")
            if call["returned_normally_typed"]:
                k = keys.index(query) + 1 if query in keys else len(keys)
                wanted = [MEMBERSHIP_STAGES[0]] + [MEMBERSHIP_STAGES[1]] * len(keys) + [MEMBERSHIP_STAGES[2]] + [MEMBERSHIP_STAGES[3]] * k + [MEMBERSHIP_STAGES[4]]
                self.equal(names, wanted, "complete actual n+k+3 source stage order")
                self.equal(call["operations_after"] - call["operations_before"], len(keys) + k + 3, "exact source-call dynamic debit")
                self.equal(call["result"], query in keys, "actual helper predicate on original admitted keys")
                self.equal([before for stage, before in steps], list(range(call["operations_before"], call["operations_after"])),
                           "no hidden source-call work or omitted tick")
        count = goal.get("expected_dynamic_membership_invocations", goal.get("expected_dynamic_invocations"))
        if count is not None and membership and not literal:
            self.equal(len(membership_calls), count, "frozen dynamic membership invocation count")
        if literal:
            self.equal(len(membership_calls), 0, "literal control has no .21 operation")
        if "expected_dynamic_concat_attempts" in goal and not literal:
            self.equal(len(concat_calls), goal["expected_dynamic_concat_attempts"], "inherited String dynamic invocation count")
        if "expected_string_concat_bytes" in goal and not literal:
            self.equal(actual.get("final_string_concat_bytes"), goal["expected_string_concat_bytes"], "unchanged inherited String reservation")
        for call in concat_calls:
            if not call["returned_normally_typed"]:
                continue
            left, right = call["left_utf8_bytes"], call["right_utf8_bytes"]
            total = left + right
            cost = 3 + (left + 63) // 64 + (right + 63) // 64 + (total + 63) // 64
            self.equal(call["operations_after"] - call["operations_before"], cost, "inherited String dynamic debit")
            self.equal(call["string_bytes_after"] - call["string_bytes_before"], total, "inherited String logical reservation")
            self.equal(call["result"]["utf8_bytes"], total, "inherited String result bytes")


_TOKEN = re.compile(rb'\s+|//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"|[A-Za-z_][A-Za-z0-9_]*|(?:[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?)|->|==|!=|<=|>=|.', re.DOTALL)


def tokens(raw, start, end):
    return [(m.group(), start + m.start(), start + m.end()) for m in _TOKEN.finditer(raw[start:end])
            if not m.group().isspace() and not m.group().startswith((b"//", b"/*"))]


def literal_type(name):
    if name == b"Length":
        return {"kind": "Quantity", "dimension": [1, 0, 0, 0], "element": None, "name": None}
    return {"kind": name.decode(), "dimension": None, "element": None, "name": None}


def original_origin(raw, wanted):
    """Parse only the finite original keyed-call roles declared in this freeze."""
    location = wanted["expression"]
    ts = tokens(raw, location["start_byte"], location["end_byte"])
    if ts[0][0].decode() != wanted["operator"] or ts[1][0] != b"<":
        raise ValueError("Frozen original operator role differs")
    generic_end = next(i for i, t in enumerate(ts) if t[0] == b">")
    types = [literal_type(t[0]) for t in ts[2:generic_end] if t[0] != b","]
    opening = generic_end + 1
    if ts[opening][0] != b"(" or ts[-1][0] != b")":
        raise ValueError("Malformed original ordinary operator call")
    args, start, stack = [], opening + 1, []
    for i in range(start, len(ts) - 1):
        token = ts[i][0]
        if token in (b"(", b"[", b"{"):
            stack.append(token)
        elif token in (b")", b"]", b"}"):
            stack.pop()
        elif token == b"," and not stack:
            args.append(ts[start:i]); start = i + 1
    args.append(ts[start:-1])
    loc = lambda part: {"source_id": "entry", "start_byte": part[0][1], "end_byte": part[-1][2]}
    body = lambda part: part[next(i for i, token in enumerate(part) if token[0] == b"->") + 1:]
    keyed_type = lambda part: literal_type(part[2][0])
    result = {"expression": {k: location[k] for k in ("source_id", "start_byte", "end_byte")}}
    family = wanted["family"]
    if family == "transforms":
        result.update(body=loc(body(args[1])), input=loc(args[0]), input_type=keyed_type(args[0]),
                      output_type=types[0], key=None, input_entry=None)
    elif family == "reductions":
        result.update(input=loc(args[0]), seed=loc(args[1]), body=loc(body(args[2])),
                      input_type=keyed_type(args[0]), accumulator_type=types[0])
    elif family == "filters":
        result.update(input=loc(args[0]), predicate=loc(body(args[1])), element_type=types[0])
    elif family == "merges":
        result.update(left=loc(args[0]), right=loc(args[1]), element_type=types[0], input_side="both")
    elif family == "zips":
        result.update(left=loc(args[0]), right=loc(args[1]), body=loc(body(args[2])),
                      left_type=types[0], right_type=types[1], output_type=types[2],
                      key=None, left_entry=None, right_entry=None)
    elif family == "rekeys":
        result.update(input=loc(args[0]), body=loc(body(args[1])), element_type=types[0],
                      old_key=None, new_key=None, input_entry=None)
    else:
        raise ValueError("Unknown frozen origin family")
    return result


def verify_sources(reader, root, mode):
    root = Path(root)
    summary = read(root / "summary.json")
    reader.case = "source-summary/" + mode
    reader.equal(summary.get("status"), "recorded", "complete source producer")
    reader.equal(summary.get("mode"), mode, "source execution mode")
    reader.equal(summary.get("full_cohort"), True, "full source/export cohort required")
    reader.equal(summary.get("source_unchanged"), True, "fixed source unchanged")
    reader.equal(summary.get("inputs_unchanged"), True, "frozen input unchanged")
    reader.equal(summary.get("internal_failures"), [], "producer internal errors")
    for name, value in reader.freeze.lineage().items():
        reader.equal(summary.get(name), value, "separately adopted " + name)
    if mode == "predecessor-controls":
        reader.equal(summary["source"]["commit"], PREDECESSOR_COMMIT, "exact predecessor control basis")
    expected = {}
    for original in reader.freeze.source["cases"]:
        if mode == "candidate":
            expected[original["id"]] = (original, "source", reader.freeze.root, original["files"])
        else:
            for control, files in original.get("controls", {}).items():
                expected[control + "-" + original["id"]] = (original, control, reader.freeze.root, files)
            if "predecessor-direct" in original.get("tags", []):
                expected[original["id"]] = (original, "source", reader.freeze.root, original["files"])
    for original in reader.freeze.representative["cases"]:
        if (original["mode"] == "source") == (mode == "candidate"):
            expected["agent-" + original["id"]] = (original, original["mode"], reader.freeze.root / "agent", original["files"])
    seen = set()
    provenance = {c["case_id"]: c for c in reader.freeze.provenance["cases"]}
    artifacts = []
    for record in jsonl_reader(root / "source-records.jsonl.gz"):
        ident = record.get("id"); reader.case = "source/" + str(ident)
        reader.require(ident in expected and ident not in seen, "exact unique source record inventory")
        if ident not in expected or ident in seen:
            continue
        seen.add(ident)
        original, control, inputs, files = expected[ident]
        representative = ident.startswith("agent-")
        goal = original if representative else original["expected"]
        manifest, revision = standalone_bundle_identity(inputs, files)
        reader.equal(record.get("program_revision"), revision, "actual immutable bundle revision")
        reader.equal(record.get("canonical_manifest"), manifest, "actual complete canonical manifest")
        reader.require("producer_exception" not in record, "no producer exception", record.get("producer_exception"))
        raw = (reader.freeze.root / original["source"]).read_bytes() if not representative else None
        control_raw = None
        if control != "source" and not representative:
            file_record = read(inputs / files)
            control_raw = (inputs / file_record["entry"]["path"]).read_bytes()
        for channel in ("public", "private"):
            result = record.get(channel, {})
            reader.equal(result.get("status"), goal["status"], channel + " source status")
            reader.execution(result.get("observation", {}), {**goal, **({"expected_dynamic_invocations": original["expected_dynamic_invocations"]} if "expected_dynamic_invocations" in original else {})},
                             membership=mode == "candidate" and control == "source", literal=control == "literal")
            if goal["status"] == "failed":
                diagnostics = result.get("result", {}).get("diagnostics", []) if channel == "public" else []
                if result.get("error", {}).get("diagnostic"):
                    diagnostics.append(result["error"]["diagnostic"])
                matches = [d for d in diagnostics if d.get("code") == goal["diagnostic_code"]]
                reader.require(len(matches) >= 1, channel + " expected error actually returned", diagnostics, goal["diagnostic_code"])
                if matches:
                    diagnostic = matches[0]
                    if channel == "private" and diagnostic.get("details") is None:
                        # C087 validator.fail passes details=None to the native
                        # constructor; its unchanged public Diagnostic.to_dict
                        # publishes that absence as {}. Source expectations use
                        # the public diagnostic representation. Native admission
                        # expectations below still compare their raw fields.
                        diagnostic = {**diagnostic, "details": {}}
                    reader.diagnostic(diagnostic, goal, raw=raw, control_raw=control_raw)
                continue
            if result.get("status") != "passed" or channel != "private":
                continue
            if not representative:
                reader.equal(result.get("observed"), goal["observed"], "independently frozen Boolean")
                reader.equal(result.get("known"), True, "result is known")
                reader.equal(result.get("observed_type"), literal_type(b"Bool"), "exact Bool type")
                if "width_m" in goal:
                    reader.equal(result.get("geometry"), {"kind": "box", "size": [goal["width_m"], 1, 1]}, "literal downstream geometry")
                elif "generated-view" in original.get("tags", []):
                    reader.equal(result.get("geometry"), {"kind": "empty"}, "generated view does not add geometry")
                reader.equal(result.get("warm_binding", {}).get("observed"), goal["observed"], "warm immutable binding Boolean")
                reader.equal(result.get("warm_binding", {}).get("provenance"), result.get("provenance"), "warm binding retains exact provenance")
                if mode == "candidate" and control == "source":
                    if "expected_member_dependencies" in original:
                        reader.equal(sorted(result["provenance"]["members"]), sorted(original["expected_member_dependencies"]), "true/false complete member dependencies")
                    if original["id"] in provenance:
                        wanted = {family: [] for family in ("transforms", "reductions", "filters", "merges", "zips", "rekeys")}
                        for origin in provenance[original["id"]]["required_origins"]:
                            wanted[origin["family"]].append(original_origin(raw, origin))
                        for family, values in wanted.items():
                            reader.equal(result["provenance"].get(family), values, "exact original detached " + family)
            else:
                reader.equal(result.get("generated_keys"), goal["generated_keys"], "exact surviving generated keys")
                reader.equal(result.get("property_names"), goal["property_names"], "complete exported property name order")
                for owner in ("first", "sibling"):
                    for field, key in (("overrides", "overrides"), ("override_flags", "flags"), ("selected", "selected")):
                        reader.equal(result["values"][owner + "." + field], goal[owner + "_" + key], "sparse " + owner + "." + field)
                reader.equal(set(result["geometry"]), set(goal["geometry"]), "complete panel/marker inventory")
                for path, wanted in goal["geometry"].items():
                    actual = result["geometry"][path]
                    for key in ("element_id", "corners_m", "triangles", "translation_samples_m", "box_size_m"):
                        if key in wanted:
                            reader.equal(actual.get(key), wanted[key], path + "." + key)
                    reader.equal(actual["quaternion_samples_wxyz"], [wanted["quaternion_wxyz"]] * 5, path + " exact rotation samples")
                    if "regions" in actual:
                        reader.equal(set(actual["regions"]), {"bottom", "side", "top"}, path + " material regions")
                        for region, material in actual["regions"].items():
                            reader.equal(material, {"color": wanted["side_color"] if region == "side" else wanted["cap_color"], "metallic": wanted["metallic"], "roughness": wanted["roughness"]}, path + " exact PBR")
                        for uv in actual["top_uv_rows"]:
                            x, y, z = uv["position"]
                            reader.equal(uv["uv"], [0.5 * x, 1 - 0.5 * y], path + " literal UV formula")
                reader.equal(result["texture_sha256"], {"label": reader.freeze.representative["texture"]["sha256"]}, "original pinned PNG bytes")
        if representative and goal["status"] == "passed":
            exported = record.get("export", {})
            reader.equal(exported.get("has_bytes"), True, "actual verified native artifact bytes")
            if exported.get("path"):
                path = root / exported["path"]
                raw_artifact = path.read_bytes()
                reader.equal(len(raw_artifact), exported["bytes"], "artifact full length")
                reader.equal(sha(raw_artifact), exported["sha256"], "artifact full SHA256")
                artifacts.append({"role": original["id"], "root": str(root), **exported})
    reader.case = "source-inventory/" + mode
    reader.equal(seen, set(expected), "complete frozen source/control record inventory")
    return artifacts


def verify_native(reader, root):
    root = Path(root)
    summary = read(root / "summary.json")
    reader.case = "native-summary"
    reader.equal(summary.get("status"), "recorded", "complete native producer")
    reader.equal(summary.get("full_cohort"), True, "full native/resource/abstract cohort")
    reader.equal(summary.get("source_unchanged"), True, "native fixed source unchanged")
    reader.equal(summary.get("inputs_unchanged"), True, "native frozen inputs unchanged")
    for name, value in reader.freeze.lineage().items():
        reader.equal(summary.get(name), value, "separately adopted " + name)
    wanted = {}
    for case in reader.freeze.native["cases"]: wanted["native/" + case["id"]] = ("negative", case)
    for case in reader.freeze.native["valid_metadata_cases"]: wanted["valid/" + case["id"]] = ("valid", case)
    for case in reader.freeze.native["callback_mutation_cases"]: wanted["capture/" + case["id"]] = ("capture", case)
    for case in reader.freeze.native["missing_context_variants"]: wanted["context/" + case["id"]] = ("context", case)
    for case in reader.freeze.native["unknown_abstract_cases"]: wanted["abstract/" + case["id"]] = ("abstract", case)
    for schedule in reader.freeze.resource["cases"]:
        for cap in schedule["operation_caps"]:
            wanted[f"cap/{schedule['id']}/{cap['available']}"] = ("cap", (schedule, cap))
        for seam in schedule["interruptions"]:
            for mode in ("cancel", "deadline", "cancel-cap-deadline", "cap-deadline"):
                wanted[f"{mode}/{schedule['id']}/{seam['before_step']}"] = (mode, (schedule, seam))
    wanted["precedence/expired-before-semantic-key-error"] = ("query-deadline", None)
    seen = set()
    for row in jsonl_reader(root / "native-records.jsonl.gz"):
        ident = row.get("id"); reader.case = "native/" + str(ident)
        reader.require(ident in wanted and ident not in seen, "exact unique native observation inventory")
        if ident not in wanted or ident in seen:
            continue
        seen.add(ident)
        kind, spec = wanted[ident]
        diagnostic = row.get("error", {}).get("diagnostic", {})
        if kind == "context":
            goal = spec["expected"]
            reader.equal(row["status"], "raised", "missing context refuses")
            for key in ("code", "phase", "message", "details"):
                reader.equal(diagnostic.get(key), goal[key], "missing context " + key)
            reader.equal(row["operations_after"], row["operations_before"], "missing context pays no dynamic operation")
            continue
        if kind == "abstract":
            reader.equal(row["events"], [], "abstract/unknown does no dynamic membership stage")
            if "expected_code" in spec:
                reader.equal(row["status"], "raised", "abstract signature still refuses")
                reader.equal(diagnostic.get("code"), spec["expected_code"], "abstract type diagnostic")
                reader.equal(diagnostic.get("message"), spec["expected_message"], "abstract type message")
            else:
                reader.equal(row["status"], "returned", "abstract returns typed unknown")
                reader.equal(row["result_type"], spec["expected_type"], "abstract Bool type")
                reader.equal(row["result_known"], spec["expected_known"], "abstract unknownness")
            continue
        reader.equal(row.get("header_operations"), 14, "actual fresh original header admission")
        reader.equal(row.get("operations_before"), 14, "no counter preloading after header")
        reader.equal(row.get("stage_before"), "execution", "original stage before helper")
        reader.equal(row.get("stage_after"), "execution", "finally restores original stage")
        reader.equal(row.get("original_started"), row.get("final_started"), "original clock start is retained")
        reader.equal(row.get("string_bytes_before"), 0, "initial native String reservation")
        reader.equal(row.get("string_bytes_after"), 0, "native membership never reserves String bytes")
        reader.equal(row.get("foreign_methods_called"), [], "no foreign equality/hash/string/payload method")
        reader.equal(row.get("stage_codes"), list(MEMBERSHIP_STAGES), "exact five native stage names")
        local = row["operations_after"] - 14
        events = row["events"]
        stages = [MEMBERSHIP_STAGES[i] for i, before in events]
        before_counters = [before for stage, before in events]
        if kind == "negative":
            goal = spec["expected"]
            reader.equal(row["status"], "raised", "malformed native input refuses")
            for key in ("code", "phase", "message", "details", "category", "related"):
                if key in goal:
                    reader.equal(diagnostic.get(key), goal[key], "native diagnostic " + key)
            ticks = goal["successful_dynamic_ticks_through_failure"]
            reader.equal(local, ticks, "paid prefix before semantic refusal")
            reader.equal(len(events), ticks, "semantic refusal has no hidden or omitted dynamic stages")
            reader.equal(before_counters, list(range(14, 14 + ticks)), "native semantic prefix counters")
            reader.require(MEMBERSHIP_STAGES[4] not in stages, "malformed input never reaches publication")
        elif kind in ("valid", "capture"):
            reader.equal(row["status"], "returned", "native known valid result")
            reader.equal(row["result_native_type"], "bool", "native exact Bool payload")
            reader.equal(row["result"], spec["expected"], "frozen native result")
            reader.equal(local, spec["operations"], "native exact dynamic cost")
            n = len(spec.get("keys", ["a"]))
            k = spec.get("keys", ["a"]).index(spec["query"]) + 1 if spec["query"] in spec.get("keys", ["a"]) else n
            order = [MEMBERSHIP_STAGES[0]] + [MEMBERSHIP_STAGES[1]] * n + [MEMBERSHIP_STAGES[2]] + [MEMBERSHIP_STAGES[3]] * k + [MEMBERSHIP_STAGES[4]]
            reader.equal(stages, order, "native complete stage order")
            reader.equal(before_counters, list(range(14, 14 + local)), "native complete counters")
            if kind == "capture":
                reader.equal(row["mutations"], [{"stage": spec["mutation_before_stage"], "case": spec["id"]}], "frozen callback mutation actually ran")
        elif kind == "cap":
            schedule, cap = spec
            count = schedule["operations"] if cap["success"] else cap["available"] + 1
            reader.equal(stages, [s["phase"] for s in schedule["stages"][:count]], "operation cap exact attempted prefix")
            reader.equal(local, count, "operation cap actual consumed counter")
            reader.equal(before_counters, list(range(14, 14 + count)), "operation cap before-tick counters")
            if cap["success"]:
                reader.equal(row["status"], "returned", "exact successful cap")
                reader.equal(row["result"], schedule["expected"], "successful cap Boolean")
            else:
                reader.equal(row["status"], "raised", "insufficient cap refuses")
                reader.equal(diagnostic.get("code"), "OKL-E-RESOURCE", "cap resource diagnostic")
                reader.equal(diagnostic.get("details", {}).get("budget_reason"), "operation_budget_exhausted", "cap refusal reason")
                reader.equal(diagnostic.get("details", {}).get("consumed"), 14 + count, "cap total consumed prefix")
                reader.equal(diagnostic.get("details", {}).get("limit"), 14 + cap["available"], "actual caller cap")
        else:
            if kind == "query-deadline":
                step, order = 2, [MEMBERSHIP_STAGES[0], MEMBERSHIP_STAGES[2]]
            else:
                schedule, seam = spec
                step = seam["before_step"]
                order = [s["phase"] for s in schedule["stages"][:step]]
            cancelled = kind in ("cancel", "cancel-cap-deadline")
            reader.equal(row["status"], "raised", "interruption prevents publication")
            reader.equal(stages, order, "interruption exact attempted prefix")
            reader.equal(before_counters, list(range(14, 14 + step)), "interruption original counters")
            reader.equal(local, step - 1 if cancelled else step, "callback-before-cap-before-deadline debit order")
            if cancelled:
                reader.equal(row.get("same_original_cancellation"), True, "original cancellation object preserved")
                reader.equal(row.get("same_ledger_callback_error"), True, "original callback error identity preserved")
                reader.equal(row.get("error", {}).get("exception"), "OriginalCancellation", "cancellation is not relabeled")
            else:
                reason = "operation_budget_exhausted" if kind == "cap-deadline" else "execution_deadline_exceeded"
                reader.equal(diagnostic.get("code"), "OKL-E-RESOURCE", "interruption resource code")
                reader.equal(diagnostic.get("details", {}).get("budget_reason"), reason, "interruption precedence")
                reader.equal(diagnostic.get("details", {}).get("stage"), order[-1], "original interrupted stage")
    reader.case = "native-inventory"
    reader.equal(seen, set(wanted), "complete frozen native/resource/abstract inventory")
    return len(seen)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--inputs", type=Path, required=True)
    p.add_argument("--source", type=Path)
    p.add_argument("--controls", type=Path)
    p.add_argument("--candidate-controls", type=Path)
    p.add_argument("--native", type=Path)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    roots = [r.resolve() for r in (a.source, a.controls, a.candidate_controls, a.native) if r is not None]
    if not roots:
        p.error("at least one observed evidence root is required")
    a.output.mkdir(parents=True, exist_ok=False)
    freeze = Freeze(a.inputs)
    reader = Reader(freeze)
    before = {str(r): inventory(r) for r in roots}
    save(a.output / "artifacts-before.json", before)
    report = {"schema_version": "ontokin.c088-independent-observation-reader/1", **freeze.lineage(),
              "started_utc": stamp(), "stdlib_only": True, "production_imports": False,
              "full_source_native_cohort": all((a.source, a.controls, a.candidate_controls, a.native)),
              "release_acceptance": False, "artifacts": []}
    try:
        if a.source: report["artifacts"] += verify_sources(reader, a.source, "candidate")
        if a.controls: report["artifacts"] += verify_sources(reader, a.controls, "predecessor-controls")
        if a.candidate_controls: report["artifacts"] += verify_sources(reader, a.candidate_controls, "candidate-controls")
        if a.controls and a.candidate_controls:
            original = {item["role"]: item for item in read(a.controls / "summary.json")["artifacts"]}
            candidate = {item["role"]: item for item in read(a.candidate_controls / "summary.json")["artifacts"]}
            reader.case = "exact-predecessor-control-artifacts"
            reader.equal(set(candidate), set(original), "all fourteen .20 control artifact roles on both fixed cuts")
            for role in original:
                reader.case = "exact-predecessor-control-artifact/" + role
                if role in candidate:
                    reader.equal((a.controls / original[role]["path"]).read_bytes(),
                                 (a.candidate_controls / candidate[role]["path"]).read_bytes(),
                                 "complete unchanged .20 GLB bytes between exact C087 and candidate")
        if a.native: report["native_record_count"] = verify_native(reader, a.native)
    except Exception as error:
        reader.failures.append({"case": reader.case, "check": "reader exception", "exception": type(error).__name__, "message": str(error)})
    after = {str(r): inventory(r) for r in roots}
    save(a.output / "artifacts-after.json", after)
    reader.case = "read-only-proof"
    reader.equal(before, after, "complete supplied evidence bytes and modes unchanged")
    freeze.assert_unchanged()
    report.update(finished_utc=stamp(), checks=reader.checks, failures=reader.failures,
                  artifact_inventories_unchanged=before == after,
                  status="passed" if not reader.failures else "failed")
    save(a.output / "result.json", report)
    print(json.dumps({"status": report["status"], "checks": reader.checks,
                      "failures": len(reader.failures), "output": str(a.output)}))
    return 0 if not reader.failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
