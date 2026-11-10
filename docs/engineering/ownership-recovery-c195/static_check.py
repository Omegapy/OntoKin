#!/usr/bin/env python3
"""Qualify only the frozen C195 ownership negatives, without native execution."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO))
from prototypes.guided_contact_v02.api import validate_source
from prototypes.guided_contact_v02.common import Budget, load_contract, schema_check


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def literal(path):
    tree = ast.parse(Path(path).read_bytes())
    assert len(tree.body) == 2 and isinstance(tree.body[0], ast.Expr)
    assert isinstance(ast.literal_eval(tree.body[0].value), str)
    assign = tree.body[1]
    assert isinstance(assign, ast.Assign) and len(assign.targets) == 1
    assert isinstance(assign.targets[0], ast.Name) and assign.targets[0].id == 'DESIGN'
    return ast.literal_eval(assign.value)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    assert not a.out.exists(), 'Do not overwrite a retained preflight'
    contract = load_contract()
    result = {'schema': 'ontokin.c195.static-qualification/0.1',
              'native_builds': 0, 'native_resimulations': 0, 'author_trials': 0,
              'passed': False, 'sources': {}, 'diagnostics': {}}
    for route, ext in [('ok', 'ok'), ('python', 'py')]:
        baseline = HERE / ('fixtures/baseline.' + ext)
        negative = HERE / ('fixtures/candidate.' + ext)
        original = REPO / ('docs/engineering/contact-comparison-c194/authors/' + route + '/reuse.' + ext)
        before = baseline.read_bytes()
        assert before == original.read_bytes(), 'Baseline differs from accepted C194 source'
        stop = b'at = [375, 130, -220][mm];' if route == 'ok' else b"'at_mm': [375, 130, -220]"
        owner = b'owner = "body.left";' if route == 'ok' else b"'owner': 'body.left'"
        assert before.count(stop) == before.count(owner) == 1
        expected = before.replace(stop, stop.replace(b'375', b'365')).replace(owner, owner.replace(b'body.left', b'body.right'))
        assert negative.read_bytes() == expected, 'Negative contains unrelated changes'
        result['sources'][route] = {'baseline_sha256': sha(baseline), 'candidate_sha256': sha(negative), 'exact_two_deltas': True}
    baseline_ok = validate_source(HERE / 'fixtures/baseline.ok', host_max_operations=1000000, host_max_elapsed_ms=80000)
    assert baseline_ok['successful']
    baseline_py = literal(HERE / 'fixtures/baseline.py')
    schema_check(baseline_py, contract['source_schema'])
    assert baseline_py == json.loads((REPO / 'docs/engineering/contact-preparation-c194/frozen/H-canonical.json').read_text())
    ok = validate_source(HERE / 'fixtures/candidate.ok', host_max_operations=1000000, host_max_elapsed_ms=80000)
    assert not ok['successful'] and not ok['committed']
    assert len(ok['diagnostics']) == 1 and ok['diagnostics'][0]['code'] == 'C193_E_OWNERSHIP'
    assert ok['diagnostics'][0]['message'] == 'Collider is assigned to the wrong mass owner'
    assert ok['diagnostics'][0]['span'] is not None
    assert ok['runtime']['executable_sha256'] is None
    assert ok['cost']['operation_components'].get('scheduled_native_substeps', 0) == 0
    result['diagnostics']['ok'] = ok
    negative_py = literal(HERE / 'fixtures/candidate.py')
    expected_py = json.loads((REPO / 'docs/engineering/contact-preparation-c194/frozen/G-canonical.json').read_text())
    expected_py['colliders']['contact.left_shoe']['owner'] = 'body.right'
    assert negative_py == expected_py
    budget = Budget(1000000, 80000)
    try:
        schema_check(negative_py, contract['source_schema'], budget=budget)
    except ValueError as exc:
        diagnostic = type(exc).__name__ + ': ' + str(exc)
    else:
        raise AssertionError('Malformed Python design was admitted; stop before native work')
    assert diagnostic == 'ValueError: $.colliders.contact.left_shoe.owner: differs from frozen constant'
    result['diagnostics']['python'] = {'error': diagnostic, 'cost': budget.cost(), 'native_launched': False}
    result['passed'] = True
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'passed': True, 'native_builds': 0, 'diagnostics': {'ok': ok['diagnostics'][0], 'python': diagnostic}}, indent=2))


if __name__ == '__main__':
    main()
