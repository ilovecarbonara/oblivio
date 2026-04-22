"""
main.py — Entry point for Oblivio.

Initialises Pygame, creates the window, and runs the main game loop.
Click events are routed through Game.handle_click(); rendering is kept
minimal here until Jim's ui.py is ready.

Owner: Jay (game logic)
"""

import sys

import pygame

from card import Card, CardState
from game import Game, GameState, Difficulty
import grid


# ---------------------------------------------------------------------------
# Window / display constants
# ---------------------------------------------------------------------------

WINDOW_TITLE  = "Oblivio"
WINDOW_W      = 1024
WINDOW_H      = 768
TARGET_FPS    = 60

# ---------------------------------------------------------------------------
# Placeholder palette — used until Jim's asset/rendering layer is ready
# ---------------------------------------------------------------------------

COLOR_BG           = (15,  12,  30)   # near-black purple — arcade vibe
COLOR_CARD_DOWN    = (35,  60, 110)   # deep blue — face-down card
COLOR_CARD_UP      = (210, 195, 155)  # warm parchment — face-up card
COLOR_CARD_MATCHED = (80,  180,  90)  # green — matched card
COLOR_CARD_BORDER  = (200, 200, 220)  # light border
COLOR_TEXT         = (230, 230, 255)  # near-white text
COLOR_DIM_TEXT     = (120, 120, 150)  # subdued text

# ---------------------------------------------------------------------------
# Layout constants — shared by grid.generate_grid() and the HUD renderer
# ---------------------------------------------------------------------------

CARD_W   = 90
CARD_H   = 120
PADDING  = 12
HUD_H    = 60   # height reserved at top for HP bar / score (Jim's HUD area)


# ---------------------------------------------------------------------------
# Placeholder rendering helpers
# (Will be replaced by calls to Jim's ui.py once it is ready)
# ---------------------------------------------------------------------------

def _draw_placeholder_card(surface: pygame.Surface, card: Card, font_sm: pygame.font.Font) -> None:
    """Draw a single card as a coloured rectangle with rank/suit label."""
    if card.state == CardState.FACE_DOWN:
        fill = COLOR_CARD_DOWN
        label = "?"
    elif card.state == CardState.FACE_UP:
        fill = COLOR_CARD_UP
        label = f"{card.rank}\n{card.suit[0]}"
    else:  # MATCHED
        fill = COLOR_CARD_MATCHED
        label = f"{card.rank}\n{card.suit[0]}"

    pygame.draw.rect(surface, fill, card.rect, border_radius=6)
    pygame.draw.rect(surface, COLOR_CARD_BORDER, card.rect, width=2, border_radius=6)

    if card.state != CardState.FACE_DOWN:
        lines = label.split("\n")
        total_h = sum(font_sm.size(l)[1] for l in lines) + (len(lines) - 1) * 2
        y = card.rect.centery - total_h // 2
        for line in lines:
            txt_surf = font_sm.render(line, True, (30, 30, 30))
            txt_rect = txt_surf.get_rect(centerx=card.rect.centerx, top=y)
            surface.blit(txt_surf, txt_rect)
            y += txt_surf.get_height() + 2
    else:
        # Draw a simple diamond pattern on the card back
        cx, cy = card.rect.center
        pts = [(cx, cy - 20), (cx + 14, cy), (cx, cy + 20), (cx - 14, cy)]
        pygame.draw.polygon(surface, (55, 90, 160), pts)
        pygame.draw.polygon(surface, COLOR_CARD_BORDER, pts, width=1)


