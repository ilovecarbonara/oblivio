"""
settings.py — Persistent settings for Oblivio.

Manages display mode, resolution, and audio volumes.
All values are saved to / loaded from ``settings.json`` in the project
directory so they survive between sessions.

Owner: Jay (options / configuration)
"""

import json
import os
import pygame

# ---------------------------------------------------------------------------
# Option catalogues
# ---------------------------------------------------------------------------

DISPLAY_MODES: list[str] = ["Fullscreen", "Windowed", "Borderless Windowed"]

RESOLUTIONS: list[tuple[int, int]] = [
    (1024, 768),    # 4:3   ← default
    (1280, 720),    # 16:9
    (1600, 900),    # 16:9
    (1920, 1080),   # 16:9
    (2560, 1440),   # 16:9
    (1440, 900),    # 16:10
    (1920, 1200),   # 16:10
]

INPUT_METHODS: list[str] = ["Keyboard & Mouse", "Keyboard", "Mouse"]

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

_DEFAULTS = {
    "display_mode":  1,     # index into DISPLAY_MODES  (Windowed)
    "resolution":    2,     # index into RESOLUTIONS     (1024×768)
    "master_volume": 1.0,   # 0.0 – 1.0
    "music_volume":  0.6,   # 0.0 – 1.0
    "sfx_volume":    1.0,   # 0.0 – 1.0
    "input_method":  0,     # index into INPUT_METHODS (Both)
}

# ---------------------------------------------------------------------------
# Live state  (module-level — imported as ``import settings as cfg``)
# ---------------------------------------------------------------------------

display_mode:  int   = _DEFAULTS["display_mode"]
resolution:    int   = _DEFAULTS["resolution"]
master_volume: float = _DEFAULTS["master_volume"]
music_volume:  float = _DEFAULTS["music_volume"]
sfx_volume:    float = _DEFAULTS["sfx_volume"]
input_method:  int   = _DEFAULTS["input_method"]

# ---------------------------------------------------------------------------
# Derived helpers
# ---------------------------------------------------------------------------

_HERE = os.path.dirname(__file__)
_SETTINGS_PATH = os.path.join(_HERE, "settings.json")


def effective_music_vol() -> float:
    """Return the final music volume (master × music), clamped 0–1."""
    return round(min(1.0, max(0.0, master_volume * music_volume)), 2)


def effective_sfx_vol() -> float:
    """Return the final SFX volume (master × sfx), clamped 0–1."""
    return round(min(1.0, max(0.0, master_volume * sfx_volume)), 2)


def current_resolution() -> tuple[int, int]:
    """Return the (width, height) tuple for the active resolution index."""
    idx = max(0, min(resolution, len(RESOLUTIONS) - 1))
    return RESOLUTIONS[idx]


def current_display_mode_label() -> str:
    """Human-readable label for the active display mode."""
    idx = max(0, min(display_mode, len(DISPLAY_MODES) - 1))
    return DISPLAY_MODES[idx]


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def load() -> None:
    """Read settings.json and populate module-level variables."""
    global display_mode, resolution, master_volume, music_volume, sfx_volume, input_method

    if not os.path.exists(_SETTINGS_PATH):
        print("[SETTINGS] No settings.json found — creating from defaults.")
        default_path = os.path.join(_HERE, "settings.default.json")
        if os.path.exists(default_path):
            with open(default_path, "r", encoding="utf-8") as f:
                default_data = f.read()
            with open(_SETTINGS_PATH, "w", encoding="utf-8") as f:
                f.write(default_data)
        else:
            print("[SETTINGS] settings.default.json is missing too! Using hardcoded defaults.")
            return

    try:
        with open(_SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        display_mode  = int(data.get("display_mode",  _DEFAULTS["display_mode"]))
        resolution    = int(data.get("resolution",    _DEFAULTS["resolution"]))
        master_volume = float(data.get("master_volume", _DEFAULTS["master_volume"]))
        music_volume  = float(data.get("music_volume",  _DEFAULTS["music_volume"]))
        sfx_volume    = float(data.get("sfx_volume",    _DEFAULTS["sfx_volume"]))
        input_method  = int(data.get("input_method",    _DEFAULTS["input_method"]))

        # Clamp indices
        display_mode = max(0, min(display_mode, len(DISPLAY_MODES) - 1))
        resolution   = max(0, min(resolution,   len(RESOLUTIONS) - 1))
        input_method = max(0, min(input_method, len(INPUT_METHODS) - 1))
        master_volume = max(0.0, min(1.0, master_volume))
        music_volume  = max(0.0, min(1.0, music_volume))
        sfx_volume    = max(0.0, min(1.0, sfx_volume))

        print(f"[SETTINGS] Loaded: mode={current_display_mode_label()}, "
              f"res={current_resolution()}, "
              f"vol=master:{master_volume:.0%} music:{music_volume:.0%} sfx:{sfx_volume:.0%}, "
              f"input={INPUT_METHODS[input_method]}")

    except (json.JSONDecodeError, ValueError, TypeError) as exc:
        print(f"[SETTINGS] Corrupt settings.json — using defaults. ({exc})")


def save() -> None:
    """Write current settings to settings.json."""
    data = {
        "display_mode":  display_mode,
        "resolution":    resolution,
        "master_volume": round(master_volume, 2),
        "music_volume":  round(music_volume, 2),
        "sfx_volume":    round(sfx_volume, 2),
        "input_method":  input_method,
    }
    try:
        with open(_SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except OSError as exc:
        print(f"[SETTINGS] Failed to save: {exc}")


# ---------------------------------------------------------------------------
# Apply helpers  —  push settings into Pygame
# ---------------------------------------------------------------------------

def apply_display(screen: pygame.Surface) -> pygame.Surface:
    """
    (Re-)create the Pygame display surface with the current
    display_mode and resolution.  Returns the new screen surface.
    """
    w, h = current_resolution()

    mode_label = current_display_mode_label()

    if mode_label == "Fullscreen":
        flags = pygame.FULLSCREEN
    elif mode_label == "Borderless Windowed":
        flags = pygame.NOFRAME
    else:  # Windowed
        flags = 0

    new_screen = pygame.display.set_mode((w, h), flags)
    print(f"[SETTINGS] Display applied: {mode_label} {w}×{h}")
    return new_screen


def apply_audio() -> None:
    """
    Push volume settings to Pygame mixer.
    Music volume = master × music.  SFX volume is stored for future use.
    """
    vol = effective_music_vol()
    pygame.mixer.music.set_volume(vol)
    print(f"[SETTINGS] Audio applied: music_vol={vol:.0%}, "
          f"sfx_vol={effective_sfx_vol():.0%} (placeholder)")
