"""Reviewer-authored assertions about frozen synthetic case mutations only.

This does not implement the proposed loader policy, call production code, or
read any logical host path. Each assertion checks a particular authored cause
against independently decoded bytes and supplied static JSON observations.
"""
import json
from pathlib import Path, PurePosixPath

root = Path('/workspace/scratch/2ad494d5da19/session_evidence')
candidate = root / 'loader_design/candidate002'
out = root / 'design_review/candidate002'
facts = {r['id']: r for r in json.loads((out / 'CASE-FACTS.json').read_text())}
elf = json.loads((out / 'ELF-FACTS.json').read_text())
contexts = {p.stem: json.loads(p.read_text()) for p in (candidate / 'fixture_inputs').glob('*.json')}
results = []


def add(ident, statement, condition, expected_rule=None, details=None):
    row = {'case': ident, 'review_statement': statement, 'pass': bool(condition), 'details': details}
    if expected_rule is not None:
        row['expected_rule'] = expected_rule
        row['pass'] = row['pass'] and facts[ident]['expected'].get('rule_id') == expected_rule
    results.append(row)


for ident, c in contexts.items():
    if not ident.startswith('N'):
        continue
    f = facts[ident]
    n = int(ident[1:3])
    p, s, k = c['plan_selection'], c['subject'], c['kernel']
    meta = f['decoded_metadata']
    if n == 1:
        add(ident, 'Only the schema is the old version while the profile is new.', p['schema'].endswith('/0.1.0') and p['profile'] == 'linux-glibc-declared-python-origin-rpath-v1', 'LP-SCHEMA-PROFILE')
    elif n == 2:
        add(ident, 'Only the profile is old while the schema is new.', p['schema'].endswith('/0.1.1') and p['profile'] == 'linux-glibc-declared-closure-v1', 'LP-SCHEMA-PROFILE')
    elif n in (3, 4, 32):
        cond = (p['origin_object_present'] is False if n == 3 else p['origin_object_unknown_keys'] == ['approved'] if n == 4 else type(k['at_secure_claim']) is bool)
        add(ident, 'The named closed-shape/type distinction is present.', cond, 'LP-CLOSED-SHAPE')
    elif n in (5, 6, 7):
        field = {5:'external_digest_matches', 6:'variant_descriptor_matches', 7:'rationale_descriptor_matches'}[n]
        add(ident, 'The named external binding observation is false.', p[field] is False, 'LP-EXTERNAL-DIGEST' if n == 5 else 'LP-VARIANT-BINDING')
    elif 8 <= n <= 11:
        add(ident, 'The token subject is a different operational role.', s['role'] == {8:'shared_object', 9:'node', 10:'ldd_target', 11:'git'}[n], 'LP-ROLE')
    elif n == 12:
        add(ident, 'The subject invocation is explicit-loader, which the proposal excludes.', s['invocation'] == 'explicit-loader', 'LP-INVOCATION')
    elif n in (13,14,15):
        cond = k['proc_exe_path'] == '/fixture/ld-linux-x86-64.so.2' if n == 13 else k['proc_exe_path'].endswith(' (deleted)') if n == 14 else k['proc_exe_path'] is None and k['read_status'] == 'unavailable'
        add(ident, 'The kernel executable path is foreign, deleted, or unavailable as named.', cond, 'LP-KERNEL-EXE')
    elif n == 16:
        add(ident, 'The kernel file inode differs from the subject inode.', k['proc_file_identity']['inode'] != s['inode'], 'LP-KERNEL-IDENTITY')
    elif n in (17,18):
        add(ident, 'The asserted origin differs from the immediate subject parent.', c['origin_claim'] != str(PurePosixPath(s['path']).parent), 'LP-ORIGIN')
    elif 19 <= n <= 23:
        cond = s['kind'] == 'symlink' if n == 19 else any(g['path'] == c['origin_claim'] and g['kind'] == 'symlink' for g in c['guards']) if n == 20 else any(g['path'] == str(PurePosixPath(c['origin_claim']).parent) and g['kind'] == 'symlink' for g in c['guards']) if n == 21 else s['nlink'] == 2 if n == 22 else any(g['path'] == c['expanded_claim'][0] and g['kind'] == 'symlink' for g in c['guards'])
        add(ident, 'The named subject/origin/ancestor/sibling alias or hardlink is present as inert JSON.', cond, 'LP-ALIAS')
    elif n == 24:
        add(ident, 'The declared subject binding does not match.', s['descriptor_matches'] is False, 'LP-SUBJECT-BINDING')
    elif n == 25:
        add(ident, 'Operational admission is requested for synthetic bytes that differ from the exact real pin.', s['enforce_operational_pin'] is True and (s['actual_bytes']['sha256'],s['actual_bytes']['size_bytes']) != (s['operational_pin']['sha256'],s['operational_pin']['size_bytes']), 'LP-SELECTED-PIN')
    elif 26 <= n <= 31:
        a = f['auxv']
        cond = a['secure_values'] == [1] if n == 26 else a['secure_values'] == [] if n == 27 else a['secure_values'] == [0,0] if n == 28 else a['terminator_indexes'] == [] if n == 29 else a['remainder_bytes'] == 1 if n == 30 else a['pair_count'] == 257 and a['remainder_bytes'] == 0 and a['secure_values'] == [0] and a['terminator_indexes'] == [256]
        add(ident, 'The independent little-endian auxiliary decoder confirms the named secure/shape/length cause.', cond, 'LP-SECURE' if n == 26 else 'LP-BOUND' if n == 31 else 'LP-AUXV', a)
    elif 33 <= n <= 46:
        add(ident, 'Independent ELF decoding does not yield the sole admitted RPATH with absent RUNPATH.', (meta['rpath'],meta['runpath']) != (['$ORIGIN/../lib'],[]), 'LP-RAW-RPATH', {'rpath':meta['rpath'],'runpath':meta['runpath']})
    elif 47 <= n <= 50:
        e = elf[f['image']['path']]
        ordinary = set(range(1,31)) | {32,33,34,35,36,37,0x6ffffef5,0x6ffffff0,0x6ffffff9,0x6ffffffa,0x6ffffffb,0x6ffffffc,0x6ffffffd,0x6ffffffe,0x6fffffff}
        cond = any(x & ~8 for x in e['flags']) if n == 47 else any(x & ~(1|0x08000000) for x in e['flags1']) if n == 48 else any(t and t not in ordinary for t,v in e['dynamic_entries']) if n == 49 else bool(e['duplicate_tags'])
        add(ident, 'Independent dynamic-table decoding confirms the pre-existing flag/tag/uniqueness refusal.', cond, 'LEGACY-ELF-GUARD', {'flags':e['flags'],'flags1':e['flags1'],'duplicate_tags':e['duplicate_tags']})
    elif n in (51,52):
        cond = c['expanded_claim'] != [str(PurePosixPath(c['origin_claim']).parent/'lib')] if n == 51 else c['expanded_claim'][0] not in c['search_directories']
        add(ident, 'The derived directory claim is wrong or absent from bound search directories.', cond, 'LP-EXPANDED')
    elif n in (53,54):
        actual = {v for image in c['closure_images'] for v in image['needed']}
        claimed = set(c['needed_names_claim'])
        add(ident, 'The claimed dependency-name union is missing a name or adds an undeclared name.', bool(actual-claimed) if n == 53 else bool(claimed-actual), 'LP-NAMES', {'missing':sorted(actual-claimed),'extra':sorted(claimed-actual)})
    elif n in (55,56):
        cond = [v['suffix'] for v in c['variants']] != c['variant_review']['suffixes'] if n == 55 else any(v['path'] != str(PurePosixPath(c['expanded_claim'][0])/v['suffix']) for v in c['variants'])
        add(ident, 'The variant inventory omits a suffix or gives an unrelated path.', cond, 'LP-VARIANTS')
    elif n == 57:
        add(ident, 'The synthetic source-review completeness state is unsupported.', c['variant_review']['completeness'] == 'unsupported', 'LP-VARIANT-SEMANTICS')
    elif n == 58:
        add(ident, 'A declared absence observation has changed to false.', any(v['absent'] is False for v in c['absence_guards'].values()), 'LP-ABSENCE')
    elif 59 <= n <= 65:
        matches = f['candidate_matches']
        cond = bool(matches)
        if n <= 62:
            cond = cond and matches[0]['entry']['kind'] == {59:'file',60:'symlink',61:'directory',62:'special'}[n]
        elif n == 63:
            cond = cond and any('/glibc-hwcaps/' in v['path'] for v in matches)
        elif n == 64:
            cond = cond and any('/tls/' in v['path'] for v in matches)
        elif n == 65:
            cond = cond and any(v['name'] == 'libgamma.so' for v in matches) and 'libgamma.so' in {v for i in c['closure_images'] for v in i['needed']}
        add(ident, 'A declared needed basename exists at the intended base/hwcaps/TLS/extension candidate location.', cond, 'LP-CANDIDATE', matches)
    elif n in (66,67):
        cond = any('$' in name for im in c['closure_images'] for name in im['needed']) if n == 66 else any('$' in (im['soname'] or '') for im in c['closure_images'])
        add(ident, 'A dependency or SONAME contains a token and must fail before ordinary name-union agreement.', cond, 'LP-NAME-TOKEN')
    elif n == 68:
        add(ident, 'An image other than the subject has token-bearing raw metadata.', any(im['id'] != 'python' and any('$' in p for p in im.get('raw_rpath',[])) for im in c['closure_images']), 'LP-ROLE')
    elif n == 69:
        add(ident, 'The pre-normalization string is 4097 bytes; refusal is valid but is not isolated in candidate002.', f['path_dimensions']['pre_normalization']['utf8_bytes'] == 4097, 'LP-BOUND')
    elif n in (70,71,72):
        counts = f['finite_counts']
        cond = counts['needed_names'] == 4097 and counts['suffixes'] <= 128 and counts['candidate_product'] <= 32768 if n == 70 else counts['needed_names'] <= 4096 and counts['suffixes'] == 129 and counts['candidate_product'] <= 32768 if n == 71 else counts['needed_names'] == 257 and counts['suffixes'] == 128 and counts['present_variants'] == 128 and counts['candidate_product'] == 32896
        cond = cond and counts['maximum_needed_per_image'] <= 256 and all(v['utf8_bytes'] <= 4096 and v['parts_including_root'] <= 128 for v in f['path_dimensions'].values())
        add(ident, 'Only the named early cardinality ceiling is exceeded; later shape/closure checks are deliberately not reached.', cond, 'LP-BOUND', counts)
    elif n == 73:
        add(ident, 'The independently decoded image machine is AArch64, while the new selected-subject rule requires x86-64.', meta['machine'] == 183, 'LP-SUBJECT-MACHINE')

