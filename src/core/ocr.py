from __future__ import annotations

import tempfile
from pathlib import Path
from typing import List

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

    def parse_characters(self, text: str) -> List[CharacterInfo]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        characters: List[CharacterInfo] = []
        for line in lines:
            # 단순하게: "이름 직업 명성" 형태를 공백 기준으로 파싱
            parts = line.split()
            if not parts:
                continue
            name = parts[0]
            job = parts[1] if len(parts) >= 2 else None
            fame = None
            if len(parts) >= 3 and parts[2].isdigit():
                fame = int(parts[2])
            characters.append(CharacterInfo(name=name, job=job, fame=fame))
        return characters

    def extract_characters_from_image(self, image: Image.Image) -> List[CharacterInfo]:
        text = self.extract_text(image)
        return self.parse_characters(text)

    def save_screenshot(self, image: Image.Image, directory: Path | None = None) -> Path:
        directory = directory or Path(tempfile.gettempdir())
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "raid_snapshot.png"
        image.save(path)
        return path
