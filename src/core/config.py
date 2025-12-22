"""Configuration loading for the Bory application.

This module centralizes configuration resolution from environment variables and
optional INI files so that other components can depend on a single source of
truth.
"""
from __future__ import annotations

import configparser
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Tuple


@dataclass
class AppConfig:
    """Resolved configuration for the application."""

    dundam_base_url: str = "https://dundam.xyz"
    request_timeout: float = 5.0
    ocr_language: str = "ko"
    max_party_members: int = 12
    config_path_used: Path | None = None


DEFAULT_CONFIG_PATHS: Tuple[Path, ...] = (
    Path("config.ini"),
    Path.home() / ".bory.ini",
)


def load_config(
    config_path: str | Path | None = None,
    environ: Mapping[str, str] | None = None,
    search_paths: Iterable[Path] | None = None,
) -> AppConfig:
    """Load configuration from environment variables and optional files.

    Resolution order (highest to lowest priority):
    1. Explicit environment variables (``BORY_*`` prefix).
    2. Values in the first discovered INI file.
    3. Built-in defaults.
    """

    environment = environ or os.environ
    parser = configparser.ConfigParser()

    candidate_paths = _determine_paths(config_path=config_path, search_paths=search_paths)
    used_path = _read_first_existing(parser, candidate_paths)

    defaults = AppConfig()

    return AppConfig(
        dundam_base_url=_resolve_value(
            environment=environment,
            parser=parser,
            key="dundam_base_url",
            env_key="BORY_DUNDAM_BASE_URL",
            default=defaults.dundam_base_url,
        ),
        request_timeout=_resolve_value(
            environment=environment,
            parser=parser,
            key="request_timeout",
            env_key="BORY_REQUEST_TIMEOUT",
            default=defaults.request_timeout,
            caster=float,
        ),
        ocr_language=_resolve_value(
            environment=environment,
            parser=parser,
            key="ocr_language",
            env_key="BORY_OCR_LANGUAGE",
            default=defaults.ocr_language,
        ),
        max_party_members=_resolve_value(
            environment=environment,
            parser=parser,
            key="max_party_members",
            env_key="BORY_MAX_PARTY_MEMBERS",
            default=defaults.max_party_members,
            caster=int,
        ),
        config_path_used=used_path,
    )


def _determine_paths(
    *, config_path: str | Path | None, search_paths: Iterable[Path] | None
) -> Tuple[Path, ...]:
    if config_path:
        return (Path(config_path).expanduser(),)
    if search_paths is not None:
        return tuple(Path(path).expanduser() for path in search_paths)
    return DEFAULT_CONFIG_PATHS


def _read_first_existing(parser: configparser.ConfigParser, paths: Iterable[Path]) -> Path | None:
    for path in paths:
        expanded = Path(path).expanduser()
        if expanded.is_file():
            parser.read(expanded)
            return expanded
    return None


def _resolve_value(
    *,
    environment: Mapping[str, str],
    parser: configparser.ConfigParser,
    key: str,
    env_key: str,
    default: Any,
    caster: Callable[[str], Any] = lambda value: value,
):
    if env_key in environment:
        return caster(environment[env_key])
    if parser.has_option("bory", key):
        return caster(parser.get("bory", key))
    return default
