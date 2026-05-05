"""
audio.py — Centralised audio manager for Oblivio.

Handles all SFX playback and BGM state transitions.
- SFX volume respects: master_volume * sfx_volume
- BGM volume respects: master_volume * music_volume
- BGM pause/resume preserves playback position (for in-game track)

Owner: Jim (visuals / UI)
"""

import os
import pygame

# ---------------------------------------------------------------------------
# Asset paths
# ---------------------------------------------------------------------------
_HERE   = os.path.dirname(__file__)
_MUSIC  = os.path.join(_HERE, "game-assets", "music")
_SFX_I  = os.path.join(_HERE, "game-assets", "sfx", "interface")
_SFX_G  = os.path.join(_HERE, "game-assets", "sfx", "in-game")

_BGM_MENU  = os.path.join(_MUSIC, "Tetuano_menuBGM.mp3")
_BGM_GAME  = os.path.join(_MUSIC, "CriticalTheme_Loopable.wav")

_SFX_FILES = {
    "hover":    os.path.join(_SFX_I, "JDSherbert - Ultimate UI SFX Pack - Select - 1.wav"),
    "select":   os.path.join(_SFX_I, "JDSherbert - Ultimate UI SFX Pack - Select - 2.wav"),
    "cancel":   os.path.join(_SFX_I, "JDSherbert - Ultimate UI SFX Pack - Cancel - 1.wav"),
    "popup":    os.path.join(_SFX_I, "JDSherbert - Ultimate UI SFX Pack - Popup Open - 1.wav"),
    "mismatch": os.path.join(_SFX_G, "JDSherbert - Ultimate UI SFX Pack - Cancel - 2.wav"),
}

# ---------------------------------------------------------------------------
# Internal state
# ---------------------------------------------------------------------------
_sounds:    dict[str, pygame.mixer.Sound] = {}
_bgm_state: str | None = None   # "menu" | "game" | "paused" | None


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

def init(master_vol: float = 1.0, music_vol: float = 1.0, sfx_vol: float = 1.0) -> None:
    """Load all SFX. Call once after pygame.mixer.init()."""
    for key, path in _SFX_FILES.items():
        if os.path.exists(path):
            _sounds[key] = pygame.mixer.Sound(path)
        else:
            print(f"[AUDIO] Missing SFX: {path}")
    apply_volumes(master_vol, music_vol, sfx_vol)


def apply_volumes(master_vol: float, music_vol: float, sfx_vol: float) -> None:
    """Update all volume levels in real time (e.g. from options menu)."""
    eff_sfx   = master_vol * sfx_vol
    eff_music = master_vol * music_vol
    for snd in _sounds.values():
        snd.set_volume(eff_sfx)
    pygame.mixer.music.set_volume(eff_music)


# ---------------------------------------------------------------------------
# SFX — one-liner API
# ---------------------------------------------------------------------------

def _play(key: str) -> None:
    snd = _sounds.get(key)
    if snd:
        snd.play()


def sfx_hover()    -> None: _play("hover")
def sfx_select()   -> None: _play("select")
def sfx_cancel()   -> None: _play("cancel")
def sfx_popup()    -> None: _play("popup")
def sfx_mismatch() -> None: _play("mismatch")


# ---------------------------------------------------------------------------
# BGM — state-guarded so repeated calls don't restart the track
# ---------------------------------------------------------------------------

def bgm_play_menu() -> None:
    """Play the menu BGM, looping. No-op if already playing."""
    global _bgm_state
    if _bgm_state == "menu":
        return
    _bgm_state = "menu"
    if os.path.exists(_BGM_MENU):
        pygame.mixer.music.load(_BGM_MENU)
        pygame.mixer.music.play(-1)


def bgm_play_game(difficulty_label: str = "") -> None:
    """
    Play in-game BGM if a track exists for this difficulty.
    Currently only Easy (4x4) has BGM — others play silence.
    """
    global _bgm_state
    _bgm_state = "game"
    if difficulty_label.lower() == "easy" and os.path.exists(_BGM_GAME):
        pygame.mixer.music.load(_BGM_GAME)
        pygame.mixer.music.play(-1)
    else:
        pygame.mixer.music.stop()


def bgm_pause() -> None:
    """Pause the in-game track (preserves position for resume)."""
    global _bgm_state
    if _bgm_state == "game":
        pygame.mixer.music.pause()
        _bgm_state = "paused"


def bgm_resume() -> None:
    """Resume the in-game track from where it was paused."""
    global _bgm_state
    if _bgm_state == "paused":
        pygame.mixer.music.unpause()
        _bgm_state = "game"


def bgm_stop() -> None:
    """Stop all BGM completely (Game Over / Win)."""
    global _bgm_state
    pygame.mixer.music.stop()
    _bgm_state = None
