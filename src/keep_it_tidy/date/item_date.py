import logging
import os
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


def get_effective_date(
    path: Path,
    file_limit: int,
) -> datetime:
    if not path.is_dir(follow_symlinks=False):
        return _file_date(path)

    fallback_ts = _stat_ts(path.stat())
    best_ts = fallback_ts
    count = 0

    for file_path in _iter_files(path):
        try:
            stat = file_path.stat()
        except OSError:
            continue
        ts = _stat_ts(stat)
        if ts > best_ts:
            best_ts = ts
        count += 1
        if count >= file_limit:
            logger.warning(
                "dir-scan-file-limit (%d) reached scanning %s; using best date found so far",
                file_limit,
                path,
            )
            break

    return datetime.fromtimestamp(best_ts)


def _file_date(path: Path) -> datetime:
    stat = path.lstat()  # lstat avoids following symlinks — consistent with scanner's follow_symlinks=False
    return datetime.fromtimestamp(_stat_ts(stat))


def _stat_ts(stat: os.stat_result) -> float:
    mtime = stat.st_mtime
    if hasattr(stat, "st_birthtime"):
        birthtime = float(stat.st_birthtime)  # type: ignore[attr-defined]  # safe: guarded by hasattr above
        return max(mtime, birthtime)
    return mtime


def _iter_files(root: Path) -> Iterator[Path]:
    try:
        with os.scandir(root) as scanner:
            entries = list(scanner)
    except OSError:
        return

    for entry in entries:
        if entry.is_dir(follow_symlinks=False):
            yield from _iter_files(Path(entry.path))
        elif entry.is_file(follow_symlinks=False):
            yield Path(entry.path)
