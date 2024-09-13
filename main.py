# card_game/main.py
from game import Game
from colorama import init, Fore, Back, Style
import os



os.system('color')  # Enable ANSI escape sequences on Windows

# Initialize colorama
init(autoreset=True)

def main():
    player_name = "Player"  # Default player name
    opponent_name = "AI Opponent"
    game = Game(player_name, opponent_name)
    game.start()

    while True:
        command = input("Enter command: ")
        if command == "exit":
            break
        game.handle_command(command)


if __name__ == "__main__":
    main()