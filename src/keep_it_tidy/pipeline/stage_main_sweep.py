from datetime import datetime
from pathlib import Path

from ..config.config_types import ClassifiedItem, Config, PipelineAction


def plan(
    items: list[ClassifiedItem],
    config: Config,
    watched_dir: Path,
    now: datetime,
) -> list[PipelineAction]:
    if not config.enable_removing:
        return []

    staging_dir = watched_dir / "_to-remove"
    date_str = now.strftime("%Y-%m-%d")
    actions: list[PipelineAction] = []

    for ci in items:
        if ci.classification != "removable":
            continue
        if ci.age_in_days < config.removable_main_sweep_ttl:
            continue

        target_path = staging_dir / f"{date_str}_{ci.item.name}"
        actions.append(
            PipelineAction(
                type="stage-for-removal",
                source_path=ci.item.path,
                target_path=target_path,
                reason=(
                    f"age {ci.age_in_days}d >= removable-main-sweep-ttl "
                    f"{config.removable_main_sweep_ttl}d"
                ),
            )
        )

    return actions
