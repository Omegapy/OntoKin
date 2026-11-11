"""Reproducible editable source fixtures for the predeclared Q01-Q05 inputs."""

from fractions import Fraction
import hashlib
import json
from pathlib import Path

from .canonical import ROOT, PARTS, json_bytes

PARAMETER_NAMES = ("payload_width", "payload_height", "payload_depth", "clearance", "wall_thickness", "base_thickness", "headroom")
PARAMETER_KEYS = ("payload-width", "payload-height", "payload-depth", "clearance", "wall-thickness", "base-thickness", "headroom")


def module_source(*, reverse_parts=False):
    lines = ['ontokin "0.2";', 'module StaticTray @ "static-tray";', 'profile "construction-0.1";',
             'private class Box @ "box" {',
             ' public param extent @ "extent": Vec3<Length> = vec3(1[m], 1[m], 1[m]);',
             ' geometry = box(self.extent);', ' physical = no_body();',
             ' motion = prescribed;', ' collision = disabled;',
             ' appearance = rgba(0.25, 0.5, 0.75, 1);', '}',
             'public class Tray @ "tray" {']
    for name, key, value in zip(PARAMETER_NAMES, PARAMETER_KEYS, (.2, .06, .12, .005, .004, .006, .02)):
        lines.append(f' public param {name} @ "{key}": Length = {value}[m];')
    lines.extend([' role = "tray-root";', ' geometry = empty();', ' physical = no_body();',
                  ' motion = prescribed;', ' collision = disabled;',
                  ' private derive W @ "width": Length = self.payload_width + (2 * self.clearance);',
                  ' private derive D @ "depth": Length = self.payload_depth + (2 * self.clearance);',
                  ' private derive H @ "height": Length = self.payload_height + self.headroom;',
                  ' private derive OX @ "outer-width": Length = self.W + (2 * self.wall_thickness);',
                  ' private derive OZ @ "outer-depth": Length = self.D + (2 * self.wall_thickness);'])
    geometry = {
        'base': ('self.OX, self.base_thickness, self.OZ', '0[m], -(self.base_thickness / 2), 0[m]'),
        'front': ('self.OX, self.H, self.wall_thickness', '0[m], self.H / 2, (self.D + self.wall_thickness) / 2'),
        'back': ('self.OX, self.H, self.wall_thickness', '0[m], self.H / 2, -((self.D + self.wall_thickness) / 2)'),
        'left-wall': ('self.wall_thickness, self.H, self.D', '-((self.W + self.wall_thickness) / 2), self.H / 2, 0[m]'),
        'right-wall': ('self.wall_thickness, self.H, self.D', '(self.W + self.wall_thickness) / 2, self.H / 2, 0[m]'),
        'payload': ('self.payload_width, self.payload_height, self.payload_depth', '0[m], self.payload_height / 2, 0[m]')}
    for key in reversed(PARTS) if reverse_parts else PARTS:
        name = key.replace('-', '_')
        size, offset = geometry[key]
        lines.extend([f' private part {name} @ "{key}": Box {{', f'  extent = vec3({size});',
                      f'  role = "{"payload-proxy" if key == "payload" else key}";'])
        if key == 'payload':
            lines.append('  appearance = rgba(0.75, 0.5, 0.25, 1);')
        lines.extend([' }', f' private follow follow_{name} @ "follow-{key}" {{',
                      '  parent = self.frame;', f'  child = self.{name};',
                      f'  offset = pose(self.frame, vec3({offset}), quat(1, 0, 0, 0));', ' }'])
    return '\n'.join(lines + ['}', '']).encode()


def _literal(v, unit):
    if unit == 'mm':
        # Exact decimal conversion avoids a binary64 multiply changing P02.
        from decimal import Decimal
        return format(Decimal(str(v)) * 1000, 'f') + '[mm]'
    return str(v) + '[m]'


def main_source(sets, module, *, units='m', reverse_roots=False, negate_quaternions=False):
    digest = hashlib.sha256(module).hexdigest()
    lines = ['ontokin "0.2";', 'module EquipmentTray @ "equipment-tray";',
             'profile "construction-0.1";',
             f'import trays @ "tray-library" from "ontokin.static-tray" version "0.1.0" digest "sha256:{digest}";',
             'scene Pair @ "pair" {', ' duration = 1[s];',
             ' gravity = vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2]);']
    for side in ('right', 'left') if reverse_roots else ('left', 'right'):
        item = sets[side]
        values = [*item['payload_m'], item['clearance_m'], item['wall_m'], item['base_m'], item['headroom_m']]
        lines.append(f' object {side} @ "{side}": trays.Tray {{')
        for name, value in zip(PARAMETER_NAMES, values):
            lines.append(f'  {name} = {_literal(value, units)};')
        q = [-v for v in item['rotation_wxyz']] if negate_quaternions else item['rotation_wxyz']
        lines.append('  placement = pose(world, vec3(' + ', '.join(_literal(v, units) for v in item['translation_m'])
                     + '), quat(' + ', '.join(str(v) for v in q) + '));')
        lines.append(' }')
    return '\n'.join(lines + ['}', '']).encode()


