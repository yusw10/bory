"""Simple dependency container for wiring application services."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .config import AppConfig, load_config


@dataclass
class Container:
    """A lightweight container holding resolved application dependencies."""

    config: AppConfig


def create_container(
    config_path: str | Path | None = None, environ: Mapping[str, str] | None = None
) -> Container:
    """Create a container with the resolved configuration.

    DI entrypoint so CLI and future services can share a single construction
    pathway.
    """

    resolved_config = load_config(config_path=config_path, environ=environ)
    return Container(config=resolved_config)
