"""
backgrounds.py — Pixel-perfect, aspect-fill game backgrounds for Oblivio.

Loads Hellish / Scorched / Mortal art, scales with uniform cover (no stretch),
anchors bottom-center (ground stays visible; sky and sides crop), and uses
nearest-neighbour scaling only.

Engine setup (call before pygame.init() — see main.py):
    os.environ["SDL_RENDER_SCALE_QUALITY"] = "0"   # nearest / point filtering
"""

from __future__ import annotations

import math
import os
from enum import Enum, auto

import pygame

_HERE = os.path.dirname(__file__)
_BG_DIR = os.path.join(_HERE, "game-assets", "backgrounds")

# Source filenames (lowercase on disk)
_ASSET_FILES: dict[str, str] = {
    "default":  "default.png",
    "hellish":  "hellish.png",
    "scorched": "scorched.png",
    "mortal":   "mortal.png",
}


class BackgroundId(Enum):
    """Background themes — swap at runtime via set_active() / set_default()."""
    DEFAULT  = auto()   # menu, codex, settings
    HELLISH  = auto()
    SCORCHED = auto()
    MORTAL   = auto()


# ---------------------------------------------------------------------------
# Internal state
# ---------------------------------------------------------------------------
_sources: dict[BackgroundId, pygame.Surface] = {}
_active: BackgroundId = BackgroundId.DEFAULT
# Cache: (active, viewport_w, viewport_h) -> (scaled_surface, blit_xy)
_scaled_cache: tuple[BackgroundId, int, int] | None = None
_scaled_surf: pygame.Surface | None = None
_blit_pos: tuple[int, int] = (0, 0)


def init() -> None:
    """Load all background PNGs. Call once after pygame.display is available."""
    global _sources
    if _sources:
        return

    if not pygame.display.get_init():
        pygame.display.init()

    for bg_id, key in (
        (BackgroundId.DEFAULT,  "default"),
        (BackgroundId.HELLISH,  "hellish"),
        (BackgroundId.SCORCHED, "scorched"),
        (BackgroundId.MORTAL,   "mortal"),
    ):
        path = os.path.join(_BG_DIR, _ASSET_FILES[key])
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Background asset missing: {path}")
        surf = pygame.image.load(path)
        # Opaque pixel art — convert() avoids alpha bleed and matches display format
        _sources[bg_id] = surf.convert()


def set_default() -> None:
    """Menu / codex / settings backdrop."""
    set_active(BackgroundId.DEFAULT)


def set_active(bg: BackgroundId) -> None:
    """Switch the active background (invalidates the scale cache)."""
    global _active
    if bg not in _sources and _sources:
        raise ValueError(f"Unknown background: {bg}")
    if bg == _active and _scaled_cache is not None:
        return
    _active = bg
    invalidate_cache()


_GRID_INDEX_TO_BG: dict[int, BackgroundId] = {
    0: BackgroundId.MORTAL,
    1: BackgroundId.SCORCHED,
    2: BackgroundId.HELLISH,
}


def set_for_grid_index(index: int) -> None:
    """Map difficulty-select row (0–2) to Mortal / Scorched / Hellish preview."""
    bg = _GRID_INDEX_TO_BG.get(index)
    if bg is not None:
        set_active(bg)


def set_for_difficulty(difficulty) -> None:
    """
    Map game difficulty to background theme.
    Easy → Mortal, Medium → Scorched, Hard → Hellish.
    """
    from game import Difficulty

    if difficulty == Difficulty.EASY:
        set_active(BackgroundId.MORTAL)
    elif difficulty == Difficulty.MEDIUM:
        set_active(BackgroundId.SCORCHED)
    else:
        set_active(BackgroundId.HELLISH)


def invalidate_cache() -> None:
    """Drop cached scaled surface (call after resolution / display changes)."""
    global _scaled_cache, _scaled_surf, _effect_layer, _effect_layer_size
    _scaled_cache = None
    _scaled_surf = None
    _effect_layer = None
    _effect_layer_size = (0, 0)


def _cover_layout(src_w: int, src_h: int, vw: int, vh: int) -> tuple[int, int, int, int]:
    """
    Uniform aspect-fill scale + bottom-center anchor.

    Returns (scaled_w, scaled_h, blit_x, blit_y).
    blit_y may be negative (crop sky); blit_x may be negative (crop sides).
    """
    if src_w <= 0 or src_h <= 0 or vw <= 0 or vh <= 0:
        return vw, vh, 0, 0

    scale = max(vw / src_w, vh / src_h)
    scaled_w = max(vw, int(math.ceil(src_w * scale)))
    scaled_h = max(vh, int(math.ceil(src_h * scale)))
    blit_x = (vw - scaled_w) // 2
    blit_y = vh - scaled_h
    return scaled_w, scaled_h, blit_x, blit_y


