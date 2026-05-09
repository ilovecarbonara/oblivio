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
C_DIM       = ( 90,  70, 100)   # muted UI text
C_MATCH     = (243,   2,  97)   # match glow
C_MISMATCH  = (210,  40,  40)   # mismatch flash
C_HUD_BG    = (  7,   3,  14)   # HUD strip background

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


# ---------------------------------------------------------------------------
# Card sprite mapping (FantasyCards.png)
# 
# Sheet layout: 13 columns (A, 2-10, J, Q, K), 4 rows.
# Card size: 23x35 px, with 1px transparent gap (stride is 24x36).
# 
# Rows (based on visual icons):
# 0: Spades (Red Sword)
# 1: Clubs (White Skull)
# 2: Diamonds (White Spark)
# 3: Hearts (Red Shield)
# ---------------------------------------------------------------------------
_RANKS      = ("A","2","3","4","5","6","7","8","9","10","J","Q","K")
_SUIT_ROW   = {"Spades": 0, "Clubs": 1, "Diamonds": 2, "Hearts": 3}

_card_sprites: dict[str, pygame.Surface] = {}
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
# Main Menu
# ---------------------------------------------------------------------------
MENU_ITEMS = ["PLAY", "OPTIONS", "QUIT"]
_menu_rects: list[pygame.Rect] = []

