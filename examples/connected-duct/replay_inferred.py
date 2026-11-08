"""Replay and audit the C168 inferred offset cases in a fresh evidence directory."""
import argparse
from math import dist
from pathlib import Path
from shutil import copyfile
import sys
import tempfile

from agent_offset import replay
from agent_repair import ROOT, write_json
from ontokin.bundle import load_file_manifest
from ontokin.budget_runtime import execute_framed_loft_export
from ontokin.execution_budget import HostPolicy
from ontokin.scene import ExportOptions

sys.path.insert(0, str(ROOT / 'tools'))
from audit_duct_route_exchanges import audit_case, check, digest, load

EXAMPLE = Path(__file__).resolve().parent


def check_decisions(decisions, spec, tolerance):
    candidates = decisions['candidates']
    selected = decisions['selected_direction']
    if spec.get('candidate_count') == 0:
        check(not candidates and selected is None and 'parallel' in decisions['reason'].lower(), 'Parallel axes')
        return
    check(len(candidates) == 2 and dist(candidates[0]['direction'], [-x for x in candidates[1]['direction']]) <= tolerance,
          'Expected two opposite directions')
    feasible = [c for c in candidates if c['feasible']]
    failed = [c for c in candidates if not c['feasible']]
    check(all(c['reason'] for c in failed), 'Missing reason for a rejected candidate')
    if spec['expected'] == 'refused':
        check(not feasible and selected is None and decisions['reason'] and
              dist(sorted(c['lengths_m'][1] for c in failed), sorted(spec['candidate_middle_spans_m'])) <= tolerance,
              'Expected both middle spans outside limits')
    else:
        check(len(feasible) == len(failed) == 1 and selected == feasible[0]['direction'] and
              dist(selected, spec['flow_axes'][2]) <= tolerance and
              dist(feasible[0]['lengths_m'], spec['straight_spans_m']) <= tolerance and
              abs(failed[0]['lengths_m'][1] - spec['opposing_middle_span_m']) <= tolerance,
              'Candidate selection or spans differ from contract')


def direct_export(manifest, directory, summary):
    editable = directory / 'editable'
    editable.mkdir()
    files = load(manifest)
    copyfile(manifest, editable / manifest.name)
    copyfile(directory / 'repaired.ok', editable / files['entry']['path'])
    for module in files['modules']:
        copyfile(manifest.parent / module['path'], editable / module['path'])
    bundle = load_file_manifest(editable / manifest.name)
    check(bundle.program_revision == summary['repaired']['program_revision'], 'Standalone source revision')
    result = execute_framed_loft_export(bundle, policy=HostPolicy(300000, 30000),
                                        options=ExportOptions(end='1', fps=2, helpers=False))
    check(result.data == (directory / 'repaired.glb').read_bytes(), 'Standalone source export differs from Agent export')
    return dict(program_revision=bundle.program_revision, glb_sha256=digest(result.data), bytes=len(result.data))


def run(output):
    contract = load(EXAMPLE / 'inferred-offset-contract.json')
    cases = contract['cases']
    agent = output / 'agent'
    agent.mkdir(parents=True, exist_ok=False)
    reports = []
    for label in [*cases, 'interior-gap', 'rollback']:
        control = None if label in cases else label
        spec = cases[label] if control is None else cases['positive']
        manifest = EXAMPLE / spec['manifest']
        directory = agent / label
        with tempfile.TemporaryDirectory(prefix='inferred-offset-') as store:
            summary = replay(manifest, directory, store, spec['chain'], control=control)
        outcome = {'rollback': 'edit-rejected', 'interior-gap': 'control-exported'}.get(control)
        if outcome is None:
            outcome = 'fitted' if spec['expected'] == 'unique_fit' else 'fit-rejected'
        fixture = EXAMPLE / load(manifest)['entry']['path']
        report = audit_case(directory, fixture, spec['chain'], outcome, agent / 'positive')
        check_decisions(load(directory / 'directions.json'), spec, contract['maximum_unit_normal_error'])
        if outcome in ('fitted', 'control-exported'):
            report['direct_export'] = direct_export(manifest, directory, summary)
        reports.append(report)
    write_json(output / 'inferred-exchanges.json', dict(result='passed', cases=reports))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    run(parser.parse_args().output)
