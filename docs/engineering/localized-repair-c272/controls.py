"""C272 evaluator and residual controls (G6, G7; TASK-020, TASK-021).

Each control presents one deliberate fault, or one correct variant, to the workflow's
own checks (`score.score_case`, which runs the unchanged C255 checker) and retains the
result with its reasons. Each fault control also judges its clean twin, the same input
without the fault, which must be accepted.

These are **evaluator controls**. None is a case outcome, a model attempt or a fixture
of the frozen corpus. The two end-to-end controls receive real service output, which
the harness produced from a different patch list. This module imports no product module.
"""
from __future__ import annotations

import copy
import hashlib
import json

import glb_edit
import observe
import score
import semantic_observe

GLB, SIDECAR = score.GLB, score.SIDECAR
BLADE = 'first.fingers["middle"].blade'
SIBLING_BLADE = 'second.fingers["top"].blade'
LABEL = "evaluator control; not a case outcome, model attempt or corpus fixture"


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def judge(corpus, m) -> dict:
    result = score.score_case(corpus, m["case"], m["authority"], m["start"], m["final"], m["rebuilt"],
                              m["rebuild_artifacts"], m["workflow"])
    reasons = [f"C255 {f['code']}: {f['detail']}" for f in result["c255"]["faults"]]
    reasons += [f"workflow check failed: {k}" for k, v in result["workflowChecks"].items() if not v]
    for state in ("final", "rebuilt"):
        observed = m[state]
        reasons += [f"{state} observer {f.get('observer', '')} {f.get('code')}: {f.get('detail', '')}".replace("  ", " ")
                    for f in (observed["delivery"].get("faults") or [])]
        fault = (observed["semantic"] or {}).get("fault")
        if fault and fault.get("code") != "DELIVERY_INVALID":
            reasons.append(f"{state} G3 {fault['code']}: {fault.get('detail', '')}")
        reasons += [f"{state} G3 cross-check failed: {c['check']}" for c in (observed["semantic"].get("crossChecks") or []) if not c["passed"]]
    reasons = list(dict.fromkeys(reasons))
    return {"accepted": result["passed"], "reasons": reasons}


def rebind(sidecar: bytes, glb: bytes) -> bytes:
    value = json.loads(sidecar)
    value["binding"]["artifact"].update(sha256="sha256:" + sha256(glb), bytes=len(glb))
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def with_artifacts(m, artifacts, *, retained_only=False):
    """The same case with other final artifacts, observed again; provenance stays consistent."""
    n = copy.deepcopy(m)
    states = ("retained",) if retained_only else ("candidate", "retained", "rebuild")
    for state in states:
        n["authority"][state]["artifacts"] = dict(artifacts)
    n["final"] = score.observe_artifacts(n["authority"]["retained"]["sourceFiles"], artifacts)
    if not retained_only:
        n["rebuilt"], n["rebuild_artifacts"] = n["final"], dict(artifacts)
    return n


def from_record(m, variant) -> dict:
    """Judge a real variant delivery as the case it claims to be."""
    n = copy.deepcopy(m)
    authority = copy.deepcopy(variant["authority"])
    authority["caseId"], authority["attemptId"] = m["case"], m["authority"]["attemptId"]
    authority["rebuild"] = {"sourceFiles": dict(authority["retained"]["sourceFiles"]), "artifacts": dict(authority["retained"]["artifacts"]),
                            "cleanWorkspace": True, "declaredInputs": ["hinges.ok", "main.ok"], "determinism": "byte-exact"}
    n["authority"] = authority
    n["final"] = score.observe_artifacts(authority["retained"]["sourceFiles"], authority["retained"]["artifacts"])
    n["rebuilt"], n["rebuild_artifacts"] = n["final"], dict(authority["retained"]["artifacts"])
    return n


def fault_control(corpus, cid, kind, description, clean, faulty) -> dict:
    bad, good = judge(corpus, faulty), judge(corpus, clean)
    return {"id": cid, "kind": kind, "description": description, "label": LABEL, "expect": "rejected",
            "fault_rejected": not bad["accepted"], "reasons": bad["reasons"],
            "clean_twin_accepted": good["accepted"], "passed": (not bad["accepted"]) and good["accepted"]}


def positive_control(corpus, cid, description, m, extra=True) -> dict:
    result = judge(corpus, m)
    return {"id": cid, "kind": "positive", "description": description, "label": LABEL, "expect": "accepted",
            "accepted": result["accepted"], "reasons": result["reasons"], "passed": result["accepted"] and extra}


