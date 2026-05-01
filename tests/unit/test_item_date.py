import logging
import os
import tempfile
import time
from datetime import datetime
from pathlib import Path

import pytest

from keep_it_tidy.date.item_date import get_effective_date


def test_file_returns_a_datetime() -> None:
    with tempfile.NamedTemporaryFile() as f:
        result = get_effective_date(Path(f.name), file_limit=10000)
        assert isinstance(result, datetime)


def test_empty_directory_falls_back_to_dir_mtime() -> None:
    with tempfile.TemporaryDirectory() as d:
        result = get_effective_date(Path(d), file_limit=10000)
        assert isinstance(result, datetime)


def test_directory_date_reflects_newest_child() -> None:
    with tempfile.TemporaryDirectory() as d:
        path = Path(d)
        old_file = path / "old.txt"
        new_file = path / "new.txt"
        old_file.write_text("old")
        new_file.write_text("new")

        old_ts = 1_000_000.0
        new_ts = 2_000_000.0
        os.utime(old_file, (old_ts, old_ts))
        os.utime(new_file, (new_ts, new_ts))

        result = get_effective_date(path, file_limit=10000)
        assert result.timestamp() >= new_ts


def test_subdirectory_files_included_in_date_scan() -> None:
    with tempfile.TemporaryDirectory() as d:
        path = Path(d)
        subdir = path / "node_modules" / "pkg"
        subdir.mkdir(parents=True)
        hot_file = subdir / "index.js"
        hot_file.write_text("x")

        future_ts = time.time() + 100_000
        os.utime(hot_file, (future_ts, future_ts))

        result = get_effective_date(path, file_limit=10000)
        assert result.timestamp() >= future_ts


def test_file_limit_logs_warning(caplog: pytest.LogCaptureFixture) -> None:
    with tempfile.TemporaryDirectory() as d:
        path = Path(d)
        for i in range(6):
            (path / f"file{i}.txt").write_text("x")

        with caplog.at_level(logging.WARNING, logger="keep_it_tidy.date.item_date"):
            get_effective_date(path, file_limit=3)

        assert any("dir-scan-file-limit" in r.message for r in caplog.records)
