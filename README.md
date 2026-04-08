# OBLIVIO

A single-player pixel art memory card matching game built with Python and Pygame.

---

## About

Oblivio is a classic flip-and-match card game wrapped in a retro 8-bit aesthetic. Find all matching pairs of arcade icons before your HP runs out. Match fast to earn bonus points!

---

## Gameplay

- Select a grid size (Easy / Medium / Hard) from the main menu.
- Click any two cards to flip them.
- If they match → they stay face-up. 🎉
- If they don't → they flip back and you lose HP. 💔
- Match all pairs to win. Run out of HP to lose.
- Your final score is displayed at the end.

---

## Requirements

- Python 3.10 or higher
- Pygame 2.x

Install dependencies:

```bash
pip install pygame
```

---

## How to Run

```bash
python main.py
```

---

## Project Structure

```
oblivio/
├── main.py               # Entry point
├── game.py               # Core game loop and state management
├── card.py               # Card class and flip logic
├── grid.py               # Grid generation and layout
├── hp_bar.py             # HP system
├── score.py              # Scoring logic
├── ui.py                 # Menus and screens
├── assets/
│   ├── images/           # Card fronts, card back, backgrounds, UI
│   └── audio/            # Music and sound effects
├── PRD.md                # Product Requirements Document
├── GAME_DESIGN.md        # Game design details
└── README.md             # This file
```

---

## Asset Credits

All pixel art and audio assets are sourced from free, permissively licensed libraries:
- [itch.io free assets](https://itch.io/game-assets/free)
- [OpenGameArt.org](https://opengameart.org)

---

## Team

Built as a learning project by a two-person team. Not intended for production release.