def mutate_glb(m, change, rebind_sidecar=True):
    artifacts = dict(m["authority"]["retained"]["artifacts"])
    artifacts[GLB] = change(artifacts[GLB])
    if rebind_sidecar:
        artifacts[SIDECAR] = rebind(artifacts[SIDECAR], artifacts[GLB])
    return artifacts


def negate_all_rotations(glb: bytes) -> bytes:
    """Negate every stored rotation keyframe of every node in one pass: the same rotations."""
    import struct
    document, binary = glb_edit.split(glb)
    data = bytearray(binary)
    for node in range(len(document["nodes"])):
        accessor = glb_edit.channel(document, node, "rotation")["output"]
        start, count = glb_edit.accessor_offset(document, accessor)
        for element in range(count):
            offset = start + 16 * element
            struct.pack_into("<4f", data, offset, *[-x for x in struct.unpack_from("<4f", data, offset)])
    return glb_edit.join(document, bytes(data))


def blade_sample(glb: bytes, path: str, channel: str, element: int, delta: float) -> bytes:
    document, _ = glb_edit.split(glb)
    node = glb_edit.node_index(document, path)
    accessor = glb_edit.channel(document, node, channel)["output"]
    width = 3 if channel == "translation" else 4
    values = glb_edit.read_floats(glb, accessor, element, width)
    values[1] += delta
    return glb_edit.edit_floats(glb, accessor, element, values, width)


