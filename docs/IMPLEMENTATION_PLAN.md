# OBLIVIO — Weekly Implementation Plan

> **Timeline:** 4 weeks (Apr 20 – May 17, 2026)  
> **Work cadence:** 2–4 days of work per week, one merge to `main` per week  
> **Roles:**  
> - **Jay** — Game Logic (`card.py`, `grid.py`, `hp_bar.py`, `score.py`, `game.py`, `main.py`)  
> - **Jim** — Visuals / UI (`ui.py`, assets, rendering, animations)  
>
> **Branch strategy:** Feature branches per person per week, merged to `main` at end of week.  
> **Naming convention:** `week-N/Jay/feature-name`, `week-N/Jim/feature-name`

---

## Week 1 — Foundation (Apr 20 – 26)

**Goal:** Pygame window running, cards rendered on a grid, clicks detected.

### Jay (Game Logic)

- [x] Initialize the repo with the flat file structure (`main.py`, `game.py`, `card.py`, `grid.py`, `hp_bar.py`, `score.py`, `ui.py`)
- [x] Set up `main.py` as the entry point — initialize Pygame, create the window (800×600 or 1024×768), and start the game loop
- [x] Create the `Card` class in `card.py` with basic attributes: `suit`, `rank`, `position`, `state` (face-down / face-up / matched)
- [x] Create `grid.py` with grid generation logic — take a difficulty setting, randomly draw N cards from a 52-card pool, duplicate into pairs, shuffle, and assign grid positions
- [x] Implement card click detection in the game loop — translate mouse click coordinates to a grid cell and identify which card was clicked
- [x] Set up `game.py` with a basic game state manager — track `current_state` (MENU, PLAYING, GAME_OVER, WIN) and the selected difficulty

**Branch:** `week-1/Jay/project-setup-and-grid-logic`

### Jim (Visuals / UI)

- [X] Source a pixel art playing card sprite sheet (all 52 cards + card back) from itch.io or OpenGameArt
- [ ] Source a pixel art background image (dark arcade-style)
- [ ] Set up `assets/images/` and `assets/audio/` directories
- [ ] Slice/organize card sprites into individual files or set up a sprite sheet loader
- [ ] Render a static grid of face-down cards on screen using placeholder or sourced card-back sprites
- [ ] Draw the HUD layout skeleton on the game screen (HP bar placeholder on top-left, score placeholder on top-right)

**Branch:** `week-1/Jim/assets-and-static-rendering`

### End-of-Week Merge Checklist

- [ ] Both branches merged to `main`
- [ ] Game launches, shows a window with a grid of face-down cards
- [ ] Clicking a card prints its position to the console (debug confirmation)

---

## Week 2 — Core Mechanics (Apr 27 – May 3)

**Goal:** Cards flip on click, matches are detected, unmatched pairs flip back, card states update correctly.

### Jay (Game Logic)

- [x] Implement card flip logic — clicking a face-down card sets it to face-up; only 2 cards can be flipped per turn
- [x] Implement match detection — after 2 cards are flipped, compare their suit+rank; if they match, set both to `matched` state
- [x] Implement mismatch handling — if cards don't match, flip both back to face-down after a ~1 second delay
- [x] Block input while two unmatched cards are being shown (prevent rapid clicks breaking state)
- [ ] Track the number of matched pairs; detect when all pairs are found (win condition trigger)
- [ ] Wire up the grid shuffle to run fresh on each new game session

**Branch:** `week-2/Jay/flip-and-match-logic`

### Jim (Visuals / UI)

- [ ] Render face-up cards using the correct sprite for each card's suit and rank
- [ ] Visually distinguish the three card states: face-down (card back), face-up (card front), matched (card front + glow/highlight border)
- [ ] Add a brief visual indicator for mismatches before cards flip back (e.g., red tint or shake)
- [ ] Ensure the grid is centered on screen and cards are evenly spaced for all three grid sizes (4×4, 6×6, 8×8)
- [ ] Add card hover effect (subtle highlight or cursor change when hovering over a clickable card)
- [ ] Source and implement a final custom font that better matches the dark retro-horror theme (replacing the system fallback)

**Branch:** `week-2/Jim/card-visuals-and-states`

### End-of-Week Merge Checklist

- [ ] Both branches merged to `main`
- [ ] Full flip-and-match gameplay loop works: click two cards → match or mismatch → continue
- [ ] All three grid sizes render correctly with proper card sprites

---

## Week 3 — Systems & Screens (May 4 – 10)

**Goal:** HP and scoring systems work, all menu/result screens are functional, full game flow from launch to game over.

### Jay (Game Logic)