PYTHON_HELPER = '''from fractions import Fraction
from struct import pack

def rn(value):
    value = float(value)
    return 0.0 if value == 0 else value

def add(a, b):
    return rn(Fraction(a) + Fraction(b))

def mul(a, b):
    return rn(Fraction(a) * Fraction(b))

def div(a, b):
    return rn(Fraction(a) / Fraction(b))

def bits(value):
    return pack(">d", rn(value)).hex()

def make_tray(side, values):
    px, py, pz = values["payload_m"]
    c, t, b, h = values["clearance_m"], values["wall_m"], values["base_m"], values["headroom_m"]
    width, depth = add(px, mul(2, c)), add(pz, mul(2, c))
    height = add(py, h)
    ox, oz = add(width, mul(2, t)), add(depth, mul(2, t))
    half_y, wall_x, wall_z = div(height, 2), div(add(width, t), 2), div(add(depth, t), 2)
    geometry = {
        "back": ((ox, height, t), (0, half_y, -wall_z)),
        "base": ((ox, b, oz), (0, -div(b, 2), 0)),
        "front": ((ox, height, t), (0, half_y, wall_z)),
        "left-wall": ((t, height, depth), (-wall_x, half_y, 0)),
        "payload": ((px, py, pz), (0, div(py, 2), 0)),
        "right-wall": ((t, height, depth), (wall_x, half_y, 0))}
    sid = ["equipment-tray", "pair", side]
    parts = []
    for key in ("back", "base", "front", "left-wall", "payload", "right-wall"):
        size, offset = geometry[key]
        parts.append({"id": sid + [key], "owner_id": sid, "key": key,
            "role": "payload-proxy" if key == "payload" else key,
            "geometry": {"type": "box", "size_m": [bits(v) for v in size]},
            "physical": "no_body", "motion": "prescribed", "collision": "disabled",
            "material": "payload" if key == "payload" else "tray",
            "following": {"id": sid + ["follow-" + key], "parent_id": sid,
                "offset": {"reference": "parent-frame", "translation_m": [bits(v) for v in offset],
                           "rotation_wxyz": [bits(v) for v in (1, 0, 0, 0)]}}})
    rotation = values["rotation_wxyz"]
    first = [v for v in rotation if v != 0][0]
    if first < 0:
        rotation = [-v for v in rotation]
    return {"id": sid, "owner_id": sid[:2], "role": "tray-root", "geometry": "empty",
        "physical": "no_body", "motion": "prescribed", "collision": "disabled",
        "root_pose": {"reference": "world", "translation_m": [bits(v) for v in values["translation_m"]],
                      "rotation_wxyz": [bits(v) for v in rotation]},
        "parameters": {"payload_size_m": [bits(v) for v in (px, py, pz)],
                       "horizontal_clearance_m": bits(c), "wall_thickness_m": bits(t),
                       "base_thickness_m": bits(b), "headroom_m": bits(h)}, "parts": parts}
'''.encode()


def python_sources(sets):
    from .canonical import CONSTANTS
    text = 'from tray import make_tray\n\n'
    for side in ('left', 'right'):
        text += side + ' = ' + repr(sets[side]) + '\n'
    text += 'record = ' + repr(CONSTANTS) + '\n'
    text += 'record["trays"] = [make_tray("left", left), make_tray("right", right)]\n'
    return {'main.py': text.encode(), 'tray.py': PYTHON_HELPER}


def write_sources(directory, route, sets, **variants):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    if route == 'ontokin':
        module = module_source(reverse_parts=variants.pop('reverse_parts', False))
        files = {'main.ok': main_source(sets, module, **variants), 'tray.ok': module}
        manifest = {'schema_version': 'ontokin.files/0.1',
                    'entry': {'filename': 'main.ok', 'path': 'main.ok'},
                    'modules': [{'package_id': 'ontokin.static-tray', 'version': '0.1.0',
                                 'filename': 'tray.ok', 'path': 'tray.ok'}]}
    elif route == 'direct-python':
        files = python_sources(sets)
        manifest = {'schema_version': 'ontokin.static-tray.python-sources/0.1.0', 'entry_filename': 'main.py',
                    'files': [{'filename': name, 'source_revision': 'sha256:' + hashlib.sha256(data).hexdigest(),
                               'size_bytes': len(data)} for name, data in sorted(files.items())]}
    else:
        raise ValueError('Unsupported fixture route')
    for name, data in files.items():
        (directory / name).write_bytes(data)
    manifest_path = directory / 'source.json'
    manifest_path.write_bytes(json_bytes(manifest))
    return manifest_path


def qualification_sets():
    return json.loads((ROOT / 'docs/engineering/static-tray-mapping-c198/CONTROLS.json').read_text())['fixture_sets']


def write_qualification_sources(directory):
    root = Path(directory)
    for case, values in qualification_sets().items():
        for route in ('ontokin', 'direct-python'):
            write_sources(root / case / route, route, values)


if __name__ == '__main__':
    import sys
    write_qualification_sources(sys.argv[1])
