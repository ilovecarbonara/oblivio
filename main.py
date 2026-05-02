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

    game          = Game()   # starts in MENU state
    menu_selected = 0        # 0=PLAY  1=QUIT
    frame         = 0

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

                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    if game.state == GameState.MENU:
                        menu_selected = (menu_selected + 1) % len(ui.MENU_ITEMS)

                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if game.state == GameState.MENU:
                        if menu_selected == 1:   # QUIT
                            running = False
                        else:                    # PLAY
                            diff = Difficulty.EASY
                            grid_w = diff.cols * CARD_W + (diff.cols - 1) * PADDING
                            grid_h = diff.rows * CARD_H + (diff.rows - 1) * PADDING
                            origin = (
                                (WINDOW_W - grid_w) // 2,
                                HUD_H + (WINDOW_H - HUD_H - grid_h) // 2,
                            )
                            cards = grid.generate_grid(diff, CARD_W, CARD_H, PADDING, origin)
                            game.start_game(diff, cards)
                            print("[INFO] Game started — difficulty: Easy (4×4)")

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
            ui.draw_card_grid(screen, game.cards, CARD_W, CARD_H)
            ui.draw_esc_hint(screen)

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
            screen.blit(ts, ts.get_rect(centerx=WINDOW_W // 2, centery=WINDOW_H // 2 - 20))
            sc = sml.render(f"SCORE: {game.score.total}", False, (200, 200, 200))
            screen.blit(sc, sc.get_rect(centerx=WINDOW_W // 2, centery=WINDOW_H // 2 + 20))
            hs = sml.render("ESC - MAIN MENU", False, (80, 60, 100))
            screen.blit(hs, hs.get_rect(centerx=WINDOW_W // 2, centery=WINDOW_H // 2 + 60))

        pygame.display.flip()
        dt_ms = clock.tick(TARGET_FPS)

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
