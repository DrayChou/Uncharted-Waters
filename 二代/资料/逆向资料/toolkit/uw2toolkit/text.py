from __future__ import annotations

import struct
from pathlib import Path


def load_charmap(path: str | Path) -> dict[int, bytes]:
    raw = Path(path).read_bytes()
    idx2gbk: dict[int, bytes] = {}
    for ln in raw.split(b"\r\n"):
        if b"\t" not in ln:
            continue
        a, b = ln.split(b"\t", 1)
        try:
            idx = int(b.decode("ascii"), 16)
        except ValueError:
            continue
        idx2gbk[idx] = a
    return idx2gbk


def decode_indexed_string(data: bytes, charmap: dict[int, bytes]) -> str:
    out: list[str] = []
    i = 0
    while i < len(data):
        if data[i] == 0:
            break
        if i + 1 < len(data):
            code = (data[i] << 8) | data[i + 1]
            gbk = charmap.get(code)
            if gbk is not None:
                try:
                    out.append(gbk.decode("gbk"))
                    i += 2
                    continue
                except UnicodeDecodeError:
                    pass
        c = data[i]
        if 32 <= c < 127:
            out.append(chr(c))
        elif c == 0x0A:
            out.append("\\n")
        else:
            out.append(f"<{c:02x}>")
        i += 1
    return "".join(out)


def parse_offsets(data: bytes, width: int) -> list[int]:
    first = struct.unpack(">H" if width == 2 else ">I", data[:width])[0]
    n = first // width
    fmt = ">H" if width == 2 else ">I"
    offsets = [struct.unpack_from(fmt, data, i * width)[0] for i in range(n)]
    offsets.append(len(data))
    return offsets


def decode_offset_file(path: str | Path, *, charmap_path: str | Path, width: int | None = None) -> list[str]:
    file_path = Path(path)
    data = file_path.read_bytes()
    charmap = load_charmap(charmap_path)
    if width is None:
        width = 2 if file_path.name.lower().startswith("message") else 4
    offsets = parse_offsets(data, width)
    return [decode_indexed_string(data[offsets[i]:offsets[i + 1]], charmap) for i in range(len(offsets) - 1)]
