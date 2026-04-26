from datetime import datetime
from pathlib import Path

from ..config.config_types import Config, PipelineAction


def build_report(actions: list[PipelineAction], config: Config, now: datetime) -> str:
    lines = [
        "# keep-it-tidy dry-run report",
        "",
        f"Generated: {now.strftime('%Y-%m-%d %H:%M:%S')}",
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
            lines.append(f"- **{action.type}** `{action.source_path}`{target}")
            lines.append(f"  _{action.reason}_")

    return "\n".join(lines) + "\n"


def write_report(
    actions: list[PipelineAction], config: Config, now: datetime, output_dir: Path
) -> Path:
    content = build_report(actions, config, now)
    report_path = output_dir / f"keep-it-tidy-report-{now.strftime('%Y-%m-%d')}.md"
    report_path.write_text(content, encoding="utf-8")
    return report_path
