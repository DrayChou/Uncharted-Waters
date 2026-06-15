#!/usr/bin/env python3

import argparse
import io
import json
import zipfile
import zlib
from pathlib import Path


RZIP_HEADER_SIZE = 0x18
FIRST_BLOCK_LEN_OFFSET = 20
RAM_OFFSET_IN_BLOCK0 = 0x20
RAM_SIZE = 65536

# 1.9E6 current lead:
# - ship 0 status table starts near 0x08A2
# - E6 appears to add a 16-byte header before the old 30-byte ShipStatus payload
# - food/water remain little-endian UInt16, stored as displayed_value * 10
SHIP_STATUS_BASE = 0x08A2
SHIP_STATUS_STRIDE = 46
SUPPLY_PAYLOAD_OFFSET = 16
FOOD_OFFSET = SUPPLY_PAYLOAD_OFFSET + 0
WATER_OFFSET = SUPPLY_PAYLOAD_OFFSET + 2
MATERIAL_OFFSET = SUPPLY_PAYLOAD_OFFSET + 4
CANNONBALL_OFFSET = SUPPLY_PAYLOAD_OFFSET + 6
HEALTH_OFFSET = 45


def read_u16le(buf: bytes, offset: int) -> int:
    return buf[offset] | (buf[offset + 1] << 8)


def write_u16le(buf: bytearray, offset: int, value: int) -> None:
    buf[offset] = value & 0xFF
    buf[offset + 1] = (value >> 8) & 0xFF


def parse_rzip_blocks(raw: bytes) -> tuple[bytes, list[bytes]]:
    header = raw[:RZIP_HEADER_SIZE]
    first_len = int.from_bytes(header[FIRST_BLOCK_LEN_OFFSET:FIRST_BLOCK_LEN_OFFSET + 4], "little")

    idx = RZIP_HEADER_SIZE
    blocks = []

    first_block = raw[idx:idx + first_len]
    if len(first_block) != first_len:
        raise ValueError("invalid first RZIP block length")
    blocks.append(first_block)
    idx += first_len

    while idx < len(raw):
        if idx + 4 > len(raw):
            raise ValueError("truncated RZIP block length")
        block_len = int.from_bytes(raw[idx:idx + 4], "little")
        idx += 4
        block = raw[idx:idx + block_len]
        if len(block) != block_len:
            raise ValueError("truncated RZIP block payload")
        blocks.append(block)
        idx += block_len

    return header, blocks


def build_rzip(header: bytes, blocks: list[bytes]) -> bytes:
    new_header = bytearray(header)
    new_header[FIRST_BLOCK_LEN_OFFSET:FIRST_BLOCK_LEN_OFFSET + 4] = len(blocks[0]).to_bytes(4, "little")

    out = bytearray(new_header)
    out.extend(blocks[0])
    for block in blocks[1:]:
        out.extend(len(block).to_bytes(4, "little"))
        out.extend(block)
    return bytes(out)


def get_ship_offsets(ship_index: int) -> dict[str, int]:
    base = SHIP_STATUS_BASE + ship_index * SHIP_STATUS_STRIDE
    return {
        "base": base,
        "food": base + FOOD_OFFSET,
        "water": base + WATER_OFFSET,
        "material": base + MATERIAL_OFFSET,
        "cannonball": base + CANNONBALL_OFFSET,
        "health": base + HEALTH_OFFSET,
    }


def read_inner_state(path: Path) -> tuple[str, bytes, dict[str, bytes]]:
    extras = {}
    with zipfile.ZipFile(path, "r") as outer:
        inner_state_name = None
        inner_state_raw = None
        for info in outer.infolist():
            data = outer.read(info.filename)
            if info.filename.endswith(".state") and inner_state_name is None:
                inner_state_name = info.filename
                inner_state_raw = data
            else:
                extras[info.filename] = data
    if inner_state_name is None or inner_state_raw is None:
        raise ValueError("outer zip does not contain .state payload")
    return inner_state_name, inner_state_raw, extras


