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
_CARDS     = os.path.join(_BASE, "CARDS", "Cards", "Dark", "Separated-Cards PNG")
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


def load_fonts() -> None:
    global _font_title, _font_lg, _font_sm
    _font_title = pygame.font.SysFont("couriernew", 20, bold=True)
    _font_lg    = pygame.font.SysFont("couriernew", 10, bold=True)
    _font_sm    = pygame.font.SysFont("couriernew",  7, bold=False)


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
# Card sprite mapping
# ---------------------------------------------------------------------------
_RANKS      = ("A","2","3","4","5","6","7","8","9","10","J","Q","K")
_SUIT_START = {"Hearts": 9, "Diamonds": 22, "Clubs": 35, "Spades": 48}
CARD_BACK_IDX = 1

_card_sprites: dict[int, pygame.Surface] = {}


def load_card_sprites() -> None:
    _card_sprites.clear()
    for i in range(1, 65):
        path = os.path.join(_CARDS, f"cardsDark{i}.png")
        if os.path.exists(path):
            _card_sprites[i] = pygame.image.load(path).convert_alpha()


def _card_idx(suit: str, rank: str) -> int:
    return _SUIT_START[suit] + _RANKS.index(rank)


def get_card_surf(suit: str, rank: str) -> pygame.Surface | None:
    return _card_sprites.get(_card_idx(suit, rank))


def get_back_surf() -> pygame.Surface | None:
    return _card_sprites.get(CARD_BACK_IDX)


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
# Mismatch flash
# ---------------------------------------------------------------------------
_flash: dict[int, float] = {}
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
MENU_ITEMS = ["PLAY", "QUIT"]


def draw_menu(screen: pygame.Surface, selected: int, frame: int) -> None:
    """
    Hell is Other Demons style:
    - OBLIVIO in cold White with deep blood-red drop shadow
    - #F30261 used ONLY for accent (cursor >, separator lines, highlight box)
    - No subtitle
    """
    c = get_canvas()
    draw_creepy_void(c, frame)

    if _font_title is None or _font_lg is None or _font_sm is None:
        blit_canvas_to_screen(screen)
        return

    cx = PIXEL_W // 2
    ty = 44

    # ── OBLIVIO title ──────────────────────────────────────────────────────
    # Step 1: deep blood-red shadow at +1,+1 offset (gives weight/menace)
    shadow = _font_title.render("OBLIVIO", False, C_ACCENT_DK)
    c.blit(shadow, shadow.get_rect(centerx=cx + 1, centery=ty + 1))
        
    # Step 2: Neon Magenta title on top
    title = _font_title.render("OBLIVIO", False, C_ACCENT)
    c.blit(title, title.get_rect(centerx=cx, centery=ty))

    # ── Accent separator lines ─────────────────────────────────────────────
    sep_y = ty + 18
    pygame.draw.line(c, C_ACCENT, (cx - 70, sep_y), (cx - 12, sep_y), 1)
    pygame.draw.line(c, C_ACCENT, (cx + 12, sep_y), (cx + 70, sep_y), 1)

    # ── Menu items ─────────────────────────────────────────────────────────
    item_y0      = PIXEL_H // 2 + 16
    item_spacing = 22
    for i, label in enumerate(MENU_ITEMS):
        is_sel = (i == selected)
        color  = C_WHITE if is_sel else C_DIM
        iy     = item_y0 + i * item_spacing

        if is_sel:
            # Accent highlight box — #F30261 border, very dark fill
            item_w = _font_lg.size(label)[0]
            box    = pygame.Rect(cx - item_w // 2 - 14, iy - 6, item_w + 28, 14)
            pygame.draw.rect(c, (25, 2, 14), box)           # near-black fill
            pygame.draw.rect(c, C_ACCENT, box, 1)           # #F30261 border

        item_s = _font_lg.render(label, False, color)
        c.blit(item_s, item_s.get_rect(centerx=cx, centery=iy))

        if is_sel:
            arr = _font_lg.render(">", False, C_ACCENT)     # #F30261 cursor
            c.blit(arr, (cx - _font_lg.size(label)[0] // 2 - 13, iy - 5))

    # ── Controls hint ──────────────────────────────────────────────────────
    hint = _font_sm.render("W/S  ENTER to select", False, C_DIM)
    c.blit(hint, hint.get_rect(centerx=cx, centery=PIXEL_H - 7))

    blit_canvas_to_screen(screen)


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

    cid = id(card)
    if cid in _pulse and int(_pulse[cid]) % 12 < 6:
        gr = rect.inflate(4, 4)
        pygame.draw.rect(screen, C_MATCH, gr, width=2, border_radius=3)

    if cid in _flash:
        alpha = int(_flash[cid])
        fsurf = pygame.Surface((dw, card_h), pygame.SRCALPHA)
        fsurf.fill((*C_MISMATCH, alpha))
        screen.blit(fsurf, (bx, rect.y))


def draw_card_grid(
    screen: pygame.Surface,
    cards:  list,
    card_w: int,
    card_h: int,
) -> None:
    for card in cards:
        draw_card(screen, card, card_w, card_h)


# ---------------------------------------------------------------------------
# HUD strip  —  pixelated slanted health bar + score
# ---------------------------------------------------------------------------

def draw_hud(
    screen: pygame.Surface,
    hp:     float,
    score:  int,
    hud_h:  int,
    frame:  int,
) -> None:
    """
    HUD layout (left → right):
        [pixelated slanted bar × 2 stacked]  <gap>  SCORE 000000  (right)

    The slanted bar is scaled up 3× from its native 42×7px to be clearly
    visible at full resolution.  Two bars are stacked vertically (they
    represent one HP value together — same frame, decorative double-bar look).
    """
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

    # ── Score (right-aligned) ───────────────────────────────────────────────
    hud_font = pygame.font.SysFont("couriernew", 14, bold=True)
    sc_surf  = hud_font.render(f"SCORE  {score:06d}", False, C_WHITE)
    screen.blit(sc_surf, (w - sc_surf.get_width() - 20,
                           hud_h // 2 - sc_surf.get_height() // 2))


# ---------------------------------------------------------------------------
# ESC hint
# ---------------------------------------------------------------------------

def draw_esc_hint(screen: pygame.Surface) -> None:
    hint_font = pygame.font.SysFont("couriernew", 12, bold=False)
    hint      = hint_font.render("ESC - MENU", False, C_DIM)
    screen.blit(hint, (10, screen.get_height() - hint.get_height() - 8))