def _draw_placeholder_hud(surface: pygame.Surface, font: pygame.font.Font) -> None:
    """Draw a minimal top bar until Jim's HUD renderer is ready."""
    pygame.draw.rect(surface, (25, 22, 45), (0, 0, WINDOW_W, HUD_H))
    pygame.draw.line(surface, (60, 60, 90), (0, HUD_H), (WINDOW_W, HUD_H), 1)

    hp_txt  = font.render("HP: [██████████] 100", True, (100, 220, 100))
    sc_txt  = font.render("Score: 0", True, COLOR_TEXT)
    surface.blit(hp_txt, (16, HUD_H // 2 - hp_txt.get_height() // 2))
    surface.blit(sc_txt, (WINDOW_W - sc_txt.get_width() - 16,
                           HUD_H // 2 - sc_txt.get_height() // 2))


def _draw_menu(surface: pygame.Surface, font_lg: pygame.font.Font,
               font_sm: pygame.font.Font) -> None:
    """Minimal placeholder main menu."""
    surface.fill(COLOR_BG)

    title = font_lg.render("OBLIVIO", True, (180, 140, 255))
    surface.blit(title, title.get_rect(centerx=WINDOW_W // 2, centery=200))

    sub = font_sm.render("A pixel memory card game", True, COLOR_DIM_TEXT)
    surface.blit(sub, sub.get_rect(centerx=WINDOW_W // 2, centery=260))

    hint = font_sm.render("Press  SPACE  to start  (Easy 4×4)", True, COLOR_TEXT)
    surface.blit(hint, hint.get_rect(centerx=WINDOW_W // 2, centery=360))

    quit_hint = font_sm.render("Press  ESC  to quit", True, COLOR_DIM_TEXT)
    surface.blit(quit_hint, quit_hint.get_rect(centerx=WINDOW_W // 2, centery=410))


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    # ------------------------------------------------------------------ init
    pygame.init()
    pygame.display.set_caption(WINDOW_TITLE)
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    clock  = pygame.time.Clock()

    # Fonts — fall back to the system default until Press Start 2P is set up
    # by Jim.  pygame.font.SysFont works on all platforms without extra files.
    try:
        font_lg = pygame.font.SysFont("couriernew", 52, bold=True)
        font_sm = pygame.font.SysFont("couriernew", 18)
    except Exception:
        font_lg = pygame.font.Font(None, 52)
        font_sm = pygame.font.Font(None, 18)

    # ----------------------------------------------------------- game manager
    game = Game()   # starts in MENU state

    # ---------------------------------------------------------------- loop
    running = True
    while running:

        # ------------------------------------------------- event processing
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if game.state == GameState.PLAYING:
                        game.to_menu()
                    else:
                        running = False

                elif event.key == pygame.K_SPACE:
                    if game.state == GameState.MENU:
                        # TODO: replace with a proper difficulty selection
                        # screen once Jim's ui.py grid-select screen is ready.
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
                # ---- card click detection --------------------------------
                # game.handle_click() does the hit-test and prints debug info
                # (Week 1 end-of-week requirement: clicking a card prints its
                # position to the console).
                clicked_card = game.handle_click(event.pos)

                if clicked_card is not None:
                    # For Week 1 we just flip the card so there is visible
                    # feedback.  Week 2 will add match logic on top of this.
                    clicked_card.flip()

        # ------------------------------------------------------- rendering
        if game.state == GameState.MENU:
            _draw_menu(screen, font_lg, font_sm)

        elif game.state == GameState.PLAYING:
            screen.fill(COLOR_BG)
            _draw_placeholder_hud(screen, font_sm)

            for card in game.cards:
                _draw_placeholder_card(screen, card, font_sm)

            # ESC hint
            esc_hint = font_sm.render("ESC — back to menu", True, COLOR_DIM_TEXT)
            screen.blit(esc_hint, (8, WINDOW_H - esc_hint.get_height() - 6))

        elif game.state in (GameState.GAME_OVER, GameState.WIN):
            # Placeholder — Week 3 Jim screens will replace this
            screen.fill(COLOR_BG)
            label = "GAME OVER" if game.state == GameState.GAME_OVER else "YOU WIN!"
            txt = font_lg.render(label, True, COLOR_TEXT)
            screen.blit(txt, txt.get_rect(centerx=WINDOW_W // 2, centery=WINDOW_H // 2))
            hint = font_sm.render("Press ESC to return to menu", True, COLOR_DIM_TEXT)
            screen.blit(hint, hint.get_rect(centerx=WINDOW_W // 2,
                                            centery=WINDOW_H // 2 + 80))

        # --------------------------------------------------- flip & tick
        pygame.display.flip()
        clock.tick(TARGET_FPS)

    # ----------------------------------------------------------------- quit
    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
