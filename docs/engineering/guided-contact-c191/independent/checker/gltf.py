"""GLB decoder adapted from C186 neutral_glb.py for the C187 rigid translation profile."""
import json
import struct
from functools import cache
from pathlib import Path

import numpy as np


class Unqualified(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise Unqualified(reason)


def at(items, index):
    require(type(index) is int and 0 <= index < len(items), "invalid glTF index")
    return items[index]


def finite(values, shape=None):
    a = np.asarray(values, dtype=np.float64)
    require((shape is None or a.shape == shape) and np.isfinite(a).all(), "invalid numeric data")
    return a


def normalize_quats(q):
    norms = np.linalg.norm(q, axis=-1, keepdims=True)
    require((np.abs(norms - 1) < .0001).all(), "quaternion is not a unit rotation")
    return q / norms


def quaternion_matrix(q):
    x, y, z, w = np.moveaxis(q, -1, 0)
    r = np.stack([1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w),
                  2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w),
                  2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)], axis=-1)
    return r.reshape(q.shape[:-1] + (3, 3))


def slerp(left, right, u):
    dot = np.sum(left * right, axis=1, keepdims=True)
    right = np.where(dot < 0, -right, right)
    orth = right - np.abs(dot) * left
    length = np.linalg.norm(orth, axis=1, keepdims=True)
    # atan2 retains the small rotations that occur in densely recorded clips.
    angle = np.arctan2(length, np.abs(dot))
    direction = np.divide(orth, length, out=np.zeros_like(orth), where=length > 0)
    return np.cos(u * angle) * left + np.sin(u * angle) * direction


