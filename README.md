# Oblivio

A single-player pixel art memory card matching game built with Python and Pygame.

---

## Owners
- Gomez | Dejito

---

## About

Oblivio is a classic flip-and-match card game wrapped in a retro pixel art aesthetic. Find all matching pairs of playing cards before your HP runs out. Match fast to earn bonus points!

### The Bloom of Oblivion (Synopsis)
A mysterious phenomenon known as the **Bloom of Oblivion** has corrupted the realm, shattering memories and fracturing reality itself. As the corruption spreads, entire kingdoms and histories are erased, leaving only fragments trapped within enchanted cards. You must brave the decay and collect these scattered shards of forgotten lore to piece together the truth—before your own memory fades into nothingness.

---

## Gameplay & Modes

### How to Play
- Select your fate (difficulty) from the main menu.
- Click or use keyboard controls to select any two cards to flip them.
- If they match → they stay face-up.
- If they don't → they flip back and you lose HP.
- Match all pairs to win. Run out of HP to lose.
- Your final score is displayed at the end.

### Game Modes
- **Mortal (Easy):** A gentle introduction to the corrupted realm. A smaller grid offers a forgiving margin for error as you uncover the basic fragments of memory.
- **Scorched (Medium):** The corruption intensifies. The grid expands to a larger layout, presenting a more difficult challenge where memory decay becomes perilous.
- **Hellish (Hard):** The core of the Bloom's domain. A massive grid where every mistake is punishing. At the start of this mode, you choose a special **Power-Up** to aid you in this nearly impossible ordeal. Only the most resolute will persist.

---

## Getting Started

Follow these steps to set up and run the game on your local machine.

### Prerequisites
- **Python 3.10** or higher

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ilovecarbonara/oblivio.git
   cd oblivio
   ```

2. **Create and activate a virtual environment (Recommended):**
   - **Windows:**
     ```bash
     python -m venv venv
     source venv/Scripts/activate
     ```
   - **Mac/Linux:**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Install dependencies:**
   We use `pygame-ce` (Community Edition) for improved performance and features.
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the game:**
   ```bash
   python main.py
   ```

---

## Configuration

The game automatically generates a `settings.json` file in the root directory the first time you run it. You can modify this file to change your default display mode, resolution, and volume settings. 

Because `settings.json` is your personal configuration, it is ignored by Git and won't affect other developers. If you ever need to reset to the original settings, you can refer to `settings.default.json`.

---

## Team

Built as a learning project by a two-person team. Not intended for production release.
