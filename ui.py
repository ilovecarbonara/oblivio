"""
ui.py — Rendering / UI layer for Oblivio.

Renders everything onto a 256×192 canvas, then scales it 4× to 1024×768
using nearest-neighbour — this gives every pixel a chunky, pixelated look.

Color philosophy: "Hell is Other Demons"
  - OBLIVIO title: stark White — cold, imposing
  - Accent (cursor, lines, glows): #F30261 — neon magenta, aggressive
  - Shadow: #4A001F — deep blood red, weight and menace
  - Void: near-black organic blobs, no stars/rings

Owner: Jim (visuals / UI)
"""

import os
import math
import pygame
import lore

# ---------------------------------------------------------------------------
# Internal (low-res) canvas size and upscale factor
# ---------------------------------------------------------------------------
PIXEL_W = 256   # internal canvas width
PIXEL_H = 192   # internal canvas height
SCALE   = 4     # upscale factor  →  1024 × 768 output

# ---------------------------------------------------------------------------
# Asset paths
# ---------------------------------------------------------------------------
_HERE      = os.path.dirname(__file__)
_BASE      = os.path.join(_HERE, "game-assets", "sprites")
_CARDS_PNG = os.path.join(_BASE, "CARDS", "FantasyCards", "FantasyCards.png")
_CARD_BACK = os.path.join(_BASE, "CARDS", "FantasyCards", "Backsides", "DefaultFantasy.png")
_JOKERS_PNG = os.path.join(_BASE, "CARDS", "FantasyCards", "FantasyJokers.png")
_HEALTH_PX = os.path.join(_BASE, "HEALTH", "Pixelated")   # new pixelated bar

# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------
C_BG        = ( 10,   5,  16)   # #0A0510  near-black void
C_SHADOW_1  = ( 22,   5,  14)   # very dark crimson blob
C_SHADOW_2  = ( 35,   8,  28)   # slightly lighter shadow
C_SHADOW_3  = ( 18,   3,  30)   # dark indigo fog
C_ACCENT    = (243,   2,  97)   # #F30261  neon magenta accent
C_ACCENT_DK = ( 74,   0,  31)   # #4A001F  deep blood-red shadow
C_WHITE     = (255, 255, 255)   # title colour — stark and cold
C_DIM       = (180, 160, 190)   # lighter purple-grey for better readability
C_MATCH     = (243,   2,  97)   # match glow
C_MISMATCH  = (210,  40,  40)   # mismatch flash
C_OVERHEAL  = ( 60, 140, 255)   # #3C8CFF overheal blue
C_HUD_BG    = (  7,   3,  14)   # HUD strip background
C_GRACE     = (255, 185,  40)   # #FFB928  Golden grace period bar
C_OVERHEAL  = ( 60, 140, 255)   # #3C8CFF overheal blue

# ---------------------------------------------------------------------------
# Language Labels (Normal vs Dark)
# ---------------------------------------------------------------------------

_NORMAL_LABELS = {
    "menu_items": ["PLAY", "CODEX", "OPTIONS", "QUIT"],
    "pause_items": ["CONTINUE", "RESTART", "OPTIONS", "QUIT"],
    "pause_title": "PAUSED",
    "options_title": "SETTINGS",
    "codex_title": "CODEX",
    "result_title": "GAME OVER",
    "result_items": ["PLAY AGAIN", "MAIN MENU"],
    "difficulty_items": ["Easy", "Medium", "Hard", "Back"],
    "perfection_title": "PERFECT",
    "overheal_label": "+50 HP OVERHEAL",
    "pause_btn": "PAUSE",
    "difficulty_title": "CHOOSE YOUR FATE",
    "codex_back_menu": "MAIN MENU",
    "codex_back_lineage": "LINEAGES",
}

_DARK_LABELS = {
    "menu_items": ["BEGIN THE RECLAMATION", "REGISTRY OF THE LOST", "ATTUNE SENSES", "EMBRACE OBLIVION"],
    "pause_items": ["PERSIST", "REKINDLE", "ATTUNE SENSES", "SURRENDER"],
    "pause_title": "STASIS",
    "options_title": "SENSES",
    "codex_title": "REGISTRY",
    "result_title": "ALL IS FORGOTTEN",
    "result_items": ["SEEK REMEMBRANCE", "ABANDON THE LIGHT"],
    "difficulty_items": ["Mortal", "Scorched", "Hellish", "Back"],
    "perfection_title": "PERFECTION",
    "overheal_label": "+50 HP OVERHEAL",
    "pause_btn": "STASIS",
    "difficulty_title": "THE WILL TO PERSIST",
    "codex_back_menu": "RETURN",
    "codex_back_lineage": "LINEAGES",
}

def get_ui_label(key: str, override_mode: int = None) -> any:
    """Return the label for the given key based on current language mode."""
    import settings
    mode = override_mode if override_mode is not None else settings.language_mode
    if mode == 0:  # Normal
        return _NORMAL_LABELS.get(key, key)
    else:          # Dark
        return _DARK_LABELS.get(key, key)

# ---------------------------------------------------------------------------
# Fonts — Courier New Bold (system), antialias=False for crisp pixel edges
# ---------------------------------------------------------------------------
_font_title: pygame.font.Font | None = None
_font_lg:    pygame.font.Font | None = None
_font_sm:    pygame.font.Font | None = None
_font_cache: dict[int, pygame.font.Font] = {}
_title_cache: dict[int, pygame.font.Font] = {}


def get_gothic_font(size: int) -> pygame.font.Font:
    """Load or retrieve a cached size of PixeloidSans-Bold (menus/HUD)."""
    if size not in _font_cache:
        path = os.path.join(_HERE, "game-assets", "fonts", "Pixeloid", "TrueType (.ttf)", "PixeloidSans-Bold.ttf")
        if os.path.exists(path):
            _font_cache[size] = pygame.font.Font(path, size)
        else:
            _font_cache[size] = pygame.font.SysFont("couriernew", size, bold=True)
    return _font_cache[size]


def get_title_font(size: int) -> pygame.font.Font:
    """Load or retrieve a cached size of GothicByte (title only — eerie feel)."""
    if size not in _title_cache:
        path = os.path.join(_HERE, "game-assets", "fonts", "GothicByte.ttf")
        if os.path.exists(path):
            _title_cache[size] = pygame.font.Font(path, size)
        else:
            _title_cache[size] = pygame.font.SysFont("couriernew", size, bold=True)
    return _title_cache[size]


def load_fonts() -> None:
    global _font_title, _font_lg, _font_sm
    # Title uses Pixeloid (reverting — sourcing a better font soon)
    _font_title = get_gothic_font(96)
    # Menus/HUD use PixeloidSans-Bold for clean readability
    _font_lg    = get_gothic_font(36)
    _font_sm    = get_gothic_font(22)


# ---------------------------------------------------------------------------
# Low-res canvas  →  scale × 4 to screen (nearest-neighbour)
# ---------------------------------------------------------------------------
_canvas: pygame.Surface | None = None


def get_canvas() -> pygame.Surface:
    global _canvas
    if _canvas is None:
        _canvas = pygame.Surface((PIXEL_W, PIXEL_H))
    return _canvas


def blit_canvas_to_screen(screen: pygame.Surface) -> None:
    canvas = get_canvas()
    w, h   = screen.get_size()
    scaled = pygame.transform.scale(canvas, (w, h))
    screen.blit(scaled, (0, 0))


# ---------------------------------------------------------------------------
# Creepy void background  —  breathing shadow blobs, no stars/rings
# ---------------------------------------------------------------------------
_VOID_BLOBS = [
    # (base_x, base_y, base_radius, drift_spd, drift_amp, pulse_spd, color)
    (100,  80, 95, 0.007, 8, 0.012, C_SHADOW_3),
    (180,  50, 80, 0.009, 6, 0.015, C_SHADOW_2),
    ( 40, 140, 75, 0.006, 7, 0.010, C_SHADOW_1),
    (220, 130, 85, 0.008, 5, 0.013, C_SHADOW_3),
    (128,  96, 55, 0.003, 3, 0.020, C_SHADOW_1),   # central deep void
    (128,  96, 14, 0.002, 2, 0.030, (60, 1, 25)),  # accent core bleed
]


