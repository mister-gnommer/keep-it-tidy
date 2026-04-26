from datetime import datetime, timedelta
from pathlib import Path

from keep_it_tidy.config.config_types import ClassifiedItem, Config, ScannedItem
from keep_it_tidy.pipeline.stage_auto_arch import plan


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


def _config(*, enable_auto_arch: bool = True, arch_main_sweep_ttl: int = 60) -> Config:
    return Config(
        directories=["/watched"],
        removable_main_sweep_ttl=7,
        removable_remove_after=14,
        arch_main_sweep_ttl=arch_main_sweep_ttl,
        enable_auto_arch=enable_auto_arch,
    )


def test_old_standard_item_archived() -> None:
    actions = plan([_classified("report.pdf", "standard", 90)], _config(), Path("/watched"))
    assert len(actions) == 1
    assert actions[0].type == "archive"
    assert "_auto-arch" in str(actions[0].target_path)
    assert "report.pdf" in str(actions[0].target_path)


def test_young_standard_item_not_archived() -> None:
    actions = plan([_classified("recent.pdf", "standard", 10)], _config(), Path("/watched"))
    assert len(actions) == 0


def test_removable_item_not_archived() -> None:
    actions = plan([_classified("old_!tmp", "removable", 90)], _config(), Path("/watched"))
    assert len(actions) == 0


def test_ignored_item_not_archived() -> None:
    actions = plan([_classified(".git", "ignored", 90)], _config(), Path("/watched"))
    assert len(actions) == 0


def test_enable_auto_arch_false_returns_empty() -> None:
    actions = plan(
        [_classified("old.pdf", "standard", 90)], _config(enable_auto_arch=False), Path("/watched")
    )
    assert len(actions) == 0
