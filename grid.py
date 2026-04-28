"""
grid.py — Grid generation logic for Oblivio.

Responsibility: Given a difficulty setting, randomly draw N cards from
the 52-card pool, duplicate them into pairs, shuffle, and assign pixel
positions to each card's rect.

Owner: Jay (game logic)
"""

import random

from card import Card, SUITS, RANKS


def generate_grid(
    difficulty,
    card_w: int,
    card_h: int,
    padding: int,
    origin: tuple[int, int],
) -> list[Card]:
    """
    Build a shuffled, position-assigned list of Card objects for the board.

    Steps
    -----
    1. Build the full 52-card pool (SUITS × RANKS).
    2. Randomly sample ``difficulty.pairs`` unique cards.
    3. Duplicate each sampled card to create pairs (2 × pairs cards total).
    4. Shuffle the combined list.
    5. Assign grid positions: for each (col, row) in the grid compute the
       pixel rect and set ``card.rect`` and ``card.grid_pos``.
    6. Return the list of Card objects.

    Parameters
    ----------
    difficulty : Difficulty
        The chosen difficulty level (carries .cols, .rows, .pairs).
    card_w : int
        Width of each card in pixels.
    card_h : int
        Height of each card in pixels.
    padding : int
        Gap between adjacent cards in pixels.
    origin : tuple[int, int]
        (x, y) pixel coordinate of the top-left corner of the grid.

    Returns
    -------
    list[Card]
        A fully initialised, shuffled list of Card objects ready for play.

    Raises
    ------
    ValueError
        If ``difficulty.pairs`` exceeds the 52-card pool size (impossible
        with the current Difficulty enum, but guarded for safety).
    """
    cols: int = difficulty.cols
    rows: int = difficulty.rows
    pairs: int = difficulty.pairs

    # ------------------------------------------------------------------
    # 1. Build the 52-card pool
    # ------------------------------------------------------------------
    pool: list[tuple[str, str]] = [
        (suit, rank) for suit in SUITS for rank in RANKS
    ]  # 52 entries

    # ------------------------------------------------------------------
    # 2. Sample N unique cards
    # ------------------------------------------------------------------
    if pairs > len(pool):
        raise ValueError(
            f"generate_grid: requested {pairs} pairs but the pool only has "
            f"{len(pool)} unique cards."
        )

    sample: list[tuple[str, str]] = random.sample(pool, pairs)

    # ------------------------------------------------------------------
    # 3 & 4. Duplicate into pairs and shuffle
    # ------------------------------------------------------------------
    combined: list[tuple[str, str]] = sample * 2
    random.shuffle(combined)

    # ------------------------------------------------------------------
    # 5. Assign grid positions and pixel rects
    # ------------------------------------------------------------------
    import pygame  # local import — pygame must already be initialised by main.py

    origin_x, origin_y = origin
    cards: list[Card] = []

    for idx, (suit, rank) in enumerate(combined):
        col: int = idx % cols
        row: int = idx // cols

        x: int = origin_x + col * (card_w + padding)
        y: int = origin_y + row * (card_h + padding)

        card = Card(suit, rank, grid_pos=(col, row))
        card.rect = pygame.Rect(x, y, card_w, card_h)
        cards.append(card)

    # ------------------------------------------------------------------
    # 6. Return
    # ------------------------------------------------------------------
    return cards
