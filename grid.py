"""
grid.py — Grid generation logic for Oblivio.

Responsibility: Given a difficulty setting, randomly draw N cards from
the 52-card pool, duplicate them into pairs, shuffle, and assign pixel
positions to each card's rect.

Owner: Jay (game logic)
Status: STUB — grid generation is scheduled for Week 1 but explicitly
        excluded from this initial commit per the plan. The module
        exists so that imports in main.py and game.py don't break.
"""

# TODO (Week 1 — Jay): Implement generate_grid()
#
#   def generate_grid(difficulty: Difficulty, card_w: int, card_h: int,
#                     padding: int, origin: tuple[int, int]) -> list[Card]:
#       1. Build the full 52-card pool (SUITS × RANKS).
#       2. Randomly sample `difficulty.pairs` unique cards.
#       3. Duplicate each sampled card to create pairs.
#       4. Shuffle the combined list.
#       5. Assign grid positions: for each (col, row) in the grid,
#          compute the pixel rect and set card.rect and card.grid_pos.
#       6. Return the list of Card objects.
