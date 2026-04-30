import logging
import shutil

from ..config.config_types import Config, PipelineAction

logger = logging.getLogger(__name__)


def execute_pipeline_actions(actions: list[PipelineAction], config: Config) -> None:
    for action in actions:
        _log(action, config.dry_run)

        if config.dry_run:
            continue

        if action.type == "stage-for-removal":
            _ensure_parent(action)
            shutil.move(str(action.source_path), str(action.target_path))

        elif action.type == "archive":
            _ensure_parent(action)
            shutil.move(str(action.source_path), str(action.target_path))

        elif action.type == "delete":
            if not config.danger_enable_removing:
                # SINGLE DELETION POINT — enforced by tests/unit/test_single_deletion_point.py
                # dry_run is guaranteed False: the continue above skips this entire block otherwise
                safe_dir = action.source_path.parent.parent / "_safe-to-remove"
                target = safe_dir / action.source_path.name
                target.parent.mkdir(parents=True, exist_ok=True)
                logger.info("danger-enable-removing=false: moving to %s instead of deleting", target)
                shutil.move(str(action.source_path), str(target))
            else:
                shutil.rmtree(action.source_path)


def _log(action: PipelineAction, dry_run: bool) -> None:
    prefix = "[DRY-RUN] " if dry_run else ""
    target = f" -> {action.target_path}" if action.target_path else ""
    logger.info("%s%s: %s%s | %s", prefix, action.type, action.source_path, target, action.reason)


def _ensure_parent(action: PipelineAction) -> None:
    if action.target_path is not None:
        action.target_path.parent.mkdir(parents=True, exist_ok=True)
