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
    DECAY_DURATION_MS = 5000.0

    def __init__(self) -> None:
        self.total  : int   = 0
        self.streak : int   = 0   # consecutive matches without a mismatch
        self.decay_timer_ms : float = 0.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def multiplier(self) -> float:
        """Current streak multiplier (read-only, used by the HUD renderer)."""
        idx = min(self.streak, len(STREAK_MULTIPLIERS) - 1)
        return STREAK_MULTIPLIERS[idx]

    @property
    def decay_fraction(self) -> float:
        """0.0 to 1.0 indicating how much of the multiplier time remains."""
        if self.streak == 0:
            return 1.0
        return max(0.0, min(1.0, self.decay_timer_ms / self.DECAY_DURATION_MS))

    def add_match(self, elapsed_seconds: float) -> int:
        """
        Award points for a successful match, apply the streak multiplier,
        increment the streak counter, reset decay timer, and return points earned.
        """
        bonus  = self._speed_bonus(elapsed_seconds)
        earned = round((self.BASE_MATCH_POINTS + bonus) * self.multiplier)
        self.total  += earned
        self.streak += 1
        self.decay_timer_ms = self.DECAY_DURATION_MS
        return earned

    def reset_streak(self) -> None:
        """Reset the streak counter to 0 after a mismatch."""
        self.streak = 0
        self.decay_timer_ms = 0.0

    def tick(self, dt_ms: float) -> bool:
        """
        Tick the multiplier decay timer.
        Returns True if the timer expired this frame (meaning streak dropped).
        """
        if self.streak == 0:
            return False

        self.decay_timer_ms -= dt_ms
        if self.decay_timer_ms <= 0:
            self.reset_streak()
            return True
        return False

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
