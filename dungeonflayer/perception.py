"""Perception: turn raw frames (HxWx3 uint8 RGB) into estimated game state.

v0 is deliberately boring computer vision — no ML yet:
  * health fraction from the red HUD bar (column-fill method)
  * screen classification from brightness / red-wash heuristics
  * a color-blob detector (toy detector, also the mock env's ground truth)
  * nearest-neighbour downscale for feeding frames to a VLM later
"""
from __future__ import annotations

import numpy as np

from .state import SCREEN_DEAD, SCREEN_IN_GAME, SCREEN_LOADING, SCREEN_UNKNOWN, Enemy

# Health bar location as relative (x, y, w, h) of the frame.
# Bottom-left HUD in Minecraft Dungeons. VERIFY against the real HUD on
# first live run and adjust — this is the single most important constant
# in the project.
HEALTH_BAR_REGION = (0.030, 0.855, 0.205, 0.045)


def _crop(frame: np.ndarray, region) -> np.ndarray:
    h, w = frame.shape[:2]
    x, y, rw, rh = region
    x0, y0 = int(x * w), int(y * h)
    x1, y1 = max(x0 + 1, int((x + rw) * w)), max(y0 + 1, int((y + rh) * h))
    return frame[y0:y1, x0:x1]


def _red_mask(arr: np.ndarray) -> np.ndarray:
    a = arr.astype(np.int16)
    return (a[..., 0] > 110) & (a[..., 0] - a[..., 1] > 45) & (a[..., 0] - a[..., 2] > 45)


def health_fraction(frame: np.ndarray, region=HEALTH_BAR_REGION) -> float | None:
    """Fraction of the health bar that is filled, 0..1, or None if unreadable.

    Column-fill method: a column counts as filled if the bar's vertical
    middle band contains bright red in that column. Robust to the exact
    bar height and to icons overlapping the top/bottom edges.
    """
    if frame is None or frame.size == 0:
        return None
    crop = _crop(frame, region)
    if crop.size == 0:
        return None
    mask = _red_mask(crop)
    rows = crop.shape[0]
    mid = mask[rows // 4 : (3 * rows // 4) + 1, :]
    if mid.size == 0:
        return None
    return float(mid.any(axis=0).mean())


def classify_screen(frame: np.ndarray) -> str:
    """Heuristic screen classifier (v0)."""
    if frame is None or frame.size == 0:
        return SCREEN_UNKNOWN
    if float(frame.astype(np.float32).mean()) < 8.0:
        return SCREEN_LOADING  # near-black frame: loading / transition
    top = frame[: int(frame.shape[0] * 0.8)]  # exclude HUD band
    if float(_red_mask(top).mean()) > 0.45:
        return SCREEN_DEAD  # full-frame red wash: death screen
    return SCREEN_IN_GAME


def downscale(frame: np.ndarray, size: int = 128) -> np.ndarray:
    """Nearest-neighbour resize to size x size (keeps HxWx3 shape)."""
    h, w = frame.shape[:2]
    ys = np.linspace(0, h - 1, size).astype(int)
    xs = np.linspace(0, w - 1, size).astype(int)
    return frame[np.ix_(ys, xs)]


def blob_detector(target_rgb=(255, 0, 255), tol: int = 60, min_pixels: int = 12):
    """Return a detector function frame -> [Enemy] for one saturated color.

    Toy detector: finds the centroid of all pixels close to target_rgb.
    Good enough for the mock environment and as a pipeline sanity check;
    Phase 2 replaces it with a learned detector. Known limitation: two
    same-colored blobs merge into one centroid.
    """
    target = np.array(target_rgb, dtype=np.int16)

    def detect(frame: np.ndarray) -> list[Enemy]:
        if frame is None or frame.size == 0:
            return []
        diff = np.abs(frame.astype(np.int16) - target).max(axis=2)
        mask = diff <= tol
        count = int(mask.sum())
        if count < min_pixels:
            return []
        ys, xs = np.nonzero(mask)
        h, w = frame.shape[:2]
        return [
            Enemy(
                x=float(xs.mean()) / w,
                y=float(ys.mean()) / h,
                confidence=min(1.0, count / 200.0),
                kind="blob",
            )
        ]

    return detect
