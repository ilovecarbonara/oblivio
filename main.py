"""
main.py — Entry point for Oblivio.

Initialises Pygame, creates the window, and runs the main game loop.
Rendering is delegated to Jim's ui.py (low-res pixel canvas system).

Owner: Jay (game logic) / Jim (ui.py wiring)
"""

import os
import sys

# Nearest-neighbour / point filtering for all SDL scaled output (must be before pygame.init)
os.environ.setdefault("SDL_RENDER_SCALE_QUALITY", "0")

import pygame

from card import Card, CardState
from game import Game, GameState, Difficulty, GRACE_MISM_COUNT
import grid
import ui
import audio
import backgrounds
import settings as cfg


# ---------------------------------------------------------------------------
# Window / display constants
# ---------------------------------------------------------------------------
WINDOW_TITLE = "Oblivio"
TARGET_FPS   = 60
EVENT_SELECT = pygame.USEREVENT + 1

# ---------------------------------------------------------------------------
# Layout constants — shared by grid.generate_grid() and the HUD renderer
# ---------------------------------------------------------------------------
CARD_W   = 90
CARD_H   = 120
PADDING  = 12
HUD_H    = 60   # height reserved at top for HP bar / score (Jim's HUD area)




# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def get_grid_layout(diff: Difficulty, win_w: int, win_h: int) -> tuple[int, int, tuple[int, int]]:
    """Return (card_w, card_h, origin_xy) dynamically scaled to fit the screen."""
    max_w = win_w - 80
    max_h = win_h - HUD_H - 40
    cw_w = (max_w - (diff.cols - 1) * PADDING) / diff.cols
    cw_h = (max_h - (diff.rows - 1) * PADDING) / (diff.rows * 4 / 3)
    
    cw = max(20, int(min(cw_w, cw_h, CARD_W)))
    ch = int(cw * 4 / 3)
    
    grid_w = diff.cols * cw + (diff.cols - 1) * PADDING
    grid_h = diff.rows * ch + (diff.rows - 1) * PADDING
    origin = (
        (win_w - grid_w) // 2,
        HUD_H + (win_h - HUD_H - grid_h) // 2,
    )
    return cw, ch, origin


def _reposition_grid(game: Game, current_cw: int, current_ch: int, win_w: int, win_h: int) -> tuple[int, int]:
    """Recalculate card pixel positions after a resolution change (preserves card states)."""
    if not game.cards:
        return current_cw, current_ch

    new_cw, new_ch, origin = get_grid_layout(game.difficulty, win_w, win_h)
    for card in game.cards:
        col, row = card.grid_pos
        px = origin[0] + col * (new_cw + PADDING)
        py = origin[1] + row * (new_ch + PADDING)
        card.rect = pygame.Rect(px, py, new_cw, new_ch)
    return new_cw, new_ch


# ---------------------------------------------------------------------------
# Options-menu input helpers
# ---------------------------------------------------------------------------
_OPTIONS_ROW_COUNT = 8   # rows 0-5 = settings, row 6 = Language, row 7 = APPLY & BACK


