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
# Layout constants  (in SCREEN pixels — card sprites are full-res)
# ---------------------------------------------------------------------------
CARD_W  = 76
CARD_H  = 100
PADDING = 10
HUD_H   = 48   # height of the top HUD strip

# ---------------------------------------------------------------------------
# Layout constants  (in SCREEN pixels — card sprites are full-res)
# ---------------------------------------------------------------------------
CARD_W  = 76
CARD_H  = 100
PADDING = 10
HUD_H   = 48   # height of the top HUD strip


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
    current_hp    = 100.0
    current_score = 0
    frame         = 0

    running = True
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
                        current_hp    = 100.0
                        current_score = 0
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
                            current_hp    = 100.0
                            current_score = 0
                            
                            # Call Jay's grid generation (Week 1 task)
                            new_cards = grid.generate_grid(
                                Difficulty.EASY, CARD_W, CARD_H, PADDING, WINDOW_W, HUD_H, WINDOW_H
                            )
                            # Fallback just in case grid.py is still empty
                            if new_cards is None:
                                new_cards = []
                                
                            game.start_game(Difficulty.EASY, new_cards)
                            print(f"[INFO] Game started — Easy")

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if game.state == GameState.PLAYING:
                    clicked = game.handle_click(event.pos)
                    if clicked and not ui.is_flipping(clicked):
                        ui.start_flip(clicked)
                        clicked.flip()

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
            ui.draw_hud(screen, current_hp, current_score, HUD_H, frame)
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
            screen.blit(ts, ts.get_rect(centerx=WINDOW_W // 2, centery=WINDOW_H // 2))
            hs = sml.render("ESC - MAIN MENU", False, (80, 60, 100))
            screen.blit(hs, hs.get_rect(centerx=WINDOW_W // 2, centery=WINDOW_H // 2 + 60))

        pygame.display.flip()
        clock.tick(TARGET_FPS)

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
