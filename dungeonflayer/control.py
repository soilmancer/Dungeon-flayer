"""Controllers: the 'hands'. Every action an agent can take goes through here.

Backends:
  DryRunController      — logs actions, touches nothing (default, safe)
  GamepadController     — virtual Xbox controller via ViGEmBus/vgamepad (Windows)
  KeyboardMouseController — pydirectinput click-to-move fallback (Windows)

Coordinate convention for move(x, y): stick direction in screen terms,
x in [-1, 1] (right positive), y in [-1, 1] (DOWN positive, like pixels),
held for `duration` seconds.
"""
from __future__ import annotations

import time


class Controller:
    def move(self, x: float, y: float, duration: float = 0.25):
        raise NotImplementedError

    def attack(self):
        raise NotImplementedError

    def roll(self):
        raise NotImplementedError

    def use_artifact(self, slot: int = 1):
        raise NotImplementedError

    def use_potion(self):
        raise NotImplementedError

    def interact(self):
        raise NotImplementedError


class DryRunController(Controller):
    """Records every action in .actions; optionally sleeps in real time."""

    def __init__(self, realtime: bool = False):
        self.actions: list[tuple] = []
        self.realtime = realtime

    def _log(self, name, *args):
        self.actions.append((name, *args))

    def move(self, x, y, duration=0.25):
        self._log("move", round(float(x), 3), round(float(y), 3), duration)
        if self.realtime:
            time.sleep(duration)

    def attack(self):
        self._log("attack")

    def roll(self):
        self._log("roll")

    def use_artifact(self, slot=1):
        self._log("artifact", int(slot))

    def use_potion(self):
        self._log("potion")

    def interact(self):
        self._log("interact")


# Default Xbox-controller mapping for Minecraft Dungeons.
# *** VERIFY against the in-game controller settings before the first live
# run and fix this dict — do not trust it blind. ***
BUTTONS = {
    "attack": "XUSB_GAMEPAD_X",
    "roll": "XUSB_GAMEPAD_A",
    "interact": "XUSB_GAMEPAD_B",
    "potion": "XUSB_GAMEPAD_LEFT_SHOULDER",
    "artifact1": "XUSB_GAMEPAD_RIGHT_SHOULDER",
    "artifact2": "XUSB_GAMEPAD_Y",
    "artifact3": "XUSB_GAMEPAD_DPAD_DOWN",
}


class GamepadController(Controller):
    """Virtual Xbox 360 controller (Windows; requires ViGEmBus driver)."""

    def __init__(self):
        import vgamepad as vg  # lazy, Windows-only

        self._vg = vg
        self.pad = vg.VX360Gamepad()

    def _press(self, key: str, hold: float = 0.08):
        btn = getattr(self._vg.XUSB_BUTTON, BUTTONS[key])
        self.pad.press_button(button=btn)
        self.pad.update()
        time.sleep(hold)
        self.pad.release_button(button=btn)
        self.pad.update()

    def move(self, x, y, duration=0.25):
        # vgamepad stick Y is up-positive; our convention is down-positive.
        self.pad.left_joystick_float(x_value_float=float(x), y_value_float=-float(y))
        self.pad.update()
        time.sleep(duration)
        self.pad.left_joystick_float(x_value_float=0.0, y_value_float=0.0)
        self.pad.update()

    def attack(self):
        self._press("attack")

    def roll(self):
        self._press("roll")

    def use_artifact(self, slot=1):
        self._press(f"artifact{int(slot)}")

    def use_potion(self):
        self._press("potion")

    def interact(self):
        self._press("interact")


class KeyboardMouseController(Controller):
    """Fallback: Dungeons on PC is click-to-move. Needs the game window's
    screen rectangle so clicks land relative to the window."""

    def __init__(self, window_rect=(0, 0, 1920, 1080)):
        import pydirectinput  # lazy, Windows-oriented

        self._pdi = pydirectinput
        self._pdi.FAILSAFE = True  # slam mouse to a corner to abort
        self.x0, self.y0, self.w, self.h = window_rect

    def _click(self, px, py):
        self._pdi.click(int(px), int(py))

    def move(self, x, y, duration=0.25):
        cx, cy = self.x0 + self.w / 2, self.y0 + self.h / 2
        self._click(cx + x * self.w * 0.18, cy + y * self.h * 0.18)
        time.sleep(duration)

    def attack(self):
        cx, cy = self.x0 + self.w / 2, self.y0 + self.h / 2
        self._click(cx, cy)

    def roll(self):
        self._pdi.press("space")

    def use_artifact(self, slot=1):
        self._pdi.press(str(int(slot)))

    def use_potion(self):
        self._pdi.press("q")

    def interact(self):
        cx, cy = self.x0 + self.w / 2, self.y0 + self.h / 2
        self._click(cx, cy)
