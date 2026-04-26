#!/usr/bin/env python3
import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from .config.config_loader import load_config
from .pipeline.pipeline import run
from .platform.os_guard import os_guard
from .config.config_types import Config
from .report.report import write_report


def _resolve_report_dir(config: Config) -> Path:
    if config.report_dir is not None:
        return config.report_dir
    xdg_data = Path(os.environ.get("XDG_DATA_HOME", "~/.local/share")).expanduser()
    return xdg_data / "keep-it-tidy"


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    parser = argparse.ArgumentParser(description="keep-it-tidy: daily directory cleanup")
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to config.toml (required)",
    )
    args = parser.parse_args()

    os_guard()

    if args.config is None:
        logging.error("--config is required. Example: keep-it-tidy --config /path/to/config.toml")
        logging.error("Copy config/config.example.toml to get started.")
        sys.exit(1)

    try:
        config = load_config(args.config)
    except (FileNotFoundError, ValueError) as e:
        logging.error("Config error: %s", e)
        sys.exit(1)

    actions = run(config)

    if config.dry_run:
        now = datetime.now()
        report_dir = _resolve_report_dir(config)
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = write_report(actions, config, now, report_dir)
        logging.info("Dry-run report written to %s", report_path)


if __name__ == "__main__":
    main()