for ident in ['L04_origin_still_refuses','L05_braced_still_refuses','L06_both_tags_refuse','L07_origin_flag_refuses']:
    f=facts[ident]; m=f['decoded_metadata']; ex=f['expected']; e=elf[f['image']['path']]
    if ident.startswith(('L04','L05')):
        cond=any('$' in v for v in m['rpath']) and ex['reason']=='Unreviewed loader token expansion'
    elif ident.startswith('L06'):
        cond=bool(m['rpath'] and m['runpath']) and all('$' not in v for v in m['rpath']+m['runpath']) and ex['reason']=='Conflicting legacy and modern search paths'
    else:
        cond=any(x & ~8 for x in e['flags']) and ex['reason']=='Unsupported dynamic flags'
    add(ident,'Legacy refusal and exact reason match the current source guard ordering.',cond,'LEGACY-UNCHANGED')

for ident in ['D01_postapproval_new_candidate','D02_origin_inode_changed','D03_kernel_origin_changed']:
    c=contexts[ident]; f=facts[ident]
    if ident.startswith('D01'):
        cond=c['approved_before']==contexts['P01_nonselecting_base']['search_directories'] and bool(f['candidate_matches']) and f['expected']['cause_code']=='CHI-LOADER'
    elif ident.startswith('D02'):
        cond=c['approved_before']==contexts['P01_nonselecting_base']['guards'] and c['guards'][3]['inode']!=c['approved_before'][3]['inode'] and f['expected']['cause_code']=='CHI-PATH'
    else:
        cond=c['approved_before']==contexts['P01_nonselecting_base']['kernel'] and c['kernel']['proc_exe_path']!=c['approved_before']['proc_exe_path'] and f['expected']['cause_code']=='CHI-INSPECTOR'
    add(ident,'Exact preapproval state and a changed after-observation support the retained CHI-DRIFT cause.',cond and c['phase']=='recheck' and f['expected']['code']=='CHI-DRIFT','LP-RECHECK')

