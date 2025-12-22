import os
from pathlib import Path

import pytest

from src.core.config import AppConfig, load_config
from src.core.container import create_container


def test_load_config_prefers_env_over_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    config_file = tmp_path / "bory.ini"
    config_file.write_text(
        """
[bory]
dundam_base_url=https://file.example
request_timeout=3.5
ocr_language=file
max_party_members=8
"""
    )

    monkeypatch.setenv("BORY_DUNDAM_BASE_URL", "https://env.example")
    monkeypatch.setenv("BORY_REQUEST_TIMEOUT", "4.0")

    config = load_config(config_path=config_file, environ=os.environ)

    assert config.dundam_base_url == "https://env.example"
    assert config.request_timeout == 4.0
    assert config.ocr_language == "file"
    assert config.max_party_members == 8
    assert config.config_path_used == config_file


def test_create_container_uses_defaults_when_no_config(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("BORY_DUNDAM_BASE_URL", raising=False)
    monkeypatch.delenv("BORY_REQUEST_TIMEOUT", raising=False)
    monkeypatch.delenv("BORY_OCR_LANGUAGE", raising=False)
    monkeypatch.delenv("BORY_MAX_PARTY_MEMBERS", raising=False)

    container = create_container(environ={})

    assert container.config == AppConfig()