def _rebuild_scaled(vw: int, vh: int) -> None:
    """Scale active source with nearest-neighbour (pygame.transform.scale)."""
    global _scaled_cache, _scaled_surf, _blit_pos

    src = _sources.get(_active)
    if src is None:
        return

    src_w, src_h = src.get_size()
    sw, sh, bx, by = _cover_layout(src_w, src_h, vw, vh)
    # scale() = nearest neighbour; never use smoothscale() for pixel art
    _scaled_surf = pygame.transform.scale(src, (sw, sh))
    _blit_pos = (bx, by)
    _scaled_cache = (_active, vw, vh)


# ---------------------------------------------------------------------------
# Atmospheric overlays (drawn above the art, below UI veils)
# ---------------------------------------------------------------------------
_effect_layer: pygame.Surface | None = None
_effect_layer_size: tuple[int, int] = (0, 0)

# (x_ratio, y_ratio, phase, drift_y, size_px, rgba)
_EMBERS_HELLISH = (
    (0.12, 0.72, 0.0, 0.0009, 2, (255, 90, 20, 55)),
    (0.28, 0.81, 1.2, 0.0011, 2, (255, 50, 10, 50)),
    (0.45, 0.68, 2.4, 0.0008, 3, (255, 120, 30, 45)),
    (0.61, 0.77, 0.8, 0.0010, 2, (220, 40, 8, 48)),
    (0.78, 0.85, 3.1, 0.0012, 2, (255, 70, 15, 42)),
    (0.88, 0.70, 1.7, 0.0007, 3, (255, 100, 25, 40)),
    (0.35, 0.90, 4.0, 0.0013, 1, (255, 140, 40, 38)),
    (0.55, 0.92, 2.9, 0.0010, 2, (255, 60, 12, 44)),
    (0.70, 0.65, 0.5, 0.0009, 2, (200, 30, 5, 36)),
    (0.18, 0.88, 3.6, 0.0011, 1, (255, 110, 35, 35)),
)

_EMBERS_SCORCHED = (
    (0.15, 0.78, 0.3, 0.0007, 2, (255, 130, 40, 42)),
    (0.32, 0.86, 1.5, 0.0008, 2, (255, 100, 25, 38)),
    (0.50, 0.74, 2.1, 0.0006, 2, (230, 80, 20, 36)),
    (0.68, 0.82, 0.9, 0.0009, 2, (255, 115, 35, 40)),
    (0.82, 0.76, 2.8, 0.0007, 1, (255, 150, 50, 32)),
    (0.42, 0.91, 3.4, 0.0008, 1, (255, 90, 20, 34)),
)

_MOTES_MORTAL = (
    (0.20, 0.35, 0.0, 0.0005, 2, (180, 210, 230, 28)),
    (0.38, 0.28, 1.4, 0.0004, 1, (160, 195, 220, 24)),
    (0.55, 0.42, 2.2, 0.0006, 2, (200, 225, 240, 26)),
    (0.72, 0.32, 0.7, 0.0005, 1, (170, 200, 225, 22)),
    (0.85, 0.38, 3.0, 0.0004, 2, (190, 215, 235, 25)),
    (0.30, 0.48, 2.5, 0.0005, 1, (150, 185, 210, 20)),
    (0.62, 0.22, 1.1, 0.0004, 2, (175, 205, 228, 23)),
    (0.48, 0.18, 3.8, 0.0003, 1, (165, 195, 218, 18)),
)

_MOTES_DEFAULT = (
    (0.25, 0.55, 0.5, 0.0003, 1, (140, 120, 160, 22)),
    (0.50, 0.45, 1.8, 0.00035, 1, (120, 100, 150, 18)),
    (0.75, 0.50, 2.6, 0.0003, 1, (130, 110, 155, 20)),
    (0.40, 0.62, 3.2, 0.00028, 1, (110, 90, 140, 16)),
)


def _ensure_effect_layer(vw: int, vh: int) -> pygame.Surface:
    global _effect_layer, _effect_layer_size
    if _effect_layer is None or _effect_layer_size != (vw, vh):
        _effect_layer = pygame.Surface((vw, vh), pygame.SRCALPHA)
        _effect_layer_size = (vw, vh)
    else:
        _effect_layer.fill((0, 0, 0, 0))
    return _effect_layer


def _blit_particles(
    layer: pygame.Surface,
    vw: int,
    vh: int,
    t: float,
    specs: tuple,
) -> None:
    for xr, yr, phase, drift, size, rgba in specs:
        y = (yr - ((t + phase * 40) * drift) % 1.2) % 1.2
        if y > 1.0:
            continue
        x = xr + 0.012 * math.sin(t * 0.04 + phase * 2.1)
        px = int(x * vw) & ~1
        py = int(y * vh) & ~1
        flicker = 0.75 + 0.25 * math.sin(t * 0.08 + phase)
        a = max(0, min(255, int(rgba[3] * flicker)))
        pygame.draw.rect(layer, (*rgba[:3], a), (px, py, size, size))


def _mist_blobs(
    layer: pygame.Surface,
    vw: int,
    vh: int,
    t: float,
    blobs: tuple[tuple[float, float, float, tuple[int, int, int, int]]],
) -> None:
    for xr, yr, br_ratio, rgba in blobs:
        ox = int(12 * math.sin(t * 0.025 + xr * 10))
        oy = int(8 * math.cos(t * 0.02 + yr * 8))
        cx = int(xr * vw) + ox
        cy = int(yr * vh) + oy
        br = int(br_ratio * min(vw, vh) * (1.0 + 0.05 * math.sin(t * 0.03 + xr)))
        pygame.draw.circle(layer, rgba, (cx, cy), max(8, br))


