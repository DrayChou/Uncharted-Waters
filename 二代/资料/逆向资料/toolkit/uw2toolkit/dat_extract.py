from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import numpy as np


def extract_za_dat(raw_dir: str | Path) -> dict:
    raw = (Path(raw_dir) / "Za_dat.dat").read_bytes()
    n = 101
    stride = 24
    if len(raw) != n * stride:
        raise ValueError(f"Unexpected Za_dat.dat size: {len(raw)}")
    ports = []
    for i in range(n):
        rec = raw[i * stride:(i + 1) * stride]
        u16_le = [int.from_bytes(rec[k:k + 2], "little") for k in range(0, stride, 2)]
        ports.append({
            "port_id": i,
            "u16_le_fields": u16_le,
            "u8_bytes": list(rec),
            "raw_hex": rec.hex(),
            "sentinel_ffff_count": sum(1 for v in u16_le if v == 0xFFFF),
        })
    field_stats = []
    for f in range(12):
        vals = [p["u16_le_fields"][f] for p in ports]
        non = [v for v in vals if v != 0xFFFF]
        field_stats.append({
            "field_index": f,
            "byte_offset": f * 2,
            "distinct_values": len(set(vals)),
            "sentinel_count": sum(1 for v in vals if v == 0xFFFF),
            "non_sentinel_min": min(non) if non else None,
            "non_sentinel_max": max(non) if non else None,
            "non_sentinel_mean": round(sum(non) / len(non), 1) if non else None,
        })
    return {
        "source": "Za_dat.dat",
        "record_count": n,
        "record_size_bytes": stride,
        "fields_per_record": 12,
        "field_stats": field_stats,
        "ports": ports,
    }


def extract_monster_dat(raw_dir: str | Path) -> dict:
    raw = (Path(raw_dir) / "Monster.dat").read_bytes()
    result = {"source": "Monster.dat", "size_bytes": len(raw), "raw_hex": raw.hex()}
    for n_records, stride in [(10, 20), (20, 10), (25, 8), (40, 5), (8, 25), (50, 4)]:
        if n_records * stride != len(raw):
            continue
        records = []
        for i in range(n_records):
            rec = raw[i * stride:(i + 1) * stride]
            records.append({
                "id": i,
                "bytes": list(rec),
                "u16_le": [int.from_bytes(rec[k:k+2], 'little') for k in range(0, stride, 2)] if stride % 2 == 0 else None,
            })
        result[f"as_{n_records}x{stride}"] = {"n_records": n_records, "stride": stride, "records": records}
    return result


def extract_windcur_dat(raw_dir: str | Path) -> dict:
    raw = (Path(raw_dir) / "Windcur.dat").read_bytes()
    if len(raw) != 1350:
        return {"source": "Windcur.dat", "size_bytes": len(raw)}
    grid = np.frombuffer(raw, dtype=np.uint8).reshape(45, 30)
    return {
        "source": "Windcur.dat",
        "size_bytes": len(raw),
        "grid_layout": "30 cols × 45 rows",
        "distinct_values": dict(sorted(Counter(raw).items())),
        "grid_30x45": grid.tolist(),
    }


def extract_phase1(raw_dir: str | Path, out_dir: str | Path | None = None) -> dict[str, dict]:
    result = {
        "za_dat": extract_za_dat(raw_dir),
        "monster_dat": extract_monster_dat(raw_dir),
        "windcur_dat": extract_windcur_dat(raw_dir),
    }
    if out_dir is not None:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        for name, payload in result.items():
            (out / f"{name}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return result