# Adequacy checks are deliberately separate from validity of the stated refusal.
for ident in ['P07_expansion_4096_bytes','N69_expansion_4097_bytes']:
    c=contexts[ident]
    needed={str(q) for s in [c['subject']['path'],*c['expanded_claim']] for q in PurePosixPath(s).parents}
    needed.update(c['expanded_claim'])
    given={g['path'] for g in c['guards']}
    add(ident,'All synthetic existing ancestor directories required for this origin are explicitly guarded.',needed<=given,details={'needed_directory_count':len(needed),'given_count':len(given),'missing_count':len(needed-given),'extraneous_count':len(given-needed)})
f=facts['N69_expansion_4097_bytes']
over={k:v for k,v in f['path_dimensions'].items() if v['utf8_bytes']>4096}
add('N69_expansion_4097_bytes','Only pre-normalization exceeds the byte ceiling; no second path can mask a missing check.',set(over)=={'pre_normalization'},details=over)

report={'schema':'ontokin.c271.p11-independent-static-case-semantics/1','candidate':'candidate002',
        'check_count':len(results),'passed':sum(r['pass'] for r in results),'failed':[r for r in results if not r['pass']],
        'checks':results,'product_imports':0,'product_calls':0,'host_observations':0,
        'claim':'Case-specific supplied causes and exact old-source refusal correspondence; not a product run or a complete loader implementation.'}
(out/'CASE-SEMANTICS.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2,sort_keys=True))
raise SystemExit(1 if report['failed'] else 0)
