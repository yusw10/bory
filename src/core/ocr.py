from __future__ import annotations

import re
import tempfile
from pathlib import Path

import cv2
import numpy as np
import pytesseract
from PIL import Image

from src.core.models import CharacterInfo


class OcrEngine:
    """OpenCV + Tesseract 기반 OCR 래퍼.

    - 이미지 전처리(그레이스케일, 이진화) 후 pytesseract로 텍스트 추출
    - 실서비스에서는 정규식을 통해 캐릭터명/직업/명성을 파싱하도록 확장 가능
    """

    def __init__(self, language: str = "kor+eng") -> None:
        self.language = language

    def extract_text(self, image: Image.Image) -> str:
        gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY)
        return pytesseract.image_to_string(thresh, lang=self.language)

    def parse_characters(self, text: str) -> list[CharacterInfo]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        characters: list[CharacterInfo] = []
        for line in lines:
            info = self._parse_line(line)
            if info:
                characters.append(info)
        return characters

    def extract_characters_from_image(self, image: Image.Image) -> list[CharacterInfo]:
        text = self.extract_text(image)
        return self.parse_characters(text)

    def save_screenshot(
        self, image: Image.Image, directory: Path | None = None
    ) -> Path:
        directory = directory or Path(tempfile.gettempdir())
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "raid_snapshot.png"
        image.save(path)
        return path

    def _parse_line(self, line: str) -> CharacterInfo | None:
        normalized = self._normalize_line(line)
        if not normalized:
            return None

        tokens = normalized.split()
        if not tokens or tokens[0].isdigit():
            return None

        fame = self._extract_fame(normalized, tokens)

        name = tokens[0]
        job = " ".join(tokens[1:]) if len(tokens) > 1 else None
        if job == "":
            job = None
        return CharacterInfo(name=name, job=job, fame=fame)

    def _normalize_line(self, line: str) -> str:
        line = line.replace("명성", " ").replace("Fame", " ")
        line = re.sub(r"[|｜丨/\\\\]", " ", line)
        line = re.sub(r"\s+", " ", line).strip()
        return line

    def _extract_fame(self, line: str, tokens: list[str]) -> int | None:
        numbers = re.findall(r"\d[\d,]*", line)
        if not numbers:
            return None
        fame_str = numbers[-1].replace(",", "")
        try:
            fame = int(fame_str)
        except ValueError:
            return None

        for i in range(len(tokens) - 1, -1, -1):
            if fame_str in tokens[i].replace(",", ""):
                tokens.pop(i)
                break
        return fame