- [ ] Implement the HP system in `hp_bar.py` — start at 100 HP, deduct on mismatch based on difficulty (Easy: −10, Medium: −15, Hard: −20)
- [ ] Trigger game-over state when HP reaches 0
- [ ] Implement the scoring system in `score.py` — award 100 base points per match, plus speed bonus (under 1s: +50, 1–2s: +25, 2–4s: +10, over 4s: +0)
- [ ] Start a per-turn timer when the first card of a pair is flipped; stop it when the second card is flipped
- [ ] Implement game state transitions in `game.py`: MENU → GRID_SELECT → PLAYING → GAME_OVER or WIN → back to MENU
- [ ] Wire "Play Again" (restart same difficulty) and "Main Menu" (go back to menu) actions from the result screens

**Branch:** `week-3/Jay/hp-scoring-and-states`

### Jim (Visuals / UI)

- [ ] Build the **Main Menu** screen in `ui.py` — game title in pixel font, "Play" and "Quit" buttons
- [ ] Build the **Grid Selection** screen — "Choose Difficulty" title, three buttons (Easy / Medium / Hard) with brief descriptions
- [ ] Build the **Game Over** screen — "GAME OVER" title, final score display, "Play Again" and "Main Menu" buttons
- [ ] Build the **Win** screen — "YOU WIN!" title, final score display, "Play Again" and "Main Menu" buttons
- [ ] Render the **HP bar** on the game screen — pixel-art segmented bar, color shifts (green → yellow → red) based on HP percentage
- [ ] Render the **live score** counter on the game screen

**Branch:** `week-3/Jim/screens-and-hud`

### End-of-Week Merge Checklist

- [ ] Both branches merged to `main`
- [ ] Complete game flow: Main Menu → Grid Select → Gameplay → Win/Game Over → Main Menu
- [ ] HP decreases on mismatch, score increases on match, both display in real time
- [ ] Game over triggers at 0 HP; win triggers when all pairs matched

---

## Week 4 — Polish & Delivery (May 11 – 17)

**Goal:** Animations, audio, final assets, bug fixes. Game is complete and presentable.

### Jay (Game Logic)

- [ ] Source audio assets: BGM (chiptune loop), SFX (card flip, match, mismatch, game over jingle, win jingle) from OpenGameArt / freesound.org
- [ ] Set up `assets/audio/` with sourced files (`.ogg` or `.wav` for SFX, `.ogg` or `.mp3` for BGM)
- [ ] Implement audio playback — load and play BGM on loop during gameplay, trigger SFX on events (flip, match, mismatch, game over, win)
- [ ] Play-test all three difficulty levels end-to-end; note and fix bugs
- [ ] Ensure input is blocked during animations (prevent click-through during flip animation)
- [ ] Final code cleanup — remove debug prints, add comments to all modules

**Branch:** `week-4/Jay/audio-and-bugfixes`

### Jim (Visuals / UI)

- [ ] Implement **card flip animation** — horizontal scale tween using `pygame.transform.scale()`: shrink width to 0, swap image, expand width back to full (~8–10 frames each phase)
- [ ] Implement **match pulse animation** — matched cards flash a highlight border 2–3 times over ~0.5 seconds
- [ ] Implement **HP bar smooth decrease** — interpolate the bar width toward the target value over ~0.3 seconds on mismatch
- [ ] Implement **screen transition** (fade-to-black) — draw a black overlay with increasing alpha (0 → 255) over ~0.5 seconds before switching to Game Over / Win screen
- [ ] Final visual polish — make sure all sprites align, fonts are consistent, colors match the style guide
- [ ] Confirm fixed window size (no resizing allowed)

**Branch:** `week-4/Jim/animations-and-polish`

### End-of-Week Merge Checklist

- [ ] Both branches merged to `main`
- [ ] All animations play smoothly (card flip, match pulse, HP bar, screen transitions)
- [ ] Audio plays correctly (BGM loops, SFX triggers)
- [ ] Game is fully playable on all three difficulties with no crashes or visual glitches
- [ ] Final commit tagged as `v1.0`

---

## Quick Reference — File Ownership

| File | Owner | Purpose |
|------|-------|---------|
| `main.py` | Jay | Entry point, Pygame init, window setup |
| `game.py` | Jay | Game loop, state management, event routing |
| `card.py` | Jay | Card class, flip logic, match checking |
| `grid.py` | Jay | Grid generation, shuffle, layout math |
| `hp_bar.py` | Jay (logic) / Jim (rendering) | HP tracking + visual HP bar |
| `score.py` | Jay (logic) / Jim (rendering) | Score tracking + visual score display |
| `ui.py` | Jim | All screens (menu, grid select, game over, win), HUD, animations |
| `assets/` | Jim | All image and audio asset files |

> **Shared files** (`hp_bar.py`, `score.py`): Jay writes the data logic (tracking values), Jim writes the rendering code. Coordinate on the interface — agree on what properties/methods the logic class exposes so the renderer can read them.

---

## Branching Workflow (per week)

```
main
 ├── week-N/Jay/feature-name
 └── week-N/Jim/feature-name
```

1. At start of week: both pull latest `main`
2. Each person creates their feature branch
3. Work and commit throughout the week
4. At end of week: merge both branches into `main` (resolve conflicts together if needed)
5. Push `main` to GitHub
