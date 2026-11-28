"""C272 scoring (G4, TASK-018): the unchanged C255 checker judges observations of actual bytes.

The C255 observation is assembled only from observations: C256's geometry and poses, and
G3's semantic record of the delivered artifacts and of the rebuilt artifacts. The verdict
is C255's `evaluate`. The per-property table localizes faults with C255's own predicates
and never sets the verdict. The workflow checks add what C255 leaves to the harness:
- the runner's outcome;
- the observed locality of the edit;
- G3's cross-checks against decoded motion;
- the source/GLB agreements of C257, C258 and C267;
- the rebuild's clean-workspace facts.

It imports no OntoKin product module.
"""
from __future__ import annotations

import copy
import hashlib
import math

import observe
import semantic_observe

ORACLE = observe.pinned("c255_oracle")
GLB, SIDECAR = "scene.glb", "scene.semantic.json"
SELECTED_FINGER = ["keyed-rack", "demo", "first", "fingers", "middle"]
SELECTED_BLADE = SELECTED_FINGER + ["blade"]


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def decode_record(document: dict) -> dict:
    """Decode the runner's hex transport with C255's own decoder; the rebuild state is added later."""
    document = copy.deepcopy(document)
    placeholder = "rebuild" not in document
    if placeholder:
        document["rebuild"] = {"sourceFiles": {}, "artifacts": {}}
    decoded = ORACLE.decode_authority(document)
    if placeholder:
        del decoded["rebuild"]
    return decoded


def observe_artifacts(source_files: dict, artifacts: dict) -> dict:
    """Decode one delivered state: C256/C257/C258/C267 on the GLB, then G3 on GLB and sidecar."""
    delivery = observe.observe_delivery(source_files, artifacts[GLB], GLB)
    semantic = (semantic_observe.observe_semantic(source_files, artifacts[GLB], artifacts[SIDECAR], delivery)
                if delivery["valid"] else {"valid": False, "semantic": None, "fault": {"code": "DELIVERY_INVALID"}})
    return {"delivery": delivery, "semantic": semantic}


def provenance(state: dict, program: str, accepted: str, sources: dict, artifacts: dict) -> dict:
    return {"acceptedRevision": accepted, "programRevision": program,
            "sourceHashes": {n: sha256(b) for n, b in sources.items()},
            "artifactHashes": {n: sha256(b) for n, b in artifacts.items()},
            "semanticOrigin": {"artifact": SIDECAR, "sha256": sha256(artifacts[SIDECAR]),
                               "location": "/sites, /actions, /events, /objects/*/placement and /motion; with scene.glb "
                                           "/extras/ontokin and /nodes/*/extras/ontokin (field pointers in semanticOrigins)",
                               "programRevision": program}}


def assemble(case_id: str, authority: dict, final: dict, rebuilt: dict, rebuild_artifacts: dict) -> dict:
    """The C255 observation, from observed records only; a missing observation stays missing (None)."""
    retained = authority["retained"]
    def part(state, artifacts):
        return {"semantic": state["semantic"].get("semantic"), "geometry": state["delivery"].get("geometry"),
                "poses": state["delivery"].get("poses"),
                "provenance": provenance(state, retained["programRevision"], retained["acceptedRevision"],
                                         retained["sourceFiles"], artifacts)}
    final_part, rebuild_part = part(final, retained["artifacts"]), part(rebuilt, rebuild_artifacts)
    return {"schema": ORACLE.SCHEMA, "attemptId": authority["attemptId"], "caseId": case_id, "layer": "delivery",
            **final_part, "rebuild": rebuild_part, "decision": copy.deepcopy(authority["decision"])}


