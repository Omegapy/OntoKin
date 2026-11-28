"""Deliberate GLB mutations for C272's controls; standard library only, no product import."""
from __future__ import annotations

import json
import struct

JSON_CHUNK, BIN_CHUNK = 0x4E4F534A, 0x004E4942


def split(raw: bytes) -> tuple[dict, bytes]:
    magic, version, length = struct.unpack_from("<III", raw)
    assert magic == 0x46546C67 and version == 2 and length == len(raw)
    size, kind = struct.unpack_from("<II", raw, 12)
    assert kind == JSON_CHUNK
    document = json.loads(raw[20:20 + size])
    offset = 20 + size
    bsize, bkind = struct.unpack_from("<II", raw, offset)
    assert bkind == BIN_CHUNK
    return document, raw[offset + 8: offset + 8 + bsize]


def join(document: dict, binary: bytes) -> bytes:
    text = json.dumps(document, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    text += b" " * (-len(text) % 4)
    binary += b"\0" * (-len(binary) % 4)
    total = 12 + 8 + len(text) + 8 + len(binary)
    return (struct.pack("<III", 0x46546C67, 2, total) + struct.pack("<II", len(text), JSON_CHUNK) + text
            + struct.pack("<II", len(binary), BIN_CHUNK) + binary)


def edit_json(raw: bytes, change) -> bytes:
    document, binary = split(raw)
    change(document)
    return join(document, binary)


def node_index(document: dict, path: str) -> int:
    return next(i for i, n in enumerate(document["nodes"]) if n["extras"]["ontokin"]["path"] == path)


def accessor_offset(document: dict, accessor: int) -> tuple[int, int]:
    a = document["accessors"][accessor]
    view = document["bufferViews"][a["bufferView"]]
    return view.get("byteOffset", 0) + a.get("byteOffset", 0), a["count"]


def edit_floats(raw: bytes, accessor: int, element: int, values, width: int) -> bytes:
    """Overwrite one element of a tightly packed binary32 accessor."""
    document, binary = split(raw)
    start, count = accessor_offset(document, accessor)
    assert 0 <= element < count
    data = bytearray(binary)
    struct.pack_into("<" + "f" * width, data, start + element * 4 * width, *values)
    return join(document, bytes(data))


def channel(document: dict, node: int, path: str) -> dict:
    animation = document["animations"][0]
    for c in animation["channels"]:
        if c["target"] == {"node": node, "path": path}:
            return animation["samplers"][c["sampler"]]
    raise KeyError((node, path))


def read_floats(raw: bytes, accessor: int, element: int, width: int) -> list[float]:
    document, binary = split(raw)
    start, _ = accessor_offset(document, accessor)
    return list(struct.unpack_from("<" + "f" * width, binary, start + element * 4 * width))
