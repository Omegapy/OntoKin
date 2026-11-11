from fractions import Fraction
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
