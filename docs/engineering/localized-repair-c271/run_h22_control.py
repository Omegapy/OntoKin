"""Execute the independently frozen C271 H22.02 inputs without repairing them."""

from __future__ import annotations

import argparse
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import subprocess
import sys
import traceback
import zipfile


ROOT = Path(__file__).resolve().parents[3]
ORACLE = Path(__file__).parent / 'control' / 'EXPECTED.json'
ORACLE_SHA256 = '0b8da6eab52323e8092c348fabad0d8d77247552e4eb5e3a1ffdc17266d12522'
INTERFACES = {
    'source_observation': ('localized-repair-c265/source_hinges.py', 'observe_source_hinges'),
    'source_program_binding': ('localized-repair-c266/hinge_binding.py', 'bind_hinge_inputs'),
    'hinge_comparison': ('localized-repair-c267/hinge_compare.py', 'compare_hinges'),
}
NONCLAIMS = ('historicalInputsBound', 'sitePosesEvaluated', 'sourceValidityQualified',
             'acceptedRevisionQualified', 'completeC255Semantic', 'executionAllowed')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + '\n').encode()


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


class CheckFailure(Exception):
    pass


class Run:
    def __init__(self, output, phase):
        self.output, self.phase = output, phase
        self.checks, self.calls, self.members, self.opened = [], [], {}, set()
        self.source = {'commit': git('rev-parse', 'HEAD'), 'tree': git('rev-parse', 'HEAD^{tree}'),
                       'dirty_before': git('status', '--porcelain=v1', '--untracked-files=normal')}

    def check(self, name, condition):
        self.checks.append({'name': name, 'passed': bool(condition)})
        if not condition:
            raise CheckFailure(name)

    def read_bound(self, item):
        path = ROOT / item['path']
        self.check('safe input path: ' + item['path'], path.resolve().is_relative_to(ROOT))
        raw = path.read_bytes()
        self.check('exact input bytes: ' + item['path'], len(raw) == item['bytes'])
        self.check('exact input hash: ' + item['path'], digest(raw) == item['sha256'])
        return raw

    def audit(self, event, args):
        if event == 'open' and isinstance(args[0], (str, bytes)):
            path = Path(args[0].decode() if isinstance(args[0], bytes) else args[0])
            if not path.is_absolute():
                path = Path.cwd() / path
            try:
                relative = path.resolve().relative_to(ROOT)
            except (ValueError, OSError):
                return
            if '.git' not in relative.parts and '__pycache__' not in relative.parts:
                self.opened.add(relative.as_posix())

    def baseline(self, interface, value, expected, case):
        label = case['id'] + '/' + interface
        self.check(label + '/object count', value.get('objectCount') == expected['object_count'])
        self.check(label + '/program revision', value.get('programRevision') == case['candidate_program']['revision'])
        self.check(label + '/program manifest', value.get('sourceManifest') == case['candidate_program']['manifest'])
        for key in NONCLAIMS:
            self.check(label + '/no broader claim/' + key, value.get(key) is False)
        if interface == 'source_program_binding':
            self.check(label + '/input binding verified', value.get('inputBindingVerified') is True)
            self.check(label + '/no hinge comparison claim', value.get('hingeComparisonVerified') is False)
            return
        self.check(label + '/hinge count', value.get('hingeCount') == expected['hinge_count'])
        self.check(label + '/site count', value.get('siteCount') == expected['distinct_endpoint_site_count'])
        rows = [row['source'] if interface == 'hinge_comparison' else row for row in value['records']]
        by_id = {tuple(row['id']): row for row in rows}
        wanted = {tuple(row['joint_occurrence_id']) for row in expected['rows']}
        self.check(label + '/complete joint set', set(by_id) == wanted and len(rows) == len(wanted))
        self.check(label + '/unique joint definition', len({tuple(row['definitionId']) for row in rows}) == expected['unique_joint_definition_count'])
        sites = set()
        for declared in expected['rows']:
            row = by_id[tuple(declared['joint_occurrence_id'])]
            row_label = label + '/' + '/'.join(declared['joint_occurrence_id'])
            for key, target in [('ownerId', declared['owning_object_id']),
                                ('parentSiteId', declared['parent_site_occurrence_id']),
                                ('childSiteId', declared['child_site_occurrence_id']),
                                ('definitionId', expected['joint_definition_id']),
                                ('name', expected['joint_name']), ('key', expected['joint_key']),
                                ('kind', expected['kind']), ('axis', expected['axis'])]:
                self.check(row_label + '/' + key, row.get(key) == target)
            self.check(row_label + '/exact limits', [float(x).hex() for x in row['limits']] == expected['limits_binary64_hex'])
            self.check(row_label + '/exact initial', float(row['initial']).hex() == expected['initial_binary64_hex'])
            for role in ('parent', 'child'):
                site = row[role + 'Site']
                sites.add(tuple(site['id']))
                for key, target in [('id', declared[role + '_site_occurrence_id']),
                                    ('definitionId', expected[role + '_site_definition_id']),
                                    ('interface', expected['site_interface']),
                                    ('poseEvaluated', False), ('compatibilityAuthority', 'source-only')]:
                    self.check(row_label + '/' + role + '/' + key, site.get(key) == target)
                self.check(row_label + '/' + role + '/exact size', float(site['sizeM']).hex() == expected['site_size_metres_binary64_hex'])
        self.check(label + '/distinct endpoint sites', len(sites) == expected['distinct_endpoint_site_count'])
        if interface == 'hinge_comparison':
            for key in ('inputBindingVerified', 'hingeComparisonVerified', 'hingeSetAgreementVerified', 'endpointAgreementVerified'):
                self.check(label + '/' + key, value.get(key) is True)

    def execute(self):
        self.check('identified clean source checkout', not self.source['dirty_before'])
        self.check('frozen oracle identity', digest(ORACLE.read_bytes()) == ORACLE_SHA256)
        oracle = json.loads(ORACLE.read_text())
        self.check('oracle schema', oracle['schema'] == 'ontokin.c271.missing-import-digest-oracle/0.1')
        self.check('six independently declared input cases', len(oracle['cases']) == 6)
        sys.addaudithook(self.audit)
        for item in oracle['basis_files']:
            self.read_bound(item)
        loaded = {}
        for name, (relative, function) in INTERFACES.items():
            path = ROOT / 'docs/engineering' / relative
            spec = importlib.util.spec_from_file_location('_c271_' + name, path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            loaded[name] = module, function
        for case in oracle['cases']:
            files = {name: self.read_bound(item) for name, item in case['source_files'].items()}
            raw = self.read_bound(case['artifact'])
            source_hashes = {name: digest(value) for name, value in files.items()}
            source_sizes = {name: len(value) for name, value in files.items()}
            mutation = case['mutation']
            if mutation:
                original = self.read_bound(mutation['original'])
                low, high = mutation['start_byte'], mutation['end_byte']
                self.check(case['id'] + '/single exact deletion', original[:low] + original[high:] == files['main.ok'])
                self.check(case['id'] + '/removed exact text', original[low:high] == mutation['removed_utf8'].encode())
                self.check(case['id'] + '/removed exact hash', digest(original[low:high]) == mutation['removed_sha256'])
                self.check(case['id'] + '/no replacement', mutation['replacement_utf8'] == '')
            self.members['requests/' + case['id'] + '.json'] = json_bytes(case)
            first_refusal = None
            for interface, (module, function) in loaded.items():
                expected = case['expected'][interface]
                response = {'interface': interface, 'case': case['id']}
                try:
                    value = getattr(module, function)(files) if interface == 'source_observation' else getattr(module, function)(files, raw)
                except module.Fault as exc:
                    response.update(outcome='typed_refusal', exception_type=type(exc).__name__, message=str(exc), fault=dict(vars(exc)))
                except Exception as exc:
                    response.update(outcome='host_exception', exception_type=type(exc).__name__, message=str(exc), traceback=traceback.format_exc())
                else:
                    response.update(outcome='success', value=value)
                member = 'responses/' + case['id'] + '--' + interface + '.json'
                captured = json_bytes(response)
                self.members[member] = captured
                call = {'case': case['id'], 'interface': interface, 'expected': expected,
                        'outcome': response['outcome'], 'refusal_code': response.get('fault', {}).get('code'),
                        'response_member': member, 'response_bytes': len(captured), 'response_sha256': digest(captured)}
                self.calls.append(call)
                label = case['id'] + '/' + interface
                self.check(label + '/outcome', response['outcome'] == expected['outcome'])
                evidence = response['fault'] if response['outcome'] == 'typed_refusal' else response['value']
                self.check(label + '/retained source hashes', evidence.get('sourceHashes') == source_hashes)
                self.check(label + '/retained source byte counts', evidence.get('sourceBytes') == source_sizes)
                if interface != 'source_observation':
                    self.check(label + '/retained artifact hash', evidence.get('artifactSha256') == digest(raw))
                    self.check(label + '/retained artifact byte count', evidence.get('artifactBytes') == len(raw))
                if response['outcome'] == 'typed_refusal':
                    self.check(label + '/exact predeclared refusal', evidence.get('code') == expected['refusal_code'])
                    self.check(label + '/retained reason', isinstance(evidence.get('detail'), str) and bool(evidence['detail']))
                    self.check(label + '/no success return', 'value' not in response)
                    self.check(label + '/no qualified partial set', not any(key in evidence for key in ('records', 'hinges', 'sites', 'objects')))
                    self.check(label + '/no qualification flag', not any(evidence.get(key) is True for key in (*NONCLAIMS, 'inputBindingVerified', 'hingeComparisonVerified', 'hingeSetAgreementVerified', 'endpointAgreementVerified')))
                    if first_refusal is None:
                        first_refusal = evidence['code'], evidence['detail']
                    else:
                        self.check(label + '/propagated source refusal', (evidence['code'], evidence['detail']) == first_refusal)
                else:
                    self.baseline(interface, response['value'], oracle['baseline_semantics'], case)
        self.check('all 18 declared calls executed', len(self.calls) == 18)
        self.check('checkout unchanged after execution', git('status', '--porcelain=v1', '--untracked-files=normal') == '')

    def finish(self, error):
        self.opened.update((ORACLE.relative_to(ROOT).as_posix(), Path(__file__).relative_to(ROOT).as_posix()))
        identities = []
        for relative in sorted(self.opened):
            path = ROOT / relative
            if path.is_file():
                raw = path.read_bytes()
                identities.append({'path': relative, 'bytes': len(raw), 'sha256': digest(raw),
                                   'git_blob': git('rev-parse', self.source['commit'] + ':' + relative)})
        self.members['INPUT-IDENTITIES.json'] = json_bytes({'source': self.source, 'files': identities})
        self.members['CHECKS.json'] = json_bytes(self.checks)
        manifest = {name: {'bytes': len(raw), 'sha256': digest(raw)} for name, raw in self.members.items()}
        self.members['MANIFEST-SHA256.json'] = json_bytes(manifest)
        archive = self.output / 'RAW-EVIDENCE.zip'
        with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as target:
            for name, raw in sorted(self.members.items()):
                target.writestr(name, raw)
        with zipfile.ZipFile(archive) as check_zip:
            assert check_zip.testzip() is None
            for name, expected in manifest.items():
                raw = check_zip.read(name)
                assert len(raw) == expected['bytes'] and digest(raw) == expected['sha256']
        report = {'schema': 'ontokin.c271.h22-control-results/1', 'phase': self.phase,
                  'source': self.source, 'oracle_sha256': ORACLE_SHA256,
                  'environment': {'python': sys.version, 'executable': sys.executable, 'platform': platform.platform()},
                  'command': [sys.executable, *sys.argv], 'finished_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  'passed': error is None, 'error': error, 'input_cases_planned': 6, 'interface_calls_planned': 18,
                  'interface_calls_executed': len(self.calls), 'checks_passed': sum(x['passed'] for x in self.checks),
                  'checks_failed': sum(not x['passed'] for x in self.checks), 'assertion_details_member': 'CHECKS.json',
                  'failed_checks': [x for x in self.checks if not x['passed']], 'calls': self.calls,
                  'input_identities': identities, 'raw_evidence': {'path': archive.name, 'bytes': archive.stat().st_size,
                  'sha256': digest(archive.read_bytes()), 'members': len(self.members)},
                  'limits': ['Six finite input cases; no implementation, grammar or contract change',
                             'No source evaluator, export, native/model trial or complete H22/C260 qualification',
                             'Routine driver, full affected integration cohort, integration and actual-main checks remain separate unrun gates']}
        (self.output / 'RESULTS.json').write_bytes(json_bytes(report))
        print(json.dumps({key: report[key] for key in ('passed', 'error', 'interface_calls_executed', 'checks_passed', 'checks_failed')}))
        return 0 if error is None else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--phase', required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        parser.error('Use a new output directory; earlier evidence must not be overwritten')
    if output.is_relative_to(ROOT):
        parser.error('Use an evidence directory outside the source checkout')
    output.mkdir(parents=True)
    run = Run(output, args.phase)
    error = None
    try:
        run.execute()
    except Exception as exc:
        error = {'type': type(exc).__name__, 'detail': str(exc), 'traceback': traceback.format_exc()}
    return run.finish(error)


if __name__ == '__main__':
    raise SystemExit(main())
