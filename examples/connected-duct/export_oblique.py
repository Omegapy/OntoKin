"""Export the independently placed nominal, shifted, and repaired source assemblies."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from agent_repair import ALIGNED, OFFSET, OPTIONS
from ontokin.budget_runtime import execute_framed_loft_export
from ontokin.bundle import ProgramBundle, SourceUnit, load_file_manifest
from ontokin.scene import ExportOptions


def replay(output):
    nominal = load_file_manifest(HERE / 'assembly-oblique.files.json')
    source = nominal.entry.text
    if source.count(ALIGNED) != 1 or OFFSET in source:
        raise ValueError('Expected one editable nominal bore shift')
    defective = source.replace(ALIGNED, OFFSET)
    output.mkdir(parents=True, exist_ok=False)
    cases = {}
    for label, text in [('nominal', source), ('defective', defective),
                        ('repaired', defective.replace(OFFSET, ALIGNED))]:
        entry = SourceUnit('entry', nominal.entry.filename, text.encode('utf-8'))
        bundle = ProgramBundle(entry, nominal.modules)
        result = execute_framed_loft_export(bundle, options=ExportOptions(**OPTIONS))
        if result.data is None:
            raise ValueError(f'{label} export failed: {result.report["diagnostics"]}')
        (output / f'{label}.ok').write_bytes(entry.raw)
        (output / f'{label}.glb').write_bytes(result.data)
        cases[label] = {'program_revision': bundle.program_revision, 'sources': bundle.manifest(),
                        'glb_sha256': hashlib.sha256(result.data).hexdigest(), 'bytes': len(result.data)}
    if cases['nominal'] != cases['repaired'] or cases['defective']['glb_sha256'] == cases['nominal']['glb_sha256']:
        raise ValueError('The defect and repair did not produce the expected artifact identities')
    (output / 'cases.json').write_text(json.dumps(cases, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path, help='new directory for direct exports')
    replay(parser.parse_args().output)
