"""
hp_bar.py — HP tracking logic for Oblivio.

Stores and mutates the player's current HP value.
Rendering of the HP bar is handled by Jim's ui.py.

Owner: Jay (data/logic) / Jim (rendering)
"""


class HPBar:
    """Tracks the player's health points during a game session."""

    MAX_HP = 100

    def __init__(self) -> None:
        self.current_hp: int = self.MAX_HP

    def deduct(self, amount: int) -> None:
        """Subtract *amount* HP, clamping at zero."""
        self.current_hp = max(0, self.current_hp - amount)

    @property
    def is_depleted(self) -> bool:
        """Return True when HP has reached zero."""
        return self.current_hp <= 0

    @property
    def fraction(self) -> float:
        """0.0 (empty) → 1.0 (full) — used by Jim's renderer."""
        return self.current_hp / self.MAX_HP
