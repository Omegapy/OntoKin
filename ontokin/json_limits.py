"""Preflight JSON by encoded bytes and logical entries before materializing it.

Repeated immutable values count on every occurrence. The walk retains only an
iterator per nesting level and rejects cycles; it never expands shared graphs.
Only exact built-in containers are accepted, matching the scalar type checks.
Custom containers can expose different values to preflight and serialization.
"""
from __future__ import annotations

import json
import math

MAX_JSON_BYTES = 4 * 1024 * 1024
MAX_JSON_ENTRIES = 100000
MAX_JSON_DEPTH = 128


class JSONLimitError(ValueError):
    def __init__(self, name, limit, consumed):
        super().__init__(f"JSON {name} exceeds {limit}.")
        self.details = {"budget": name, "limit": limit, "consumed": consumed}


def measure_json(value, *, max_bytes=MAX_JSON_BYTES, max_entries=MAX_JSON_ENTRIES,
                 max_depth=MAX_JSON_DEPTH, check=None):
    """Count the exact compact ensure_ascii=False JSON encoding without building it."""
    size = entries = ticks = 0
    active = set()
    stack = [(iter((value,)), None, 0)]

    def add(n):
        nonlocal size
        size += n
        if size > max_bytes:
            raise JSONLimitError("encoded_json_bytes", max_bytes, size)

    def string_size(text):
        add(2)
        for i, char in enumerate(text):
            n = ord(char)
            if 0xD800 <= n <= 0xDFFF:
                raise ValueError("JSON strings must contain Unicode scalar values.")
            add(2 if char in '\\"\b\f\n\r\t' else 6 if n < 32 else
                1 if n < 0x80 else 2 if n < 0x800 else 3 if n < 0x10000 else 4)
            if check is not None and i % 1024 == 0:
                check()

    while stack:
        iterator, container, depth = stack[-1]
        try:
            item = next(iterator)
        except StopIteration:
            stack.pop()
            if container is not None:
                active.remove(container)
            continue
        entries += 1
        if entries > max_entries:
            raise JSONLimitError("logical_json_entries", max_entries, entries)
        ticks += 1
        if check is not None and ticks % 128 == 0:
            check()
        if item is None:
            add(4)
        elif type(item) is bool:
            add(4 if item else 5)
        elif type(item) is str:
            string_size(item)
        elif type(item) is int:
            # Very large Python integers cannot be emitted by the bounded wire.
            if item.bit_length() > 14000:
                raise ValueError("JSON integer exceeds the bounded numeric encoding.")
            add(len(str(item)))
        elif type(item) is float:
            if not math.isfinite(item):
                raise ValueError("JSON numbers must be finite.")
            add(len(json.dumps(item, allow_nan=False)))
        elif type(item) is dict or type(item) is list or type(item) is tuple:
            if id(item) in active:
                raise ValueError("JSON cannot encode cyclic values.")
            if depth >= max_depth:
                raise JSONLimitError("json_depth", max_depth, depth + 1)
            add(2 + max(0, len(item) - 1))
            if type(item) is dict:
                for key in item:
                    if type(key) is not str:
                        raise ValueError("JSON object keys must be strings.")
                    string_size(key)
                    add(1)
                iterator = iter(item.values())
            else:
                iterator = iter(item)
            active.add(id(item))
            stack.append((iterator, id(item), depth + 1))
        else:
            raise ValueError(f"Unsupported JSON value type: {type(item).__name__}.")
    return {"bytes": size, "entries": entries}


def bounded_dumps(value, **limits):
    measure_json(value, **limits)
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False)
