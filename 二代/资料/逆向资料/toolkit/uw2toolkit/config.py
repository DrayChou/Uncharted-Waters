from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _env_path(name: str, default: Path) -> Path:
    value = os.getenv(name)
    return Path(value).expanduser().resolve() if value else default.resolve()


@dataclass(slots=True)
class ToolkitConfig:
    toolkit_root: Path
    raw_dir: Path
    output_dir: Path
    charmap_path: Path
    chip_no_path: Path
    exe_path: Path

    @classmethod
    def from_env(
        cls,
        *,
        raw_dir: str | Path | None = None,
        output_dir: str | Path | None = None,
    ) -> "ToolkitConfig":
        toolkit_root = Path(__file__).resolve().parents[1]
        default_raw = toolkit_root / "raw" / "Koukai2"
        default_out = toolkit_root / "output"
        raw = Path(raw_dir).resolve() if raw_dir else _env_path("UW2_RAW_DIR", default_raw)
        out = Path(output_dir).resolve() if output_dir else _env_path("UW2_OUT_DIR", default_out)
        return cls(
            toolkit_root=toolkit_root,
            raw_dir=raw,
            output_dir=out,
            charmap_path=raw / "KoeiCht.txt",
            chip_no_path=raw / "Chip_no.dat",
            exe_path=raw / "Main.exe",
        )

    def ensure_output_dir(self) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        return self.output_dir

    def require(self, path: Path, label: str | None = None) -> Path:
        if not path.exists():
            name = label or str(path)
            raise FileNotFoundError(f"Missing required file: {name}")
        return path
