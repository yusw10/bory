from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CharacterInfo:
    name: str
    job: Optional[str] = None
    fame: Optional[int] = None


@dataclass
class CharacterDamage:
    name: str
    damage: str
    job: Optional[str] = None
    fame: Optional[int] = None


@dataclass
class RaidSnapshot:
    characters: List[CharacterInfo]
    screenshot_path: Optional[str] = None
