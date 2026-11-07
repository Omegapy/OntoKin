"""Build functioning square-rim impostors and require the independent oracle to reject them."""
import argparse
import json
import math
from pathlib import Path

from agent_repair import OPTIONS
from agent_place import replacement
from ontokin.bundle import ProgramBundle, SourceUnit, load_file_manifest
from ontokin.budget_runtime import execute_framed_loft_export
from ontokin.scene import ExportOptions
from tools.verify_duct_placement import CONTRACT, endpoints, verify


def run(before, output):
    spec = json.loads(CONTRACT.read_text())
    bundle = load_file_manifest(CONTRACT.with_name('assembly-misplaced.files.json'))
    w, x, y, z = spec['straight_target_rotation_wxyz']
    joint = spec['elbow_outlet_center_m']
    # Reverse the straight axis and land its top face on the elbow outlet.
    # A half-turn about the straight axis instead gives a flush, but wrong-roll, joint.
    cases = [('wrong-endpoint', spec['straight_outlet_center_m'], [-y, -z, w, x], 'top'),
             ('wrong-roll', joint, [-z, y, -x, w], 'bottom')]
    output.mkdir(parents=True, exist_ok=False)
    report = {}
    for name, origin, rotation, region in cases:
        old, new = replacement(bundle.entry.text, dict(translation_m=origin, rotation_wxyz=rotation))
        source = bundle.entry.text.replace(old, new).encode()
        entry = SourceUnit('entry', bundle.entry.filename, source)
        result = execute_framed_loft_export(ProgramBundle(entry, bundle.modules), options=ExportOptions(**OPTIONS))
        if result.data is None:
            raise ValueError(f'{name} failed to export')
        (output / f'{name}.ok').write_bytes(source)
        (output / f'{name}.glb').write_bytes(result.data)
        _, _, faces = endpoints(result.data)
        endpoint, normal = faces['straight', region]
        cap, cap_normal = faces['elbow', 'top']
        distance = math.dist(endpoint, cap)
        normal_error = math.dist(normal, [-v for v in cap_normal])
        if max(distance, normal_error) > 1e-5:
            raise ValueError(f'{name} failed to construct the intended impostor')
        try:
            verify(before, result.data)
        except ValueError as exc:
            report[name] = dict(rejection=str(exc), straight_endpoint=region,
                                wrong_or_ambiguous_endpoint_gap_m=distance,
                                opposing_normal_error=normal_error)
        else:
            raise ValueError(f'{name} escaped verification')
    (output / 'results.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('before', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    run(args.before.read_bytes(), args.output)
