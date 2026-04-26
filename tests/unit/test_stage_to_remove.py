import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from keep_it_tidy.config.config_types import Config
from keep_it_tidy.pipeline.stage_to_remove import plan


def _config(*, danger_enable_removing: bool = True, removable_remove_after: int = 14) -> Config:
    return Config(
        directories=["/watched"],
        removable_main_sweep_ttl=7,
        removable_remove_after=removable_remove_after,
        arch_main_sweep_ttl=60,
        danger_enable_removing=danger_enable_removing,
    )


def _staged_name(days_ago: int, original: str = "file.txt") -> str:
    date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    return f"{date}_{original}"


def test_old_item_produces_delete() -> None:
    with tempfile.TemporaryDirectory() as d:
        staging = Path(d) / "_to-remove"
        staging.mkdir()
        (staging / _staged_name(20)).write_text("x")

        actions = plan(Path(d), _config(), datetime.now())
        assert len(actions) == 1
        assert actions[0].type == "delete"


def test_recent_item_not_touched() -> None:
    with tempfile.TemporaryDirectory() as d:
        staging = Path(d) / "_to-remove"
        staging.mkdir()
        (staging / _staged_name(3)).write_text("x")

        actions = plan(Path(d), _config(), datetime.now())
        assert len(actions) == 0


def test_danger_disable_produces_move_to_safe() -> None:
    with tempfile.TemporaryDirectory() as d:
        staging = Path(d) / "_to-remove"
        staging.mkdir()
        (staging / _staged_name(20)).write_text("x")

        actions = plan(Path(d), _config(danger_enable_removing=False), datetime.now())
        assert len(actions) == 1
        assert actions[0].type == "move-to-safe"
        assert actions[0].target_path is not None
        assert "_safe-to-remove" in str(actions[0].target_path)


def test_missing_staging_dir_returns_empty() -> None:
    with tempfile.TemporaryDirectory() as d:
        actions = plan(Path(d), _config(), datetime.now())
        assert len(actions) == 0


def test_entries_without_date_prefix_skipped() -> None:
    with tempfile.TemporaryDirectory() as d:
        staging = Path(d) / "_to-remove"
        staging.mkdir()
        (staging / "no-date-prefix.txt").write_text("x")

        actions = plan(Path(d), _config(), datetime.now())
        assert len(actions) == 0
