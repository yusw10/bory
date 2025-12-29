from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CharacterInfo:
    name: str
    job: str | None = None
    fame: int | None = None


@dataclass
class CharacterDamage:
    name: str
    damage: str
    job: str | None = None
    fame: int | None = None


@dataclass
class RaidSnapshot:
    characters: list[CharacterInfo]
    screenshot_path: str | None = None
