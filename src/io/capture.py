from __future__ import annotations

from pathlib import Path

import pyautogui
from PIL import Image


def capture_fullscreen() -> Image.Image:
    """현재 화면 전체를 캡쳐한다."""
    screenshot = pyautogui.screenshot()
    return screenshot


def save_image(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
