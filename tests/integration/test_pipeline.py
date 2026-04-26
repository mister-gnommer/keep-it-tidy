import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from keep_it_tidy.config.config_types import Config
from keep_it_tidy.pipeline.pipeline import run


def _age(path: Path, days: int) -> None:
    ts = (datetime.now() - timedelta(days=days)).timestamp()
    os.utime(path, (ts, ts))


def _config(tmpdir: str, **overrides: object) -> Config:
    return Config(
        directories=[tmpdir],
        removable_main_sweep_ttl=7,
        removable_remove_after=14,
        arch_main_sweep_ttl=60,
        dry_run=True,
        enable_auto_arch=bool(overrides.get("enable_auto_arch", False)),
        ignore_pattern=list(overrides.get("ignore_pattern", [])),  # type: ignore[arg-type]
        danger_enable_removing=bool(overrides.get("danger_enable_removing", True)),
    )


def test_old_removable_file_staged() -> None:
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "scratch_!tmp.txt"
        f.write_text("x")
        _age(f, 10)

        actions = run(_config(d))
        assert any(a.type == "stage-for-removal" for a in actions)


def test_young_removable_not_staged() -> None:
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "fresh_!tmp.txt"
        f.write_text("x")
        _age(f, 2)

        actions = run(_config(d))
        assert not any(a.type == "stage-for-removal" for a in actions)


def test_standard_old_file_archived_when_enabled() -> None:
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "old_report.pdf"
        f.write_text("x")
        _age(f, 90)

        actions = run(_config(d, enable_auto_arch=True))
        assert any(a.type == "archive" for a in actions)


def test_ignored_file_not_touched() -> None:
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "node_modules_backup_!tmp.txt"
        f.write_text("x")
        _age(f, 100)

        actions = run(_config(d, ignore_pattern=["node_modules"]))
        paths = [str(a.source_path) for a in actions]
        assert not any("node_modules" in p for p in paths)


def test_staged_old_item_deleted() -> None:
    with tempfile.TemporaryDirectory() as d:
        staging = Path(d) / "_to-remove"
        staging.mkdir()
        old_date = (datetime.now() - timedelta(days=20)).strftime("%Y-%m-%d")
        entry = staging / f"{old_date}_old_file.txt"
        entry.write_text("x")

        actions = run(_config(d))
        assert any(a.type == "delete" for a in actions)


def test_dry_run_makes_no_filesystem_changes() -> None:
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "old_!tmp.txt"
        f.write_text("x")
        _age(f, 10)

        run(_config(d))

        assert f.exists(), "File should not be moved in dry_run mode"
