from datetime import datetime
from pathlib import Path

from ..classifier.classifier import classify
from ..config.config_types import Config, PipelineAction
from ..fs.fs_ops import execute_pipeline_actions
from ..report.report import write_report
from ..scanner.scanner import scan
from .stage_auto_arch import plan as plan_auto_arch
from .stage_main_sweep import plan as plan_main_sweep
from .stage_to_remove import plan as plan_to_remove


def run_pipeline(config: Config) -> list[PipelineAction]:
    now = datetime.now()
    actions_from_all_dirs: list[PipelineAction] = []

    for dir_str in config.directories:
        watched_dir = Path(dir_str)
        if not watched_dir.is_dir():
            continue

        items = scan(watched_dir, config)
        classified = classify(items, config, now)

        stage_actions: list[PipelineAction] = []
        stage_actions.extend(plan_main_sweep(classified, config, watched_dir, now))
        stage_actions.extend(plan_to_remove(watched_dir, config, now))
        stage_actions.extend(plan_auto_arch(classified, config, watched_dir))

        execute_pipeline_actions(stage_actions, config)
        actions_from_all_dirs.extend(stage_actions)

    write_report(actions_from_all_dirs, config, now)

    # Returned for integration tests; __main__ does not use this value.
    # Prefer keeping it over restructuring tests — it also leaves the door open
    # for future callers (e.g. a --summary flag or non-zero exit on actions taken).
    return actions_from_all_dirs
