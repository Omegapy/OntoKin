"""Check C266 dependency admission after one successful in-process call."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import shutil
import sys
import tempfile


PINS = {
    'localized-repair-c266/hinge_binding.py': ('68849dbe3339c158eac7ec43fb1defcbd2993c37c6a0a5ee813d2da71fb03dda', 17639),
    'localized-repair-c265/source_hinges.py': ('04bea0f7c5f82a3e3e74610d3ee98755f44ed0905566c00eb063647e31abbf9e', 37570),
    'localized-repair-c261/hinge_glb.py': ('6167b3a56a2b1a600812340d85ee02eaa3b6399801d585a758333aabcfaa5e08', 14036),
    'localized-repair-c257/ownership.py': ('c28b6a52e0d3575204e138986e5b1dfa57081943b8e194be0613fc33a28210f1', 35942),
}
SOURCE_PINS = {
    'before.main.ok': '73c95c6509363e492084d7b6959356fe1955f4e78086a72b507167a271a33123',
    'hinges.ok': '1516e53179a7b9deecf593ab48afdcd72fba8124ea77868327c25a28a654681a',
    'before.glb': 'd009d9dba6c69bb8e8e6decdfa9d7e1e92f819e3b59013d481cd30101c973534',
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    engineering = args.repo / 'docs/engineering'
    code = {name: (engineering / name).read_bytes() for name in PINS}
    for name, data in code.items():
        assert (digest(data), len(data)) == PINS[name], name
        path = args.output / 'original-code' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    proof = engineering / 'semantic-export-c210/evidence/proof'
    payloads = {name: (proof / name).read_bytes() for name in SOURCE_PINS}
    for name, raw in payloads.items():
        assert digest(raw) == SOURCE_PINS[name]
        dest = args.output / 'inputs' / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(raw)
    files = {'main.ok': payloads['before.main.ok'], 'hinges.ok': payloads['hinges.ok']}
    artifact = payloads['before.glb']
    scenarios = [
        ('same_size_c265_after_success', 'localized-repair-c265/source_hinges.py', 'same-size'),
        ('same_size_c261_after_success', 'localized-repair-c261/hinge_glb.py', 'same-size'),
        ('same_size_c257_after_success', 'localized-repair-c257/ownership.py', 'same-size'),
        ('missing_c261_after_success', 'localized-repair-c261/hinge_glb.py', 'missing'),
        ('symlink_c257_after_success', 'localized-repair-c257/ownership.py', 'symlink'),
    ]
    results = []
    for index, (name, target_name, mode) in enumerate(scenarios):
        record = {'name': name, 'dependency': target_name, 'mutation': mode,
                  'originalSha256': PINS[target_name][0], 'originalBytes': PINS[target_name][1]}
        evidence = args.output / 'cases' / name
        evidence.mkdir(parents=True)
        with tempfile.TemporaryDirectory(prefix='c266-pins-', dir=args.output) as temporary:
            base = Path(temporary)
            for relative, data in code.items():
                path = base / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            candidate = base / 'localized-repair-c266/hinge_binding.py'
            spec = importlib.util.spec_from_file_location('c266_dependency_review_' + str(index), candidate)
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            before = module.bind_hinge_inputs(files, artifact)
            assert before['inputBindingVerified'] is True and before['objectCount'] == 18
            record['firstCall'] = {'outcome': 'accepted', 'objectCount': before['objectCount'],
                                   'inputBindingVerified': before['inputBindingVerified']}
            target = base / target_name
            if mode == 'same-size':
                original = target.read_bytes()
                assert original[-1:] == b'\n'
                modified = original[:-1] + b' '
                assert len(modified) == len(original) and digest(modified) != digest(original)
                target.write_bytes(modified)
                (evidence / 'mutated-dependency.py').write_bytes(modified)
                record.update({'mutatedSha256': digest(modified), 'mutatedBytes': len(modified)})
            elif mode == 'missing':
                target.unlink()
                assert not target.exists()
                record['targetAbsentBeforeSecondCall'] = True
            else:
                twin = target.with_name(target.stem + '.same_bytes.py')
                shutil.copyfile(target, twin)
                target.unlink()
                target.symlink_to(twin.name)
                assert target.is_symlink() and digest(target.read_bytes()) == PINS[target_name][0]
                record.update({'symlinkTarget': twin.name, 'symlinkTargetSha256': digest(twin.read_bytes()),
                               'targetSymlinkBeforeSecondCall': True})
            try:
                module.bind_hinge_inputs(files, artifact)
                record.update({'secondCall': {'outcome': 'accepted'}, 'passed': False})
            except Exception as exc:
                second = {'outcome': 'refused', 'exception': type(exc).__name__, 'code': getattr(exc, 'code', None),
                          'detail': str(exc), 'sourceHashes': getattr(exc, 'sourceHashes', None),
                          'artifactSha256': getattr(exc, 'artifactSha256', None)}
                record['secondCall'] = second
                record['passed'] = (isinstance(exc, module.Fault) and second['code'] == 'INPUT_BINDING'
                                    and second['sourceHashes'] == {k:digest(v) for k,v in files.items()}
                                    and second['artifactSha256'] == digest(artifact))
            (evidence / 'RESULT.json').write_text(json.dumps(record, indent=2) + '\n')
            results.append(record)
    for relative, data in code.items():
        assert (engineering / relative).read_bytes() == data, 'real checkout changed during experiment'
    summary = {'schema': 'ontokin.c266.independent-dependency-review/0.1', 'purpose': 'Recheck every exact dependency after an already successful in-process call',
               'implementationSha256': PINS['localized-repair-c266/hinge_binding.py'][0],
               'scriptSha256': digest(Path(__file__).read_bytes()), 'python': platform.python_version(), 'platform': platform.platform(),
               'inputPins': SOURCE_PINS, 'dependencyPins': {k:{'sha256':v[0], 'bytes':v[1]} for k,v in PINS.items()},
               'checks': len(results), 'passed': all(r['passed'] for r in results), 'results': results,
               'realCheckoutUnchanged': True, 'existingReviewArchiveModified': False}
    (args.output / 'RESULTS.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({key:summary[key] for key in ('checks','passed','implementationSha256','scriptSha256','python','realCheckoutUnchanged')}, indent=2))
    return 0 if summary['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
