import re
from datetime import datetime
from pathlib import Path

from ..config.config_types import Config, PipelineAction

_DATE_PREFIX = re.compile(r"^(\d{4}-\d{2}-\d{2})_.+$")


def plan(watched_dir: Path, config: Config, now: datetime) -> list[PipelineAction]:
    staging_dir = watched_dir / "_to-remove"
    if not staging_dir.exists():
        return []

    actions: list[PipelineAction] = []

    try:
        entries = list(staging_dir.iterdir())
    except OSError:
        return actions

    for entry in entries:
        match = _DATE_PREFIX.match(entry.name)
        if not match:
            continue

        try:
            staged_date = datetime.strptime(match.group(1), "%Y-%m-%d")
        except ValueError:
            continue

        staged_age_days = (now - staged_date).days
        if staged_age_days < config.removable_remove_after:
            continue

        reason = (
            f"staged {staged_age_days}d ago >= removable-remove-after "
            f"{config.removable_remove_after}d"
        )

        if config.danger_enable_removing:
            actions.append(
                PipelineAction(
                    type="delete",
                    source_path=entry,
                    target_path=None,
                    reason=reason,
                )
            )
        else:
            safe_dir = watched_dir / "_safe-to-remove"
            actions.append(
                PipelineAction(
                    type="move-to-safe",
                    source_path=entry,
                    target_path=safe_dir / entry.name,
                    reason=reason + " (danger-enable-removing=false)",
                )
            )

    return actions
