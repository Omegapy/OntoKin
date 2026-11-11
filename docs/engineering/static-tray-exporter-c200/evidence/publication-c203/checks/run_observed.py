"""Observe unchanged check commands without permitting native lifecycle starts."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import runpy
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', required=True, type=Path)
    parser.add_argument('--receipt', required=True, type=Path)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command
    if command and command[0] == '--':
        command = command[1:]
    repo = args.repo.resolve()
    initial = {'started_at_utc': datetime.now(timezone.utc).isoformat(),
               'actual_launcher_argv': list(sys.orig_argv),
               'target_argv': command, 'python': sys.executable,
               'python_version': platform.python_version(),
               'platform': platform.platform(), 'process_starts': []}
    def observe(event, details):
        if event != 'subprocess.Popen':
            return
        executable, argv, cwd, _ = details
        record = {'executable': str(executable), 'argv': list(argv) if not isinstance(argv, str) else argv,
                  'cwd': str(cwd) if cwd is not None else None}
        if Path(str(executable)).name not in {'git', 'python', 'python3', 'python3.12'}:
            record['blocked'] = True
            initial['process_starts'].append(record)
            raise RuntimeError('Unexpected child executable in CPU-only check')
        record['blocked'] = False
        initial['process_starts'].append(record)
    sys.addaudithook(observe)
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(repo))
    sys.argv = command
    target = repo / command[0]
    initial['target_sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
    result = 1
    try:
        runpy.run_path(str(target), run_name='__main__')
        result = 0
    except SystemExit as exc:
        result = exc.code or 0
    finally:
        initial['finished_at_utc'] = datetime.now(timezone.utc).isoformat()
        initial['exit_code'] = result
        initial['target_unchanged'] = hashlib.sha256(target.read_bytes()).hexdigest() == initial['target_sha256']
        args.receipt.write_text(json.dumps(initial, indent=2) + '\n')
    return result


if __name__ == '__main__':
    raise SystemExit(main())
