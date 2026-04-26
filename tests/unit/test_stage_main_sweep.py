from datetime import datetime, timedelta
from pathlib import Path

from keep_it_tidy.config.config_types import ClassifiedItem, Config, ScannedItem
from keep_it_tidy.pipeline.stage_main_sweep import plan


def _classified(name: str, classification: str, age: int) -> ClassifiedItem:
    return ClassifiedItem(
        item=ScannedItem(
            path=Path(f"/watched/{name}"),
            name=name,
            is_directory=False,
            effective_date=datetime.now() - timedelta(days=age),
        ),
        classification=classification,  # type: ignore[arg-type]
        age_in_days=age,
    )


def _config(*, enable_removing: bool = True, removable_main_sweep_ttl: int = 7) -> Config:
    return Config(
        directories=["/watched"],
        removable_main_sweep_ttl=removable_main_sweep_ttl,
        removable_remove_after=14,
        arch_main_sweep_ttl=60,
        enable_removing=enable_removing,
    )


def test_old_removable_is_staged() -> None:
    actions = plan([_classified("old_!tmp", "removable", 10)], _config(), Path("/watched"), datetime.now())
    assert len(actions) == 1
    assert actions[0].type == "stage-for-removal"
    assert "_to-remove" in str(actions[0].target_path)
    assert "old_!tmp" in str(actions[0].target_path)


def test_target_has_date_prefix() -> None:
    now = datetime(2026, 4, 26)
    actions = plan([_classified("old_!tmp", "removable", 10)], _config(), Path("/watched"), now)
    assert actions[0].target_path is not None
    assert actions[0].target_path.name.startswith("2026-04-26_")


def test_young_removable_not_staged() -> None:
    actions = plan([_classified("new_!tmp", "removable", 3)], _config(), Path("/watched"), datetime.now())
    assert len(actions) == 0


def test_standard_item_not_staged() -> None:
    actions = plan([_classified("doc.pdf", "standard", 100)], _config(), Path("/watched"), datetime.now())
    assert len(actions) == 0


def test_ignored_item_not_staged() -> None:
    actions = plan([_classified(".git", "ignored", 100)], _config(), Path("/watched"), datetime.now())
    assert len(actions) == 0


def test_enable_removing_false_returns_empty() -> None:
    actions = plan(
        [_classified("old_!tmp", "removable", 10)],
        _config(enable_removing=False),
        Path("/watched"),
        datetime.now(),
    )
    assert len(actions) == 0
