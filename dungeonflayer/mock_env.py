"""A tiny synthetic 'game' for developing DungeonFlayer without Minecraft
Dungeons: renders frames with a real health bar (so the real perception
code reads it), one magenta enemy that walks at the player, and simple
combat/potion rules. The full observe -> decide -> act loop runs against
this in tests and on any laptop.
"""
from __future__ import annotations

import numpy as np

from .control import DryRunController
from .perception import HEALTH_BAR_REGION

BG = (24, 48, 32)  # dark green 'grass'
BAR_TROUGH = (100, 20, 20)  # dark red — must NOT trip the bright-red mask
BAR_FILL = (225, 45, 45)  # bright red — the mask's target
ENEMY_COLOR = (255, 0, 255)  # magenta — blob detector's target
PLAYER_COLOR = (240, 240, 240)
DEAD_COLOR = (140, 25, 25)


class MockEnv:
    def __init__(self, width: int = 640, height: int = 360):
        self.width, self.height = width, height
        self.player_health = 1.0
        self.dead = False
        self.kills = 0
        self._spawn_enemy()

    # -- world rules -----------------------------------------------------
    def _spawn_enemy(self):
        self.enemy_hp = 3
        self.enemy_dist = 260.0  # px right of the player
        self.enemy_alive = True
        self._respawn_timer = 0

    def apply_action(self, name: str, *args):
        if self.dead:
            if name == "interact":  # click through the death screen
                self.dead = False
                self.player_health = 1.0
                self._spawn_enemy()
            return
        if name == "potion":
            self.player_health = min(1.0, self.player_health + 0.55)
        elif name == "attack":
            if self.enemy_alive and self.enemy_dist < 110:
                self.enemy_hp -= 1
                if self.enemy_hp <= 0:
                    self.enemy_alive = False
                    self.kills += 1
                    self._respawn_timer = 6

    def _tick(self):
        if self.dead:
            return
        if self.enemy_alive:
            self.enemy_dist = max(28.0, self.enemy_dist - 9.0)
            if self.enemy_dist <= 40:
                self.player_health = max(0.0, self.player_health - 0.02)
                if self.player_health <= 0.0:
                    self.dead = True
        else:
            self._respawn_timer -= 1
            if self._respawn_timer <= 0:
                self._spawn_enemy()

    # -- rendering --------------------------------------------------------
    def render(self) -> np.ndarray:
        self._tick()
        w, h = self.width, self.height
        if self.dead:
            frame = np.zeros((h, w, 3), dtype=np.uint8)
            frame[:] = DEAD_COLOR
            return frame
        frame = np.zeros((h, w, 3), dtype=np.uint8)
        frame[:] = BG
        # health bar: trough + bright fill, inside HEALTH_BAR_REGION
        rx, ry, rw, rh = HEALTH_BAR_REGION
        x0, y0 = int(rx * w), int(ry * h)
        x1, y1 = int((rx + rw) * w), int((ry + rh) * h)
        frame[y0:y1, x0:x1] = BAR_TROUGH
        fill = int((x1 - x0) * self.player_health)
        frame[y0:y1, x0 : x0 + fill] = BAR_FILL
        # player: white square, screen center
        cx, cy = w // 2, h // 2
        frame[cy - 6 : cy + 6, cx - 6 : cx + 6] = PLAYER_COLOR
        # enemy: magenta square approaching from the right
        if self.enemy_alive:
            ex = int(cx + self.enemy_dist)
            if ex + 8 < w:
                frame[cy - 8 : cy + 8, ex - 8 : ex + 8] = ENEMY_COLOR
        return frame


class MockController(DryRunController):
    """Dry-run controller that also feeds actions into a MockEnv, closing
    the loop: agent acts -> world changes -> next frame shows it."""

    def __init__(self, env: MockEnv):
        super().__init__(realtime=False)
        self.env = env

    def move(self, x, y, duration=0.25):
        super().move(x, y, duration)
        self.env.apply_action("move", x, y)

    def attack(self):
        super().attack()
        self.env.apply_action("attack")

    def roll(self):
        super().roll()
        self.env.apply_action("roll")

    def use_artifact(self, slot=1):
        super().use_artifact(slot)
        self.env.apply_action("artifact", slot)

    def use_potion(self):
        super().use_potion()
        self.env.apply_action("potion")

    def interact(self):
        super().interact()
        self.env.apply_action("interact")
