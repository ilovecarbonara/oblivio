"""
score.py — Score tracking logic for Oblivio.

Stores the player's running score and calculates speed bonuses.
Rendering of the live score is handled by Jim's ui.py.

Owner: Jay (data/logic) / Jim (rendering)
"""

SPEED_BONUS = {
    "under_1s": 50,
    "1s_to_2s": 25,
    "2s_to_4s": 10,
    "over_4s":  0,
}


class Score:
    """Tracks the player's cumulative score during a game session."""

    BASE_MATCH_POINTS = 100

    def __init__(self) -> None:
        self.total: int = 0

    def add_match(self, elapsed_seconds: float) -> int:
        """Award points for a successful match and return the amount earned."""
        bonus  = self._speed_bonus(elapsed_seconds)
        earned = self.BASE_MATCH_POINTS + bonus
        self.total += earned
        return earned

    @staticmethod
    def _speed_bonus(t: float) -> int:
        """Return the speed bonus based on how fast the player matched."""
        if t < 1.0:  return SPEED_BONUS["under_1s"]
        if t < 2.0:  return SPEED_BONUS["1s_to_2s"]
        if t < 4.0:  return SPEED_BONUS["2s_to_4s"]
        return SPEED_BONUS["over_4s"]
