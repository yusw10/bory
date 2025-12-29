from __future__ import annotations

import re
from collections.abc import Iterable

import requests
from bs4 import BeautifulSoup

from src.core.models import CharacterDamage


class DundamScraper:
    """던담 사이트에서 공대원 데미지(총딜)를 가져오는 간단한 스크래퍼.

    - HTML 구조가 자주 변할 수 있으므로, 문자열 패턴 기반의 안전한 파서를 사용한다.
    - 네트워크 실패 시 requests 예외를 그대로 올리며, UI 계층에서 처리한다.
    """

    def __init__(self, session: requests.Session | None = None) -> None:
        self.session = session or requests.Session()

    def fetch_html(self, url: str) -> str:
        response = self.session.get(url, timeout=10)
        response.raise_for_status()
        return response.text

    def parse_total_damage(self, html: str) -> str:
        """HTML에서 '총딜' 키워드가 포함된 숫자/단위를 추출한다.

        반환 예: "12.3조", "845억" 등 문자열 그대로.
        찾을 수 없으면 ValueError를 발생시킨다.
        """

        soup = BeautifulSoup(html, "lxml")

        # 1) 텍스트 노드에 '총딜'이 포함된 경우 주변 숫자를 찾는다.
        text_nodes = soup.find_all(string=re.compile("총딜"))
        for text_node in text_nodes:
            candidate = self._extract_damage_from_text(text_node)
            if candidate:
                return candidate
            # 부모 요소에 숫자가 있을 수 있다.
            if text_node.parent:
                parent_text = text_node.parent.get_text(" ", strip=True)
                candidate = self._extract_damage_from_text(parent_text)
                if candidate:
                    return candidate

        # 2) 숫자+단위 패턴만 있는 경우(백업 전략)
        body_text = soup.get_text(" ", strip=True)
        candidate = self._extract_damage_from_text(body_text)
        if candidate:
            return candidate

        raise ValueError("총딜 정보를 찾을 수 없습니다.")

    def _extract_damage_from_text(self, text: str) -> str | None:
        # 예시 패턴: "총딜 12.3조", "총딜: 845억", "총딜=1,234,567,890"
        pattern = r"총딜\s*[:=]?\s*([0-9][0-9,\.]*\s*(?:조|억|만|))"
        match = re.search(pattern, text)
        if match:
            return match.group(1).replace(" ", "")

        # 단순 숫자만 있는 경우(단위 없음)
        unitless_pattern = r"총딜\s*[:=]?\s*([0-9][0-9,\.]*)(?!\S)"
        match = re.search(unitless_pattern, text)
        if match:
            return match.group(1).replace(" ", "")
        return None

    def fetch_character_damage(
        self, url: str, name: str, job: str | None = None
    ) -> CharacterDamage:
        html = self.fetch_html(url)
        total_damage = self.parse_total_damage(html)
        return CharacterDamage(name=name, job=job, damage=total_damage)

    def fetch_many(
        self, urls: Iterable[tuple[str, str, str | None]]
    ) -> list[CharacterDamage]:
        results: list[CharacterDamage] = []
        for url, name, job in urls:
            results.append(self.fetch_character_damage(url, name, job))
        return results
