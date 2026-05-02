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
from hp_bar import HPBar
from score import Score


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MISMATCH_DELAY_MS = 1000.0  # ms to show mismatched cards before flipping back
WIN_DELAY_MS      = 600.0   # ms to wait after last match before showing WIN screen




# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class GameState(Enum):
    """Top-level states the game can be in."""
    MENU        = auto()   # Main menu is visible
    GRID_SELECT = auto()   # Selecting difficulty
    PLAYING     = auto()   # Active gameplay
    GAME_OVER   = auto()   # HP reached 0
    WIN         = auto()   # All pairs matched


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
    - Track flipped cards (up to 2 per turn) and detect matches.
    - Handle mismatch delay — lock input, then flip cards back.
    - Route mouse-click events to card hit-testing during PLAYING state.
    - Expose simple transition helpers (start_game, game_over, win, to_menu).

    What this class does NOT do
    ---------------------------
    - Rendering (Jim's ui.py)
    - Grid generation / shuffle (grid.py)
    - HP / score arithmetic (hp_bar.py, score.py)
    """

    def __init__(self) -> None:
        self.state           : GameState    = GameState.MENU
        self.difficulty      : Difficulty   = Difficulty.EASY   # default
        self.cards           : list[Card]   = []                # populated by grid.py

        # --- Turn / flip tracking (Week 2) ---
        self.flipped_cards   : list[Card]   = []     # up to 2 face-up cards this turn
        self.lock_input      : bool         = False  # True while showing a mismatch
        self.mismatch_timer  : float        = 0.0    # countdown (ms) until flip-back
        self.matched_pairs   : int          = 0      # number of pairs found so far
        self._win_pending    : bool         = False  # True when last match found, waiting for anim
        self._win_delay      : float        = 0.0    # countdown (ms) before WIN transition

        # --- HP & scoring (Week 3) ---
        self.hp              : HPBar        = HPBar()
        self.score           : Score        = Score()
        self._turn_start_ticks: int         = 0      # pygame ticks when 1st card flipped

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
        self.difficulty      = difficulty
        self.cards           = cards
        self.state           = GameState.PLAYING
        self.flipped_cards.clear()
        self.lock_input      = False
        self.mismatch_timer  = 0.0
        self.matched_pairs   = 0
        self._win_pending    = False
        self._win_delay      = 0.0
        self.hp              = HPBar()
        self.score           = Score()
        self._turn_start_ticks = 0

    def game_over(self) -> None:
        """Transition to the GAME_OVER screen."""
        self.state = GameState.GAME_OVER

    def win(self) -> None:
        """Transition to the WIN screen."""
        self.state = GameState.WIN

    def to_grid_select(self) -> None:
        """Transition to the GRID_SELECT screen."""
        self.state = GameState.GRID_SELECT

    def to_menu(self) -> None:
        """Return to the main menu and clear board state."""
        self.state          = GameState.MENU
        self.cards          = []
        self.flipped_cards.clear()
        self.lock_input     = False
        self.mismatch_timer = 0.0
        self.matched_pairs  = 0
        self._win_pending   = False
        self._win_delay     = 0.0
        self.hp             = HPBar()
        self.score          = Score()
        self._turn_start_ticks = 0

    # ------------------------------------------------------------------
    # Input handling
    # ------------------------------------------------------------------

    def handle_click(self, mouse_pos: tuple[int, int]) -> Optional[Card]:
        """
        Translate a mouse-click position into a card.

        Returns the first face-down card whose rect contains *mouse_pos*.
        Returns None if the game is not in PLAYING state, input is locked
        (mismatch delay), or no eligible card occupies the position.

        Parameters
        ----------
        mouse_pos : tuple[int, int]
            Pixel coordinate (x, y) of the mouse click.

        Returns
        -------
        Card | None
        """
        if self.state != GameState.PLAYING or self.lock_input:
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
    # Card flip / match logic (Week 2)
    # ------------------------------------------------------------------

    def flip_card(self, card: Card) -> Optional[str]:
        """
        Attempt to flip a face-down card and evaluate the turn.

        Call this after handle_click() returns a card.  The method
        flips the card to FACE_UP and, once two cards are revealed,
        checks for a match or starts the mismatch timer.

        Parameters
        ----------
        card : Card
            The card to flip (must currently be FACE_DOWN).

        Returns
        -------
        str | None
            ``"flip"``     — first card of the turn was flipped.
            ``"match"``    — second card flipped and it matches the first.
            ``"mismatch"`` — second card flipped, no match; timer started.
            ``None``       — flip rejected (wrong state, locked, etc.).
        """
        if self.state != GameState.PLAYING or self.lock_input:
            return None
        if card.state != CardState.FACE_DOWN:
            return None
        if card in self.flipped_cards:
            return None

        card.flip()
        self.flipped_cards.append(card)

        if len(self.flipped_cards) < 2:
            self._turn_start_ticks = pygame.time.get_ticks()
            return "flip"

        # --- Two cards revealed: evaluate ---
        a, b = self.flipped_cards

        if a.matches(b):
            a.mark_matched()
            b.mark_matched()
            self.matched_pairs += 1

            # --- Score calculation (Week 3) ---
            elapsed_ms = pygame.time.get_ticks() - self._turn_start_ticks
            elapsed_s  = elapsed_ms / 1000.0
            earned     = self.score.add_match(elapsed_s)

            print(
                f"[MATCH] {a.rank} of {a.suit}  "
                f"({self.matched_pairs}/{self.difficulty.pairs})  "
                f"+{earned} pts ({elapsed_s:.2f}s)"
            )
            self.flipped_cards.clear()

            # --- Win condition: all pairs found ---
            if self.matched_pairs >= self.difficulty.pairs:
                print("[WIN] All pairs matched — waiting for flip animation...")
                self._win_pending = True
                self._win_delay   = WIN_DELAY_MS

            return "match"

        # Mismatch — lock input, deduct HP, start countdown
        self.hp.deduct(self.difficulty.hp_penalty)
        print(
            f"[MISMATCH] {a.rank} of {a.suit} vs {b.rank} of {b.suit}  "
            f"HP: {self.hp.current_hp}/{HPBar.MAX_HP} (\u2212{self.difficulty.hp_penalty})"
        )
        self.lock_input     = True
        self.mismatch_timer = MISMATCH_DELAY_MS
        return "mismatch"

    def update(self, dt_ms: float) -> Optional[list[Card]]:
        """
        Per-frame update.  Manages the mismatch countdown timer.

        Parameters
        ----------
        dt_ms : float
            Milliseconds elapsed since the last frame.

        Returns
        -------
        list[Card] | None
            The two cards that were just flipped back on mismatch
            expiry, so main.py can trigger UI animations.  Returns
            None on every other frame.
        """
        # --- Pending win delay (let last flip animation play) ---
        if self._win_pending:
            self._win_delay -= dt_ms
            if self._win_delay <= 0:
                self._win_pending = False
                print("[WIN] Transition to WIN screen.")
                self.win()
            return None

        if not self.lock_input:
            return None

        self.mismatch_timer -= dt_ms
        if self.mismatch_timer > 0:
            return None

        # Timer expired — flip both cards back
        mismatched = list(self.flipped_cards)
        for c in self.flipped_cards:
            c.flip_back()
        self.flipped_cards.clear()
        self.lock_input = False

        # --- Game-over check (Week 3) ---
        if self.hp.is_depleted:
            print(f"[GAME OVER] HP depleted — final score: {self.score.total}")
            self.game_over()

        return mismatched

    # ------------------------------------------------------------------
    # Debug
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"Game(state={self.state.name}, "
            f"difficulty={self.difficulty.label}, "
            f"cards={len(self.cards)})"
        )
