from __future__ import annotations

import importlib.util
from dataclasses import asdict, dataclass
from pathlib import Path

from .config import ToolkitConfig


@dataclass(slots=True)
class CheckResult:
    name: str
    status: str
    detail: str


def _has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def run_doctor(cfg: ToolkitConfig) -> list[CheckResult]:
    results: list[CheckResult] = []

    results.append(CheckResult('toolkit_root', 'ok' if cfg.toolkit_root.exists() else 'missing', str(cfg.toolkit_root)))
    results.append(CheckResult('raw_dir', 'ok' if cfg.raw_dir.exists() else 'missing', str(cfg.raw_dir)))
    cfg.ensure_output_dir()
    results.append(CheckResult('output_dir', 'ok', str(cfg.output_dir)))

    required = [
        ('Main.exe', cfg.exe_path),
        ('Chip_no.dat', cfg.chip_no_path),
        ('KoeiCht.txt', cfg.charmap_path),
    ]
    for label, path in required:
        results.append(CheckResult(label, 'ok' if path.exists() else 'missing', str(path)))

    lzw_count = len(list(cfg.raw_dir.glob('*.lzw'))) if cfg.raw_dir.exists() else 0
    dat_count = len(list(cfg.raw_dir.glob('*.dat'))) if cfg.raw_dir.exists() else 0
    results.append(CheckResult('raw_lzw_count', 'ok' if lzw_count > 0 else 'warn', str(lzw_count)))
    results.append(CheckResult('raw_dat_count', 'ok' if dat_count > 0 else 'warn', str(dat_count)))

    for module, group in [('numpy', 'core'), ('PIL', 'core'), ('unicorn', 'research'), ('capstone', 'research'), ('pyte', 'research')]:
        ok = _has_module(module)
        status = 'ok' if ok else ('warn' if group == 'research' else 'missing')
        results.append(CheckResult(f'dep:{module}', status, group))

    return results


def summarize(results: list[CheckResult]) -> dict:
    return {
        'ok': sum(1 for r in results if r.status == 'ok'),
        'warn': sum(1 for r in results if r.status == 'warn'),
        'missing': sum(1 for r in results if r.status == 'missing'),
        'results': [asdict(r) for r in results],
    }