def evaluator_controls(corpus, base: dict, variants: dict, extras: dict) -> list[dict]:
    """BASE holds the V1, V2 and N1 materials of the actual run; VARIANTS the real fault deliveries."""
    v1, v2, n1 = base["V1"], base["V2"], base["N1"]
    rows = []
    rows.append(fault_control(corpus, "E01", "wrong-part edit",
                              "The real service accepted 0.75 m on first.fingers[\"upper\"] instead of the middle finger; presented as V1.",
                              v1, from_record(v1, variants["wrong-target"])))
    rows.append(fault_control(corpus, "E02", "changed sibling",
                              "The real service accepted the V1 edit together with a second-rack mount change (top 1.2 m to 1.3 m).",
                              v1, from_record(v1, variants["changed-sibling"])))
    middle = 60  # Index 60 of the 121 samples over 2 s is t = 1 s.
    rows.append(fault_control(corpus, "E03", "incorrect motion",
                              "One translation sample of the selected blade moved by 0.01 m in Y; all records stay consistent.",
                              v1, with_artifacts(v1, mutate_glb(v1, lambda g: blade_sample(g, BLADE, "translation", middle, 0.01)))))
    stale_source = copy.deepcopy(v1)
    stale_source["authority"]["retained"]["sourceFiles"] = dict(v1["authority"]["start"]["sourceFiles"])
    rows.append(fault_control(corpus, "E04a", "stale provenance: source",
                              "The retained record names the pre-edit source with the new artifacts.", v1, stale_source))
    rows.append(fault_control(corpus, "E04b", "stale provenance: artifact",
                              "The retained record names the pre-edit GLB and sidecar with the accepted new source.",
                              v1, with_artifacts(v1, v1["authority"]["start"]["artifacts"])))
    asserted = copy.deepcopy(v1)
    asserted["authority"]["retained"] = copy.deepcopy(v1["authority"]["start"])
    asserted["authority"]["decision"]["acceptedRevision"] = v1["authority"]["start"]["acceptedRevision"]
    rows.append(fault_control(corpus, "E04c", "self-asserted acceptance",
                              "The client claims acceptance while the service's accepted state is still the start.", v1, asserted))
    claimed = dict(v1["authority"]["retained"]["artifacts"])
    side = json.loads(claimed[SIDECAR])
    side["binding"]["accepted_program_revision"] = v1["authority"]["start"]["programRevision"]
    claimed[SIDECAR] = json.dumps(side, sort_keys=True, separators=(",", ":")).encode()
    rows.append(fault_control(corpus, "E04d", "self-asserted acceptance in the artifact",
                              "The delivered GLB with a sidecar whose acceptance claim names a program revision that the GLB does not carry.",
                              v1, with_artifacts(v1, claimed)))
    promoted = copy.deepcopy(n1)
    promoted["authority"]["retained"]["sourceFiles"] = dict(n1["authority"]["candidate"]["sourceFiles"])
    promoted["authority"]["decision"].update(status="accepted", invalidEverAccepted=True, diagnostic=None)
    rows.append(fault_control(corpus, "E05", "accepted invalid candidate",
                              "N1's 0.75 kg candidate recorded as accepted and retained.", n1, promoted))
    missing = copy.deepcopy(v1)
    for state in ("candidate", "retained", "rebuild"):
        missing["authority"][state]["artifacts"] = {SIDECAR: v1["authority"]["retained"]["artifacts"][SIDECAR]}
    missing["final"] = {"delivery": {"valid": False, "geometry": None, "poses": None, "faults": [{"code": "MISSING"}]},
                        "semantic": {"valid": False, "semantic": None}}
    missing["rebuilt"] = missing["final"]
    missing["rebuild_artifacts"] = dict(missing["authority"]["rebuild"]["artifacts"])
    rows.append(fault_control(corpus, "E06a", "missing output", "No GLB was delivered for V1.", v1, missing))
    crashed = copy.deepcopy(v1)
    crashed["workflow"]["runner completed"] = False
    rows.append(fault_control(corpus, "E06b", "missing output: crashed case",
                              "The runner's case outcome is a crash; the evaluator's other inputs are intact.", v1, crashed))
    inconsistent = copy.deepcopy(v1)
    inconsistent["rebuild_artifacts"] = mutate_glb(v1, lambda g: blade_sample(g, BLADE, "rotation", middle, 1e-3))
    inconsistent["authority"]["rebuild"]["artifacts"] = dict(inconsistent["rebuild_artifacts"])
    inconsistent["rebuilt"] = score.observe_artifacts(v1["authority"]["retained"]["sourceFiles"], inconsistent["rebuild_artifacts"])
    rows.append(fault_control(corpus, "E07a", "inconsistent rebuild", "The rebuilt GLB differs from the delivered one in one sample.",
                              v1, inconsistent))
    if "undeclared-input rebuild" in extras:
        undeclared = copy.deepcopy(v1)
        record = extras["undeclared-input rebuild"]
        undeclared["workflow"]["rebuild workspace clean"] = bool(record.get("clean"))
        undeclared["authority"]["rebuild"]["cleanWorkspace"] = bool(record.get("clean"))
        rows.append(fault_control(corpus, "E07b", "rebuild with an undeclared input",
                                  "A real rebuild ran in a workspace that also held an undeclared file (extra.ok).", v1, undeclared))
    pin = copy.deepcopy(v1)
    library = pin["authority"]["retained"]["sourceFiles"]["hinges.ok"]
    pin["authority"]["retained"]["sourceFiles"]["hinges.ok"] = library.replace(b"0.08[m]", b"0.09[m]", 1)
    rows.append(fault_control(corpus, "E08", "changed dependency pin",
                              "The retained library differs from the pinned bytes that main.ok's digest names.", v1, pin))
    rows.append(positive_control(corpus, "P01", "Independently correct 0.75 m state (V1 final) is accepted.", v1))
    rows.append(positive_control(corpus, "P02", "Independently correct 0.65 m state (V2 final) is accepted.", v2))
    rows.append(positive_control(corpus, "P03", "Every stored rotation keyframe of all 18 nodes negated in the actual GLB bytes "
                                 "(the same rotations) and judged end to end, the sidecar rebound, is accepted.",
                                 with_artifacts(v1, mutate_glb(v1, negate_all_rotations))))
    changed = (v1["authority"]["start"]["acceptedRevision"] != v1["authority"]["retained"]["acceptedRevision"]
               and v1["authority"]["start"]["sourceFiles"]["main.ok"] != v1["authority"]["retained"]["sourceFiles"]["main.ok"]
               and all(v1["authority"]["start"]["artifacts"][k] != v1["authority"]["retained"]["artifacts"][k] for k in (GLB, SIDECAR)))
    rows.append(positive_control(corpus, "P04", "A legitimate change of accepted revision, source hash and artifact hashes after the valid V1 edit is accepted.",
                                 v1, extra=changed))
    return rows


REVISION_BOUND = {"sha256", "source_revision", "program_revision", "programRevision", "artifactSha256",
                  "entry_revision", "revision", "artifact_sha256"}


def stable(value):
    """Declaration meaning without revision-bound digests and revision identities (SCORING.md)."""
    if isinstance(value, dict):
        return {k: stable(v) for k, v in value.items() if k not in REVISION_BOUND}
    if isinstance(value, list):
        return [stable(v) for v in value]
    return value


