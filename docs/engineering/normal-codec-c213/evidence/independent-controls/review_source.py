#!/usr/bin/env python3
"""Check exact selected source provenance without importing the probe runner."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def body(text,signature):
    start=text.index(signature);opening=text.index('{',start);depth=0
    for k in range(opening,len(text)):
        depth+=(text[k]=='{')-(text[k]=='}')
        if depth==0:return text[start:k+1]+'\n'
    raise ValueError('missing complete body')

ap=argparse.ArgumentParser();ap.add_argument('--repo',type=Path,required=True);ap.add_argument('--historical-package',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
root=a.repo/'docs/engineering/normal-codec-c213';checks=[]
def check(name,ok,**detail):checks.append({'name':name,'passed':bool(ok),**detail})
binding=json.loads((root/'SOURCE-BINDINGS.json').read_text())
check('pinned_source_commit',binding['upstreamCommit']=='32f5fdce0a0a571a39198edf8d7b5d719bf59f2c')
for row in binding['upstreamFiles']:
    check('source_hash:'+row['path'],digest(root/row['path'])==row['sha256'])
for name in ('mesh_normals.cc','BLI_math_base.hh'):
    other=a.historical_package/'evidence/c212/blender-mechanism'/name
    check('retained_c212_source_equality:'+name,(root/'upstream'/name).read_bytes()==other.read_bytes())
for name in ('math_vector_inline.c','math_base_inline.c','BLI_math_vector.hh'):
    # Independent source copies were frozen with a documented extra terminal LF.
    check('independently_retrieved_source_equality:'+name,(root/'upstream'/name).read_bytes()==(HERE/'source'/name).read_bytes()[:-1])
include=(root/'codec_exact.inc').read_text();mesh=(root/'upstream/mesh_normals.cc').read_text();base=(root/'upstream/BLI_math_base.hh').read_text()
selected={}
for text,signature in [(mesh,'MINLINE float unit_short_to_float('),(mesh,'MINLINE short unit_float_to_short('),(base,'inline float safe_acos_approx('),(mesh,'static float3 corner_space_custom_data_to_normal('),(mesh,'short2 corner_space_custom_normal_to_data(')]:
    b=body(text,signature);name=signature.split('(')[0].split()[-1];selected[name]=hashlib.sha256(b.encode()).hexdigest();check('complete_exact_body:'+name,b in include)
final=json.loads((HERE/'observed-final.json').read_text());initial=json.loads((HERE/'observed-initial.json').read_text())
check('selected_function_hashes_match_independent_extraction',final['selectedFunctionSha256']==selected)
check('selected_functions_unchanged_by_review_corrections',initial['selectedFunctionSha256']==final['selectedFunctionSha256'])
for name,expected in final['sourceBindings'].items():check('final_observation_binds_current_source:'+name,digest(root/name)==expected)
old={r['id']:r for r in initial['rows']};keys=('status','encoded','decoded','trace','metrics','approximate','normalizedInput','valueFloat32','scaled','shifted','decodedFraction','exactDoubleReference','normalizationCollapsed')
check('all_observed_numeric_values_unchanged_by_corrections',all(all(row.get(k)==old[row['id']].get(k) for k in keys) for row in final['rows']))
supp=json.loads((HERE/'supplemental-observed.json').read_text());declared=json.loads((HERE/'supplemental-cases.json').read_text())
check('supplemental_exact_case_identity_set',{x['id'] for x in supp['rows']}=={x['id'] for x in declared['cases']} and len(supp['rows'])==len(declared['cases']))
for row in supp['rows']:
    prefix='supplemental:'+row['id']+':'
    check(prefix+'explicit_refusal',row['status']=='rejected' and bool(row.get('reason')))
    check(prefix+'encoder_not_executed',row['codecEncoderExecuted'] is False)
    check(prefix+'decoder_not_executed',row['codecDecoderExecuted'] is False)
    check(prefix+'normalization_not_executed',row['inputNormalizationExecuted'] is False)
    check(prefix+'no_helper_executed',row['standaloneHelperExecuted'] is None)
    check(prefix+'accurate_process_observation',row['probeProcessExecuted']==(row['id']=='zero_sentinel_nonzero'))
for row in final['rows']:
    accepted=row['status']=='accepted';op=row['operation'];mode=row['mode'];prefix='execution_observation:'+row['id']+':'
    check(prefix+'encoder',row['codecEncoderExecuted']==(accepted and op=='roundtrip'))
    check(prefix+'decoder',row['codecDecoderExecuted']==(accepted and op in ('roundtrip','decode')))
    expected_norm=(accepted and op=='roundtrip' and mode=='strict') or row.get('reason')=='normal_collapsed_by_upstream_normalize'
    check(prefix+'input_normalization',row['inputNormalizationExecuted']==expected_norm)
env=final['environment']
check('observed_float32_and_short_domain',env['floatBytes']==4 and env['shortMax']==32767 and env['FLT_EVAL_METHOD']==0)
check('rounding_mode_actually_verified',env['roundingMode']=='FE_TONEAREST' and env['roundingModeVerified'] is True)
check('separate_subnormal_observations',env['float32SubnormalParsingPreserved'] is True and env['float32SubnormalArithmeticPreserved'] is True)
manual=[
 {'topic':'Scalar dot operation order','finding':'The wrapper accumulates a[0]*b[0], then += the two remaining float products, matching BLI_math_vector.hh dot<float,3>.'},
 {'topic':'Normalization route','finding':'The wrapper uses squared-length cutoff 1e-35f, float sqrt and per-component division, matching C++ math::normalize used by the selected from-verts input route; it does not substitute the separate C reciprocal-multiply function.'},
 {'topic':'Projection and decoded additions','finding':'float3 addition/multiplication/division and mul_v3_v3fl/madd_v3_v3fl match pinned componentwise operations; -ffp-contract=off and no-fast-math preserve this selected order.'},
 {'topic':'Component comparison','finding':'is_zero_v3 exact equality and compare_ff fabsf(a-b)<=limit match independent pinned helpers.'},
 {'topic':'Frame validation','finding':'The wrapper checks finite/unit/orthogonal/right-handed basis and stated ranges before encoder execution. Zero-range decoder diagnostics remain explicit and separate. This is harness policy, not native fan construction.'},
 {'topic':'Decoder short domain correction','finding':'Full int16 decoding, including -32768, follows the source. The initial reviewer expectation was narrower than the upstream decoder; ORACLE-CORRECTION.json preserves and explains the corrected assertion.'},
 {'topic':'Missing explicit input correction','finding':'Initial source defaulted required normal/short/value fields. Corrected source rejects these before probe execution; eleven supplemental controls verify refusal and execution claims.'},
 {'topic':'Scope','finding':'No OntoKin runtime, existing receiver, fan-construction algorithm, original strict tolerance or historical evidence is modified by this implementation. No Blender process is invoked.'}
]
result={'schema':'ontokin.c213.independent-source-review/0.1','passed':all(x['passed'] for x in checks),'checkCount':len(checks),'failedChecks':[x for x in checks if not x['passed']],'reviewedCommit':subprocess.check_output(['git','-C',str(a.repo),'rev-parse','HEAD'],text=True).strip(),'workingTreeStatus':subprocess.check_output(['git','-C',str(a.repo),'status','--porcelain'],text=True),'selectedFunctions':selected,'manualSourceReview':manual,'checks':checks,'limitations':['This scalar extraction is not a compiled Blender build or native-binary attestation.','Source-level equivalence of selected adapters is reviewed; compiler/platform/libm equivalence to C211 remains unproved.','The investigation supports conditional counterexamples and finite observations only; no new receiving loss budget is approved.']}
a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('passed','checkCount','failedChecks','reviewedCommit','workingTreeStatus')}));raise SystemExit(0 if result['passed'] else 1)
