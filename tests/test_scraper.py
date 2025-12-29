from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import requests
from src.core.scraper import DundamScraper


def test_parse_total_damage_basic():
    html = """
    <div>
        <span>총딜</span>
        <span>12.3조</span>
    </div>
    """
    scraper = DundamScraper()
    assert scraper.parse_total_damage(html) == "12.3조"


def test_parse_total_damage_in_text():
    html = """
    <div class="info">캐릭터 정보: 총딜 845억 / DPS 123만</div>
    """
    scraper = DundamScraper()
    assert scraper.parse_total_damage(html) == "845억"


def test_parse_total_damage_missing():
    scraper = DundamScraper()
    with pytest.raises(ValueError):
        scraper.parse_total_damage("<html><body>데미지 없음</body></html>")


def test_fetch_html_retries_on_server_error():
    response_ok = SimpleNamespace(status_code=200, text="ok")
    response_ok.raise_for_status = Mock()

    response_err = SimpleNamespace(status_code=500, text="error")
    response_err.raise_for_status = Mock()

    session = Mock()
    session.get = Mock(side_effect=[response_err, response_ok])

    scraper = DundamScraper(
        session=session, request_timeout=1.0, max_retries=1, retry_backoff=0.0
    )

    assert scraper.fetch_html("https://example.test") == "ok"
    assert session.get.call_count == 2


def test_fetch_html_fails_fast_on_client_error():
    response = SimpleNamespace(status_code=404, text="not found")
    response.raise_for_status = Mock(side_effect=requests.HTTPError(response=response))

    session = Mock()
    session.get = Mock(return_value=response)

    scraper = DundamScraper(
        session=session, request_timeout=1.0, max_retries=3, retry_backoff=0.0
    )

    with pytest.raises(RuntimeError, match="요청 실패"):
        scraper.fetch_html("https://example.test")
    assert session.get.call_count == 1


def test_fetch_html_raises_after_retries():
    response = SimpleNamespace(status_code=503, text="error")
    response.raise_for_status = Mock(
        side_effect=requests.HTTPError("Server error", response=response)
    )

    session = Mock()
    session.get = Mock(return_value=response)

    scraper = DundamScraper(
        session=session, request_timeout=1.0, max_retries=1, retry_backoff=0.0
    )

    with pytest.raises(RuntimeError, match="재시도 초과"):
        scraper.fetch_html("https://example.test")
    assert session.get.call_count == 2
