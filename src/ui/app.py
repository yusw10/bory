from __future__ import annotations

import threading
import urllib.parse
from pathlib import Path
from typing import List, Optional

import PySimpleGUI as sg

from src.core.models import CharacterDamage, CharacterInfo, RaidSnapshot
from src.core.ocr import OcrEngine
from src.core.scraper import DundamScraper
from src.io import capture


class RaidHelperApp:
    def __init__(self) -> None:
        self.ocr_engine = OcrEngine()
        self.scraper = DundamScraper()
        self.snapshot: Optional[RaidSnapshot] = None
        self.window = self._build_window()

    def _build_window(self) -> sg.Window:
        sg.theme("SystemDefault")

        layout = [
            [sg.Text("던담 URL 템플릿", size=(15, 1)), sg.InputText(
                "https://dundam.xyz/character?server=hilder&key={name}", key="-URL-TEMPLATE-", size=(60, 1)
            )],
            [
                sg.Button("시작(캡쳐)", key="-CAPTURE-"),
                sg.Button("데미지 조회", key="-FETCH-"),
                sg.Button("초기화", key="-RESET-"),
                sg.Button("종료", key="-EXIT-"),
            ],
            [sg.Text("상태", size=(15, 1)), sg.Text("대기 중", key="-STATUS-", size=(50, 1))],
            [sg.Table(
                values=[],
                headings=["이름", "직업", "명성", "총딜"],
                key="-TABLE-",
                auto_size_columns=False,
                col_widths=[15, 15, 10, 15],
                justification="left",
                enable_events=False,
            )],
            [sg.Multiline(size=(90, 8), key="-LOG-", disabled=True, autoscroll=True)],
        ]
        return sg.Window("던담 공대원 데미지 도우미", layout, finalize=True)

    def run(self) -> None:
        while True:
            event, values = self.window.read(timeout=200)
            if event in (sg.WINDOW_CLOSED, "-EXIT-"):
                break

            if event == "-CAPTURE-":
                self._handle_capture()
            elif event == "-FETCH-":
                self._handle_fetch(values)
            elif event == "-RESET-":
                self._handle_reset()
        self.window.close()

    def _handle_capture(self) -> None:
        try:
            self._set_status("화면 캡쳐 중...")
            image = capture.capture_fullscreen()
            screenshot_path = capture.save_image(image, Path.cwd() / "artifacts" / "raid_snapshot.png")
            characters = self.ocr_engine.extract_characters_from_image(image)
            self.snapshot = RaidSnapshot(characters=characters, screenshot_path=screenshot_path)
            self._update_table_from_characters(characters)
            self._log(f"캡쳐 완료: {screenshot_path}")
            if not characters:
                self._log("OCR 결과가 비어 있습니다. 텍스트 영역이 잘 보이도록 다시 캡쳐하세요.")
            self._set_status("캡쳐 완료")
        except Exception as exc:  # noqa: BLE001
            self._set_status("캡쳐 실패")
            self._log(f"오류: {exc}")

    def _handle_fetch(self, values: dict) -> None:
        if not self.snapshot or not self.snapshot.characters:
            self._log("먼저 캡쳐를 수행해 캐릭터를 추출하세요.")
            return

        template = values.get("-URL-TEMPLATE-") or ""
        characters = list(self.snapshot.characters)
        self._set_status("데미지 조회 중...")
        threading.Thread(target=self._fetch_damage_async, args=(template, characters), daemon=True).start()

    def _fetch_damage_async(self, template: str, characters: List[CharacterInfo]) -> None:
        damages: List[CharacterDamage] = []
        for info in characters:
            url = self._render_url(template, info.name)
            try:
                result = self.scraper.fetch_character_damage(url, name=info.name, job=info.job)
                damages.append(result)
                self._log(f"{info.name}: {result.damage}")
            except Exception as exc:  # noqa: BLE001
                self._log(f"{info.name} 조회 실패: {exc}")

        self.snapshot = RaidSnapshot(characters=characters, screenshot_path=self.snapshot.screenshot_path)
        self._update_table_from_damages(damages)
        self._set_status("조회 완료")

    def _handle_reset(self) -> None:
        self.snapshot = None
        self.window["-TABLE-"].update(values=[])
        self.window["-LOG-"].update("")
        self._set_status("대기 중")

    def _render_url(self, template: str, name: str) -> str:
        safe_name = urllib.parse.quote(name)
        return template.replace("{name}", safe_name)

    def _update_table_from_characters(self, characters: List[CharacterInfo]) -> None:
        rows = [[c.name, c.job or "", c.fame or "", ""] for c in characters]
        self.window["-TABLE-"].update(values=rows)

    def _update_table_from_damages(self, damages: List[CharacterDamage]) -> None:
        rows = [[d.name, d.job or "", d.fame or "", d.damage] for d in damages]
        self.window["-TABLE-"].update(values=rows)

    def _set_status(self, message: str) -> None:
        self.window["-STATUS-"].update(message)

    def _log(self, message: str) -> None:
        log_elem = self.window["-LOG-"]
        current = log_elem.get() or ""
        log_elem.update(current + message + "\n")


def main() -> None:
    app = RaidHelperApp()
    app.run()


if __name__ == "__main__":
    main()
