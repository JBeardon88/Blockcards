I'm trying to build a card engine first. the game is simple, but it should handle things honestly without tricks.

---

# Blockcards: A Card Engine

I ripped off mtg. It'll change as time goes on, but to start, it's just simplified magic. Play cards, summon creatures, cast spells, fuck around. You target for the AI rn because it's easier for me to debug that way. Fuck you.

## Features:
- **Energy system**: Gain and use energy to play cards.
- **Turn-based combat**: Includes main phases, combat phases, and end phases.
- **AI opponent**: Test your strategies against an AI.
- **Card effects**: Cards can have effects that trigger during various game phases.

---

## Installation

be a man. use the command line. Windows key, command line, get ready to hackerman.


To get started, ensure you have Python installed on your system. You can download it from [python.org](https://www.python.org/).

### Step 1: Clone the Repository

First, clone the repository to your local machine.


git clone https://github.com/JBeardon88/Blockcards.git
cd Blockcards


### Step 2: Install Dependencies

Install the required dependencies using `pip`. Make sure you have `colorama` installed for colored output in the terminal:


pip install colorama


### Step 3: Run the Game

Command prompt. 

then type,

cd path\to\Blockcards

python main.py


This will start the game, allowing you to interact with the card engine.

---

## How to Play

Once the game starts, you’ll be playing against an AI opponent. Here's what to expect:

- **Turn-based system**: Each turn is divided into phases: upkeep, main phase, combat, and end phase.
- **Commands**: You can use commands like `play`, `pass`, and more to interact with the game.
- **Energy system**: Spend energy to play cards. The game will handle energy regeneration automatically during each turn.
  
The goal is to defeat the AI opponent by reducing their life total to 0!

---

## Controls

- `1. Play a card`: Select a card from your hand to play, provided you have enough energy.
- `2. Pass turn`: End your current phase or turn.
- `3. View game log`: Check the latest game actions.
- `4. View graveyard`: Inspect cards that have been destroyed or used.
- `5. Card Info`: Get detailed information about the cards in play or in your hand.

---

Enjoy the game! If you encounter any issues or have suggestions, feel free to open an issue on the GitHub repo.

---

Let me know if you'd like to modify or expand on any part of this README!