# keep-it-tidy — Implementation Plan

> Session: `b87fb0b1-5fc3-4de6-8dc9-3f67b92bedac` — resume with `claude --resume b87fb0b1-5fc3-4de6-8dc9-3f67b92bedac`

## Context

Create a daily-running Python CLI script that keeps configured directories tidy by removing or staging old files/directories based on age and pattern rules. The spec lives in `tmp-description.md` and should be deleted after the user confirms everything is done. Safety is paramount: file deletion must happen in exactly one place in the code, enforced by a unit test.

---

## Key Decisions

- **Language**: Python 3.11+ — no external dependencies needed (`tomllib` is stdlib since 3.11)
- **Date strategy**: `max(stat().st_mtime, stat().st_birthtime)` per file. For directories: recursively find the max date among all descendants (fallback to directory's own mtime if empty). Note: `st_birthtime` may not be available on all Linux filesystems — fall back to `st_mtime` if missing.
- **Directory scan guard**: `item_date.py` respects `ignore-pattern` during recursive date scanning (so `node_modules` in ignore-pattern won't be traversed). Additionally a hard cap `dir-scan-file-limit` (default `10000`) stops recursion early and falls back to the directory's own mtime with a warning logged — prevents runaway scanning of huge trees.
- **Folder names**: `_to-remove` (staging), `_auto-arch` (archive), `_safe-to-remove` (non-destructive mode destination)
- **Staged item naming**: `_to-remove/YYYY-MM-DD_<originalName>` — date prefix encodes when it was staged, parsed by the removal stage
- **Config format**: TOML (`tomllib` stdlib) — supports comments, human-readable
- **Scheduler**: systemd user timer (not cron) — correct for Fedora

---

## Project Structure

```
keep-it-tidy/
├── pyproject.toml                    # project config, deps, tool settings
├── .gitignore
├── config/
│   ├── config.example.toml           # committed — documents all fields with comments
│   └── config.toml                   # gitignored — actual user config
├── src/
│   └── keep_it_tidy/
│       ├── __init__.py
│       ├── __main__.py               # entry: parse args, load config, run pipeline
│       ├── config/
│       │   ├── __init__.py
│       │   ├── config_types.py       # Config, dataclass definitions
│       │   └── config_loader.py      # parse TOML, validate, apply defaults
│       ├── platform/
│       │   ├── __init__.py
│       │   └── os_guard.py           # raises if not Linux
│       ├── scanner/
│       │   ├── __init__.py
│       │   └── scanner.py            # iterdir walk → list[ScannedItem]
│       ├── date/
│       │   ├── __init__.py
│       │   └── item_date.py          # get_effective_date(path, is_dir) → datetime
│       ├── classifier/
│       │   ├── __init__.py
│       │   └── classifier.py         # pattern + TTL rules → list[ClassifiedItem]
│       ├── pipeline/
│       │   ├── __init__.py
│       │   ├── pipeline.py           # orchestrates stages, collects PipelineAction list
│       │   ├── stage_main_sweep.py   # removable items → _to-remove staging
│       │   ├── stage_to_remove.py    # staged items past TTL → delete or _safe-to-remove
│       │   └── stage_auto_arch.py    # old standard items → _auto-arch
│       ├── fs/
│       │   ├── __init__.py
│       │   └── fs_ops.py             # THE ONLY MODULE THAT MUTATES THE FILESYSTEM
│       └── report/
│           ├── __init__.py
│           └── report.py             # builds dry-run markdown report
├── tests/
│   ├── unit/
│   │   ├── test_single_deletion_point.py   # safety enforcement test (highest priority)
│   │   ├── test_config_loader.py
│   │   ├── test_item_date.py
│   │   ├── test_classifier.py
│   │   ├── test_stage_main_sweep.py
│   │   ├── test_stage_to_remove.py
│   │   └── test_stage_auto_arch.py
│   └── integration/
│       └── test_pipeline.py
└── scripts/
    └── setup-systemd.sh              # installs systemd user timer
```

---

## Core Types (`src/keep_it_tidy/config/config_types.py`, `src/keep_it_tidy/pipeline/pipeline.py`)

```python
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

@dataclass
class Config:
    directories: list[str]
    ignore_pattern: list[str]
    removable_pattern: list[str]      # default: ["_!tmp"]
    danger_enable_removing: bool      # default: True
    dry_run: bool                     # default: False
    removable_main_sweep_ttl: int     # days
    removable_remove_after: int       # days
    arch_main_sweep_ttl: int          # days
    enable_auto_arch: bool            # default: False
    enable_removing: bool             # default: True
    remove_all: bool                  # default: False
    dir_scan_file_limit: int          # default: 10000

@dataclass
class ScannedItem:
    path: Path
    name: str
    is_directory: bool
    effective_date: datetime

ItemClassification = Literal['ignored', 'removable', 'standard']

@dataclass
class ClassifiedItem:
    item: ScannedItem
    classification: ItemClassification
    age_in_days: int

ActionType = Literal['stage-for-removal', 'delete', 'move-to-safe', 'archive', 'skip']

@dataclass
class PipelineAction:
    type: ActionType
    source_path: Path
    target_path: Path | None
    reason: str
```

---

## Module Responsibilities

| Module | Responsibility |
|---|---|
| `__main__.py` | Parse `--config` flag, call `os_guard()`, load config, run pipeline, write report |
| `os_guard.py` | `if platform.system() != 'Linux': raise RuntimeError(...)` |
| `config_loader.py` | `tomllib.load()`, validate fields, apply defaults → `Config` |
| `scanner.py` | `iterdir()` top-level items; skip `_to-remove`, `_auto-arch`, `_safe-to-remove`; call `get_effective_date` per item |
| `item_date.py` | `max(mtime, birthtime)` for files; max over all descendants for directories — skips `ignore-pattern` subdirs and stops at `dir_scan_file_limit` |
| `classifier.py` | Pure function: ignore-pattern → `'ignored'`; removable-pattern → `'removable'`; else `'standard'` |
| `stage_main_sweep.py` | Pure: `removable` + age ≥ `removable_main_sweep_ttl` → `stage-for-removal` to `_to-remove/YYYY-MM-DD_name` |
| `stage_to_remove.py` | Scans `_to-remove/`, parses date prefix, staged-age ≥ `removable_remove_after` → `delete` or `move-to-safe` |
| `stage_auto_arch.py` | Pure: `standard` + age ≥ `arch_main_sweep_ttl` + `enable_auto_arch` → `archive` to `_auto-arch/name` |
| `fs_ops.py` | **Sole executor** of `PipelineAction` list; all mutations gated on `not config.dry_run` |
| `report.py` | Builds markdown from `PipelineAction` list; written by `__main__.py` when `dry_run=True` |

---

## Safety: Single Deletion Point

`src/keep_it_tidy/fs/fs_ops.py` is the only file that may call `shutil.rmtree`, `Path.unlink`, or `os.remove`. The deletion line must be directly preceded by the `dry_run` guard:

```python
# SINGLE DELETION POINT — enforced by tests/unit/test_single_deletion_point.py
if not config.dry_run:
    shutil.rmtree(action.source_path)
```

`tests/unit/test_single_deletion_point.py` enforces this in two ways:

1. **Static** — uses `ast` module to walk all `.py` files under `src/`, finds `Attribute` nodes for `rmtree`, `unlink`, `remove` — asserts only `fs_ops.py` contains them:

```python
import ast, glob

def test_deletion_only_in_fs_ops():
    for path in glob.glob('src/**/*.py', recursive=True):
        if path.endswith('fs_ops.py'):
            continue
        tree = ast.parse(open(path).read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                assert node.attr not in ('rmtree', 'unlink', 'remove'), \
                    f"Deletion call found in {path}"
```

2. **Behavioral** — call `execute_pipeline_actions` with a `delete` action and `dry_run=True` against a real temp file, assert the file still exists after.

---

## Data Flow

```
__main__.py
  os_guard()
  load_config(path) → Config
  for each dir:
    scan(dir) → list[ScannedItem]         (skips _to-remove, _auto-arch, _safe-to-remove)
    classify(items, config, now) → list[ClassifiedItem]
    stage_main_sweep.plan() → list[PipelineAction]
    stage_to_remove.plan(dir) → list[PipelineAction]   (separate scan of _to-remove/)
    stage_auto_arch.plan() → list[PipelineAction]
    fs_ops.execute(all_actions, config)
      dry_run=True  → no changes, accumulate for report
      dry_run=False → rename/rmtree based on action type
  if dry_run: report.write(actions) → <dir>/keep-it-tidy-report-YYYY-MM-DD.md
```

---

## pyproject.toml

```toml
[build-system]
requires = ["setuptools==80.1.0"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "keep-it-tidy"
version = "1.0.0"
description = "Daily directory cleanup tool for Linux"
requires-python = ">=3.11"
dependencies = []

[project.scripts]
keep-it-tidy = "keep_it_tidy.__main__:main"

[project.optional-dependencies]
dev = [
    "pytest==8.3.5",
    "mypy==1.15.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.mypy]
strict = true
files = ["src"]
```

No runtime dependencies — `tomllib`, `pathlib`, `shutil`, `platform`, `argparse`, `ast` are all stdlib.

---

## Systemd Timer (Fedora)

Two user-unit files installed by `setup-systemd.sh`:
- `keep-it-tidy.service` — `Type=oneshot`, runs `keep-it-tidy --config /path/to/config/config.toml`
- `keep-it-tidy.timer` — `OnCalendar=daily`, `Persistent=true`, `RandomizedDelaySec=300`

`Persistent=true` fires the timer once on next boot if the machine was off at scheduled time.

---

## Verification

1. `pip install -e ".[dev]"` — installs package + dev deps
2. `mypy src/` — type checks pass with strict mode
3. `pytest` — all tests pass, including `test_single_deletion_point.py`
4. Manual smoke test with `dry-run = true` against a real `~/Downloads` dir — check report is generated, nothing moved/deleted
5. Manual smoke test with `dry-run = false`, `danger-enable-removing = false` — verify items move to `_safe-to-remove`, nothing deleted
6. `scripts/setup-systemd.sh` — verify timer is listed by `systemctl --user list-timers`

---

## Cleanup

Delete `tmp-description.md` after user confirms everything works as expected.
