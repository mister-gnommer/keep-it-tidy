#!/usr/bin/env python3
import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

from .config.config_loader import load_config
from .pipeline.pipeline import run
from .platform.os_guard import os_guard
from .report.report import write_report


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

    if config.dry_run and config.directories:
        now = datetime.now()
        first_dir = Path(config.directories[0])
        report_path = write_report(actions, config, now, first_dir)
        logging.info("Dry-run report written to %s", report_path)


if __name__ == "__main__":
    main()