def localize_semantic(observed: dict | None, expected: dict) -> list[dict]:
    """Per-property outcomes with C255's semantic predicate; for reporting, never the verdict."""
    rows = []
    def outcome(label, replace):
        trial = copy.deepcopy(expected)
        try:
            replace(trial)
            ORACLE.semantic_check(trial, expected)
            rows.append({"property": label, "outcome": "passed"})
        except ORACLE.Fault as error:
            rows.append({"property": label, "outcome": "failed", "fault": {"code": error.code, "detail": error.detail}})
        except (KeyError, TypeError, ValueError) as error:
            rows.append({"property": label, "outcome": "failed", "fault": {"code": "MALFORMED", "detail": type(error).__name__}})
    if observed is None:
        return [{"property": "semantic", "outcome": "incomplete", "reason": "no semantic observation"}]
    for field in ("units", "frame", "scene", "events"):
        outcome(f"semantic.{field}", lambda t, f=field: t.__setitem__(f, observed[f]))
    for collection in ("objects", "sites", "follows", "hinges", "actions"):
        wanted = {tuple(r["id"]): i for i, r in enumerate(expected[collection])}
        got = {}
        for r in observed.get(collection) or []:
            got.setdefault(tuple(r["id"]), []).append(r)
        for key, index in wanted.items():
            label = f"semantic.{collection}[{'/'.join(key)}]"
            if len(got.get(key, [])) != 1:
                rows.append({"property": label, "outcome": "failed", "fault": {"code": "IDENTITY", "detail": "missing or duplicated"}})
                continue
            outcome(label, lambda t, c=collection, i=index, r=got[key][0]: t[c].__setitem__(i, r))
        for key in set(got) - set(wanted):
            rows.append({"property": f"semantic.{collection}[{'/'.join(key)}]", "outcome": "failed",
                         "fault": {"code": "IDENTITY", "detail": "extra identity"}})
    return rows


def pose_table(poses: list | None, expected: list) -> list[dict]:
    """Per-pose errors against the independent equations; diagnostics only, C255's pose_check is the verdict."""
    if poses is None:
        return []
    observed = {(tuple(p["id"]), p["time_s"]): p for p in poses}
    rows = []
    for target in expected:
        key = (tuple(target["id"]), target["time_s"])
        row = observed.get(key)
        if row is None:
            rows.append({"id": target["id"], "time_s": target["time_s"], "outcome": "missing"})
            continue
        position_error = max(abs(a - e) for a, e in zip(row["position_m"], target["position_m"]))
        angle_error = ORACLE.quaternion_angle(row["rotation_wxyz"], target["rotation_wxyz"])
        rows.append({"id": target["id"], "time_s": target["time_s"], "position_error_m": position_error,
                     "angle_error_rad": angle_error, "origin": row["origin"]["location"],
                     "outcome": "passed" if position_error <= ORACLE.DELIVERY_POSITION and angle_error <= ORACLE.DELIVERY_ANGLE else "failed"})
    return rows


def locality(case_id: str, start: dict, final: dict) -> dict:
    """Observed difference between the start and final delivered semantics and poses."""
    if not (start["semantic"].get("semantic") and final["semantic"].get("semantic")):
        return {"passed": False, "reason": "missing semantic observation"}
    a, b = start["semantic"]["semantic"], final["semantic"]["semantic"]
    changed = []
    for field in ("units", "frame", "scene", "events"):
        if a[field] != b[field]:
            changed.append(field)
    for collection in ("objects", "sites", "follows", "hinges", "actions"):
        left = {tuple(r["id"]): r for r in a[collection]}
        right = {tuple(r["id"]): r for r in b[collection]}
        for key in sorted(set(left) | set(right)):
            if left.get(key) != right.get(key):
                fields = sorted(k for k in set(left.get(key, {})) | set(right.get(key, {}))
                                if (left.get(key) or {}).get(k) != (right.get(key) or {}).get(k))
                changed.append(f"{collection}[{'/'.join(key)}]:{','.join(fields)}")
    pose_a = {(tuple(p["id"]), p["time_s"]): p for p in start["delivery"]["poses"]}
    pose_b = {(tuple(p["id"]), p["time_s"]): p for p in final["delivery"]["poses"]}
    moved = sorted({"/".join(k[0]) for k in set(pose_a) | set(pose_b)
                    if k not in pose_a or k not in pose_b
                    or (pose_a[k]["position_m"], pose_a[k]["rotation_wxyz"]) != (pose_b[k]["position_m"], pose_b[k]["rotation_wxyz"])})
    finger, blade = "/".join(SELECTED_FINGER), "/".join(SELECTED_BLADE)
    allowed = {f"objects[{finger}]:parameters", f"objects[{blade}]:parameters,primitive", f"sites[{blade}/base]:position_m"}
    if case_id == "N1":
        passed = not changed and not moved
    else:
        passed = set(changed) == allowed and moved == [blade]
    unrelated = [o for o in ORACLE.semantic_state(0.65)["objects"] if o["id"] not in (SELECTED_FINGER, SELECTED_BLADE)]
    return {"passed": passed, "changed": changed, "movedObjects": moved, "allowed": sorted(allowed) if case_id != "N1" else [],
            "unrelatedObjectsUnchanged": len(unrelated), "secondRackObjects": sum(o["id"][2] == "second" for o in unrelated)}


