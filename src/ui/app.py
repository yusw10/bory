from __future__ import annotations

import logging
import threading
import tkinter as tk
import urllib.parse
from pathlib import Path
from tkinter import ttk

from src.core.config import AppConfig
from src.core.models import CharacterDamage, CharacterInfo, RaidSnapshot
from src.core.ocr import OcrEngine
from src.core.scraper import DundamScraper
from src.io import capture

logger = logging.getLogger(__name__)


class RaidHelperApp:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.ocr_engine = OcrEngine(language=config.ocr_language)
        self.scraper = DundamScraper(
            request_timeout=config.request_timeout,
            max_retries=config.request_max_retries,
            retry_backoff=config.request_retry_backoff,
        )
        self.snapshot: RaidSnapshot | None = None

        self.root = tk.Tk()
        self.root.title("던담 공대원 데미지 도우미")
        self.root.protocol("WM_DELETE_WINDOW", self._handle_exit)

        base_url = self.config.dundam_base_url.rstrip("/")
        default_template = f"{base_url}/character?server=hilder&key={{name}}"
        self.url_var = tk.StringVar(value=default_template)
        self.status_var = tk.StringVar(value="대기 중")

        self._build_window()

    def _build_window(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        main = ttk.Frame(self.root, padding=10)
        main.grid(row=0, column=0, sticky="nsew")
        main.columnconfigure(1, weight=1)
        main.rowconfigure(3, weight=1)
        main.rowconfigure(4, weight=1)

        ttk.Label(main, text="던담 URL 템플릿").grid(row=0, column=0, sticky="w")
        url_entry = ttk.Entry(main, textvariable=self.url_var)
        url_entry.grid(row=0, column=1, sticky="ew", padx=(8, 0))

        button_frame = ttk.Frame(main)
        button_frame.grid(row=1, column=0, columnspan=2, pady=(8, 0), sticky="w")
        ttk.Button(button_frame, text="시작(캡쳐)", command=self._handle_capture).grid(
            row=0, column=0, padx=(0, 6)
        )
        ttk.Button(button_frame, text="데미지 조회", command=self._handle_fetch).grid(
            row=0, column=1, padx=(0, 6)
        )
        ttk.Button(button_frame, text="초기화", command=self._handle_reset).grid(
            row=0, column=2, padx=(0, 6)
        )
        ttk.Button(button_frame, text="종료", command=self._handle_exit).grid(
            row=0, column=3
        )

        ttk.Label(main, text="상태").grid(row=2, column=0, sticky="w", pady=(8, 0))
        ttk.Label(main, textvariable=self.status_var).grid(
            row=2, column=1, sticky="w", padx=(8, 0), pady=(8, 0)
        )

        table_frame = ttk.Frame(main)
        table_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=(8, 0))
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        columns = ("name", "job", "fame", "damage")
        self.table = ttk.Treeview(
            table_frame, columns=columns, show="headings", height=8
        )
        self.table.heading("name", text="이름")
        self.table.heading("job", text="직업")
        self.table.heading("fame", text="명성")
        self.table.heading("damage", text="총딜")
        self.table.column("name", width=150, anchor="w")
        self.table.column("job", width=150, anchor="w")
        self.table.column("fame", width=80, anchor="center")
        self.table.column("damage", width=120, anchor="w")

        table_scroll = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.table.yview
        )
        self.table.configure(yscrollcommand=table_scroll.set)
        self.table.grid(row=0, column=0, sticky="nsew")
        table_scroll.grid(row=0, column=1, sticky="ns")

        log_frame = ttk.Frame(main)
        log_frame.grid(row=4, column=0, columnspan=2, sticky="nsew", pady=(8, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_text = tk.Text(log_frame, height=8, state="disabled")
        log_scroll = ttk.Scrollbar(
            log_frame, orient="vertical", command=self.log_text.yview
        )
        self.log_text.configure(yscrollcommand=log_scroll.set)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        log_scroll.grid(row=0, column=1, sticky="ns")

    def run(self) -> None:
        self.root.mainloop()

    def _handle_capture(self) -> None:
        try:
            self._set_status("화면 캡쳐 중...")
            logger.info("Starting capture.")
            image = capture.capture_fullscreen()
            screenshot_path = capture.save_image(
                image, Path.cwd() / "artifacts" / "raid_snapshot.png"
            )
            characters = self.ocr_engine.extract_characters_from_image(image)
            self.snapshot = RaidSnapshot(
                characters=characters, screenshot_path=screenshot_path
            )
            self._update_table_from_characters(characters)
            self._log(f"캡쳐 완료: {screenshot_path}")
            if not characters:
                self._log(
                    "OCR 결과가 비어 있습니다. 텍스트 영역이 잘 보이도록 다시 캡쳐하세요."
                )
            self._set_status("캡쳐 완료")
            logger.info("Capture completed with %s characters.", len(characters))
        except Exception as exc:  # noqa: BLE001
            self._set_status("캡쳐 실패")
            self._log(f"오류: {exc}")
            logger.exception("Capture failed.")

    def _handle_fetch(self) -> None:
        if not self.snapshot or not self.snapshot.characters:
            self._log("먼저 캡쳐를 수행해 캐릭터를 추출하세요.")
            logger.warning("Fetch requested before capture.")
            return

        template = self.url_var.get() or ""
        characters = list(self.snapshot.characters)
        self._set_status("데미지 조회 중...")
        logger.info("Starting fetch for %s characters.", len(characters))
        threading.Thread(
            target=self._fetch_damage_async, args=(template, characters), daemon=True
        ).start()

    def _fetch_damage_async(
        self, template: str, characters: list[CharacterInfo]
    ) -> None:
        damages: list[CharacterDamage] = []
        for info in characters:
            url = self._render_url(template, info.name)
            try:
                result = self.scraper.fetch_character_damage(
                    url, name=info.name, job=info.job
                )
                damages.append(result)
                self._log(f"{info.name}: {result.damage}")
            except Exception as exc:  # noqa: BLE001
                self._log(f"{info.name} 조회 실패: {exc}")
                logger.warning("Fetch failed for %s: %s", info.name, exc)

        self.root.after(0, self._finalize_fetch, characters, damages)

    def _finalize_fetch(
        self, characters: list[CharacterInfo], damages: list[CharacterDamage]
    ) -> None:
        self.snapshot = RaidSnapshot(
            characters=characters, screenshot_path=self.snapshot.screenshot_path
        )
        self._update_table_from_damages(damages)
        self._set_status("조회 완료")
        logger.info("Fetch completed with %s results.", len(damages))

    def _handle_reset(self) -> None:
        self.snapshot = None
        self._update_table_from_characters([])
        self._clear_log()
        self._set_status("대기 중")

    def _handle_exit(self) -> None:
        self.root.destroy()

    def _render_url(self, template: str, name: str) -> str:
        safe_name = urllib.parse.quote(name)
        return template.replace("{name}", safe_name)

    def _update_table_from_characters(self, characters: list[CharacterInfo]) -> None:
        rows = [[c.name, c.job or "", c.fame or "", ""] for c in characters]
        self._set_table_rows(rows)

    def _update_table_from_damages(self, damages: list[CharacterDamage]) -> None:
        rows = [[d.name, d.job or "", d.fame or "", d.damage] for d in damages]
        self._set_table_rows(rows)

    def _set_table_rows(self, rows: list[list[str]]) -> None:
        def update():
            for item in self.table.get_children():
                self.table.delete(item)
            for row in rows:
                self.table.insert("", "end", values=row)

        self.root.after(0, update)

    def _set_status(self, message: str) -> None:
        self.root.after(0, self.status_var.set, message)

    def _log(self, message: str) -> None:
        def append():
            self.log_text.configure(state="normal")
            self.log_text.insert("end", message + "\n")
            self.log_text.see("end")
            self.log_text.configure(state="disabled")

        self.root.after(0, append)

    def _clear_log(self) -> None:
        def clear():
            self.log_text.configure(state="normal")
            self.log_text.delete("1.0", "end")
            self.log_text.configure(state="disabled")

        self.root.after(0, clear)


def main(config: AppConfig | None = None) -> None:
    app = RaidHelperApp(config or AppConfig())
    app.run()


if __name__ == "__main__":
    main()
