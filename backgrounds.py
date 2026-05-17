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

_fade_prev_surf: pygame.Surface | None = None
_fade_prev_pos: tuple[int, int] = (0, 0)
_fade_p: float = 1.0
_fade_last_ticks: int = 0


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
    global _active, _fade_prev_surf, _fade_prev_pos, _fade_p, _fade_last_ticks
    if bg not in _sources and _sources:
        raise ValueError(f"Unknown background: {bg}")
    if bg == _active and _scaled_cache is not None:
        return
    
    if _scaled_surf is not None:
        _fade_prev_surf = _scaled_surf
        _fade_prev_pos = _blit_pos
    _fade_p = 0.0
    _fade_last_ticks = pygame.time.get_ticks()
    
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
    global _scaled_cache, _scaled_surf
    _scaled_cache = None
    _scaled_surf = None


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


def draw(screen: pygame.Surface, t: float = 0) -> None:
    """Blit the active background to *screen*."""
    global _fade_p, _fade_last_ticks, _fade_prev_surf
    if not _sources:
        return

    now = pygame.time.get_ticks()
    if _fade_p < 1.0 and _fade_last_ticks > 0:
        dt_ms = now - _fade_last_ticks
        _fade_p = min(1.0, _fade_p + dt_ms / 600.0)
        if _fade_p == 1.0:
            _fade_prev_surf = None
    _fade_last_ticks = now

    vw, vh = screen.get_size()
    key = (_active, vw, vh)
    if _scaled_cache != key or _scaled_surf is None:
        _rebuild_scaled(vw, vh)

    # Crossfade
    if _fade_prev_surf is not None and _fade_p < 1.0:
        screen.blit(_fade_prev_surf, _fade_prev_pos)
        if _scaled_surf is not None:
            _scaled_surf.set_alpha(int(255 * _fade_p))
            screen.blit(_scaled_surf, _blit_pos)
            _scaled_surf.set_alpha(255)
    else:
        if _scaled_surf is not None:
            screen.blit(_scaled_surf, _blit_pos)


def active() -> BackgroundId:
    """Currently selected background id."""
    return _active
