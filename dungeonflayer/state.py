"""Shared state types for DungeonFlayer.

Everything in here is *estimated* state: values inferred from screenshots,
never read from the game. Any field may be missing/None when perception
could not read it — agents must cope, the API never fabricates.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

SCREEN_IN_GAME = "in_game"
SCREEN_LOADING = "loading"
SCREEN_DEAD = "dead"
SCREEN_MENU = "menu"
SCREEN_UNKNOWN = "unknown"


@dataclass
class Enemy:
    """A detected enemy, in normalized screen coordinates (0..1)."""

    x: float
    y: float
    confidence: float
    kind: str = "unknown"


@dataclass
class GameState:
    health: float | None  # 0..1 fraction of the health bar, None if unreadable
    screen: str  # one of the SCREEN_* constants
    enemies: list[Enemy] = field(default_factory=list)
    frame_shape: tuple = ()
    timestamp: float = field(default_factory=time.time)
