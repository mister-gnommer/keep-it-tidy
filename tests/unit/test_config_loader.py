import tempfile
from pathlib import Path

import pytest

from keep_it_tidy.config.config_loader import load_config


def _write(content: str) -> Path:
    f = tempfile.NamedTemporaryFile(suffix=".toml", delete=False, mode="w", encoding="utf-8")
    f.write(content)
    f.close()
    return Path(f.name)


def test_loads_minimal_valid_config() -> None:
    path = _write("""
directories = ["/tmp"]
removable-main-sweep-ttl = 7
removable-remove-after = 14
arch-main-sweep-ttl = 60
""")
    config = load_config(path)
    assert config.directories == ["/tmp"]
    assert config.removable_main_sweep_ttl == 7
    assert config.removable_pattern == ["_!tmp"]
    assert config.dry_run is False
    assert config.enable_auto_arch is False
    assert config.dir_scan_file_limit == 10000
    assert config.report_dir is None


def test_missing_directories_raises() -> None:
    path = _write("""
removable-main-sweep-ttl = 7
removable-remove-after = 14
arch-main-sweep-ttl = 60
""")
    with pytest.raises(ValueError, match="directories"):
        load_config(path)


def test_empty_directories_raises() -> None:
    path = _write("""
directories = []
removable-main-sweep-ttl = 7
removable-remove-after = 14
arch-main-sweep-ttl = 60
""")
    with pytest.raises(ValueError, match="non-empty"):
        load_config(path)


def test_missing_ttl_raises() -> None:
    path = _write("""
directories = ["/tmp"]
removable-remove-after = 14
arch-main-sweep-ttl = 60
""")
    with pytest.raises(ValueError, match="removable-main-sweep-ttl"):
        load_config(path)


def test_zero_ttl_raises() -> None:
    path = _write("""
directories = ["/tmp"]
removable-main-sweep-ttl = 0
removable-remove-after = 14
arch-main-sweep-ttl = 60
""")
    with pytest.raises(ValueError, match="removable-main-sweep-ttl"):
        load_config(path)


def test_negative_ttl_raises() -> None:
    path = _write("""
directories = ["/tmp"]
removable-main-sweep-ttl = 7
removable-remove-after = -1
arch-main-sweep-ttl = 60
""")
    with pytest.raises(ValueError, match="removable-remove-after"):
        load_config(path)


def test_all_fields_loaded() -> None:
    path = _write("""
directories = ["/home/user/Downloads", "/tmp"]
ignore-pattern = ["node_modules", ".git"]
removable-pattern = ["_!tmp", "_trash"]
danger-enable-removing = false
dry-run = true
removable-main-sweep-ttl = 3
removable-remove-after = 7
arch-main-sweep-ttl = 30
enable-auto-arch = true
enable-removing = false
remove-all = true
dir-scan-file-limit = 500
report-dir = "/tmp/reports"
""")
    config = load_config(path)
    assert config.directories == ["/home/user/Downloads", "/tmp"]
    assert config.ignore_pattern == ["node_modules", ".git"]
    assert config.removable_pattern == ["_!tmp", "_trash"]
    assert config.danger_enable_removing is False
    assert config.dry_run is True
    assert config.removable_main_sweep_ttl == 3
    assert config.removable_remove_after == 7
    assert config.arch_main_sweep_ttl == 30
    assert config.enable_auto_arch is True
    assert config.enable_removing is False
    assert config.remove_all is True
    assert config.dir_scan_file_limit == 500
    assert config.report_dir == Path("/tmp/reports")
