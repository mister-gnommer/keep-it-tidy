import ast
import tempfile
from pathlib import Path

from keep_it_tidy.config.config_types import Config, PipelineAction
from keep_it_tidy.fs.fs_ops import execute_pipeline_actions

_SRC_DIR = Path(__file__).parent.parent.parent / "src"

_DELETION_ATTRS = frozenset(["rmtree", "unlink", "rmdir"])


def test_deletion_calls_only_in_fs_ops() -> None:
    offenders: list[str] = []

    for path in _SRC_DIR.rglob("*.py"):
        if path.name == "fs_ops.py":
            continue
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr in _DELETION_ATTRS:
                offenders.append(f"{path}: uses '{node.attr}'")

    assert not offenders, (
        "Deletion calls found outside fs_ops.py:\n" + "\n".join(offenders)
    )


def test_dry_run_prevents_deletion() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir) / "should_survive.txt"
        target.write_text("keep me")

        action = PipelineAction(
            type="delete",
            source_path=target,
            target_path=None,
            reason="test",
        )
        execute_pipeline_actions([action], _config(dry_run=True))

        assert target.exists(), "File was deleted despite dry_run=True"


def test_dry_run_prevents_move() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        source = Path(tmpdir) / "source.txt"
        source.write_text("x")
        dest = Path(tmpdir) / "_to-remove" / "2026-01-01_source.txt"

        action = PipelineAction(
            type="stage-for-removal",
            source_path=source,
            target_path=dest,
            reason="test",
        )
        execute_pipeline_actions([action], _config(dry_run=True))

        assert source.exists(), "File was moved despite dry_run=True"
        assert not dest.exists(), "Destination should not exist in dry_run"


def test_danger_disable_moves_to_safe_instead_of_deleting() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        # source must be inside _to-remove/ so fs_ops can derive the safe dir
        to_remove = Path(tmpdir) / "_to-remove"
        to_remove.mkdir()
        source = to_remove / "2026-01-01_old_file.txt"
        source.write_text("x")

        action = PipelineAction(
            type="delete",
            source_path=source,
            target_path=None,
            reason="test",
        )
        execute_pipeline_actions([action], _config(danger_enable_removing=False))

        assert not source.exists(), "File should have been moved"
        safe = Path(tmpdir) / "_safe-to-remove" / source.name
        assert safe.exists(), "File should be in _safe-to-remove/"


def _config(*, dry_run: bool = False, danger_enable_removing: bool = True) -> Config:
    return Config(
        directories=["/tmp"],
        removable_main_sweep_ttl=7,
        removable_remove_after=14,
        arch_main_sweep_ttl=60,
        dry_run=dry_run,
        danger_enable_removing=danger_enable_removing,
    )
