from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image


def render_tileset(raw: bytes, tile_w: int, tile_h: int, *, cols: int = 64, scale: int = 1, gap: int = 1) -> Image.Image:
    bytes_per_row = (tile_w + 7) // 8
    tile_bytes = bytes_per_row * tile_h
    n = len(raw) // tile_bytes
    rows = (n + cols - 1) // cols
    cell_w = tile_w + gap
    cell_h = tile_h + gap
    img = np.zeros((rows * cell_h, cols * cell_w), dtype=np.uint8)
    for i in range(n):
        chunk = raw[i * tile_bytes:(i + 1) * tile_bytes]
        bits = np.unpackbits(np.frombuffer(chunk, dtype=np.uint8)).reshape(tile_h, bytes_per_row * 8)
        glyph = bits[:tile_h, :tile_w]
        r, c = divmod(i, cols)
        img[r * cell_h:r * cell_h + tile_h, c * cell_w:c * cell_w + tile_w] = glyph * 255
    pil = Image.fromarray(img, 'L')
    if scale != 1:
        pil = pil.resize((img.shape[1] * scale, img.shape[0] * scale), Image.NEAREST)
    return pil


def render_fonts(raw_dir: str | Path, out_dir: str | Path) -> Path:
    raw_dir = Path(raw_dir)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    p1 = (raw_dir / '1.pat').read_bytes()
    p2 = (raw_dir / '2.pat').read_bytes()
    render_tileset(p2[:256 * 32], 16, 16, cols=16, scale=3).save(out / '2pat_first256.png')
    render_tileset(p2, 16, 16, cols=80, scale=1).save(out / '2pat_atlas.png')
    raw_256_1 = p1[:256 * 24]
    render_tileset(raw_256_1, 16, 12, cols=16, scale=3).save(out / '1pat_first256_16x12.png')
    render_tileset(raw_256_1, 12, 16, cols=16, scale=3).save(out / '1pat_first256_12x16.png')
    return out
