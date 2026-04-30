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
        staged_date = _parse_staged_date(entry.name)

        if staged_date is None:
            # No valid date prefix (missing or malformed) — stamp with today so
            # TTL tracking starts from this run.
            stamped = staging_dir / f"{now.strftime('%Y-%m-%d')}_{entry.name}"
            actions.append(PipelineAction(
                type="stage-for-removal",
                source_path=entry,
                target_path=stamped,
                reason="missing or invalid date prefix in _to-remove/; stamped with today's date",
            ))
            continue

        staged_age_days = (now - staged_date).days
        if staged_age_days < config.removable_remove_after:
            continue

        reason = (
            f"staged {staged_age_days}d ago >= removable-remove-after "
            f"{config.removable_remove_after}d"
        )

        actions.append(PipelineAction(
            type="delete",
            source_path=entry,
            target_path=None,
            reason=reason,
        ))

    return actions


def _parse_staged_date(name: str) -> datetime | None:
    match = _DATE_PREFIX.match(name)
    if not match:
        return None
    try:
        return datetime.strptime(match.group(1), "%Y-%m-%d")
    except ValueError:
        return None
