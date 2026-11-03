#!/usr/bin/env python3
"""Losslessly pack exact JSON-line bytes by transposing their raw lexemes.

This is storage encoding, not JSON normalization. Numbers, quoted strings,
escapes, punctuation and whitespace are retained exactly as received. The
unpacker joins those original lexemes and verifies the complete raw SHA-256.
No source, request, response, clock, or diagnostic field is removed.
"""
import argparse
import gzip
import hashlib
import json
import lzma
from pathlib import Path
import re

SCHEMA = "ontokin.lossless-jsonl-lexemes/1"
MAX_LINE = 8 * 1024 * 1024
MAX_PACKET = 64 * 1024 * 1024
MAX_RAW_PACKET = 4 * 1024 * 1024
MAX_ROWS = 1024
MAX_STREAM = 64 * 1024 * 1024 * 1024
LEXEME = re.compile(r'"(?:[^"\\]|\\.)*"|-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?|true|false|null|[{}\[\],:]|\s+')


def identity(path):
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
            size += len(block)
    return {"bytes": size, "sha256": digest.hexdigest()}


def emit(stream, record):
    raw = (json.dumps(record, ensure_ascii=False, allow_nan=False, separators=(",", ":")) + "\n").encode("utf-8")
    if len(raw) > MAX_PACKET:
        raise ValueError("Lossless record packet exceeds its fixed byte bound.")
    stream.write(raw)


def pack(source, destination, manifest):
    if destination.exists() or manifest.exists():
        raise FileExistsError("Fresh packed output and manifest are required.")
    before = identity(source)
    digest = hashlib.sha256()
    raw_bytes = records = packets = 0
    rows, width, raw_pending = [], None, 0
    opener = gzip.open if source.suffix == ".gz" else open
    with opener(source, "rb") as incoming, lzma.open(destination, "xb", preset=6) as outgoing:
        emit(outgoing, {"schema_version": SCHEMA, "max_rows": MAX_ROWS,
                        "max_line_bytes": MAX_LINE, "max_packet_bytes": MAX_PACKET})

        def flush():
            nonlocal rows, packets, raw_pending
            if not rows:
                return
            columns = []
            for column in zip(*rows):
                columns.append(column[0] if all(value == column[0] for value in column) else list(column))
            emit(outgoing, {"rows": len(rows), "columns": columns})
            packets += 1
            rows, raw_pending = [], 0

        while raw := incoming.readline(MAX_LINE + 1):
            if len(raw) > MAX_LINE or raw_bytes + len(raw) > MAX_STREAM:
                raise ValueError("Raw record stream exceeds its fixed byte bound.")
            text = raw.decode("utf-8")
            tokens = LEXEME.findall(text)
            if "".join(tokens) != text:
                raise ValueError("A raw line contains bytes outside the lossless JSON lexeme grammar.")
            if rows and (len(tokens) != width or len(rows) == MAX_ROWS
                         or raw_pending + len(raw) > MAX_RAW_PACKET):
                flush()
            width = len(tokens)
            rows.append(tokens)
            raw_pending += len(raw)
            digest.update(raw)
            raw_bytes += len(raw)
            records += 1
            if records % 100000 == 0:
                print(json.dumps({"records_packed": records, "raw_bytes": raw_bytes}), flush=True)
        flush()
        raw_identity = {"bytes": raw_bytes, "records": records, "sha256": digest.hexdigest()}
        emit(outgoing, {"end": raw_identity})
    if identity(source) != before:
        raise ValueError("Original transcript changed while it was being packed.")
    result = {"schema_version": SCHEMA, "status": "packed_pending_exact_decode",
              "input": {"name": source.name, **before, "gzip": source.suffix == ".gz"},
              "packed": {"name": destination.name, **identity(destination)},
              "raw": raw_identity, "packets": packets,
              "scope": "Exact decompressed original transcript bytes; original gzip container encoding is separately identified, not claimed to be recreated."}
    with manifest.open("x", encoding="utf-8") as output:
        json.dump(result, output, indent=2)
        output.write("\n")
    print(json.dumps(result), flush=True)


def strict_json(raw):
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise ValueError("Duplicate packed record key.")
            value[key] = item
        return value
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError("Nonfinite packed number.")))


def unpack(source, destination, manifest, report):
    if destination.exists() or report.exists():
        raise FileExistsError("Fresh unpacked output and report are required.")
    if manifest.stat().st_size > 16384:
        raise ValueError("Packed manifest is too large.")
    expected = strict_json(manifest.read_bytes())
    before = identity(source)
    if expected.get("schema_version") != SCHEMA or any(before[k] != expected["packed"][k] for k in before):
        raise ValueError("Packed transcript identity differs from its manifest.")
    digest = hashlib.sha256()
    raw_bytes = records = packets = 0
    footer = None
    with lzma.open(source, "rb") as incoming, destination.open("xb") as outgoing:
        header = strict_json(incoming.readline(16385))
        if header != {"schema_version": SCHEMA, "max_rows": MAX_ROWS,
                      "max_line_bytes": MAX_LINE, "max_packet_bytes": MAX_PACKET}:
            raise ValueError("Unknown lossless transcript format or allocation.")
        while encoded := incoming.readline(MAX_PACKET + 1):
            if len(encoded) > MAX_PACKET or footer is not None:
                raise ValueError("Oversized packet or data following the final receipt.")
            packet = strict_json(encoded)
            if type(packet) is not dict:
                raise ValueError("Packed record is not an object.")
            if set(packet) == {"end"}:
                footer = packet["end"]
                continue
            if set(packet) != {"rows", "columns"}:
                raise ValueError("Packed record has unknown fields.")
            count, columns = packet["rows"], packet["columns"]
            if type(count) is not int or not 1 <= count <= MAX_ROWS or type(columns) is not list:
                raise ValueError("Invalid bounded packet shape.")
            for column in columns:
                if not (type(column) is str or type(column) is list and len(column) == count
                        and all(type(value) is str for value in column)):
                    raise ValueError("Invalid raw-lexeme column.")
            for index in range(count):
                line = "".join(column if type(column) is str else column[index] for column in columns)
                raw = line.encode("utf-8")
                if len(raw) > MAX_LINE or raw_bytes + len(raw) > MAX_STREAM:
                    raise ValueError("Restored stream exceeds its fixed byte bound.")
                outgoing.write(raw)
                digest.update(raw)
                raw_bytes += len(raw)
                records += 1
            packets += 1
    actual = {"bytes": raw_bytes, "records": records, "sha256": digest.hexdigest()}
    if actual != footer or actual != expected["raw"] or packets != expected["packets"] or identity(source) != before:
        raise ValueError("The complete restored transcript differs from its original byte identity.")
    result = {"schema_version": SCHEMA, "status": "passed", "packed": before,
              "raw": actual, "packets": packets, "every_original_raw_byte_exact": True,
              "normalization_or_field_removal": False}
    with report.open("x", encoding="utf-8") as output:
        json.dump(result, output, indent=2)
        output.write("\n")
    print(json.dumps(result), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("pack", "unpack"):
        command = subparsers.add_parser(name)
        command.add_argument("--source", type=Path, required=True)
        command.add_argument("--destination", type=Path, required=True)
        command.add_argument("--manifest", type=Path, required=True)
        if name == "unpack":
            command.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "pack":
        pack(args.source, args.destination, args.manifest)
    else:
        unpack(args.source, args.destination, args.manifest, args.report)


if __name__ == "__main__":
    main()
