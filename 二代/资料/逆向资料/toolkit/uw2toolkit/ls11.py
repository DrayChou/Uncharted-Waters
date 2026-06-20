from __future__ import annotations

from pathlib import Path
from typing import Iterable

LS11_MAGIC = (b"LS11", b"Ls12", b"LS10")


def bits_from_bytes(data: bytes) -> Iterable[int]:
    for byte in data:
        for i in range(7, -1, -1):
            yield (byte >> i) & 1


def decode_codes(data: bytes) -> list[int]:
    codes: list[int] = []
    bit_iter = iter(bits_from_bytes(data))
    while True:
        mask_len = 0
        while True:
            try:
                bit = next(bit_iter)
            except StopIteration:
                return codes
            mask_len += 1
            if bit == 0:
                break
        factor = 0
        try:
            for _ in range(mask_len):
                factor = (factor << 1) | next(bit_iter)
        except StopIteration:
            return codes
        mask = (1 << mask_len) - 2
        codes.append(mask + factor)


def recover_bytes(codes: list[int], dictionary: bytes) -> bytes:
    out = bytearray()
    delta = 0
    for code in codes:
        if delta > 0:
            length = 3 + code
            for _ in range(length):
                pos = len(out) - delta
                out.append(0 if pos < 0 else out[pos])
            delta = 0
        elif code < 256:
            out.append(dictionary[code])
        else:
            delta = code - 256
    return bytes(out)


def decode_parts(data: bytes) -> list[bytes]:
    if data[:4] not in LS11_MAGIC:
        raise ValueError(f"Bad magic: {data[:4]!r}")
    dictionary = data[16:272]
    pos = 272
    infos: list[tuple[int, int, int]] = []
    while data[pos:pos + 4] != b"\x00\x00\x00\x00":
        compressed_size = int.from_bytes(data[pos:pos + 4], "big")
        uncompressed_size = int.from_bytes(data[pos + 4:pos + 8], "big")
        offset = int.from_bytes(data[pos + 8:pos + 12], "big")
        infos.append((compressed_size, uncompressed_size, offset))
        pos += 12

    out: list[bytes] = []
    for compressed_size, uncompressed_size, offset in infos:
        chunk = data[offset:offset + compressed_size]
        if compressed_size == uncompressed_size:
            out.append(chunk)
        else:
            decoded = recover_bytes(decode_codes(chunk), dictionary)
            out.append(decoded[:uncompressed_size])
    return out


def decode_file(path: str | Path) -> list[bytes]:
    return decode_parts(Path(path).read_bytes())


def write_parts(parts: list[bytes], out_dir: str | Path) -> Path:
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    for i, part in enumerate(parts):
        (out_path / f"part_{i:04d}_{len(part)}bytes.bin").write_bytes(part)
    return out_path
