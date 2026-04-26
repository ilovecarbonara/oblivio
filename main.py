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
# TEMP MOCKUP (JAY: REPLACE THIS IN WEEK 2)
# This allows Jim's visual flip/mismatch animations to be tested.
# ---------------------------------------------------------------------------
MISMATCH_TIMER = pygame.USEREVENT + 1
_face_up: list[Card] = []   # tracks up to 2 face-up cards


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
                        _face_up.clear()
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
                            _start_game_mockup(game, Difficulty.EASY)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if game.state == GameState.PLAYING:
                    # [TEMP MOCKUP] block clicks while mismatch timer runs
                    if len(_face_up) >= 2:
                        pass
                    else:
                        clicked = game.handle_click(event.pos)
                        if clicked and not ui.is_flipping(clicked):
                            ui.start_flip(clicked)
                            clicked.flip()
                            _face_up.append(clicked)
                            if len(_face_up) == 2:
                                pygame.time.set_timer(MISMATCH_TIMER, 1100, loops=1)

            elif event.type == MISMATCH_TIMER:
                # [TEMP MOCKUP] auto-flip cards back and deal damage
                for c in _face_up:
                    if c.state == CardState.FACE_UP:
                        ui.trigger_mismatch_flash(c, c)
                        ui.start_flip(c)
                        c.flip_back()
                        current_hp = max(0.0, current_hp - 10.0)
                _face_up.clear()

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


# ---------------------------------------------------------------------------
# [TEMP MOCKUP - JAY: REPLACE IN WEEK 2]
# Temporary grid generation so Jim's UI works before grid logic is finished.
# Replace usage of this function with: grid.generate_grid(...)
# ---------------------------------------------------------------------------
def _start_game_mockup(game: Game, diff: Difficulty) -> None:
    import random
    from card import Card, SUITS, RANKS

    pool  = [(s, r) for s in SUITS for r in RANKS]
    picks = random.sample(pool, diff.pairs)
    deck  = picks * 2      
    random.shuffle(deck)

    gw = diff.cols * CARD_W + (diff.cols - 1) * PADDING
    gh = diff.rows * CARD_H + (diff.rows - 1) * PADDING
    ox = (WINDOW_W - gw) // 2
    oy = HUD_H + (WINDOW_H - HUD_H - gh) // 2

    cards: list[Card] = []
    for idx, (suit, rank) in enumerate(deck):
        col = idx % diff.cols
        row = idx // diff.cols
        c   = Card(suit, rank, grid_pos=(col, row))
        c.rect = pygame.Rect(
            ox + col * (CARD_W + PADDING),
            oy + row * (CARD_H + PADDING),
            CARD_W,
            CARD_H,
        )
        cards.append(c)

    game.start_game(diff, cards)
    print(f"[INFO] Game started — {diff.label} ({diff.cols}×{diff.rows})")


if __name__ == "__main__":
    main()
