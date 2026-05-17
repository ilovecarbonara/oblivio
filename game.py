"""
game.py — Game state manager for Oblivio.

Tracks the high-level game state (MENU, PLAYING, GAME_OVER),
the selected difficulty, and routes click events to the right handler.
There is no win condition — the game is endless.  When all pairs on a
board are matched the board refreshes and the score carries forward.

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

MISMATCH_DELAY_MS    = 1000.0  # ms to show mismatched cards before flipping back
NEXT_ROUND_DELAY_MS  = 1200.0  # ms to wait after last match before starting the next round
GRACE_MISM_COUNT     = 8    # mismatches allowed in Hellish mode before HP loss starts
GAME_OVER_DELAY_MS   = 2500.0  # ms to wait after last mismatch flip back before showing GAME OVER screen




# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class GameState(Enum):
    """Top-level states the game can be in."""
    MENU           = auto()   # Main menu is visible
    GRID_SELECT    = auto()   # Selecting difficulty
    PLAYING        = auto()   # Active gameplay
    PAUSED         = auto()   # Game frozen — pause overlay visible
    OPTIONS        = auto()   # Options menu visible
    POWERUP_SELECT = auto()   # Choosing a buff (Hard Mode only)
    GAME_OVER      = auto()   # HP reached 0  (only end state — no WIN)
    NEXT_ROUND     = auto()   # Brief interstitial before the next board loads
    CODEX          = auto()   # Viewing the card library


class Difficulty(Enum):
    """
    Maps a human-readable difficulty name to its grid dimensions
    and HP penalty per mismatch.

    Grid sizes from GDD §3:
        Easy   → 4×4  (8 pairs,  -15 HP per mismatch)
        Medium → 6×6  (18 pairs, -10 HP per mismatch)
        Hard   → 8×8  (32 pairs, −5 HP per mismatch)
    """
    EASY   = ("Easy",   4, 4,  8, 15)
    MEDIUM = ("Medium", 6, 6, 18, 10)
    HARD   = ("Hard", 8, 8, 32, 10)

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
        self.round           : int          = 1                 # current round number

        # --- Turn / flip tracking (Week 2) ---
        self.flipped_cards      : list[Card]   = []     # up to 2 face-up cards this turn
        self.lock_input         : bool         = False  # True while showing a mismatch
        self.mismatch_timer     : float        = 0.0    # countdown (ms) until flip-back
        self.matched_pairs      : int          = 0      # number of pairs found so far
        self._next_round_pending: bool         = False  # True when last pair matched, waiting for anim
        self._next_round_delay  : float        = 0.0    # countdown (ms) before next round starts
        self._game_over_pending : bool         = False  # True when HP is 0, waiting for flip back anim
        self._game_over_delay   : float        = 0.0    # countdown (ms) before GAME_OVER transition

        # --- HP & scoring (Week 3) ---
        self.hp              : HPBar        = HPBar()
        self.score           : Score        = Score()
        self._turn_start_ticks: int         = 0      # pygame ticks when 1st card flipped

        # --- Power-Ups (Hard Mode) ---
        self.shield_charges  : int          = 0
        self.lifesteal_active: bool         = False
        self.has_extra_life  : bool         = False

        # --- New Reward System ---
        self.successive_matches: int        = 0      # streak for regen rewards
        self.grace_mismatches  : int          = 0      # number of free mismatches remaining
        self.last_round_was_perfect: bool     = False  # True if the previous round had no mistakes

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
        self.difficulty         = difficulty
        self.cards              = cards
        self.round              = 1
        self.state              = GameState.POWERUP_SELECT if difficulty == Difficulty.HARD else GameState.PLAYING
        self.flipped_cards.clear()
        self.lock_input         = False
        self.mismatch_timer     = 0.0
        self.matched_pairs      = 0
        self._next_round_pending = False
        self._next_round_delay   = 0.0
        self._game_over_pending  = False
        self._game_over_delay    = 0.0
        self.hp                 = HPBar()
        self.score              = Score()
        self._turn_start_ticks  = 0

        # Reset reward tracking
        self.successive_matches = 0
        self.mistakes_made      = False
        self.last_round_was_perfect = False

        # Reset power-ups
        self.shield_charges  = 0
        self.lifesteal_active = False
        self.has_extra_life  = False

        # Reset grace period for Hellish
        self.grace_mismatches = GRACE_MISM_COUNT if difficulty == Difficulty.HARD else 0

    def game_over(self) -> None:
        """Transition to the GAME_OVER screen."""
        self.state = GameState.GAME_OVER

    def advance_round(self, cards: list[Card]) -> None:
        """
        Start the next round with a fresh board.

        Score and HP carry over; only the board and per-round counters reset.
        Power-ups are NOT stripped (they persist across rounds).

        Parameters
        ----------
        cards : list[Card]
            A fresh, fully-shuffled set of cards from grid.py.
        """
        self.round              += 1
        self.cards               = cards
        self.state               = GameState.PLAYING
        self.flipped_cards.clear()
        self.lock_input          = False
        self.mismatch_timer      = 0.0
        self.matched_pairs       = 0
        self._next_round_pending = False
        self._next_round_delay   = 0.0
        self._game_over_pending  = False
        self._game_over_delay    = 0.0
        self._turn_start_ticks   = 0

        # Regeneration for clearing the previous round
        self.hp.heal(25)

        # Perfect Round Reward
        if not self.mistakes_made:
            self.hp.add_overheal(50)
            self.last_round_was_perfect = True
            print(f"[REGEN] Perfect Round! +50 HP overheal bonus. (Current: {self.hp.current_hp})")
        else:
            self.last_round_was_perfect = False

        self.mistakes_made = False
        self.grace_mismatches = GRACE_MISM_COUNT if self.difficulty == Difficulty.HARD else 0
        print(f"[REGEN] Round {self.round-1} cleared! +25 HP (Current: {self.hp.current_hp})")
        print(f"[ROUND {self.round}] New board generated — score carries over: {self.score.total}")

    def to_grid_select(self) -> None:
        """Transition to the GRID_SELECT screen."""
        self.state = GameState.GRID_SELECT

    def to_codex(self) -> None:
        """Transition to the CODEX screen."""
        self.state = GameState.CODEX

    def to_menu(self) -> None:
        """Return to the main menu and clear board state."""
        self.state               = GameState.MENU
        self.cards               = []
        self.round               = 1
        self.flipped_cards.clear()
        self.lock_input          = False
        self.mismatch_timer      = 0.0
        self.matched_pairs       = 0
        self._next_round_pending = False
        self._next_round_delay   = 0.0
        self._game_over_pending  = False
        self._game_over_delay    = 0.0
        self.hp                  = HPBar()
        self.score               = Score()
        self._turn_start_ticks   = 0
        self.shield_charges      = 0
        self.lifesteal_active    = False
        self.has_extra_life      = False
        self.successive_matches  = 0
        self.mistakes_made       = False
        self.grace_mismatches    = 0

    def to_pause(self) -> None:
        """Freeze gameplay and show the pause overlay."""
        if self.state == GameState.PLAYING:
            self._pre_pause_state = GameState.PLAYING
            self.state = GameState.PAUSED

    def resume(self) -> None:
        """Resume gameplay from the pause overlay."""
        if self.state == GameState.PAUSED:
            self.state = GameState.PLAYING

    def to_options(self, origin_state: 'GameState') -> None:
        """Enter the options menu, remembering which state we came from."""
        self._options_origin = origin_state
        self.state = GameState.OPTIONS

    def from_options(self) -> None:
        """Return from options to wherever we came from."""
        self.state = getattr(self, '_options_origin', GameState.MENU)

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
        if self.state != GameState.PLAYING or self.lock_input or self._game_over_pending or self._next_round_pending:
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
        if self.state != GameState.PLAYING or self.lock_input or self._game_over_pending or self._next_round_pending:
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

            # --- Score calculation (Week 3 + streak multiplier) ---
            elapsed_ms = pygame.time.get_ticks() - self._turn_start_ticks
            elapsed_s  = elapsed_ms / 1000.0
            mult       = self.score.multiplier   # capture BEFORE add_match increments streak
            earned     = self.score.add_match(elapsed_s)

            print(
                f"[MATCH] {a.rank} of {a.suit}  "
                f"({self.matched_pairs}/{self.difficulty.pairs})  "
                f"+{earned} pts ({elapsed_s:.2f}s)  "
                f"{mult:.1f}x streak"
            )
            self.flipped_cards.clear()

            # --- All pairs matched → queue next round ---
            if self.matched_pairs >= self.difficulty.pairs:
                print(f"[ROUND CLEAR] All pairs matched — round {self.round} complete! Queuing next round...")
                self._next_round_pending = True
                self._next_round_delay   = NEXT_ROUND_DELAY_MS

            if self.lifesteal_active:
                self.hp.heal(5)
                print(f"[LIFESTEAL] Match found! +5 HP (Current: {self.hp.current_hp})")

            # --- Successive Match Rewards ---
            self.successive_matches += 1
            if self.successive_matches == 3:
                self.hp.add_overheal(10)
                print(f"[REGEN] 3 successive matches! +10 HP reward. (Current: {self.hp.current_hp})")
            elif self.successive_matches == 5:
                self.hp.add_overheal(15)
                print(f"[REGEN] 5 successive matches! +15 HP reward. (Current: {self.hp.current_hp})")
                self.successive_matches = 0  # reset to allow the cycle to repeat

            return "match"

        # Mismatch — lock input, deduct HP, reset streak, start countdown
        if self.grace_mismatches > 0:
            self.grace_mismatches -= 1
            print(f"[GRACE] Mismatch ignored! Grace remaining: {self.grace_mismatches}")
        elif self.shield_charges > 0:
            self.shield_charges -= 1
            print(f"[SHIELD] Mismatch blocked! Charges remaining: {self.shield_charges}")
        else:
            self.hp.deduct(self.difficulty.hp_penalty)
            print(
                f"[MISMATCH] {a.rank} of {a.suit} vs {b.rank} of {b.suit}  "
                f"HP: {self.hp.current_hp}/{HPBar.MAX_HP} (-{self.difficulty.hp_penalty})  "
                f"streak reset"
            )
        
        self.score.reset_streak()
        self.successive_matches = 0
        self.mistakes_made      = True
        self.lock_input     = True
        self.mismatch_timer = MISMATCH_DELAY_MS
        return "mismatch"

    def update(self, dt_ms: float) -> Optional[list[Card]]:
        """
        Per-frame update.  Manages the mismatch countdown timer and score decay.

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
        if self.score.tick(dt_ms):
            print("[STREAK] Multiplier timed out — streak reset")

        # --- Pending next-round delay (let last flip animation play) ---
        if self._next_round_pending:
            self._next_round_delay -= dt_ms
            if self._next_round_delay <= 0:
                # Signal main.py to generate a new board.
                # We set state to NEXT_ROUND; main.py detects the transition
                # and calls advance_round() with fresh cards.
                self._next_round_pending = False
                self.state = GameState.NEXT_ROUND
                print(f"[NEXT ROUND] Signalling main.py to load round {self.round + 1}.")
            return None

        # --- Pending game over delay ---
        if self._game_over_pending:
            self._game_over_delay -= dt_ms
            
            revealed_card = None
            # Staggered card reveal effect for missed cards
            unflipped = [c for c in self.cards if c.state == CardState.FACE_DOWN]
            if unflipped:
                if not hasattr(self, "_reveal_trickle_timer"):
                    self._reveal_trickle_timer = 0.0
                
                self._reveal_trickle_timer -= dt_ms
                if self._reveal_trickle_timer <= 0:
                    import random
                    c = random.choice(unflipped)
                    c.flip() # Reveal the missed card
                    revealed_card = c
                    # Calculate how fast to flip based on remaining time and cards
                    reveal_interval = max(30.0, (self._game_over_delay - 800.0) / max(len(unflipped), 1))
                    self._reveal_trickle_timer = reveal_interval

            if self._game_over_delay <= 0:
                self._game_over_pending = False
                print(f"[GAME OVER] HP depleted — final score: {self.score.total}")
                self.game_over()
            
            return [revealed_card] if revealed_card else None

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
            if self.has_extra_life:
                self.has_extra_life = False
                self.hp.heal(30)
                print("[REVIVE] Extra Life consumed! HP restored to 30.")
            else:
                print("[GAME OVER] HP depleted — waiting for flip back animation...")
                self._game_over_pending = True
                self._game_over_delay   = GAME_OVER_DELAY_MS

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
