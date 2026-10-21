"""The Bot: the Mineflayer-style API surface an agent program talks to.

    bot = Bot(source, controller, detector=None)
    state = bot.observe()
    bot.health, bot.screen, bot.nearest_enemy(), bot.view()
    bot.move(x, y), bot.attack(), bot.roll(), bot.use_potion(), ...
    bot.on('damage' | 'death' | 'respawn', fn)
"""
from __future__ import annotations

import time

from . import perception
from .state import SCREEN_DEAD, GameState


class Bot:
    def __init__(self, source, controller, detector=None):
        self.source = source
        self.controller = controller
        self.detector = detector
        self._handlers: dict[str, list] = {}
        self._state: GameState | None = None
        self._frame = None
        self._was_dead = False

    # -- events -----------------------------------------------------------
    def on(self, event: str, fn):
        self._handlers.setdefault(event, []).append(fn)
        return fn

    def _emit(self, event: str, *args):
        for fn in self._handlers.get(event, []):
            fn(*args)

    # -- perception -------------------------------------------------------
    def observe(self) -> GameState:
        frame = self.source.grab()
        self._frame = frame
        prev = self._state
        state = GameState(
            health=perception.health_fraction(frame),
            screen=perception.classify_screen(frame),
            enemies=self.detector(frame) if self.detector else [],
            frame_shape=tuple(frame.shape),
            timestamp=time.time(),
        )
        if (
            prev is not None
            and prev.health is not None
            and state.health is not None
            and state.health < prev.health - 0.02
        ):
            self._emit("damage", prev.health, state.health)
        if state.screen == SCREEN_DEAD and not self._was_dead:
            self._emit("death", state)
        if state.screen != SCREEN_DEAD and self._was_dead:
            self._emit("respawn", state)
        self._was_dead = state.screen == SCREEN_DEAD
        self._state = state
        return state

    @property
    def health(self) -> float | None:
        return self._state.health if self._state else None

    @property
    def screen(self) -> str | None:
        return self._state.screen if self._state else None

    def nearest_enemy(self):
        if not self._state or not self._state.enemies:
            return None
        return min(
            self._state.enemies,
            key=lambda e: (e.x - 0.5) ** 2 + (e.y - 0.5) ** 2,
        )

    def view(self, size: int = 128):
        """Downscaled latest frame — the input a VLM policy would see."""
        if self._frame is None:
            self.observe()
        return perception.downscale(self._frame, size)

    # -- actions ------------------------------------------------------------
    def move(self, x: float, y: float, duration: float = 0.25):
        self.controller.move(x, y, duration)

    def attack(self):
        self.controller.attack()

    def roll(self):
        self.controller.roll()

    def use_artifact(self, slot: int = 1):
        self.controller.use_artifact(slot)

    def use_potion(self):
        self.controller.use_potion()

    def interact(self):
        self.controller.interact()