def draw_menu(screen: pygame.Surface, selected: int, frame: int) -> None:
    """
    Hell is Other Demons style:
    - OBLIVIO in cold White with deep blood-red drop shadow
    - #F30261 used ONLY for accent (cursor >, separator lines, highlight box)
    - No subtitle
    """
    global _menu_rects
    _menu_rects.clear()
    c = get_canvas()
    draw_creepy_void(c, frame)
    blit_canvas_to_screen(screen)  # chunky void background first

    if _font_title is None or _font_lg is None or _font_sm is None:
        return

    w  = screen.get_width()
    h  = screen.get_height()
    cx = w // 2
    ty = 130   # title vertical center on the 1024x768 screen

    # ── OBLIVIO title — 3-layer extruded pixel-art style ──────────────────
    C_DEPTH   = (45, 10, 90)      # deep indigo-purple block depth
    C_OUTLINE = (255, 255, 255)   # stark white outline
    DEPTH     = 10                # px of 3D block shadow
    OUTLINE   = 3                 # outline thickness

    depth_surf   = _font_title.render("OBLIVIO", False, C_DEPTH)
    outline_surf = _font_title.render("OBLIVIO", False, C_OUTLINE)
    title_surf   = _font_title.render("OBLIVIO", False, C_ACCENT)
    title_rect   = title_surf.get_rect(centerx=cx, centery=ty)

    # Step 1: stacked purple copies for the 3D block depth (down-right)
    for d in range(DEPTH, 0, -1):
        dr = depth_surf.get_rect(centerx=cx + d, centery=ty + d)
        screen.blit(depth_surf, dr)

    # Step 2: white outline — blit white text in every direction
    for ox in range(-OUTLINE, OUTLINE + 1):
        for oy in range(-OUTLINE, OUTLINE + 1):
            if ox == 0 and oy == 0:
                continue
            or_ = outline_surf.get_rect(centerx=cx + ox, centery=ty + oy)
            screen.blit(outline_surf, or_)

    # Step 3: neon magenta fill on top — use GothicByte for eerie horror look
    screen.blit(title_surf, title_rect)

    # ── Separator lines ────────────────────────────────────────────────────
    sep_y = title_rect.bottom + 20
    pygame.draw.line(screen, C_ACCENT, (cx - 280, sep_y), (cx - 50, sep_y), 2)
    pygame.draw.line(screen, C_ACCENT, (cx + 50,  sep_y), (cx + 280, sep_y), 2)

    # ── Menu items ─────────────────────────────────────────────────────────
    item_y0      = sep_y + 60
    item_spacing = 80
    for i, label in enumerate(MENU_ITEMS):
        is_sel = (i == selected)
        color  = C_WHITE if is_sel else C_DIM
        iy     = item_y0 + i * item_spacing

        item_s = _font_lg.render(label, False, color)
        item_w = item_s.get_width()
        item_h = item_s.get_height()

        if is_sel:
            box = pygame.Rect(cx - item_w // 2 - 32, iy - item_h // 2 - 8,
                              item_w + 64, item_h + 16)
            pygame.draw.rect(screen, (25, 2, 14), box)
            pygame.draw.rect(screen, C_ACCENT, box, 2)

        screen.blit(item_s, item_s.get_rect(centerx=cx, centery=iy))
        _menu_rects.append(item_s.get_rect(centerx=cx, centery=iy).inflate(40, 20))

        if is_sel:
            arr = _font_lg.render(">", False, C_ACCENT)
            screen.blit(arr, (cx - item_w // 2 - 44, iy - arr.get_height() // 2))

    # -- Controls hint --
    hint = _font_sm.render("WASD / Arrows  |  ENTER to select", False, C_DIM)
    screen.blit(hint, hint.get_rect(centerx=cx, centery=h - 32))


# ---------------------------------------------------------------------------
# Game-screen background
# ---------------------------------------------------------------------------

def draw_game_bg(screen: pygame.Surface, frame: int) -> None:
    c = get_canvas()
    draw_creepy_void(c, frame)
    blit_canvas_to_screen(screen)
    # Dark veil so cards remain readable over the void
    veil = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    veil.fill((0, 0, 0, 155))
    screen.blit(veil, (0, 0))


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
    if cid == _hovered_card_id and card.state == CardState.FACE_DOWN:
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
    if _cursor_grid_pos is not None and card.grid_pos == _cursor_grid_pos:
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
    cursor_pos: tuple[int, int] | None = None,
) -> None:
    set_cursor(cursor_pos)
    for card in cards:
        draw_card(screen, card, card_w, card_h)

    # Draw persistent multiplier badge on the top right corner of the grid
    if multiplier > 1.0 and cards:
        max_x = max(c.rect.right for c in cards)
        min_y = min(c.rect.top for c in cards)
        
        font = get_gothic_font(42)  # slightly larger and juicy
        
        # Text and shadow
        text_surf = font.render(f"{multiplier:.1f}x", False, C_ACCENT)
        shadow_surf = font.render(f"{multiplier:.1f}x", False, C_ACCENT_DK)
        
        # Tilt to the right
        text_surf = pygame.transform.rotate(text_surf, -15)
        shadow_surf = pygame.transform.rotate(shadow_surf, -15)
        
        # Position offset: place the bottom-left of the text near the top-right of the grid
        tw = text_surf.get_width()
        th = text_surf.get_height()
        tx = max_x - tw // 2 + 10
        ty = min_y - th // 2 - 10
        
        screen.blit(shadow_surf, (tx + 4, ty + 4))
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

def draw_hud(
    screen: pygame.Surface,
    hp:     float,
    score:  int,
    multiplier: float,
    hud_h:  int,
    frame:  int,
) -> None:
    global _prev_score, _score_juice

    w = screen.get_width()

    pygame.draw.rect(screen, C_HUD_BG, (0, 0, w, hud_h))
    pygame.draw.line(screen, C_ACCENT, (0, hud_h - 1), (w, hud_h - 1), 1)

    set_hp(hp)
    _tick_hp()

    # ── Pixelated health bar ────────────────────────────────────────────────
    if _PX_BAR_FRAMES:
        fidx = _hp_to_frame_idx(_hp_drawn)
        bar_surf = _PX_BAR_FRAMES[fidx]

        # Scale up 4× (nearest-neighbour) so the pixel art stays chunky
        bar_display_w = _BAR_W * 4
        bar_display_h = _BAR_H * 4
        bar_scaled = pygame.transform.scale(bar_surf, (bar_display_w, bar_display_h))

        # Single bar, centered vertically in the HUD strip
        bar_x     = 14
        bar_top_y = hud_h // 2 - bar_display_h // 2
        screen.blit(bar_scaled, (bar_x, bar_top_y))
    else:
        # Fallback drawn bar if sprite not loaded
        bar_x = 14
        bar_display_w = 168
        bar_display_h = 12
        bar_top_y = hud_h // 2 - bar_display_h
        fill_w = max(0, int(bar_display_w * (_hp_drawn / 100.0)))
        pygame.draw.rect(screen, (25, 10, 35), (bar_x, bar_top_y, bar_display_w, bar_display_h))
        if fill_w > 0:
            pygame.draw.rect(screen, C_ACCENT, (bar_x, bar_top_y, fill_w, bar_display_h))
        pygame.draw.rect(screen, C_ACCENT_DK, (bar_x, bar_top_y, bar_display_w, bar_display_h), 1)

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


# ---------------------------------------------------------------------------
# ESC hint
# ---------------------------------------------------------------------------

def draw_esc_hint(screen: pygame.Surface) -> None:
    hint_font = get_gothic_font(18)
    lines = [
        "ESC - PAUSE",
        "WASD / Arrow Keys - move   SPACE - flip card",
    ]
    y = screen.get_height() - hint_font.get_height() * len(lines) - 10
    for line in lines:
        surf = hint_font.render(line, False, C_DIM)
        screen.blit(surf, (10, y))
        y += hint_font.get_height() + 2


# ---------------------------------------------------------------------------
# Pause overlay  —  drawn ON TOP of the frozen game frame
# ---------------------------------------------------------------------------
PAUSE_ITEMS = ["RESUME", "RESTART", "OPTIONS", "QUIT"]
_pause_rects: list[pygame.Rect] = []

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
    title_surf = title_font.render("PAUSED", False, C_WHITE)
    shadow_surf = title_font.render("PAUSED", False, C_ACCENT_DK)
    title_rect = title_surf.get_rect(centerx=cx, centery=h // 2 - 120)
    screen.blit(shadow_surf, (title_rect.x + 3, title_rect.y + 3))
    screen.blit(title_surf, title_rect)

    # Separator
    sep_y = title_rect.bottom + 12
    pygame.draw.line(screen, C_ACCENT, (cx - 160, sep_y), (cx + 160, sep_y), 2)

    # Menu items
    item_y0 = sep_y + 40
    item_spacing = 60
    for i, label in enumerate(PAUSE_ITEMS):
        is_sel = (i == selected)
        color = C_WHITE if is_sel else C_DIM
        iy = item_y0 + i * item_spacing

        item_s = _font_lg.render(label, False, color)
        item_w = item_s.get_width()
        item_h = item_s.get_height()

        if is_sel:
            box = pygame.Rect(cx - item_w // 2 - 32, iy - item_h // 2 - 8,
                              item_w + 64, item_h + 16)
            pygame.draw.rect(screen, (25, 2, 14), box)
            pygame.draw.rect(screen, C_ACCENT, box, 2)

        screen.blit(item_s, item_s.get_rect(centerx=cx, centery=iy))
        _pause_rects.append(item_s.get_rect(centerx=cx, centery=iy).inflate(40, 20))

        if is_sel:
            arr = _font_lg.render(">", False, C_ACCENT)
            screen.blit(arr, (cx - item_w // 2 - 44, iy - arr.get_height() // 2))

    # Controls hint
    hint = _font_sm.render("WASD / Arrows  |  ENTER to select", False, C_DIM)
    screen.blit(hint, hint.get_rect(centerx=cx, centery=h - 32))


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
    "",              # APPLY & BACK button row
]
_options_rects: list[pygame.Rect] = []


def _draw_volume_bar(
    screen: pygame.Surface,
    x: int, y: int,
    width: int, height: int,
    value: float,
    is_selected: bool,
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
    pygame.draw.rect(screen, border_color, (x, y, width, height), 2)

    # Percentage text
    pct_font = get_gothic_font(18)
    pct_text = f"{int(value * 100)}%"
    pct_surf = pct_font.render(pct_text, False, C_WHITE if is_selected else C_DIM)
    screen.blit(pct_surf, (x + width + 14, y + height // 2 - pct_surf.get_height() // 2))


def draw_options_menu(
    screen: pygame.Surface,
    settings,
    selected_row: int,
    frame: int,
    origin: str,
) -> None:
    """
    Full-screen options menu.  ``settings`` is the settings module.
    ``origin`` is 'menu' or 'pause' — changes the back-button label.
    """
    global _options_rects
    if selected_row == 0:  # Only clear when starting to draw the first row, wait no, this runs per frame
        pass # Actually we should clear before the loop.
    _options_rects.clear()

    c = get_canvas()
    draw_creepy_void(c, frame)
    blit_canvas_to_screen(screen)

    w = screen.get_width()
    h = screen.get_height()
    cx = w // 2

    if _font_lg is None or _font_sm is None:
        return

    # ── Title ───────────────────────────────────────────────────────────
    title_font = get_gothic_font(48)
    title_surf = title_font.render("OPTIONS", False, C_WHITE)
    shadow_surf = title_font.render("OPTIONS", False, C_ACCENT_DK)
    title_rect = title_surf.get_rect(centerx=cx, centery=80)
    screen.blit(shadow_surf, (title_rect.x + 3, title_rect.y + 3))
    screen.blit(title_surf, title_rect)

    # Separator
    sep_y = title_rect.bottom + 12
    pygame.draw.line(screen, C_ACCENT, (cx - 240, sep_y), (cx + 240, sep_y), 2)

    # ── Settings rows ──────────────────────────────────────────────────
    row_y0 = sep_y + 40
    row_spacing = 60
    label_font = get_gothic_font(22)
    value_font = get_gothic_font(22)

    label_x = cx - 280   # left-aligned labels
    value_x = cx + 40    # right-aligned values area

    for row in range(6):
        is_sel = (row == selected_row)
        ry = row_y0 + row * row_spacing
        color = C_WHITE if is_sel else C_DIM

        # Row 5 is the APPLY & BACK button
        if row == 5:
            btn_label = "APPLY & BACK"
            btn_surf = _font_lg.render(btn_label, False, color)
            btn_w = btn_surf.get_width()
            btn_h = btn_surf.get_height()
            btn_y = ry

            if is_sel:
                box = pygame.Rect(cx - btn_w // 2 - 32, btn_y - btn_h // 2 - 8,
                                  btn_w + 64, btn_h + 16)
                pygame.draw.rect(screen, (25, 2, 14), box)
                pygame.draw.rect(screen, C_ACCENT, box, 2)
                arr = _font_lg.render(">", False, C_ACCENT)
                screen.blit(arr, (cx - btn_w // 2 - 44, btn_y - arr.get_height() // 2))

            screen.blit(btn_surf, btn_surf.get_rect(centerx=cx, centery=btn_y))
            _options_rects.append(btn_surf.get_rect(centerx=cx, centery=btn_y).inflate(64, 16))
            continue

        # Label
        lbl_surf = label_font.render(_OPT_LABELS[row], False, color)
        screen.blit(lbl_surf, (label_x, ry - lbl_surf.get_height() // 2))

        # Row highlight line
        if is_sel:
            hl_y = ry + lbl_surf.get_height() // 2 + 4
            pygame.draw.line(screen, C_ACCENT,
                             (label_x, hl_y),
                             (label_x + lbl_surf.get_width(), hl_y), 1)
                             
        row_rect = pygame.Rect(cx - 300, ry - 15, 600, 30)
        _options_rects.append(row_rect)

        # Value display
        if row == 0:  # Display Mode
            mode_label = settings.current_display_mode_label()
            val_str = f"< {mode_label} >"
            val_surf = value_font.render(val_str, False, color)
            screen.blit(val_surf, (value_x, ry - val_surf.get_height() // 2))

        elif row == 1:  # Resolution
            res_w, res_h = settings.current_resolution()
            val_str = f"< {res_w} x {res_h} >"
            val_surf = value_font.render(val_str, False, color)
            screen.blit(val_surf, (value_x, ry - val_surf.get_height() // 2))

        elif row == 2:  # Master Volume
            _draw_volume_bar(screen, value_x, ry - 10, 200, 20,
                             settings.master_volume, is_sel)

        elif row == 3:  # Music Volume
            _draw_volume_bar(screen, value_x, ry - 10, 200, 20,
                             settings.music_volume, is_sel)

        elif row == 4:  # SFX Volume
            _draw_volume_bar(screen, value_x, ry - 10, 200, 20,
                             settings.sfx_volume, is_sel)

    # ── Controls hint ──────────────────────────────────────────────────
    hint1 = _font_sm.render("UP/DOWN - navigate  |  LEFT/RIGHT - adjust", False, C_DIM)
    hint2 = _font_sm.render("ENTER - apply & back  |  ESC - back", False, C_DIM)
    screen.blit(hint1, hint1.get_rect(centerx=cx, centery=h - 56))
    screen.blit(hint2, hint2.get_rect(centerx=cx, centery=h - 28))

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

def get_options_rect(row: int) -> pygame.Rect | None:
    if 0 <= row < len(_options_rects):
        return _options_rects[row]
    return None

