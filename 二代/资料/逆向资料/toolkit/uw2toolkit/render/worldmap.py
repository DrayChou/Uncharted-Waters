from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

PALETTE_HEX = {
    0: "000000", 1: "717192", 2: "888888", 3: "0082F3", 4: "D34100",
    5: "A26100", 6: "F3A261", 7: "00B261", 8: "0041D3", 9: "0041C3",
    10: "00A2F3", 11: "007161", 12: "888888", 13: "E3B251", 14: "F3E3D3",
    15: "F3E3D3",
}
PALETTE = np.array(
    [tuple(int(PALETTE_HEX[k][i:i + 2], 16) for i in (0, 2, 4)) for k in range(16)],
    dtype=np.uint8,
)
LAND_TILES = set(range(51, 66)) | {73, 81, 89, 97} | set(range(105, 128))
DESERT_TILES = {25, 26, 28, 29, 30, 31, 32, 89, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114}
_TEMPLATES: dict[int, np.ndarray] = {}
_ADJ_CHECK = {1: [1, 2, 8], 2: [8], 3: [6, 7, 8], 4: [2], 5: [6], 6: [2, 3, 4], 7: [4], 8: [4, 5, 6]}
_ADJ_OFFSETS = {
    1: ((-1, -1), {89, 105}), 2: ((0, -1), {89, 105, 106, 108, 110, 111}),
    3: ((1, -1), {89, 110}), 4: ((1, 0), {89, 108, 109, 110, 111, 112}),
    5: ((1, 1), {89, 112}), 6: ((0, 1), {89, 106, 107, 109, 111, 112}),
    7: ((-1, 1), {89, 107}), 8: ((-1, 0), {89, 105, 106, 107, 108, 109}),
}


