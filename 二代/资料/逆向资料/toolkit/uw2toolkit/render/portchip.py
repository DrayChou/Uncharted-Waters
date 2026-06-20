from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

PALETTE_DAY = {
    0: "000000", 1: "717192", 2: "888888", 3: "0082F3", 4: "D34100",
    5: "A26100", 6: "F3A261", 7: "00B261", 8: "0041D3", 9: "0041C3",
    10: "00A2F3", 11: "007161", 12: "888888", 13: "E3B251", 14: "F3E3D3",
    15: "F3E3D3",
}
PALETTE = np.array(
    [tuple(int(PALETTE_DAY[k][i:i + 2], 16) for i in (0, 2, 4)) for k in range(16)],
    dtype=np.uint8,
)
TILE_W = TILE_H = 16
BLOCK_BITS = TILE_W * TILE_H * 4
PIXELS_PER_BLOCK = 256


def decode_part(raw: bytes) -> np.ndarray:
    bits = np.unpackbits(np.frombuffer(raw, dtype=np.uint8))
    n_blocks = len(bits) // BLOCK_BITS
    tiles = np.zeros((n_blocks, TILE_H, TILE_W, 3), dtype=np.uint8)
    for b in range(n_blocks):
        block = bits[b * BLOCK_BITS:(b + 1) * BLOCK_BITS]
        for i in range(PIXELS_PER_BLOCK):
            p = ((int(block[i]) << 3)
                 | (int(block[i + 256]) << 2)
                 | (int(block[i + 512]) << 1)
                 | int(block[i + 768]))
            y, x = divmod(i, TILE_W)
            tiles[b, y, x] = PALETTE[p]
    return tiles


def load_atlases(parts_dir: str | Path) -> list[np.ndarray]:
    parts = sorted(p for p in Path(parts_dir).glob('*.bin') if p.stat().st_size == 30720)
    return [decode_part(p.read_bytes()) for p in parts]


def save_atlas_sheets(parts_dir: str | Path, out_dir: str | Path, *, scale: int = 3, cols: int = 16) -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    atlases = load_atlases(parts_dir)
    for idx, tiles in enumerate(atlases):
        rows = (len(tiles) + cols - 1) // cols
        sheet = Image.new('RGB', (cols * TILE_W * scale, rows * TILE_H * scale), (40, 40, 60))
        for i, tile in enumerate(tiles):
            r, c = divmod(i, cols)
            tile_img = Image.fromarray(tile, 'RGB').resize((TILE_W * scale, TILE_H * scale), Image.NEAREST)
            sheet.paste(tile_img, (c * TILE_W * scale, r * TILE_H * scale))
        sheet.save(out / f'part{idx}_atlas.png')
    return out
