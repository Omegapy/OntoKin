import sys
sys.dont_write_bytecode=True
from pathlib import Path
from fractions import Fraction as Q
import hashlib,json,math,random,struct,time
root=Path('docs/language-design/planar-reach-v0.1')
sys.path.insert(0,str(root.resolve()))
import interval_oracle as p
files=['interval_oracle.py','numeric-admission.md','verify_rounding.py','rounding-certificates.json']
before={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in files}
started=time.monotonic()
rng=random.Random(2026102014)
seeds=[0,1,2,3,0x000ffffffffffffe,0x000fffffffffffff,0x0010000000000000,0x0010000000000001,0x3fefffffffffffff,0x3ff0000000000000,0x3ff0000000000001,0x3ff0000000000002,0x7feffffffffffffe,0x7fefffffffffffff]
seeds += [rng.randrange(p.MAX_FINITE_BITS+1) for _ in range(72)]
rounding_checks=cell_checks=0
for magnitude in seeds:
    for bits in (magnitude,magnitude|p.SIGN):
        lo,hi,ties=p.rounding_cell(bits)
        value=p.bits_fraction(bits)
        probes=[lo,hi,value,(lo+value)/2,(hi+value)/2,lo-(hi-lo)/4,hi+(hi-lo)/4]
        for exact in probes:
            try: expected=float(exact)
            except OverflowError: expected=-math.inf if exact<0 else math.inf
            expected_bits=p.binary64_bits(expected) if expected!=0 else 0
            actual=p.round_binary64(exact)
            assert actual==expected_bits,(hex(bits),exact,hex(actual),hex(expected_bits))
            rounding_checks+=1
            accepted=p.cell_contains(p.Interval(exact,exact),bits)
            normalized_bits=bits if magnitude else 0
            assert accepted==(actual==normalized_bits),(hex(bits),exact,accepted,hex(actual))
            cell_checks+=1
quadrants=[]
for target in ([2,0,0],[0,2,0],[-2,0,0],[0,-2,0],[1,1,0],[-1,1,0],[-1,-1,0],[1,-1,0]):
    for branch in ('positive','negative'):
        result=p.prove_solution([1,1],target,branch)
        assert result['status']=='proved'
        q1,q2=[p.bits_float(int(c['canonical_bits'],16)) for c in result['coordinates']]
        elbow=(1 if branch=='positive' else -1)*math.acos((target[0]**2+target[1]**2-2)/2)
        shoulder=math.atan2(target[1],target[0])-math.atan2(math.sin(elbow),1+math.cos(elbow))
        shoulder=(shoulder+math.pi)%(2*math.pi)-math.pi
        assert abs(q1-shoulder)<2e-15 and abs(q2-elbow)<2e-15,(target,branch,q1,q2,shoulder,elbow)
        quadrants.append({'target':target,'branch':branch,'bits':[c['canonical_bits'] for c in result['coordinates']]})
# This target's shoulder is just above the half-smallest-subnormal midpoint:
# asin(delta/2) = delta/2 + positive O(delta**3). The finite schedule must not
# claim either rounding cell when it cannot distinguish that exact offset.
tiny=p.bits_float(1)
budget=p.Budget()
try:
    p.prove_solution([1,1],[0,tiny,0],budget=budget)
except p.NumericFailure:
    inconclusive='NumericFailure'
else:
    raise AssertionError('half-subnormal shoulder must remain inconclusive in the fixed schedule')
# Cancellation after work has started must propagate without being recast as
# another precision attempt or successful proof.
polls=[0]
def delayed_cancel():
    polls[0]+=1
    return polls[0]>=250
cancel_budget=p.Budget(cancel=delayed_cancel)
try:
    p.prove_solution([1,1],[1,1,0],budget=cancel_budget)
except p.Cancelled:
    assert cancel_budget.interval_operations>0
else:
    raise AssertionError('mid-proof cancellation swallowed')
after={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in files}
assert before==after
print(json.dumps({'status':'passed','scope':'independent focused pure numerical review; no source runtime/Agent/SQLite/export/full suite','rounding_fraction_conversion_crosschecks':rounding_checks,'cell_membership_crosschecks':cell_checks,'axis_and_quadrant_solutions':quadrants,'finite_inconclusive':{'outcome':inconclusive,'work':budget.record()},'mid_proof_cancellation':{'polls':polls[0],'work':cancel_budget.record()},'elapsed_seconds':time.monotonic()-started,'before':before,'after':after},indent=2,sort_keys=True))
