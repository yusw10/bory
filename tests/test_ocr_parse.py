from __future__ import annotations

from src.core.ocr import OcrEngine


def test_parse_characters_from_text_lines():
    sample = """
    보리사랑 버서커 45678
    세컨캐릭 마도학자 42310
    """
    engine = OcrEngine()
    characters = engine.parse_characters(sample)

    assert len(characters) == 2
    assert characters[0].name == "보리사랑"
    assert characters[0].job == "버서커"
    assert characters[0].fame == 45678
    assert characters[1].name == "세컨캐릭"
    assert characters[1].job == "마도학자"
    assert characters[1].fame == 42310


def test_parse_characters_with_commas_and_labels():
    sample = """
    보리사랑 버서커 명성 45,678
    세컨캐릭/마도학자 42,310
    """
    engine = OcrEngine()
    characters = engine.parse_characters(sample)

    assert len(characters) == 2
    assert characters[0].name == "보리사랑"
    assert characters[0].job == "버서커"
    assert characters[0].fame == 45678
    assert characters[1].name == "세컨캐릭"
    assert characters[1].job == "마도학자"
    assert characters[1].fame == 42310


def test_parse_characters_missing_job():
    sample = """
    보리사랑 45678
    """
    engine = OcrEngine()
    characters = engine.parse_characters(sample)

    assert len(characters) == 1
    assert characters[0].name == "보리사랑"
    assert characters[0].job is None
    assert characters[0].fame == 45678
