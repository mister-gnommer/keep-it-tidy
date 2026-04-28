#!/usr/bin/env python3
import argparse
import logging
import sys
from pathlib import Path

from .config.config_loader import load_config
from .pipeline.pipeline import run_pipeline
from .platform.os_guard import os_guard


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

    run_pipeline(config)


if __name__ == "__main__":
    main()
