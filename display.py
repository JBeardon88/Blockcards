import os
from colorama import Fore, Back, Style
import textwrap

def display_game_state(game):
    os.system('cls' if os.name == 'nt' else 'clear')
    print("====================")
    print(f"{Fore.CYAN}      TURN {game.turn_counter}      {Style.RESET_ALL}")
    print("====================")
    print(f"{Fore.RED}Opponent - Life: {game.opponent.life}, Energy: {game.opponent.energy}, Deck: {len(game.opponent.deck)} cards, Hand: {len(game.opponent.hand)} cards, Graveyard: {len(game.opponent.graveyard)} cards{Style.RESET_ALL}")
    print("__________________________")
    print("Opponent's Environs:")
    print("__________________________")
    display_environs(game.opponent.environs)
    print("__________________________")
    print("OPPONENT'S BATTLEZONE")
    print("__________________________")
    display_battlezone(game.opponent.battlezone)
    print("__________________________")
    print("PLAYER'S BATTLEZONE")
    print("__________________________")
    display_battlezone(game.player.battlezone)
    print("__________________________")
    print("Player's Environs:")
    print("__________________________")
    display_environs(game.player.environs)
    print("__________________________")
    print(f"{Fore.GREEN}Player - Life: {game.player.life}, Energy: {game.player.energy}, Deck: {len(game.player.deck)} cards, Hand: {len(game.player.hand)} cards, Graveyard: {len(game.player.graveyard)} cards{Style.RESET_ALL}")
    print("CARDS IN HAND:")
    display_hand(game.player.hand)
    print("__________________________")
    print("Game Log:")
    for entry, color in game.game_log[-5:]:
        print(color + entry + Style.RESET_ALL)
    print("__________________________")

def display_battlezone(battlezone):
    max_width = 25
    card_lines = []
    for idx, card in enumerate(battlezone, 1):
        name_display = f"~~{card.name}~~" if card.tapped else card.name
        card_info = [
            f"| {idx}: {name_display[:max_width-4]}",
            f"| Type: {card.card_type[:3]} Cost: {card.cost}",
            f"| ATK/DEF: {card.attack}/{card.defense}",
            f"| ID: {str(card.id)[:8]}",
            f"| {card.description[:max_width-2]}"
        ]
        card_lines.append(card_info)

    # Transpose the card lines to display them side by side
    for line_idx in range(5):  # Changed to 5 lines
        for card_info in card_lines:
            print(f"{card_info[line_idx]:<{max_width}}", end=" ")
        print()

def display_environs(environs):
    max_width = 25  # Increased to accommodate UUID
    card_lines = []
    for idx, card in enumerate(environs, 1):
        card_info = [
            f"| {idx}: {card.name[:max_width-4]}",
            f"| Type: {card.card_type[:3]} Cost: {card.cost}",
            f"| ATK/DEF: {card.attack}/{card.defense}",
            f"| ID: {str(card.id)[:8]}",  # Display first 8 characters of UUID
            f"| {card.description[:max_width-2]}"  # Add description line
        ]
        card_lines.append(card_info)

    # Transpose the card lines to display them side by side
    for line_idx in range(5):  # Changed to 5 lines
        for card_info in card_lines:
            print(f"{card_info[line_idx]:<{max_width}}", end=" ")
        print()

def display_hand(hand):
    print("Index  Name                 Type ERG ATK/DEF  ID        Description")
    print("-" * 80)  # Add a separator line for clarity
    for idx, card in enumerate(hand, 1):
        name = card.name[:20]
        card_type = card.card_type[:3]
        cost = str(card.cost)
        attack_defense = f"{card.attack}/{card.defense}"
        card_id = card.id[:8]  # Display first 8 characters of the ID
        description = card.description[:75] + "..." if len(card.description) > 75 else card.description

        print(f"{idx:<6} {name:<20} {card_type:<4} {cost:<3} {attack_defense:<7} {card_id:<9} {description}")
    print("-" * 80)  # Add a separator line at the end


def display_graveyard(graveyard):
    for idx, card in enumerate(graveyard, 1):
        print(f"{idx}. {card.name} (Type: {card.card_type}, ATK/DEF: {card.attack}/{card.defense}, Cost: {card.cost}, ID: {str(card.id)[:8]})")



def display_card_info(cards):
    for card in cards:
        print("\n" + "=" * 50)
        print(f"{Fore.CYAN}{Style.BRIGHT}{card.name}{Style.RESET_ALL}")
        print("=" * 50)
        print(f"{Fore.YELLOW}Type:{Style.RESET_ALL} {card.card_type.capitalize()}")
        print(f"{Fore.YELLOW}Cost:{Style.RESET_ALL} {card.cost} Energy")
        print(f"{Fore.YELLOW}Attack/Defense:{Style.RESET_ALL} {card.attack}/{card.defense}")
        print(f"{Fore.YELLOW}ID:{Style.RESET_ALL} {card.id}")
        print("-" * 50)
        print(f"{Fore.GREEN}Description:{Style.RESET_ALL}")
        description_lines = textwrap.wrap(card.description, width=48)
        for line in description_lines:
            print(f"  {line}")
        print("-" * 50)
        if hasattr(card, 'flavor_text') and card.flavor_text:
            print(f"{Fore.MAGENTA}Flavor Text:{Style.RESET_ALL}")
            flavor_lines = textwrap.wrap(card.flavor_text, width=48)
            for line in flavor_lines:
                print(f"  {Fore.LIGHTBLACK_EX}{Style.DIM}{line}{Style.RESET_ALL}")
        print("-" * 50)
        if hasattr(card, 'effects') and card.effects:
            print(f"{Fore.BLUE}Effects:{Style.RESET_ALL}")
            for effect in card.effects:
                print(f"  • {effect['type'].replace('_', ' ').capitalize()}")
                if 'value' in effect:
                    print(f"    Value: {effect['value']}")
                if 'trigger' in effect:
                    print(f"    Trigger: {effect['trigger'].replace('_', ' ').capitalize()}")
        print("=" * 50)
    input("\nPress Enter to continue...")

def display_cards_in_play(player):
    print(f"\n{player.name}'s Cards in Play:")
    all_cards = player.battlezone + player.environs
    for i, card in enumerate(all_cards, 1):
        print(f"{i}. {card.name} (Type: {card.card_type}, Cost: {card.cost}, ATK/DEF: {card.attack}/{card.defense}, ID: {card.id})")

        
def display_cards_in_play(player):
    print(f"\n{player.name}'s Cards in Play:")
    all_cards = player.battlezone + player.environs
    for i, card in enumerate(all_cards, 1):
        print(f"{i}. {card.name} (Type: {card.card_type}, Cost: {card.cost}, ATK/DEF: {card.attack}/{card.defense}, ID: {card.id})")