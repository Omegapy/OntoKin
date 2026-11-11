"""Independent read-only audit of the completed, nonresumable C200 execution.

No Blender, Node, receiving worker, lifecycle control or subprocess is launched.
The review retains raw result bytes and creates a separate final disposition.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import stat
import struct
import sys
import tarfile
import time

ROOT = Path('/workspace/scratch/ef5ae272e66e/ontokin')
BASE = ROOT.parent
C200 = ROOT / 'docs/engineering/static-tray-exporter-c200'
C199 = ROOT / 'docs/engineering/static-tray-qualification-c199'
SCHEDULE = BASE / 'c200-native'
DRIVER = BASE / 'c200-native-driver'
CAPTURE = C200 / 'evidence/native-execution'
OUT = C200 / 'evidence/result-review'
VISUAL = BASE / 'worker-review-c200/visual/VISUAL-REVIEW.json'
NUMERIC = BASE / 'audit-repository/numeric-result-review.json'
sys.path[:0] = [str(ROOT), str(C200)]
from prototypes.static_tray_v01.lock import verify_lock
from qualification_gate import verify_revision

CHECKS = Counter()


def require(condition, name):
    if not condition:
        raise AssertionError(name)
    CHECKS[name.split(':', 1)[0]] += 1


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def binding(path):
    p = Path(path)
    return {'path': str(p), 'sha256': digest(p), 'size_bytes': p.stat().st_size}


def read(path):
    return json.loads(Path(path).read_bytes())


def matches(path, row):
    require(not Path(path).is_symlink() and Path(path).is_file(), 'file kind:' + str(path))
    require(digest(path) == row['sha256'], 'file digest:' + str(path))
    require(Path(path).stat().st_size == row.get('size_bytes', row.get('bytes')), 'file size:' + str(path))


def sealed(candidate, expected_hash):
    candidate = Path(candidate)
    require(digest(candidate / 'closure.json') == expected_hash, 'closure identity:' + str(candidate))
    manifest = read(candidate / 'closure.json')
    actual = {p.relative_to(candidate).as_posix() for p in candidate.rglob('*') if p.is_file()}
    require(actual == set(manifest['files']) | {'closure.json'}, 'closure inventory:' + str(candidate))
    require(not any(p.is_symlink() for p in candidate.rglob('*')), 'closure no aliases:' + str(candidate))
    for name, row in manifest['files'].items():
        path = candidate / name
        matches(path, row)
        require(stat.S_IMODE(path.stat().st_mode) == 0o444, 'closure immutable mode:' + str(path))
    return manifest


def process_check(process, argv, environment, label):
    require(process['argv'] == argv and process['environment'] == environment, 'actual process inputs:' + label)
    require(process['label'] == label and process['returncode'] == 0 and process['error'] is None,
            'actual process success:' + label)
    require(process['cleanup']['passed'] and process['cleanup']['reaped']
            and process['cleanup']['process_group_absent'] and process['handles_closed'],
            'actual process cleanup:' + label)
    require(0 <= process['cleanup']['elapsed_ms'] <= 2000, 'cleanup budget:' + label)
    require(0 <= process['end_monotonic'] - process['start_monotonic'] <= 30, 'child budget:' + label)
    require(process['observed_log_bytes'] <= 4194304 and process['retained_log_bytes'] <= 4194304,
            'log budget:' + label)


def main():
    lock_path = C200 / 'EXECUTABLE-INPUTS.json'
    approval_path = C200 / 'EXECUTABLE-INPUTS.approval.json'
    lock = read(lock_path); approval = read(approval_path)
    lock_hash = digest(lock_path)
    require(lock_hash == 'e22d12703926740c2c4cb8596781192b9f0412836e3fba7c6f353bedfc60e0e0', 'executed exact lock')
    require(digest(approval_path) == 'aa9c5234b666b5f4a79924502f3074dada274ff1135b78b11a8d83a560ceae2a', 'executed exact approval')
    invocation_path = BASE / 'c200-native-C200-INVOCATION.json'
    coordinator_path = BASE / 'c200-native-C200-RESULT.json'
    invocation = read(invocation_path); coordinator = read(coordinator_path)
    command = read(DRIVER / 'COMMAND.json'); completed = read(DRIVER / 'COMPLETED.json')
    require(command['argv'] == invocation['actual_argv'] == lock['coordinator_command'], 'sole coordinator command')
    require(command['environment'] == invocation['environment'] == lock['coordinator_environment'], 'sole coordinator environment')
    require(invocation['input_lock_sha256'] == completed['input_lock_sha256'] == lock_hash, 'coordinator lock binding')
    require(invocation['approval_sha256'] == completed['approval_sha256'] == digest(approval_path), 'coordinator approval binding')
    require(invocation['allowance'] == approval['authorization_scope'], 'coordinator finite allowance')
    require(completed['returncode'] == 0 and completed['process_reaped']
            and completed['stdout_closed'] and completed['stderr_closed']
            and completed['outer_timeout'] is False and completed['automatic_retry_permitted'] is False,
            'terminal observed driver')
    require(coordinator['c200_native_starts'] == coordinator['c200_receiving_starts']
            == coordinator['c200_read_only_checker_starts'] == 12, 'terminal counts')
    require(coordinator['cumulative_c199_c200_native_starts'] == 13
            and coordinator['preserved_c199_native_starts'] == 1, 'consumed C199 retained')

    qualification_path = SCHEDULE / 'qualification-result.json'
    qualification = read(qualification_path)
    require(qualification['status'] == 'MEASURED_GATES_PASSED_VISUAL_REVIEW_PENDING'
            and qualification['measured_gates_passed'] is True and qualification['qualified'] is False,
            'raw measured outcome preserved')
    require(qualification['implementation'] == lock['implementation'], 'actual implementation identity')
    require(len(qualification['transactions']) == len(qualification['external_readbacks']) == 12
            and len(qualification['delivered_controls']) == 9, 'complete result cohorts')
    rows = [json.loads(line) for line in (SCHEDULE / 'attempts.jsonl').read_text().splitlines() if line]
    names = [r['slot'] for r in lock['slots']]
    require(len(rows) == 60, 'attempt count')
    require([r['slot'] for r in rows] == [slot for slot in names for _ in range(5)], 'assigned attempt ordering')
    require(not list(SCHEDULE.glob('*.finalization-pending.json'))
            and not (SCHEDULE / 'finalization-stop.json').exists(), 'no unresolved finalization')
    require({p.name for p in (SCHEDULE / 'results').glob('*.json')} == {n + '.json' for n in names}, 'exact transaction result inventory')
    external_manifest = read(lock['external_readback']['path'])
    export_settings = read(ROOT / 'prototypes/static_tray_v01/export-settings.json')
    import_settings = read(ROOT / 'prototypes/static_tray_v01/import-settings.json')
    transactions = {}; actual = []; processes = []; candidates = {}
    for index, assigned in enumerate(lock['slots']):
        slot = assigned['slot']; result_path = Path(assigned['result']); result = read(result_path)
        transactions[slot] = result
        terminal = rows[index * 5 + 4]; events = rows[index * 5:index * 5 + 5]
        require([e['state'] for e in events] == ['RESERVED', 'STARTED', 'BUILT_PENDING_RECEIVING', 'RECEIVING', 'ACCEPTED'], 'five-state ledger:' + slot)
        require(all(e['input_lock_sha256'] == lock_hash for e in events), 'ledger lock binding:' + slot)
        require(events[:4] == result['attempt_events'], 'result event binding:' + slot)
        require(terminal['result_sha256'] == digest(result_path), 'terminal durable result binding:' + slot)
        require(result['state'] == 'ACCEPTED' and result['native_starts'] == result['receiving_starts'] == 1,
                'accepted exact starts:' + slot)
        require(result['input_lock_sha256'] == lock_hash and result['implementation'] == lock['implementation'], 'transaction identity:' + slot)
        for field in ('slot', 'case', 'route', 'purpose', 'candidate_revision', 'source_identity', 'expected_predecessor', 'command'):
            require(result[field] == assigned[field], 'assigned transaction field:' + slot + ':' + field)
        expected_limits = {k: v for k, v in lock['limits'].items() if not k.startswith('source_')}
        require(result['requested_limits'] == result['effective_limits'] == expected_limits, 'unchanged transaction limits:' + slot)
        timing = qualification['transactions'][index]
        require(timing['slot'] == slot and timing['state'] == 'ACCEPTED'
                and result['elapsed_before_finalization_ms'] <= terminal['elapsed_before_terminal_ms'] <= timing['elapsed_ms'] <= 65000,
                'actual finalization timing:' + slot)
        require(result['built_pending_receiving_pointer_unchanged'] is True, 'receiving precedes promotion:' + slot)
        candidate = Path(result['candidate']); receiver = Path(result['receiving_candidate'])
        candidates[slot] = candidate
        sealed(candidate, result['closure_sha256']); sealed(receiver, result['receiving_closure_sha256'])
        require(candidate == Path(assigned['store']) / 'objects' / slot
                and receiver == Path(assigned['store']) / 'objects' / (slot + '-receiving'), 'assigned candidate locations:' + slot)
        require(not Path(assigned['stage']).exists() and not Path(assigned['receiver_stage']).exists(), 'sealed stages moved once:' + slot)
        require(sum(p.stat().st_size for p in candidate.rglob('*') if p.is_file()) <= 67108864
                and sum(p.stat().st_size for p in receiver.rglob('*') if p.is_file()) <= 67108864, 'native output budgets:' + slot)
        canonical = candidate / 'canonical-input.json'
        require(digest(canonical) == assigned['canonical_sha256'], 'actual canonical identity:' + slot)
        for filename, row in assigned['source_files'].items(): matches(candidate / 'source' / filename, row)
        matches(candidate / 'source/source.json', {'sha256': assigned['source_manifest_sha256'], 'size_bytes': assigned['source_manifest_size_bytes']})
        native = read(candidate / 'native-result.json'); startup = read(candidate / 'native-startup.json')
        require(native['passed'] is True and native['record_sha256'] == assigned['canonical_sha256'], 'native canonical result:' + slot)
        require(native['blender_version'] == startup['blender_version'] == [4, 5, 3]
                and native['build_hash'] == startup['build_hash'] == '67807e1800cc', 'actual pinned native version:' + slot)
        requested_settings = {**export_settings, 'filepath': str(Path(assigned['stage']) / 'raw.glb')}
        require(native['operator_settings'] == startup['operator_settings'] == requested_settings, 'actual full exporter properties:' + slot)
        require(startup['phase'] == 'BEFORE_EXPORT' and startup['delivery_state'] == 'NOT_EXPORTED'
                and startup['settings_sha256'] == digest(ROOT / 'prototypes/static_tray_v01/export-settings.json'), 'actual preexport receipt:' + slot)
        require(startup['action_filter_initialization'] == {'action_count': 0, 'active_index': 0, 'filter_count': 0, 'scene_count': 1},
                'actual empty filter initialization:' + slot)
        policy = native['exporter_policy']
        require(policy['action_filter_properties_removed'] is True
                and policy['logging_observed'] == {'error_logger_level': 40, 'logger_level': 20}
                and policy['startup_receipt_sha256'] == digest(candidate / 'native-startup.json'), 'actual exporter postconditions:' + slot)
        require(policy['operator_property_count'] == 108 and policy['omitted_operator_properties'] == []
                and policy['operator_context'] == 'EXEC_DEFAULT' and policy['requested_log_level'] == -1
                and policy['resolved_log_level'] == 20 and policy['action_filter'] is False
                and policy['exporter_sha256'] == '82428a0415e11c27a285fd950f63e874add5ba2f8bacc6806ed762614560fa2e'
                and policy['debug'] == {'debug': False, 'debug_python': False, 'debug_value': 0}, 'actual repaired policy:' + slot)
        require({k: policy[k] for k in startup['exporter_policy']} == startup['exporter_policy'], 'startup-to-result policy continuity:' + slot)
        for filename, row in native['artifacts'].items():
            matches(candidate / filename, row)
            require(row == result['artifacts'][filename], 'transaction artifact identity:' + slot)
        require((candidate / 'raw.glb').read_bytes() == (candidate / 'final.glb').read_bytes(), 'raw-final exact equality:' + slot)
        require((candidate / 'final.glb').stat().st_size <= 8388608, 'GLB size ceiling:' + slot)
        audit = read(candidate / 'independent-audit.json')
        require(audit['passed'] is True and audit['findings'] == []
                and audit['artifact_sha256'] == digest(candidate / 'final.glb'), 'actual independent audit binding:' + slot)
        require(len(audit['nodes']) == 14 and len(native['objects']) == 14
                and sorted(native['objects']) == sorted(audit['nodes']), 'actual identity inventory:' + slot)
        provenance = read(candidate / 'source-provenance.json')
        require(provenance['candidate_identity'] == assigned['source_identity']
                and provenance['source_budget'] == {'max_elapsed_ms': 30000, 'max_operations': 100000}
                and provenance['source_elapsed_ms'] < 30000, 'unchanged source budget:' + slot)
        if assigned['route'] == 'ontokin':
            budget = provenance['construction_budget']
            source_operations = budget['operations']
            source_counter_kind = 'construction_budget.operations'
            require(budget['elapsed_ms'] < 30000, 'observed construction source work:' + slot)
        else:
            source_operations = provenance['source_operations']
            source_counter_kind = 'source_operations'
        require(source_operations <= 100000, 'observed source work:' + slot)
        observations = read(receiver / 'observations.json'); receiving_check = read(receiver / 'receiving-check.json')
        require(receiving_check == result['receiving_check'] and receiving_check['passed']
                and not receiving_check['findings'] and receiving_check['compared_imported_glb']
                and receiving_check['compared_native_scene'], 'actual two-input receiving:' + slot)
        require(observations['input_sha256'] == {n: digest(candidate / n) for n in ('final.glb', 'scene.blend')}, 'receiver immutable inputs:' + slot)
        require(observations['blender_version'] == [4, 5, 3] and observations['build_hash'] == '67807e1800cc', 'receiver pinned version:' + slot)
        require(observations['operator_settings'] == {**import_settings, 'filepath': str(candidate / 'final.glb')}, 'actual importer properties:' + slot)
        for section in ('native_scene', 'imported_glb'):
            require(observations[section]['object_count'] == 14 and observations[section]['physics_world'] is False
                    and observations[section]['measurement_frame'] == 'source-rh-y-up-metres', 'receiver measured scene:' + slot)
        for record in (native, startup, observations):
            flags = record['python_startup']['flags']
            require(flags['dont_write_bytecode'] == 1 and flags['no_user_site'] == 1
                    and flags['hash_randomization'] == 0 and flags['safe_path'] is True,
                    'actual pinned Python startup:' + slot)
        render = observations['render']; image = receiver / 'review.png'
        require(digest(image) == render['sha256'] and str(image) == result['render'], 'receiving image identity:' + slot)
        header = image.read_bytes()[:24]
        require(header[:8] == b'\x89PNG\r\n\x1a\n' and struct.unpack('>II', header[16:24]) == (1024, 768), 'actual PNG dimensions:' + slot)
        require(render['engine'] == 'BLENDER_WORKBENCH' and render['projection'] == 'ORTHO'
                and render['resolution'] == [1024, 768] and render['source_direction'] == [1.5, 1.2, 1.5], 'fixed visual contract:' + slot)
        effective = render['effective_settings']
        require(effective['camera']['type'] == 'ORTHO' and effective['render']['resolution_percentage'] == 100
                and effective['render']['film_transparent'] is False and effective['shading']['color_type'] == 'MATERIAL'
                and effective['shading']['type'] == 'SOLID' and effective['shading']['background_type'] == 'WORLD'
                and effective['shading']['show_xray'] is False and effective['shading']['show_object_outline'] is False,
                'actual opaque material view:' + slot)
        for process, key, label in zip(result['processes'], ('native_argv', 'receiver_argv'), ('construction', 'receiving')):
            process_check(process, assigned[key], assigned['environment'], label)
            retained_process = candidate / 'construction.process.json' if label == 'construction' else receiver / 'receiving.process.json'
            require(read(retained_process) == process, 'retained native process receipt:' + slot)
            processes.append(process)
        require(result['processes'][0]['end_monotonic'] <= events[2]['monotonic'] <= result['processes'][1]['start_monotonic']
                and result['processes'][1]['end_monotonic'] <= terminal['monotonic'], 'cleanup before acceptance ordering:' + slot)
        require(events[2]['monotonic'] - result['transaction_start_monotonic'] <= 30, 'construction total stage budget:' + slot)
        require(result['processes'][1]['start_monotonic'] - result['transaction_start_monotonic'] <= 35, 'full receiving allowance remained:' + slot)
        require(result['promotion']['promoted'] is True and result['promotion']['state']['revision'] == assigned['candidate_revision'], 'actual promotion revision:' + slot)
        readback_dir = SCHEDULE / 'external-readback' / slot
        readback = read(readback_dir / 'result.json'); probe = read(readback_dir / 'probe.json'); job = read(readback_dir / 'job.json')
        require(readback['passed'] is True and readback['state'] == 'ACCEPTED'
                and readback['checker_starts'] == 1 and readback['input_lock_sha256'] == lock_hash,
                'actual delivered readback:' + slot)
        require(not (readback_dir / 'finalization.pending').exists(), 'readback finalization complete:' + slot)
        require(readback['artifact_sha256'] == probe['artifact_sha256'] == job['artifact_sha256'] == digest(candidate / 'final.glb')
                and probe['audit_sha256'] == job['audit_sha256'] == digest(candidate / 'independent-audit.json'), 'readback actual bytes:' + slot)
        require(probe['input_lock_sha256'] == lock_hash and probe['input_preserved'] and probe['passed'], 'readback lock and preservation:' + slot)
        process_check(readback['process'], external_manifest['slots'][index]['argv'], external_manifest['environment'], 'external-readback')
        require(read(readback_dir / 'external-readback.process.json') == readback['process'], 'retained Node process receipt:' + slot)
        processes.append(readback['process'])
        require(readback['elapsed_ms'] <= 30000 and qualification['external_readbacks'][index]['elapsed_ms'] <= 30000, 'readback finite budget:' + slot)
        actual.append({'slot': slot, 'case': assigned['case'], 'route': assigned['route'],
            'result': binding(result_path), 'canonical_sha256': digest(canonical),
            'raw_and_final_glb_sha256': digest(candidate / 'final.glb'),
            'native_scene_sha256': digest(candidate / 'scene.blend'),
            'candidate_closure_sha256': result['closure_sha256'], 'receiving_closure_sha256': result['receiving_closure_sha256'],
            'native_startup_sha256': digest(candidate / 'native-startup.json'),
            'independent_audit_sha256': digest(candidate / 'independent-audit.json'),
            'receiving_check_sha256': digest(receiver / 'receiving-check.json'),
            'review_image_sha256': digest(image),
            'source_operations': source_operations, 'source_counter_kind': source_counter_kind,
            'source_elapsed_ms': provenance['source_elapsed_ms'],
            'transaction_elapsed_ms': timing['elapsed_ms'], 'read_only_check_elapsed_ms': qualification['external_readbacks'][index]['elapsed_ms'],
            'native_starts': 1, 'receiving_starts': 1, 'read_only_checker_starts': 1})
    require(len(processes) == len({p['pid'] for p in processes}) == 36, 'exact distinct process receipts')
    comparisons = []
    for assigned in lock['slots']:
        slot = assigned['slot']; reference_pairs = []
        ordinal = int(slot[1:])
        if ordinal % 2 == 0: reference_pairs.append(('paired-route', 'N%02d' % (ordinal - 1)))
        if assigned['purpose'] == 'clean-regeneration': reference_pairs.append(('clean-regeneration', 'N01' if assigned['route'] == 'ontokin' else 'N02'))
        require(len(transactions[slot]['equality_checks']) == len(reference_pairs), 'equality obligation count:' + slot)
        for purpose, reference in reference_pairs:
            for filename in ('canonical-input.json', 'raw.glb', 'final.glb'):
                require((candidates[slot] / filename).read_bytes() == (candidates[reference] / filename).read_bytes(), 'independent exact comparison:' + slot + ':' + filename)
            comparisons.append({'slot': slot, 'reference': reference, 'purpose': purpose, 'canonical_raw_final_exact': True})
        if assigned['case'] in {'Q04', 'Q05'}:
            reference = 'N01' if assigned['route'] == 'ontokin' else 'N02'
            baseline = candidates[reference]; candidate = candidates[slot]
            a = read(baseline / 'independent-audit.json'); b = read(candidate / 'independent-audit.json')
            require(a['right_closure'] == b['right_closure'] and a['right_closure_sha256'] == b['right_closure_sha256'], 'decoded right sibling unchanged:' + slot)
            require(read(baseline / 'canonical-input.json')['trays'][1] == read(candidate / 'canonical-input.json')['trays'][1], 'right canonical unchanged:' + slot)
            helper, entry, marker = ('tray.ok', 'main.ok', b' object right') if assigned['route'] == 'ontokin' else ('tray.py', 'main.py', b'right = ')
            require((baseline / 'source' / helper).read_bytes() == (candidate / 'source' / helper).read_bytes(), 'shared source definition unchanged:' + slot)
            old_source = (baseline / 'source' / entry).read_bytes(); new_source = (candidate / 'source' / entry).read_bytes()
            require(old_source.count(marker) == new_source.count(marker) == 1 and old_source.split(marker)[1] == new_source.split(marker)[1], 'right source suffix unchanged:' + slot)
        if assigned['case'] == 'Q05':
            selectors = ['N01', 'N09'] if assigned['route'] == 'ontokin' else ['N02', 'N10']
            require([x['slot'] for x in transactions[slot]['retained_selector_checks']] == selectors
                    and all(x['canonical_bytes_equal'] and x['retained_closure_unchanged'] and x['native_starts'] == 0
                            for x in transactions[slot]['retained_selector_checks']), 'retained selectors recompiled without export:' + slot)
    for store in {Path(r['store']) for r in lock['slots']}:
        last = [r for r in lock['slots'] if Path(r['store']) == store][-1]
        require(read(store / 'state.json') == transactions[last['slot']]['promotion']['state'], 'final accepted pointer:' + str(store))
        for assigned in [r for r in lock['slots'] if Path(r['store']) == store]:
            result = transactions[assigned['slot']]
            expected = assigned['expected_predecessor']
            require((None if result['previous_state'] is None else result['previous_state']['revision']) == expected,
                    'expected predecessor preservation:' + assigned['slot'])

    manifest = read(CAPTURE / 'MANIFEST.json')
    archive = CAPTURE / manifest['archive']['path']; matches(archive, manifest['archive'])
    require(manifest['absent_inputs'] == [] and manifest['source_tree_unchanged'] is True, 'complete terminal capture')
    entry_names = set(); regular_count = 0; payload_bytes = 0
    with tarfile.open(archive, 'r:gz') as packed:
        for member in packed:
            require(member.name in manifest['entries'] and member.name not in entry_names, 'unique captured member:' + member.name)
            entry_names.add(member.name); recorded = manifest['entries'][member.name]
            require(member.mode == int(recorded['mode'], 8), 'captured original mode:' + member.name)
            if member.isfile():
                stream = packed.extractfile(member); data = stream.read()
                require(recorded['type'] == 'file' and len(data) == recorded['size_bytes']
                        and hashlib.sha256(data).hexdigest() == recorded['sha256'], 'captured actual payload:' + member.name)
                matches(recorded['source_path'], recorded)
                regular_count += 1; payload_bytes += len(data)
            else:
                require(member.isdir() and recorded['type'] == 'directory', 'captured directory:' + member.name)
    require(entry_names == set(manifest['entries']), 'complete captured inventory')
    require(regular_count == 1704 and payload_bytes == 60009373, 'terminal payload totals')
    for row in manifest['direct_receipt_copies']:
        matches(CAPTURE / row['path'], row)
        require(row['sha256'] == manifest['entries'][row['archive_path']]['sha256'], 'direct receipt equals captured payload')

    numeric = read(NUMERIC)
    visual = read(VISUAL)
    # Numeric cross-check has its own independent script and detailed counts.
    require(numeric['passed'] is True and numeric['discrepancies'] == []
            and numeric['input_lock_sha256'] == lock_hash, 'independent numeric cross-check passed')
    require(visual['passed'] and visual['visual_review_complete'] and visual['viewed_images'] == visual['required_slots'] == 12
            and not visual['visible_defect_observed'] and visual['overall_technical_qualification_decided'] is False,
            'all actual images reviewed')
    require(visual['input_lock_sha256'] == lock_hash and visual['completed_driver_sha256'] == digest(DRIVER / 'COMPLETED.json')
            and visual['terminal_wrapper_sha256'] == digest(coordinator_path), 'visual terminal identity')
    require(visual['resolution_limited_slots'] == ['N05', 'N06'] and visual['occlusion_limited_slots'] == ['N07', 'N08']
            and visual['extra_renders_requested_or_generated'] == 0, 'visual limits and allowance preserved')
    require([image['slot'] for image in visual['images']] == names, 'all visual slots assigned')
    for image in visual['images']:
        result = transactions[image['slot']]; receiver = Path(result['receiving_candidate'])
        matches(image['path'], {'sha256': image['sha256'], 'size_bytes': image['bytes']})
        require(image['transaction_result_sha256'] == digest(Path(lock['schedule_root']) / 'results' / (image['slot'] + '.json'))
                and image['receiving_closure_sha256'] == result['receiving_closure_sha256']
                and image['observations_sha256'] == digest(receiver / 'observations.json')
                and image['viewed_individually'] and not image['visible_defect_observed'], 'actual individual visual evidence:' + image['slot'])

    started = time.monotonic()
    checked_lock, checked_hash = verify_lock(lock_path, approval=True)
    verify_revision(checked_lock, lock_path, approval=True, fresh=False)
    require(checked_hash == lock_hash, 'post-execution sealed input verification')
    verification_seconds = time.monotonic() - started
    OUT.mkdir(parents=True, exist_ok=True)
    for original, name in [(VISUAL, 'VISUAL-REVIEW.json'), (NUMERIC, 'NUMERIC-REVIEW.json'),
                           (BASE / 'audit-repository/review_c200_numeric_results.py', 'review_numeric_results.py'),
                           (Path(__file__), 'review_recorded_result.py')]:
        with (OUT / name).open('xb') as stream: stream.write(original.read_bytes())
    report = {
        'schema': 'ontokin.c200.independent-native-result-review/0.1',
        'reviewer': '/root/repository_audit', 'reviewed_at_utc': datetime.now(timezone.utc).isoformat(),
        'decision': 'FINITE_STATIC_TRAY_QUALIFICATION_PASSED', 'qualified': True,
        'profile': 'ontokin.static-tray/0.1.0', 'qualification_revision': 'OK-QUAL-STATIC-TRAY-C200/0.1.0',
        'implementation': lock['implementation'], 'input_lock': binding(lock_path),
        'independent_pre_execution_approval': binding(approval_path),
        'reviewer_script': binding(OUT / 'review_recorded_result.py'),
        'integration_disposition': 'APPROVE_INTEGRATION_OF_EXACT_EXECUTED_EXPERIMENTAL_SOURCE_AND_EVIDENCE',
        'counts': {'c200_native_construction_starts': 12, 'c200_receiving_starts': 12,
            'c200_actual_delivered_node_checks': 12, 'accepted_transactions': 12,
            'delivered_control_variants': 9, 'actual_images_reviewed': 12,
            'preserved_c199_failed_native_starts': 1, 'cumulative_c199_c200_native_construction_starts': 13,
            'automatic_retries': 0, 'new_native_starts_by_reviewers': 0,
            'new_receiving_starts_by_reviewers': 0, 'new_node_starts_by_reviewers': 0,
            'new_lifecycle_starts_by_reviewers': 0},
        'checks_passed': sum(CHECKS.values()), 'check_categories': dict(CHECKS),
        'execution': {'invocation': binding(invocation_path), 'terminal_coordinator': binding(coordinator_path),
            'terminal_driver': binding(DRIVER / 'COMPLETED.json'), 'ledger': binding(SCHEDULE / 'attempts.jsonl'),
            'raw_qualification_result': binding(qualification_path),
            'raw_qualified_false_preserved': True,
            'raw_pending_status_meaning': 'The raw coordinator correctly stopped at measured gates. This later separate review completes visual and independent acceptance without rewriting that earlier receipt.',
            'transaction_elapsed_ms_min': min(x['transaction_elapsed_ms'] for x in actual),
            'transaction_elapsed_ms_max': max(x['transaction_elapsed_ms'] for x in actual),
            'coordinator_elapsed_seconds': completed['elapsed_seconds'],
            'distinct_child_process_receipts': 36, 'terminal_ledger_records': 12, 'total_ledger_records': 60},
        'actual_slots': actual, 'independently_compared_exact_equalities': comparisons,
        'retained_source_and_right_sibling_preservation': {'Q04': True, 'Q05': True,
            'Q05_old_selectors_recompiled_without_new_exports': True,
            'all_prior_accepted_closures_still_exact': True},
        'numeric_independent_review': binding(OUT / 'NUMERIC-REVIEW.json'),
        'numeric_independent_script': binding(OUT / 'review_numeric_results.py'),
        'numeric_comparison_rows_recomputed': 95904,
        'numeric_review_counts': numeric['counts'],
        'visual_review': binding(OUT / 'VISUAL-REVIEW.json'),
        'visual_gate_assessment': {
            'contract': binding(ROOT / 'docs/engineering/static-tray-mapping-c198/VALIDATION-PLAN.md'),
            'contract_section': '6. Receiving implementation and visual review',
            'required_fixed_views_and_actual_review_complete': True,
            'independent_result_reviewer_additional_actual_images_viewed': ['N05', 'N07'],
            'N05_independent_observation': 'The full-scene image shows the larger blue tray and tan proxy at small scale; the minimum-size tray is not individually resolvable. This image does not prove that smaller tray surface visually.',
            'N07_independent_observation': 'Both rotated tray exteriors are visible; the left opening/proxy is visible while the right interior/proxy is occluded by its exterior. No visible contradiction was observed.',
            'resolution_limited_slots': ['N05', 'N06'], 'occlusion_limited_slots': ['N07', 'N08'],
            'reasoning': 'The frozen gate prescribes one full-scene image and actual inspection with recorded findings; it sets no minimum projected object size and expressly avoids a complete hidden-surface claim. All twelve prescribed actual images were inspected, no visible contradiction was found, and all required native/imported geometry comparisons independently passed. The limits are retained rather than changing views or asserting unobserved surfaces.',
            'visual_reviewer_role_disclosure': visual['reviewer_role_disclosure']},
        'captured_evidence': {'manifest': binding(CAPTURE / 'MANIFEST.json'), 'archive': binding(archive),
            'all_archive_payloads_independently_rehashed': True, 'archive_members': len(entry_names),
            'regular_files': regular_count, 'regular_payload_bytes': payload_bytes,
            'direct_receipts_verified': len(manifest['direct_receipt_copies'])},
        'post_execution_complete_input_verification_passed': True,
        'post_execution_complete_input_verification_seconds': verification_seconds,
        'limitations': [
            'Qualification is restricted to the explicitly selected finite two-tray static geometry mapping, its frozen source families, pinned distribution, settings and finite cases.',
            'Q02 minimum geometry is subpixel in the prescribed full-scene view. Q03 right interior/proxy is occluded. Their measured geometry is verified; their unresolvable or hidden surfaces are not claimed visually verified.',
            'The retained .blend scenes are hash-bound and were independently reopened; native .blend byte equality is not the required regeneration rule. Canonical/raw/final GLB equality passed exactly.',
            'Controlled lifecycle proof does not establish deliberate actual-Blender cancellation behavior. No extra lifecycle experiment was run.',
            'C199 remains a failed, consumed one-start cohort. C200 is a separately approved completed cohort; neither schedule is resumable and no retry follows from this disposition.',
            'Separate tray admission remains pending and retains its four-export ceiling. Timed authors, comparative advantage, contact/live physics, external roles, full-product acceptance and inherited failed legacy regression remain unresolved.'
        ]}
    with (OUT / 'RESULT-REVIEW.json').open('x') as stream:
        json.dump(report, stream, indent=2, sort_keys=True); stream.write('\n')
    print(json.dumps({'decision': report['decision'], 'qualified': True,
        'review': binding(OUT / 'RESULT-REVIEW.json'), 'checks_passed': report['checks_passed'],
        'counts': report['counts']}, indent=2))


if __name__ == '__main__':
    main()
