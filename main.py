"""
main.py — Entry point for Oblivio.

Initialises Pygame, creates the window, and runs the main game loop.
Rendering is delegated to Jim's ui.py (low-res pixel canvas system).

Owner: Jay (game logic) / Jim (ui.py wiring)
"""

import sys
import pygame

from card import Card, CardState
from game import Game, GameState, Difficulty
import grid
import ui


# ---------------------------------------------------------------------------
# Window / display constants
# ---------------------------------------------------------------------------
WINDOW_TITLE = "Oblivio"
WINDOW_W     = 1024
WINDOW_H     = 768
TARGET_FPS   = 60

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

def get_grid_layout(diff: Difficulty) -> tuple[int, int, tuple[int, int]]:
    """Return (card_w, card_h, origin_xy) dynamically scaled to fit the screen."""
    max_w = WINDOW_W - 80
    max_h = WINDOW_H - HUD_H - 40
    cw_w = (max_w - (diff.cols - 1) * PADDING) / diff.cols
    cw_h = (max_h - (diff.rows - 1) * PADDING) / (diff.rows * 4 / 3)
    
    cw = max(20, int(min(cw_w, cw_h, CARD_W)))
    ch = int(cw * 4 / 3)
    
    grid_w = diff.cols * cw + (diff.cols - 1) * PADDING
    grid_h = diff.rows * ch + (diff.rows - 1) * PADDING
    origin = (
        (WINDOW_W - grid_w) // 2,
        HUD_H + (WINDOW_H - HUD_H - grid_h) // 2,
    )
    return cw, ch, origin

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    pygame.init()
    pygame.display.set_caption(WINDOW_TITLE)
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    clock  = pygame.time.Clock()

    # Load all UI assets
    ui.load_fonts()
    ui.load_card_sprites()
    ui.load_health_sprites()

    game            = Game()   # starts in MENU state
    menu_selected   = 0        # 0=PLAY  1=QUIT
    grid_selected   = 0        # 0=Easy  1=Medium  2=Hard
    result_selected = 0        # 0=Play Again  1=Main Menu
    frame           = 0
    
    current_cw      = CARD_W
    current_ch      = CARD_H

    running = True
    dt_ms   = 0.0          # milliseconds since last frame
    while running:

        # -------------------------------------------------- events
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:
                    if game.state == GameState.PLAYING:
                        game.to_menu()
                        ui.reset_hp()
                    else:
                        running = False

                elif event.key in (pygame.K_UP, pygame.K_w):
                    if game.state == GameState.MENU:
                        menu_selected = (menu_selected - 1) % len(ui.MENU_ITEMS)
                    elif game.state == GameState.GRID_SELECT:
                        grid_selected = (grid_selected - 1) % 3
                    elif game.state in (GameState.GAME_OVER, GameState.WIN):
                        result_selected = (result_selected - 1) % 2

                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    if game.state == GameState.MENU:
                        menu_selected = (menu_selected + 1) % len(ui.MENU_ITEMS)
                    elif game.state == GameState.GRID_SELECT:
                        grid_selected = (grid_selected + 1) % 3
                    elif game.state in (GameState.GAME_OVER, GameState.WIN):
                        result_selected = (result_selected + 1) % 2

                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if game.state == GameState.MENU:
                        if menu_selected == 1:   # QUIT
                            running = False
                        else:                    # PLAY
                            game.to_grid_select()
                            grid_selected = 0

                    elif game.state == GameState.GRID_SELECT:
                        diff = list(Difficulty)[grid_selected]
                        current_cw, current_ch, origin = get_grid_layout(diff)
                        cards = grid.generate_grid(diff, current_cw, current_ch, PADDING, origin)
                        game.start_game(diff, cards)
                        print(f"[INFO] Game started — difficulty: {diff.label} ({diff.cols}×{diff.rows})")

                    elif game.state in (GameState.GAME_OVER, GameState.WIN):
                        if result_selected == 0: # PLAY AGAIN
                            diff = game.difficulty
                            current_cw, current_ch, origin = get_grid_layout(diff)
                            cards = grid.generate_grid(diff, current_cw, current_ch, PADDING, origin)
                            game.start_game(diff, cards)
                            print(f"[INFO] Restarted — difficulty: {diff.label} ({diff.cols}×{diff.rows})")
                        else:                    # MAIN MENU
                            game.to_menu()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if game.state == GameState.PLAYING:
                    clicked = game.handle_click(event.pos)
                    if clicked and not ui.is_flipping(clicked):
                        result = game.flip_card(clicked)
                        if result is not None:
                            ui.start_flip(clicked)

        # -------------------------------------------------- game logic tick
        mismatched = game.update(dt_ms)
        if mismatched and len(mismatched) == 2:
            ui.trigger_mismatch_flash(mismatched[0], mismatched[1])
            for c in mismatched:
                ui.start_flip(c)

        # -------------------------------------------------- animation ticks
        ui.update_flips()
        ui.update_mismatch_flash()
        ui.update_match_pulse()
        frame += 1

        # -------------------------------------------------- render
        if game.state == GameState.MENU:
            ui.draw_menu(screen, menu_selected, frame)

        elif game.state == GameState.PLAYING:
            ui.draw_game_bg(screen, frame // 4)   # slow spin behind cards
            ui.draw_hud(screen, game.hp.current_hp, game.score.total, HUD_H, frame)
            ui.draw_card_grid(screen, game.cards, current_cw, current_ch)
            ui.draw_esc_hint(screen)

        elif game.state == GameState.GRID_SELECT:
            # Week 3 Jim screen replaces this placeholder
            screen.fill((10, 6, 24))
            try:
                from pygame.font import Font as _F
                import os
                _fp = os.path.join("assets", "PressStart2P.ttf")
                big  = _F(_fp, 20) if os.path.exists(_fp) else pygame.font.SysFont("couriernew", 28, bold=True)
                sml  = _F(_fp, 10) if os.path.exists(_fp) else pygame.font.SysFont("couriernew", 14)
            except Exception:
                big  = pygame.font.SysFont("couriernew", 28, bold=True)
                sml  = pygame.font.SysFont("couriernew", 14)

            ts = big.render("SELECT DIFFICULTY", False, (255, 255, 255))
            screen.blit(ts, ts.get_rect(centerx=WINDOW_W // 2, centery=WINDOW_H // 2 - 60))

            diffs = ["Easy (4x4)", "Medium (6x6)", "Hard (8x8)"]
            for i, d in enumerate(diffs):
                color = (243, 2, 97) if i == grid_selected else (90, 70, 100)
                text = f"> {d} <" if i == grid_selected else d
                ds = sml.render(text, False, color)
                screen.blit(ds, ds.get_rect(centerx=WINDOW_W // 2, centery=WINDOW_H // 2 + i * 30))

        elif game.state in (GameState.GAME_OVER, GameState.WIN):
            # Week 3 Jim screens replace this placeholder
            screen.fill((10, 6, 24))
            try:
                from pygame.font import Font as _F
                import os
                _fp = os.path.join("assets", "PressStart2P.ttf")
                big  = _F(_fp, 20) if os.path.exists(_fp) else pygame.font.SysFont("couriernew", 28, bold=True)
                sml  = _F(_fp, 10) if os.path.exists(_fp) else pygame.font.SysFont("couriernew", 14)
            except Exception:
                big  = pygame.font.SysFont("couriernew", 28, bold=True)
                sml  = pygame.font.SysFont("couriernew", 14)

            label = "GAME OVER" if game.state == GameState.GAME_OVER else "YOU WIN!"
            color = (200, 40, 40) if game.state == GameState.GAME_OVER else (232, 24, 90)
            ts    = big.render(label, False, color)
            screen.blit(ts, ts.get_rect(centerx=WINDOW_W // 2, centery=WINDOW_H // 2 - 40))
            sc = sml.render(f"SCORE: {game.score.total}", False, (200, 200, 200))
            screen.blit(sc, sc.get_rect(centerx=WINDOW_W // 2, centery=WINDOW_H // 2))

            opts = ["PLAY AGAIN", "MAIN MENU"]
            for i, o in enumerate(opts):
                color = (243, 2, 97) if i == result_selected else (90, 70, 100)
                text = f"> {o} <" if i == result_selected else o
                os_surf = sml.render(text, False, color)
                screen.blit(os_surf, os_surf.get_rect(centerx=WINDOW_W // 2, centery=WINDOW_H // 2 + 60 + i * 30))

        pygame.display.flip()
        dt_ms = clock.tick(TARGET_FPS)

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