def hinge_records(source_files, glb):
    try:
        result = observe.pinned("c267_hinge_compare").compare_hinges(source_files, glb)
        return {"refused": None, "records": stable(result["records"])}
    except Exception as error:
        return {"refused": getattr(error, "code", type(error).__name__), "records": None}


def residual_controls(corpus, base: dict) -> list[dict]:
    """H20: isolated changes of one ownership, follow or motion field; H24: bounds of G3's reader."""
    v1 = base["V1"]
    sources = v1["authority"]["retained"]["sourceFiles"]
    glb = v1["authority"]["retained"]["artifacts"][GLB]
    baseline = hinge_records(sources, glb)
    rows = []
    def h20(cid, field, change):
        artifacts = mutate_glb(v1, change)
        mutated = with_artifacts(v1, artifacts)
        bad, good = judge(corpus, mutated), judge(corpus, v1)
        hinges = hinge_records(sources, artifacts[GLB])
        independent = hinges["refused"] is not None or hinges["records"] == baseline["records"]
        rows.append({"id": cid, "group": "H20", "field": field, "label": LABEL,
                     "workflow_rejects": not bad["accepted"], "reasons": bad["reasons"], "clean_twin_accepted": good["accepted"],
                     "c267_hinge_result": "refused: " + hinges["refused"] if hinges["refused"] else "records unchanged" if independent else "records changed",
                     "no_hinge_value_inferred": independent,
                     "passed": (not bad["accepted"]) and good["accepted"] and independent})
    h20("R01", "ownership: owner of second.fingers[\"top\"].blade", lambda g: glb_edit.edit_json(
        g, lambda d: d["nodes"][glb_edit.node_index(d, SIBLING_BLADE)]["extras"]["ontokin"].__setitem__("owner", "second")))
    h20("R02", "follow: offset of first.fingers[\"lower\"].mounting", lambda g: glb_edit.edit_json(
        g, lambda d: d["extras"]["ontokin"]["follows"][0]["offset_position_m"].__setitem__(1, -0.55)))
    h20("R03", "motion: one translation sample of second.fingers[\"top\"].blade", lambda g: blade_sample(g, SIBLING_BLADE, "translation", 60, 0.01))
    start_hinges = hinge_records(v1["authority"]["start"]["sourceFiles"], v1["authority"]["start"]["artifacts"][GLB])
    unchanged = (start_hinges["refused"] is None and baseline["refused"] is None
                 and start_hinges["records"] == baseline["records"])
    rows.append({"id": "R04", "group": "H20", "field": "length parameter (the actual V1 edit, 0.65 m to 0.75 m)", "label": LABEL,
                 "c267_hinge_result": ("hinge records equal across the edit apart from revision-bound digests and revision identities"
                                       if unchanged else "hinge records differ beyond revision-bound fields"),
                 "no_hinge_value_inferred": unchanged, "passed": unchanged})
    delivery = v1["final"]["delivery"]
    side = json.loads(v1["authority"]["retained"]["artifacts"][SIDECAR])
    excessive = copy.deepcopy(side)
    excessive["sites"] = excessive["sites"] * 9
    for cid, label, mutated, code in (
            ("R05", "excessive sites (306) in the sidecar", json.dumps(excessive).encode(), "RESOURCE_LIMIT"),
            ("R06", "duplicate JSON key in the sidecar", b'{"status":"duplicate",' + v1["authority"]["retained"]["artifacts"][SIDECAR][1:], "JSON_DUPLICATE")):
        result = semantic_observe.observe_semantic(sources, glb, mutated, delivery)
        clean = semantic_observe.observe_semantic(sources, glb, v1["authority"]["retained"]["artifacts"][SIDECAR], delivery)
        rows.append({"id": cid, "group": "H24", "field": label, "label": LABEL, "typed_fault": result["fault"],
                     "clean_twin_valid": clean["valid"], "passed": bool(result["fault"]) and result["fault"]["code"] == code and clean["valid"]})
    truncated = observe.observe_delivery(sources, glb[:-200], GLB)
    rows.append({"id": "R07", "group": "H24", "field": "truncated GLB", "label": LABEL, "typed_fault": truncated["faults"][:1],
                 "clean_twin_valid": delivery["valid"], "passed": (not truncated["valid"]) and delivery["valid"]
                 and all("code" in f for f in truncated["faults"])})
    return rows
