from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from .config import ToolkitConfig
from .dat_extract import extract_phase1
from .doctor import run_doctor, summarize
from .ls11 import decode_file, write_parts
from .render.portchip import save_atlas_sheets
from .render.portmap import render_all_portmaps
from .render.worldmap import render_worldmaps
from .text import decode_offset_file


def cmd_ls11_decode(args: argparse.Namespace) -> None:
    parts = decode_file(args.input)
    out = write_parts(parts, args.outdir)
    print(f"decoded {len(parts)} parts -> {out}")


def cmd_inventory_lzw(args: argparse.Namespace) -> None:
    src = Path(args.src_dir)
    out_root = Path(args.out_dir)
    out_root.mkdir(parents=True, exist_ok=True)
    files = sorted(src.glob('*.lzw'))
    for f in files:
        parts = decode_file(f)
        sizes = [len(p) for p in parts]
        ctr = Counter(sizes)
        sub = out_root / f.stem
        write_parts(parts, sub)
        print(f"{f.name}: parts={len(parts)} total={sum(sizes)} top_sizes={ctr.most_common(5)}")


def cmd_render_portchip(args: argparse.Namespace) -> None:
    out = save_atlas_sheets(args.parts_dir, args.out_dir)
    print(f"rendered atlases -> {out}")


def cmd_render_portmap(args: argparse.Namespace) -> None:
    out = render_all_portmaps(args.portmap_dir, args.portchip_dir, args.chip_no, args.out_dir)
    print(f"rendered portmaps -> {out}")


def cmd_render_worldmap(args: argparse.Namespace) -> None:
    out = render_worldmaps(args.worldmap_dir, args.data1_dir, args.out_dir, mode=args.mode)
    print(f"rendered worldmaps ({args.mode}) -> {out}")


def cmd_extract_phase1(args: argparse.Namespace) -> None:
    result = extract_phase1(args.raw_dir, args.out_dir)
    print(json.dumps({k: 'ok' for k in result}, ensure_ascii=False, indent=2))


def cmd_decode_text(args: argparse.Namespace) -> None:
    messages = decode_offset_file(args.file, charmap_path=args.charmap)
    print(f"count={len(messages)}")
    preview = messages if args.all else messages[: min(40, len(messages))]
    for i, m in enumerate(preview):
        print(f"[{i}] {m}")


def cmd_doctor(args: argparse.Namespace) -> None:
    cfg = ToolkitConfig.from_env(raw_dir=args.raw_dir, output_dir=args.out_dir)
    summary = summarize(run_doctor(cfg))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    cfg = ToolkitConfig.from_env()
    parser = argparse.ArgumentParser(prog='uw2tool')
    sub = parser.add_subparsers(dest='command', required=True)

    p = sub.add_parser('ls11-decode')
    p.add_argument('input')
    p.add_argument('outdir')
    p.set_defaults(func=cmd_ls11_decode)

    p = sub.add_parser('inventory-lzw')
    p.add_argument('--src-dir', default=str(cfg.raw_dir))
    p.add_argument('--out-dir', default=str(cfg.output_dir / 'lzw_parts'))
    p.set_defaults(func=cmd_inventory_lzw)

    p = sub.add_parser('render-portchip')
    p.add_argument('--parts-dir', default=str(cfg.output_dir / 'lzw_parts' / 'Portchip'))
    p.add_argument('--out-dir', default=str(cfg.output_dir / 'portchip'))
    p.set_defaults(func=cmd_render_portchip)

    p = sub.add_parser('render-portmap')
    p.add_argument('--portmap-dir', default=str(cfg.output_dir / 'lzw_parts' / 'Portmap'))
    p.add_argument('--portchip-dir', default=str(cfg.output_dir / 'lzw_parts' / 'Portchip'))
    p.add_argument('--chip-no', default=str(cfg.chip_no_path))
    p.add_argument('--out-dir', default=str(cfg.output_dir / 'portmap'))
    p.set_defaults(func=cmd_render_portmap)

    p = sub.add_parser('render-worldmap')
    p.add_argument('--worldmap-dir', default=str(cfg.output_dir / 'lzw_parts' / 'Worldmap'))
    p.add_argument('--data1-dir', default=str(cfg.output_dir / 'lzw_parts' / 'Data1'))
    p.add_argument('--out-dir', default=str(cfg.output_dir / 'worldmap'))
    p.add_argument('--mode', choices=['v1', 'v2'], default='v2')
    p.set_defaults(func=cmd_render_worldmap)

    p = sub.add_parser('extract-phase1')
    p.add_argument('--raw-dir', default=str(cfg.raw_dir))
    p.add_argument('--out-dir', default=str(cfg.output_dir / 'game_data'))
    p.set_defaults(func=cmd_extract_phase1)

    p = sub.add_parser('decode-text')
    p.add_argument('file')
    p.add_argument('--charmap', default=str(cfg.charmap_path))
    p.add_argument('--all', action='store_true')
    p.set_defaults(func=cmd_decode_text)

    p = sub.add_parser('doctor')
    p.add_argument('--raw-dir', default=str(cfg.raw_dir))
    p.add_argument('--out-dir', default=str(cfg.output_dir))
    p.set_defaults(func=cmd_doctor)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
