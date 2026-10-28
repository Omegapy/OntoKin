"""Prepare only new C045 evidence files from retained source and review records."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path('/workspace/scratch/bd03c06e866f/ontokin')
META = ROOT.parent / 'c045-meta'
BASE = ROOT / 'docs/engineering/reach-recording-validation-2026-10-23'
EV = BASE / 'checkpoint-045-evidence'
OWNER = 'interactive-reach06-conditional-angular-feasibility-20261026-c045-7f92'
BRANCH = 'work/reach06-conditional-angular-feasibility-20261026-c045'
PARENT = '91e8899ad90f04292dd4aee5aaec8b730b397d45'
TREE = '11d1ce9acc2cb4fa93be44c4772a9e8e3b3270ff'

def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + '\n')

def copy(source, relative):
    target = EV / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        assert target.read_bytes() == source.read_bytes(), target
    else:
        shutil.copyfile(source, target)
    return target

for name in ('analysis-001.stdout', 'analysis-001.stderr', 'analysis-002.stdout',
             'analysis-002.stderr', 'analysis-002.json', 'audit-v001.py'):
    copy(META / name, 'analysis/' + name)
copy(BASE / 'checkpoint-045-audit.py', 'analysis/audit-v002.py')
for name in ('receipt.json', 'stdout.json', 'stderr.txt'):
    copy(META / 'restore' / name, 'restore/' + name)
for name in ('acquire.py', 'authenticated-url-cleanup.json', 'complete-elevated.json',
             'complete-file-verification.json', 'parent-commit-binding.json', 'parent-commit.json',
             'parent.commit', 'priority-default.json', 'priority-elevated.json',
             'refresh-recording-elevated.json', 'tree-verification.json'):
    copy(META / 'recovery' / name, 'recovery/' + name)
for name in ('import_parent.py', 'import-parent-result.json', 'branches-start.json',
             'prs-start.json', 'issue26-start.json', 'startup-ci.json'):
    copy(META / name, 'preparation/' + name)

preparation = {
    'schema': 'ontokin.checkpoint045-preparation-attempts/0.1',
    'failures': [
        {'operation': 'default git ls-remote', 'exit_code': 128,
         'outcome': 'Could not connect to configured browser-proxy port8889; no remote write attempted.'},
        {'operation': 'initial metadata/source materialization command', 'process_started': False,
         'outcome': 'exec-server rejected argument list too long; sequential bounded text writes succeeded.'},
        {'operation': 'default source download', 'receipt': 'recovery/priority-default.json',
         'outcome': '72 URLError entries retained; approved elevated acquisition succeeded.'},
        {'operation': 'first complete source download', 'receipt': 'recovery/complete-elevated.json',
         'outcome': '486 HTTPError entries retained; fresh authenticated directory links completed recovery; exact HTTP cause unestablished.'},
        {'operation': 'initial raw parent commit reconstruction', 'receipt': 'recovery/parent-commit-binding.json',
         'outcome': 'A +0000-only representation failed; exact original -0600 author/committer representation was then SHA-verified.'},
        {'operation': 'source/data audit001', 'command': 'python3 checkpoint-045-audit.py --repo ontokin --retained c044-retained --output c045-meta/analysis-001.json',
         'script': 'analysis/audit-v001.py', 'stdout': 'analysis/analysis-001.stdout',
         'stderr': 'analysis/analysis-001.stderr', 'exit_code': 1,
         'outcome': 'KeyError invocation_id on envelope return; no result JSON produced.',
         'timestamps': None, 'timestamp_qualification': 'No separate local start/end receipt was captured for failed attempt001; tool transcript retains the observed invocation and exit.'}
    ],
    'correction': {'operation': 'source/data audit002', 'result': 'analysis/analysis-002.json',
                   'script': 'analysis/audit-v002.py', 'exit_code': 0,
                   'change': 'Resolve an envelope return through its call_event identifier.'},
    'product_requests': 0, 'failure_records_relabelled': False
}
write(EV / 'preparation/attempts.json', preparation)

audit = json.loads((META / 'analysis-002.json').read_bytes())
runtime = json.loads((META / 'runtime-binding.json').read_bytes())
assert len(runtime) == 65 and all(row['equal'] for row in runtime)
binding = {
    'schema': 'ontokin.checkpoint045-source-binding/0.1', 'owner': OWNER, 'branch': BRANCH,
    'parent_commit': PARENT, 'parent_tree': TREE, 'parent_files': 2356, 'parent_bytes': 490821760,
    'exact_actual_parent_commit_imported': True, 'synthetic_source_commit_created': False,
    'history_qualification': 'Earlier Git history objects were not downloaded; complete parent files/tree and original raw parent commit were verified.',
    'recovery_verification': 'checkpoint-045-evidence/recovery/complete-file-verification.json',
    'tree_verification': 'checkpoint-045-evidence/recovery/tree-verification.json',
    'original_commit_binding': 'checkpoint-045-evidence/recovery/parent-commit-binding.json',
    'actual_git_import': 'checkpoint-045-evidence/preparation/import-parent-result.json',
    'held_runtime': '4ca73909f861fe4bef9694787473621c1d21c140',
    'accepted_reach': 'd2f0088c4f3c1f570630334804a5a8f78e0105ac',
    'native_module_count': 65, 'all_native_modules_equal_held': True, 'native_blobs': runtime,
    'actual_audit_inputs': audit['inputs'], 'C044_evidence_restore': 'checkpoint-045-evidence/restore/receipt.json',
    'replay_qualification': 'Original observed key-order replay uses the exact hash-bound C044 independent native-equality class mapping; native equality and non-angular numeric payloads were not newly executed or traversed.',
    'C044_product_status': {'fresh_original_requests': 2, 'both_exit_codes': 1,
        'shared_operations': 100001, 'reach_operations': 80801,
        'stock_elapsed_seconds': 2.303072429999702, 'capture_elapsed_seconds': 10.730872985000133,
        'elapsed_neutrality': False, 'new_C045_product_requests': 0},
    'C044_preserved_qualifications': ['Actual17:25:13.341049Z launch preceded declared17:26:00Z start; no backdating or rerun.',
        'Unknown partial archive retains unknown origin.', 'Only recorded angular cache payloads were traversed.',
        'Final lookup refused before membership.', 'Schedule does not establish later sample completion.',
        'Original whole-entry retention is not candidate retention.', 'Complete checkout recovery is not formal release input closure.'],
    'all_existing_source_files_preserved': True, 'product_imports_or_runs': 0,
    'complete_release_input_closure_claimed': False
}
write(BASE / 'checkpoint-045-source-binding.json', binding)

ledger = {
    'schema': 'ontokin.checkpoint045-cost-ledger/0.1',
    'candidate': 'B-Angular/full-entry-audit/0.1', 'implemented': False,
    'decision': 'NO-GO for this explicit audit schedule on the observed current32-call group; proper necessary profitability screen declines.',
    'screen': {'predicate': '13*(N-1) > 2*C', 'N': 32, 'C': 256, 'left': 403, 'right': 512, 'passes': False,
        'kind': 'optimistic structural necessary condition, not sufficient admission',
        'proof_qualifications': 'Fresh batch has no private seed. All later calls are optimistically granted as reuse opportunities. Signature discovery and screen costs are not free.'},
    'rejected_route': {'prefix_reuses': 0, 'full_entry_audit_executed': False,
        'added_screening_work': 'must be charged in any implementation; unmeasured', 'measured_cost': None},
    'forced_admitted_route': {'prefix_reuse_maximum': 31, 'prefix_sites_per_reuse': 13, 'gross_ceiling': 403,
        'audit_policy': 'one key admission and one separate value/lifetime admission per existing cache entry',
        'current_entries': 256, 'audit_charge_floor': 512, 'saving_upper_bound': -109,
        'all_other_required_costs_granted_zero_only_for_optimistic_rejection': True,
        'other_work_condition': 'Grant exact original whole-cache behavior and zero induced difference for this rejection. If not proved, admission is unavailable; no favorable induced work is assumed.',
        'late_reuse_selected': False, 'even_with31_late_sites_upper_bound': -78,
        'necessary_prefix_cohort_at_C256': 41, 'necessary_cohort_is_sufficient': False},
    'remaining_nonnegative_cost_terms': ['profitability and structural admissions', 'native owner/dispatch/callback/observer authority',
        'category key/value audit', 'recursive cache key/value checks', 'signature and constant snapshots',
        'copied/reconstructed logical values', 'per-use seed/current-domain checks',
        'same-slot seed attachment and retirement', 'fallback/declined gate work', 'return-boundary receipt', 'cleanup'],
    'entry_category_count': None, 'final222_is_not_entry_count': True,
    'entry_key_tuples': 256, 'entry_immediate_child_occurrences': 1656,
    'immediate_children_are_selected_cost_units': False,
    'guard_domain': {'input_max_bits': 2048, 'native_full_cap': 32768, 'prefix_max_prospective_bits': 4327,
        'current_sq_denominator_bits': 1075, 'authority_proved_by_width': False},
    'preserved_paths': ['original bound/selector admission and whole-cache warm route',
        'ten ordinary position sites', 'four selected dynamic position sites', 'both ordered short-circuit comparisons',
        'original late multiplication', 'optional cell radii', 'whole-cache publication', 'cold final1075-bit/domain guards'],
    'C043_unconditional_counterexample_saving_upper_bounds': [-2, -3, -64],
    'candidate_cache_or_numerical_replay': False, 'candidate_retention_established': False,
    'complete_P23_cost_or_tail_deficit': None, 'positive_complete_bound_established': False,
    'universal_angular_impossibility_claimed': False, 'runtime_scope_selected': False
}
write(BASE / 'checkpoint-045-cost-ledger.json', ledger)

next_scope = {
    'schema': 'ontokin.checkpoint045-next-scope/0.1', 'next_checkpoint': 'C046',
    'task': 'Source/retained-data audit of required L03 cursor retirement/direct reseeding and existing series-coefficient cache lifetime',
    'start': 'New owned branch from freshly observed finalC045 publication after live Issue26/heads/lease reconciliation.',
    'immediate_mode': 'source and retained evidence only; no product rerun or runtime implementation',
    'evidence': {'historical_C033': {'source': 'a7af3ee6ad0a22869b3b26fc45ad4f42f0191c41',
        'key_index': 153, 'clock': '244/89', 'carrier': 'rig.arm.forearm.frame', 'cursor_updates': 64,
        'refused_series_coefficient': {'exponent': 129, 'degree': 14, 'index': 7},
        'earlier_reseed_key': 66, 'next_phase_start_key': 88,
        'qualification': 'Historical observed locals; no automatic transfer to current runtime.'},
        'current_C035': {'source': '4ca73909f861fe4bef9694787473621c1d21c140',
            'L03_shared_operations': 100001, 'L03_reach_operations': 95767,
            'status': 'failed and held, with adverse diagnostic timing',
            'qualification': 'Equal failure totals do not establish equal locals or cache chronology.'}},
    'source_targets': ['ontokin/reach_reference_center.py:_orientation', 'ontokin/reach_reference_center.py:_seed',
        'ontokin/reach_reference.py:_series_coefficients', 'ontokin/reach_reference.py:direct source reconstruction',
        'native work/callback/cache helpers and relevant callers'],
    'required_work': ['restore and verify original C033/C035 evidence without executing archived product drivers',
        'compare complete relevant current/original source bodies and ownership paths',
        'census supported retirements, seeds, exact coefficient keys and existing cache outcomes/lifetimes',
        'distinguish pre-membership refusal from a miss and completed work from unvisited tail',
        'publish precise evidence gaps if current chronology cannot be bound',
        'require structural eligibility, complete charged bound and independent proof before any implementation'],
    'preserve': ['64-update limit and required direct seed', 'original independent source equations',
        'coefficient/remainder/precision proof', 'original L03 end4/fps1/helpersfalse/tolerances',
        '100000 operations/30000ms/32768bits/256cache entries', 'callback identity and pending publication',
        'all failed results and C035 hold', 'other-owner branches/main/sharedSTATUS'],
    'conditional_later_capture': 'Only if necessary after separate ownership, complete source closure, independent instrumentation review and an actually active exclusive window; use fresh unchanged original requests.',
    'forbidden_in_immediate_scope': ['product request or failed-tail continuation', 'runtime implementation',
        'raised cursor/cap/tolerance', 'extra private numeric allowance', 'assumed coefficient-cache hits',
        'hosted jobs or main merge'],
    'recording_gate': '24/28', 'full_goal_completed': False
}
write(BASE / 'checkpoint-045-next-scope.json', next_scope)

review_rows = []
for role in ('authority', 'cost'):
    for suffix in ('md', 'json'):
        p = BASE / 'checkpoint-045-reviews' / (role + '.' + suffix)
        data = p.read_bytes()
        review_rows.append({'role': role, 'path': str(p.relative_to(BASE)), 'bytes': len(data),
                            'sha256': hashlib.sha256(data).hexdigest()})
write(BASE / 'checkpoint-045-reviews.json', {'schema': 'ontokin.checkpoint045-review-index/0.1',
    'reviews': review_rows, 'independence': {'authority': 'Separate source authority review and independent bit-width derivation; did not execute root complete original cache-order audit.',
        'cost': 'Separately authored source/metadata cost review; reviewer contributed to defining the conservative candidate cost argument during design. This is disclosed, not blind independent algorithm design.'},
    'main_report_and_handoff_consistency_review': 'Both reviewers read finaldrafts and reported no material correction; no product execution.',
    'later_final_publication_audit': 'Recorded separately in checkpoint-045-validation.json after actual published-core validation.'})

members = []
for p in sorted(EV.rglob('*')):
    if p.is_file():
        data = p.read_bytes()
        members.append({'path': str(p.relative_to(BASE)), 'bytes': len(data), 'sha256': sha(data)})
write(BASE / 'checkpoint-045-evidence-manifest.json', {'schema': 'ontokin.checkpoint045-evidence-manifest/0.1',
    'created_utc': datetime.now(timezone.utc).isoformat(), 'members': members,
    'files': len(members), 'bytes': sum(row['bytes'] for row in members),
    'storage': 'plain repository files; no new archive', 'prior_C044_archive_restored': True,
    'product_imports_or_requests': 0})
print(json.dumps({'core_evidence_files': len(members), 'core_evidence_bytes': sum(row['bytes'] for row in members),
                  'metadata_audit_checks': audit['checks_passed'], 'new_runtime_files': 0}))
