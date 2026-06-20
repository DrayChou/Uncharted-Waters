from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

COLOR_MAP = {
    0: (0x00, 0x00, 0x00),
    1: (0x00, 0xA0, 0x60),
    2: (0xD0, 0x40, 0x00),
    3: (0xF0, 0xA0, 0x60),
    4: (0x00, 0x40, 0xD0),
    5: (0x00, 0xA0, 0xF0),
    6: (0xD0, 0x60, 0xA0),
    7: (0xF0, 0xE0, 0xD0),
}


def decode_3plane_8color(raw_bytes: bytes, *, width: int, height: int) -> np.ndarray:
    bits = np.unpackbits(np.frombuffer(raw_bytes, dtype=np.uint8))
    pixels = []
    pointer = 0
    while pointer + 24 <= len(bits):
        for j in range(8):
            idx = (int(bits[pointer + j]) << 2) | (int(bits[pointer + j + 8]) << 1) | int(bits[pointer + j + 16])
            pixels.append(COLOR_MAP[idx])
        pointer += 24
    arr = np.array(pixels, dtype=np.uint8)
    if arr.size != width * height * 3:
        raise ValueError(f'Unexpected decoded pixel count for {width}x{height}: {arr.size}')
    return arr.reshape(height, width, 3)


def render_parts(parts_dir: str | Path, out_dir: str | Path, *, size_bytes: int, width: int, height: int, scale: int = 3, cols: int = 16, contact_name: str = 'contact.png') -> Path:
    parts = sorted(Path(parts_dir).glob(f'*_{size_bytes}bytes.bin'))
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    images: list[Image.Image] = []
    for i, p in enumerate(parts):
        arr = decode_3plane_8color(p.read_bytes(), width=width, height=height)
        img = Image.fromarray(arr, 'RGB')
        img.resize((width * scale, height * scale), Image.NEAREST).save(out / f'{i:03d}.png')
        images.append(img)
    if images:
        thumb_w, thumb_h = width * 2, height * 2
        rows = (len(images) + cols - 1) // cols
        sheet = Image.new('RGB', (cols * thumb_w, rows * thumb_h), (20, 20, 30))
        for i, img in enumerate(images):
            sheet.paste(img.resize((thumb_w, thumb_h), Image.NEAREST), ((i % cols) * thumb_w, (i // cols) * thumb_h))
        sheet.save(out.parent / contact_name)
    return out


def render_portraits(parts_dir: str | Path, out_dir: str | Path) -> Path:
    return render_parts(parts_dir, out_dir, size_bytes=1920, width=64, height=80, contact_name='contact_kao.png')


def render_items(parts_dir: str | Path, out_dir: str | Path) -> Path:
    return render_parts(parts_dir, out_dir, size_bytes=864, width=48, height=48, contact_name='contact_items.png')
