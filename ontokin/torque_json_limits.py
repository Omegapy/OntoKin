"""Equivalent publication JSON preflight for explicit Agent/0.22.

The ordinary JSON walk and every callback retain their original order. Only
safe ASCII tails between callbacks use a bounded native scan. Earlier profiles
continue to call json_limits.measure_json directly.
"""
from __future__ import annotations

import json
import math
import re

from .json_limits import JSONLimitError, MAX_JSON_BYTES, MAX_JSON_DEPTH, MAX_JSON_ENTRIES

_ASCII_ESCAPES = re.compile(r'[\x00-\x1f"\\]')


def measure_response_json(value, *, max_bytes=MAX_JSON_BYTES, max_entries=MAX_JSON_ENTRIES,
                          max_depth=MAX_JSON_DEPTH, check=None):
    """Keep the original no-numeric-work JSON path with bounded ASCII tails."""
    size = entries = ticks = 0
    active = set()
    stack = [(iter((value,)), None, 0)]

    def add(n):
        nonlocal size
        size += n
        if size > max_bytes:
            raise JSONLimitError("encoded_json_bytes", max_bytes, size)

    def character(char):
        n = ord(char)
        if 0xD800 <= n <= 0xDFFF:
            raise ValueError("JSON strings must contain Unicode scalar values.")
        add(2 if char in '\\"\b\f\n\r\t' else 6 if n < 32 else
            1 if n < 0x80 else 2 if n < 0x800 else 3 if n < 0x10000 else 4)

    def string_size(text):
        add(2)
        for start in range(0, len(text), 1024):
            # Exactly the original after-character-0/1024/... callback, before
            # examining the following immutable tail or any later container.
            character(text[start])
            if check is not None:
                check()
            tail = text[start + 1:start + 1024]
            # The slice is at most 1023 native characters. A safe ASCII tail
            # adds one byte per character and has no intervening callbacks.
            # If it could exceed the byte cap, retain the original per-char
            # path so the first failure's exact consumed count is unchanged.
            if len(tail) <= max_bytes - size and tail.isascii() and _ASCII_ESCAPES.search(tail) is None:
                add(len(tail))
            else:
                for char in tail:
                    character(char)

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
                for name in item:
                    if type(name) is not str:
                        raise ValueError("JSON object keys must be strings.")
                    string_size(name)
                    add(1)
                iterator = iter(item.values())
            else:
                iterator = iter(item)
            active.add(id(item))
            stack.append((iterator, id(item), depth + 1))
        else:
            raise ValueError(f"Unsupported JSON value type: {type(item).__name__}.")
    return {"bytes": size, "entries": entries}
