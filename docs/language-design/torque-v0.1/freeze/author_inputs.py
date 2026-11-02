#!/usr/bin/env python3
"""Independently author C090 expectations without importing OntoKin or candidate output.

The literal scalar table below is the authority for the dyadic physical cases.
This script writes review inputs, not a runtime implementation or passing result.
"""
from __future__ import annotations

import base64
from copy import deepcopy
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASELINE = "7b6900baa0357ab96c4639ac5c2ebe4e1791833e"
PACKAGE = "fixture.torque-carriers"


def digest(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def write(path, data):
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    if not isinstance(data, str):
        data = json.dumps(data, sort_keys=True, indent=2, allow_nan=False) + "\n"
    target.write_text(data, encoding="utf-8")
    target.chmod(0o644)


def dec(value):
    value = F(value)
    n, d = value.numerator, value.denominator
    k = 0
    while d % 2 == 0:
        d //= 2
        k += 1
    j = 0
    while d % 5 == 0:
        d //= 5
        j += 1
    if d != 1:
        raise ValueError("not a finite decimal source clock")
    scale = max(k, j)
    number = str(abs(n) * 2 ** (scale-k) * 5 ** (scale-j)).zfill(scale+1)
    result = number if scale == 0 else number[:-scale]+"."+number[-scale:]
    if "." in result:
        result = result.rstrip("0").rstrip(".")
    return ("-" if n < 0 else "") + result


def tor(key, start, duration, magnitude, axis="world_z", target="ball"):
    return {"key": key, "start": str(start), "duration": str(duration),
            "torque": str(magnitude), "axis": axis, "target": target}


# Each row is time, unwrapped phase in radians, signed angular speed in rad/s.
# The independent verifier recomputes these from the input law and refuses a
# changed literal. No runtime output is read by the author or verifier.
CASES = [
    {"id":"p01-spin-up", "torques":[tor("drive",0,2,2)],
     "samples":[["0","0","0"],["1/2","1/4","1"],["1","1","2"],["2","4","4"],["3","8","4"]]},
    {"id":"p02-negative", "torques":[tor("drive",0,1,-3)], "horizon":"2",
     "samples":[["0","0","0"],["1/2","-3/8","-3/2"],["1","-3/2","-3"],["2","-9/2","-3"]]},
    {"id":"p03-braking-reversal", "omega":"2", "torques":[tor("brake",0,2,-2)],
     "samples":[["0","0","2"],["1/2","3/4","1"],["1","1","0"],["3/2","3/4","-1"],["2","0","-2"],["3","-2","-2"]]},
    {"id":"p04-overlap", "torques":[tor("drive",0,3,2),tor("brake",1,1,-1)],
     "samples":[["0","0","0"],["1","1","2"],["3/2","17/8","5/2"],["2","7/2","3"],["3","15/2","5"]]},
    {"id":"p05-cancelling", "omega":"1/2", "torques":[tor("positive",0,2,3),tor("negative",0,2,-3)],
     "samples":[["0","0","1/2"],["1","1/2","1/2"],["2","1","1/2"],["3","3/2","1/2"]]},
    {"id":"p06-zero", "omega":"1/2", "torques":[tor("neutral",0,2,0)],
     "samples":[["0","0","1/2"],["1","1/2","1/2"],["2","1","1/2"],["3","3/2","1/2"]]},
    {"id":"p07-same-net-replacement", "torques":[tor("first",0,1,2),tor("second",1,1,2)],
     "samples":[["0","0","0"],["1/2","1/4","1"],["1","1","2"],["2","4","4"],["3","8","4"]]},
    {"id":"p08-split-neutral-overlap", "torques":[tor("drive",0,3,2),tor("positive",1,1,3),tor("negative",1,1,-3)],
     "samples":[["0","0","0"],["1","1","2"],["2","4","4"],["3","9","6"]]},
    {"id":"p09-completion-starts-rotation", "torques":[tor("long",0,2,2),tor("short",0,1,-2)],
     "samples":[["0","0","0"],["1","0","0"],["3/2","1/4","1"],["2","1","2"],["3","3","2"]]},
    {"id":"p10-half-inertia", "mass":"5", "radius":"1/2", "torques":[tor("drive",0,2,1)],
     "samples":[["0","0","0"],["1","1","2"],["2","4","4"],["3","8","4"]]},
    {"id":"p11-large-inertia", "mass":"10", "radius":"2", "torques":[tor("drive",0,2,4)],
     "samples":[["0","0","0"],["1","1/8","1/4"],["2","1/2","1/2"],["3","1","1/2"]]},
    {"id":"p12-world-x", "axis":"world_x", "torques":[tor("drive",0,1,1,"world_x")], "horizon":"2",
     "samples":[["0","0","0"],["1","1/2","1"],["2","3/2","1"]]},
    {"id":"p13-world-y", "axis":"world_y", "torques":[tor("drive",0,1,1,"world_y")], "horizon":"2",
     "samples":[["0","0","0"],["1","1/2","1"],["2","3/2","1"]]},
    {"id":"p14-offset-reversal", "omega":"-1/1024", "marker_radius":"100", "horizon":"1", "torques":[tor("drive",0,1,"1/512")],
     "samples":[["0","0","-1/1024"],["1/2","-1/4096","0"],["1","0","1/1024"]]},
    {"id":"p15-translation-tie", "position":["1","0","0"], "velocity":["1/4503599627370496","0","0"], "horizon":"1", "torques":[tor("drive","1/2","1/4",2)],
     "samples":[["0","0","0"],["1/2","0","0"],["3/4","1/16","1/2"],["1","3/16","1/2"]]},
    {"id":"p16-neutral-com-force", "omega":"1/2", "torques":[tor("neutral","1/4",1,0)],
     "forces":[{"key":"push","start":"1/2","duration":"1/2","force":["5/2","0","0"]}],
     "samples":[["0","0","1/2"],["1/2","1/4","1/2"],["1","1/2","1/2"],["2","1","1/2"],["3","3/2","1/2"]]},
    {"id":"p17-split-com-force", "omega":"1/2", "torques":[tor("drive",0,2,1)],
     "forces":[{"key":"push","start":"1/2","duration":"1/2","force":["5/2","0","0"]}],
     "samples":[["0","0","1/2"],["1/2","3/8","1"],["1","1","3/2"],["2","3","5/2"],["3","11/2","5/2"]]},
    {"id":"p18-sticky-after-empty", "torques":[tor("neutral",0,"1/2",0),tor("drive",1,1,1)],
     "samples":[["0","0","0"],["1/2","0","0"],["1","0","0"],["2","1/2","1"],["3","3/2","1"]]},
    {"id":"p19-torque-then-impulse", "torques":[tor("drive",0,2,1)], "omega_after_zero_impulse":"5/4", "velocity":["0","1/2","0"],
     "impulse_order":"after", "samples":[["0","0","5/4"],["1","7/4","9/4"],["2","9/2","13/4"],["3","31/4","13/4"]]},
    {"id":"p20-impulse-then-torque", "torques":[tor("drive",0,2,1)], "omega_after_zero_impulse":"5/4", "velocity":["0","1/2","0"],
     "impulse_order":"before", "samples":[["0","0","5/4"],["1","7/4","9/4"],["2","9/2","13/4"],["3","31/4","13/4"]]},
    {"id":"p21-equal-endpoint-reversal", "omega":"-1", "torques":[tor("drive",0,1,2)], "horizon":"1",
     "samples":[["0","0","-1"],["1/4","-3/16","-1/2"],["1/2","-1/4","0"],["3/4","-3/16","1/2"],["1","0","1"]]},
    {"id":"p22-nondyadic-zero-crossing", "omega":"1", "torques":[tor("brake",0,1,-3)], "horizon":"1",
     "samples":[["0","0","1"],["1/4","5/32","1/4"],["1/2","1/8","-1/2"],["3/4","-3/32","-5/4"],["1","-1/2","-2"]]},
    {"id":"p23-partial-sum-overflow-cancels", "torques":[tor("a",0,1,"1e308"),tor("b",0,1,"1e308"),tor("c",0,1,"-1e308"),tor("d",0,1,"-1e308")], "horizon":"1",
     "samples":[["0","0","0"],["1/2","0","0"],["1","0","0"]]},
    {"id":"p24-underflow-is-neutral", "mass":"5", "torques":[tor("tiny",0,1,"5e-324")], "horizon":"1",
     "samples":[["0","0","0"],["1/2","0","0"],["1","0","0"]]},
    {"id":"p25-beyond-horizon", "torques":[tor("long",0,100,2)], "horizon":"1",
     "samples":[["0","0","0"],["1/2","1/4","1"],["1","1","2"]]},
    {"id":"p26-small-marker", "marker_radius":"1/16", "torques":[tor("drive",0,1,1)], "horizon":"2",
     "samples":[["0","0","0"],["1","1/2","1"],["2","3/2","1"]]},
    {"id":"p27-generated-two-carriers", "generated":True, "torques":[tor("drive",0,2,1,target='rack.rotors["first"]')],
     "samples":[["0","0","0"],["1","1/2","1"],["2","2","2"],["3","4","2"]]},
    {"id":"p28-release-then-torque", "release":True, "velocity":["1","0","0"], "torques":[tor("drive",1,1,1)],
     "samples":[["0","0","0"],["1","0","0"],["3/2","1/8","1/2"],["2","1/2","1"],["3","3/2","1"]]},
    {"id":"p30-underflow-replacement", "mass":"5", "torques":[tor("first",0,"1/2","5e-324"),tor("second","1/2","1/2","5e-324")], "horizon":"1",
     "samples":[["0","0","0"],["1/2","0","0"],["1","0","0"]]},
    {"id":"p31-noncommuting-initial-rotation", "initial_quaternion":["0","1","0","0"], "torques":[tor("drive",0,1,1)], "horizon":"2",
     "samples":[["0","0","0"],["1","1/2","1"],["2","3/2","1"]],
     "orientation_reference":"World-Z left product with the saved exact X half-turn: quaternion (0,cos(theta/2),sin(theta/2),0), modulo inherited publication sign. Right multiplication gives the forbidden opposite Y sign."},
]

# The independently calculated exact clock table uses canonical source seconds.
_start=F(float('0.1')); _duration=F(float('0.2')); _end=_start+_duration
_near=F(float('0.3'))
CASES.append({"id":"p29-canonical-clock-addition", "horizon":"1/2", "torques":[tor("drive","0.1","0.2",1)],
    "samples":[["0","0","0"],[str(_start),"0","0"],
               [str(_near),str((_near-_start)**2/2),str(_near-_start)],
               [str(_end),str(_duration*_duration/2),str(_duration)],
               ["1/2",str(_duration*_duration/2+_duration*(F(1,2)-_end)),str(_duration)]]})


def norm(case):
    c = deepcopy(case)
    for k,v in {"mass":"5/2", "radius":"1", "marker_radius":"1", "axis":"world_z", "omega":"0", "horizon":"3", "position":["0","0","0"], "velocity":["0","0","0"], "forces":[]}.items():
        c.setdefault(k,v)
    c["inertia_hex"] = float(F(2,5)*F(float(F(c["mass"]))) * F(float(F(c["radius"])))**2).hex()
    return c


def literal(s):
    # Preserve two deliberate canonical-domain extremes as short source literals.
    return s if "e" in str(s).lower() else dec(s)


def source(case, profile="torque-0.1", version="0.22", include_torque=True):
    c=norm(case)
    library_hash=digest((ROOT/"modules/carriers.ok").read_bytes())
    zero="0"
    axis_index={"world_x":0,"world_y":1,"world_z":2}[c["axis"]]
    omega=[zero,zero,zero]; omega[axis_index]=literal(c["omega"])
    initial_quaternion=c.get('initial_quaternion',['1','0','0','0'])
    # A prescribed release fixture obtains its incoming velocity from the
    # carrier action. Its authored initial velocity must remain zero.
    vel=c["velocity"] if not (c.get("impulse_order") or c.get("release")) else ["0","0","0"]
    head=f'''ontokin "{version}";
module TorqueCases @ "torque-cases";
profile "{profile}";

import rotors @ "rotors" from "{PACKAGE}" version "1.0.0" digest "{library_hash}";

'''
    if c.get("generated"):
        head+='''public class Rack @ "rack-type" {
    public param masses @ "masses": Keyed<Mass> = keyed<Mass> { "first": 2.5[kg], "second": 2.5[kg] };
    public parts rotors @ "rotors": rotors.Rotor for (key, mass) in self.masses {
        body_mass = mass;
        placement = pose(world, vec3(if key == "first" then 0[m] else 5[m], 0[m], 0[m]), quat(1, 0, 0, 0));
    }
    geometry = empty();
    physical = no_body();
}

'''
    if c.get('release'):
        head+='''public class Carrier @ "carrier-type" {
    geometry = empty();
    physical = no_body();
    public site tip @ "tip" {
        pose = pose(self.frame, vec3(0[m], 0[m], 0[m]), quat(1, 0, 0, 0));
        interface = "rigid.origin";
        size = 0[m];
    }
}

'''
    head+=f'''scene Demo @ "demo" {{
    duration = {literal(c["horizon"])}[s];
    gravity = vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2]);
'''
    if c.get("generated"):
        head+='    object rack @ "rack": Rack {}\n'
    else:
        head+=f'''    object ball @ "ball": rotors.Rotor {{
        body_mass = {literal(c["mass"])}[kg];
        body_radius = {literal(c["radius"])}[m];
        marker_radius = {literal(c["marker_radius"])}[m];
        placement = pose(world, vec3({literal(c["position"][0])}[m], {literal(c["position"][1])}[m], {literal(c["position"][2])}[m]), quat({', '.join(initial_quaternion)}));
        velocity = vector(world, {literal(vel[0])}[m/s], {literal(vel[1])}[m/s], {literal(vel[2])}[m/s]);
        omega = vector(world, {omega[0]}[rad/s], {omega[1]}[rad/s], {omega[2]}[rad/s]);
    }}
    object sibling @ "sibling": rotors.Rotor {{
        placement = pose(world, vec3(5[m], 0[m], 0[m]), quat(1, 0, 0, 0));
    }}
'''
    events={}
    for t in c["torques"] if include_torque else []:
        events.setdefault(F(t["start"]),[]).append(f'torque {t["target"]} @ "{t["key"]}" about {t["axis"]} using {literal(t["torque"])}[N*m] for {literal(t["duration"])}[s];')
    for f in c["forces"]:
        events.setdefault(F(f["start"]),[]).append(f'force ball @ "{f["key"]}" using vector(world, {literal(f["force"][0])}[N], {literal(f["force"][1])}[N], {literal(f["force"][2])}[N]) for {literal(f["duration"])}[s];')
    if c.get("impulse_order"):
        line='impulse ball using vector(world, 0[N*s], 1.25[N*s], 0[N*s]) at point(ball.frame, 1[m], 0[m], 0[m]);'
        lines=events.setdefault(F(0),[])
        lines.insert(0 if c["impulse_order"]=="before" else len(lines),line)
    if c.get('release'):
        head=head.replace('    object ball @ "ball": rotors.Rotor {\n','    object ball @ "ball": rotors.Rotor {\n        motion = prescribed;\n')
        # The initially active grip owns this object's pose. The library's
        # inherited default remains available, but an entry placement override
        # would be a second incoming pose authority.
        head=head.replace('        placement = pose(world, vec3(0[m], 0[m], 0[m]), quat(1, 0, 0, 0));\n','',1)
        head+='''    object carrier @ "carrier": Carrier {}
    joint hold @ "hold": grip { parent = carrier.tip; child = ball.origin; }
    action carry @ "carry" = move(carrier, vector(world, 1[m/s], 0[m/s], 0[m/s]), 1[s]);
'''
        events.setdefault(F(0),[]).insert(0,'start carry;')
        events.setdefault(F(1),[]).insert(0,'release hold using incoming;')
    for time, lines in sorted(events.items()):
        head+=f'    at {dec(time)}[s] sequence {{\n'+''.join('        '+s+'\n' for s in lines)+'    }\n'
    return head+'}\n'


def manifest(name):
    return {"schema_version":"ontokin.files/0.2", "entry":{"filename":"main.ok","path":"sources/"+name+".ok"},
            "modules":[{"package_id":PACKAGE,"version":"1.0.0","filename":"carriers.ok","path":"modules/carriers.ok"}],
            "assets":[{"asset_id":"label","sha256":digest((ROOT/"assets/label.png").read_bytes()),"media_type":"image/png","path":"assets/label.png"}]}


def identities(name):
    m=json.loads((ROOT/(name+'.files.json')).read_text())
    units=[{"source_id":"entry","package_id":None,"version":None,"filename":m['entry']['filename'],"source_revision":digest((ROOT/m["entry"]["path"]).read_bytes())}]
    units.extend({'source_id':'package:'+u['package_id']+'@'+u['version'],'package_id':u['package_id'],'version':u['version'],'filename':u['filename'],'source_revision':digest((ROOT/u['path']).read_bytes())} for u in m['modules'])
    identities={"schema_version":"ontokin.bundle/0.2","entry_source_id":"entry","units":sorted(units,key=lambda x:x["source_id"]),
                "assets":sorted([{'asset_id':a['asset_id'],'media_type':a['media_type'],'sha256':digest((ROOT/a['path']).read_bytes()),'byte_length':(ROOT/a['path']).stat().st_size} for a in m['assets']],key=lambda a:a['asset_id'])}
    raw=json.dumps(identities,sort_keys=True,ensure_ascii=False,separators=(",",":"),allow_nan=False).encode()
    return {"program_revision":digest(b"ontokin.bundle/0.2\0"+raw),"manifest":identities}


def span(text, match, occurrence=0):
    raw=text.encode(); needle=match.encode(); at=0
    for _ in range(occurrence+1):
        at=raw.index(needle,at)+(len(needle) if _ < occurrence else 0)
    return {"source_id":"entry","start_byte":at,"end_byte":at+len(needle),"text":match}


def main():
    cases=[]
    for authored in CASES:
        c=norm(authored)
        write('sources/'+c['id']+'.ok', source(c))
        write(c['id']+'.files.json',manifest(c['id']))
        c.update(file_manifest=c['id']+'.files.json', identity=identities(c['id']), expected_compile="accepted_after_implementation", expected_evaluation="accepted_after_implementation", executed_by_author=False)
        c['expected_start_rotation'] = {'p05-cancelling':None,'p06-zero':None,'p09-completion-starts-rotation':'1','p16-neutral-com-force':None,'p18-sticky-after-empty':'1','p23-partial-sum-overflow-cancels':None,'p24-underflow-is-neutral':None,'p28-release-then-torque':'1','p29-canonical-clock-addition':str(_start),'p30-underflow-replacement':None}.get(c['id'],'1/2' if c['id']=='p15-translation-tie' else '0')
        cases.append(c)
        # These controls use the unchanged predecessor language and keep every
        # non-torque physical input. They have independently fixed identities.
        control='control-'+c['id'][4:]
        write('sources/'+control+'.ok',source(c,profile='keyed-membership-0.1',version='0.21',include_torque=False))
        write(control+'.files.json',manifest(control))
        c['predecessor_control']={"file_manifest":control+'.files.json',"identity":identities(control)}
    write('physics-cases.json',{"schema_version":"ontokin.torque-independent-physics/1","baseline":BASELINE,"candidate_output_used":False,"cases":cases})

    # These mathematical domain checks name exact binary64 inputs. The bounded
    # runtime's interpretation, rather than unrounded decimal inputs, is tested.
    numerical=[
      {"id":"num01-inertia-and-alpha","mass":"0.1","radius":"0.2","torque":"0.3","dt":"1/1024","kind":"canonical-rounding"},
      {"id":"num02-underflow","mass":"5","radius":"1","torque":"5e-324","dt":"1","kind":"canonical-rounding"},
      {"id":"num03-near-cancelling","mass":"2.5","radius":"1","torque_sum_terms":["1e308","1e308","-1e308","-1e308"],"expected_net_hex":"0x0.0p+0","kind":"canonical-sum"},
      {"id":"num04-canonical-clock","start":"0.1","duration":"0.2","expected_end_fraction":"10808639105689191/36028797018963968","separately_authored_time":"0.3","expected_equal":False,"kind":"clock"},
      {"id":"num05-translation-tie","position_hex":"0x1.0000000000000p+0","velocity_hex":"0x1.0000000000000p-52","split":"1/2","end":"1","expected_unsplit_hex":"0x1.0000000000001p+0","forbidden_extra_anchor_hex":"0x1.0000000000000p+0","kind":"anchor"},
      {"id":"num06-marker-bound","alpha":"1/512","omega_start":"-1/1024","omega_end":"1/1024","rho":"100","width":"1","expected_phase_chord":"1/4096","expected_position_chord":"51225/2097152","kind":"recording-bound"},
      {"id":"num07-unpublishable-zero-crossing","omega":"1","alpha":"-3","expected_crossing":"1/3","mandatory_source_event":False,"kind":"zero-crossing"}
    ]
    for n in numerical:
        if n['kind']=='canonical-rounding':
            mass=F(float(n['mass'])); radius=F(float(n['radius'])); torque=F(float(n['torque']))
            inertia=F(float(F(2,5)*mass*radius*radius)); alpha=F(float(torque/inertia)); dt=F(n['dt'])
            n['expected']={"mass_hex":float(mass).hex(),"radius_hex":float(radius).hex(),"inertia_hex":float(inertia).hex(),"net_hex":float(torque).hex(),"alpha_hex":float(alpha).hex(),"speed_hex":float(alpha*dt).hex(),"phase_hex":float(alpha*dt*dt/2).hex()}
            n['independent_shadow']={"alpha_reference":str(torque/inertia),"alpha_canonical":str(alpha),"acceleration_error":str(abs(torque/inertia-alpha)),"speed_error_at_dt":str(abs(torque/inertia-alpha)*dt),"phase_error_at_dt":str(abs(torque/inertia-alpha)*dt*dt/2)}
    write('numerical-cases.json',{"schema_version":"ontokin.torque-independent-numerical/1","candidate_output_used":False,"cases":numerical})

    # One pair of independently named intervals drives two occurrences from
    # one immutable library. Repair only the first carrier or its authored input.
    base=norm({"id":"agent-base","horizon":"2","torques":[tor("left-drive",0,2,1),tor("right-drive",0,2,"-1/2",target="sibling")],"samples":[]})
    entry=source(base)
    write('sources/agent-base.ok',entry); write('agent-base.files.json',manifest('agent-base'))
    variants=[('agent-magnitude', 'using 1[N*m]', 'using 2[N*m]'),('agent-duration','using 1[N*m] for 2[s]','using 1[N*m] for 1[s]'),('agent-mass','body_mass = 2.5[kg]','body_mass = 5[kg]'),('agent-radius','body_radius = 1[m]','body_radius = 0.5[m]'),('agent-invalid-duration','using 1[N*m] for 2[s]','using 1[N*m] for 0[s]'),('agent-invalid-mass','body_mass = 2.5[kg]','body_mass = 0[kg]')]
    repairs=[]
    for name,old,new in variants:
        variant=entry.replace(old,new,1)
        write('sources/'+name+'.ok',variant); write(name+'.files.json',manifest(name))
        s=span(entry,old)
        repairs.append({"id":name,"from":identities('agent-base'),"to":identities(name),"file_manifest":name+'.files.json',"patch":{"source_id":"entry","source_revision":digest(entry.encode()),"element_id":["sources","entry"],"start_byte":s['start_byte'],"end_byte":s['end_byte'],"expected_text":old,"replacement":new},"expected_accepted":'invalid' not in name})
    write('agent/repairs.json',{"schema_version":"ontokin.torque-independent-repairs/1","base_identity":identities('agent-base'),"repairs":repairs,"unchanged":{"library":digest((ROOT/'modules/carriers.ok').read_bytes()),"image":digest((ROOT/'assets/label.png').read_bytes()),"sibling_phase_at_2":"-1","sibling_speed_at_2":"-1","sibling_position_at_2":["5","0","0"],"sibling_inertia":"1"},"first_carrier_at_2":{"agent-base":{"phase":"2","speed":"2","inertia":"1"},"agent-magnitude":{"phase":"4","speed":"4","inertia":"1"},"agent-duration":{"phase":"3/2","speed":"1","inertia":"1"},"agent-mass":{"phase":"1","speed":"1","inertia":"2"},"agent-radius":{"phase":"8","speed":"8","inertia":"1/4"}},"invalid_candidates_preserve":"Exact accepted agent-base revision, run prefix, artifacts, sibling and source/library/image identities"})


if __name__ == '__main__':
    main()
