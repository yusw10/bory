"""Command-line entrypoint for the Bory application."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core.container import create_container


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bory command-line tools")
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to an INI configuration file. Defaults to config.ini or ~/.bory.ini.",
    )
    parser.add_argument(
        "--show-config",
        action="store_true",
        help="Print the resolved configuration and exit.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    container = create_container(config_path=args.config)

    if args.show_config:
        print(
            json.dumps(
                {
                    "dundam_base_url": container.config.dundam_base_url,
                    "request_timeout": container.config.request_timeout,
                    "ocr_language": container.config.ocr_language,
                    "max_party_members": container.config.max_party_members,
                    "config_path_used": str(container.config.config_path_used)
                    if container.config.config_path_used
                    else None,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    # Placeholder for future command implementations.
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