def score_case(corpus, case_id: str, authority: dict, start: dict, final: dict, rebuilt: dict,
               rebuild_artifacts: dict, workflow: dict) -> dict:
    """Score one case. WORKFLOW holds the runner's and the rebuild's harness facts."""
    observation = assemble(case_id, authority, final, rebuilt, rebuild_artifacts)
    verdict = ORACLE.evaluate(corpus, case_id, observation, authority)
    expected = ORACLE.expected_state(corpus, case_id)
    rows = [{"property": "accepted-state record (C255 authority)", "outcome": "passed"}]
    try:
        ORACLE.authority_check(corpus, case_id, authority)
    except ORACLE.Fault as error:
        rows[0].update(outcome="failed", fault={"code": error.code, "detail": error.detail})
    rows += localize_semantic(observation["semantic"], expected["semantic"])
    for label, function, args in (
            ("geometry (18 meshes)", ORACLE.geometry_check, (observation["geometry"], expected["semantic"], authority["retained"]["artifacts"], authority["retained"]["programRevision"])),
            ("poses (126)", ORACLE.pose_check, (observation["poses"], expected["poses"], "delivery", authority["retained"]["artifacts"], authority["retained"]["programRevision"])),
            ("provenance", ORACLE.provenance_check, (observation["provenance"], authority["retained"])),
            ("rebuild semantic", ORACLE.semantic_check, (observation["rebuild"]["semantic"], expected["semantic"])),
            ("rebuild geometry", ORACLE.geometry_check, (observation["rebuild"]["geometry"], expected["semantic"], authority["retained"]["artifacts"], authority["retained"]["programRevision"])),
            ("rebuild poses", ORACLE.pose_check, (observation["rebuild"]["poses"], expected["poses"], "delivery", authority["retained"]["artifacts"], authority["retained"]["programRevision"])),
            ("rebuild provenance", ORACLE.provenance_check, (observation["rebuild"]["provenance"], authority["retained"]))):
        try:
            function(*args)
            rows.append({"property": label, "outcome": "passed"})
        except ORACLE.Fault as error:
            rows.append({"property": label, "outcome": "failed", "fault": {"code": error.code, "detail": error.detail}})
        except (KeyError, TypeError, ValueError) as error:
            rows.append({"property": label, "outcome": "failed", "fault": {"code": "MALFORMED", "detail": type(error).__name__}})
    checks = dict(workflow)
    checks["delivery decoded and agreements consistent"] = final["delivery"]["valid"] and rebuilt["delivery"]["valid"]
    checks["delivered semantics cross-checked against decoded motion"] = bool(final["semantic"].get("valid") and rebuilt["semantic"].get("valid"))
    local = locality(case_id, start, final)
    checks["observed locality of the edit"] = local["passed"]
    pose_rows = pose_table(observation["poses"], expected["poses"])
    consistent = verdict["componentPass"] == all(r["outcome"] == "passed" for r in rows)
    checks["per-property table agrees with the C255 verdict"] = consistent
    passed = verdict["componentPass"] and all(checks.values())
    return {"schema": "ontokin.c272.case-score/1", "caseId": case_id, "passed": passed,
            "c255": verdict, "properties": rows, "poses": pose_rows, "locality": local, "workflowChecks": checks,
            "statement": ("Agreement at seven sampled times (0, 0.25, 0.5, 0.75, 1, 1.5, 2 s) on one previously "
                          "exposed assembly family; not proof of continuous motion or dynamics.")}
