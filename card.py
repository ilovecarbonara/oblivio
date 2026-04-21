"""
card.py — Card data model for Oblivio.

Defines the Card class and the CardState enum.
Rendering is handled separately by Jim's ui.py; this module
is purely data / logic.

Owner: Jay (game logic)
"""

from enum import Enum, auto
import pygame


class CardState(Enum):
    """The three possible states a card can be in at any point."""
    FACE_DOWN = auto()   # Hidden — the default state at game start
    FACE_UP   = auto()   # Revealed — player has clicked this card
    MATCHED   = auto()   # Permanently revealed — this card's pair was found


# The four suits in a standard deck.
SUITS = ("Hearts", "Diamonds", "Clubs", "Spades")

# The thirteen ranks in a standard deck.
RANKS = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")


class Card:
    """
    Represents a single playing card on the game board.

    Attributes
    ----------
    suit : str
        One of the four suits ("Hearts", "Diamonds", "Clubs", "Spades").
    rank : str
        One of the thirteen ranks ("A", "2"–"10", "J", "Q", "K").
    state : CardState
        Current visibility state of the card.
    rect : pygame.Rect
        Screen-space bounding rectangle used for rendering and click detection.
        Set externally by grid.py after layout positions are calculated.
    grid_pos : tuple[int, int]
        (col, row) index of this card within the grid — useful for debugging
        and for any grid-aware logic.
    """

    def __init__(
        self,
        suit: str,
        rank: str,
        grid_pos: tuple[int, int] = (0, 0),
    ) -> None:
        if suit not in SUITS:
            raise ValueError(f"Invalid suit '{suit}'. Must be one of {SUITS}.")
        if rank not in RANKS:
            raise ValueError(f"Invalid rank '{rank}'. Must be one of {RANKS}.")

        self.suit      : str                  = suit
        self.rank      : str                  = rank
        self.state     : CardState            = CardState.FACE_DOWN
        self.grid_pos  : tuple[int, int]      = grid_pos
        # rect is set by grid.py once pixel positions are known.
        self.rect      : pygame.Rect          = pygame.Rect(0, 0, 0, 0)

    # ------------------------------------------------------------------
    # Identity helpers
    # ------------------------------------------------------------------

    @property
    def identity(self) -> tuple[str, str]:
        """Return (suit, rank) — the unique identity used for match checking."""
        return (self.suit, self.rank)

    def matches(self, other: "Card") -> bool:
        """Return True if this card is the same suit+rank as *other*."""
        return self.identity == other.identity

    # ------------------------------------------------------------------
    # State helpers
    # ------------------------------------------------------------------

    def flip(self) -> None:
        """Flip a face-down card to face-up. No-op for any other state."""
        if self.state == CardState.FACE_DOWN:
            self.state = CardState.FACE_UP

    def flip_back(self) -> None:
        """Return a face-up card to face-down. No-op for matched cards."""
        if self.state == CardState.FACE_UP:
            self.state = CardState.FACE_DOWN

    def mark_matched(self) -> None:
        """Permanently mark this card as matched."""
        self.state = CardState.MATCHED

    # ------------------------------------------------------------------
    # Click / hit detection
    # ------------------------------------------------------------------

    def contains_point(self, point: tuple[int, int]) -> bool:
        """Return True if the pixel coordinate *point* is inside this card's rect."""
        return self.rect.collidepoint(point)

    # ------------------------------------------------------------------
    # Debug
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"Card({self.rank} of {self.suit}, "
            f"state={self.state.name}, "
            f"grid={self.grid_pos})"
        )
