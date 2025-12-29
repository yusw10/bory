from __future__ import annotations

import urllib.parse

from PIL import Image
from src.core.ocr import OcrEngine
from src.core.scraper import DundamScraper


def _run_capture_ocr_fetch(
    template: str,
    ocr_engine: OcrEngine,
    scraper: DundamScraper,
    capture_fn,
):
    image = capture_fn()
    characters = ocr_engine.extract_characters_from_image(image)
    damages = []
    for info in characters:
        url = template.replace("{name}", urllib.parse.quote(info.name))
        damages.append(
            scraper.fetch_character_damage(url, name=info.name, job=info.job)
        )
    return characters, damages


def test_capture_ocr_fetch_pipeline(monkeypatch):
    capture_called = {"value": False}

    def fake_capture():
        capture_called["value"] = True
        return Image.new("RGB", (10, 10), "white")

    ocr_engine = OcrEngine()
    monkeypatch.setattr(
        ocr_engine,
        "extract_text",
        lambda _: "Alpha Warrior 12345\nBeta Mage 67890\n",
    )

    scraper = DundamScraper()
    template = "https://example.test/character?name={name}"
    html_map = {
        template.replace(
            "{name}", urllib.parse.quote("Alpha")
        ): "<div>총딜 12.3조</div>",
        template.replace("{name}", urllib.parse.quote("Beta")): "<div>총딜 845억</div>",
    }
    monkeypatch.setattr(scraper, "fetch_html", lambda url: html_map[url])

    characters, damages = _run_capture_ocr_fetch(
        template, ocr_engine, scraper, fake_capture
    )

    assert capture_called["value"] is True
    assert [c.name for c in characters] == ["Alpha", "Beta"]
    assert [c.job for c in characters] == ["Warrior", "Mage"]
    assert [c.fame for c in characters] == [12345, 67890]
    assert [d.damage for d in damages] == ["12.3조", "845억"]
