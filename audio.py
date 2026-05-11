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

_SFX_INGAME = os.path.join(_HERE, "game-assets", "sfx", "in-game")

_SFX_FILES = {
    "hover":    os.path.join(_SFX_I, "JDSherbert - Ultimate UI SFX Pack - Select - 1.wav"),
    "select":   os.path.join(_SFX_I, "JDSherbert - Ultimate UI SFX Pack - Select - 2.wav"),
    "cancel":   os.path.join(_SFX_I, "JDSherbert - Ultimate UI SFX Pack - Cancel - 1.wav"),
    "popup":    os.path.join(_SFX_I, "JDSherbert - Ultimate UI SFX Pack - Popup Open - 1.wav"),
    "flip":     os.path.join(_SFX_I, "JDSherbert - Ultimate UI SFX Pack - Swipe - 1.wav"),
    "mismatch": os.path.join(_SFX_INGAME, "JDSherbert - Ultimate UI SFX Pack - Cancel - 2.wav"),
}

# Heartbeat tracks — loaded separately, played on a dedicated channel
_HB_SLOW_PATH = os.path.join(_SFX_INGAME, "heart_beat_human_a_slow.wav")
_HB_FAST_PATH = os.path.join(_SFX_INGAME, "heart_beat_human_a_fast.wav")
_hb_slow: pygame.mixer.Sound | None = None
_hb_fast: pygame.mixer.Sound | None = None
_hb_channel: pygame.mixer.Channel | None = None
_hb_state: str | None = None   # None | "slow" | "fast"

# ---------------------------------------------------------------------------
# Internal state
# ---------------------------------------------------------------------------
_sounds:    dict[str, pygame.mixer.Sound] = {}
_bgm_state: str | None = None   # "menu" | "game" | "paused" | None
_menu_bgm_snd: pygame.mixer.Sound | None = None
_menu_bgm_channel: pygame.mixer.Channel | None = None


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

def init(master_vol: float = 1.0, music_vol: float = 1.0, sfx_vol: float = 1.0) -> None:
    """Load all SFX. Call once after pygame.mixer.init()."""
    global _menu_bgm_snd, _menu_bgm_channel, _hb_slow, _hb_fast, _hb_channel
    for key, path in _SFX_FILES.items():
        if os.path.exists(path):
            _sounds[key] = pygame.mixer.Sound(path)
        else:
            print(f"[AUDIO] Missing SFX: {path}")

    # Heartbeat tracks on dedicated channel 1
    if os.path.exists(_HB_SLOW_PATH):
        _hb_slow = pygame.mixer.Sound(_HB_SLOW_PATH)
    else:
        print(f"[AUDIO] Missing heartbeat slow: {_HB_SLOW_PATH}")
    if os.path.exists(_HB_FAST_PATH):
        _hb_fast = pygame.mixer.Sound(_HB_FAST_PATH)
    else:
        print(f"[AUDIO] Missing heartbeat fast: {_HB_FAST_PATH}")
    _hb_channel = pygame.mixer.Channel(1)

    if os.path.exists(_BGM_MENU):
        try:
            _menu_bgm_snd = pygame.mixer.Sound(_BGM_MENU)
            _menu_bgm_channel = pygame.mixer.Channel(7)
        except Exception as e:
            print(f"[AUDIO] Failed to load menu BGM as Sound: {e}")

    apply_volumes(master_vol, music_vol, sfx_vol)



def apply_volumes(master_vol: float, music_vol: float, sfx_vol: float) -> None:
    """Update all volume levels in real time (e.g. from options menu)."""
    eff_sfx   = master_vol * sfx_vol
    eff_music = master_vol * music_vol
    for snd in _sounds.values():
        snd.set_volume(eff_sfx)
    if _hb_slow: _hb_slow.set_volume(eff_sfx)
    if _hb_fast: _hb_fast.set_volume(eff_sfx)
    pygame.mixer.music.set_volume(eff_music)
    if _menu_bgm_snd:
        _menu_bgm_snd.set_volume(eff_music)


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
def sfx_flip()     -> None: _play("flip")
def sfx_mismatch() -> None: _play("mismatch")


# ---------------------------------------------------------------------------
# Heartbeat — dedicated looping channel, BGM ducked when active
# ---------------------------------------------------------------------------
_DUCK_VOLUME = 0.35   # BGM volume when heartbeat is playing


def update_heartbeat(hp: float, music_vol: float, master_vol: float) -> None:
    """
    Call every frame with current HP.
    - hp <= 50: slow heartbeat starts, BGM ducks
    - hp <= 30: fast heartbeat replaces slow, BGM ducks further
    - hp > 50:  heartbeat stops, BGM restored
    Transitions are guarded so tracks don't restart on every frame.
    """
    global _hb_state
    if _hb_channel is None:
        return

    base_music_vol = master_vol * music_vol

    if hp <= 0:
        # Dead — let game_over handle stopping everything
        return
    elif hp <= 30:
        if _hb_state != "fast":
            _hb_state = "fast"
            _hb_channel.stop()
            if _hb_fast:
                _hb_channel.play(_hb_fast, loops=-1)
            # Duck BGM significantly
            pygame.mixer.music.set_volume(base_music_vol * _DUCK_VOLUME)
    elif hp <= 50:
        if _hb_state != "slow":
            _hb_state = "slow"
            _hb_channel.stop()
            if _hb_slow:
                _hb_channel.play(_hb_slow, loops=-1)
            # Duck BGM slightly
            pygame.mixer.music.set_volume(base_music_vol * 0.6)
    else:
        if _hb_state is not None:
            _hb_state = None
            _hb_channel.stop()
            # Restore BGM to full volume
            pygame.mixer.music.set_volume(base_music_vol)


def heartbeat_stop() -> None:
    """Stop heartbeat and restore BGM volume. Call on pause/game-over/menu."""
    global _hb_state
    _hb_state = None
    if _hb_channel:
        _hb_channel.stop()


# ---------------------------------------------------------------------------
# BGM — state-guarded so repeated calls don't restart the track
# ---------------------------------------------------------------------------

def bgm_play_menu() -> None:
    """Play the menu BGM, looping. No-op if already playing."""
    global _bgm_state
    if _bgm_state == "menu":
        return
    _bgm_state = "menu"
    pygame.mixer.music.stop()
    if _menu_bgm_snd and _menu_bgm_channel:
        if not _menu_bgm_channel.get_busy():
            _menu_bgm_channel.play(_menu_bgm_snd, loops=-1)


def bgm_play_game(difficulty_label: str = "") -> None:
    """
    Play in-game BGM if a track exists for this difficulty.
    Currently only Easy (4x4) has BGM — others play silence.
    """
    global _bgm_state
    _bgm_state = "game"
    if _menu_bgm_channel:
        _menu_bgm_channel.stop()
        
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
        if _menu_bgm_snd and _menu_bgm_channel:
            _menu_bgm_channel.play(_menu_bgm_snd, loops=-1)


def bgm_resume() -> None:
    """Resume the in-game track from where it was paused."""
    global _bgm_state
    if _bgm_state == "paused":
        if _menu_bgm_channel:
            _menu_bgm_channel.stop()
        pygame.mixer.music.unpause()
        _bgm_state = "game"


def bgm_stop() -> None:
    """Stop all BGM completely (Game Over / Win)."""
    global _bgm_state
    pygame.mixer.music.stop()
    if _menu_bgm_channel:
        _menu_bgm_channel.stop()
    _bgm_state = None
