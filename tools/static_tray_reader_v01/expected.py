"""Independent decimal expectations for OK-VAL-STATIC-TRAY-001/0.1.0.

This module is written from the frozen C198 equations and control constants.
It never imports or consumes the producer's canonical geometry or helpers.
"""

from copy import deepcopy
from fractions import Fraction
from itertools import product


PARTS = ("back", "base", "front", "left-wall", "payload", "right-wall")
SIDES = ("left", "right")
DELTA = Fraction("0.000005")
FRAME_DELTA = Fraction("0.000001")
MATERIALS = {
    "tray": {"baseColorFactor": [0.25, 0.5, 0.75, 1.0], "metallicFactor": 0.0,
             "roughnessFactor": 0.75, "alphaMode": "OPAQUE", "doubleSided": False},
    "payload": {"baseColorFactor": [0.75, 0.5, 0.25, 1.0], "metallicFactor": 0.0,
                "roughnessFactor": 0.75, "alphaMode": "OPAQUE", "doubleSided": False},
}


def expected_case(case):
    """Return hand-transcribed C198 control inputs, independent of producer data."""
    left = {"payload_m": ["0.20", "0.06", "0.12"], "clearance_m": "0.005",
            "wall_m": "0.004", "base_m": "0.006", "headroom_m": "0.020",
            "translation_m": ["-0.3", "0", "0"], "rotation_wxyz": [1, 0, 0, 0]}
    right = {**deepcopy(left), "payload_m": ["0.16", "0.04", "0.10"],
             "translation_m": ["0.3", "0", "0"]}
    if case == "Q02":
        left = {"payload_m": ["0.01"] * 3, "clearance_m": "0.001",
                "wall_m": "0.001", "base_m": "0.001", "headroom_m": "0.001",
                "translation_m": [-10, -10, -10], "rotation_wxyz": [1, 0, 0, 0]}
        right = {"payload_m": ["1", "0.5", "1"], "clearance_m": "0.05",
                 "wall_m": "0.025", "base_m": "0.025", "headroom_m": "0.1",
                 "translation_m": [10, 10, 10], "rotation_wxyz": [1, 0, 0, 0]}
    elif case == "Q03":
        left.update(translation_m=["-0.3", "0.2", "0.1"], rotation_wxyz=[0.5] * 4)
        right.update(translation_m=["0.3", "0.1", "-0.2"],
                     rotation_wxyz=[0.5, 0.5, -0.5, 0.5])
    elif case == "Q04":
        left["payload_m"][0] = "0.24"
    elif case == "Q05":
        left["payload_m"][0] = "0.18"
    elif case != "Q01":
        raise ValueError("Unknown frozen qualification fixture " + str(case))
    return {"left": left, "right": right}


def scalar(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ValueError("Expected a finite decimal fixture scalar")
    return Fraction(str(value))


def rotation(wxyz):
    w, x, y, z = map(scalar, wxyz)
    result = ((1 - 2 * (y*y + z*z), 2 * (x*y - z*w), 2 * (x*z + y*w)),
              (2 * (x*y + z*w), 1 - 2 * (x*x + z*z), 2 * (y*z - x*w)),
              (2 * (x*z - y*w), 2 * (y*z + x*w), 1 - 2 * (x*x + y*y)))
    if sum(v*v for v in (w, x, y, z)) != 1:
        raise ValueError("Independent expected quaternion is not unit")
    if any(v not in (-1, 0, 1) for row in result for v in row):
        raise ValueError("Independent expected orientation is not in the exact subset")
    catalog = [(1,0,0,0), (0,1,0,0), (0,0,1,0), (0,0,0,1)]
    catalog += [(Fraction(1,2), *p) for p in product((Fraction(1,2), Fraction(-1,2)), repeat=3)]
    if (w, x, y, z) not in catalog:
        raise ValueError("Expected orientation is outside the canonical catalog")
    return result


def mat_vec(matrix, vector):
    return tuple(sum(a*b for a,b in zip(row, vector)) for row in matrix)


def transpose(matrix):
    return tuple(zip(*matrix))


def root_name(side):
    return "equipment-tray/pair/" + side


def metadata(side, part=None):
    identity = ["equipment-tray", "pair", side]
    if part is None:
        return {"semantic_id": identity, "role": "tray-root",
                "owner_id": ["equipment-tray", "pair"]}
    return {"semantic_id": identity + [part],
            "role": "payload-proxy" if part == "payload" else part,
            "owner_id": identity, "follow_id": identity + ["follow-" + part],
            "follow_parent_id": identity}


def geometry(fixture):
    """Use exact decimal mathematics for independent dimensional expectations."""
    if set(fixture) != set(SIDES):
        raise ValueError("Expected fixture requires exactly left and right")
    result = {}
    for side in SIDES:
        values = fixture[side]
        if set(values) != {"payload_m", "clearance_m", "wall_m", "base_m", "headroom_m",
                           "translation_m", "rotation_wxyz"}:
            raise ValueError("Invalid independent fixture fields")
        px, py, pz = map(scalar, values["payload_m"])
        c, t, b, h = (scalar(values[k]) for k in
                      ("clearance_m", "wall_m", "base_m", "headroom_m"))
        trans = tuple(map(scalar, values["translation_m"]))
        if len(trans) != 3 or any(abs(v) > 10 for v in trans):
            raise ValueError("Independent fixture translation outside domain")
        for v, low, high in ((px,".01","1"),(pz,".01","1"),(py,".01",".5"),
                             (c,".001",".05"),(t,".001",".025"),
                             (b,".001",".025"),(h,".001",".1")):
            if not scalar(low) <= v <= scalar(high):
                raise ValueError("Independent fixture parameter outside domain")
        W, D, H = px+2*c, pz+2*c, py+h
        OX, OZ = W+2*t, D+2*t
        boxes = {
            "base": ((OX,b,OZ), (0,-b/2,0)),
            "front": ((OX,H,t), (0,H/2,(D+t)/2)),
            "back": ((OX,H,t), (0,H/2,-(D+t)/2)),
            "left-wall": ((t,H,D), (-(W+t)/2,H/2,0)),
            "right-wall": ((t,H,D), ((W+t)/2,H/2,0)),
            "payload": ((px,py,pz), (0,py/2,0)),
        }
        result[side] = {"rotation": rotation(values["rotation_wxyz"]),
                        "translation": trans, "boxes": boxes,
                        "cavity": (W,H,D), "clearance": c, "headroom": h}
    return result


def expected_bounds(case):
    """Independent world bounds used only to frame a receiving review image."""
    roots=geometry(expected_case(case) if isinstance(case,str) else case)
    points=[]
    for root in roots.values():
        for size,offset in root["boxes"].values():
            for signs in product((-1,1),repeat=3):
                local=tuple(offset[i]+signs[i]*size[i]/2 for i in range(3))
                points.append(tuple(a+b for a,b in zip(mat_vec(root["rotation"],local),root["translation"])))
    return [[float(min(p[i] for p in points)) for i in range(3)],
            [float(max(p[i] for p in points)) for i in range(3)]]
