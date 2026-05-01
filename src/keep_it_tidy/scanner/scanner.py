from pathlib import Path

from ..config.config_types import Config, ScannedItem
from ..date.item_date import get_effective_date

_SPECIAL_DIRS = frozenset(["_to-remove", "_auto-arch", "_safe-to-remove"])


def scan(directory: Path, config: Config) -> list[ScannedItem]:
    items: list[ScannedItem] = []
    try:
        entries = list(directory.iterdir())
    except OSError:
        return items

    for entry in entries:
        if entry.name in _SPECIAL_DIRS:
            continue
        try:
            is_dir = entry.is_dir(follow_symlinks=False)
        except OSError:
            continue
        effective_date = get_effective_date(entry, config.dir_scan_file_limit)
        items.append(
            ScannedItem(
                path=entry,
                name=entry.name,
                is_directory=is_dir,
                effective_date=effective_date,
            )
        )

    return items
