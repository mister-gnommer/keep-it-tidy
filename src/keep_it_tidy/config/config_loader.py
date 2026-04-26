import tomllib
from pathlib import Path

from .config_types import Config


def load_config(path: Path) -> Config:
    with open(path, "rb") as f:
        raw = tomllib.load(f)

    _require(raw, "directories")
    if not isinstance(raw["directories"], list) or len(raw["directories"]) == 0:
        raise ValueError("Config field 'directories' must be a non-empty list")
    _require(raw, "removable-main-sweep-ttl")
    _require(raw, "removable-remove-after")
    _require(raw, "arch-main-sweep-ttl")

    removable_main_sweep_ttl = int(raw["removable-main-sweep-ttl"])
    removable_remove_after = int(raw["removable-remove-after"])
    arch_main_sweep_ttl = int(raw["arch-main-sweep-ttl"])
    dir_scan_file_limit = int(raw.get("dir-scan-file-limit", 10000))

    _require_positive(removable_main_sweep_ttl, "removable-main-sweep-ttl")
    _require_positive(removable_remove_after, "removable-remove-after")
    _require_positive(arch_main_sweep_ttl, "arch-main-sweep-ttl")
    _require_positive(dir_scan_file_limit, "dir-scan-file-limit")

    return Config(
        directories=raw["directories"],
        ignore_pattern=raw.get("ignore-pattern", []),
        removable_pattern=raw.get("removable-pattern", ["_!tmp"]),
        danger_enable_removing=bool(raw.get("danger-enable-removing", True)),
        dry_run=bool(raw.get("dry-run", False)),
        removable_main_sweep_ttl=removable_main_sweep_ttl,
        removable_remove_after=removable_remove_after,
        arch_main_sweep_ttl=arch_main_sweep_ttl,
        enable_auto_arch=bool(raw.get("enable-auto-arch", False)),
        enable_removing=bool(raw.get("enable-removing", True)),
        remove_all=bool(raw.get("remove-all", False)),
        dir_scan_file_limit=dir_scan_file_limit,
        report_dir=Path(raw["report-dir"]) if "report-dir" in raw else None,
    )


def _require(raw: dict[str, object], key: str) -> None:
    if key not in raw:
        raise ValueError(f"Config missing required field: {key}")


def _require_positive(value: int, field: str) -> None:
    if value < 1:
        raise ValueError(f"Config field '{field}' must be >= 1, got {value}")
