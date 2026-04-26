from datetime import datetime
from pathlib import Path

from ..classifier.classifier import classify
from ..config.config_types import Config, PipelineAction
from ..fs.fs_ops import execute_pipeline_actions
from ..scanner.scanner import scan
from .stage_auto_arch import plan as plan_auto_arch
from .stage_main_sweep import plan as plan_main_sweep
from .stage_to_remove import plan as plan_to_remove


def run(config: Config) -> list[PipelineAction]:
    now = datetime.now()
    all_actions: list[PipelineAction] = []

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
        all_actions.extend(stage_actions)

    return all_actions
