"""Execute the explicitly selected C211 one-import/save/reopen proof.

Do not start this command until the integrator has saved the contract and exact
implementation checkpoint. This driver never retries a process or overwrites an
existing experiment directory. It does not implement the deferred C201 protocol.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import subprocess
import sys
import time

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from validation import BUILD, INPUTS, identity, validate_build, validate_inputs, validate_observations


def write(path, data):
    Path(path).write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')


def run_stage(label, inputs, output, timeout=300):
    command = [BUILD['executable']['path'], '--background', '--factory-startup', '--threads', '2',
        '--python-exit-code', '1', '--python', str(HERE/'blender_observe.py'), '--',
        '--inputs', str(inputs), '--output', str(output), '--mode', label]
    receipt = {'stage': label, 'command': command, 'cwd': str(output), 'timeout_seconds': timeout,
               'started_utc': datetime.now(timezone.utc).isoformat(), 'status': 'start_reserved',
               'returncode': None, 'attempt': 1}
    path = output/(label+'-process.json')
    write(path, receipt)
    start = time.monotonic()
    with (output/(label+'-stdout.log')).open('w') as stdout, (output/(label+'-stderr.log')).open('w') as stderr:
        process = subprocess.Popen(command, cwd=output, stdout=stdout, stderr=stderr, start_new_session=True,
                                   env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
        receipt['pid'] = process.pid
        receipt['status'] = 'running'
        write(path, receipt)
        try:
            receipt['returncode'] = process.wait(timeout=timeout)
            receipt['status'] = 'completed' if process.returncode == 0 else 'failed'
        except subprocess.TimeoutExpired:
            receipt['status'] = 'timed_out'
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            receipt['returncode'] = process.returncode
        finally:
            receipt['elapsed_seconds'] = time.monotonic()-start
            receipt['finished_utc'] = datetime.now(timezone.utc).isoformat()
            write(path, receipt)
    if receipt['status'] != 'completed':
        raise RuntimeError(label + ' process failed; original receipt/logs retained; no retry')
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    summary = {'schema': 'ontokin.c211.receiving-run/0.1', 'status': 'pending', 'stages': [],
        'python': sys.version, 'platform': platform.platform(), 'full_release': False,
        'visual_review': 'pending independent inspection', 'no_automatic_retries': True}
    try:
        semantic, reference, reader = validate_inputs(args.inputs)
        validate_build()
        inputs = output/'inputs'
        inputs.mkdir()
        for name in INPUTS['files']:
            shutil.copyfile(args.inputs/name, inputs/name)
        validate_inputs(inputs)
        source_files = [p for p in sorted(HERE.iterdir()) if p.suffix in ('.py', '.json')]
        before = {p.name: identity(p) for p in source_files}
        repo = HERE.parents[1]
        git_identity = {name: subprocess.check_output(['git', *args], cwd=repo, text=True).strip() for name, args in [('commit', ['rev-parse', 'HEAD']), ('tree', ['rev-parse', 'HEAD^{tree}']), ('status', ['status', '--porcelain'])]}
        write(output/'execution-inputs.json', {'source_files': before, 'git_identity': git_identity,
             'frozen_inputs': INPUTS, 'build_manifest': identity(HERE/'build_bindings.json'),
             'contract': identity(HERE.parents[1]/'docs/engineering/semantic-receiving-c211/CONTRACT.md')})
        summary['stages'].append(run_stage('import', inputs, output))
        imported = json.loads((output/'import-observations.json').read_text())
        imported_result = validate_observations(imported, semantic, reference, reader)
        write(output/'import-validation.json', imported_result)
        summary['stages'].append(run_stage('reopen', inputs, output))
        reopened = json.loads((output/'reopen-observations.json').read_text())
        reopened_result = validate_observations(reopened, semantic, reference, reader)
        write(output/'reopen-validation.json', reopened_result)
        after = {p.name: identity(p) for p in source_files}
        if before != after:
            raise RuntimeError('Receiving implementation changed during execution')
        summary['implementation_stable'] = True
        summary['git_identity'] = git_identity
        summary['status'] = 'numeric_and_metadata_checks_passed'
        summary['import'] = imported_result
        summary['reopen'] = reopened_result
        summary['received_blend'] = identity(output/'received.blend')
        summary['renders'] = imported['renders']
    except Exception as exc:
        summary['status'] = 'failed'
        summary['error_type'] = type(exc).__name__
        summary['error'] = str(exc)
        raise
    finally:
        write(output/'SUMMARY.json', summary)
    print(json.dumps({'status': summary['status'], 'output': str(output), 'visual_review': summary['visual_review']}))


if __name__ == '__main__':
    main()
