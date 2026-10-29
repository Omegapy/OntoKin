#!/usr/bin/env python3
"""Source-derived C062 ceiling from frozen C061 evidence; no product imports.

This checks bytes and performs an offline census. The LRU argument and the
source-expansion census are documented premises, not runtime measurements.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import struct
import zipfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    if not __debug__:
        raise SystemExit("Run without -O; the offline verifier requires assertions.")
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint", type=Path)
    args = parser.parse_args()
    root = args.checkpoint
    manifest_bytes = (root / "evidence-manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    parts = []
    for row in manifest["parts"]:
        raw = (root / row["path"]).read_bytes()
        assert len(raw) == row["bytes"] and digest(raw) == row["sha256"]
        parts.append(raw)
    archive_bytes = b"".join(parts)
    assert len(archive_bytes) == manifest["archive"]["bytes"]
    assert digest(archive_bytes) == manifest["archive"]["sha256"]
    members = {row["path"]: row for row in manifest["members"]}
    verified = {}
    z = zipfile.ZipFile(io.BytesIO(archive_bytes))

    def read(name):
        raw = z.read(name)
        row = members[name]
        assert len(raw) == row["bytes"] and digest(raw) == row["sha256"], name
        verified[name] = {"bytes": len(raw), "sha256": digest(raw)}
        return raw

    def js(name):
        return json.loads(read(name))

    source_prefix = "source/docs/language-design/planar-reach-v0.1/"
    lib_hashes = {
        "libraries/reach-assets.ok": "6551d3dd5a772e85e92547d71db081e6ae7c21a0f3d57424b01c64a18191d6ba",
        "libraries/reach-parts.ok": "aa04a78696122cd18def6993b1056971f8990a21e8617b3ee73ca98be9b9b0cb",
        "libraries/reach-exterior.ok": "3b94fc91ca96f8fb0b21a90a1d6b4d78cdbd19600383a10cb6a3646ba67af763",
    }
    for path, expected in lib_hashes.items():
        raw = read(source_prefix + path)
        assert digest(raw) == expected
        assert re.search(rb"\bgrip\b", raw) is None
    for path in ("ontokin/reach_reference.py", "ontokin/reach_reference_plan.py",
                 "ontokin/reach_reference_center.py", "ontokin/reach_conformance.py",
                 "ontokin/reach_numeric.py", "ontokin/construction.py",
                 "tools/capture_reach_reader_setup.py"):
        read("source/" + path)

    limbs = [f'rig.arms["{key}"]' for key in ("left", "right")]
    limbs += [f'rig.legs["{key}"]' for key in ("left", "middle", "right")]
    eyes = [f'rig.head.eyes["{key}"]' for key in ("brow", "left", "right")]
    cases = {
        "P11": {
            "objects": ["rig", "rig.head", *eyes,
                        *(name + suffix for name in limbs for suffix in ("", ".upper", ".forearm"))],
            "joints": ["rig.look", *(name + suffix for name in limbs for suffix in (".shoulder", ".elbow"))],
            "follows": [name + ".mounting" for name in (*limbs, *eyes)],
            "calls": 60, "visits": 171, "future_keys": 15, "future_rows": 320,
            "entry_source": "sources/p11-complete-segmented-character.ok",
            "entry_sha256": "9e58d517ad21f6838247096ced3983188b6820b3a7f94d2bb7ac8ace8b77146a",
        },
        "L03": {
            "objects": ["rig", "rig.column", "rig.arm", "rig.arm.upper", "rig.arm.forearm", "rig.tool"],
            "joints": ["rig.arm.shoulder", "rig.arm.elbow"],
            "follows": ["rig.column_mount", "rig.arm.mounting", "rig.tool_mount"],
            "calls": 24, "visits": 68, "future_keys": 24, "future_rows": 150,
            "entry_source": "draft2-supplements/sources/l03-completed-action-new-owner.ok",
            "entry_sha256": "a57e8513d93cc4dd5b8998bd4119b9b534c7b6c1faf06574a8d88ceb99e11736",
        },
    }
    results = {}
    for case, expected in cases.items():
        entry = read(source_prefix + expected["entry_source"])
        assert digest(entry) == expected["entry_sha256"]
        assert re.search(rb"\b(release|grip)\b", entry) is None
        prefix = f"evidence/round-001/{case}/capture/"
        capture = js(prefix + "capture.json")
        setup = js(prefix + "reader-setup.json")
        keys = js(prefix + "key-ledger.json")
        ledger = js(f"evidence/round-001/{case}/audit-001/work-ledger.json")
        callbacks = capture["callbacks"]
        assert callbacks["external"] == {"module": "ontokin.construction", "qualname": "ConstructionBudget.tick", "bound_owner_type": "ConstructionBudget"}
        assert callbacks["construction_check"] is None
        assert callbacks["observer_at_reader_entry"] is None
        assert callbacks["observer_after_request"] is None
        assert capture["work_limits"]["max_operand_bits"] == 32768
        assert capture["shared_operations_after_request"] == 100001
        rows = [r for r in setup["spans"] if r["label"] == "reference._phase"]
        assert len(rows) == expected["calls"]
        assert all(first["exit"]["shared_operations"] <= last["entry"]["shared_operations"]
                   for first, last in zip(rows, rows[1:]))
        frames = {name + ".frame" for name in expected["objects"]}
        relations = set(expected["joints"]) | set(expected["follows"])
        visits = 0
        for row in rows:
            assert row["outcome"] == "returned" and not row["clipped_at_first_key"]
            assert row["input"]["arithmetic_bits"] == 128 and row["input"]["operand_limit_field"] == 32768
            path = row["result"]["path"]
            assert path["type"] == "tuple" and all(x["type"] == "str" for x in path["items"])
            path = [x["value"] for x in path["items"]]
            assert path[0] == row["input"]["carrier"] and path[-1] == "rig.frame"
            assert len(path) % 2 == 1
            assert all(x in frames for x in path[::2])
            assert all(x in relations for x in path[1::2])
            assert len(path[::2]) == len(set(path[::2]))
            visits += len(path[::2])
        assert visits == expected["visits"]

        # The retained GLB is corroboration only; it is still an unvalidated
        # reader input and is not the authority for the source expansion above.
        raw = read(prefix + "unvalidated-reader-input.glb")
        assert raw[:4] == b"glTF"
        size, kind = struct.unpack_from("<II", raw, 12)
        assert kind == 0x4E4F534A
        doc = json.loads(raw[20:20 + size])
        observed_objects = [node["extras"]["ontokin"]["path"] for node in doc["nodes"]
                            if node["extras"]["ontokin"]["kind"] == "object"]
        assert set(observed_objects) == set(expected["objects"])
        meta = doc["extras"]["ontokin"]
        assert len(meta["joints"]) == len(expected["joints"])
        assert len(meta["follows"]) == len(expected["follows"])
        key_count = len(doc["animations"][0]["extras"]["ontokin"]["exact_times_seconds"])
        assert {row["frame"] for row in keys["geometry"]} == frames
        assert len(keys["geometry"]) == len(frames)
        assert len(keys["keys"]) == ledger["entered_keys"]
        assert all(row["outcome"] == "returned" for row in keys["keys"][:-1])
        assert keys["keys"][-1]["outcome"] == "raised"
        assert [row["index"] for row in keys["keys"]] == list(range(len(keys["keys"])))
        assert ledger["returned_provisional_keys"] == len(keys["keys"]) - 1
        unvisited = key_count - ledger["entered_keys"]
        remaining_rows = (key_count - ledger["returned_provisional_keys"]) * len(frames)
        assert unvisited == expected["future_keys"] == len(ledger["unvisited_key_indices"])
        assert remaining_rows == expected["future_rows"] == ledger["interval_rows_not_yet_traversed"]
        assert ledger["provisional_interval_rows_traversed"] + remaining_rows == (key_count - 1) * len(frames)
        assert ledger["source_batch_finalized_at_refusal"] is False

        interval = rows[-1]["exit"]["shared_operations"] - rows[0]["entry"]["shared_operations"]
        cold_extra = len(relations) + 1
        all_miss_ceiling = visits + len(rows) + len(rows) * cold_extra
        # This arithmetic requires the reviewed original-domain LRU premise:
        # a fixed key, no resets, one charge for each later promotion/insertion,
        # no deferred precharged writer entering this setup call graph. It does
        # not claim to have observed any particular cache hit or miss.
        lru_miss_ceiling = min(len(rows), 1 + interval // 256)
        lru_ceiling = visits + len(rows) + lru_miss_ceiling * cold_extra
        chosen_ceiling = lru_ceiling if case == "P11" else all_miss_ceiling
        future = expected["future_keys"] * len(frames) + 3 * expected["future_rows"]
        results[case] = {
            "phase_calls": len(rows), "source_derived_object_visits": visits,
            "objects": len(frames), "joints": len(expected["joints"]), "follows": len(expected["follows"]),
            "grips": 0, "phase_entry_to_final_exit_charges": interval,
            "sum_measured_whole_phase_bodies": sum(r["exit"]["shared_operations"] - r["entry"]["shared_operations"] for r in rows),
            "incoming_base_lookup_charges": len(rows), "extra_charges_per_incoming_miss": cold_extra,
            "all_incoming_calls_miss_target_ceiling": all_miss_ceiling,
            "conservative_lru_miss_ceiling": lru_miss_ceiling,
            "conservative_lru_target_ceiling": lru_ceiling,
            "selected_whole_ancestry_target_ceiling": chosen_ceiling,
            "mandatory_future_wholly_unvisited_key_ticks": expected["future_keys"] * len(frames),
            "mandatory_future_interval_row_ticks": 3 * expected["future_rows"],
            "mandatory_future_selected_ticks": future,
            "conditional_necessary_work_lower_bound": 100000 - chosen_ceiling + future,
            "source_expansion_objects": expected["objects"],
            "source_expansion_joints": expected["joints"],
            "source_expansion_follows": expected["follows"],
        }
    print(json.dumps({
        "schema_version": "ontokin.c062-offline-ancestry-ceiling/0.1",
        "status": "calculation_passed_conditional_screen",
        "executed_source_commit": "bd5a09618c123a0b1d3339df3a944cfd6ed63b56",
        "c061_archive_sha256": digest(archive_bytes),
        "manifest_sha256": digest(manifest_bytes),
        "product_requests_executed": 0,
        "new_ancestry_measurements": False,
        "cache_misses_observed": False,
        "runtime_optimization_selected": False,
        "bound_condition": "Exact setup outputs and unchanged downstream control paths, charges, source admission and cache effects; original native callback/cap behavior. Free removal of entire target is a deliberately optimistic bound.",
        "source_expansion_note": "Explicit manual expansion of the pinned native .ok definitions, checked against every retained ReferencePhase.path and corroborated by retained unvalidated GLB metadata. No compiler or product runtime imported.",
        "results": results,
        "verified_inputs": verified,
    }, indent=2))


if __name__ == "__main__":
    main()
