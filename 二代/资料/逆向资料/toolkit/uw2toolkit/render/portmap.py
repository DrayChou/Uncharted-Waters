from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from .portchip import load_atlases

W = H = 96
T = 16


def load_chip_no(path: str | Path, port_count: int) -> list[int]:
    chip_no = list(Path(path).read_bytes())
    while len(chip_no) < port_count:
        chip_no.append(0)
    return chip_no


def render_portmap(index_bytes: bytes, atlas: np.ndarray) -> np.ndarray:
    idx = np.frombuffer(index_bytes, dtype=np.uint8).reshape(H, W)
    img = np.zeros((H * T, W * T, 3), dtype=np.uint8)
    for y in range(H):
        for x in range(W):
            tile_id = idx[y, x]
            if tile_id < atlas.shape[0]:
                img[y * T:(y + 1) * T, x * T:(x + 1) * T] = atlas[tile_id]
    return img


def render_all_portmaps(portmap_dir: str | Path, portchip_dir: str | Path, chip_no_path: str | Path, out_dir: str | Path) -> Path:
    atlases = load_atlases(portchip_dir)
    port_files = sorted(Path(portmap_dir).glob('*.bin'))
    chip_no = load_chip_no(chip_no_path, len(port_files))
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rendered = []
    for pi, pf in enumerate(port_files):
        atlas = atlases[chip_no[pi]]
        img = render_portmap(pf.read_bytes(), atlas)
        rendered.append(img)
        Image.fromarray(img, 'RGB').save(out / f'{pi:03d}.png')
    cols = 10
    rows = (len(rendered) + cols - 1) // cols
    thumb_size = 192
    sheet = Image.new('RGB', (cols * thumb_size, rows * thumb_size), (20, 20, 30))
    for i, img in enumerate(rendered):
        thumb = Image.fromarray(img, 'RGB').resize((thumb_size, thumb_size), Image.BILINEAR)
        sheet.paste(thumb, ((i % cols) * thumb_size, (i // cols) * thumb_size))
    sheet.save(out.parent / 'contact_portmap.png')
    return out
