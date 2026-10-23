"""Preflight JSON by encoded bytes and logical entries before materializing it.

Repeated immutable values count on every occurrence. The walk retains an
iterator and at most 64 short string references per nesting level and rejects
cycles; it never expands shared graphs. Only exact built-in containers are
accepted, matching the scalar type checks. Custom containers can expose
different values to preflight and serialization.
"""
from __future__ import annotations

import json
import math
import re

MAX_JSON_BYTES = 4 * 1024 * 1024
MAX_JSON_ENTRIES = 100000
MAX_JSON_DEPTH = 128
_ASCII_ESCAPES = re.compile(r'[\x00-\x1f"\\]')


def _literal_text_size(pending):
    """Size one bounded block whose ASCII characters need no JSON escaping.

    The caller retains at most 64 exact strings of at most 128 code points.
    Concatenation allocates at most 8,192 characters. ASCII without a control,
    quote or backslash contributes exactly its length plus two quotes per
    occurrence. Every other block keeps the ordinary Unicode/escape proof.
    """
    text = "".join(pending)
    if text.isascii() and _ASCII_ESCAPES.search(text) is None:
        return len(text) + 2 * len(pending)
    return None


class JSONLimitError(ValueError):
    def __init__(self, name, limit, consumed):
        super().__init__(f"JSON {name} exceeds {limit}.")
        self.details = {"budget": name, "limit": limit, "consumed": consumed}


def measure_json(value, *, max_bytes=MAX_JSON_BYTES, max_entries=MAX_JSON_ENTRIES,
                 max_depth=MAX_JSON_DEPTH, check=None, work=None):
    """Count the exact compact ensure_ascii=False JSON encoding without building it."""
    size = entries = ticks = 0
    active = set()
    stack = [(iter((value,)), None, 0, [])]
    text_reuse = (work is not None and hasattr(work, "lookup") and hasattr(work, "remember"))

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

    def flush_text(pending):
        # A repeated certificate includes short field names, rational clock
        # strings and carrier identities. Reuse their Unicode/escape scans as
        # one bounded immutable sequence, not a trusted container or its values.
        # Every string was exact-type/length checked before entering this list;
        # every logical value, number, container/depth and cycle still takes the
        # ordinary walk below. All cache bookkeeping stays on the same work.
        cacheable = text_reuse and len(pending) >= 5
        if cacheable:
            work.charge("json_text_batch_domain")
            literal_size = _literal_text_size(pending)
            if literal_size is not None:
                # Admit these actual current string bytes directly. Keeping a
                # cache entry for their length would cost more bookkeeping and
                # displace numeric work used by the same request. The bounded
                # native scan remains bracketed by the original work context.
                work.charge("json_text_literal_return")
                add(literal_size)
                pending.clear()
                return
            key = ("bounded_json_text_batch_v1", tuple(pending))
            cached = work.lookup(key)
            if cached is not None:
                add(cached)
                pending.clear()
                return
        before = size
        if cacheable:
            # This exact built-in list contains at most 64 exact strings, each
            # at most 128 code points. The native JSON encoder performs the
            # escaping/Unicode work for that bounded block once. Its largest
            # compact UTF-8 result is 49,345 bytes (all six-byte escapes).
            # Count the quoted strings, removing only the array punctuation.
            # Invalid Unicode still fails UTF-8 encoding; caller cancellation
            # and the original request budget bracket the native operation.
            work.charge("json_text_block_encode")
            encoded = json.dumps(pending, ensure_ascii=False, allow_nan=False,
                                 separators=(",", ":")).encode("utf-8")
            work.charge("json_text_block_encode_return")
            add(len(encoded) - 2 - (len(pending) - 1))
        else:
            for text in pending:
                string_size(text)
        if cacheable:
            work.remember(key, size - before)
        pending.clear()

    def text_size(text, pending):
        if text_reuse and len(text) <= 128:
            pending.append(text)
            if len(pending) == 64:
                flush_text(pending)
        else:
            flush_text(pending)
            string_size(text)

    while stack:
        iterator, container, depth, pending = stack[-1]
        try:
            item = next(iterator)
        except StopIteration:
            stack.pop()
            if container is not None:
                active.remove(container)
            if stack:
                parent_text = stack[-1][3]
                if len(parent_text) + len(pending) > 64:
                    flush_text(parent_text)
                parent_text.extend(pending)
                if len(parent_text) == 64:
                    flush_text(parent_text)
            else:
                flush_text(pending)
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
            text_size(item, pending)
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
            child_text = []
            if type(item) is dict:
                for name in item:
                    if type(name) is not str:
                        raise ValueError("JSON object keys must be strings.")
                    text_size(name, child_text)
                    add(1)
                iterator = iter(item.values())
            else:
                iterator = iter(item)
            active.add(id(item))
            stack.append((iterator, id(item), depth + 1, child_text))
        else:
            raise ValueError(f"Unsupported JSON value type: {type(item).__name__}.")
    return {"bytes": size, "entries": entries}


def bounded_dumps(value, **limits):
    measure_json(value, **limits)
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False)
