"""Bounded, metered PNG admission for textured-surfaces-0.1.

Only the deliberately finite C080 subset is accepted.  Decoding establishes
opaque pixel content without retaining a second image copy on the model.  The
caller owns execution authority; callbacks never grant or cache that authority.
"""

from __future__ import annotations

import binascii
from dataclasses import dataclass
import hashlib
import struct
from typing import Callable
import zlib

from .surface import SurfaceError


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_PNG_BYTES = 300_000
MAX_DIMENSION = 256
MAX_PIXEL_BYTES = 262_144
MAX_TOTAL_PIXEL_BYTES = 1_048_576
MAX_IDAT_CHUNKS = 64


@dataclass(frozen=True)
class PngInfo:
    width: int
    height: int
    channels: int
    pixel_sha256: str

    @property
    def decoded_bytes(self) -> int:
        return self.width * self.height * self.channels


def _bad(message: str, **details: object) -> None:
    raise SurfaceError("OKL-E-PNG", message, details=details)


def _paeth(left: int, above: int, upper_left: int) -> int:
    prediction = left + above - upper_left
    a, b, c = (abs(prediction - left), abs(prediction - above),
               abs(prediction - upper_left))
    if a <= b and a <= c:
        return left
    return above if b <= c else upper_left


def validate_png(raw: bytes, *, charge: Callable[[int], None] | None = None,
                 check: Callable[[], None] | None = None) -> PngInfo:
    """Validate one original PNG, charging before every admitted unit of work.

    ``charge(n)`` counts encoded 64-byte blocks, chunks, rows, and reconstructed
    channel bytes.  Adjacent charges may be batched, with cancellation checks
    between bounded blocks.  Errors use ``SurfaceError('OKL-E-PNG', ...)``;
    callback exceptions propagate unchanged so cancellation/resource failures
    cannot be converted into image-validity failures.
    """
    def work(amount: int) -> None:
        if charge is not None:
            charge(amount)

    def checkpoint() -> None:
        if check is not None:
            check()

    checkpoint()
    if not isinstance(raw, bytes):
        _bad("PNG input must be immutable original bytes.")
    if len(raw) > MAX_PNG_BYTES:
        _bad("PNG encoded byte bound exceeded.", limit=MAX_PNG_BYTES,
             consumed=len(raw))
    # The entire encoded byte string will be examined.  Precharge bounded
    # batches before any parser/CRC/decompression work touches those bytes.
    blocks = (len(raw) + 63) // 64
    for start in range(0, blocks, 64):
        work(min(64, blocks - start))
        checkpoint()
    if not raw.startswith(PNG_SIGNATURE):
        _bad("PNG signature is missing or invalid.")

    offset = len(PNG_SIGNATURE)
    width = height = channels = 0
    idats: list[memoryview] = []
    saw_header = saw_end = False
    view = memoryview(raw)
    while offset < len(raw):
        work(1)
        checkpoint()
        if len(raw) - offset < 12:
            _bad("PNG chunk is truncated.", offset=offset)
        length = struct.unpack_from(">I", raw, offset)[0]
        kind = raw[offset + 4:offset + 8]
        end = offset + 8 + length
        if end + 4 > len(raw):
            _bad("PNG chunk length exceeds the original byte string.", offset=offset)
        expected_crc = struct.unpack_from(">I", raw, end)[0]
        if binascii.crc32(view[offset + 4:end]) & 0xffffffff != expected_crc:
            _bad("PNG chunk CRC does not match.", offset=offset)
        data = view[offset + 8:end]
        offset = end + 4
        if not saw_header:
            if kind != b"IHDR" or length != 13:
                _bad("PNG must begin with one 13-byte IHDR chunk.")
            width, height, depth, color, compression, filtering, interlace = struct.unpack(
                ">IIBBBBB", data)
            if not (1 <= width <= MAX_DIMENSION and 1 <= height <= MAX_DIMENSION):
                _bad("PNG dimensions must each be between 1 and 256.",
                     width=width, height=height)
            if (depth != 8 or color not in (2, 6) or compression != 0
                    or filtering != 0 or interlace != 0):
                _bad("PNG requires noninterlaced 8-bit RGB or RGBA with standard compression/filtering.")
            channels = 3 if color == 2 else 4
            if width * height * channels > MAX_PIXEL_BYTES:
                _bad("PNG reconstructed byte bound exceeded.", limit=MAX_PIXEL_BYTES)
            saw_header = True
        elif kind == b"IDAT":
            if len(idats) >= MAX_IDAT_CHUNKS:
                _bad("PNG permits at most 64 contiguous IDAT chunks.", limit=MAX_IDAT_CHUNKS)
            idats.append(data)
        elif kind == b"IEND":
            if length != 0 or not idats:
                _bad("PNG requires one or more IDAT chunks followed by empty IEND.")
            if offset != len(raw):
                _bad("PNG has trailing bytes or chunks after IEND.")
            saw_end = True
            break
        else:
            _bad("PNG permits only one IHDR, contiguous IDAT chunks, and final IEND.",
                 chunk_type=kind.hex())
    if not saw_header or not saw_end:
        _bad("PNG is missing its complete IHDR/IDAT/IEND sequence.")

    row_bytes = width * channels
    expected_length = height * (1 + row_bytes)
    # A decoder call emits at most 4096 bytes, and never more than the exact
    # expected filtered count plus one detection byte across all calls.
    decoder = zlib.decompressobj()
    filtered = bytearray()
    for compressed in idats:
        for start in range(0, len(compressed), 4096):
            pending = compressed[start:start + 4096]
            while len(pending):
                checkpoint()
                if decoder.eof:
                    _bad("PNG contains trailing compressed bytes or another zlib stream.")
                allowance = min(4096, expected_length + 1 - len(filtered))
                try:
                    output = decoder.decompress(pending, allowance)
                except zlib.error as exc:
                    raise SurfaceError("OKL-E-PNG", "PNG IDAT is not one supported zlib stream.") from exc
                filtered.extend(output)
                if len(filtered) > expected_length:
                    _bad("PNG decompression exceeds its exact filtered byte count.",
                         expected=expected_length)
                if decoder.unused_data:
                    _bad("PNG contains trailing compressed bytes or another zlib stream.")
                tail = decoder.unconsumed_tail
                if tail and len(tail) == len(pending) and not output:
                    _bad("PNG decompression made no bounded progress.")
                pending = tail
    checkpoint()
    if not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
        _bad("PNG IDAT must end at exactly one complete zlib stream.")
    if len(filtered) != expected_length:
        _bad("PNG decoded byte count does not match its dimensions.",
             expected=expected_length, actual=len(filtered))

    pixel_digest = hashlib.sha256()
    previous = bytearray(row_bytes)
    for row in range(height):
        work(1)
        checkpoint()
        begin = row * (row_bytes + 1)
        filtering = filtered[begin]
        if filtering > 4:
            _bad("PNG row uses an unsupported filter.", row=row, filter=filtering)
        current = bytearray(row_bytes)
        for index in range(row_bytes):
            if index % 128 == 0:
                work(min(128, row_bytes - index))
                checkpoint()
            left = current[index - channels] if index >= channels else 0
            above = previous[index]
            upper_left = previous[index - channels] if index >= channels else 0
            value = filtered[begin + 1 + index]
            if filtering == 1:
                value += left
            elif filtering == 2:
                value += above
            elif filtering == 3:
                value += (left + above) // 2
            elif filtering == 4:
                value += _paeth(left, above, upper_left)
            current[index] = value & 255
            if channels == 4 and index % 4 == 3 and current[index] != 255:
                _bad("PNG RGBA pixels must all be fully opaque.", row=row,
                     column=index // channels)
        pixel_digest.update(current)
        previous = current
    checkpoint()
    return PngInfo(width, height, channels, "sha256:" + pixel_digest.hexdigest())
