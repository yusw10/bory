from __future__ import annotations

import pytest

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
