from pathlib import Path

from ..config.config_types import ClassifiedItem, Config, PipelineAction


def plan(
    items: list[ClassifiedItem],
    config: Config,
    watched_dir: Path,
) -> list[PipelineAction]:
    if not config.enable_auto_arch:
        return []

    arch_dir = watched_dir / "_auto-arch"
    actions: list[PipelineAction] = []

    for ci in items:
        if ci.classification != "standard":
            continue
        if ci.age_in_days < config.arch_main_sweep_ttl:
            continue

        actions.append(
            PipelineAction(
                type="archive",
                source_path=ci.item.path,
                target_path=arch_dir / ci.item.name,
                reason=(
                    f"age {ci.age_in_days}d >= arch-main-sweep-ttl "
                    f"{config.arch_main_sweep_ttl}d"
                ),
            )
        )

    return actions
