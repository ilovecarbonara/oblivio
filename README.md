# Oblivio 🕹️

A single-player pixel art memory card matching game built with Python and Pygame.

---

## 👥 Owners
- Gomez | Dejito

---

## 📖 About

Oblivio is a classic flip-and-match card game wrapped in a retro pixel art aesthetic. Find all matching pairs of playing cards before your HP runs out. Match fast to earn bonus points!

---

## 🎮 Gameplay

- Select a grid size (Easy / Medium / Hard) from the main menu.
- Click any two cards to flip them.
- If they match → they stay face-up. 🎉
- If they don't → they flip back and you lose HP. 💔
- Match all pairs to win. Run out of HP to lose.
- Your final score is displayed at the end.

---

## 🚀 Getting Started

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

## ⚙️ Configuration

The game automatically generates a `settings.json` file in the root directory the first time you run it. You can modify this file to change your default display mode, resolution, and volume settings. 

Because `settings.json` is your personal configuration, it is ignored by Git and won't affect other developers. If you ever need to reset to the original settings, you can refer to `settings.default.json`.

---

## 🏗️ Team

Built as a learning project by a two-person team. Not intended for production release.
