#!/usr/bin/env python3
"""Author a deterministic force proposal corpus, never execute a force runtime.

The analytical expectations below are authored from piecewise constant
acceleration and canonical binary64 operands. They are not measured results.
Use --write with a new empty directory, or --check with a published corpus.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from fractions import Fraction as Q
from pathlib import Path
import re
import sys

BASE = "3b962fede4d44fb26ad152029a1fd9b1414159dc"
LIBS = (
    ("fixture.impulse-parts", "impulse-parts.ok", "02-impulse-parts04.ok", "bc122164d828386ec970f8cf183ff22d57dcc90180fe84c574de84c575fc78d6"),
    ("fixture.surface-parts", "surface-parts.ok", "01-surface-parts03.ok", "87fed50bdcb9b6274ec87981cc67028463c10b1cdce301060416c69586b428ce"),
)
HEADER = '''ontokin "0.5";
module ForceDemo @ "force-demo";
profile "force-0.1";

import bodies @ "impulse-parts" from "fixture.impulse-parts" version "1.0.0"
    digest "sha256:bc122164d828386ec970f8cf183ff22d57dcc90180fe84c574de84c575fc78d6";

'''
RACK = '''public class Rack @ "rack-class" {
    public param masses @ "masses": Keyed<Mass> = keyed<Mass> { "first": 2[kg], "second": 4[kg] };
    public parts props @ "props": bodies.SphereProp for (key, mass) in self.masses {
        body_mass = mass;
        placement = pose(world, vec3(if key == "first" then 0[m] else 3[m], 0[m], 0[m]), quat(1, 0, 0, 0));
    }
}

'''
CARRIER = '''public class Carrier @ "carrier-type" {
    geometry = empty();
    physical = no_body();
    public site tip @ "tip" {
        pose = pose(self.frame, vec3(0.5[m], 0[m], 0[m]), quat(1, 0, 0, 0));
        interface = "rigid.origin";
        size = 0[m];
    }
}

'''

def digest(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()

def encode(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()

def q(value: str | float | int | Q) -> Q:
    return value if isinstance(value, Q) else Q.from_float(float(value))

def clock(value: Q) -> dict:
    return {"numerator": str(value.numerator), "denominator": str(value.denominator)}

def vec(values: tuple | list, unit: str) -> str:
    return "vector(world, " + ", ".join(str(v) + "[" + unit + "]" for v in values) + ")"

def body(mass="2", position=("0", "0", "0"), velocity=("0", "0", "0")) -> dict:
    return dict(mass=mass, position=position, velocity=velocity)

def force(key="push", at="1", duration="1", vector=("4", "0", "0"), target="ball") -> dict:
    return dict(kind="force", key=key, at=at, duration=duration, vector=vector, target=target)

def impulse(at="1", vector=("0", "2", "0"), point=("0.5", "0", "0")) -> dict:
    return dict(kind="impulse", at=at, vector=vector, point=point, target="ball")

def case(id: str, name: str, forces: list[dict], **kwargs) -> dict:
    return dict(id=id, name=name, kind="positive", events=forces, bodies=kwargs.pop("bodies", {"ball": body()}),
                gravity=kwargs.pop("gravity", ("0", "0", "0")), duration=kwargs.pop("duration", "3"), **kwargs)

def cases() -> list[dict]:
    items = [
        case("P01", "single-interval", [force()]),
        case("P02", "overlap", [force("a", "0", "2"), force("b", "1", "2", ("-2", "0", "0"))], duration="4"),
        case("P03", "opposite-forces", [force("a", "0", "2"), force("b", "0", "2", ("-4", "0", "0"))]),
        case("P04", "same-boundary-replacement", [force("a", "0", "1"), force("b", "1", "1")]),
        case("P05", "zero-preserves-anchor", [force(vector=("0", "0", "0"))], bodies={"ball":body(velocity=("3", "0", "0"))}),
        case("P06", "gravity-cancellation", [force(vector=("0", "20", "0"))], gravity=("0", "-10", "0")),
        case("P07", "off-center-impulse", [force("a", "0", "2"), impulse()]),
        case("P08", "impulse-at-force-end", [force("a", "0", "1"), impulse(vector=("2", "0", "0"), point=("0", "0", "0"))]),
        case("P09", "release-at-action-end", [dict(kind="release", at="1", target="hold"), force(vector=("2", "20", "0"))],
             gravity=("0", "-10", "0"), release=True),
        case("P10", "generated-base", [force(target='rack.props["first"]'), force("sibling", target='rack.props["second"]')],
             bodies={'rack.props["first"]':body(), 'rack.props["second"]':body("4", ("3", "0", "0"))}, rack=True),
        case("P11", "generated-mass-repair", [force(target='rack.props["first"]'), force("sibling", target='rack.props["second"]')],
             bodies={'rack.props["first"]':body("4"), 'rack.props["second"]':body("4", ("3", "0", "0"))}, rack=True,
             repair={"from":"P10", "old":'masses = keyed<Mass> { "first": 2[kg]', "new":'masses = keyed<Mass> { "first": 4[kg]'}),
        case("P12", "generated-force-repair", [force(vector=("8", "0", "0"), target='rack.props["first"]'), force("sibling", target='rack.props["second"]')],
             bodies={'rack.props["first"]':body(), 'rack.props["second"]':body("4", ("3", "0", "0"))}, rack=True,
             repair={"from":"P10", "old":'force rack.props["first"] @ "push" using vector(world, 4[N]', "new":'force rack.props["first"] @ "push" using vector(world, 8[N]'}),
        case("P13", "generated-duration-repair", [force(duration="0.5", target='rack.props["first"]'), force("sibling", target='rack.props["second"]')],
             bodies={'rack.props["first"]':body(), 'rack.props["second"]':body("4", ("3", "0", "0"))}, rack=True,
             repair={"from":"P10", "old":'force rack.props["first"] @ "push" using vector(world, 4[N], 0[N], 0[N]) for 1[s];', "new":'force rack.props["first"] @ "push" using vector(world, 4[N], 0[N], 0[N]) for 0.5[s];'}),
        case("P14", "time-zero", [force(at="0")], duration="2"),
        case("P15", "activation-at-horizon", [force(at="2")], duration="2"),
        case("P16", "canonical-clock-addition", [force(at="0.1", duration="0.2")], duration="1", extra_times=["0.3"]),
        case("P17", "completion-beyond-horizon", [force(duration="5")], duration="2"),
        case("P18", "endpoint-beyond-binary64", [force(at="1e308", duration="1e308", vector=("0", "0", "0"))], duration="1.5e308"),
        case("P19", "finite-final-aggregate", [force("a", "0", "1", ("1e308", "0", "0")), force("b", "0", "1", ("1e308", "0", "0")), force("c", "0", "1", ("-1e308", "0", "0"))], bodies={"ball":body("1e308")}, duration="2"),
        case("P20", "combined-acceleration-cancellation", [force(at="0", duration="0.5", vector=("1e308", "0", "0"))], bodies={"ball":body("0.5")}, gravity=("-1e308", "0", "0"), duration="1"),
        case("P21", "valid-short-prefix", [force("early", "0", "1", ("1", "0", "0")), force("late", "2", "1", ("1e308", "0", "0"))], bodies={"ball":body("0.5")}, duration="4", horizon="1"),
        case("P22", "unseen-vector-variant", [force(at="0.5", duration="1.25", vector=("1", "3", "-2"))], bodies={"ball":body("3.5", velocity=("0.2", "-0.1", "0.3"))}, duration="2.5"),
    ]
    negatives = [
        ("N01", "impulse-is-not-force", "P01", "4[N]", "4[N*s]", "OKL-E-TYPE", "elaboration"),
        ("N02", "force-in-self-frame", "P01", "using vector(world,", "using vector(ball.frame,", "OKL-E-FRAME", "elaboration"),
        ("N03", "point-is-not-force", "P01", "vector(world, 4[N], 0[N], 0[N])", "point(world, 4[m], 0[m], 0[m])", "OKL-E-TYPE", "elaboration"),
        ("N04", "site-is-not-object", "P01", 'force ball @', 'force ball.origin @', "OKL-E-TYPE", "elaboration"),
        ("N05", "missing-target", "P01", 'force ball @', 'force missing @', "OKL-E-NAME", "elaboration"),
        ("N06", "zero-duration", "P01", 'for 1[s]', 'for 0[s]', "OKL-E-EVENT-ORDER", "elaboration"),
        ("N07", "negative-duration", "P01", 'for 1[s]', 'for -1[s]', "OKL-E-EVENT-ORDER", "elaboration"),
        ("N08", "duration-units", "P01", 'for 1[s]', 'for 1[m]', "OKL-E-TYPE", "elaboration"),
        ("N09", "duplicate-key", "P03", '@ "b"', '@ "a"', "OKL-E-NAME", "elaboration"),
        ("N10", "duplicate-key-across-times", "P04", '@ "b"', '@ "a"', "OKL-E-NAME", "elaboration"),
        ("N11", "static-target", "P01", 'body_mass = 2[kg];', 'body_mass = 2[kg]; motion = static;', "OKL-E-MOTION-MODE", "transition"),
        ("N12", "prescribed-target", "P01", 'body_mass = 2[kg];', 'body_mass = 2[kg]; motion = prescribed;', "OKL-E-MOTION-MODE", "transition"),
        ("N13", "zero-mass", "P01", 'body_mass = 2[kg];', 'body_mass = 0[kg];', "OKL-E-PHYSICAL-DOMAIN", "elaboration"),
        ("N14", "negative-mass", "P01", 'body_mass = 2[kg];', 'body_mass = -2[kg];', "OKL-E-PHYSICAL-DOMAIN", "elaboration"),
        ("N15", "zero-radius", "P01", 'body_mass = 2[kg];', 'body_mass = 2[kg]; body_radius = 0[m];', "OKL-E-PHYSICAL-DOMAIN", "elaboration"),
        ("N16", "nonfinite-force", "P01", '4[N]', '1e309[N]', "OKL-E-NUMERIC", "elaboration"),
        ("N17", "nonfinite-duration", "P01", 'for 1[s]', 'for 1e309[s]', "OKL-E-NUMERIC", "elaboration"),
        ("N18", "net-force-overflow", "P19", 'force ball @ "c" using vector(world, -1e308[N], 0[N], 0[N]) for 1[s];', '', "OKL-E-NUMERIC", "transition"),
        ("N19", "later-acceleration-overflow", "P21", None, None, "OKL-E-NUMERIC", "transition"),
        ("N20", "older-profile-rejects-force", "P01", None, None, "OKL-E-SYNTAX", "elaboration"),
        ("N21", "force-before-release", "P09", None, None, "OKL-E-MOTION-MODE", "transition"),
        ("N22", "later-sequence-failure", "P01", None, None, "OKL-E-MOTION-MODE", "transition"),
    ]
    for id, name, origin, old, new, code, phase in negatives:
        items.append(dict(id=id, name=name, kind="negative", origin=origin, old=old, new=new,
                          expected={"diagnostic_code":code, "phase_group":phase}))
    return items

def statement(event: dict) -> str:
    if event["kind"] == "force":
        return f'force {event["target"]} @ "{event["key"]}" using {vec(event["vector"], "N")} for {event["duration"]}[s];'
    if event["kind"] == "release":
        return 'release hold using incoming;'
    point = ", ".join(str(v) + "[m]" for v in event["point"])
    return f'impulse ball using {vec(event["vector"], "N*s")} at point(ball.frame, {point});'

def render(item: dict) -> str:
    text = HEADER + (RACK if item.get("rack") else CARRIER if item.get("release") else "")
    text += f'scene Demo @ "demo" {{\n    duration = {item["duration"]}[s];\n    gravity = {vec(item["gravity"], "m/s^2")};\n'
    if item.get("rack"):
        m = item["bodies"]['rack.props["first"]']["mass"]
        text += f'    object rack @ "rack": Rack {{ masses = keyed<Mass> {{ "first": {m}[kg], "second": 4[kg] }}; }}\n'
    elif item.get("release"):
        text += '''    object carrier @ "carrier": Carrier {
        placement = pose(world, vec3(0[m], 0[m], 0[m]), axis_angle(vec3(0, 0, 1), -2[rad]));
    }
    object ball @ "ball": bodies.SphereProp { motion = prescribed; }
    joint hold @ "hold": grip { parent = carrier.tip; child = ball.origin; }
    action carry @ "carry" = move(carrier, vector(world, 1[m/s], 0[m/s], 0[m/s]), 1[s]);
    action turn @ "turn" = spin(carrier, vector(world, 0[rad/s], 0[rad/s], 2[rad/s]), 1[s]);
    at 0[s] sequence { start carry; start turn; }
'''
    else:
        b = item["bodies"]["ball"]
        text += f'    object ball @ "ball": bodies.SphereProp {{\n        body_mass = {b["mass"]}[kg];\n        velocity = {vec(b["velocity"], "m/s")};\n    }}\n'
    groups = {}
    for event in item["events"]:
        groups.setdefault(q(event["at"]), []).append(event)
    for _, events in sorted(groups.items()):
        text += f'    at {events[0]["at"]}[s] sequence {{\n'
        text += "".join("        " + statement(e) + "\n" for e in events)
        text += '    }\n'
    return text + '}\n'

def expected(item: dict) -> list[dict]:
    """Independent authored translational/planar-rotation oracle, not a parser."""
    horizon = q(item.get("horizon", item["duration"]))
    boundaries = {Q(0)}
    for e in item["events"]:
        boundaries.add(q(e["at"]))
        if e["kind"] == "force":
            boundaries.add(q(e["at"]) + q(e["duration"]))
    relevant = sorted(t for t in boundaries if t <= horizon)
    sample_times = set(relevant) | {horizon} | {q(t) for t in item.get("extra_times", [])}
    for a,b in zip(sorted(set(relevant) | {horizon}), sorted(set(relevant) | {horizon})[1:]):
        sample_times.add((a+b)/2)
    result = []
    for target, b in item["bodies"].items():
        mass = q(b["mass"]); gravity = tuple(float(x) for x in item["gravity"])
        active = {}; starts = ends = 0; last_time = None; last_changes = []
        anchor = Q(0); p = tuple(float(x) for x in b["position"]); v = tuple(float(x) for x in b["velocity"])
        accel = gravity; angle = 0.0; omega = 0.0; free = not item.get("release", False); since = Q(0)
        next_boundary = 0
        def pose(t):
            if not free:
                theta = -2 + 2*float(t)
                return ((float(t)+.5*math.cos(theta), .5*math.sin(theta), 0.),
                        (1-math.sin(theta), math.cos(theta), 0.), theta, 2.)
            dt = t-anchor
            return (tuple(float(q(x)+q(y)*dt+q(a)*dt*dt/2) for x,y,a in zip(p,v,accel)),
                    tuple(float(q(y)+q(a)*dt) for y,a in zip(v,accel)),
                    angle+float(q(omega)*dt), omega)
        for time in sorted(sample_times):
            for side in ("before", "after"):
                while next_boundary < len(relevant) and (relevant[next_boundary] < time or (relevant[next_boundary] == time and side == "after")):
                    at = relevant[next_boundary]; next_boundary += 1
                    incoming_p, incoming_v, incoming_angle, incoming_w = pose(at)
                    changed = []
                    for key in sorted(list(active)):
                        e = active[key]
                        if q(e["at"])+q(e["duration"]) == at:
                            del active[key]; ends += 1; changed.append({"key":key,"kind":"completed"})
                    for e in item["events"]:
                        if q(e["at"]) != at: continue
                        if e["kind"] == "release":
                            free = True; since = at; anchor = at
                            p,v,angle,omega = incoming_p,incoming_v,incoming_angle,incoming_w
                        elif e["target"] != target: continue
                        elif e["kind"] == "force":
                            assert free
                            active[e["key"]] = e; starts += 1; changed.append({"key":e["key"],"kind":"started"})
                        elif e["kind"] == "impulse":
                            cp,cv,theta,w = pose(at); J = tuple(float(x) for x in e["vector"])
                            sx,sy,sz = map(float,e["point"])
                            lx,ly = math.cos(theta)*sx-math.sin(theta)*sy, math.sin(theta)*sx+math.cos(theta)*sy
                            Lz = float(q(lx)*q(J[1])-q(ly)*q(J[0]))
                            nv = tuple(float(q(x)+q(j)/mass) for x,j in zip(cv,J))
                            nw = float(q(w)+q(Lz)/q(.2))
                            if any(J): p,v,angle,omega,anchor = cp,nv,theta,nw,at
                    total = tuple(float(sum((q(e["vector"][i]) for e in active.values()), Q(0))) for i in range(3))
                    new_a = tuple(float(q(g)+q(f)/mass) for g,f in zip(gravity,total))
                    if new_a != accel:
                        p,v,angle,omega = pose(at); anchor = at; accel = new_a
                    if changed: last_time=at; last_changes=changed
                pp,vv,theta,w = pose(time)
                total = tuple(float(sum((q(e["vector"][i]) for e in active.values()), Q(0))) for i in range(3))
                row = {"target":target, "time":clock(time), "side":side, "position_m":pp,"velocity_m_s":vv,
                       "orientation_wxyz":(math.cos(theta/2),0,0,math.sin(theta/2)), "omega_world_rad_s":(0,0,w),
                       "dynamic_since":clock(since) if free else None, "anchor_time":clock(anchor) if free else None,
                       "net_force_world_n":total,"acceleration_world_m_s2":accel if free else None,
                       "active_keys":sorted(active), "started_count":starts,"completed_count":ends,
                       "last_boundary":clock(last_time) if last_time is not None else None,"last_changes":last_changes,
                       "active_ends":{k:clock(q(e["at"])+q(e["duration"])) for k,e in sorted(active.items())}}
                result.append(row)
    return result

def build(repo: Path) -> dict[str, bytes]:
    output = {}; modules = []; descriptors=[]
    for package, filename, source, expected_hash in LIBS:
        raw = (repo / "docs/language-design/impulse-v0.1/libraries" / source).read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected_hash: raise ValueError("Inherited library bytes changed: "+source)
        output["libraries/"+source] = raw
        modules.append(dict(source_id="package:"+package+"@1.0.0",package_id=package,version="1.0.0",filename=filename,source_revision=digest(raw)))
        descriptors.append(dict(package_id=package,version="1.0.0",filename=filename,path="libraries/"+source))
    items=cases(); sources={}; records=[]
    for item in items:
        if item["kind"] == "positive": text=render(item)
        else:
            text=sources[item["origin"]]
            if item["old"] is not None:
                if text.count(item["old"]) != 1: raise ValueError("Ambiguous negative edit "+item["id"])
                text=text.replace(item["old"],item["new"])
            if item["id"] == "N20": text=text.replace('"0.5"','"0.4"').replace('"force-0.1"','"impulse-0.1"')
            if item["id"] == "N21":
                old='        release hold using incoming;\n        force ball @ "push" using vector(world, 2[N], 20[N], 0[N]) for 1[s];'
                assert text.count(old)==1
                text=text.replace(old, '        force ball @ "push" using vector(world, 2[N], 20[N], 0[N]) for 1[s];\n        release hold using incoming;')
            if item["id"] == "N22":
                text=text.replace('    at 1[s]', '    object other @ "other": bodies.SphereProp { motion = static; }\n    at 1[s]')
                text=text.replace('for 1[s];','for 1[s];\n        force other @ "invalid" using vector(world, 0[N], 0[N], 0[N]) for 1[s];')
        sources[item["id"]]=text; raw=text.encode()
        basename=item["id"].lower()+"-"+item["name"]
        source_path="sources/"+basename+".ok"; manifest_path=basename+".files.json"
        output[source_path]=raw
        output[manifest_path]=encode(dict(schema_version="ontokin.files/0.1",entry=dict(filename="force-demo.ok",path=source_path),modules=descriptors))
        units=sorted([dict(source_id="entry",package_id=None,version=None,filename="force-demo.ok",source_revision=digest(raw)),*modules],key=lambda x:x["source_id"])
        canonical=json.dumps(dict(schema_version="ontokin.bundle/0.1",entry_source_id="entry",units=units),sort_keys=True,ensure_ascii=False,separators=(",",":"),allow_nan=False).encode()
        record=dict(id=item["id"],kind=item["kind"],name=item["name"],file_manifest=manifest_path,source_sha256=digest(raw),program_revision=digest(b"ontokin.bundle/0.1\0"+canonical),source_units=units)
        spans=[]
        for match in re.finditer(r'(?m)^\s*(force [^\n]*;)', text):
            start=len(text[:match.start(1)].encode()); end=len(text[:match.end(1)].encode())
            spans.append(dict(source_id="entry",source_revision=digest(raw),start_byte=start,end_byte=end,text=match.group(1)))
        record["force_statements"]=spans
        if item["kind"] == "positive":
            record["request_horizon"]=clock(q(item.get("horizon",item["duration"])))
            record["expected_samples"]=expected(item)
            if "repair" in item:
                patch=item["repair"]; original=sources[patch["from"]]
                assert original.count(patch["old"])==1
                assert original.replace(patch["old"],patch["new"])==text
                start=len(original[:original.index(patch["old"])].encode())
                record["repair"]=dict(from_case=patch["from"],source_id="entry",start_byte=start,end_byte=start+len(patch["old"].encode()),expected_text=patch["old"],replacement=patch["new"],unchanged_sibling='rack.props["second"]')
        else:
            record["expected"]=item["expected"].copy()
            if item["expected"]["phase_group"]=="transition":
                at = "0" if item["id"]=="N18" else "2" if item["id"]=="N19" else "1"
                record["expected"].update(time=clock(q(at)),side="after",whole_boundary_rollback=True)
        records.append(record)
    acceptance=dict(schema_version="ontokin.force-proposal-corpus/0.1",status="authored-not-runtime-executed",base_commit=BASE,
                    proposal="0.1-recovery-proposal",source_case_count=len(records),positive_count=22,negative_count=22,
                    tolerances=dict(ordinary_position_m=1e-9,ordinary_velocity_m_s=1e-9,orientation_rad=1e-9,
                                    canonical_clocks_keys_counts_anchors="exact",extreme_numeric_cases="exact canonical component equality; no relative tolerance"),
                    oracle_scope="Independent authored piecewise constant acceleration with planar inherited impulse/release examples. Not a parser, solver, export or test result.",
                    remaining_before_adoption=["Review all diagnostic precedence, especially automatic-end numeric failures.","Add fixed interior-extremum overflow, duration-underflow, incompatible import-edge, budget/cancellation and delivery cases.","Freeze concrete Agent operation/result schemas and release method mapping before runtime acceptance.","Record independent review and adoption of these actual bytes; do not reuse unavailable draft hashes."],
                    source_cases=records)
    output["acceptance.json"]=encode(acceptance)
    output["member-manifest.json"]=encode({"schema_version":"ontokin.force-authored-members/0.1","status":"authored-not-runtime-executed","files":[{"path":name,"bytes":len(raw),"sha256":digest(raw)} for name,raw in sorted(output.items())]})
    return output

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo",type=Path,required=True)
    modes=parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--write",type=Path)
    modes.add_argument("--check",type=Path)
    args=parser.parse_args(); files=build(args.repo.resolve()); destination=(args.write or args.check).resolve()
    if args.write:
        if destination.exists() and any(destination.iterdir()): raise ValueError("--write requires an empty directory")
        destination.mkdir(parents=True,exist_ok=True)
        for name,raw in files.items():
            p=destination/name; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(raw)
    else:
        for name,raw in files.items():
            if (destination/name).read_bytes()!=raw: raise ValueError("Different authored bytes: "+name)
    print(json.dumps({"status":"authoring-bytes-verified","files":len(files),"source_cases":44,
                      "acceptance_sha256":digest(files["acceptance.json"]),"runtime_executed":False}))
    return 0

if __name__ == "__main__":
    try: raise SystemExit(main())
    except (ValueError, OSError, OverflowError) as error:
        print(str(error),file=sys.stderr); raise SystemExit(1)
