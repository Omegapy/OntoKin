"""Independent pure checks of NEW lifecycle/protocol reconstruction.

Uses explicit case equations, exact rounding cells and independent stdlib FK.
Does not import the author scripts, original oracle, or any OntoKin runtime.
No source/Agent/export execution or release acceptance is established here.
"""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
from fractions import Fraction as Q
import struct
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
PROPOSAL = HERE.parent


def require(condition, label):
    if not condition:
        raise AssertionError(label)


def sha(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def read(name):
    return json.loads((HERE / name).read_bytes())


def q(value):
    return Q(int(value["numerator"]), int(value["denominator"]))


def rounded(value, exact, label):
    """Verify membership in the binary64 nearest/even cell, not float(exact)."""
    require(type(value) in (int, float) and math.isfinite(value), label + " finite")
    value = float(value)
    if exact == 0:
        require(value == 0 and math.copysign(1, value) == 1, label + " canonical zero")
        return
    center = Q.from_float(value)
    left = (Q.from_float(math.nextafter(value, -math.inf)) + center) / 2
    right = (center + Q.from_float(math.nextafter(value, math.inf))) / 2
    even = struct.unpack(">Q", struct.pack(">d", value))[0] % 2 == 0
    require(left <= exact <= right and (even or exact not in (left, right)), label + " correct rounding")


def vector_close(actual, expected, label, tolerance=2e-12):
    require(len(actual) == len(expected), label + " dimensions")
    require(all(math.isfinite(x) and abs(x-y) <= tolerance for x,y in zip(actual, expected)), label)


def fk(coordinates, rates):
    a, b = coordinates
    da, db = rates
    elbow = [math.cos(a), math.sin(a), 0.0]
    tip = [elbow[0] + math.cos(a+b), elbow[1] + math.sin(a+b), 0.0]
    rotation = [math.cos((a+b)/2), 0.0, 0.0, math.sin((a+b)/2)]
    if next(v for v in rotation if v != 0) < 0:
        rotation = [-v if v != 0 else 0.0 for v in rotation]
    return {"tip": tip, "elbow": elbow, "rotation": rotation,
            "velocity": [-math.sin(a)*da - math.sin(a+b)*(da+db), math.cos(a)*da + math.cos(a+b)*(da+db), 0.0],
            "omega": [0.0, 0.0, da+db]}


def closure(files):
    paths = [files["entry"], *files["modules"]]
    units = []
    for n, item in enumerate(paths):
        relative = Path(item["path"])
        require(not relative.is_absolute() and ".." not in relative.parts, "manifest local containment")
        path = HERE / relative
        require(path.resolve().is_relative_to(HERE.resolve()), "manifest symlink containment")
        package = item.get("package_id")
        version = item.get("version")
        units.append({"filename": item["filename"], "source_id": "entry" if n == 0 else "package:" + package + "@" + version,
                      "source_revision": sha(path.read_bytes()), "package_id": package, "version": version})
    manifest = {"schema_version": "ontokin.bundle/0.1", "entry_source_id": "entry", "units": sorted(units, key=lambda x:x["source_id"])}
    data = json.dumps(manifest, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()
    return sha(b"ontokin.bundle/0.1\0" + data), manifest


def check_states(acceptance):
    original = json.loads((PROPOSAL / "acceptance.json").read_bytes())
    original_cases = {case["id"]: case for case in original["source_cases"]}
    a = original_cases["P16"]["expected"]["independent_solution"]["resolved_joint_targets_rad"]
    b = original_cases["P02"]["expected"]["independent_solution"]["resolved_joint_targets_rad"]
    aq, bq = list(map(Q.from_float, a)), list(map(Q.from_float, b))
    captured = [v / 4 for v in aq]
    for actual, exact in zip([a[0]/4, a[1]/4], captured):
        require(Q.from_float(actual) == exact, "quarter coordinate representable exactly")
    ids = ["planar-reach-lifecycle", "demo", "rig", "arm"]
    claimed = [ids + ["shoulder"], ids + ["elbow"]]
    counts = {"L01": (16,16), "L02": (14,28), "L03": (14,28), "L04": (7,14)}
    stored = {}
    for case in acceptance["source_cases"]:
        cid = case["id"]
        require(cid in counts, "case inventory")
        require((case["sample_side_count"],case["action_state_count"]) == counts[cid], cid + " inventory")
        revision, manifest = closure(read(case["file_manifest"]))
        require(revision == case["program_revision"] and manifest == case["source_manifest"], cid + " bundle identity")
        require(sha((HERE / case["file_manifest"]).read_bytes()) == case["file_manifest_sha256"], cid + " manifest hash")
        source = (HERE / case["entry_source"]).read_bytes()
        require(sha(source) == case["source_sha256"] and len(source) == case["source_bytes"], cid + " entry identity")
        unique = set()
        prior_latches = {}
        for sample in case["samples"]:
            t, side = Q(sample["time_seconds"]), sample["side"]
            require(t == q(sample["time"]), cid + " exact clock")
            key = (cid, t, side)
            require(key not in unique, cid + " sample uniqueness")
            unique.add(key)
            stored[key] = sample
            after = lambda boundary: (t, side == "after") > (Q(boundary), False)
            require(cid != "L04" or (t, side == "after") <= (Q(1,2), False), "L04 no invalid after")
            life_a = "pending" if not after(0) else "running"
            life_b = "pending"
            elapsed_a = min(t, Q(2))
            completion_a = Q(2)
            if cid == "L01":
                if after(Q(1,2)) and not after(Q(3,2)):
                    life_a, elapsed_a, completion_a = "paused", Q(1,2), None
                if after(Q(3,2)):
                    elapsed_a, completion_a = min(t - 1, Q(2)), Q(3)
                if after(3):
                    life_a = "completed"
            elif cid == "L02" and after(Q(1,2)):
                life_a, elapsed_a, completion_a = "stopped", Q(1,2), None
                life_b = "completed" if after(Q(3,2)) else "running"
            elif cid == "L03" and after(2):
                life_a = "completed"
                life_b = "completed" if after(3) else "running"
            if life_a == "pending":
                expected_q = [Q(0), Q(0)]
                expected_v = [Q(0), Q(0)]
            else:
                expected_q = [x * elapsed_a / 2 for x in aq]
                expected_v = [x / 2 for x in aq] if life_a == "running" else [Q(0), Q(0)]
            bstart = captured if cid == "L02" else aq
            btime = Q(1,2) if cid == "L02" else Q(2)
            belapsed = min(t-btime, Q(1))
            if life_b != "pending":
                expected_q = [x + (y-x)*belapsed for x,y in zip(bstart,bq)]
                expected_v = [y-x for x,y in zip(bstart,bq)] if life_b == "running" else [Q(0),Q(0)]
            require(set(sample["reaches"]) == ({"reach_a"} if cid == "L01" else {"reach_a", "reach_b"}), cid + " complete reach map")
            for name, projection in sample["reaches"].items():
                label = cid + " " + sample["time_seconds"] + " " + side + " " + name
                current = projection["current"]
                require(current["available"] is True and current["reason"] is None, label + " available source expectation")
                s = current["value"]
                life = life_a if name == "reach_a" else life_b
                target = a if name == "reach_a" else b
                start = [0.0,0.0] if name == "reach_a" else [float(x) for x in bstart]
                elapsed = elapsed_a if name == "reach_a" else belapsed
                start_time = Q(0) if name == "reach_a" else btime
                duration = Q(2) if name == "reach_a" else Q(1)
                completion = completion_a if name == "reach_a" else btime+1
                outcome = {"pending":"pending","running":"active","paused":"active","stopped":"interrupted","completed":"satisfied"}[life]
                require(s["lifecycle"] == life and s["goal_outcome"] == outcome, label + " lifecycle/outcome")
                require(s["observation"] == {"time_seconds":sample["time_seconds"],"side":side,"run_id":None,"context_kind":"recorded_prefix"}, label + " observation")
                require(projection["accepted_program_revision"] is None and projection["candidate_only"] is None and projection["context_origin"] == "source_recording", label + " no fabricated Agent identity")
                require(projection["program_revision"] == revision, label + " revision")
                source_loc = projection["source_location"]
                rawspan = source[source_loc["start_byte"]:source_loc["end_byte"]]
                require(source_loc["source_id"] == "entry" and source_loc["source_revision"] == case["source_sha256"], label + " source span identity")
                require(rawspan.startswith(("action "+name+" ").encode()) and rawspan.endswith(b";"), label + " action source span")
                require(projection["element_id"] == ["planar-reach-lifecycle","demo",name.replace("_","-")] == projection["description_identity"], label + " action ID")
                for index,(value,exact) in enumerate(zip(s["joint_coordinates_rad"],expected_q)):
                    rounded(value,exact,label+" coordinate "+str(index))
                for index,(value,exact) in enumerate(zip(s["joint_rates_rad_per_s"],expected_v)):
                    rounded(value,exact,label+" actual rate "+str(index))
                own_rate = [(Q.from_float(y)-Q.from_float(x))/duration for x,y in zip(start,target)] if life == "running" else [Q(0),Q(0)]
                for index,(value,exact) in enumerate(zip(s["action_joint_rates_rad_per_s"],own_rate)):
                    rounded(value,exact,label+" own rate "+str(index))
                require(s["claimed_joint_ids"] == (claimed if life in ("running","paused") else []), label+" claims")
                pending_fields = ("resolved_joint_targets_rad","start_coordinates_rad","start_time_seconds","elapsed_seconds","completion_time_seconds","current_residual_m","terminal_result")
                if life == "pending":
                    require(all(s[field] is None for field in pending_fields),label+" pending nulls")
                else:
                    require(s["resolved_joint_targets_rad"] == target and s["start_coordinates_rad"] == start,label+" captured admission coordinates")
                    require(Q(s["start_time_seconds"]) == start_time and Q(s["elapsed_seconds"]) == elapsed,label+" exact admission/elapsed clocks")
                    require((s["completion_time_seconds"] is None and completion is None) or (s["completion_time_seconds"] is not None and Q(s["completion_time_seconds"]) == completion),label+" completion clock")
                physical = fk(s["joint_coordinates_rad"],s["joint_rates_rad_per_s"])
                for pose_name, expected_pos in [("tip_pose_base",physical["tip"]),("tip_pose_world",[physical["tip"][0],physical["tip"][1]+1,0.0])]:
                    vector_close(s[pose_name]["position_m"],expected_pos,label+" "+pose_name)
                    vector_close(s[pose_name]["orientation_wxyz"],physical["rotation"],label+" orientation")
                vector_close(sample["physical"]["tip_velocity_world_m_per_s"],physical["velocity"],label+" velocity")
                vector_close(sample["physical"]["forearm_omega_world_rad_per_s"],physical["omega"],label+" angular velocity")
                goal = [0.0,1.0,0.0] if name == "reach_a" else ([8.0,8.0,0.0] if cid == "L04" else [1.0,1.0,0.0])
                require(projection["target"]["coordinates_m"] == goal,label+" source goal")
                require(s["current_world_target_m"] == [goal[0],goal[1]+1,goal[2]],label+" transported world goal")
                if life != "pending":
                    require(abs(s["current_residual_m"] - math.dist(physical["tip"],goal)) <= 2e-12,label+" current residual")
                terminal=s["terminal_result"]
                if life in ("stopped","completed"):
                    require(terminal is not None and terminal["outcome"] == outcome,label+" terminal outcome")
                    expected_terminal_time = Q(1,2) if life == "stopped" else completion
                    require(Q(terminal["time_seconds"]) == expected_terminal_time,label+" latched time")
                    terminal_q = captured if life == "stopped" else list(map(Q.from_float,target))
                    for index,(actual,exact) in enumerate(zip(terminal["joint_coordinates_rad"],terminal_q)):
                        rounded(actual,exact,label+" latched coordinate "+str(index))
                    endpoint=fk(terminal["joint_coordinates_rad"],[0,0])
                    vector_close(terminal["tip_pose_base"]["position_m"],endpoint["tip"],label+" latched pose")
                    require(abs(terminal["position_residual_m"]-math.dist(endpoint["tip"],goal))<=2e-12,label+" latched residual")
                    if life == "completed": require(terminal["position_residual_m"]<=1e-9,label+" satisfied tolerance")
                    if name in prior_latches: require(terminal==prior_latches[name],label+" latch immutable under later physical ownership")
                    prior_latches[name]=terminal
                else:
                    require(terminal is None,label+" no premature terminal latch")
        if cid == "L04":
            require(case["failure"]["whole_boundary_rollback"] and case["failure"]["reach_code"]=="reach_unreachable", "failed handoff requirement")
    require(len(stored)==51,"51 distinct sampled sides")
    for cid,clocks in {"L01":["0","0.5","1.5","3"],"L02":["0","0.5","1.5"],"L03":["0","2","3"],"L04":["0"]}.items():
        for time in clocks:
            require(all((cid,Q(time),side) in stored for side in ("before","after")), cid+" both boundary sides "+time)
    for cid,time in [("L02","1"),("L03","2.5")]:
        astate=stored[(cid,Q(time),"after")]["reaches"]["reach_a"]["current"]["value"]
        bstate=stored[(cid,Q(time),"after")]["reaches"]["reach_b"]["current"]["value"]
        require(astate["joint_coordinates_rad"]==bstate["joint_coordinates_rad"],cid+" shared actual coordinates")
        require(astate["action_joint_rates_rad_per_s"]==[0,0] and any(bstate["action_joint_rates_rad_per_s"]),cid+" own versus physical rates")
        require(astate["joint_coordinates_rad"]!=astate["terminal_result"]["joint_coordinates_rad"],cid+" physical coordinates differ from latch")


def check_protocol(data, release):
    groups=data["protocol_cases"]
    require([g["id"] for g in groups]==["LP01","LP02","LP03","LP04","LP05"],"fixed LP inventory")
    require([len(g["steps"]) for g in groups]==[9,9,5,7,12],"42 fixed semantic requirements")
    steps={step["id"]:step for group in groups for step in group["steps"]}
    require(len(steps)==42 and data["protocol_step_count"]==42,"unique LP steps")
    require(all(s["execution_status"]=="not_executed" for s in steps.values()),"no invented execution")
    require(all(s["request_template"]["operation"]!="export" for s in groups[0]["steps"]),"LP01 no extra export")
    require(steps["LP02.05"]["request_template"]==steps["LP02.06"]["request_template"],"identical retry")
    correct=steps["LP02.05"]["request_template"]["patches"][0]
    require(correct["element_id"]==["planar-reach-fixture","demo","rig"],"root occurrence authority")
    for sid in ("LP02.03","LP02.04"):
        bad=steps[sid]["request_template"]["patches"][0]
        require({k:v for k,v in bad.items() if k!="element_id"}=={k:v for k,v in correct.items() if k!="element_id"},"wrong authority isolated")
        require(bad["element_id"]!=correct["element_id"] and steps[sid]["expected"]["status"]=="rejected","wrong authority rejection")
    for sid in ("LP04.03","LP04.04","LP04.05"):
        r=steps[sid]["request_template"]
        require(r["time"]=={"seconds":"1.5","side":"after"} and r["selector"]=={"kind":"action"} and r["fields"]==["actions"] and r["limit"]==128,"fixed complete P24 query")
        require(r["run_id"]=={"$binding":"LP04.sampled_run"},"actual P24 run")
    require(steps["LP04.05"]["expected"]["status"]=="failed" and steps["LP04.05"]["expected"]["failure_stage"]=="final complete-response guard","inherited final publication failure")
    require(steps["LP05.03"]["expected"]["current"]=={"available":False,"reason":"run_required","value":None},"unsampled candidate distinct from pending")
    require(steps["LP05.04"]["expected"]["current_available"] and steps["LP05.04"]["request_template"]["time"]=={"seconds":"0","side":"before"},"actual before-zero candidate sample")
    require(all(steps[s]["expected"]["status"]=="rejected" for s in ("LP05.05","LP05.06","LP05.07","LP05.11")),"candidate ordinary operations remain rejected")
    historical = steps["LP05.09"]["expected"]
    require("candidate_only" not in historical and historical["projection_candidate_only"] is False
            and historical["retained_run_candidate_only"] is True
            and steps["LP05.12"]["expected"]["candidate_only"] is False,
            "accepted source projection distinct from retained candidate run and fresh reset")
    require(release["included_in_original_42_protocol_steps"] is False,"additional release probes separated")
    q22=next(p for p in release["probes"] if p["id"].startswith("Q22"))
    edit=q22["edit_request_template"]
    require(edit["operation"]=="edit" and len(edit["patches"])==1,"Q22 actual one-edit precondition")
    patch=edit["patches"][0]
    source=(HERE/"sources/l04-failed-handoff-valid-prefix.ok").read_bytes()
    require(source[patch["start_byte"]:patch["end_byte"]]==patch["expected_text"].encode(),"Q22 exact expected source bytes")
    changed=source[:patch["start_byte"]]+patch["replacement"].encode()+source[patch["end_byte"]:]
    require(changed==(HERE/"sources/l02-stopped-action-new-owner.ok").read_bytes(),"Q22 exact L04 to L02")
    mismatch=q22["mismatch_request_template"]
    require(mismatch["project_id"]==edit["project_id"] and mismatch["run_id"]=={"$binding":"LP01.failed_run"},"Q22 actual same-project old run")
    export=release["probes"][0]["request_template"]
    require(export["options"]=={"end":"0.25"} and export["program_revision"]==data["fixture_revisions"]["L04"],"tenth artifact unchanged L04 prefix")


def main():
    acceptance=read("acceptance.json")
    provenance=read("reconstruction.json")
    inventory=read("generated-members.json")
    for item in inventory["members"]+inventory["authoring_inputs"]:
        data=(HERE/item["path"]).read_bytes()
        require(len(data)==item["bytes"] and sha(data)==item["sha256"],"member identity "+item["path"])
    for item in provenance["exact_recovered_files"]+provenance["exact_unchanged_libraries"]:
        data=(HERE/item["path"]).read_bytes()
        require(sha(data)==item["sha256"] and len(data)==item["bytes"],"recovery identity "+item["path"])
    for item in provenance["exact_unchanged_libraries"]:
        require((HERE/item["path"]).read_bytes()==(PROPOSAL/item["path"]).read_bytes(),"unchanged original library")
    for lost in provenance["historical_lost_files"]:
        require(lost["contents_recovered"] is False and sha((HERE/lost["path"]).read_bytes())!=lost["sha256"],"new reconstruction not historical bytes")
    require(acceptance["reconstruction"]["sample_grid_recovered"] is False,"historical grid gap disclosed")
    require((acceptance["sample_side_count"],acceptance["action_state_count"])==(51,86),"aggregate sample inventory")
    check_states(acceptance)
    check_protocol(read("protocol-cases.json"),read("release-probes.json"))
    print(json.dumps({"status":"passed","scope":"pure reconstruction checks; not source/Agent/export acceptance",
        "sample_sides":51,"action_states":86,"protocol_steps":42,"additional_release_probes":2,
        "source_runtime_executed":False,"agent_sqlite_executed":False,"glb_or_destination_executed":False},sort_keys=True))


if __name__=="__main__":
    main()