def write_outer_state(path: Path, inner_state_name: str, inner_state_raw: bytes, extras: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as outer:
        outer.writestr(inner_state_name, inner_state_raw)
        for name, data in extras.items():
            outer.writestr(name, data)


def patch_state(
    path: Path,
    output: Path,
    ship_index: int,
    food_display: int | None,
    water_display: int | None,
    health: int | None,
) -> dict[str, int]:
    inner_name, inner_raw, extras = read_inner_state(path)
    header, blocks = parse_rzip_blocks(inner_raw)

    block0 = zlib.decompress(blocks[0])
    ram = bytearray(block0[RAM_OFFSET_IN_BLOCK0:RAM_OFFSET_IN_BLOCK0 + RAM_SIZE])

    offsets = get_ship_offsets(ship_index)

    before_food = read_u16le(ram, offsets["food"])
    before_water = read_u16le(ram, offsets["water"])
    before_material = read_u16le(ram, offsets["material"])
    before_cannonball = read_u16le(ram, offsets["cannonball"])
    before_health = ram[offsets["health"]]

    if food_display is not None:
        write_u16le(ram, offsets["food"], food_display * 10)
    if water_display is not None:
        write_u16le(ram, offsets["water"], water_display * 10)
    if health is not None:
        ram[offsets["health"]] = health & 0xFF

    block0_mut = bytearray(block0)
    block0_mut[RAM_OFFSET_IN_BLOCK0:RAM_OFFSET_IN_BLOCK0 + RAM_SIZE] = ram
    blocks[0] = zlib.compress(bytes(block0_mut))

    new_inner_raw = build_rzip(header, blocks)
    write_outer_state(output, inner_name, new_inner_raw, extras)

    return {
        "food_before_raw": before_food,
        "water_before_raw": before_water,
        "material_raw": before_material,
        "cannonball_raw": before_cannonball,
        "health_before": before_health,
        "food_after_raw": read_u16le(ram, offsets["food"]),
        "water_after_raw": read_u16le(ram, offsets["water"]),
        "health_after": ram[offsets["health"]],
        "food_before_display": before_food // 10,
        "water_before_display": before_water // 10,
        "food_after_display": read_u16le(ram, offsets["food"]) // 10,
        "water_after_display": read_u16le(ram, offsets["water"]) // 10,
        "food_offset": offsets["food"],
        "water_offset": offsets["water"],
        "health_offset": offsets["health"],
        "ship_index": ship_index,
    }


def inspect_state(path: Path, ship_index: int) -> dict[str, int]:
    inner_name, inner_raw, _extras = read_inner_state(path)
    _ = inner_name
    _header, blocks = parse_rzip_blocks(inner_raw)
    block0 = zlib.decompress(blocks[0])
    ram = block0[RAM_OFFSET_IN_BLOCK0:RAM_OFFSET_IN_BLOCK0 + RAM_SIZE]
    offsets = get_ship_offsets(ship_index)
    food = read_u16le(ram, offsets["food"])
    water = read_u16le(ram, offsets["water"])
    material = read_u16le(ram, offsets["material"])
    cannonball = read_u16le(ram, offsets["cannonball"])
    health = ram[offsets["health"]]
    return {
        "ship_index": ship_index,
        "food_raw": food,
        "water_raw": water,
        "material_raw": material,
        "cannonball_raw": cannonball,
        "health": health,
        "food_display": food // 10,
        "water_display": water // 10,
        "food_offset": offsets["food"],
        "water_offset": offsets["water"],
        "health_offset": offsets["health"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Patch Uncharted Waters II MD 1.9E6 save-state food/water for the first ship."
    )
    parser.add_argument("state", type=Path, help="path to the outer .state zip file")
    parser.add_argument("--output", type=Path, help="output path, defaults to <input>.patched.state")
    parser.add_argument("--ship-index", type=int, default=0, help="ship slot to patch, default: 0")
    parser.add_argument("--food", type=int, help="target displayed food value, e.g. 100")
    parser.add_argument("--water", type=int, help="target displayed water value, e.g. 100")
    parser.add_argument("--health", type=int, help="target health value, e.g. 100")
    parser.add_argument("--inspect", action="store_true", help="only inspect current values, do not patch")
    args = parser.parse_args()

    if args.inspect:
        print(json.dumps(inspect_state(args.state, args.ship_index), ensure_ascii=False, indent=2))
        return

    if args.food is None and args.water is None and args.health is None:
        parser.error("at least one of --food, --water, or --health is required unless --inspect is used")

    output = args.output or args.state.with_name(args.state.stem + ".patched.state")
    result = patch_state(args.state, output, args.ship_index, args.food, args.water, args.health)
    result["output"] = str(output)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
