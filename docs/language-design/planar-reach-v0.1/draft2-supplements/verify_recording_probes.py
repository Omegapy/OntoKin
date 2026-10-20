"""NEW independent exact-arithmetic check of the recovered Q16 preparation.

The original probe record remains verbatim, including references to lost old
acceptance files. This checks clocks, source closure and that historical/new
distinction. It does not claim to build a GLB or execute the future mutation.
"""
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROPOSAL = HERE.parent


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def sha(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def fraction(record):
    numerator, denominator = int(record["numerator"]), int(record["denominator"])
    result = Q(numerator, denominator)
    require((result.numerator, result.denominator) == (numerator, denominator), "reduced rational required")
    return result


def ieee(bits, width):
    """Decode finite positive IEEE bits with integers; no floating conversion."""
    mantissa_width, exponent_width, bias = (23, 8, 127) if width == 32 else (52, 11, 1023)
    require(bits >> (width - 1) == 0, "positive time bits")
    exponent = (bits >> mantissa_width) & ((1 << exponent_width) - 1)
    require(exponent != (1 << exponent_width) - 1, "finite time bits")
    mantissa = bits & ((1 << mantissa_width) - 1)
    if exponent:
        mantissa += 1 << mantissa_width
    power = (exponent or 1) - bias - mantissa_width
    return Q(mantissa * (2 ** power)) if power >= 0 else Q(mantissa, 2 ** (-power))


def nearest_cell(value, bits, width):
    center = ieee(bits, width)
    left = (ieee(bits - 1, width) + center) / 2
    right = (center + ieee(bits + 1, width)) / 2
    require(left <= value <= right, "value outside nearest rounding cell")
    require(bits % 2 == 0 or value not in (left, right), "nearest tie must select even")


def stored(record, source):
    require(record["rounding"] == "direct_exact_rational_to_binary32_nearest_ties_even", "direct rational rounding rule")
    bits = int(record["bits_hex"], 16)
    value = ieee(bits, 32)
    require(fraction(record["time"]) == Q(record["time_seconds"]) == value, "stored clock exact agreement")
    nearest_cell(source, bits, 32)
    require(fraction(record["stored_minus_source"]) == value - source, "exact recorded time shift")
    return value


def main():
    raw = (HERE / "recording-probes.json").read_bytes()
    require(len(raw) == 10932 and sha(raw) == "sha256:cf50015e6c7e46833ede254963806fa28aa4b9f3cc9939234799bfdf043e7123", "exact recovered probe bytes")
    record = json.loads(raw)
    probe = record["probes"][0]
    require(len(record["probes"]) == 1 and probe["id"] == "Q16", "one retained Q16 probe")
    require(record["status"] == "expected_preparation_not_executed" and not record["source_and_agent_execution"] and not record["glb_generated_or_validated"], "no historical execution claim")
    source = (HERE / probe["entry_source"]).read_bytes()
    require(sha(source) == probe["source_sha256"] and len(source) == probe["source_bytes"] == 1114, "exact Q16 entry identity")
    l01 = (HERE / "sources/l01-both-moving-pause-resume.ok").read_bytes()
    require(source == l01.replace(b"at 0.5[s]", b"at 0.50000002[s]").replace(b"at 1.5[s]", b"at 1.50000002[s]"), "only two source event-time literals differ")
    fmraw = (HERE / probe["file_manifest"]).read_bytes()
    require(sha(fmraw) == probe["file_manifest_sha256"] and len(fmraw) == 657, "exact Q16 transport manifest")
    files = json.loads(fmraw)
    l01files = json.loads((HERE / "l01.files.json").read_bytes())
    l01files["entry"]["path"] = probe["entry_source"]
    require(files == l01files, "Q16 manifest changes only entry path")
    units = []
    for index, unit in enumerate([files["entry"], *files["modules"]]):
        path = Path(unit["path"])
        require(not path.is_absolute() and ".." not in path.parts and (HERE / path).resolve().is_relative_to(HERE.resolve()), "manifest local closure")
        units.append({"filename":unit["filename"], "source_id":"entry" if index == 0 else "package:" + unit["package_id"] + "@" + unit["version"],
                      "source_revision":sha((HERE / path).read_bytes()), "package_id":unit.get("package_id"), "version":unit.get("version")})
    units.sort(key=lambda unit:unit["source_id"])
    require(units == probe["source_units"], "exact recorded source units")
    manifest = {"schema_version":"ontokin.bundle/0.1","entry_source_id":"entry","units":units}
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    require(sha(b"ontokin.bundle/0.1\0" + canonical) == probe["program_revision"], "exact Q16 program revision")
    events = {}
    for event in probe["only_source_changes"]:
        bits = int(event["canonical_binary64_bits_hex"],16)
        clock = ieee(bits,64)
        nearest_cell(Q(event["source_literal_seconds"]),bits,64)
        require(fraction(event["source_time"]) == Q(event["source_time_seconds"]) == clock, "canonical source event clock")
        stored_clock = stored(event["stored_binary32"],clock)
        require(stored_clock < clock, "event clock rounds down")
        events[event["event"]] = (clock,stored_clock)
    pause, stored_pause = events["pause"]
    resume, stored_resume = events["resume"]
    completion = Q(2) + resume - pause
    require(completion == Q(3) + Q(1,2**53), "completion is exactly 3 + 2^-53")
    require(fraction(probe["completion"]["source_time"]) == Q(probe["completion"]["source_time_seconds"]) == completion, "computed clock never rounded back to binary64")
    require(fraction(probe["completion"]["source_minus_three"]) == Q(1,2**53), "exact completion offset")
    require(stored(probe["completion"]["stored_binary32"],completion) == 3, "direct binary32 completion")
    expected_phases = [(0,pause,"running"),(pause,resume,"paused"),(resume,completion,"running"),(completion,Q(4),"completed")]
    require(len(probe["source_phases"]) == 4, "four source phases")
    for index,(phase,expected) in enumerate(zip(probe["source_phases"],expected_phases)):
        require(phase["index"] == index and (fraction(phase["start"]),fraction(phase["end"]),phase["lifecycle"]) == expected, "exact source phase partition")
    witness=probe["phase_coverage_witness"]
    authored = list(map(fraction,witness["authored_interval"]))
    stored_interval = list(map(fraction,witness["stored_interval"]))
    enclosing = list(map(fraction,witness["enclosing_interval"]))
    require(authored == [pause,Q(1)] and stored_interval == [stored_pause,Q(1)], "fixed witness intervals")
    require(enclosing == [min(authored[0],stored_interval[0]),max(authored[1],stored_interval[1])], "clock enclosure")
    overlap = max(Q(0),min(pause,enclosing[1])-max(Q(0),enclosing[0]))
    require(overlap == fraction(witness["incoming_moving_overlap_seconds"]) > 0, "positive neighboring moving phase overlap")
    require(witness["required_source_phase_indices"] == [0,1], "incoming phase cannot be omitted")
    original = json.loads((PROPOSAL / "acceptance.json").read_bytes())
    a = next(c for c in original["source_cases"] if c["id"] == "P16")["expected"]["independent_solution"]["resolved_joint_targets_rad"]
    require(witness["incoming_joint_rates_rad_per_s"] == [x/2 for x in a] and all(witness["incoming_joint_rates_rad_per_s"]), "both incoming joints move")
    require(probe["future_artifact_probe"]["execution_status"] == "not_executed", "future artifact probe still pending")
    provenance=json.loads((HERE/"reconstruction.json").read_bytes())
    lost={item["path"]:item for item in provenance["historical_lost_files"]}
    historical=0
    for base in record["base_inputs"]:
        if base["path"] in lost:
            historical+=1
            old=lost[base["path"]]
            require((base["bytes"],base["sha256"]) == (old["bytes"],old["sha256"]), "historical reference retained exactly")
            require(sha((HERE/base["path"]).read_bytes()) != base["sha256"] and not old["contents_recovered"], "new acceptance not relabeled as recovered old input")
        else:
            rawbase=(HERE/base["path"]).read_bytes()
            require(len(rawbase)==base["bytes"] and sha(rawbase)==base["sha256"], "exact available historical base input")
    require(historical == 3, "three lost historical file references remain explicit")
    binding = json.loads((HERE / "effective-recording-probes.json").read_bytes())
    require(binding["effective_probe"] == probe, "effective Q16 source, clocks, phases and mutation unchanged")
    require(binding["historical_record"] == {"path":"recording-probes.json","bytes":len(raw),"sha256":sha(raw)}, "effective binding pins exact historical record")
    require(len(binding["input_rebindings"]) == len(record["base_inputs"]), "all historical inputs explicitly rebound")
    changed = 0
    for old, pair in zip(record["base_inputs"], binding["input_rebindings"]):
        require(pair["historical_input"] == old, "old input identity preserved in binding")
        new = pair["effective_input"]
        current_bytes = (HERE / new["path"]).read_bytes()
        require(sha(current_bytes) == new["sha256"] and len(current_bytes) == new["bytes"], "effective input exact current identity")
        unchanged = old["sha256"] == new["sha256"]
        require(pair["identity_unchanged"] is unchanged, "honest old/new equality flag")
        changed += not unchanged
        if old["path"] == "generated-members.json":
            require(new["path"] == "recording-probe-inputs.json", "noncircular effective closure replacement")
    require(changed == 3, "three lost inputs explicitly replaced")
    input_closure = json.loads((HERE / "recording-probe-inputs.json").read_bytes())
    for item in input_closure["members"] + input_closure["authoring_inputs"]:
        content = (HERE / item["path"]).read_bytes()
        require(sha(content) == item["sha256"] and len(content) == item["bytes"], "effective closure member exact identity")
    target_reference = binding["effective_target_solution_reference"]
    require(target_reference["case_id"] == "P16" and target_reference["sha256"] == sha((PROPOSAL / "acceptance.json").read_bytes()), "effective independent target reference")
    print(json.dumps({"status":"passed","scope":"exact recovered Q16 inputs and pure clock mathematics; future GLB mutation not executed",
        "completion_exact":"3 + 2^-53","positive_incoming_overlap":witness["incoming_moving_overlap_seconds"],
        "historical_lost_references":3,"explicit_effective_rebindings":3,"effective_probe_unchanged":True,
        "source_runtime_executed":False,"agent_sqlite_executed":False,"glb_or_destination_executed":False},sort_keys=True))


if __name__ == "__main__":
    main()
