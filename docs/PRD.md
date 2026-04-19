# Product Requirements Document (PRD)
## OBLIVIO — A Pixel Art Memory Card Game

**Version:** 1.0  
**Status:** Draft  
**Platform:** Windows (Desktop GUI)  
**Engine/Language:** Python + Pygame  
**Team Size:** 2  
**Target Completion:** 1 Month  

---

## 1. Overview

Retro Memory is a single-player, pixel art memory card matching game built in Python using Pygame. The player flips cards on a grid to find matching pairs of retro/8-bit arcade icons. Every mismatched flip costs HP, and a scoring system rewards players who match quickly. The game is intended as a GUI-only personal project and is not scoped for production release.

---

## 2. Goals

- Build a fully playable memory card game within one month.
- Use Python and Pygame as the sole technology stack.
- Deliver a polished retro/8-bit pixel art visual style.
- Keep scope tight and avoid feature creep.

---

## 3. Non-Goals

- Online multiplayer or networking of any kind.
- Mobile or web builds.
- Production deployment, app store distribution, or monetization.
- Save/load game state between sessions.

---

## 4. Player Experience Summary

The player launches the game and is greeted with a main menu. They select a grid size (difficulty), then the game begins. Cards are placed face-down on a grid. The player clicks two cards per turn to reveal them — if they match, the cards stay face-up; if they don't, the cards flip back over and the player loses a fixed amount of HP. The player's score increases based on match speed. The game ends either when all pairs are matched (win) or the player's HP hits zero (lose), both resulting in a game over screen showing the final score.

---

## 5. Core Features

### 5.1 Main Menu
- Game title displayed in pixel font.
- "Play" button leading to grid size selection.
- "Quit" button to exit.

### 5.2 Grid Size Selection
| Option | Grid | Pairs |
|--------|------|-------|
| Easy   | 4×4  | 8     |
| Medium | 6×6  | 18    |
| Hard   | 8×8  | 32    |

- Player selects difficulty before the game starts.
- Cards are shuffled and randomly placed each session.

### 5.3 Card System
- Cards use a standard 52-card pixel art playing card deck (4 suits × 13 ranks).
- At the start of each session, N cards are randomly drawn from the 52-card deck, duplicated to form pairs, shuffled, and placed on the grid — ensuring a unique layout every run.
- Each card value appears exactly twice on the grid.
- Cards have three states: **face-down**, **face-up (flipped)**, **matched (locked face-up)**.
- Only two cards can be flipped per turn. Unmatched cards flip back after a short delay (~1 second).

### 5.4 Animations
All animations are implemented using Pygame's `pygame.transform.scale()` — no additional libraries or languages required.

| Animation | Description |
|-----------|-------------|
| **Card flip** | Horizontal scale tween: card width shrinks to 0 (Phase 1), image swaps, width grows back to full (Phase 2). Applies on every flip — both face-down → face-up and face-up → face-down. |
| **Match pulse** | Matched cards briefly flash or pulse with a highlight border to confirm a successful pair. |
| **HP bar decrease** | HP bar smoothly shrinks on mismatch rather than instantly jumping to the new value. |
| **Game over / Win transition** | Short fade-to-black before the result screen appears. |

### 5.5 HP System

- Player starts with a fixed HP pool (e.g. 100 HP).
- Each mismatched flip deducts a fixed amount of HP (e.g. 10 HP).
- HP is displayed as a pixel-art style HP bar on the game screen.
- If HP reaches 0, the game ends immediately with a Game Over screen.

### 5.6 Scoring System
- Points are awarded for each successful match.
- Faster matches yield higher points (time bonus per match).
- Score is displayed live on the game screen.
- Final score is shown on the Game Over / Win screen.

### 5.7 Game Over & Win Screens
- Both screens display the player's **final score**.
- Options presented: **Play Again** (same grid size) or **Main Menu**.
- Win screen and Game Over screen have distinct visuals.

### 5.8 Audio
- **Background music:** Looping chiptune/8-bit track during gameplay.
- **Sound effects:**
  - Card flip sound.
  - Match success sound.
  - Mismatch / HP loss sound.
  - Game over jingle.
  - Win jingle.
- Music and SFX sourced from free, licensed asset libraries (e.g. OpenGameArt.org, itch.io).

---

## 6. Visual Style

- **Art style:** Pixel art, retro/8-bit aesthetic throughout.
- **Card backs:** Uniform pixel art design (e.g. retro pattern or logo).
- **Card fronts:** Pixel art standard playing cards — 4 suits (♠ ♥ ♦ ♣) × 13 ranks (A, 2–10, J, Q, K).
- **UI elements:** HP bar, score counter, and all text use pixel fonts.
- **Background:** Static pixel art background (e.g. dark arcade-style backdrop).
- **Resolution:** Fixed window size (suggested: 800×600 or 1024×768).

---

## 7. Technical Requirements

| Item | Detail |
|------|--------|
| Language | Python 3.10+ |
| Library | Pygame 2.x |
| Platform | Windows 10/11 |
| Distribution | Run via script locally (`python main.py`) |
| Assets | Sourced from free-to-use pixel art libraries |
| Audio format | `.ogg` or `.wav` for SFX, `.mp3` or `.ogg` for music |
| Image format | `.png` with transparency support |

---

## 8. Out of Scope (Explicitly)

- Leaderboard persistence (no file/database storage).
- Settings menu (volume, resolution controls).
- Localization / multiple languages.
- Two-player or AI opponent mode.

---

## 9. Milestones

| Week | Milestone |
|------|-----------|
| Week 1 | Project setup, Pygame window, static grid rendering, card click detection |
| Week 2 | Card flip logic, match detection, shuffle, card state management |
| Week 3 | HP system, scoring system, Game Over and Win screens, main menu |
| Week 4 | Card flip animation, match pulse, HP bar animation, screen transitions, pixel art assets, audio, polish and bug fixing |

---

## 10. Risks

| Risk | Mitigation |
|------|------------|
| Unfamiliarity with Pygame | Use AI tools for boilerplate and debugging; reference official Pygame docs |
| Pixel art asset creation time | Source free pre-made assets from itch.io / OpenGameArt instead of drawing custom ones |
| Scope creep | Lock feature list at Week 2; no new features after that point |
| Team coordination | Divide ownership clearly: one person on game logic, one on visuals/UI |