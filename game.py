"""
game.py — Game state manager for Oblivio.

Tracks the high-level game state (MENU, PLAYING, GAME_OVER, WIN),
the selected difficulty, and routes click events to the right handler.

Owner: Jay (game logic)
"""

from enum import Enum, auto
from typing import Optional

import pygame

from card import Card, CardState


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class GameState(Enum):
    """Top-level states the game can be in."""
    MENU      = auto()   # Main menu is visible
    PLAYING   = auto()   # Active gameplay
    GAME_OVER = auto()   # HP reached 0
    WIN       = auto()   # All pairs matched


class Difficulty(Enum):
    """
    Maps a human-readable difficulty name to its grid dimensions
    and HP penalty per mismatch.

    Grid sizes from GDD §3:
        Easy   → 4×4  (8 pairs,  −10 HP per mismatch)
        Medium → 6×6  (18 pairs, −15 HP per mismatch)
        Hard   → 8×8  (32 pairs, −20 HP per mismatch)
    """
    EASY   = ("Easy",   4, 4,  8, 10)
    MEDIUM = ("Medium", 6, 6, 18, 15)
    HARD   = ("Hard",   8, 8, 32, 20)

    def __init__(
        self,
        label: str,
        cols: int,
        rows: int,
        pairs: int,
        hp_penalty: int,
    ) -> None:
        self.label      = label        # Human-readable name
        self.cols       = cols         # Grid columns
        self.rows       = rows         # Grid rows
        self.pairs      = pairs        # Number of unique card pairs on the board
        self.hp_penalty = hp_penalty   # HP deducted on each mismatch


# ---------------------------------------------------------------------------
# Game manager
# ---------------------------------------------------------------------------

class Game:
    """
    Central game state manager.

    Responsibilities
    ----------------
    - Hold the current GameState and selected Difficulty.
    - Store the active card grid (list of Card objects).
    - Route mouse-click events to card hit-testing during PLAYING state.
    - Expose simple transition helpers (start_game, game_over, win, to_menu).

    What this class does NOT do
    ---------------------------
    - Rendering (Jim's ui.py)
    - Grid generation / shuffle (grid.py — Week 1 task excluded per plan)
    - HP / score arithmetic (hp_bar.py, score.py — Week 3)
    """

    def __init__(self) -> None:
        self.state      : GameState            = GameState.MENU
        self.difficulty : Difficulty           = Difficulty.EASY   # default
        self.cards      : list[Card]           = []                # populated by grid.py

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------

    def start_game(self, difficulty: Difficulty, cards: list[Card]) -> None:
        """
        Transition from MENU (or any state) into PLAYING.

        Parameters
        ----------
        difficulty : Difficulty
            The chosen difficulty level.
        cards : list[Card]
            A fully-shuffled, position-assigned list of Card objects
            produced by grid.py.
        """
        self.difficulty = difficulty
        self.cards      = cards
        self.state      = GameState.PLAYING

    def game_over(self) -> None:
        """Transition to the GAME_OVER screen."""
        self.state = GameState.GAME_OVER

    def win(self) -> None:
        """Transition to the WIN screen."""
        self.state = GameState.WIN

    def to_menu(self) -> None:
        """Return to the main menu and clear board state."""
        self.state = GameState.MENU
        self.cards = []

    # ------------------------------------------------------------------
    # Input handling
    # ------------------------------------------------------------------

    def handle_click(self, mouse_pos: tuple[int, int]) -> Optional[Card]:
        """
        Translate a mouse-click position into a card.

        Iterates over all cards and returns the first face-down card
        whose rect contains *mouse_pos*.  Returns None if:
            - The game is not in PLAYING state.
            - No face-down card occupies the clicked position.

        Notes
        -----
        Only FACE_DOWN cards are eligible to be clicked — clicking on
        a face-up or matched card is intentionally ignored here.  The
        caller (main.py game loop) decides what to do with the returned
        card (e.g. flip it, check for a match).

        Parameters
        ----------
        mouse_pos : tuple[int, int]
            Pixel coordinate (x, y) of the mouse click.

        Returns
        -------
        Card | None
        """
        if self.state != GameState.PLAYING:
            return None

        for card in self.cards:
            if card.state == CardState.FACE_DOWN and card.contains_point(mouse_pos):
                # Debug trace — Week 1 requirement: print card position on click
                print(
                    f"[CLICK] {card}  pixel=({mouse_pos[0]}, {mouse_pos[1]})"
                )
                return card

        return None

    # ------------------------------------------------------------------
    # Debug
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"Game(state={self.state.name}, "
            f"difficulty={self.difficulty.label}, "
            f"cards={len(self.cards)})"
        )