def _heat_shimmer(
    layer: pygame.Surface,
    vw: int,
    vh: int,
    t: float,
    band_count: int,
    alpha: int,
) -> None:
    for i in range(band_count):
        y_ratio = 0.55 + i * 0.08
        y = int(y_ratio * vh) + int(3 * math.sin(t * 0.06 + i * 1.7))
        y &= ~1
        shift = int(4 * math.sin(t * 0.05 + i * 2.3))
        a = alpha + int(6 * math.sin(t * 0.07 + i))
        pygame.draw.rect(
            layer,
            (255, 140, 60, max(0, min(255, a))),
            (shift, y, vw, 2),
        )


def _tint_pulse(layer: pygame.Surface, vw: int, vh: int, t: float, rgba: tuple[int, int, int, int]) -> None:
    pulse = 0.5 + 0.5 * math.sin(t * 0.04)
    a = int(rgba[3] * (0.65 + 0.35 * pulse))
    layer.fill((*rgba[:3], max(0, min(255, a))))


def _draw_fx_default(layer: pygame.Surface, vw: int, vh: int, t: float) -> None:
    _mist_blobs(
        layer, vw, vh, t,
        (
            (0.35, 0.72, 0.22, (35, 20, 50, 18)),
            (0.65, 0.78, 0.18, (28, 15, 42, 14)),
            (0.50, 0.35, 0.14, (22, 12, 38, 10)),
        ),
    )
    _blit_particles(layer, vw, vh, t, _MOTES_DEFAULT)
    torch = int(28 + 10 * math.sin(t * 0.09))
    for tx in (int(vw * 0.08), int(vw * 0.92)):
        pygame.draw.rect(layer, (255, 160, 70, torch), (tx, int(vh * 0.62) & ~1, 2, 2))
        pygame.draw.rect(layer, (255, 100, 30, torch // 2), (tx, (int(vh * 0.62) + 4) & ~1, 1, 1))


def _draw_fx_mortal(layer: pygame.Surface, vw: int, vh: int, t: float) -> None:
    _tint_pulse(layer, vw, vh, t, (40, 55, 75, 8))
    _mist_blobs(
        layer, vw, vh, t,
        (
            (0.40, 0.30, 0.20, (60, 80, 100, 16)),
            (0.60, 0.25, 0.16, (50, 70, 95, 12)),
            (0.30, 0.55, 0.24, (45, 65, 90, 14)),
        ),
    )
    _blit_particles(layer, vw, vh, t, _MOTES_MORTAL)


def _draw_fx_scorched(layer: pygame.Surface, vw: int, vh: int, t: float) -> None:
    _tint_pulse(layer, vw, vh, t, (80, 30, 5, 10))
    _heat_shimmer(layer, vw, vh, t, 4, 10)
    _blit_particles(layer, vw, vh, t, _EMBERS_SCORCHED)


def _draw_fx_hellish(layer: pygame.Surface, vw: int, vh: int, t: float) -> None:
    _mist_blobs(
        layer, vw, vh, t,
        (
            (0.45, 0.70, 0.20, (40, 5, 5, 20)),
            (0.70, 0.75, 0.16, (35, 3, 3, 16)),
        ),
    )
    _heat_shimmer(layer, vw, vh, t, 5, 14)
    _blit_particles(layer, vw, vh, t, _EMBERS_HELLISH)
    flicker = int(12 + 8 * math.sin(t * 0.12))
    layer.fill((120, 15, 0, flicker), special_flags=pygame.BLEND_RGBA_ADD)


_FX_DRAWERS = {
    BackgroundId.DEFAULT:  _draw_fx_default,
    BackgroundId.MORTAL:   _draw_fx_mortal,
    BackgroundId.SCORCHED: _draw_fx_scorched,
    BackgroundId.HELLISH:  _draw_fx_hellish,
}


def _draw_effects(screen: pygame.Surface, t: float) -> None:
    vw, vh = screen.get_size()
    if vw <= 0 or vh <= 0:
        return
    layer = _ensure_effect_layer(vw, vh)
    drawer = _FX_DRAWERS.get(_active, _draw_fx_default)
    drawer(layer, vw, vh, t)
    screen.blit(layer, (0, 0))


def draw(screen: pygame.Surface, t: float = 0) -> None:
    """Blit the active background and subtle atmospheric overlay to *screen*."""
    if not _sources:
        return

    vw, vh = screen.get_size()
    key = (_active, vw, vh)
    if _scaled_cache != key or _scaled_surf is None:
        _rebuild_scaled(vw, vh)

    if _scaled_surf is not None:
        screen.blit(_scaled_surf, _blit_pos)

    _draw_effects(screen, t)


def active() -> BackgroundId:
    """Currently selected background id."""
    return _active
