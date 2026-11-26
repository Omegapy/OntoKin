"""Run one frozen P29 command with immutable attempt paths and source identities."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys

BASE = Path('/workspace/scratch/2eb33b59a678')
REPO = BASE / 'repository'
AREA = REPO / 'docs/engineering/localized-repair-c271/required-images-p29'


def digest(path):
    data = path.read_bytes()
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def verify_freeze(expected_sha256):
    assert re.fullmatch(r'[0-9a-f]{64}', expected_sha256)
    freeze_path = AREA / 'controls/FREEZE.json'
    assert digest(freeze_path)['sha256'] == expected_sha256, 'Accepted freeze identity changed'
    freeze = json.loads(freeze_path.read_text())
    assert freeze['schema'] == 'ontokin.c271.p29-required-images-freeze/1'
    assert freeze['obligations'] == 116

    def verify_rows(rows):
        seen = set()
        for row in rows:
            relative = row['path']
            part = Path(relative)
            assert not part.is_absolute() and '..' not in part.parts and str(part) == relative
            assert relative not in seen, 'Duplicate frozen path'
            seen.add(relative)
            path = REPO / part
            info = path.lstat()
            assert path.resolve() == path and stat.S_ISREG(info.st_mode), 'Nonregular frozen file'
            assert stat.S_IMODE(info.st_mode) == int(row['mode'], 8), 'Frozen file mode changed'
            assert digest(path) == {'bytes': row['size_bytes'], 'sha256': row['sha256']}, relative
        return seen

    payloads = verify_rows(freeze['files'])
    actual = {p.relative_to(REPO).as_posix() for p in (AREA / 'controls').rglob('*')
              if p.is_file() and p != freeze_path}
    actual.add(freeze['adapter']['path'])
    assert payloads == actual, 'Frozen payload inventory changed'
    verify_rows([freeze['adapter'], freeze['fixture_manifest']])
    companion_path = AREA / 'controls/COMPANIONS.json'
    assert companion_path.relative_to(REPO).as_posix() in payloads
    companions = json.loads(companion_path.read_text())
    bound_companions = verify_rows(companions['files'])
    cohort_path = AREA / 'INHERITED-COHORT.json'
    assert cohort_path.relative_to(REPO).as_posix() in bound_companions
    cohort = json.loads(cohort_path.read_text())
    for row in cohort['generated_method_sources']:
        assert digest(REPO / row['path']) == {'bytes': row['bytes'], 'sha256': row['sha256']}
    return {'accepted_freeze_sha256': expected_sha256, 'verified_payloads': len(payloads),
            'verified_companions': len(bound_companions),
            'verified_generated_inventory_sources': len(cohort['generated_method_sources']),
            'verified_before_process_start': True}


def main(label, kind, accepted_freeze_sha256):
    assert re.fullmatch(r'[a-z0-9_-]+', label)
    assert kind in ('focused', 'inherited')
    out = BASE / 'verification' / label
    out.mkdir(parents=True, exist_ok=False)
    try:
        freeze_verification = verify_freeze(accepted_freeze_sha256)
    except Exception as error:
        write(out / 'PRELAUNCH-REFUSAL.json', {'exception_type': type(error).__name__,
              'message': str(error), 'process_started': False})
        raise
    commands = json.loads((AREA / 'controls/COMMANDS.json').read_text())
    command = commands['focused' if kind == 'focused' else 'inherited_command']
    env = os.environ.copy()
    retained = ['ONTOKIN_REQUIRED_IMAGES_RETAIN_ROOT', 'ONTOKIN_HI_RETAIN_ROOT',
                'ONTOKIN_ELF_RETAIN_ROOT', 'ONTOKIN_LP_RETAIN_ROOT',
                'ONTOKIN_LIBC_RETAIN_ROOT', 'ONTOKIN_RTLD_RETAIN_ROOT',
                'ONTOKIN_INHERITED_RETAIN_ROOT']
    for key in retained:
        env.pop(key, None)
    selected_env = {'PYTHONDONTWRITEBYTECODE': '1',
                    'ONTOKIN_INHERITED_INVENTORY_PATH': str(out / 'RUNTIME-INVENTORY.json')}
    data = out / 'control-data'
    data.mkdir()
    if kind == 'focused':
        selected_env[retained[0]] = str(data / 'required-images')
    else:
        selected_env['ONTOKIN_INHERITED_RETAIN_ROOT'] = str(data / 'inherited')
    env.update(selected_env)
    source_paths = [REPO / 'prototypes/static_tray_v01/current_host_inspection_v01.py',
                    REPO / 'tests/test_current_host_required_images_v01.py',
                    AREA / 'INHERITED-COHORT.json']
    cohort = json.loads((AREA / 'INHERITED-COHORT.json').read_text())
    source_paths += [REPO / row['path'] for row in cohort['modules']]
    source_paths += [p for p in (AREA / 'controls').rglob('*') if p.is_file()]
    sources = {p.relative_to(REPO).as_posix(): digest(p) for p in sorted(set(source_paths))}
    snapshot = out / 'source-snapshot'
    snapshot.mkdir()
    for path in source_paths[:2]:
        shutil.copyfile(path, snapshot / path.name)
    request = {'label': label, 'kind': kind, 'command': command, 'cwd': str(REPO),
               'freeze_verification': freeze_verification,
               'started_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'runner_python': {'executable': sys.executable, 'version': sys.version},
               'command_executable': shutil.which(command[0], path=env.get('PATH')),
               'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip(),
               'selected_environment': selected_env, 'sources': sources,
               'scope': 'Frozen inert controls; no operational host admission or native targets. The inherited driver has one environment-transport Python child; this is not a global process count.'}
    write(out / 'REQUEST.json', request)
    with (out / 'stdout.log').open('wb') as stdout, (out / 'stderr.log').open('wb') as stderr:
        process = subprocess.Popen(command, cwd=REPO, env=env, stdout=stdout, stderr=stderr)
        write(out / 'PROCESS.json', {'pid': process.pid, 'status': 'started_not_yet_complete', 'command': command})
        code = process.wait()
    changed = [relative for relative, identity in sources.items() if digest(REPO / relative) != identity]
    result = {'label': label, 'kind': kind, 'returncode': code, 'pid': process.pid,
              'completed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'source_changes_during_run': changed,
              'stdout': digest(out / 'stdout.log'), 'stderr': digest(out / 'stderr.log')}
    write(out / 'RESULT.json', result)
    print(json.dumps(result))
    return code if code else (2 if changed else 0)


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:]))
