#!/usr/bin/env python3
"""Independent C269 frozen package inspection; no builder/product execution."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import stat
import subprocess
import sys
import zipfile

W = Path('/workspace/scratch/d59e10906594')
R = W / 'OntoKin'
OUT = W / 'session/final-package-review'
ZIP = W / 'packages/OntoKin_C269_Development_Handoff_2026-11-19.zip'
REV = '3ad6f2e0d56e1b97c87a63e1d3353aec899bfaf0'
TREE = '6ad85ea35edb68d747dbe3291883556b3c93c260'
EXPECTED = {'bytes': 925448, 'sha256': '6f09f8855c361f7157bc87f2c56d2a097df7aa60f78a779a90db9a124091200f'}
E = 'docs/engineering/localized-repair-c269'
T = 'docs/workflow/tasks/C269'
ENV = dict(os.environ, GIT_NO_LAZY_FETCH='1', GIT_TERMINAL_PROMPT='0')
CHECKS = []


def identity(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def require(condition, name, detail=None):
    if not condition:
        raise AssertionError(name + ': ' + str(detail))
    CHECKS.append({'check': name, 'passed': True, 'detail': detail})


def object_no_duplicates(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError('Duplicate JSON key: ' + key)
        value[key] = item
    return value


def parsed(raw):
    return json.loads(raw, object_pairs_hook=object_no_duplicates)


def git(*args):
    p = subprocess.run(['git', *args], cwd=R, env=ENV, capture_output=True)
    if p.returncode:
        raise RuntimeError('Read-only Git failed: ' + repr(args) + '\n' + p.stderr.decode())
    return p.stdout


def main():
    raw_zip = ZIP.read_bytes()
    require(identity(raw_zip) == EXPECTED, 'exact frozen archive identity', identity(raw_zip))
    config_bytes = (W/'session/final-config.json').read_bytes()
    config = parsed(config_bytes)
    root_receipt = parsed((W/'session/FINAL-HANDOFF-VERIFICATION.json').read_bytes())
    require(config['revision'] == REV and config['tree'] == TREE, 'config source binding')
    require(root_receipt['archive']['bytes'] == EXPECTED['bytes'] and root_receipt['archive']['sha256'] == EXPECTED['sha256'], 'root receipt refers to inspected ZIP')
    require(git('rev-parse', REV+'^{tree}').decode().strip() == TREE, 'actual Git source tree')

    extract = OUT/'fresh-extracted'
    require(not extract.exists(), 'independent extraction destination starts absent')
    extract.mkdir()
    with zipfile.ZipFile(ZIP) as archive:
        infos = archive.infolist()
        names = [row.filename for row in infos]
        require(len(names) == len(set(names)) == 224, 'duplicate-free 224-member inventory')
        for row in infos:
            name = row.filename
            p = PurePosixPath(name)
            require(not p.is_absolute() and '..' not in p.parts and '.' not in p.parts
                    and p.as_posix() == name and '\\' not in name and ':' not in name
                    and all(ord(c) >= 32 for c in name) and not row.is_dir(), 'safe file path', name)
            mode = row.external_attr >> 16
            require(not stat.S_ISLNK(mode), 'no archive symlink', name)
        require(archive.testzip() is None, 'CRC for every ZIP member')
        manifest = parsed(archive.read('MANIFEST-SHA256.json'))
        require('MANIFEST-SHA256.json' not in manifest and len(manifest) == 223, '223-item self-excluding manifest')
        require(set(names) == set(manifest) | {'MANIFEST-SHA256.json'}, 'exact manifest/member set')
        for row in infos:
            dest = extract/row.filename
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(archive.read(row.filename))
        for name, expected in manifest.items():
            require(identity((extract/name).read_bytes()) == expected, 'extracted payload size/SHA256', name)
        required = {'README-START-HERE.md','CHECKPOINT.json','HANDOFF.md','NEXT-TASK.md','RECOVERY-STATUS.md',
                    'PROMPT-1-CONTINUE.md','PROMPT-2-RECOVER.md','HISTORICAL-DEPENDENCIES.json','MANIFEST-SHA256.json'}
        require(required <= set(names), 'all nine required root files')

        snapshots = parsed((extract/'SNAPSHOT-SOURCES.json').read_bytes())
        require(snapshots['revision'] == REV and snapshots['tree'] == TREE, 'snapshot source declaration')
        rows = snapshots['files']
        require(len(rows) == 205, '205 declared Git snapshots')
        require(len({r['package_path'] for r in rows}) == len(rows), 'unique Git snapshot paths')
        require({r['package_path'] for r in rows} == {n for n in names if n.startswith('repository/')}, 'no unbound repository snapshots')
        git_entries = {}
        for item in git('ls-tree','-r','-z',REV).split(b'\0'):
            if item:
                head, path = item.split(b'\t',1)
                mode, kind, blob = head.decode().split()
                git_entries[path.decode()] = (mode,kind,blob)
        snapshot_records = []
        zip_mode_by_name = {row.filename: row.external_attr >> 16 for row in infos}
        for row in rows:
            path = row['repository_path']
            mode,kind,blob = git_entries[path]
            require(row['revision'] == REV and row['package_path'] == 'repository/'+path, 'snapshot path/revision', path)
            require(kind == 'blob' and row['mode'] == mode and row['git_blob'] == blob, 'snapshot Git mode/blob binding', path)
            data = (extract/row['package_path']).read_bytes()
            require(data == git('cat-file','blob',blob), 'snapshot bytes match actual Git blob', path)
            require(identity(data) == {'bytes':row['bytes'],'sha256':row['sha256']}, 'snapshot declared size/SHA256', path)
            require(stat.S_IMODE(zip_mode_by_name[row['package_path']]) == int(mode,8)&0o777,
                    'ZIP snapshot permission bits agree with Git', path)
            snapshot_records.append({'path':path,'revision':REV,'git_blob':blob,'mode':mode,**identity(data)})

        for name in ('OK-LANG-001-core-language-specification.md','OK-LANG-002-pinned-modules-and-keyed-assembly-construction.md'):
            path='repository/docs/language-design/'+name
            require(path in manifest and path in {r['package_path'] for r in rows}, 'P01 adopted specification included and Git-bound', path)

    cp = parsed((extract/'CHECKPOINT.json').read_bytes())
    task = parsed((extract/'repository'/T/'task.json').read_bytes())
    current = parsed((extract/'repository/docs/workflow/CURRENT.json').read_bytes())
    integration = parsed((extract/'repository'/E/'INTEGRATION.json').read_bytes())
    for key in ('observed_main','ownership','branch_state','pull_request','coverage_summary','verification','workers','completed'):
        require(cp[key] == config[key], 'checkpoint agrees with exact configuration', key)
    require(cp['source_snapshot_revision'] == REV and cp['source_snapshot_tree'] == TREE, 'checkpoint source identity')
    require(cp['observed_main']['sha'] == REV and cp['observed_main']['tree'] == TREE, 'observed main matches snapshot')
    require(cp['task'] == task['id'] == current['active_task'] == current['latest_task'] == 'C269', 'task/CURRENT/checkpoint identity')
    require(cp['parent_task_status'] == task['status'] == 'in_progress', 'parent stays in progress')
    require(cp['branch'] == task['branch'] and cp['scope_issue'] == task['scope_issue'] == 'https://github.com/Omegapy/OntoKin/issues/268', 'branch/issue identity')
    req = {row['id']:row['status'] for row in task['requirements']}
    require(cp['requirements'] == req == {**{f'R{i:02}':'done' for i in range(1,6)},'R06':'not_done'}, 'R01-R05 done; R06 pending')
    require(task['delivery']['status'] == 'pending' and 'save_pending' in cp['session_delivery_at_freeze'], 'save is pending in frozen records')
    require(cp['scope_issue_state'].startswith('open at freeze') and cp['ownership']['release'].startswith('pending'), 'issue closure and ownership release pending')
    require(task['completion']['merge_commit'] == integration['merge_commit'] == cp['pull_request']['merge_commit'] == 'c3bda080febf6359a6ad364b940d5d68f2741c9d', 'retained integration identity')
    require(task['completion']['branch_disposition'] == integration['branch']['disposition'] == 'deleted', 'recorded branch disposition agrees')
    require(current['observed_main'] == integration['merge_commit'], 'CURRENT preserves its original observed merge identity')
    require(git('merge-base','--is-ancestor',integration['merge_commit'],REV) == b'', 'merge retained in snapshot ancestry')

    historical = parsed((extract/'HISTORICAL-DEPENDENCIES.json').read_bytes())
    require(historical['C262'] == current['historical_handoff'], 'C262 unchanged dependency identity')
    require(historical['previous_C268'] == current['latest_handoff'], 'previous saved handoff identity')
    require(historical['C269_early_recovery'] == parsed((extract/'repository'/E/'EARLY-RECOVERY-RECEIPT.json').read_bytes()), 'early recovery receipt identity')
    require(historical['C269_early_recovery']['status']=='confirmed', 'early recovery remains confirmed')

    recovery = parsed((extract/'recovery/RECOVERY-BINDINGS.json').read_bytes())
    bundle = extract/'recovery/C269-bootstrap-native.bundle'
    bundle_expected={'bytes':55410,'sha256':'50ec91ed3e960995f8db2b4254650f0310b90355808a5ed7f2e5f49f1d5c10dd'}
    require(identity(bundle.read_bytes())==bundle_expected, 'P02 mandatory bundle exact identity')
    require(bundle.read_bytes()==(extract/'repository'/E/'evidence/publication/C269-bootstrap-native.bundle').read_bytes(), 'bundle equals Git-bound preserved native payload')
    require(recovery['files']==[{'path':'recovery/C269-bootstrap-native.bundle',**bundle_expected}], 'recovery file binding')
    require(recovery['base_revision']=='23c044775ad77e7c1ab2f27eb1c9dd4a67c004bb', 'restore prerequisite identity')
    require(recovery['native_commits']==['37d55eded8d903ff6dbf61fc5924783a983273e0','b9b0590b8155a6591ab9ed60bd03e2a59f56291e'], 'native recovery commit identities')
    heads=git('bundle','list-heads',str(bundle)).decode()
    require(heads.strip()=='b9b0590b8155a6591ab9ed60bd03e2a59f56291e HEAD', 'extracted bundle export head')
    verified=subprocess.run(['git','bundle','verify',str(bundle)],cwd=R,env=ENV,capture_output=True)
    (OUT/'bundle-verification.log').write_bytes(verified.stdout+verified.stderr)
    require(verified.returncode==0 and recovery['base_revision'] in verified.stdout.decode(), 'extracted bundle verifies with expected base prerequisite')
    native_tree=git('rev-parse',recovery['native_commits'][-1]+'^{tree}').decode().strip()
    require(native_tree==recovery['tree']==git('rev-parse',recovery['published_equivalent']+'^{tree}').decode().strip(), 'native/published same-tree identity')
    require(git('rev-parse',recovery['native_commits'][-1]+'^').decode().strip()==recovery['native_commits'][0], 'native commit parent retained')
    require('separate recovery ref' in recovery['restore'] and 'do not replay onto main' in recovery['restore'], 'executable safe recovery guidance')

    checks_path=extract/'session-evidence/published-checkpoint-checks/CHECKS.json'
    saved_checks=parsed(checks_path.read_bytes())
    require(saved_checks['source_revision']==REV and saved_checks['source_tree']==TREE and saved_checks['source_clean'] and saved_checks['result']=='passed', 'post-snapshot session checks identify actual source')
    require('session-evidence/published-checkpoint-checks/CHECKS.json' not in {r['package_path'] for r in rows}, 'session checks not claimed as Git snapshots')
    for row in saved_checks['checks']:
        log=checks_path.parent/row['log']['path']
        require(identity(log.read_bytes())=={'bytes':row['log']['bytes'],'sha256':row['log']['sha256']} and row['result']=='passed' and row['exit_code']==0, 'retained post-snapshot log identity/result', row['name'])
    require(identity((extract/'repository'/E/'evidence/run_record_checks.py').read_bytes())=={k:saved_checks['runner'][k] for k in ('bytes','sha256')}, 'session-check runner matches Git snapshot')

    for inside,outside in (('PROMPT-1-CONTINUE.md','OntoKin_C269_Continue.md'),('PROMPT-2-RECOVER.md','OntoKin_C269_Recover.md')):
        data=(extract/inside).read_bytes()
        require(data==(W/'packages'/outside).read_bytes(), 'standalone prompt byte identity', inside)
        text=data.decode()
        require(not any(s in text for s in ('[PASTE LINK]','[PASTE LINK OR NONE]','[DESCRIBE BRIEFLY OR UNKNOWN]','[LEAVE BLANK TO RESUME CURRENT TASK]')), 'all reusable prompt placeholders filled', inside)
        require('https://github.com/Omegapy/OntoKin' in text and ZIP.name in text and 'archive.url' in text and E+'/DELIVERY.json' in text, 'complete repository/archive/receipt prompt binding', inside)
        require('fresh chat' in text and 'early recovery ZIP' in text and 'stop' in text and 'first unmet gate' in text if inside=='PROMPT-2-RECOVER.md' else 'fresh chat' in text and 'early recovery ZIP' in text and 'Do not begin another phase' in text, 'complete procedural prompt and stop boundary', inside)
    next_task=(extract/'NEXT-TASK.md').read_bytes()
    require(next_task==(extract/'repository'/E/'NEXT-TASK.md').read_bytes(), 'next task is exact source snapshot')
    require(b'H16' in next_task and b'Finish any unmet C269 delivery/closure gate' in next_task and b'fresh continuation' in next_task, 'executable first unmet gate before queued next phase')
    for path in ('README-START-HERE.md','HANDOFF.md','RECOVERY-STATUS.md'):
        text=(extract/path).read_text()
        require('receipt' in text.lower() and ('external' in text.lower() or 'outside' in text.lower()), 'external future receipt boundary', path)
    readme=(extract/'README-START-HERE.md').read_text()
    require('not a complete offline backup' in readme and 'receipt/closure commits do not require rebuilding' in readme, 'online-only completeness and freeze boundary')
    require(cp['unknown_operations']==[] and cp['external_delivery_record']==E+'/DELIVERY.json', 'explicit unknown-operation and future receipt fields')
    require((extract/'session-evidence/build_final_handoff.py').read_bytes()==(W/'session/build_final_handoff.py').read_bytes(), 'frozen builder equals supplied reviewed current builder')
    require(identity(ZIP.read_bytes())==EXPECTED, 'frozen ZIP unchanged throughout review')

    result={'schema':'ontokin.c269.independent-final-package-review/0.1','reviewer':'/root/audit_h01_h14',
            'verdict':'approved','mandatory_findings':[],'archive':{'path':str(ZIP),**EXPECTED},
            'source_revision':REV,'source_tree':TREE,'independent_fresh_extraction':str(extract),
            'counts':{'archive_members':224,'manifest_payload_files':223,'git_snapshots':205,'adopted_specifications':2,
                      'standalone_prompts':2,'post_snapshot_check_logs':2,'checks_passed':len(CHECKS)},
            'preflight_dispositions':{'P01':'resolved: both specifications included from exact REV',
                                      'P02':'resolved: mandatory exact bundle verified after independent extraction'},
            'config_identity':identity(config_bytes),'builder_identity':identity((W/'session/build_final_handoff.py').read_bytes()),
            'checks':CHECKS,'git_snapshot_bindings':snapshot_records,'environment':{'python':sys.version,'platform':platform.platform()},
            'remaining_gates':['Confirmed final ZIP and both standalone prompt saves','Separate external delivery receipt',
                               'R06/task/issue closure and ownership release','Final live-state reconciliation and stop'],
            'limits':['Package verification only; no H01-H14 semantic re-review','No builder rebuild or product/observer/native/model execution',
                      'No independent new remote-state observation; packaged integration records/config agree',
                      'Online GitHub continuation; no complete offline restoration claim','Post-snapshot check logs are session evidence at source3ad, not Git snapshot files'],
            'unknown_operations':[]}
    (OUT/'RESULTS.json').write_text(json.dumps(result,indent=2)+'\n')
    (OUT/'INPUT-IDENTITIES.json').write_text(json.dumps({'archive':{'path':str(ZIP),**EXPECTED},
        'configuration':{'path':str(W/'session/final-config.json'),**identity(config_bytes)},
        'root_verification':{'path':str(W/'session/FINAL-HANDOFF-VERIFICATION.json'),**identity((W/'session/FINAL-HANDOFF-VERIFICATION.json').read_bytes())},
        'builder':{'path':str(W/'session/build_final_handoff.py'),**identity((W/'session/build_final_handoff.py').read_bytes())}},indent=2)+'\n')
    print(json.dumps({'verdict':result['verdict'],'archive':result['archive'],'counts':result['counts'],'mandatory_findings':[]},indent=2))


if __name__=='__main__':
    main()