def _options_adjust(row: int, direction: int, data: dict) -> None:
    """
    Adjust the setting on the given row by *direction* (-1 = left, +1 = right).
    Changes are made to the provided *data* dict and NOT applied/saved immediately.
    """
    if row == 0:  # Display Mode
        data["display_mode"] = (data["display_mode"] + direction) % len(cfg.DISPLAY_MODES)

    elif row == 1:  # Resolution
        data["resolution"] = (data["resolution"] + direction) % len(cfg.RESOLUTIONS)

    elif row == 2:  # Master Volume
        data["master_volume"] = round(max(0.0, min(1.0, data["master_volume"] + direction * 0.1)), 2)
        audio.apply_volumes(data["master_volume"], data["music_volume"], data["sfx_volume"])
        audio.sfx_hover()

    elif row == 3:  # Music Volume
        data["music_volume"] = round(max(0.0, min(1.0, data["music_volume"] + direction * 0.1)), 2)
        audio.apply_volumes(data["master_volume"], data["music_volume"], data["sfx_volume"])

    elif row == 4:  # SFX Volume
        data["sfx_volume"] = round(max(0.0, min(1.0, data["sfx_volume"] + direction * 0.1)), 2)
        audio.apply_volumes(data["master_volume"], data["music_volume"], data["sfx_volume"])
        audio.sfx_hover()

    elif row == 5:  # Input Method
        data["input_method"] = (data["input_method"] + direction) % len(cfg.INPUT_METHODS)

    elif row == 6:  # Language
        data["language_mode"] = (data["language_mode"] + direction) % len(cfg.LANGUAGE_MODES)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    pygame.init()
    pygame.mixer.init()
    pygame.display.set_caption(WINDOW_TITLE)
    pygame.key.set_repeat(300, 60)

    # Load and apply persistent settings
    cfg.load()
    screen = cfg.apply_display(pygame.display.set_mode(cfg.current_resolution()))
    cfg.apply_audio()

    win_w, win_h = screen.get_size()

    clock = pygame.time.Clock()

    # Initialise audio (loads all SFX, applies volumes)
    audio.init(
        master_vol = cfg.master_volume,
        music_vol  = cfg.music_volume,
        sfx_vol    = cfg.sfx_volume,
    )
    audio.bgm_play_menu()   # start menu BGM immediately

    # Load all UI assets
    ui.load_fonts()
    ui.load_card_sprites()
    ui.load_health_sprites()
    backgrounds.init()
    backgrounds.set_default()

    game            = Game()   # starts in MENU state
    menu_selected   = 0        # 0=PLAY  1=OPTIONS  2=QUIT
    grid_selected   = 0        # 0=Easy  1=Medium  2=Hard
    result_selected = 0        # 0=Play Again  1=Main Menu
    pause_selected  = 0        # 0=Resume  1=Restart  2=Options
    powerup_selected = 0       # 0=Shield  1=Lifesteal  2=Revive
    options_selected = 0       # 0-5 (rows in options menu)
    codex_selected   = 0       # 0-12 (cards in current suit)
    codex_suit_idx   = 0       # 0-3 (Sundered, Hollow, Arcanum, Grafted)
    codex_view_mode  = 0       # 0=Deck Select, 1=Fan View
    codex_revealed_card: tuple[str, str] | None = None
    _codex_scroll_dragging:   bool = False   # True while thumb is being dragged
    _codex_scroll_drag_start_y:    int = 0   # mouse y when drag began
    _codex_scroll_drag_start_step: int = 0   # scroll step value when drag began
    _SCROLL_REPEAT_INITIAL: float = 400.0    # ms before hold-repeat begins
    _SCROLL_REPEAT_RATE:    float = 70.0     # ms between repeated scroll steps
    _scroll_btn_held: str | None = None      # 'up' or 'down' while button is held
    _scroll_btn_held_timer: float = 0.0      # countdown to next repeat fire
    options_origin  = "menu"   # "menu" or "pause" — where we came from
    frame           = 0
    _next_round_wait = 0.0     # used for perfection popup delay

    current_cw      = CARD_W
    current_ch      = CARD_H

    # Keyboard cursor for card selection during PLAYING state.
    # Tracks (col, row) within the active grid; None when not playing.
    cursor_pos: tuple[int, int] | None = None

    # Previous game state — used to detect transitions (e.g. → GAME_OVER)
    _prev_state: GameState = game.state

    # Hover trackers — play sfx_hover() only on first frame a new item is highlighted
    _prev_menu_sel:    int = menu_selected
    _prev_grid_sel:    int = grid_selected
    _prev_pause_sel:   int = pause_selected
    _prev_powerup_sel: int = powerup_selected
    _prev_options_sel: int = options_selected
    _prev_result_sel:  int = result_selected
    _prev_codex_sel:   int = codex_selected
    _prev_codex_suit:  int = codex_suit_idx
    _prev_hovered_card       = None   # tracks mouse-hover card changes in PLAYING


    options_data = {
        "display_mode":  cfg.display_mode,
        "resolution":    cfg.resolution,
        "master_volume": cfg.master_volume,
        "music_volume":  cfg.music_volume,
        "sfx_volume":    cfg.sfx_volume,
        "input_method":  cfg.input_method,
        "language_mode": cfg.language_mode,
    }

    running = True
    dt_ms   = 0.0          # milliseconds since last frame
    while running:
        # Update mouse visibility based on input method
        pygame.mouse.set_visible(cfg.input_method != 1)

        # -------------------------------------------------- events
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEMOTION:
                if cfg.input_method == 1: continue
                mx, my = event.pos
                if game.state == GameState.MENU:
                    idx = ui.get_hovered_menu_item(mx, my)
                    if idx is not None: menu_selected = idx
                elif game.state == GameState.PAUSED:
                    idx = ui.get_hovered_pause_item(mx, my)
                    if idx is not None: pause_selected = idx
                elif game.state == GameState.OPTIONS:
                    idx = ui.get_hovered_options_item(mx, my)
                    if idx is not None: options_selected = idx
                    
                    # Handle slider dragging
                    if pygame.mouse.get_pressed()[0] and options_selected in (2, 3, 4):
                        value_x = (win_w // 2) + 40
                        slider_w = 200
                        if value_x - 20 <= mx <= value_x + slider_w + 20:
                            pct = (mx - value_x) / slider_w
                            pct = round(max(0.0, min(1.0, pct)), 2)
                            if options_selected == 2: 
                                options_data["master_volume"] = pct
                            elif options_selected == 3: 
                                options_data["music_volume"] = pct
                            elif options_selected == 4: 
                                options_data["sfx_volume"] = pct
                            
                            # Real-time audio update
                            audio.apply_volumes(options_data["master_volume"], options_data["music_volume"], options_data["sfx_volume"])
                            
                elif game.state == GameState.GRID_SELECT:
                    idx = ui.get_hovered_difficulty_item(mx, my)
                    if idx is not None: grid_selected = idx

                elif game.state == GameState.GAME_OVER:
                    idx = ui.get_hovered_result_item(mx, my)
                    if idx is not None: result_selected = idx
                
                elif game.state == GameState.POWERUP_SELECT:
                    idx = ui.get_hovered_powerup_item(mx, my)
                    if idx is not None: powerup_selected = idx
                
                elif game.state == GameState.CODEX:
                    if _codex_scroll_dragging and codex_view_mode == 0:
                        ui.set_codex_desc_scroll_from_drag(
                            my, _codex_scroll_drag_start_y, _codex_scroll_drag_start_step
                        )
                    else:
                        res = ui.get_hovered_codex_item(mx, my)
                        if res:
                            type, idx = res
                            if type == "card":
                                codex_selected = idx

            elif event.type == pygame.KEYDOWN:
                if cfg.input_method == 2 and event.key != pygame.K_ESCAPE:
                    continue

                # =====================================================
                # ESC  —  context-dependent
                # =====================================================
                if event.key == pygame.K_ESCAPE:
                    if game.state == GameState.PLAYING:
                        audio.bgm_pause()
                        audio.heartbeat_stop()
                        audio.sfx_popup()
                        game.to_pause()
                        pause_selected = 0
                    elif game.state == GameState.PAUSED:
                        audio.bgm_resume()
                        audio.sfx_cancel()
                        game.resume()
                    elif game.state == GameState.OPTIONS:
                        audio.sfx_cancel()
                        def _from_options_esc_cb():
                            nonlocal screen, win_w, win_h, current_cw, current_ch
                            # Revert volumes to persistent settings
                            audio.apply_volumes(cfg.master_volume, cfg.music_volume, cfg.sfx_volume)
                            screen = cfg.apply_display(screen)
                            win_w, win_h = screen.get_size()
                            backgrounds.invalidate_cache()
                            if game.cards:
                                current_cw, current_ch = _reposition_grid(game, current_cw, current_ch, win_w, win_h)
                            game.from_options()
                        ui.start_transition(_from_options_esc_cb)
                    elif game.state == GameState.GRID_SELECT:
                        audio.sfx_cancel()
                        def _to_menu_cb():
                            game.to_menu()
                        ui.start_transition(_to_menu_cb)
                    elif game.state == GameState.POWERUP_SELECT:
                        audio.sfx_cancel()
                        def _to_menu_cb():
                            nonlocal cursor_pos
                            game.to_menu()
                            cursor_pos = None
                            audio.bgm_play_menu()
                        ui.start_transition(_to_menu_cb)
                    elif game.state == GameState.GAME_OVER:
                        audio.sfx_cancel()
                        def _to_menu_cb():
                            nonlocal cursor_pos
                            game.to_menu()
                            cursor_pos = None
                            audio.bgm_play_menu()
                        ui.start_transition(_to_menu_cb)
                    elif game.state == GameState.CODEX:
                        if codex_revealed_card:
                            audio.sfx_flip()
                            codex_revealed_card = None
                        elif codex_view_mode == 1:
                            audio.sfx_cancel()
                            codex_view_mode = 0
                        else:
                            audio.sfx_cancel()
                            def _to_menu_cb():
                                game.to_menu()
                            ui.start_transition(_to_menu_cb)
                    else:
                        running = False

                # =====================================================
                # UP / W
                # =====================================================
                elif event.key in (pygame.K_UP, pygame.K_w):
                    if game.state == GameState.MENU:
                        menu_selected = (menu_selected - 1) % len(ui.get_menu_items())
                    elif game.state == GameState.GRID_SELECT:
                        grid_selected = (grid_selected - 1) % 4
                    elif game.state == GameState.PLAYING and cursor_pos is not None:
                        cx, cy = cursor_pos
                        new_pos = (cx, max(0, cy - 1))
                        if new_pos != cursor_pos:
                            audio.sfx_cursor()
                        cursor_pos = new_pos
                    elif game.state == GameState.GAME_OVER:
                        result_selected = (result_selected - 1) % 2
                    elif game.state == GameState.PAUSED:
                        pause_selected = (pause_selected - 1) % len(ui.get_pause_items())
                    elif game.state == GameState.OPTIONS:
                        options_selected = (options_selected - 1) % _OPTIONS_ROW_COUNT
                    elif game.state == GameState.CODEX:
                        if not codex_revealed_card:
                            if codex_view_mode == 0:
                                ui.scroll_codex_desc(-1)

                # =====================================================
                # DOWN / S
                # =====================================================
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    if game.state == GameState.MENU:
                        menu_selected = (menu_selected + 1) % len(ui.get_menu_items())
                    elif game.state == GameState.GRID_SELECT:
                        grid_selected = (grid_selected + 1) % 4
                    elif game.state == GameState.PLAYING and cursor_pos is not None:
                        cx, cy = cursor_pos
                        new_pos = (cx, min(game.difficulty.rows - 1, cy + 1))
                        if new_pos != cursor_pos:
                            audio.sfx_cursor()
                        cursor_pos = new_pos
                    elif game.state == GameState.GAME_OVER:
                        result_selected = (result_selected + 1) % 2
                    elif game.state == GameState.PAUSED:
                        pause_selected = (pause_selected + 1) % len(ui.get_pause_items())
                    elif game.state == GameState.OPTIONS:
                        options_selected = (options_selected + 1) % _OPTIONS_ROW_COUNT
                    elif game.state == GameState.CODEX:
                        if not codex_revealed_card:
                            if codex_view_mode == 0:
                                ui.scroll_codex_desc(+1)

                # =====================================================
                # LEFT / A
                # =====================================================
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    if game.state == GameState.PLAYING and cursor_pos is not None:
                        cx, cy = cursor_pos
                        new_pos = (max(0, cx - 1), cy)
                        if new_pos != cursor_pos:
                            audio.sfx_cursor()
                        cursor_pos = new_pos
                    elif game.state == GameState.POWERUP_SELECT:
                        powerup_selected = (powerup_selected - 1) % 3
                    elif game.state == GameState.OPTIONS:
                        _options_adjust(options_selected, -1, options_data)
                    elif game.state == GameState.CODEX:
                        if not codex_revealed_card:
                            if codex_view_mode == 0:
                                audio.sfx_cursor()
                                codex_suit_idx = (codex_suit_idx - 1) % 4
                                ui.reset_codex_desc_scroll()
                            else:
                                codex_selected = (codex_selected - 1) % 13

                # =====================================================
                # RIGHT / D
                # =====================================================
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    if game.state == GameState.PLAYING and cursor_pos is not None:
                        cx, cy = cursor_pos
                        new_pos = (min(game.difficulty.cols - 1, cx + 1), cy)
                        if new_pos != cursor_pos:
                            audio.sfx_cursor()
                        cursor_pos = new_pos
                    elif game.state == GameState.POWERUP_SELECT:
                        powerup_selected = (powerup_selected + 1) % 3
                    elif game.state == GameState.OPTIONS:
                        _options_adjust(options_selected, +1, options_data)
                    elif game.state == GameState.CODEX:
                        if not codex_revealed_card:
                            if codex_view_mode == 0:
                                audio.sfx_cursor()
                                codex_suit_idx = (codex_suit_idx + 1) % 4
                                ui.reset_codex_desc_scroll()
                            else:
                                codex_selected = (codex_selected + 1) % 13

                # =====================================================
                # ENTER / SPACE / MOUSE SELECT -> MOVED OUTSIDE KEYDOWN
                # =====================================================

            # =====================================================
            # SELECTION HANDLER (outside KEYDOWN block)
            # =====================================================
            if event.type == EVENT_SELECT or (event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE)):
                # If it's a keyboard event, check if we're in Mouse Only mode
                if event.type == pygame.KEYDOWN and cfg.input_method == 2:
                    continue

                # --- Main Menu ---
                if game.state == GameState.MENU and not ui.is_transition_active():
                    if menu_selected == 0:         # PLAY
                        audio.sfx_select()
                        def _to_grid_select_cb():
                            nonlocal grid_selected
                            game.to_grid_select()
                            grid_selected = 0
                        ui.start_transition(_to_grid_select_cb)
                    elif menu_selected == 1:       # CODEX
                        audio.sfx_select()
                        def _to_codex_cb():
                            nonlocal codex_selected, codex_revealed_card
                            game.to_codex()
                            codex_selected = 0
                            codex_suit_idx = 0
                            codex_view_mode = 0
                            codex_revealed_card = None
                            ui.reset_codex_desc_scroll()
                        ui.start_transition(_to_codex_cb)
                    elif menu_selected == 2:       # OPTIONS
                        audio.sfx_select()
                        def _to_options_cb():
                            nonlocal options_origin, options_selected
                            options_origin = "menu"
                            options_selected = 0
                            # Sync temp scratchpad with current configuration
                            options_data.update({
                                "display_mode":  cfg.display_mode,
                                "resolution":    cfg.resolution,
                                "master_volume": cfg.master_volume,
                                "music_volume":  cfg.music_volume,
                                "sfx_volume":    cfg.sfx_volume,
                                "input_method":  cfg.input_method,
                                "language_mode": cfg.language_mode,
                            })
                            game.to_options(GameState.MENU)
                        ui.start_transition(_to_options_cb)
                    elif menu_selected == 3:       # QUIT
                        audio.sfx_select()
                        running = False

                elif game.state == GameState.CODEX:
                    if codex_revealed_card:
                        audio.sfx_flip()
                        codex_revealed_card = None
                    elif codex_view_mode == 0:
                        audio.sfx_flip()
                        codex_view_mode = 1
                        codex_selected = 0
                    else:
                        audio.sfx_flip()
                        suits = ["Sundered", "Hollow", "Arcanum", "Grafted"]
                        suit = suits[codex_suit_idx]
                        rank = ui._RANKS[codex_selected]
                        codex_revealed_card = (suit, rank)

                # --- Grid Select ---
                elif game.state == GameState.GRID_SELECT and not ui.is_transition_active():
                    if grid_selected == 3:  # Back
                        audio.sfx_cancel()
                        def _to_menu_cb():
                            game.to_menu()
                        ui.start_transition(_to_menu_cb)
                    else:
                        diff = list(Difficulty)[grid_selected]
                        audio.sfx_select()
                        # Capture locals for the closure
                        _diff = diff
                        def _start_game_cb():
                            nonlocal current_cw, current_ch, cursor_pos
                            _cw, _ch, _origin = get_grid_layout(_diff, win_w, win_h)
                            current_cw, current_ch = _cw, _ch
                            _cards = grid.generate_grid(_diff, _cw, _ch, PADDING, _origin)
                            game.start_game(_diff, _cards)
                            backgrounds.set_for_difficulty(_diff)
                            cursor_pos = (0, 0)
                            ui.start_preview(_cards)
                            if game.state == GameState.POWERUP_SELECT:
                                audio.bgm_play_menu()
                            else:
                                audio.bgm_play_game(_diff.label)
                            print(f"[INFO] Game started — difficulty: {_diff.label} ({_diff.cols}×{_diff.rows})")
                        ui.start_transition(_start_game_cb)

                # --- Powerup Select ---
                elif game.state == GameState.POWERUP_SELECT:
                    audio.sfx_flip()
                    if powerup_selected == 0: # SHIELD
                        game.shield_charges = 2
                    elif powerup_selected == 1: # LIFESTEAL
                        game.lifesteal_active = True
                    elif powerup_selected == 2: # EXTRA LIFE
                        game.has_extra_life = True
                    game.state = GameState.PLAYING
                    audio.bgm_stop()                        # force-stop menu BGM channel
                    audio.bgm_play_game(game.difficulty.label)

                # --- Playing (Flip card) ---
                elif (event.type == EVENT_SELECT or (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE)) and game.state == GameState.PLAYING:
                    if cursor_pos is not None and not game.lock_input and not ui.is_preview_active():
                            target = next(
                                (c for c in game.cards if c.grid_pos == cursor_pos),
                                None,
                            )
                            if target is not None:
                                clicked = game.handle_click(target.rect.center)
                                if clicked and not ui.is_flipping(clicked):
                                    result = game.flip_card(clicked)
                                    if result is not None:
                                        audio.sfx_flip()
                                        ui.start_flip(clicked)

                # --- Paused ---
                elif game.state == GameState.PAUSED and not ui.is_transition_active():
                    if pause_selected == 0:        # RESUME
                        audio.bgm_resume()
                        audio.sfx_cancel()
                        game.resume()
                    elif pause_selected == 1:      # RESTART
                        audio.sfx_select()
                        _diff_r = game.difficulty
                        def _restart_cb():
                            nonlocal current_cw, current_ch, cursor_pos
                            _cw, _ch, _origin = get_grid_layout(_diff_r, win_w, win_h)
                            current_cw, current_ch = _cw, _ch
                            _cards = grid.generate_grid(_diff_r, _cw, _ch, PADDING, _origin)
                            game.start_game(_diff_r, _cards)
                            backgrounds.set_for_difficulty(_diff_r)
                            ui.reset_hp()
                            cursor_pos = (0, 0)
                            ui.start_preview(_cards)
                            if game.state == GameState.POWERUP_SELECT:
                                audio.bgm_play_menu()
                            else:
                                audio.bgm_play_game(_diff_r.label)
                            print(f"[INFO] Restarted — difficulty: {_diff_r.label} ({_diff_r.cols}×{_diff_r.rows})")
                        ui.start_transition(_restart_cb)
                    elif pause_selected == 2:      # OPTIONS
                        audio.sfx_select()
                        def _pause_to_options_cb():
                            nonlocal options_origin, options_selected
                            options_origin = "pause"
                            options_selected = 0
                            # Sync temp scratchpad with current configuration
                            options_data.update({
                                "display_mode":  cfg.display_mode,
                                "resolution":    cfg.resolution,
                                "master_volume": cfg.master_volume,
                                "music_volume":  cfg.music_volume,
                                "sfx_volume":    cfg.sfx_volume,
                                "input_method":  cfg.input_method,
                                "language_mode": cfg.language_mode,
                            })
                            game.to_options(GameState.PAUSED)
                        ui.start_transition(_pause_to_options_cb)
                    elif pause_selected == 3:      # QUIT
                        audio.sfx_cancel()
                        def _quit_cb():
                            nonlocal cursor_pos
                            game.to_menu()
                            cursor_pos = None
                            audio.bgm_play_menu()
                        ui.start_transition(_quit_cb)

                # --- Options ---
                elif game.state == GameState.OPTIONS and not ui.is_transition_active():
                    if options_selected == 7:      # APPLY & BACK
                        audio.sfx_select()
                        def _apply_and_back_cb():
                            nonlocal screen, win_w, win_h, current_cw, current_ch
                            # Apply temporary changes to persistent settings
                            cfg.display_mode  = options_data["display_mode"]
                            cfg.resolution    = options_data["resolution"]
                            cfg.master_volume = options_data["master_volume"]
                            cfg.music_volume  = options_data["music_volume"]
                            cfg.sfx_volume    = options_data["sfx_volume"]
                            cfg.input_method  = options_data["input_method"]
                            cfg.language_mode = options_data["language_mode"]
                            
                            cfg.save()
                            screen = cfg.apply_display(screen)
                            win_w, win_h = screen.get_size()
                            backgrounds.invalidate_cache()
                            cfg.apply_audio()
                            audio.apply_volumes(cfg.master_volume, cfg.music_volume, cfg.sfx_volume)

                            if game.cards:
                                current_cw, current_ch = _reposition_grid(game, current_cw, current_ch, win_w, win_h)
                            game.from_options()
                        ui.start_transition(_apply_and_back_cb)

                # --- Game Over ---
                elif game.state == GameState.GAME_OVER and not ui.is_transition_active():
                    if result_selected == 0:       # SEEK REMEMBRANCE
                        audio.sfx_select()
                        _diff_ga = game.difficulty
                        def _play_again_cb():
                            nonlocal current_cw, current_ch, cursor_pos
                            _cw, _ch, _origin = get_grid_layout(_diff_ga, win_w, win_h)
                            current_cw, current_ch = _cw, _ch
                            _cards = grid.generate_grid(_diff_ga, _cw, _ch, PADDING, _origin)
                            game.start_game(_diff_ga, _cards)
                            backgrounds.set_for_difficulty(_diff_ga)
                            cursor_pos = (0, 0)
                            ui.start_preview(_cards)
                            if game.state == GameState.POWERUP_SELECT:
                                audio.bgm_play_menu()
                            else:
                                audio.bgm_play_game(_diff_ga.label)
                            print(f"[INFO] Restarted — difficulty: {_diff_ga.label} ({_diff_ga.cols}×{_diff_ga.rows})")
                        ui.start_transition(_play_again_cb)
                    else:                          # ABANDON THE LIGHT
                        audio.sfx_select()
                        def _to_menu_cb():
                            nonlocal cursor_pos
                            game.to_menu()
                            cursor_pos = None
                            audio.bgm_play_menu()
                        ui.start_transition(_to_menu_cb)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if cfg.input_method == 1: continue
                mx, my = event.pos
                if game.state == GameState.PLAYING:
                    if not ui.is_preview_active():
                        clicked = game.handle_click(event.pos)
                        if clicked and not ui.is_flipping(clicked):
                            result = game.flip_card(clicked)
                            if result is not None:
                                audio.sfx_flip()
                                ui.start_flip(clicked)
                    
                    # Check Pause button
                    if ui.get_hovered_pause_btn(mx, my):
                        audio.bgm_pause()
                        audio.heartbeat_stop()
                        audio.sfx_popup()
                        game.to_pause()
                        pause_selected = 0
                else:
                    valid_click = False
                    if game.state == GameState.MENU and ui.get_hovered_menu_item(mx, my) is not None:
                        valid_click = True
                    elif game.state == GameState.PAUSED and ui.get_hovered_pause_item(mx, my) is not None:
                        valid_click = True
                    elif game.state == GameState.GRID_SELECT and ui.get_hovered_difficulty_item(mx, my) is not None:

                        valid_click = True
                    elif game.state == GameState.GAME_OVER and ui.get_hovered_result_item(mx, my) is not None:
                        valid_click = True
                    elif game.state == GameState.POWERUP_SELECT and ui.get_hovered_powerup_item(mx, my) is not None:
                        valid_click = True
                    elif game.state == GameState.CODEX:
                        back = ui.get_hovered_codex_back(mx, my)
                        if back == "menu":
                            audio.sfx_cancel()
                            def _to_menu_cb():
                                game.to_menu()
                            ui.start_transition(_to_menu_cb)
                        elif back == "lineage":
                            audio.sfx_cancel()
                            codex_view_mode = 0
                            codex_revealed_card = None
                        else:
                            lineage_nav = ui.get_hovered_codex_lineage_nav(mx, my)
                            if lineage_nav == "prev":
                                audio.sfx_cursor()
                                codex_suit_idx = (codex_suit_idx - 1) % 4
                                ui.reset_codex_desc_scroll()
                            elif lineage_nav == "next":
                                audio.sfx_cursor()
                                codex_suit_idx = (codex_suit_idx + 1) % 4
                                ui.reset_codex_desc_scroll()
                            else:
                                # Check scrollbar before falling through to card items
                                scroll_hit = (
                                    ui.get_hovered_codex_scroll(mx, my)
                                    if codex_view_mode == 0 and not codex_revealed_card
                                    else None
                                )
                                if scroll_hit == "up":
                                    ui.scroll_codex_desc(-1)
                                    _scroll_btn_held = "up"
                                    _scroll_btn_held_timer = _SCROLL_REPEAT_INITIAL
                                    ui.set_codex_scroll_held_btn("up")
                                elif scroll_hit == "down":
                                    ui.scroll_codex_desc(+1)
                                    _scroll_btn_held = "down"
                                    _scroll_btn_held_timer = _SCROLL_REPEAT_INITIAL
                                    ui.set_codex_scroll_held_btn("down")
                                elif scroll_hit == "thumb":
                                    _codex_scroll_dragging    = True
                                    _codex_scroll_drag_start_y    = my
                                    _codex_scroll_drag_start_step = ui.get_codex_desc_scroll()
                                    ui.set_codex_scroll_dragging(True)
                                else:
                                    codex_item = ui.get_hovered_codex_item(mx, my)
                                    if codex_item is not None:
                                        item_type, item_idx = codex_item
                                        if item_type == "card" or item_idx == codex_suit_idx:
                                            valid_click = True
                        
                    if valid_click:
                        pygame.event.post(pygame.event.Event(EVENT_SELECT))
                    elif game.state == GameState.OPTIONS:
                        idx = ui.get_hovered_options_item(mx, my)
                        if idx is not None:
                            if idx == 7:  # APPLY & BACK
                                pygame.event.post(pygame.event.Event(EVENT_SELECT))
                            elif idx in (0, 1, 5, 6): # Display, Res, Input Method, Language
                                value_x = (win_w // 2) + 40
                                if mx < value_x + 80:
                                    _options_adjust(idx, -1, options_data)
                                else:
                                    _options_adjust(idx, +1, options_data)
                            elif idx in (2, 3, 4):
                                value_x = (win_w // 2) + 40
                                slider_w = 200
                                if value_x <= mx <= value_x + slider_w:
                                    pct = (mx - value_x) / slider_w
                                    pct = round(max(0.0, min(1.0, pct)), 2)
                                    if idx == 2: 
                                        options_data["master_volume"] = pct
                                        audio.sfx_hover()
                                    elif idx == 3: 
                                        options_data["music_volume"] = pct
                                    elif idx == 4: 
                                        options_data["sfx_volume"] = pct
                                        audio.sfx_hover()
                                    
                                    # Real-time audio update
                                    audio.apply_volumes(options_data["master_volume"], options_data["music_volume"], options_data["sfx_volume"])
                                else:
                                    if mx < value_x + slider_w / 2:
                                        _options_adjust(idx, -1, options_data)
                                    else:
                                        _options_adjust(idx, +1, options_data)

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                _codex_scroll_dragging = False
                ui.set_codex_scroll_dragging(False)
                _scroll_btn_held = None
                ui.set_codex_scroll_held_btn(None)

            elif event.type == pygame.MOUSEWHEEL:
                if (cfg.input_method != 1
                        and game.state == GameState.CODEX
                        and codex_view_mode == 0
                        and not codex_revealed_card):
                    # event.y: positive = scroll up (away from user) → move content down
                    ui.scroll_codex_desc(-event.y)

        # ---- Hold-to-scroll repeat ----------------------------------------
        if (_scroll_btn_held
                and game.state == GameState.CODEX
                and codex_view_mode == 0
                and not codex_revealed_card):
            if pygame.mouse.get_pressed()[0]:
                _scroll_btn_held_timer -= dt_ms
                if _scroll_btn_held_timer <= 0:
                    _scroll_btn_held_timer += _SCROLL_REPEAT_RATE
                    ui.scroll_codex_desc(-1 if _scroll_btn_held == "up" else +1)
            else:
                _scroll_btn_held = None
                ui.set_codex_scroll_held_btn(None)

        # -------------------------------------------------- game logic tick
        mismatched = game.update(dt_ms)
        if mismatched:
            if len(mismatched) == 2 and not game._reveal_all_done:
                audio.sfx_mismatch()
                ui.trigger_mismatch_flash(mismatched[0], mismatched[1])
                ui.trigger_screen_shake()
            else:
                audio.sfx_flip()

            for c in mismatched:
                ui.start_flip(c)

        # Detect state transitions
        if game.state != _prev_state or _next_round_wait > 0:
            # NEXT_ROUND: generate a fresh board and continue playing
            # (If perfect, we wait for the popup before advancing)
            if game.state == GameState.NEXT_ROUND:
                if not game.mistakes_made and _next_round_wait <= 0:
                    _next_round_wait = 2200.0
                    ui.trigger_perfection_popup()
                
                if _next_round_wait > 0:
                    _next_round_wait -= dt_ms
                    if _next_round_wait <= 0:
                        _next_round_wait = 0.0
                        # Wait finished, proceed!
                        _diff_nr = game.difficulty
                        _cw, _ch, _origin = get_grid_layout(_diff_nr, win_w, win_h)
                        current_cw, current_ch = _cw, _ch
                        _new_cards = grid.generate_grid(_diff_nr, _cw, _ch, PADDING, _origin)
                        game.advance_round(_new_cards)
                        cursor_pos = (0, 0)
                        ui.start_preview(_new_cards)
                        ui.reset_hp()
                        audio.bgm_play_game(game.difficulty.label)
                else:
                    # Mismatch made, advance immediately
                    _diff_nr = game.difficulty
                    _cw, _ch, _origin = get_grid_layout(_diff_nr, win_w, win_h)
                    current_cw, current_ch = _cw, _ch
                    _new_cards = grid.generate_grid(_diff_nr, _cw, _ch, PADDING, _origin)
                    game.advance_round(_new_cards)
                    cursor_pos = (0, 0)
                    ui.start_preview(_new_cards)
                    ui.reset_hp()
                    audio.bgm_play_game(game.difficulty.label)
            
            elif game.state == GameState.GAME_OVER:
                audio.bgm_play_menu()
                audio.heartbeat_stop()
                ui.start_result_anim()
            elif game.state == GameState.MENU and _prev_state not in (
                    GameState.GRID_SELECT, GameState.OPTIONS):
                audio.bgm_play_menu()
                audio.heartbeat_stop()
            _prev_state = game.state

        # Hover SFX — fire once per new keyboard selection
        if game.state == GameState.MENU and menu_selected != _prev_menu_sel:
            audio.sfx_hover()
            _prev_menu_sel = menu_selected
        elif game.state == GameState.GRID_SELECT and grid_selected != _prev_grid_sel:
            audio.sfx_hover()
            _prev_grid_sel = grid_selected
        elif game.state == GameState.PAUSED and pause_selected != _prev_pause_sel:
            audio.sfx_hover()
            _prev_pause_sel = pause_selected
        elif game.state == GameState.OPTIONS and options_selected != _prev_options_sel:
            audio.sfx_hover()
            _prev_options_sel = options_selected
        elif game.state == GameState.POWERUP_SELECT and powerup_selected != _prev_powerup_sel:
            audio.sfx_hover()
            _prev_powerup_sel = powerup_selected
        elif game.state == GameState.GAME_OVER and result_selected != _prev_result_sel:
            audio.sfx_hover()
            _prev_result_sel = result_selected
        elif game.state == GameState.CODEX and (codex_selected != _prev_codex_sel or codex_suit_idx != _prev_codex_suit):
            audio.sfx_hover()
            _prev_codex_sel = codex_selected
            _prev_codex_suit = codex_suit_idx

        # -------------------------------------------------- animation ticks
        ui.update_flips()
        ui.update_mismatch_flash()
        ui.update_match_pulse()
        ui.update_screen_shake()
        ui.update_transition()
        ui.update_result_anim(dt_ms)
        ui.update_perfection_popup(dt_ms)
        ui.update_codex_transitions(dt_ms, codex_revealed_card, codex_selected, codex_view_mode, codex_suit_idx)
        if game.state == GameState.PLAYING and game.cards:
            ui.update_preview(game.cards, dt_ms)
            audio.update_heartbeat(game.hp.current_hp, cfg.music_volume, cfg.master_volume)
        frame += 1

        # (BGM managed explicitly at each state transition above)

        # -------------------------------------------------- render
        if game.state == GameState.MENU:
            ui.draw_menu(screen, menu_selected, frame)

        elif game.state == GameState.PLAYING:
            ui.draw_game_bg(screen, frame // 4)   # slow spin behind cards
            ui.draw_hud(screen, game.hp.current_hp, game.score.total, game.score.multiplier, game.grace_mismatches, GRACE_MISM_COUNT, HUD_H, frame)
            ui.draw_powerups(screen, game.shield_charges, game.lifesteal_active, game.has_extra_life)
            ui.draw_pause_button(screen, frame)
            ui.draw_danger_vignette(screen, game.hp.current_hp, frame)

            # Hover detection — find which face-down card the mouse is over
            mx, my = pygame.mouse.get_pos()
            hovered = None
            if cfg.input_method != 1 and not game.lock_input:
                for c in game.cards:
                    if c.rect.collidepoint(mx, my):
                        from card import CardState
                        if c.state == CardState.FACE_DOWN:
                            hovered = c
                        break
            ui.set_hovered(hovered)

            # Fire cursor SFX once per new card the mouse enters
            if hovered is not _prev_hovered_card:
                if hovered is not None and not ui.is_preview_active():
                    audio.sfx_cursor()
                _prev_hovered_card = hovered

            # If the mouse moved, sync cursor_pos to the card under the pointer
            if cfg.input_method != 1 and hovered is not None:
                cursor_pos = hovered.grid_pos

            ui.draw_card_grid(screen, game.cards, current_cw, current_ch, game.score.multiplier, game.score.decay_fraction, cursor_pos)


        elif game.state == GameState.PAUSED:
            # Draw the frozen game underneath
            ui.draw_game_bg(screen, frame // 4)
            ui.draw_hud(screen, game.hp.current_hp, game.score.total, game.score.multiplier, game.grace_mismatches, GRACE_MISM_COUNT, HUD_H, frame)
            ui.draw_powerups(screen, game.shield_charges, game.lifesteal_active, game.has_extra_life)
            ui.set_hovered(None)
            ui.draw_card_grid(screen, game.cards, current_cw, current_ch, game.score.multiplier, game.score.decay_fraction, cursor_pos)
            # Pause overlay on top
            ui.draw_pause_overlay(screen, pause_selected, frame)

        elif game.state == GameState.OPTIONS:
            ui.draw_options_menu(screen, options_data, options_selected, frame, options_origin)

        elif game.state == GameState.GRID_SELECT:
            ui.draw_difficulty_select(screen, grid_selected, frame)

        elif game.state == GameState.POWERUP_SELECT:
            ui.draw_powerup_select(screen, powerup_selected, frame)

        elif game.state == GameState.CODEX:
            ui.draw_codex(screen, codex_view_mode, codex_suit_idx, codex_selected, codex_revealed_card, frame)


        elif game.state == GameState.GAME_OVER:
            ui.draw_result_screen(screen, False, game.score.total, game.round, result_selected, frame)

        # Transition overlay (drawn last, on top of everything)
        ui.draw_perfection_popup(screen)
        ui.draw_transition(screen)

        # Screen shake post-process — shift entire frame then black-fill edges
        ox, oy = ui.get_screen_shake_offset()
        if ox != 0 or oy != 0:
            snap = screen.copy()
            screen.fill((0, 0, 0))
            screen.blit(snap, (ox, oy))

        pygame.display.flip()
        dt_ms = clock.tick(TARGET_FPS)

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
