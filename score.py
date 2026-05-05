"""
score.py — Score tracking logic for Oblivio.

Stores the player's running score and calculates speed bonuses.
Also tracks the current match streak and applies a streak multiplier
to reward consecutive matches without a mismatch.
Rendering of the live score is handled by Jim's ui.py.

Owner: Jay (data/logic) / Jim (rendering)
"""

SPEED_BONUS = {
    "under_1s": 50,
    "1s_to_2s": 25,
    "2s_to_4s": 10,
    "over_4s":  0,
}


# Multiplier steps indexed by streak length (capped at the last entry).
# streak 0 → 1.0×, streak 1 → 1.5×, streak 2 → 2.0×, streak 3 → 2.5×, streak 4+ → 3.0×
STREAK_MULTIPLIERS: list[float] = [1.0, 1.5, 2.0, 2.5, 3.0]


class Score:
    """Tracks the player's cumulative score during a game session."""

    BASE_MATCH_POINTS = 100

    def __init__(self) -> None:
        self.total  : int   = 0
        self.streak : int   = 0   # consecutive matches without a mismatch

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def multiplier(self) -> float:
        """Current streak multiplier (read-only, used by the HUD renderer)."""
        idx = min(self.streak, len(STREAK_MULTIPLIERS) - 1)
        return STREAK_MULTIPLIERS[idx]

    def add_match(self, elapsed_seconds: float) -> int:
        """
        Award points for a successful match, apply the streak multiplier,
        increment the streak counter, and return the total amount earned.

        Parameters
        ----------
        elapsed_seconds : float
            Seconds elapsed from first-card flip to second-card flip.

        Returns
        -------
        int
            Points awarded this match (base + speed bonus, scaled by multiplier).
        """
        bonus  = self._speed_bonus(elapsed_seconds)
        earned = round((self.BASE_MATCH_POINTS + bonus) * self.multiplier)
        self.total  += earned
        self.streak += 1
        return earned

    def reset_streak(self) -> None:
        """Reset the streak counter to 0 after a mismatch."""
        self.streak = 0

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _speed_bonus(t: float) -> int:
        """Return the speed bonus based on how fast the player matched."""
        if t < 1.0:  return SPEED_BONUS["under_1s"]
        if t < 2.0:  return SPEED_BONUS["1s_to_2s"]
        if t < 4.0:  return SPEED_BONUS["2s_to_4s"]
        return SPEED_BONUS["over_4s"]
