from pathlib import Path
import hashlib
import json
import os
import stat
import sys
from datetime import datetime, timezone


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def descriptor(path):
    path = Path(path)
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode):
        raise ValueError('Expected regular, nonsymlink file: ' + str(path))
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': digest(raw), 'mode': oct(stat.S_IMODE(info.st_mode))}


def compare_file(expected, category, results):
    actual = descriptor(expected['path'])
    match = all(actual[key] == expected[key] for key in ('bytes', 'sha256', 'mode'))
    results.append({'category': category, 'expected': expected, 'actual': actual, 'match': match})
    if not match:
        raise ValueError('File identity mismatch: ' + expected['path'])
    return actual


def aliases(plan):
    rows = []
    for item in plan['aliases']:
        path = Path(item['path'])
        info = path.lstat()
        resolved = str(path.resolve(strict=True))
        row = {'path': str(path), 'resolved_path': resolved, 'symlink': path.is_symlink(), 'link_target': os.readlink(path) if path.is_symlink() else None, 'mode': oct(stat.S_IMODE(info.st_mode))}
        rows.append(row)
        if resolved != item['resolved_path'] or not path.is_symlink():
            raise ValueError('Alias identity mismatch: ' + str(path))
    return rows


def site_inventory(site_root, expected_files):
    site = Path(site_root)
    expected = {item['path'] for item in expected_files if Path(item['path']).is_relative_to(site)}
    actual = set()
    directories = []
    for directory, dirs, files in os.walk(site, followlinks=False):
        directory = Path(directory)
        directories.append({'path': str(directory), 'mode': oct(stat.S_IMODE(directory.lstat().st_mode))})
        for name in dirs:
            if (directory/name).is_symlink():
                raise ValueError('Unexpected symlink directory: ' + str(directory/name))
        for name in files:
            path = directory/name
            if not stat.S_ISREG(path.lstat().st_mode):
                raise ValueError('Unexpected nonregular site file: ' + str(path))
            actual.add(str(path))
    if actual != expected:
        raise ValueError('Site inventory mismatch: ' + json.dumps({'extra': sorted(actual-expected), 'missing': sorted(expected-actual)}))
    return {'site_file_count': len(actual), 'files': sorted(actual), 'directories': sorted(directories, key=lambda x:x['path'])}


def main():
    if len(sys.argv) != 3:
        raise ValueError('Expected plan path and independently supplied SHA256')
    plan_path = Path(sys.argv[1])
    plan_raw = plan_path.read_bytes()
    if digest(plan_raw) != sys.argv[2]:
        raise ValueError('Plan digest mismatch')
    plan = json.loads(plan_raw)
    review = json.loads(Path(plan['independent_review']).read_text())
    script_sha = digest(Path(__file__).read_bytes())
    if review['verdict'] != 'accepted_for_execution' or review['plan_sha256'] != sys.argv[2] or review['script_sha256'] != script_sha:
        raise ValueError('Independent review does not bind this candidate')
    early = json.loads(Path(plan['early_receipt']['path']).read_text())
    if not early['early_before_technical_work'] or not early['saved_bytes_readback_equal'] or early['status'] != 'confirmed_saved_and_byte_read_back':
        raise ValueError('Early recovery not confirmed')
    output = Path(plan['output'])
    if output.exists() or output.is_symlink() or Path(plan['pycache_prefix']).exists():
        raise ValueError('Fresh output/cache path required')
    result = {'schema':'ontokin.c271.p21-static-rebind-result/1', 'started_at_utc':datetime.now(timezone.utc).isoformat(), 'plan_sha256':sys.argv[2], 'script_sha256':script_sha, 'source_revision':plan['source_revision'], 'argv':sys.orig_argv, 'cwd':os.getcwd(), 'checks':[], 'status':'in_progress', 'package_imports':False, 'product_imports':False, 'child_processes':0, 'node_ldd_direct_loader_starts':0, 'h0_accepted':False, 'h1_executed':False, 'full_routine_executed':False}
    try:
        for row in plan['bound_documents']:
            compare_file(row, 'bound_document', result['checks'])
        if str(Path(sys.executable).resolve(strict=True)) != plan['python']['path']:
            raise ValueError('Controller interpreter differs from selected canonical file')
        result['python_version'] = sys.version
        if sys.version_info[:3] != (3,12,14):
            raise ValueError('Controller interpreter version mismatch')
        compare_file(plan['python'], 'canonical_python', result['checks'])
        p20 = json.loads(Path(plan['p20_result']).read_text())
        inventory = json.loads(Path(plan['p20_inventory']).read_text())
        installed = p20['installed']['files']
        if len(installed) != 293 or len(p20['installed']['packages']) != 7 or p20['installed']['native_artifacts_hashed_as_data'] != 27:
            raise ValueError('Unexpected P20 inventory shape')
        targets = [('venv_config', p20['venv']['cfg'])]
        targets += [('installed_file', row) for row in installed]
        targets += [('shared_metadata', row) for row in inventory['shared_package_metadata']]
        targets += [('shared_pth', row) for row in inventory['shared_pth_files']]
        targets += [('locked_wheel', row) for row in plan['packaged_wheels']]
        targets += [('current_source', row) for row in plan['source_files']]
        result['aliases_before'] = aliases(plan)
        result['site_inventory_before'] = site_inventory(p20['installed']['site_root'], installed)
        for category, expected in targets:
            compare_file(expected, 'before_'+category, result['checks'])
        result['packages'] = []
        for package in p20['installed']['packages']:
            raw = Path(package['metadata']['path']).read_text()
            headers = [line for line in raw.split('\n\n',1)[0].splitlines() if line.startswith(('Name: ', 'Version: '))]
            want = ['Name: '+package['name'], 'Version: '+package['version']]
            if headers != want:
                raise ValueError('Package metadata differs: '+package['name'])
            result['packages'].append({'name':package['name'],'version':package['version'],'metadata_path':package['metadata']['path']})
        result['aliases_after'] = aliases(plan)
        result['site_inventory_after'] = site_inventory(p20['installed']['site_root'], installed)
        if result['aliases_after'] != result['aliases_before'] or result['site_inventory_after'] != result['site_inventory_before']:
            raise ValueError('Input directory/alias drift during observation')
        for category, expected in targets:
            compare_file(expected, 'after_'+category, result['checks'])
        compare_file(plan['python'], 'canonical_python_after', result['checks'])
        for row in plan['bound_documents']:
            compare_file(row, 'bound_document_after', result['checks'])
        if Path(plan['pycache_prefix']).exists():
            raise ValueError('Fresh cache path was created')
        result['status'] = 'passed_static_rebind_only'
        result['installed_file_count'] = 293
        result['native_files_hashed_without_loading'] = 27
        result['wheel_count'] = len(plan['packaged_wheels'])
        result['first_failure'] = None
    except Exception as error:
        result['status'] = 'blocked_first_observed_failure'
        result['first_failure'] = {'type':type(error).__name__,'message':str(error)}
    result['finished_at_utc'] = datetime.now(timezone.utc).isoformat()
    result['limits'] = 'Current static preservation evidence only; no ordinary package discovery, native compatibility, operational validator dispatch or H0 acceptance'
    with output.open('x') as stream:
        json.dump(result,stream,indent=2)
        stream.write('\n')
    print(json.dumps({'status':result['status'],'checks':len(result['checks']),'first_failure':result['first_failure'],'output':str(output)}))
    return 0 if result['status']=='passed_static_rebind_only' else 2


if __name__ == '__main__':
    raise SystemExit(main())
