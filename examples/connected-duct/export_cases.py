"""Export six editable source cases for the C161 joint and check the delivered GLBs."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from ontokin.budget_runtime import execute_framed_loft_export
from ontokin.bundle import ProgramBundle, SourceUnit, load_file_manifest
from ontokin.scene import ExportOptions
from tools.verify_connected_duct import JointFailure, measure


def source_cases(nominal):
    yield 'nominal', nominal.entry.raw
    yield 'wide', (HERE / 'assembly-wide.ok').read_bytes()

    aligned = 'bore_shift = 0[m];'
    along_x = 'quat(0.7071067811865476, 0, 0.7071067811865476, 0)'
    changes = [
        ('offset', aligned, 'bore_shift = 0.25[m];'),
        ('undersized', aligned, 'bore_half = 0.375[m];\n        ' + aligned),
        # The straight duct follows local +Z. Identity tilts its axis from +X to +Z.
        ('tilt', along_x, 'quat(1, 0, 0, 0)'),
        # World X+90 composed with the nominal placement Y+90, in source (w,x,y,z) order.
        ('roll', along_x, 'quat(0.5, 0.5, 0.5, 0.5)'),
    ]
    for name, old, new in changes:
        if nominal.entry.text.count(old) != 1:
            raise ValueError(f'{name} requires exactly one edit site in the entry')
        yield name, nominal.entry.text.replace(old, new).encode('utf-8')


def replay(output):
    nominal = load_file_manifest(HERE / 'assembly.files.json')
    output.mkdir(parents=True, exist_ok=False)
    options = ExportOptions(end='1', fps=2, helpers=False)
    cases = {}
    for name, source in source_cases(nominal):
        entry = SourceUnit('entry', nominal.entry.filename, source)
        bundle = ProgramBundle(entry, nominal.modules)
        result = execute_framed_loft_export(bundle, options=options)
        if result.data is None:
            raise ValueError(f'{name} source failed to export: {result.report["diagnostics"]}')
        raw = result.data
        (output / f'{name}.ok').write_bytes(source)
        (output / f'{name}.glb').write_bytes(raw)
        expected_failure = {
            'offset': 'straight rim corner differs',
            'undersized': 'straight rim corner differs',
            'tilt': 'straight cap normal differs',
        }.get(name)
        width = 1.25 if name == 'wide' else 1
        try:
            measurements = measure(raw, width)
        except JointFailure as exc:
            if str(exc) != expected_failure:
                raise ValueError(f'{name} failed an unexpected check: {exc}') from exc
            audit = {'passed': False, 'failure': str(exc), 'measurements': exc.measurements}
        else:
            if expected_failure:
                raise ValueError(f'{name} passed the joint check unexpectedly')
            audit = {'passed': True, 'measurements': measurements}
        cases[name] = {
            'program_revision': bundle.program_revision,
            'sources': bundle.manifest(),
            'glb_sha256': hashlib.sha256(raw).hexdigest(),
            'bytes': len(raw),
            'expected_bore_width_m': width,
            'expected_pass': expected_failure is None,
            'audit': audit,
        }
    (output / 'cases.json').write_text(json.dumps(cases, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path, help='new directory for sources, GLBs and measurements')
    replay(parser.parse_args().output)