def draw_creepy_void(surf: pygame.Surface, frame: int) -> None:
    """
    Atmospheric horror background: near-black fill + slow-breathing
    shadow blobs.  Drawn at 256×192 → chunky when scaled 4×.
    """
    surf.fill(C_BG)

    for bx, by, br, ds, da, ps, color in _VOID_BLOBS:
        ox = int(da * math.sin(frame * ds))
        oy = int(da * math.cos(frame * ds * 0.7))
        r  = int(br + (br * 0.08) * math.sin(frame * ps))
        cx = max(r, min(PIXEL_W - r, bx + ox))
        cy = max(r, min(PIXEL_H - r, by + oy))
        pygame.draw.circle(surf, color, (cx, cy), r)

    # Deep abyss pit at center
    abyss_r = 32 + int(4 * math.sin(frame * 0.018))
    pygame.draw.circle(surf, (5, 1, 10), (PIXEL_W // 2, PIXEL_H // 2), abyss_r)

    # Crimson heartbeat — 1-pixel core dot
    hb_r = 2 + (1 if int(frame * 0.05) % 2 == 0 else 0)
    pygame.draw.circle(surf, C_ACCENT_DK, (PIXEL_W // 2, PIXEL_H // 2), hb_r)


# ---------------------------------------------------------------------------
# Pixelated health bar  (06.png — pink/magenta slanted bars)
#
# Sprite layout (from pixel inspection):
#   Row y=69-75 contains 5 frames side-by-side (each 42×7 px):
#     Frame 0 (x=  6): full — 4 pink segments filled
#     Frame 1 (x= 54): ~75% — 3 segments
#     Frame 2 (x=102): ~50% — 2 segments
#     Frame 3 (x=150): ~25% — 1 segment
#     Frame 4 (x=198): empty — dark only
#
# We map HP% → frame index:
#   100-75% → 0,  74-50% → 1,  49-25% → 2,  24-1% → 3,  0% → 4
# ---------------------------------------------------------------------------

_PX_BAR_SRC: pygame.Surface | None = None
_PX_BAR_FRAMES: list[pygame.Surface] = []

_BAR_SHEET  = "06.png"
_BAR_ROW_Y  = 69         # y start of the pink bar row
_BAR_H      = 7          # height of each bar frame
_BAR_XS     = [6, 54, 102, 150, 198]  # x-start of each frame
_BAR_W      = 42         # width of each frame


def load_health_sprites() -> None:
    """Load the 5 pixelated bar frames from 06.png."""
    global _PX_BAR_SRC, _PX_BAR_FRAMES
    _PX_BAR_FRAMES.clear()

    path = os.path.join(_HEALTH_PX, _BAR_SHEET)
    if not os.path.exists(path):
        print(f"[WARN] Health bar sheet not found: {path}")
        return

    sheet = pygame.image.load(path).convert_alpha()
    for bx in _BAR_XS:
        frame_surf = sheet.subsurface(pygame.Rect(bx, _BAR_ROW_Y, _BAR_W, _BAR_H))
        _PX_BAR_FRAMES.append(frame_surf.copy())


def _hp_to_frame_idx(hp_pct: float) -> int:
    """Map HP percentage (0–100) to bar frame index (0=full, 4=empty)."""
    if   hp_pct > 75: return 0
    elif hp_pct > 50: return 1
    elif hp_pct > 25: return 2
    elif hp_pct >  0: return 3
    else:             return 4


# ---------------------------------------------------------------------------
# HP bar smooth interpolation
# ---------------------------------------------------------------------------
_hp_drawn:  float = 100.0
_hp_target: float = 100.0
HP_LERP = 0.12

_grace_drawn : float = 0.0
_grace_target: float = 0.0


def set_hp(hp: float) -> None:
    global _hp_target
    _hp_target = float(hp)


def reset_hp() -> None:
    global _hp_drawn, _hp_target
    _hp_drawn = _hp_target = 100.0


def _tick_hp() -> None:
    global _hp_drawn
    d = _hp_target - _hp_drawn
    _hp_drawn += d * HP_LERP
    if abs(d) < 0.1:
        _hp_drawn = _hp_target

def _tick_grace() -> None:
    global _grace_drawn
    d = _grace_target - _grace_drawn
    _grace_drawn += d * HP_LERP
    if abs(d) < 0.05:
        _grace_drawn = _grace_target


# ---------------------------------------------------------------------------
# Card sprite mapping (FantasyCards.png)
# 
# Sheet layout: 13 columns (A, 2-10, J, Q, K), 4 rows.
# Card size: 23x35 px, with 1px transparent gap (stride is 24x36).
# 
# Rows (based on visual icons):
# 0: Sundered (Red Sword)
# 1: Hollow (White Skull)
# 2: Arcanum (White Spark)
# 3: Grafted (Red Shield)
# ---------------------------------------------------------------------------
_RANKS      = ("A","2","3","4","5","6","7","8","9","10","J","Q","K")
_SUIT_ROW   = {"Sundered": 0, "Hollow": 1, "Arcanum": 2, "Grafted": 3}

_card_sprites: dict[str, pygame.Surface] = {}
_joker_sprites: list[pygame.Surface] = []
_card_back: pygame.Surface | None = None


def load_card_sprites() -> None:
    global _card_back
    _card_sprites.clear()
    
    if os.path.exists(_CARDS_PNG):
        sheet = pygame.image.load(_CARDS_PNG).convert_alpha()
        for suit, row_idx in _SUIT_ROW.items():
            for rank_idx, rank in enumerate(_RANKS):
                x = rank_idx * 24
                y = row_idx * 36
                surf = sheet.subsurface(pygame.Rect(x, y, 23, 35))
                _card_sprites[f"{suit}_{rank}"] = surf.copy()
    else:
        print(f"[WARN] Card sheet not found: {_CARDS_PNG}")
        
    if os.path.exists(_CARD_BACK):
        _card_back = pygame.image.load(_CARD_BACK).convert_alpha()

    _joker_sprites.clear()
    if os.path.exists(_JOKERS_PNG):
        sheet = pygame.image.load(_JOKERS_PNG).convert_alpha()
        # 3 jokers: 23x35 with 1px gap (71x35 sheet)
        for i in range(3):
            x = i * 24
            surf = sheet.subsurface(pygame.Rect(x, 0, 23, 35))
            _joker_sprites.append(surf.copy())


def get_card_surf(suit: str, rank: str) -> pygame.Surface | None:
    return _card_sprites.get(f"{suit}_{rank}")


def get_back_surf() -> pygame.Surface | None:
    return _card_back


# ---------------------------------------------------------------------------
# Flip animation
# ---------------------------------------------------------------------------
FLIP_FRAMES = 8
FLIP_SPEED  = 1.0 / FLIP_FRAMES
_flips: dict[int, dict] = {}


def start_flip(card) -> None:
    _flips[id(card)] = {"phase": "close", "progress": 0.0, "card": card}


def update_flips(dt: float = 1.0) -> None:
    done = []
    for cid, fs in _flips.items():
        fs["progress"] += FLIP_SPEED * dt
        if fs["progress"] >= 1.0:
            fs["progress"] = 0.0
            if fs["phase"] == "close":
                fs["phase"] = "open"
            else:
                done.append(cid)
    for cid in done:
        del _flips[cid]


def is_flipping(card) -> bool:
    return id(card) in _flips


def _flip_scale(card) -> float:
    fs = _flips.get(id(card))
    if fs is None:
        return 1.0
    t = fs["progress"]
    return (1.0 - t) if fs["phase"] == "close" else t


# ---------------------------------------------------------------------------
# Screen transition  —  fade to black, fire callback at peak, fade back in
# ---------------------------------------------------------------------------
_trans_active:   bool  = False
_trans_phase:    str   = "in"    # "in" | "out"
_trans_alpha:    float = 0.0
_trans_callback          = None
_TRANS_SPEED:    float = 10.0    # alpha units per frame  (255/10 = ~25 frames each way)


def start_transition(callback) -> None:
    """
    Begin a fade-to-black transition.
    *callback* is called once the screen is fully black (at peak).
    After the callback fires the overlay fades back out.
    Input should be blocked while is_transition_active() is True.
    """
    global _trans_active, _trans_phase, _trans_alpha, _trans_callback
    _trans_active   = True
    _trans_phase    = "in"
    _trans_alpha    = 0.0
    _trans_callback = callback


def is_transition_active() -> bool:
    return _trans_active


def update_transition() -> None:
    global _trans_active, _trans_phase, _trans_alpha, _trans_callback
    if not _trans_active:
        return
    if _trans_phase == "in":
        _trans_alpha = min(255.0, _trans_alpha + _TRANS_SPEED)
        if _trans_alpha >= 255.0:
            if _trans_callback:
                _trans_callback()
                _trans_callback = None
            _trans_phase = "out"
    else:
        _trans_alpha = max(0.0, _trans_alpha - _TRANS_SPEED)
        if _trans_alpha <= 0.0:
            _trans_active = False


def draw_transition(screen: pygame.Surface) -> None:
    """Draw the black fade overlay. Call this AFTER all other rendering."""
    if not _trans_active or _trans_alpha <= 0:
        return
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, int(_trans_alpha)))
    screen.blit(overlay, (0, 0))


# ---------------------------------------------------------------------------
# Danger vignette  —  smooth gradient pulsing when HP ≤ 50
# ---------------------------------------------------------------------------

def draw_danger_vignette(screen: pygame.Surface, hp: float, frame: int) -> None:
    """
    Draw a pulsing triangular vignette on screen edges when HP is low.
    Intensity and pulse speed increase smoothly as HP drops from 50 to 0.
    The center remains clear to maintain visibility.
    """
    if hp > 50:
        return

    w, h = screen.get_size()

    # Smooth HP interpolation (50 -> 0)
    hp_factor = max(0.0, min(1.0, (50.0 - hp) / 50.0))
    
    # Gradually intensify speed and alpha
    # Increased alpha slightly since it's now restricted to the corners
    speed     = 0.04 + 0.12 * hp_factor
    max_alpha = 50 + 150 * hp_factor

    t     = (frame * speed) % (2 * math.pi)
    pulse = (math.sin(t) + 1) / 2
    base_alpha = int(max_alpha * pulse)

    if base_alpha <= 0:
        return

    # Create the vignette surface (solid pulsing red)
    vsurf = pygame.Surface((w, h), pygame.SRCALPHA)
    vsurf.fill((160, 0, 0, base_alpha))
    
    # Create a mask to isolate ONLY the four corners
    mask = pygame.Surface((w, h), pygame.SRCALPHA)
    mask.fill((0, 0, 0, 0)) # Start fully transparent
    
    # Configuration for corner glows
    # corner_r: how far the glow extends from each corner
    corner_r = int(min(w, h) * 0.45) 
    corners = [(0, 0), (w, 0), (0, h), (w, h)]
    bands = 32
    
    for cx, cy in corners:
        # Directional multipliers for triangle vertices
        dx = 1 if cx == 0 else -1
        dy = 1 if cy == 0 else -1
        
        # Draw nested triangles from OUTER (low alpha) to INNER (high alpha)
        for i in range(1, bands + 1):
            t = i / bands
            # Triangle size decreases as we move toward the corner tip
            r = int(corner_r * (1.0 - t + 1.0/bands))
            # Alpha increases as we get closer to the corner tip
            alpha = int(255 * (t ** 1.5))
            
            pts = [
                (cx, cy),
                (cx + dx * r, cy),
                (cx, cy + dy * r)
            ]
            pygame.draw.polygon(mask, (255, 255, 255, alpha), pts)

    # Use BLEND_RGBA_MULT to only keep the corners of the red surface
    vsurf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    
    screen.blit(vsurf, (0, 0))



# ---------------------------------------------------------------------------
# Card preview  —  flip all cards face-up at game start, then flip back
# ---------------------------------------------------------------------------
_preview_active:   bool  = False
_preview_phase:    str   = "flip_in"   # "flip_in" | "hold" | "flip_out"
_preview_timer:    float = 0.0
_preview_col:      int   = 0
_preview_max_cols: int   = 0

_PREVIEW_STAGGER_MS: float = 60.0    # delay between each column flip
_PREVIEW_HOLD_MS:    float = 1000.0  # how long cards stay shown before flip-back


def start_preview(cards: list) -> None:
    """
    Animate all cards flipping face-up in a wave from left to right.
    Input must be blocked while is_preview_active() is True.
    """
    global _preview_active, _preview_phase, _preview_timer, _preview_col, _preview_max_cols
    
    _preview_active = True
    _preview_phase  = "flip_in"
    _preview_timer  = 0.0
    _preview_col    = 0
    _preview_max_cols = max((c.grid_pos[0] for c in cards), default=0)


def update_preview(cards: list, dt_ms: float) -> None:
    """Tick the preview phases: staggered flip_in → hold → staggered flip_out."""
    global _preview_active, _preview_phase, _preview_timer, _preview_col
    if not _preview_active:
        return

    _preview_timer -= dt_ms

    if _preview_timer <= 0:
        from card import CardState
        import audio

        if _preview_phase == "flip_in":
            # Flip one column
            flipped_any = False
            for c in cards:
                if c.grid_pos[0] == _preview_col and c.state == CardState.FACE_DOWN:
                    c.state = CardState.FACE_UP
                    start_flip(c)
                    flipped_any = True
            
            if flipped_any:
                audio.sfx_flip()

            _preview_col += 1
            if _preview_col > _preview_max_cols:
                # All columns flipped, wait for the last animation (250ms) + hold time
                _preview_phase = "hold"
                _preview_timer = 250.0 + _PREVIEW_HOLD_MS
            else:
                _preview_timer = _PREVIEW_STAGGER_MS

        elif _preview_phase == "hold":
            # Hold done, start closing wave
            _preview_phase = "flip_out"
            _preview_col   = 0
            _preview_timer = 0.0

        elif _preview_phase == "flip_out":
            # Close one column
            flipped_any = False
            for c in cards:
                if c.grid_pos[0] == _preview_col and c.state == CardState.FACE_UP:
                    c.state = CardState.FACE_DOWN
                    start_flip(c)
                    flipped_any = True
            
            if flipped_any:
                audio.sfx_flip()

            _preview_col += 1
            if _preview_col > _preview_max_cols:
                _preview_active = False
            else:
                _preview_timer = _PREVIEW_STAGGER_MS



def is_preview_active() -> bool:
    return _preview_active


# ---------------------------------------------------------------------------
# Mismatch flash
# ---------------------------------------------------------------------------
_flash:  dict[int, float] = {}
FLASH_FRAMES = 24


def trigger_mismatch_flash(card_a, card_b) -> None:
    _flash[id(card_a)] = 255.0
    _flash[id(card_b)] = 255.0


def update_mismatch_flash(dt: float = 1.0) -> None:
    done = []
    for cid in _flash:
        _flash[cid] -= (255.0 / FLASH_FRAMES) * dt
        if _flash[cid] <= 0:
            done.append(cid)
    for cid in done:
        del _flash[cid]


# ---------------------------------------------------------------------------
# Screen shake  —  triggered on mismatch, replaces per-card shake
# ---------------------------------------------------------------------------
_shake_frames: int = 0
_SHAKE_MAX:    int = 18     # frames of shake duration
_SHAKE_AMP:    int = 14     # max pixel displacement


def trigger_screen_shake() -> None:
    """Call on mismatch to start a screen shake hit."""
    global _shake_frames
    _shake_frames = _SHAKE_MAX


def update_screen_shake() -> None:
    global _shake_frames
    if _shake_frames > 0:
        _shake_frames -= 1


def get_screen_shake_offset() -> tuple[int, int]:
    """Returns (ox, oy) pixel offset to apply to the whole screen this frame."""
    if _shake_frames <= 0:
        return (0, 0)
    t  = _shake_frames / _SHAKE_MAX   # 1.0 → 0.0  (trauma envelope)
    ox = int(_SHAKE_AMP * t * math.sin(_shake_frames * 2.5))
    oy = int(_SHAKE_AMP * 0.5 * t * math.sin(_shake_frames * 1.8 + 0.8))
    return (ox, oy)


# ---------------------------------------------------------------------------
# Match pulse
# ---------------------------------------------------------------------------
_pulse: dict[int, float] = {}
PULSE_FRAMES = 36


def trigger_match_pulse(card_a, card_b) -> None:
    _pulse[id(card_a)] = float(PULSE_FRAMES)
    _pulse[id(card_b)] = float(PULSE_FRAMES)


def update_match_pulse(dt: float = 1.0) -> None:
    done = []
    for cid in _pulse:
        _pulse[cid] -= dt
        if _pulse[cid] <= 0:
            done.append(cid)
    for cid in done:
        del _pulse[cid]


# ---------------------------------------------------------------------------
# Perfection Popup
# ---------------------------------------------------------------------------
_perf_timer:  float = 0.0
_perf_active: bool  = False
PERF_DURATION_MS = 2200.0


def trigger_perfection_popup() -> None:
    """Trigger the 'PERFECTION' popup for matching all cards perfectly."""
    global _perf_timer, _perf_active
    _perf_timer  = PERF_DURATION_MS
    _perf_active = True


def update_perfection_popup(dt_ms: float) -> None:
    global _perf_timer, _perf_active
    if not _perf_active:
        return
    _perf_timer -= dt_ms
    if _perf_timer <= 0:
        _perf_active = False


def draw_perfection_popup(screen: pygame.Surface) -> None:
    """Draw a flashy 'PERFECTION' message with glow and animation."""
    if not _perf_active or _perf_timer <= 0:
        return

    if _font_title is None:
        return

    w, h = screen.get_size()
    cx, cy = w // 2, h // 2
    
    # Progress: 0.0 (start) -> 1.0 (end)
    t = 1.0 - (_perf_timer / PERF_DURATION_MS)
    
    # Animation: scale up and fade out
    # Starts big and fades in, then stays, then fades out?
    # Let's do:
    # 0.0 - 0.2: Fade in & Scale up (overshoot)
    # 0.2 - 0.8: Hold & pulse
    # 0.8 - 1.0: Fade out & Scale up further
    
    alpha = 255
    scale = 1.0
    
    if t < 0.2:
        # Intro
        sub_t = t / 0.2
        alpha = int(255 * sub_t)
        scale = 0.5 + 0.6 * sub_t   # starts small, grows to 1.1
    elif t < 0.8:
        # Hold
        alpha = 255
        scale = 1.1 + 0.05 * math.sin(t * 20)  # gentle pulse
    else:
        # Outro
        sub_t = (t - 0.8) / 0.2
        alpha = int(255 * (1.0 - sub_t))
        scale = 1.1 + 0.3 * sub_t   # expands as it vanishes
        
    label = get_ui_label("perfection_title")
    
    # Render with layers
    C_DEPTH   = (45, 10, 90)
    C_OUTLINE = (255, 255, 255)
    DEPTH     = 8
    OUTLINE   = 2
    
    # Base surface
    base_surf = _font_title.render(label, False, C_ACCENT)
    
    # Scaling
    sw = int(base_surf.get_width() * scale)
    sh = int(base_surf.get_height() * scale)
    if sw <= 0 or sh <= 0: return
    
    # Render layers
    depth_surf   = _font_title.render(label, False, C_DEPTH)
    outline_surf = _font_title.render(label, False, C_OUTLINE)
    title_surf   = _font_title.render(label, False, C_ACCENT)
    
    # Scale layers
    depth_surf   = pygame.transform.scale(depth_surf,   (sw, sh))
    outline_surf = pygame.transform.scale(outline_surf, (sw, sh))
    title_surf   = pygame.transform.scale(title_surf,   (sw, sh))
    
    # Apply alpha
    depth_surf.set_alpha(alpha)
    outline_surf.set_alpha(alpha)
    title_surf.set_alpha(alpha)
    
    # Center rect
    rect = title_surf.get_rect(center=(cx, cy))
    
    # Blit layers
    for d in range(int(DEPTH * scale), 0, -1):
        screen.blit(depth_surf, (rect.x + d, rect.y + d))
        
    for ox in range(-OUTLINE, OUTLINE + 1):
        for oy in range(-OUTLINE, OUTLINE + 1):
            if ox == 0 and oy == 0: continue
            screen.blit(outline_surf, (rect.x + ox, rect.y + oy))
            
    screen.blit(title_surf, rect)
    
    # Or just "ROUND CLEAR" 
    sub_font = get_gothic_font(24)
    sub_label = get_ui_label("overheal_label")
    sub_surf = sub_font.render(sub_label, False, C_OVERHEAL)
    sub_surf.set_alpha(alpha)
    sub_rect = sub_surf.get_rect(centerx=cx, centery=rect.bottom + 40)
    screen.blit(sub_surf, sub_rect)


# ---------------------------------------------------------------------------
# Main Menu
# ---------------------------------------------------------------------------
_menu_rects: list[pygame.Rect] = []
_codex_rects: list[pygame.Rect] = []
_suit_rects: list[pygame.Rect] = []

def get_menu_items() -> list[str]:
    return get_ui_label("menu_items")

def draw_menu(screen: pygame.Surface, selected: int, frame: int) -> None:
    """
    Hell is Other Demons style:
    - OBLIVIO in cold White with deep blood-red drop shadow
    - #F30261 used ONLY for accent (cursor >, separator lines, highlight box)
    - No subtitle
    """
    global _menu_rects
    _menu_rects.clear()
    _draw_ui_background(screen, frame=frame // 4)

    if _font_title is None or _font_lg is None or _font_sm is None:
        return

    w  = screen.get_width()
    h  = screen.get_height()
    left_x = 80         # Left-aligned anchor
    ty = h // 2 - 140   # Centered vertically (offset to account for menu items below)

    # ── OBLIVIO title — 3-layer extruded pixel-art style ──────────────────
    C_DEPTH   = (45, 10, 90)      # deep indigo-purple block depth
    C_OUTLINE = (255, 255, 255)   # stark white outline
    DEPTH     = 10                # px of 3D block shadow
    OUTLINE   = 3                 # outline thickness

    title_text = "OBLIVIO"
    depth_surf   = _font_title.render(title_text, False, C_DEPTH)
    outline_surf = _font_title.render(title_text, False, C_OUTLINE)
    title_surf   = _font_title.render(title_text, False, C_ACCENT)
    title_rect   = title_surf.get_rect(left=left_x, centery=ty)

    # Step 1: stacked purple copies for the 3D block depth (down-right)
    for d in range(DEPTH, 0, -1):
        dr = depth_surf.get_rect(left=left_x + d, centery=ty + d)
        screen.blit(depth_surf, dr)

    # Step 2: white outline — blit white text in every direction
    for ox in range(-OUTLINE, OUTLINE + 1):
        for oy in range(-OUTLINE, OUTLINE + 1):
            if ox == 0 and oy == 0:
                continue
            or_ = outline_surf.get_rect(left=left_x + ox, centery=ty + oy)
            screen.blit(outline_surf, or_)

    # Step 3: neon magenta fill on top — use GothicByte for eerie horror look
    screen.blit(title_surf, title_rect)

    # ── Separator line ─────────────────────────────────────────────────────
    sep_y = title_rect.bottom + 20
    # Single long line starting from left margin
    pygame.draw.line(screen, C_ACCENT, (left_x, sep_y), (left_x + 500, sep_y), 2)

    # ── Menu items ─────────────────────────────────────────────────────────
    item_y0      = sep_y + 60
    item_spacing = 80
    items        = get_menu_items()
    for i, label in enumerate(items):
        is_sel = (i == selected)
        color  = C_WHITE if is_sel else C_DIM
        iy     = item_y0 + i * item_spacing

        display_label = f"> {label}" if is_sel else label
        item_s = _font_lg.render(display_label, False, color)
        item_w = item_s.get_width()
        item_h = item_s.get_height()

        if is_sel:
            # Selection box anchored to the left
            box = pygame.Rect(left_x - 16, iy - item_h // 2 - 8,
                              item_w + 48, item_h + 16)
            pygame.draw.rect(screen, (25, 2, 14), box)
            pygame.draw.rect(screen, C_ACCENT, box, 2)

        item_rect = item_s.get_rect(left=left_x, centery=iy)
        screen.blit(item_s, item_rect)
        _menu_rects.append(item_rect.inflate(40, 20))






# ---------------------------------------------------------------------------
# Themed playfield backgrounds (pixel-perfect cover + veil)
# ---------------------------------------------------------------------------

def _draw_themed_background(
    screen: pygame.Surface,
    veil_alpha: int = 155,
    frame: int = 0,
) -> None:
    import backgrounds

    backgrounds.draw(screen, float(frame))
    veil = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    veil.fill((0, 0, 0, veil_alpha))
    screen.blit(veil, (0, 0))


def _draw_ui_background(
    screen: pygame.Surface,
    veil_alpha: int = 100,
    frame: int = 0,
) -> None:
    """Default castle backdrop for menu, codex, and settings."""
    import backgrounds

    backgrounds.set_default()
    _draw_themed_background(screen, veil_alpha=veil_alpha, frame=frame)


def draw_game_bg(screen: pygame.Surface, frame: int) -> None:
    _draw_themed_background(screen, veil_alpha=155, frame=frame)


# ---------------------------------------------------------------------------
# Hover tracking
# ---------------------------------------------------------------------------
_hovered_card_id: int = -1


def set_hovered(card) -> None:
    """Call each frame from main.py with the card under the mouse (or None)."""
    global _hovered_card_id
    _hovered_card_id = id(card) if card is not None else -1


# ---------------------------------------------------------------------------
# Keyboard cursor tracking
# ---------------------------------------------------------------------------
_cursor_grid_pos: tuple[int, int] | None = None


def set_cursor(grid_pos: tuple[int, int] | None) -> None:
    """Set the current keyboard-cursor grid cell, or None to hide the cursor."""
    global _cursor_grid_pos
    _cursor_grid_pos = grid_pos


# ---------------------------------------------------------------------------
# Card rendering  (full-res — sprites are already pixel art)
# ---------------------------------------------------------------------------

def draw_card(
    screen: pygame.Surface,
    card,
    card_w: int,
    card_h: int,
) -> None:
    from card import CardState

    rect: pygame.Rect = card.rect
    cid = id(card)

    if card.state == CardState.FACE_DOWN:
        src = get_back_surf()
    else:
        src = get_card_surf(card.suit, card.rank)

    if src is None:
        fb = (25, 10, 40) if card.state == CardState.FACE_DOWN else (60, 20, 50)
        pygame.draw.rect(screen, fb, rect, border_radius=3)
        pygame.draw.rect(screen, C_DIM, rect, width=1, border_radius=3)
        return

    scale  = _flip_scale(card)
    dw     = max(1, int(card_w * scale))
    scaled = pygame.transform.scale(src, (dw, card_h))
    bx     = rect.x + (card_w - dw) // 2
    screen.blit(scaled, (bx, rect.y))

    # Match pulse border
    if cid in _pulse and int(_pulse[cid]) % 12 < 6:
        gr = pygame.Rect(bx, rect.y, dw, card_h).inflate(4, 4)
        pygame.draw.rect(screen, C_MATCH, gr, width=2, border_radius=3)

    # Mismatch red overlay (stays with the shake)
    if cid in _flash:
        alpha = int(_flash[cid])
        fsurf = pygame.Surface((dw, card_h), pygame.SRCALPHA)
        fsurf.fill((*C_MISMATCH, alpha))
        screen.blit(fsurf, (bx, rect.y))

    # Hover highlight — dynamic pulsing magenta glow on face-down hoverable cards
    import settings as cfg
    if cfg.input_method != 1 and cid == _hovered_card_id and card.state == CardState.FACE_DOWN:
        hr = pygame.Rect(bx, rect.y, dw, card_h)
        # Sine-wave pulse: completes a cycle every ~800ms
        t_pulse = (pygame.time.get_ticks() % 800) / 800.0
        pulse   = (math.sin(t_pulse * 2 * math.pi) + 1) / 2   # 0.0 -> 1.0
        # Glow alpha breathes between 30 and 100
        glow_alpha = int(30 + pulse * 70)
        # Border width alternates between 1 and 3
        border_w = 1 + int(pulse * 2)
        # Outer glow (inflated rectangle, semi-transparent fill)
        glow_pad  = 6 + int(pulse * 4)
        glow_surf = pygame.Surface((dw + glow_pad * 2, card_h + glow_pad * 2), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (*C_ACCENT, glow_alpha), glow_surf.get_rect(), border_radius=6)
        screen.blit(glow_surf, (bx - glow_pad, rect.y - glow_pad))
        # Sharp inner border
        pygame.draw.rect(screen, C_ACCENT, hr, width=border_w, border_radius=3)

    # Keyboard cursor highlight — bright solid corner-bracket frame, animated dash
    if cfg.input_method != 2 and _cursor_grid_pos is not None and card.grid_pos == _cursor_grid_pos:
        t_dash = (pygame.time.get_ticks() % 600) / 600.0
        pulse2 = (math.sin(t_dash * 2 * math.pi) + 1) / 2   # 0->1
        # Solid bright-white inner border
        kb_rect = pygame.Rect(bx, rect.y, dw, card_h)
        pygame.draw.rect(screen, C_WHITE, kb_rect, width=2, border_radius=3)
        # Corner brackets — four L-shaped marks in neon magenta
        arm = max(6, dw // 5)   # bracket arm length scales with card width
        thickness = 2
        corners = [
            (bx,          rect.y),           # top-left
            (bx + dw - 1, rect.y),           # top-right
            (bx,          rect.y + card_h - 1),  # bottom-left
            (bx + dw - 1, rect.y + card_h - 1),  # bottom-right
        ]
        dirs = [
            ( 1,  1), (-1,  1),
            ( 1, -1), (-1, -1),
        ]
        for (cx_c, cy_c), (dx, dy) in zip(corners, dirs):
            pygame.draw.line(screen, C_ACCENT, (cx_c, cy_c), (cx_c + dx * arm, cy_c), thickness)
            pygame.draw.line(screen, C_ACCENT, (cx_c, cy_c), (cx_c, cy_c + dy * arm), thickness)
        # Pulsing outer glow ring
        glow_a2 = int(60 + pulse2 * 100)
        pad2 = 5 + int(pulse2 * 3)
        glow2 = pygame.Surface((dw + pad2 * 2, card_h + pad2 * 2), pygame.SRCALPHA)
        pygame.draw.rect(glow2, (*C_WHITE, glow_a2), glow2.get_rect(), border_radius=6)
        screen.blit(glow2, (bx - pad2, rect.y - pad2))


def draw_card_grid(
    screen: pygame.Surface,
    cards:  list,
    card_w: int,
    card_h: int,
    multiplier: float = 1.0,
    decay_fraction: float = 1.0,
    cursor_pos: tuple[int, int] | None = None,
) -> None:
    set_cursor(cursor_pos)
    for card in cards:
        draw_card(screen, card, card_w, card_h)

    # Draw persistent multiplier badge — animated, pulsing, color-shifted, and decaying
    if multiplier > 1.0 and cards and decay_fraction > 0:
        import time
        now_ms  = pygame.time.get_ticks()

        # Bounce: gentle sine scale wobble (faster at higher multipliers)
        wobble_speed = 0.003 + (multiplier - 1.0) * 0.001
        wobble       = 1.0 + 0.06 * math.sin(now_ms * wobble_speed)

        # Color: magenta (×1) → orange (×2) → bright yellow (×4+)
        t_col = min(1.0, (multiplier - 1.0) / 3.0)
        r_c = int(243 + (255 - 243) * t_col)
        g_c = int(  2 + (200 -   2) * t_col)
        b_c = int( 97 + (  0 -  97) * t_col)
        badge_color = (max(0, min(255, r_c)),
                       max(0, min(255, g_c)),
                       max(0, min(255, b_c)))

        # Shrink as it decays, with a minimum size floor
        effective_scale = max(0.4, decay_fraction)
        base_size  = (38 + int(multiplier * 3)) * effective_scale
        font       = get_gothic_font(int(base_size * wobble))

        max_x = max(c.rect.right  for c in cards)
        min_y = min(c.rect.top    for c in cards)

        text_surf   = font.render(f"×{multiplier:.1f}", False, badge_color)
        shadow_surf = font.render(f"×{multiplier:.1f}", False, C_ACCENT_DK)

        # Fade out alpha based on decay_fraction
        alpha = int(255 * min(1.0, decay_fraction * 1.5))  # Fade starts later
        
        # Flash urgency when under 20%
        if decay_fraction < 0.2:
            flash_alpha = int(120 + 135 * math.sin(now_ms * 0.03))
            alpha = min(alpha, flash_alpha)

        text_surf.set_alpha(alpha)
        shadow_surf.set_alpha(alpha)

        # Tilt slightly right for energy
        text_surf   = pygame.transform.rotate(text_surf,   -12)
        shadow_surf = pygame.transform.rotate(shadow_surf, -12)

        tw, th = text_surf.get_size()
        tx = max_x - tw // 2 + 14
        ty = min_y - th // 2 - 14

        # Drop shadow
        screen.blit(shadow_surf, (tx + 5, ty + 5))
        # Main text
        screen.blit(text_surf, (tx, ty))



# ---------------------------------------------------------------------------
# Floating Text & Score Juice
# ---------------------------------------------------------------------------
_prev_score:  int = 0
_score_juice: float = 0.0
_floating_texts: list[dict] = []

def _spawn_floating_score(x: int, y: int, text: str) -> None:
    _floating_texts.append({
        "x": float(x),
        "y": float(y),
        "text": text,
        "life": 1.0,
    })

def _draw_floating_texts(screen: pygame.Surface) -> None:
    font = get_gothic_font(36)
    for ft in _floating_texts:
        ft["y"] -= 0.8  # drift up
        ft["life"] -= 0.015
        if ft["life"] <= 0:
            continue
            
        alpha = int(255 * min(1.0, ft["life"] * 3.0))
        
        # Shadow
        sh = font.render(ft["text"], False, C_ACCENT_DK)
        sh.set_alpha(alpha)
        screen.blit(sh, (int(ft["x"]) + 2, int(ft["y"]) + 2))
        
        # Text
        ts = font.render(ft["text"], False, C_ACCENT)
        ts.set_alpha(alpha)
        screen.blit(ts, (int(ft["x"]), int(ft["y"])))
        
    _floating_texts[:] = [ft for ft in _floating_texts if ft["life"] > 0]


# ---------------------------------------------------------------------------
# HUD strip  —  pixelated slanted health bar + score
# ---------------------------------------------------------------------------
_pause_btn_rect: pygame.Rect = pygame.Rect(0, 0, 0, 0)

def draw_hud(
    screen: pygame.Surface,
    hp:     float,
    score:  int,
    multiplier: float,
    grace_mismatches: int,
    max_grace: int,
    hud_h:  int,
    frame:  int,
) -> None:
    global _prev_score, _score_juice

    w = screen.get_width()

    pygame.draw.rect(screen, C_HUD_BG, (0, 0, w, hud_h))
    pygame.draw.line(screen, C_ACCENT, (0, hud_h - 1), (w, hud_h - 1), 1)

    set_hp(hp)
    _tick_hp()

    # ── Custom drawn health bar ──────────────────────────────────────────────
    bar_x         = 14
    bar_display_w = 200
    bar_display_h = 14
    bar_top_y     = hud_h // 2 - bar_display_h // 2

    # Split HP into normal and overheal
    normal_hp   = min(100.0, _hp_drawn)
    overheal_hp = max(0.0, _hp_drawn - 100.0)

    normal_fill_w   = max(0, int(bar_display_w * (normal_hp / 100.0)))
    overheal_fill_w = int(bar_display_w * (overheal_hp / 100.0))

    # Color for normal part: magenta (#F30261) at full → deep crimson (#8B0000) at critical
    hp_frac = normal_hp / 100.0
    r = int(243 + (139 - 243) * (1.0 - hp_frac))
    g = int(  2 + (  0 -   2) * (1.0 - hp_frac))
    b = int( 97 + (  0 -  97) * (1.0 - hp_frac))
    bar_color = (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))

    # Track (empty portion)
    pygame.draw.rect(screen, (18, 6, 28), (bar_x, bar_top_y, bar_display_w, bar_display_h), border_radius=3)
    
    # Fill normal
    if normal_fill_w > 0:
        pygame.draw.rect(screen, bar_color, (bar_x, bar_top_y, normal_fill_w, bar_display_h), border_radius=3)
    
    # Fill overheal (extends beyond the track)
    if overheal_fill_w > 0:
        pygame.draw.rect(screen, C_OVERHEAL, (bar_x + bar_display_w, bar_top_y, overheal_fill_w, bar_display_h), border_radius=3)

    # Border (covers the entire visible health)
    total_w = bar_display_w + overheal_fill_w
    pygame.draw.rect(screen, C_ACCENT_DK, (bar_x, bar_top_y, total_w, bar_display_h), 1, border_radius=3)

    # HP text label above the bar
    label_font = get_gothic_font(14)
    hp_int     = max(0, int(round(_hp_drawn)))
    hp_surf    = label_font.render(f"{hp_int}/100 HP", False, C_DIM)
    screen.blit(hp_surf, (bar_x, bar_top_y - hp_surf.get_height() - 2))

    # ── Grace Bar (Gold Overlay) ───────────────────────────────────────────
    global _grace_target
    _grace_target = float(grace_mismatches)
    _tick_grace()

    if _grace_drawn > 0 and max_grace > 0:
        # Width proportional to grace (max_grace = full bar width)
        grace_frac = min(1.0, _grace_drawn / float(max_grace))
        grace_fill_w = int(bar_display_w * grace_frac)
        
        if grace_fill_w > 0:
            # Draw gold bar
            pygame.draw.rect(screen, C_GRACE, (bar_x, bar_top_y, grace_fill_w, bar_display_h), border_radius=3)
            
            # Subtle shine/highlight on top of gold
            pygame.draw.line(screen, (255, 255, 200), (bar_x + 1, bar_top_y + 1), (bar_x + grace_fill_w - 2, bar_top_y + 1), 1)

    # ── Power-up indicators ... (rest of the logic remains)


    # ── Scoreboard (Gothic Housing + Juice) ─────────────────────────────────
    box_w = 240
    box_h = 36
    box_x = w - box_w - 20
    box_y = hud_h // 2 - box_h // 2

    # Check for score increase
    if score > _prev_score:
        _score_juice = 1.0  # Max juice
        diff = score - _prev_score
        
        # Spawn floating text right beneath the box
        _spawn_floating_score(box_x + box_w // 2 - 20, box_y + box_h + 10, f"+{diff}")
    
    _prev_score = score

    if _score_juice > 0:
        _score_juice = max(0.0, _score_juice - 0.05)

    # Draw Gothic Box
    box_bg = (15 + int(40 * _score_juice), 5, 25)  # Brightens when juiced
    pygame.draw.rect(screen, box_bg, (box_x, box_y, box_w, box_h), border_radius=4)
    pygame.draw.rect(screen, C_ACCENT_DK, (box_x, box_y, box_w, box_h), 2, border_radius=4)

    # Juicy Font Scale — base 18px, grows to 26px when juiced
    base_size = 18
    font_size = base_size + int(_score_juice * 8)
    hud_font = get_gothic_font(font_size)

    # Color interpolates from White to Neon Magenta when juiced
    t_c = (
        int(C_WHITE[0] + (C_ACCENT[0] - C_WHITE[0]) * _score_juice),
        int(C_WHITE[1] + (C_ACCENT[1] - C_WHITE[1]) * _score_juice),
        int(C_WHITE[2] + (C_ACCENT[2] - C_WHITE[2]) * _score_juice)
    )

    score_str = f"SCORE {score:06d}"
    
    # Shadow
    sh_surf = hud_font.render(score_str, False, C_ACCENT_DK)
    tx = box_x + box_w // 2 - sh_surf.get_width() // 2
    ty = box_y + box_h // 2 - sh_surf.get_height() // 2
    screen.blit(sh_surf, (tx + 2, ty + 2))
    
    # Foreground Text
    sc_surf = hud_font.render(score_str, False, t_c)
    screen.blit(sc_surf, (tx, ty))

    # Draw Floating Texts over everything
    _draw_floating_texts(screen)


def draw_powerups(
    screen: pygame.Surface,
    shield_charges: int,
    lifesteal_active: bool,
    has_extra_life: bool,
) -> None:
    """
    Draw active Power-Ups glued to the bottom-right corner.
    Uses large sprites and no text labels.
    """
    w, h = screen.get_size()
    
    # Scale: internal 23x35 -> Big icons (approx 4.2x scale -> 96x147)
    scale  = 4.2
    icon_w = int(23 * scale)
    icon_h = int(35 * scale)
    
    margin = 20
    px = w - icon_w - margin
    py = h - icon_h - margin
    
    # List of active power-up sprites to draw
    active_sprites = []
    if shield_charges > 0: 
        if len(_joker_sprites) > 0: active_sprites.append(_joker_sprites[0])
    if lifesteal_active:
        if len(_joker_sprites) > 1: active_sprites.append(_joker_sprites[1])
    if has_extra_life:
        if len(_joker_sprites) > 2: active_sprites.append(_joker_sprites[2])
        
    # Draw them stacking horizontally to the left from the corner
    for sprite in reversed(active_sprites):
        s_icon = pygame.transform.scale(sprite, (icon_w, icon_h))
        # Drop shadow
        shadow_rect = pygame.Rect(px + 4, py + 4, icon_w, icon_h)
        pygame.draw.rect(screen, (0, 0, 0, 150), shadow_rect, border_radius=4)
        # Main sprite
        screen.blit(s_icon, (px, py))
        # Step left for next icon
        px -= (icon_w + 12)


def draw_pause_button(screen: pygame.Surface, frame: int) -> None:
    """
    Draw a gothic Pause button with a "||" icon in the bottom-left corner.
    Brightens and pulses when hovered.
    """
    global _pause_btn_rect
    w, h = screen.get_size()
    
    # Button dimensions (compact square for the icon)
    bw, bh = 42, 42
    
    margin = 20
    bx = margin
    by = h - bh - margin
    
    _pause_btn_rect = pygame.Rect(bx, by, bw, bh)
    
    # Hover detection
    mx, my = pygame.mouse.get_pos()
    is_hovered = _pause_btn_rect.collidepoint(mx, my)
    
    # Pulse effect when hovered
    alpha_mult = 1.0
    if is_hovered:
        t = (pygame.time.get_ticks() % 600) / 600.0
        pulse = (math.sin(t * 2 * math.pi) + 1) / 2
        alpha_mult = 0.8 + 0.2 * pulse
    
    # Draw background box
    bg_color = (25, 2, 14) if is_hovered else (15, 5, 20)
    pygame.draw.rect(screen, bg_color, _pause_btn_rect, border_radius=4)
    
    # Draw border
    border_color = C_ACCENT if is_hovered else C_ACCENT_DK
    pygame.draw.rect(screen, border_color, _pause_btn_rect, 2, border_radius=4)
    
    # Draw "||" icon
    icon_color = C_WHITE if is_hovered else C_DIM
    bar_w = 6
    bar_h = 18
    gap   = 6
    
    # Center the bars in the button
    total_icon_w = bar_w * 2 + gap
    ix = bx + (bw - total_icon_w) // 2
    iy = by + (bh - bar_h) // 2
    
    if is_hovered:
        # Create a small surface to apply alpha pulse to the icon
        icon_surf = pygame.Surface((total_icon_w, bar_h), pygame.SRCALPHA)
        pygame.draw.rect(icon_surf, (*icon_color, int(255 * alpha_mult)), (0, 0, bar_w, bar_h))
        pygame.draw.rect(icon_surf, (*icon_color, int(255 * alpha_mult)), (bar_w + gap, 0, bar_w, bar_h))
        screen.blit(icon_surf, (ix, iy))
    else:
        pygame.draw.rect(screen, icon_color, (ix, iy, bar_w, bar_h))
        pygame.draw.rect(screen, icon_color, (ix + bar_w + gap, iy, bar_w, bar_h))


# ---------------------------------------------------------------------------
# ESC hint
# ---------------------------------------------------------------------------

def draw_esc_hint(screen: pygame.Surface) -> None:
    pass


# ---------------------------------------------------------------------------
# Pause overlay  —  drawn ON TOP of the frozen game frame
# ---------------------------------------------------------------------------
_pause_rects: list[pygame.Rect] = []

def get_pause_items() -> list[str]:
    return get_ui_label("pause_items")

def draw_pause_overlay(screen: pygame.Surface, selected: int, frame: int) -> None:
    """
    Semi-transparent dark veil over the frozen game, with a centered
    pause menu in the same gothic style as the main menu.
    """
    global _pause_rects
    _pause_rects.clear()
    w = screen.get_width()
    h = screen.get_height()
    cx = w // 2

    # Dark overlay
    veil = pygame.Surface((w, h), pygame.SRCALPHA)
    veil.fill((0, 0, 0, 180))
    screen.blit(veil, (0, 0))

    if _font_lg is None or _font_sm is None:
        return

    # Title
    title_font = get_gothic_font(48)
    title_text = get_ui_label("pause_title") if "pause_title" in _NORMAL_LABELS else "PAUSED"
    title_surf = title_font.render(title_text, False, C_WHITE)
    shadow_surf = title_font.render(title_text, False, C_ACCENT_DK)
    title_rect = title_surf.get_rect(centerx=cx, centery=h // 2 - 120)
    screen.blit(shadow_surf, (title_rect.x + 3, title_rect.y + 3))
    screen.blit(title_surf, title_rect)

    # Separator
    sep_y = title_rect.bottom + 12
    pygame.draw.line(screen, C_ACCENT, (cx - 160, sep_y), (cx + 160, sep_y), 2)

    # Menu items
    item_y0 = sep_y + 40
    item_spacing = 60
    items = get_pause_items()
    for i, label in enumerate(items):
        is_sel = (i == selected)
        color  = C_WHITE if is_sel else C_DIM
        iy     = item_y0 + i * item_spacing

        display_label = f"> {label} <" if is_sel else label
        item_s = _font_lg.render(display_label, False, color)
        item_w = item_s.get_width()
        item_h = item_s.get_height()

        if is_sel:
            box = pygame.Rect(cx - item_w // 2 - 32, iy - item_h // 2 - 8,
                              item_w + 64, item_h + 16)
            pygame.draw.rect(screen, (25, 2, 14), box)
            pygame.draw.rect(screen, C_ACCENT, box, 2)

        screen.blit(item_s, item_s.get_rect(centerx=cx, centery=iy))
        _pause_rects.append(item_s.get_rect(centerx=cx, centery=iy).inflate(40, 20))






# ---------------------------------------------------------------------------
# Options menu  —  full-screen settings panel
# ---------------------------------------------------------------------------

# Row labels for the options menu
_OPT_LABELS = [
    "DISPLAY MODE",
    "RESOLUTION",
    "MASTER VOLUME",
    "MUSIC VOLUME",
    "SFX VOLUME",
    "INPUT METHOD",
    "LANGUAGE",
    "",              # APPLY & BACK button row
]
_options_rects: list[pygame.Rect] = []


def _draw_volume_bar(
    screen: pygame.Surface,
    x: int, y: int,
    width: int, height: int,
    value: float,
    is_selected: bool,
    sc: float = 1.0,
) -> None:
    """Draw a pixel-art volume bar: filled portion in accent, empty in dark."""
    # Background
    bg_color = (25, 10, 35)
    pygame.draw.rect(screen, bg_color, (x, y, width, height))

    # Filled portion
    fill_w = int(width * value)
    if fill_w > 0:
        fill_color = C_ACCENT if is_selected else (160, 2, 70)
        pygame.draw.rect(screen, fill_color, (x, y, fill_w, height))

    # Border
    border_color = C_ACCENT if is_selected else C_ACCENT_DK
    border_thickness = max(1, int(2 * sc))
    pygame.draw.rect(screen, border_color, (x, y, width, height), border_thickness)

    # Percentage text
    pct_font = get_gothic_font(int(18 * sc))
    pct_text = f"{int(value * 100)}%"
    pct_surf = pct_font.render(pct_text, False, C_WHITE if is_selected else C_DIM)
    # Use sc for horizontal offset, maybe min for vertical? Let's stay simple here as volume bar is small.
    screen.blit(pct_surf, (x + width + int(14 * sc), y + height // 2 - pct_surf.get_height() // 2))


def get_display_mode_label(idx: int) -> str:
    """Helper to get display mode label from index."""
    import settings
    idx = max(0, min(idx, len(settings.DISPLAY_MODES) - 1))
    return settings.DISPLAY_MODES[idx]


def get_resolution_label(idx: int) -> str:
    """Helper to get resolution label from index."""
    import settings
    idx = max(0, min(idx, len(settings.RESOLUTIONS) - 1))
    w, h = settings.RESOLUTIONS[idx]
    return f"{w} x {h}"


def draw_options_menu(
    screen: pygame.Surface,
    opts:   dict,
    selected_row: int,
    frame: int,
    origin: str,
) -> None:
    """
    Full-screen options menu.  ``opts`` is a dictionary of current (potentially unsaved) values.
    ``origin`` is 'menu' or 'pause' — changes the back-button label.
    """
    global _options_rects
    _options_rects.clear()

    _draw_ui_background(screen, frame=frame // 4)

    w = screen.get_width()
    h = screen.get_height()
    cx = w // 2
    
    # Dual scale factors to handle aspect ratio changes
    sc_w = w / 1024.0
    sc_h = h / 768.0
    # Use sc_w for font sizes and widths, sc_h for vertical positions
    sc = sc_w 

    if _font_lg is None or _font_sm is None:
        return

    # ── Title ───────────────────────────────────────────────────────────
    title_font = get_gothic_font(int(48 * sc_w))
    title_text = get_ui_label("options_title", override_mode=opts.get("language_mode"))
    title_surf = title_font.render(title_text, False, C_WHITE)
    shadow_surf = title_font.render(title_text, False, C_ACCENT_DK)
    title_rect = title_surf.get_rect(centerx=cx, centery=int(80 * sc_h))
    screen.blit(shadow_surf, (title_rect.x + int(3 * sc_w), title_rect.y + int(3 * sc_w)))
    screen.blit(title_surf, title_rect)

    # Separator
    sep_y = title_rect.bottom + int(12 * sc_h)
    pygame.draw.line(screen, C_ACCENT, (cx - int(240 * sc_w), sep_y), (cx + int(240 * sc_w), sep_y), max(1, int(2 * sc_w)))

    # ── Settings rows ──────────────────────────────────────────────────
    row_y0 = sep_y + int(40 * sc_h)
    row_spacing = int(60 * sc_h)
    label_font = get_gothic_font(int(22 * sc_w))
    value_font = get_gothic_font(int(22 * sc_w))

    label_x = cx - int(280 * sc_w)   # left-aligned labels
    value_x = cx + int(40 * sc_w)    # right-aligned values area

    for row in range(8):
        is_sel = (row == selected_row)
        ry = row_y0 + row * row_spacing
        color = C_WHITE if is_sel else C_DIM

        # Row 7 is the APPLY & BACK button
        if row == 7:
            btn_label = "APPLY & BACK"
            if is_sel:
                btn_label = f"> {btn_label} <"
            
            # Use font scaled by sc_w
            btn_font = get_gothic_font(int(36 * sc_w))
            btn_surf = btn_font.render(btn_label, False, color)
            btn_w = btn_surf.get_width()
            btn_h = btn_surf.get_height()
            btn_y = ry

            if is_sel:
                box = pygame.Rect(cx - btn_w // 2 - int(32 * sc_w), btn_y - btn_h // 2 - int(8 * sc_h),
                                  btn_w + int(64 * sc_w), btn_h + int(16 * sc_h))
                pygame.draw.rect(screen, (25, 2, 14), box)
                pygame.draw.rect(screen, C_ACCENT, box, max(1, int(2 * sc_w)))


            screen.blit(btn_surf, btn_surf.get_rect(centerx=cx, centery=btn_y))
            _options_rects.append(btn_surf.get_rect(centerx=cx, centery=btn_y).inflate(int(64 * sc_w), int(16 * sc_h)))
            continue

        # Label
        lbl_surf = label_font.render(_OPT_LABELS[row], False, color)
        screen.blit(lbl_surf, (label_x, ry - lbl_surf.get_height() // 2))

        # Row highlight line
        if is_sel:
            hl_y = ry + lbl_surf.get_height() // 2 + int(4 * sc_h)
            pygame.draw.line(screen, C_ACCENT,
                             (label_x, hl_y),
                             (label_x + lbl_surf.get_width(), hl_y), 1)
                             
        row_rect = pygame.Rect(cx - int(300 * sc_w), ry - int(15 * sc_h), int(600 * sc_w), int(30 * sc_h))
        _options_rects.append(row_rect)

        # Value display
        if row == 0:  # Display Mode
            mode_label = get_display_mode_label(opts["display_mode"])
            val_str = f"< {mode_label} >"
            val_surf = value_font.render(val_str, False, color)
            screen.blit(val_surf, (value_x, ry - val_surf.get_height() // 2))

        elif row == 1:  # Resolution
            res_label = get_resolution_label(opts["resolution"])
            val_str = f"< {res_label} >"
            val_surf = value_font.render(val_str, False, color)
            screen.blit(val_surf, (value_x, ry - val_surf.get_height() // 2))

        elif row == 2:  # Master Volume
            _draw_volume_bar(screen, value_x, ry - int(10 * sc_h), int(200 * sc_w), int(20 * sc_h),
                             opts["master_volume"], is_sel, sc_w)

        elif row == 3:  # Music Volume
            _draw_volume_bar(screen, value_x, ry - int(10 * sc_h), int(200 * sc_w), int(20 * sc_h),
                             opts["music_volume"], is_sel, sc_w)

        elif row == 4:  # SFX Volume
            _draw_volume_bar(screen, value_x, ry - int(10 * sc_h), int(200 * sc_w), int(20 * sc_h),
                             opts["sfx_volume"], is_sel, sc_w)

        elif row == 5:  # Input Method
            import settings
            method_label = settings.INPUT_METHODS[opts["input_method"]]
            val_str = f"< {method_label} >"
            val_surf = value_font.render(val_str, False, color)
            screen.blit(val_surf, (value_x, ry - val_surf.get_height() // 2))

        elif row == 6:  # Language
            import settings
            lang_label = settings.LANGUAGE_MODES[opts["language_mode"]]
            val_str = f"< {lang_label} >"
            val_surf = value_font.render(val_str, False, color)
            screen.blit(val_surf, (value_x, ry - val_surf.get_height() // 2))



# ---------------------------------------------------------------------------
# Result Screen (Game Over / Win)
# ---------------------------------------------------------------------------
_result_anim_timer: float = 0.0

def get_result_items() -> list[str]:
    return get_ui_label("result_items")

def start_result_anim() -> None:
    global _result_anim_timer
    _result_anim_timer = 0.0

def update_result_anim(dt_ms: float) -> None:
    global _result_anim_timer
    _result_anim_timer += dt_ms

RESULT_ITEMS = ["SEEK REMEMBRANCE", "ABANDON THE LIGHT"]
_result_rects: list[pygame.Rect] = []

def draw_result_screen(screen: pygame.Surface, is_win: bool, score: int, round_num: int, selected: int, frame: int) -> None:
    """
    Game Over screen matching the Main Menu aesthetic with dramatic fade-in.
    Displays the score and the round number the player reached.
    (is_win is kept for signature compatibility but the WIN state no longer exists.)
    """
    global _result_rects, _result_anim_timer
    _result_rects.clear()

    c = get_canvas()
    draw_creepy_void(c, frame)
    blit_canvas_to_screen(screen)

    # ── Animation Timings ────────────────────────────────────────────────
    t = _result_anim_timer
    # Dramatic reveal for YOU DIED
    bg_alpha    = min(255, max(0, int((t / 800.0) * 255)))
    title_alpha = min(255, max(0, int(((t - 600.0) / 1000.0) * 255)))
    score_alpha = min(255, max(0, int(((t - 1400.0) / 600.0) * 255)))
    btn_alpha   = min(255, max(0, int(((t - 1400.0) / 600.0) * 255)))

    # ── Background Fade ──────────────────────────────────────────────────
    if bg_alpha < 255:
        fade_surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        fade_surf.fill((0, 0, 0, 255 - bg_alpha))
        screen.blit(fade_surf, (0, 0))

    if _font_title is None or _font_lg is None or _font_sm is None:
        return

    w = screen.get_width()
    h = screen.get_height()
    cx = w // 2
    ty = h // 2 - 180   # Centered vertically

    # ── Title ───────────────────────────────────────────────────────────
    import settings
    is_dark = settings.language_mode != 0
    
    label = get_ui_label("result_title")
    color = C_ACCENT

    # Dynamic scaling for long titles
    base_size = 64 if is_dark else 80
    scale_factor = w / 1024.0
    
    scaled_size = int(base_size * scale_factor)
    title_f = get_gothic_font(scaled_size)

    C_DEPTH   = (45, 10, 90)
    C_OUTLINE = (255, 255, 255)
    DEPTH     = int(10 * scale_factor)
    OUTLINE   = int(3 * scale_factor)

    if title_alpha > 0:
        depth_surf   = title_f.render(label, False, C_DEPTH)
        depth_surf.set_alpha(title_alpha)
        outline_surf = title_f.render(label, False, C_OUTLINE)
        outline_surf.set_alpha(title_alpha)
        title_surf   = title_f.render(label, False, color)
        title_surf.set_alpha(title_alpha)
        title_rect   = title_surf.get_rect(centerx=cx, centery=ty)

        for d in range(DEPTH, 0, -1):
            dr = depth_surf.get_rect(centerx=cx + d, centery=ty + d)
            screen.blit(depth_surf, dr)

        for ox in range(-OUTLINE, OUTLINE + 1):
            for oy in range(-OUTLINE, OUTLINE + 1):
                if ox == 0 and oy == 0:
                    continue
                or_ = outline_surf.get_rect(centerx=cx + ox, centery=ty + oy)
                screen.blit(outline_surf, or_)

        screen.blit(title_surf, title_rect)

        # ── Separator ───────────────────────────────────────────────────────
        sep_y = title_rect.bottom + 20
        line_w = title_surf.get_width() // 2 + 60
        sep_surf = pygame.Surface((screen.get_width(), 4), pygame.SRCALPHA)
        pygame.draw.line(sep_surf, (*C_ACCENT, title_alpha), (cx - line_w, 2), (cx - 50, 2), 2)
        pygame.draw.line(sep_surf, (*C_ACCENT, title_alpha), (cx + 50, 2), (cx + line_w, 2), 2)
        screen.blit(sep_surf, (0, sep_y - 2))

    # ── Score & Round ────────────────────────────────────────────────────
    score_y = ty + 150
    if score_alpha > 0:
        sc = _font_lg.render(f"SCORE {score:06d}", False, C_WHITE)
        sc.set_alpha(score_alpha)
        screen.blit(sc, sc.get_rect(centerx=cx, centery=score_y))

        rnd_font = get_gothic_font(24)
        rnd_surf = rnd_font.render(f"REACHED ROUND {round_num}", False, C_ACCENT)
        rnd_surf.set_alpha(score_alpha)
        screen.blit(rnd_surf, rnd_surf.get_rect(centerx=cx, centery=score_y + 44))

    # ── Menu items ──────────────────────────────────────────────────────
    item_y0 = score_y + 110
    item_spacing = 80
    items = get_result_items()
    for i, label_str in enumerate(items):
        is_sel = (i == selected)
        color_item = C_WHITE if is_sel else C_DIM
        iy = item_y0 + i * item_spacing

        display_label = f"> {label_str} <" if is_sel else label_str
        
        # Always build rects so hover detection doesn't break, even if invisible
        item_s_hidden = _font_lg.render(display_label, False, color_item)
        _result_rects.append(item_s_hidden.get_rect(centerx=cx, centery=iy).inflate(40, 20))

        if btn_alpha > 0:
            item_s = _font_lg.render(display_label, False, color_item)
            item_s.set_alpha(btn_alpha)
            item_w = item_s.get_width()
            item_h = item_s.get_height()

            if is_sel:
                box_surf = pygame.Surface((item_w + 64, item_h + 16), pygame.SRCALPHA)
                pygame.draw.rect(box_surf, (25, 2, 14, btn_alpha), box_surf.get_rect())
                pygame.draw.rect(box_surf, (*C_ACCENT, btn_alpha), box_surf.get_rect(), 2)
                screen.blit(box_surf, (cx - item_w // 2 - 32, iy - item_h // 2 - 8))

            screen.blit(item_s, item_s.get_rect(centerx=cx, centery=iy))






# ---------------------------------------------------------------------------
# Difficulty Selection
# ---------------------------------------------------------------------------
_diff_rects: list[pygame.Rect] = []

def get_difficulty_items() -> list[str]:
    return get_ui_label("difficulty_items")

def draw_difficulty_select(screen: pygame.Surface, selected: int, frame: int) -> None:
    """
    Difficulty selection screen — previews Mortal / Scorched / Hellish backdrops
    for rows 0–2; procedural void when Back is highlighted.
    """
    global _diff_rects
    _diff_rects.clear()

    t = frame // 4
    if selected in (0, 1, 2):
        import backgrounds
        backgrounds.set_for_grid_index(selected)
        _draw_themed_background(screen, veil_alpha=120, frame=t)
    else:
        _draw_ui_background(screen, veil_alpha=120, frame=t)

    if _font_title is None or _font_lg is None or _font_sm is None:
        return

    w = screen.get_width()
    h = screen.get_height()
    cx = w // 2
    ty = h // 2 - 140

    # ── Title ───────────────────────────────────────────────────────────
    import settings
    is_dark = settings.language_mode != 0
    
    label = get_ui_label("difficulty_title")
    color = C_ACCENT

    # Dynamic scaling for long titles
    base_size = 64 if is_dark else 80
    scale_factor = w / 1024.0
    
    scaled_size = int(base_size * scale_factor)
    title_f = get_gothic_font(scaled_size)

    C_DEPTH   = (45, 10, 90)
    C_OUTLINE = (255, 255, 255)
    DEPTH     = int(10 * scale_factor)
    OUTLINE   = int(3 * scale_factor)

    depth_surf   = title_f.render(label, False, C_DEPTH)
    outline_surf = title_f.render(label, False, C_OUTLINE)
    title_surf   = title_f.render(label, False, color)
    title_rect   = title_surf.get_rect(centerx=cx, centery=ty)

    for d in range(DEPTH, 0, -1):
        dr = depth_surf.get_rect(centerx=cx + d, centery=ty + d)
        screen.blit(depth_surf, dr)

    for ox in range(-OUTLINE, OUTLINE + 1):
        for oy in range(-OUTLINE, OUTLINE + 1):
            if ox == 0 and oy == 0:
                continue
            or_ = outline_surf.get_rect(centerx=cx + ox, centery=ty + oy)
            screen.blit(outline_surf, or_)

    screen.blit(title_surf, title_rect)

    # ── Separator ───────────────────────────────────────────────────────
    sep_y = title_rect.bottom + 20
    pygame.draw.line(screen, C_ACCENT, (cx - 280, sep_y), (cx - 50, sep_y), 2)
    pygame.draw.line(screen, C_ACCENT, (cx + 50,  sep_y), (cx + 280, sep_y), 2)

    # ── Menu items ──────────────────────────────────────────────────────
    item_y0 = sep_y + 60
    item_spacing = 80
    items = get_difficulty_items()
    for i, label_str in enumerate(items):
        is_sel = (i == selected)
        color_item = C_WHITE if is_sel else C_DIM
        iy = item_y0 + i * item_spacing

        display_label = f"> {label_str} <" if is_sel else label_str
        item_s = _font_lg.render(display_label, False, color_item)
        item_w = item_s.get_width()
        item_h = item_s.get_height()

        if is_sel:
            box = pygame.Rect(cx - item_w // 2 - 32, iy - item_h // 2 - 8,
                              item_w + 64, item_h + 16)
            pygame.draw.rect(screen, (25, 2, 14), box)
            pygame.draw.rect(screen, C_ACCENT, box, 2)

        rect = item_s.get_rect(centerx=cx, centery=iy)
        screen.blit(item_s, rect)
        _diff_rects.append(rect.inflate(40, 20))


# ---------------------------------------------------------------------------
# Mouse Hover Helpers
# ---------------------------------------------------------------------------


def get_hovered_menu_item(mx: int, my: int) -> int | None:
    for i, r in enumerate(_menu_rects):
        if r.collidepoint(mx, my): return i
    return None

def get_hovered_pause_item(mx: int, my: int) -> int | None:
    for i, r in enumerate(_pause_rects):
        if r.collidepoint(mx, my): return i
    return None

def get_hovered_options_item(mx: int, my: int) -> int | None:
    for i, r in enumerate(_options_rects):
        if r.collidepoint(mx, my): return i
    return None

def get_hovered_result_item(mx: int, my: int) -> int | None:
    for i, r in enumerate(_result_rects):
        if r.collidepoint(mx, my): return i
    return None

def get_hovered_difficulty_item(mx: int, my: int) -> int | None:
    for i, r in enumerate(_diff_rects):
        if r.collidepoint(mx, my): return i
    return None

def get_hovered_pause_btn(mx: int, my: int) -> bool:
    return _pause_btn_rect.collidepoint(mx, my)


# ---------------------------------------------------------------------------
# Power-Up Selection (Hard Mode only)
# ---------------------------------------------------------------------------
_powerup_rects: list[pygame.Rect] = []

def draw_powerup_select(screen: pygame.Surface, selected: int, frame: int) -> None:
    """
    Pick your Power-Up screen at the start of a Hard Mode game.
    """
    global _powerup_rects
    _powerup_rects.clear()

    c = get_canvas()
    draw_creepy_void(c, frame)
    blit_canvas_to_screen(screen)

    if _font_title is None or _font_lg is None or _font_sm is None:
        return

    w = screen.get_width()
    h = screen.get_height()
    cx = w // 2
    
    # Scale factor based on 1920x1080 baseline
    sc = w / 1920.0

    # Title
    title_font = get_gothic_font(int(48 * sc))
    title_surf = title_font.render("CHOOSE YOUR POWER-UP", False, C_WHITE)
    shadow_surf = title_font.render("CHOOSE YOUR POWER-UP", False, C_ACCENT_DK)
    title_rect = title_surf.get_rect(centerx=cx, centery=int(100 * sc))
    screen.blit(shadow_surf, (title_rect.x + int(3 * sc), title_rect.y + int(3 * sc)))
    screen.blit(title_surf, title_rect)

    # Options: (Name, Description, Color, SpriteIndex)
    options = [
        ("SHIELD",     "Block 2 mismatches.", (100, 180, 255), 0),
        ("LIFESTEAL",  "Heal 5 HP per match.", (100, 255, 100), 1),
        ("EXTRA LIFE", "Revive at 30 HP once.", (255, 100, 100), 2),
    ]

    item_spacing = int(500 * sc)
    item_x_start = cx - item_spacing
    
    # Card and Font scaling
    card_w = int(276 * sc)
    card_h = int(420 * sc)
    name_font = get_gothic_font(int(36 * sc))
    desc_font = get_gothic_font(int(22 * sc))
    
    for i, (name, desc, color, spr_idx) in enumerate(options):
        is_sel = (i == selected)
        ix = item_x_start + i * item_spacing
        iy = h // 2 + int(140 * sc)
        
        # Draw Joker Sprite (Responsive Size)
        if spr_idx < len(_joker_sprites):
            spr = pygame.transform.scale(_joker_sprites[spr_idx], (card_w, card_h))
            spr_rect = spr.get_rect(centerx=ix, centery=iy - int(200 * sc))
            
            # Hover effect / Selection box
            if is_sel:
                glow_rect = spr_rect.inflate(int(20 * sc), int(20 * sc))
                pygame.draw.rect(screen, (40, 5, 25), glow_rect, border_radius=int(8 * sc))
                pygame.draw.rect(screen, C_ACCENT, glow_rect, 2, border_radius=int(8 * sc))
                # Subtle bounce
                spr_rect.y -= int(5 * math.sin(frame * 0.1))
            
            screen.blit(spr, spr_rect)
            _powerup_rects.append(spr_rect.inflate(int(20 * sc), int(100 * sc))) # hit area

        # Text
        name_s = name_font.render(name, False, C_WHITE if is_sel else C_DIM)
        screen.blit(name_s, name_s.get_rect(centerx=ix, centery=iy + int(80 * sc)))
        
        desc_s = desc_font.render(desc, False, C_WHITE if is_sel else C_DIM)
        screen.blit(desc_s, desc_s.get_rect(centerx=ix, centery=iy + int(120 * sc)))

def get_hovered_powerup_item(mx: int, my: int) -> int | None:
    for i, r in enumerate(_powerup_rects):
        if r.collidepoint(mx, my): return i
    return None


def get_options_rect(row: int) -> pygame.Rect | None:
    if 0 <= row < len(_options_rects):
        return _options_rects[row]
    return None


# ---------------------------------------------------------------------------
# Codex Screen
# ---------------------------------------------------------------------------
_codex_rects: list[pygame.Rect] = []
_codex_back_menu_rect: pygame.Rect | None = None
_codex_back_lineage_rect: pygame.Rect | None = None

_codex_anim_p: float = 0.0 # 0.0 = fan, 1.0 = center
_codex_anim_card: tuple[str, str] | None = None
_codex_anim_idx: int = -1
_CODEX_ANIM_MS = 350.0 # speed of transition
_codex_suit_hovers: list[float] = [0.0, 0.0, 0.0, 0.0]
_codex_fan_hovers: list[float] = [0.0] * 13

def _clear_codex_back_rects() -> None:
    global _codex_back_menu_rect, _codex_back_lineage_rect
    _codex_back_menu_rect = None
    _codex_back_lineage_rect = None


def _draw_codex_back_button(
    screen: pygame.Surface,
    label: str,
    margin_x: int,
    margin_y: int,
) -> pygame.Rect:
    """Gothic text back control for mouse users; returns clickable rect."""
    import settings as cfg
    sc_w = screen.get_width() / 1024.0
    font = get_gothic_font(int(22 * sc_w))
    pad_x = int(16 * sc_w)
    pad_y = int(10 * sc_w)

    plain = font.render(label, False, C_DIM)
    active = font.render(f"> {label}", False, C_WHITE)
    hit = plain.get_rect(topleft=(margin_x, margin_y)).inflate(pad_x, pad_y)

    mx, my = pygame.mouse.get_pos()
    is_hov = False
    if cfg.input_method != 1:  # Not pure keyboard
        is_hov = hit.collidepoint(mx, my)

    surf = active if is_hov else plain
    at = surf.get_rect(topleft=(margin_x, margin_y))

    if is_hov:
        box = at.inflate(pad_x, pad_y)
        pygame.draw.rect(screen, (25, 2, 14), box)
        pygame.draw.rect(screen, C_ACCENT, box, max(1, int(2 * sc_w)))

    screen.blit(surf, at)
    return hit


def get_hovered_codex_back(mx: int, my: int) -> str | None:
    """'menu' = return to main menu, 'lineage' = return to suit select."""
    if _codex_back_menu_rect and _codex_back_menu_rect.collidepoint(mx, my):
        return "menu"
    if _codex_back_lineage_rect and _codex_back_lineage_rect.collidepoint(mx, my):
        return "lineage"
    return None


def update_codex_transitions(dt_ms: float, revealed_card: tuple[str, str] | None, selected_idx: int, view_mode: int = 0, suit_idx: int = 0) -> None:
    """Drive the codex animation progress based on whether a card is revealed."""
    global _codex_anim_p, _codex_anim_card, _codex_anim_idx, _codex_suit_hovers, _codex_fan_hovers
    
    if revealed_card:
        if _codex_anim_card != revealed_card:
            # New card revealed
            _codex_anim_card = revealed_card
            _codex_anim_idx = selected_idx
            
        _codex_anim_p = min(1.0, _codex_anim_p + dt_ms / _CODEX_ANIM_MS)
    else:
        _codex_anim_p = max(0.0, _codex_anim_p - dt_ms / _CODEX_ANIM_MS)
        if _codex_anim_p <= 0:
            _codex_anim_card = None
            _codex_anim_idx = -1

    # Update suit hovers
    for i in range(4):
        target = 1.0 if (view_mode == 0 and suit_idx == i) else 0.0
        if _codex_suit_hovers[i] < target:
            _codex_suit_hovers[i] = min(target, _codex_suit_hovers[i] + dt_ms / 120.0)
        else:
            _codex_suit_hovers[i] = max(target, _codex_suit_hovers[i] - dt_ms / 120.0)

    # Update fan hovers
    for i in range(13):
        target = 1.0 if (view_mode == 1 and not revealed_card and selected_idx == i) else 0.0
        if _codex_fan_hovers[i] < target:
            _codex_fan_hovers[i] = min(target, _codex_fan_hovers[i] + dt_ms / 100.0)
        else:
            _codex_fan_hovers[i] = max(target, _codex_fan_hovers[i] - dt_ms / 100.0)

def draw_codex(
    screen: pygame.Surface,
    view_mode: int, # 0=Decks, 1=Fan
    suit_idx: int,
    selected_idx: int,
    revealed_card: tuple[str, str] | None,
    frame: int
) -> None:
    """
    Display 13 cards of a selected suit in a fan-shape at the bottom.
    Includes a suit selector at the top.
    """
    global _codex_rects, _suit_rects
    _codex_rects.clear()
    _suit_rects.clear()
    _clear_codex_back_rects()
    
    _draw_ui_background(screen, frame=frame // 4)
    
    w, h = screen.get_size()
    cx = w // 2
    
    if view_mode == 0:
        _draw_codex_suit_select(screen, suit_idx, frame)
        return
    
    # Dual scale factors
    sc_w = w / 1024.0
    sc_h = h / 768.0
    
    # Title
    title_font = get_gothic_font(int(48 * sc_w))
    title_text = get_ui_label("codex_title")
    title_surf = title_font.render(title_text, False, C_WHITE)
    shadow_surf = title_font.render(title_text, False, C_ACCENT_DK)
    title_rect = title_surf.get_rect(centerx=cx, centery=int(50 * sc_h))
    screen.blit(shadow_surf, (title_rect.x + int(3 * sc_w), title_rect.y + int(3 * sc_w)))
    screen.blit(title_surf, title_rect)
    
    # Suit Label (instead of selector)
    suits = ["Sundered", "Hollow", "Arcanum", "Grafted"]
    suit_name = suits[suit_idx]
    suit_font = get_gothic_font(int(28 * sc_w))
    s_surf = suit_font.render(suit_name.upper(), False, C_WHITE)
    s_rect = s_surf.get_rect(centerx=cx, centery=title_rect.bottom + int(40 * sc_h))
    screen.blit(s_surf, s_rect)
    
    # Static accent line below suit name
    line_y = s_rect.bottom + int(5 * sc_h)
    pygame.draw.line(screen, C_ACCENT, (s_rect.left - 20, line_y), (s_rect.right + 20, line_y), max(1, int(2 * sc_w)))

    # Fan Layout Parameters
    # We want the cards to fan out from the bottom center.
    fan_cx = w // 2
    fan_cy = h + int(320 * sc_h) # pushed further down to edge
    radius = int(520 * sc_h)
    arc_spread = math.radians(60) # total spread of the fan
    
    ranks = _RANKS
    suit = suits[suit_idx]
    
    card_w = int(90 * sc_w)
    card_h = int(140 * sc_w)
    
    for i, rank in enumerate(ranks):
        is_sel = (i == selected_idx)
        
        # Don't draw the card in the fan if it's the one transitioning/focused
        is_animating = (_codex_anim_idx == i and _codex_anim_p > 0)
        if is_animating and not revealed_card and _codex_anim_p > 0.99:
             # edge case: if we just closed but p is still 1.0, hide it
             pass
        elif is_animating:
            continue

        # Angle calculation
        angle_offset = (i - 6) * (arc_spread / 12) # -30 to +30 degrees
        angle = -math.pi/2 + angle_offset
        
        # Base position
        px = fan_cx + radius * math.cos(angle)
        py = fan_cy + radius * math.sin(angle)
        
        # Hover effect (Smooth)
        fan_lift_p = _codex_fan_hovers[i]
        ext_radius = radius + int(60 * sc_h * fan_lift_p)
        px = fan_cx + ext_radius * math.cos(angle)
        py = fan_cy + ext_radius * math.sin(angle)
            
        # Rotation
        rot_deg = -math.degrees(angle_offset)
        
        src = get_card_surf(suit, rank)
        if src:
            scaled = pygame.transform.scale(src, (card_w, card_h))
            rotated = pygame.transform.rotate(scaled, rot_deg)
            
            # Darken if any card is revealed/animating
            # We use _codex_anim_p to dim the fan
            if (revealed_card or _codex_anim_p > 0):
                dark = pygame.Surface(rotated.get_size(), pygame.SRCALPHA)
                dark.fill((0, 0, 0, int(150 * _codex_anim_p)))
                rotated.blit(dark, (0, 0))
                
            r_rect = rotated.get_rect(center=(px, py))
            _codex_rects.append(r_rect)
            
            screen.blit(rotated, r_rect)

    # Transitioning / Focused Card
    if _codex_anim_p > 0 and _codex_anim_card:
        asuit, arank = _codex_anim_card
        
        # Start (Fan) position
        angle_offset = (_codex_anim_idx - 6) * (arc_spread / 12)
        angle = -math.pi/2 + angle_offset
        start_x = fan_cx + radius * math.cos(angle)
        start_y = fan_cy + radius * math.sin(angle)
        start_rot = -math.degrees(angle_offset)
        
        # End (Left side) position
        end_x = cx - int(200 * sc_w)
        end_y = h // 2
        end_rot = 0

        # Lerp
        t = _codex_anim_p
        # Smooth step for better feel
        t_smooth = t * t * (3 - 2 * t)

        cur_x = start_x + (end_x - start_x) * t_smooth
        cur_y = start_y + (end_y - start_y) * t_smooth
        cur_rot = start_rot + (end_rot - start_rot) * t_smooth

        # Scale lerp
        large_w = int(200 * sc_w)
        large_h = int(300 * sc_w)
        cur_w = int(card_w + (large_w - card_w) * t_smooth)
        cur_h = int(card_h + (large_h - card_h) * t_smooth)

        src = get_card_surf(asuit, arank)
        if src:
            l_card = pygame.transform.scale(src, (cur_w, cur_h))
            rotated = pygame.transform.rotate(l_card, cur_rot)
            lc_rect = rotated.get_rect(center=(cur_x, cur_y))

            # Dim background further (only if p > 0)
            if _codex_anim_p > 0:
                dim = pygame.Surface((w, h), pygame.SRCALPHA)
                dim.fill((0, 0, 0, int(180 * _codex_anim_p)))
                screen.blit(dim, (0, 0))

            # Shadow/Glow
            glow_alpha = int(80 * _codex_anim_p)
            glow_r = lc_rect.inflate(int(20 * sc_w), int(20 * sc_h))
            glow_s = pygame.Surface(glow_r.size, pygame.SRCALPHA)
            pygame.draw.rect(glow_s, (*C_ACCENT, glow_alpha), glow_s.get_rect(), border_radius=int(10 * sc_w))
            screen.blit(glow_s, glow_r)

            screen.blit(rotated, lc_rect)

            # Lore Overlay (Fades in when p > 0.5)
            if _codex_anim_p > 0.5:
                lore_t = (_codex_anim_p - 0.5) / 0.5
                lore_alpha = int(255 * lore_t)

                # Title
                name_font = get_gothic_font(int(36 * sc_w))
                name_text = lore.get_title(asuit, arank)
                name_surf = name_font.render(name_text, False, C_WHITE)
                name_surf.set_alpha(lore_alpha)
                # Position on the right side
                screen.blit(name_surf, name_surf.get_rect(left=cx - int(20 * sc_w), top=end_y - large_h // 2))

                # Lore text
                l_text = lore.get_lore(asuit, arank)
                lore_font = get_gothic_font(int(22 * sc_w))
                wrap_width = int(450 * sc_w)
                words = l_text.split()
                lines = []
                cur_line = ""
                for word in words:
                    test_line = cur_line + " " + word if cur_line else word
                    if lore_font.size(test_line)[0] < wrap_width:
                        cur_line = test_line
                    else:
                        lines.append(cur_line)
                        cur_line = word
                lines.append(cur_line)

                ly = end_y - large_h // 2 + int(60 * sc_h)
                for line in lines:
                    ls = lore_font.render(line, False, C_DIM)
                    ls.set_alpha(lore_alpha)
                    screen.blit(ls, ls.get_rect(left=cx - int(20 * sc_w), top=ly))
                    ly += int(28 * sc_h)

                # Instruction to close
                hint_font = get_gothic_font(int(18 * sc_w))
                hint_text = "Press SPACE or ESC to close"
                hint_surf = hint_font.render(hint_text, False, C_ACCENT)
                hint_surf.set_alpha(lore_alpha)
                screen.blit(hint_surf, hint_surf.get_rect(left=cx - int(20 * sc_w), top=ly + int(30 * sc_h)))

    # Back to lineages (mouse + keyboard hint)
    if not revealed_card and _codex_anim_p == 0:
        global _codex_back_lineage_rect
        margin = int(24 * sc_w)
        _codex_back_lineage_rect = _draw_codex_back_button(
            screen, get_ui_label("codex_back_lineage"), margin, margin,
        )
        hint_font = get_gothic_font(int(16 * sc_w))
        hint_text = "Press ESC to return to lineages"
        hint_surf = hint_font.render(hint_text, False, C_DIM)
        screen.blit(hint_surf, hint_surf.get_rect(centerx=cx, bottom=h - int(20 * sc_h)))


def _draw_codex_suit_select(screen: pygame.Surface, selected_suit: int, frame: int) -> None:
    """Draw 4 stacks of cards, one for each suit."""
    global _codex_rects, _suit_rects
    _codex_rects.clear()
    _suit_rects.clear()

    w, h = screen.get_size()
    cx = w // 2
    sc_w = w / 1024.0
    sc_h = h / 768.0

    # Title
    title_font = get_gothic_font(int(48 * sc_w))
    title_text = get_ui_label("codex_title")
    title_surf = title_font.render(title_text, False, C_WHITE)
    title_rect = title_surf.get_rect(centerx=cx, centery=int(100 * sc_h))
    screen.blit(title_surf, title_rect)

    # Decks
    suits = ["Sundered", "Hollow", "Arcanum", "Grafted"]
    deck_w = int(120 * sc_w)
    deck_h = int(180 * sc_w)
    spacing = int(220 * sc_w)
    start_x = cx - (spacing * 1.5)

    for i, suit in enumerate(suits):
        is_sel = (i == selected_suit)
        dx = start_x + i * spacing
        dy = h // 2
        
        rect = pygame.Rect(0, 0, deck_w, deck_h)
        rect.center = (dx, dy)
        _suit_rects.append(rect) # for click detection
        
        # Hover lift (Smooth)
        lift_p = _codex_suit_hovers[i]
        dy -= int(20 * sc_h * lift_p)
            
        # Draw stack (3 cards)
        for offset in range(3, 0, -1):
            ox = dx + offset * int(3 * sc_w)
            oy = dy + offset * int(3 * sc_w)
            
            back = get_back_surf()
            if back:
                b_scaled = pygame.transform.scale(back, (deck_w, deck_h))
                screen.blit(b_scaled, b_scaled.get_rect(center=(ox, oy)))
        
        # Top card (Ace)
        ace_surf = get_card_surf(suit, "A")
        if ace_surf:
            a_scaled = pygame.transform.scale(ace_surf, (deck_w, deck_h))
            screen.blit(a_scaled, a_scaled.get_rect(center=(dx, dy)))
            
        # Highlight border removed as requested (redundant with hover lift)
            
        # Suit Label
        label_font = get_gothic_font(int(24 * sc_w))
        # Label color also transitions
        t_c = (
            int(C_DIM[0] + (C_WHITE[0] - C_DIM[0]) * lift_p),
            int(C_DIM[1] + (C_WHITE[1] - C_DIM[1]) * lift_p),
            int(C_DIM[2] + (C_WHITE[2] - C_DIM[2]) * lift_p)
        )
        l_surf = label_font.render(suit.upper(), False, t_c)
        screen.blit(l_surf, l_surf.get_rect(centerx=dx, top=dy + deck_h // 2 + int(30 * sc_h)))

    # Hint
    hint_font = get_gothic_font(int(18 * sc_w))
    hint_text = "Select a suit to view registry"
    hint_surf = hint_font.render(hint_text, False, C_ACCENT)
    screen.blit(hint_surf, hint_surf.get_rect(centerx=cx, bottom=h - int(40 * sc_h)))

    global _codex_back_menu_rect
    margin = int(24 * sc_w)
    _codex_back_menu_rect = _draw_codex_back_button(
        screen, get_ui_label("codex_back_menu"), margin, int(24 * sc_h),
    )


def get_hovered_codex_item(mx: int, my: int) -> tuple[str, int] | None:
    """Returns ('suit', idx) or ('card', idx) or None."""
    for i, r in enumerate(_suit_rects):
        if r.collidepoint(mx, my):
            return ("suit", i)
    for i, r in enumerate(_codex_rects):
        if r.collidepoint(mx, my):
            return ("card", i)
    return None


