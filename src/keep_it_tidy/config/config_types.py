from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal


@dataclass
class Config:
    directories: list[str]
    removable_main_sweep_ttl: int
    removable_remove_after: int
    arch_main_sweep_ttl: int
    ignore_pattern: list[str] = field(default_factory=list)
    removable_pattern: list[str] = field(default_factory=lambda: ["_!tmp"])
    danger_enable_removing: bool = True
    dry_run: bool = False
    enable_auto_arch: bool = False
    enable_removing: bool = True
    remove_all: bool = False
    dir_scan_file_limit: int = 10000


@dataclass
class ScannedItem:
    path: Path
    name: str
    is_directory: bool
    effective_date: datetime


ItemClassification = Literal["ignored", "removable", "standard"]


@dataclass
class ClassifiedItem:
    item: ScannedItem
    classification: ItemClassification
    age_in_days: int


ActionType = Literal["stage-for-removal", "delete", "move-to-safe", "archive", "skip"]


@dataclass
class PipelineAction:
    type: ActionType
    source_path: Path
    target_path: Path | None
    reason: str
