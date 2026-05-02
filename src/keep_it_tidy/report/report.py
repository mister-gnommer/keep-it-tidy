import logging
import os
from datetime import datetime
from pathlib import Path

from ..config.config_types import Config, PipelineAction


def resolve_report_dir(config: Config) -> Path:
    if config.report_dir is not None:
        return config.report_dir
    xdg_data = Path(os.environ.get("XDG_DATA_HOME", "~/.local/share")).expanduser()
    return xdg_data / "keep-it-tidy"


def build_report(actions: list[PipelineAction], config: Config, now: datetime) -> str:
    lines = [
        "# keep-it-tidy report",
        "",
        f"Generated: {now.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Dry-run: {'yes' if config.dry_run else 'no'}",
        f"Watched: {', '.join(config.directories)}",
        "",
        "## Summary",
        "",
        "| Action | Count |",
        "|---|---|",
    ]

    counts: dict[str, int] = {}
    for action in actions:
        counts[action.type] = counts.get(action.type, 0) + 1

    if counts:
        for action_type, count in sorted(counts.items()):
            lines.append(f"| {action_type} | {count} |")
    else:
        lines.append("| (none) | 0 |")

    lines += ["", "## Actions", ""]

    if not actions:
        lines.append("No actions would be taken.")
    else:
        for action in actions:
            target = f" -> `{action.target_path}`" if action.target_path else ""
            lines.append(f"- **{action.type}** `{action.source_path}` -> {target}")
            lines.append(f"  _{action.reason}_")

    return "\n".join(lines) + "\n"


def write_report(actions: list[PipelineAction], config: Config, now: datetime) -> Path:
    report_dir = resolve_report_dir(config)
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{now.strftime('%Y%m%d-%H%M%S')}-keep-it-tidy.md"
    report_path.write_text(build_report(actions, config, now), encoding="utf-8")
    logging.info("Report written to %s", report_path)
    return report_path
