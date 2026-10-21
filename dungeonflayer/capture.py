"""Frame sources. A source is anything with .grab() -> HxWx3 uint8 RGB array.

Backends:
  mock   — renders the synthetic MockEnv (development, tests, CI)
  mss    — cross-platform screen grab (pip install mss)
  dxcam  — high-fps Windows capture (pip install dxcam), preferred live
"""
from __future__ import annotations

import numpy as np


class MockSource:
    def __init__(self, env):
        self.env = env

    def grab(self) -> np.ndarray:
        return self.env.render()


class MSSSource:
    def __init__(self, region=None):
        import mss  # lazy: only needed for live capture

        self._mss = mss.mss()
        self.region = region

    def grab(self) -> np.ndarray:
        shot = self._mss.grab(self.region or self._mss.monitors[1])
        arr = np.asarray(shot)  # BGRA
        return arr[:, :, :3][:, :, ::-1].copy()  # -> RGB


class DXCamSource:
    """Windows-only, high frame rate. Preferred for live runs."""

    def __init__(self):
        import dxcam  # lazy, Windows-only

        self._cam = dxcam.create(output_color="RGB")
        self._cam.start()

    def grab(self) -> np.ndarray:
        frame = self._cam.get_latest_frame()
        return np.asarray(frame)


def make_source(kind: str = "mock", **kwargs):
    if kind == "mock":
        return MockSource(kwargs["env"])
    if kind == "mss":
        return MSSSource(kwargs.get("region"))
    if kind == "dxcam":
        return DXCamSource()
    raise ValueError(f"unknown source kind: {kind!r}")