class Scene:
    def __init__(self, path, ids):
        raw = Path(path).read_bytes()
        require(len(raw) >= 28 and struct.unpack_from("<4sII", raw) == (b"glTF", 2, len(raw)),
                "invalid GLB header")
        size, tag = struct.unpack_from("<I4s", raw, 12)
        require(tag == b"JSON" and size % 4 == 0 and 28+size <= len(raw), "invalid JSON chunk")
        self.doc = d = json.loads(raw[20:20+size])
        def check_extensions(x):
            if isinstance(x, dict):
                require(not x.get("extensions"), "extension payload outside core glTF profile")
                for k, v in x.items():
                    if k not in ("extras", "extensions"):
                        check_extensions(v)
            elif isinstance(x, list):
                for v in x:
                    check_extensions(v)
        check_extensions(d)
        blob_size, tag = struct.unpack_from("<I4s", raw, 20+size)
        require(tag == b"BIN\0" and blob_size % 4 == 0 and 28+size+blob_size == len(raw), "invalid BIN chunk")
        self.bin = raw[28+size:]
        require(d["asset"]["version"] == "2.0" and not d.get("extensionsRequired"),
                "unsupported required extension or glTF version")
        require(len(d["buffers"]) == 1 and "uri" not in d["buffers"][0]
                and 0 <= blob_size - d["buffers"][0]["byteLength"] <= 3, "expected one embedded buffer")
        require(len(d["scenes"]) == 1, "expected exactly one scene")
        require(not any(d.get(k) for k in ("skins", "images", "textures")),
                "skins and textures outside solid rigid profile")
        self.nodes = d["nodes"]
        roots = at(d["scenes"], d.get("scene", 0))["nodes"]
        self.parent, self.order, self.parts, self.tracks = {}, [], {}, {}

        def visit(i, parent):
            n = at(self.nodes, i)
            require(i not in self.parent, "cycle or shared child in scene")
            self.parent[i] = parent
            self.order.append(i)
            require("skin" not in n and "weights" not in n and not n.get("extensions"),
                    "unsupported skin, morph or node extension")
            if "mesh" in n:
                mesh = at(d["meshes"], n["mesh"])
                name = n.get("name")
                require(name in ids and mesh.get("name") == name,
                        f"mesh node and mesh must share the specified ID: {name!r} / {mesh.get('name')!r}")
                require(name not in self.parts, "part ID occurs on multiple mesh nodes")
                self.parts[name] = (i, *self.geometry(mesh))
            for child in n.get("children", []):
                visit(child, i)

        for i in roots:
            visit(i, None)
        require(set(self.parts) == ids, "missing semantic part")
        require(len(self.parent) == len(self.nodes), "unreachable node outside the default scene")
        for name in ids:
            require(sum(n.get("name") == name for n in self.nodes) == 1,
                    f"duplicate stable node ID: {name}")
        require(len(d["meshes"]) == len(ids), "unreferenced or extra mesh")
        for name in ids:
            require(sum(m.get("name") == name for m in d["meshes"]) == 1,
                    f"duplicate stable mesh ID: {name}")
        require(len(d["animations"]) == 1, "expected exactly one animation")
        anim = d["animations"][0]
        times = []
        for chan in anim["channels"]:
            i, path = chan["target"]["node"], chan["target"]["path"]
            require(i in self.parent and path in ("rotation", "translation", "scale")
                    and "matrix" not in self.nodes[i] and (i, path) not in self.tracks,
                    "unsupported or duplicate animation target")
            s = at(anim["samplers"], chan["sampler"])
            require(s.get("interpolation", "LINEAR") == "LINEAR", "unsupported interpolation")
            t = self.access(s["input"], "SCALAR", (5126,))[:, 0]
            require(len(t) and (np.diff(t) > 0).all() and t[0] >= 0 and t[-1] <= 2,
                    "invalid time range or key order")
            v = self.access(s["output"], "VEC4" if path == "rotation" else "VEC3", (5126,))
            require(len(v) == len(t), "inconsistent animation key counts")
            if path == "rotation":
                v = normalize_quats(v)
                # q and -q describe the same rotation and slerp takes the short arc.
                same = np.all(v == v[0], axis=1) | np.all(v == -v[0], axis=1)
                require(same.all(), "time-varying rotation outside translation-only profile")
                v[:] = v[0]
            if path == "scale":
                require((v == v[0]).all(), "time-varying scale is outside the rigid profile")
            self.tracks[i, path] = t, v
            times.extend(t)
        require(times and min(times) == 0 and max(times) == 2, "clip does not span [0,2] seconds")
        self.knots = np.unique(times)

    @cache
    def access(self, i, kind, components):
        a = at(self.doc["accessors"], i)
        require(a["type"] == kind and a["componentType"] in components and "sparse" not in a
                and not a.get("normalized"), "unsupported accessor")
        dtype = np.dtype({5121: "u1", 5123: "<u2", 5125: "<u4", 5126: "<f4"}[a["componentType"]])
        count, width = a["count"], {"SCALAR": 1, "VEC3": 3, "VEC4": 4}[kind]
        view = at(self.doc["bufferViews"], a["bufferView"])
        start, offset = view.get("byteOffset", 0), a.get("byteOffset", 0)
        stride = view.get("byteStride", width*dtype.itemsize)
        require(type(count) is int and count > 0 and view["buffer"] == 0 and
                start >= 0 and offset >= 0 and stride >= width*dtype.itemsize and
                offset + (count-1)*stride + width*dtype.itemsize <= view["byteLength"] and
                start + view["byteLength"] <= self.doc["buffers"][0]["byteLength"], "out-of-bounds accessor")
        arr = np.ndarray((count, width), dtype, self.bin, start+offset, (stride, dtype.itemsize))
        require(np.isfinite(arr).all(), "non-finite accessor")
        return arr.astype(np.float64 if dtype.kind == "f" else np.int64)

    def geometry(self, mesh):
        triangles, colors = [], []
        require(not mesh.get("weights") and not mesh.get("extensions"), "morphed or extended mesh")
        for p in mesh["primitives"]:
            require(p.get("mode", 4) == 4 and not p.get("targets") and not p.get("extensions")
                    and not any(k.startswith("COLOR_") for k in p["attributes"]), "unsupported triangle or color profile")
            pos = self.access(p["attributes"]["POSITION"], "VEC3", (5126,))
            ix = (self.access(p["indices"], "SCALAR", (5121, 5123, 5125))[:, 0]
                  if "indices" in p else np.arange(len(pos)))
            require(len(ix) > 0 and len(ix) % 3 == 0 and ix.max() < len(pos), "invalid triangle indices")
            triangles.append(pos[ix].reshape(-1, 3, 3))
            m = at(self.doc["materials"], p["material"])
            pbr = m.get("pbrMetallicRoughness", {})
            rgb = finite(pbr.get("baseColorFactor", [1]*4), (4,))
            require("baseColorTexture" not in pbr and np.all((rgb >= 0) & (rgb <= 1)) and not m.get("extensions") and
                    m.get("alphaMode", "OPAQUE") == "OPAQUE" and rgb[3] == 1,
                    "unsupported non-solid material")
            colors.append(rgb[:3])
        require(bool(triangles), "empty visible mesh")
        return np.concatenate(triangles), np.array(colors)

    def track(self, i, path, times):
        if (i, path) not in self.tracks:
            default = {"rotation": [0,0,0,1], "translation": [0,0,0], "scale": [1,1,1]}[path]
            v = finite(self.nodes[i].get(path, default), (len(default),))
            if path == "rotation":
                v = normalize_quats(v)
            return np.broadcast_to(v, (len(times), len(v)))
        t, v = self.tracks[i, path]
        if len(t) == 1:
            return np.broadcast_to(v[0], (len(times), v.shape[1]))
        lo = np.clip(np.searchsorted(t, times, side="right")-1, 0, len(t)-2)
        u = np.clip((times-t[lo]) / (t[lo+1]-t[lo]), 0, 1)[:, None]
        if path == "rotation":
            return slerp(v[lo], v[lo+1], u)
        return (1-u) * v[lo] + u * v[lo+1]

    def transforms(self, times):
        world, local = {}, {}
        for i in self.order:
            n = self.nodes[i]
            if "matrix" in n:
                require(not any(k in n for k in ("rotation", "scale", "translation")), "matrix and TRS mixed")
                mat = finite(n["matrix"], (16,)).reshape(4, 4).T
                require(np.array_equal(mat[3], [0, 0, 0, 1]), "non-affine node matrix")
                m = np.broadcast_to(mat, (len(times), 4, 4))
            else:
                m = np.zeros((len(times), 4, 4))
                m[:, 3, 3] = 1
                m[:, :3, 3] = self.track(i, "translation", times)
                m[:, :3, :3] = quaternion_matrix(self.track(i, "rotation", times)) * self.track(i, "scale", times)[:, None, :]
            parent = self.parent[i]
            local[i] = m
            world[i] = world[parent] @ m if parent is not None else m
        return world, local
