from datetime import datetime, timedelta
from pathlib import Path

from keep_it_tidy.classifier.classifier import classify
from keep_it_tidy.config.config_types import Config, ScannedItem


def _item(name: str, days_ago: int) -> ScannedItem:
    return ScannedItem(
        path=Path(f"/watched/{name}"),
        name=name,
        is_directory=False,
        effective_date=datetime.now() - timedelta(days=days_ago),
    )


def _config(
    *,
    ignore_pattern: list[str] | None = None,
    removable_pattern: list[str] | None = None,
    remove_all: bool = False,
) -> Config:
    return Config(
        directories=["/watched"],
        removable_main_sweep_ttl=7,
        removable_remove_after=14,
        arch_main_sweep_ttl=60,
        ignore_pattern=ignore_pattern or [],
        removable_pattern=removable_pattern or ["_!tmp"],
        remove_all=remove_all,
    )


def test_ignore_pattern_match() -> None:
    result = classify([_item(".git_config", 100)], _config(ignore_pattern=[".git"]), datetime.now())
    assert result[0].classification == "ignored"


def test_removable_pattern_match() -> None:
    result = classify([_item("scratch_!tmp", 10)], _config(), datetime.now())
    assert result[0].classification == "removable"


def test_standard_item() -> None:
    result = classify([_item("important.pdf", 10)], _config(), datetime.now())
    assert result[0].classification == "standard"


def test_remove_all_overrides() -> None:
    result = classify([_item("important.pdf", 10)], _config(remove_all=True), datetime.now())
    assert result[0].classification == "removable"


def test_ignore_takes_priority_over_removable() -> None:
    result = classify(
        [_item("keep_!tmp", 10)],
        _config(ignore_pattern=["keep"], removable_pattern=["_!tmp"]),
        datetime.now(),
    )
    assert result[0].classification == "ignored"


def test_age_in_days_computed() -> None:
    result = classify([_item("file.txt", 30)], _config(), datetime.now())
    assert 29 <= result[0].age_in_days <= 31


def test_age_never_negative() -> None:
    future_item = ScannedItem(
        path=Path("/watched/future.txt"),
        name="future.txt",
        is_directory=False,
        effective_date=datetime.now() + timedelta(days=1),
    )
    result = classify([future_item], _config(), datetime.now())
    assert result[0].age_in_days == 0
