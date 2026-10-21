from dataclasses import asdict
from pathlib import Path
import hashlib
import json
import platform
import subprocess
import sys
import time
import traceback
from unittest.mock import patch

root, output, mode = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), sys.argv[3]
sys.path.insert(0, str(root))
from tools.reach_delivery_inventory import snapshot

output.mkdir(parents=True, exist_ok=False)
(output / 'run_source_mesh_checks.py').write_bytes(Path(__file__).read_bytes())
before = snapshot()
(output / 'inputs-before.json').write_text(json.dumps(before, indent=2) + '\n')
report = {'mode': mode, 'source_commit': before['git']['commit'], 'source_tree': before['git']['tree'],
          'python': sys.version, 'executable': sys.executable, 'platform': platform.platform(),
          'working_directory': str(root), 'status': 'running', 'full_recording_claimed': False}
started = time.monotonic()
compiler = None
try:
    if mode == 'tests':
        command = [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests',
                   '-p', 'test_reach_source_mesh_reuse.py', '-v']
        report['command'] = command
        with (output / 'tests.log').open('xb') as stream:
            completed = subprocess.run(command, cwd=root, stdin=subprocess.DEVNULL,
                                       stdout=stream, stderr=subprocess.STDOUT, timeout=180)
        report.update(returncode=completed.returncode, status='passed' if completed.returncode == 0 else 'failed')
    else:
        from ontokin.bundle import load_file_manifest
        from ontokin.construction import compile_construction
        from ontokin import scene
        report['command'] = [sys.executable, str(Path(__file__).resolve()), str(root), str(output), mode]
        report['source_manifest'] = 'docs/language-design/planar-reach-v0.1/p23.files.json'
        report['settings'] = {'helpers': False, 'phase': 'source compile and complete node construction'}
        compiler = compile_construction(load_file_manifest(root / report['source_manifest']), level='constructed')
        report['source_operations'] = compiler.budget.operations
        initial_counts = dict(compiler.reach_work.counts)
        report['shared_limits'] = {'max_operations': compiler.reach_work.max_operations,
                                   'max_cache_entries': compiler.reach_work.max_cache_entries}
        with patch('ontokin.scene.materialize_surface', wraps=scene.materialize_surface) as build:
            try:
                nodes = scene._nodes(compiler.model, scene.ExportOptions(fps=1, helpers=False),
                    check=compiler.reach_work.tick, work=compiler.reach_work if mode == 'candidate' else None)
            finally:
                report['materializations'] = build.call_count
                report['node_construction_operations'] = compiler.budget.operations - report['source_operations']
                report['node_construction_counts'] = {key: value - initial_counts.get(key, 0)
                    for key, value in compiler.reach_work.counts.items() if value != initial_counts.get(key, 0)}
        report['object_count'] = len(nodes)
        report['aggregate_vertices'] = sum(len(node.mesh.positions) for node in nodes if node.mesh)
        report['surface_occurrences'] = sum(isinstance(node.mesh, scene.SurfaceMesh) for node in nodes)
        report['unique_surface_meshes'] = len({id(node.mesh) for node in nodes if isinstance(node.mesh, scene.SurfaceMesh)})
        digest = hashlib.sha256()
        for node in nodes:
            digest.update(json.dumps(asdict(node), sort_keys=True, ensure_ascii=False,
                                     allow_nan=False, separators=(',', ':')).encode())
            digest.update(b'\n')
        report['complete_nodes_sha256'] = digest.hexdigest()
        report['status'] = 'passed'
except BaseException as error:
    report.update(status='failed', failure={'type': type(error).__name__, 'message': str(error)},
                  traceback=traceback.format_exc())
finally:
    if compiler is not None:
        report.update(operations=compiler.budget.operations, work=compiler.reach_work.record())
    after = snapshot(require_clean=False)
    (output / 'inputs-after.json').write_text(json.dumps(after, indent=2) + '\n')
    report['inputs_stable'] = before == after
    if before != after:
        report['status'] = 'failed'
    report['elapsed_seconds'] = time.monotonic() - started
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: value for key, value in report.items() if key not in ('work', 'traceback')}, indent=2))
