# Game Design Document (GDD)
## OBLIVIO

---

## 1. Game Summary

**Genre:** Puzzle / Memory  
**Player Count:** 1  
**Session Length:** ~3–10 minutes per game  
**Tone:** Lighthearted, nostalgic, retro arcade  

---

## 2. Core Game Loop

```
Start Screen
     ↓
Select Grid Size
     ↓
Game Board Loads (cards shuffled, face-down)
     ↓
Player clicks Card A → flips face-up
     ↓
Player clicks Card B → flips face-up
     ↓
  Match? ──Yes──→ Cards stay face-up, Score increases
     │
    No
     │
     ↓
Cards flip back, HP decreases
     ↓
HP = 0? ──Yes──→ Game Over Screen (show score)
     │
    No
     │
     ↓
All pairs matched? ──Yes──→ Win Screen (show score)
     │
    No
     │
     ↓
Continue flipping...
```

---

## 3. Grid Sizes & Difficulty

| Difficulty | Grid | Card Pairs | Starting HP | HP Lost per Mismatch |
|------------|------|------------|-------------|----------------------|
| Easy       | 4×4  | 8          | 100         | 10                   |
| Medium     | 6×6  | 18         | 100         | 15                   |
| Hard       | 8×8  | 32         | 100         | 20                   |

- Grids are always even-numbered to ensure every card has exactly one pair.
- Cards are randomly shuffled at the start of every session.

---

## 4. HP System

- Player begins each game with **100 HP**.
- A mismatched flip (two cards that don't match) deducts HP immediately after the cards flip back.
- HP is shown as a pixel-art bar in the top-left corner of the game screen.
- The bar changes color as HP decreases (e.g. green → yellow → red).
- At 0 HP, the game ends immediately — no further input is accepted.

---

## 5. Scoring System

### Base Score
- Each successful match awards **100 base points**.

### Speed Bonus
- A per-match timer starts when the first card of each turn is flipped.
- The faster the second card is flipped after the first:

| Time to Match | Bonus Points |
|---------------|--------------|
| Under 1s      | +50          |
| 1s – 2s       | +25          |
| 2s – 4s       | +10          |
| Over 4s       | +0           |

### Final Score
- Total score = sum of all match points + speed bonuses.
- Displayed on the Game Over and Win screens.

---

## 6. Card Design

### Card States
| State     | Visual |
|-----------|--------|
| Face-down | Uniform card back (pixel pattern or logo) |
| Face-up   | Pixel art playing card showing suit and rank |
| Matched   | Face-up, slightly highlighted or glowing border |

### Deck & Selection
- A full standard deck of **52 cards** is used as the source pool (4 suits × 13 ranks: A, 2–10, J, Q, K).
- At the start of each session, **N cards are randomly drawn** from the 52-card pool, duplicated into pairs, shuffled, and placed on the grid.
- This means every session has a different card layout, increasing replayability.

| Difficulty | Pairs | Cards Drawn from Deck |
|------------|-------|-----------------------|
| Easy       | 8     | 8 of 52               |
| Medium     | 18    | 18 of 52              |
| Hard       | 32    | 32 of 52              |

### Asset Sourcing
Source a pre-made **pixel art playing card sprite sheet** from itch.io or OpenGameArt. These typically include all 52 card faces and a card back in a single download, already sized consistently — no need to create individual assets.

---

## 7. Screens & UI

### Main Menu
- Game title (pixel font, centered)
- "Play" button
- "Quit" button
- Background: static pixel art arcade backdrop

### Grid Selection Screen
- Title: "Choose Difficulty"
- Three buttons: Easy / Medium / Hard
- Brief description of each (grid size + HP penalty)

### Game Screen Layout
```
┌─────────────────────────────────────┐
│  HP: [██████████] 100     Score: 0  │
├─────────────────────────────────────┤
│                                     │
│         [ Card Grid Here ]          │
│                                     │
└─────────────────────────────────────┘
```

### Game Over Screen
- "GAME OVER" title in large pixel font
- Final score displayed
- Two buttons: "Play Again" | "Main Menu"

### Win Screen
- "YOU WIN!" title
- Final score displayed
- Two buttons: "Play Again" | "Main Menu"

---

## 8. Audio Design

| Event              | Sound Type     | Notes                          |
|--------------------|----------------|--------------------------------|
| Gameplay           | BGM (loop)     | Chiptune, upbeat retro track   |
| Card flip          | SFX            | Short click or whoosh          |
| Match success      | SFX            | Bright chime or "ding"         |
| Mismatch           | SFX            | Low buzz or "thud"             |
| HP critical (<25%) | SFX (looping?) | Optional warning beep          |
| Game Over          | Jingle         | Short sad 8-bit jingle         |
| Win                | Jingle         | Short triumphant 8-bit jingle  |

All audio should be sourced from royalty-free / CC0 libraries such as OpenGameArt.org or freesound.org.

---

## 9. Visual Style Guide

- **Color palette:** Dark background (near-black), bright saturated pixel art elements. Inspired by classic arcade cabinets.
- **Font:** Pixel/bitmap font throughout (e.g. Press Start 2P, freely available on Google Fonts).
- **Card back:** Repeating pixel pattern or small game logo — consistent across all grid sizes.
- **Card fronts:** Pixel art standard playing cards — suits in classic red/black, ranks clearly readable at small sizes.
- **HP bar:** Block-style segmented bar, color shifts green → yellow → red.
- **Resolution:** Fixed at 800×600 or 1024×768. No window resizing.

---

## 10. Animation Details

All animations run inside Pygame's game loop using `pygame.transform.scale()` and surface alpha blending. No external animation libraries needed.

### Card Flip (Horizontal Scale Tween)
The core animation. Runs every time a card is flipped in either direction.

```
Phase 1 — Close:   scale card width from full → 0 over ~8–10 frames
                   (card appears to squish toward the center)
Image swap:        swap card_back surface ↔ card_front surface
Phase 2 — Open:    scale card width from 0 → full over ~8–10 frames
                   (card appears to expand back out)
```

- Implemented with `pygame.transform.scale(surface, (current_width, card_height))` each frame.
- Input is blocked during the flip animation to prevent double-clicks.

### Match Pulse
Triggered when two cards are successfully matched.
- The matched cards flash a bright highlight border 2–3 times over ~0.5 seconds.
- Implemented by drawing a colored rect behind the card surface each frame and toggling visibility.

### HP Bar Decrease
- On mismatch, the HP bar does not jump instantly — it smoothly slides to the new value over ~0.3 seconds.
- Implemented by interpolating the bar's drawn width toward the target width each frame.

### Screen Transition (Fade to Black)
- Triggered on Game Over and Win condition.
- A black surface is drawn over the screen with increasing alpha (0 → 255) over ~0.5 seconds.
- Implemented using `pygame.Surface.set_alpha()` on a full-screen black overlay.

---

## 11. Stretch Goals (Post-MVP Only)

These are explicitly out of scope for the one-month timeline but are noted for future consideration:

- Volume control in a settings menu.
- Session high score saved to a local file.
- Additional themes (e.g. fantasy, space).