def extract_regular_tileset(data1_dir: str | Path) -> np.ndarray:
    raw = (Path(data1_dir) / 'part_0011_32768bytes.bin').read_bytes()
    raw = raw[:len(raw) // 2]
    bits = np.unpackbits(np.frombuffer(raw, dtype=np.uint8))
    n = len(bits) // 1024
    tiles = np.zeros((n, 16, 16, 3), dtype=np.uint8)
    for b in range(n):
        block = bits[b * 1024:(b + 1) * 1024]
        for i in range(256):
            p = ((int(block[i]) << 3) | (int(block[i + 256]) << 2) | (int(block[i + 512]) << 1) | int(block[i + 768]))
            y, x = divmod(i, 16)
            tiles[b, y, x] = PALETTE[p]
    return tiles


def extract_large_tileset(data1_dir: str | Path) -> np.ndarray:
    raw = (Path(data1_dir) / 'part_0018_1024bytes.bin').read_bytes()
    out = np.zeros((256, 4), dtype=np.uint8)
    for i in range(16):
        bits = bin(i)[2:].zfill(4)
        out[i] = [0 if c == '0' else 65 for c in bits]
    cursor = 16 * 4
    for i in range(16, 256):
        for j in range(4):
            v = raw[cursor + j]
            out[i, j] = 0 if v > 128 else v
        cursor += 4
    return out


def _template(number: int) -> np.ndarray:
    if number in _TEMPLATES:
        return _TEMPLATES[number].copy()
    t = np.zeros((12, 12), dtype=np.uint8)
    if number == 0:
        t[:, :6] = 15
    elif number == 1:
        t[:, 6:] = 15
    elif number == 2:
        t[:6, :] = 15
    elif number == 3:
        t[6:, :] = 15
    elif number == 4:
        t[:, :] = 15
    _TEMPLATES[number] = t
    return t.copy()


def decode_part(raw: bytes) -> np.ndarray:
    bits = np.unpackbits(np.frombuffer(raw, dtype=np.uint8))
    stream = bits[2700 * 8:]
    blocks = []
    cursor = 0
    for _ in range(1350):
        is_diff = stream[cursor] == 0
        tnum = int(''.join(str(int(b)) for b in stream[cursor + 5:cursor + 8]), 2)
        tile = _template(tnum).flatten()
        cursor += 8
        if is_diff:
            corrections = []
            for i in range(144):
                if stream[cursor] == 1:
                    corrections.append(i)
                cursor += 1
            for c in corrections:
                v = int(''.join(str(int(b)) for b in stream[cursor:cursor + 8]), 2)
                tile[c] = v
                cursor += 8
        blocks.append(tile.reshape(12, 12))
    return np.array(blocks).reshape(45, 30, 12, 12)


def expand_to_regular_grid(blocks: np.ndarray, large_ts: np.ndarray) -> np.ndarray:
    large_grid = blocks.transpose(0, 2, 1, 3).reshape(45 * 12, 30 * 12)
    reg = np.zeros((large_grid.shape[0] * 2, large_grid.shape[1] * 2), dtype=np.uint8)
    for ly in range(large_grid.shape[0]):
        for lx in range(large_grid.shape[1]):
            idx = large_grid[ly, lx]
            tl, tr, bl, br = large_ts[idx]
            reg[ly * 2, lx * 2] = tl
            reg[ly * 2, lx * 2 + 1] = tr
            reg[ly * 2 + 1, lx * 2] = bl
            reg[ly * 2 + 1, lx * 2 + 1] = br
    return reg


def render_thumbnail(grid: np.ndarray, regular_ts: np.ndarray) -> np.ndarray:
    mean_colors = regular_ts.reshape(regular_ts.shape[0], -1, 3).mean(axis=1).astype(np.uint8)
    flat = grid.flatten()
    pixels = mean_colors[np.clip(flat, 0, mean_colors.shape[0] - 1)]
    return pixels.reshape(grid.shape[0], grid.shape[1], 3)


def render_detailed(grid: np.ndarray, regular_ts: np.ndarray, px_per_tile: int = 4) -> np.ndarray:
    n = regular_ts.shape[0]
    small_tiles = np.zeros((n, px_per_tile, px_per_tile, 3), dtype=np.uint8)
    for i in range(n):
        small_tiles[i] = np.array(Image.fromarray(regular_ts[i], 'RGB').resize((px_per_tile, px_per_tile), Image.BILINEAR))
    h, w = grid.shape
    out = np.zeros((h * px_per_tile, w * px_per_tile, 3), dtype=np.uint8)
    flat = np.clip(grid, 0, n - 1)
    for y in range(h):
        for x in range(w):
            out[y * px_per_tile:(y + 1) * px_per_tile, x * px_per_tile:(x + 1) * px_per_tile] = small_tiles[flat[y, x]]
    return out


def fill_deserts(world_map: np.ndarray) -> np.ndarray:
    rows, cols = world_map.shape
    for c in range(cols):
        for r in range(rows):
            if world_map[r, c] == 89:
                if c + 1 < cols and world_map[r, c + 1] == 65:
                    world_map[r, c + 1] = 89
                if r + 1 < rows and world_map[r + 1, c] == 65:
                    world_map[r + 1, c] = 89
    return world_map


def replace_coasts(world_map: np.ndarray, coastal_lut: np.ndarray):
    rows, cols = world_map.shape
    land_mask = np.isin(world_map, list(LAND_TILES))
    desert_mask = np.isin(world_map, list(DESERT_TILES))
    padded = np.zeros((rows + 2, cols + 2), dtype=bool)
    desert_padded = np.zeros((rows + 2, cols + 2), dtype=bool)
    padded[1:-1, 1:-1] = land_mask
    desert_padded[1:-1, 1:-1] = desert_mask
    offs = [(-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0)]
    bits = np.zeros((rows, cols), dtype=np.uint16)
    desert_adj = np.zeros((rows, cols), dtype=bool)
    for i, (dr, dc) in enumerate(offs):
        nb = padded[1 + dr:1 + dr + rows, 1 + dc:1 + dc + cols]
        bits |= nb.astype(np.uint16) << (7 - i)
        dnb = desert_padded[1 + dr:1 + dr + rows, 1 + dc:1 + dc + cols]
        desert_adj |= dnb & nb
    lut_idx = bits | 0x100
    water = world_map == 0
    new_tiles = coastal_lut[lut_idx]
    world_map = np.where(water, new_tiles, world_map)
    coords = np.argwhere(water & desert_adj)
    return world_map, [tuple(c) for c in coords]


def replace_desert_coasts(world_map: np.ndarray, candidates: list[tuple[int, int]]) -> np.ndarray:
    rows, cols = world_map.shape
    for r, c in candidates:
        t = int(world_map[r, c])
        if t not in _ADJ_CHECK:
            continue
        ok = True
        for x in _ADJ_CHECK[t]:
            (dr, dc), allowed = _ADJ_OFFSETS[x]
            nr, nc = r + dr, c + dc
            if not (0 <= nr < rows and 0 <= nc < cols) or int(world_map[nr, nc]) not in allowed:
                ok = False
                break
        if ok and world_map[r, c] != 0:
            world_map[r, c] = world_map[r, c] + 24
    return world_map


def update_frigid_temperate(world_map: np.ndarray) -> np.ndarray:
    rows, _ = world_map.shape
    mask = np.isin(world_map, list(range(1, 9)) + list(range(65, 73)))
    row_idx = np.arange(rows)[:, None]
    frigid_rows = (row_idx < 24) | (row_idx >= rows - 24)
    temperate_rows = ((row_idx < 24 * 14) | (row_idx >= 24 * 31)) & ~frigid_rows
    world_map = np.where(mask & frigid_rows, world_map + 16, world_map)
    world_map = np.where(mask & temperate_rows, world_map + 8, world_map)
    return world_map


def manual_corrections(world_map: np.ndarray, part_idx: int) -> np.ndarray:
    if part_idx == 0:
        world_map[444, 366] = 28
        world_map[445, 366] = 28
        world_map[489, 415] = 27
        world_map[1055, 266] = 23
        world_map[1055, 267] = 23
    if part_idx == 2:
        world_map[890, 134] = 26
        world_map[890, 135] = 26
        world_map[1056, 417] = 13
        world_map[1061, 435] = 12
    return world_map


def render_worldmaps(worldmap_dir: str | Path, data1_dir: str | Path, out_dir: str | Path, *, mode: str = 'v2') -> Path:
    worldmap_dir = Path(worldmap_dir)
    data1_dir = Path(data1_dir)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    regular_ts = extract_regular_tileset(data1_dir)
    large_ts = extract_large_tileset(data1_dir)
    coastal_lut = np.frombuffer((data1_dir / 'part_0010_512bytes.bin').read_bytes(), dtype=np.uint8)
    parts = sorted(worldmap_dir.glob('*.bin'))
    grids = []
    for pi, pf in enumerate(parts):
        g = expand_to_regular_grid(decode_part(pf.read_bytes()), large_ts).astype(np.int32)
        if mode == 'v2':
            g = fill_deserts(g)
            g, candidates = replace_coasts(g, coastal_lut)
            g = replace_desert_coasts(g, candidates)
            g = update_frigid_temperate(g)
            g = manual_corrections(g, pi)
        grids.append(g)
        Image.fromarray(render_thumbnail(g, regular_ts), 'RGB').save(out / f'part{pi}_thumb.png')
        Image.fromarray(render_detailed(g, regular_ts, 4), 'RGB').save(out / f'part{pi}_4xtile.jpg', quality=85, optimize=True)
    combined = np.concatenate(grids, axis=1)
    Image.fromarray(render_thumbnail(combined, regular_ts), 'RGB').save(out.parent / f'contact_worldmap_{mode}.png')
    return out
