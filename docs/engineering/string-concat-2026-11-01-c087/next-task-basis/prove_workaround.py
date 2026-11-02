"""Run only the existing .19 typed reduction workaround on exact C086."""
from pathlib import Path
import hashlib
import json
import platform
import subprocess
import sys

from ontokin.construction import compile_construction
from ontokin.execution_budget import SharedExecutionBudget, admit_entry_budget
from ontokin.texture_bundle import load_texture_file_manifest


HERE = Path(__file__).resolve().parent
BASELINE = Path('/tmp/ontokin-c087-c086-recovered/OntoKin')
expected = json.loads((HERE / 'workaround-expected.json').read_bytes())
bundle = load_texture_file_manifest(HERE / 'membership-workaround.files.json')
ledger = SharedExecutionBudget()
admit_entry_budget(bundle.entry, ledger, profile='keyed-rekey-0.1')
compiler = compile_construction(bundle, level='constructed', execution_budget=ledger)
actual = {path: compiler.memo[(path, 'width')].value for path in expected['expected_widths_m']}
report = {
    'scope': 'Existing .19 helper workaround only; no new membership operation implemented or executed.',
    'baseline_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=BASELINE, text=True).strip(),
    'interpreter': sys.executable, 'python': platform.python_version(),
    'source_path': str(HERE / 'membership-workaround.ok'),
    'source_sha256': hashlib.sha256((HERE / 'membership-workaround.ok').read_bytes()).hexdigest(),
    'expected_sha256': hashlib.sha256((HERE / 'workaround-expected.json').read_bytes()).hexdigest(),
    'program_revision': bundle.program_revision,
    'expected_widths_m': expected['expected_widths_m'], 'actual_widths_m': actual,
    'status': 'passed' if actual == expected['expected_widths_m'] else 'failed',
    'execution': ledger.report(),
}
(HERE / 'workaround-observation.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
assert actual == expected['expected_widths_m'], report
