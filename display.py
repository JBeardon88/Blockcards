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
    print("Index Name                Type ERG ATK/DEF ID     Description")
    print("-" * 75)
    for i, card in enumerate(game.player.hand, 1):
        adjusted_cost = card.get_adjusted_cost(game.player)
        name = card.name.ljust(20)
        card_type = card.card_type[:3].ljust(4)
        atk_def = f"{card.attack}/{card.defense}".ljust(5)
        id_short = card.id[:8]
        description = card.description[:50] + "..." if len(card.description) > 50 else card.description
        print(f"{i:<5} {name} {card_type} {adjusted_cost:<3} {atk_def} {id_short} {description}")
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
        equipment_display = f"EQP: {Fore.BLUE}{card.equipment.id[:4]}{Style.RESET_ALL}" if card.equipment else "EQP: None"
        card_info = [
            f"| {idx}: {name_display[:max_width-4]}",
            f"| Type: {card.card_type[:3]} Cost: {card.cost}",
            f"| A/D: {card.attack}/{card.defense} {equipment_display}",
            f"| ID: {str(card.id)[:8]}",
            f"| {card.description[:max_width-4]}"  # Truncate description if too long
        ]
        card_lines.append(card_info)

    # Transpose the card lines to display them side by side
    for line_idx in range(5):
        for card_info in card_lines:
            print(f"{card_info[line_idx]:<{max_width}}", end=" ")
        print()

def display_environs(environs):
    max_width = 25
    card_lines = []
    for idx, card in enumerate(environs, 1):
        if card.card_type == "equipment":
            if card.equipped_to:
                name_display = f"{Fore.BLUE}{card.name[:max_width-4]}{Style.RESET_ALL}"
                id_display = f"{Fore.BLUE}ID: {str(card.id)[:8]}{Style.RESET_ALL}"
                equipped_to = f"On: {card.equipped_to.name[:8]}"
            else:
                name_display = card.name[:max_width-4]
                id_display = f"ID: {str(card.id)[:8]}"
                equipped_to = ""
        else:
            name_display = card.name[:max_width-4]
            id_display = f"ID: {str(card.id)[:8]}"
            equipped_to = ""

        card_info = [
            f"| {idx}: {name_display}",
            f"| Type: {card.card_type[:3]} Cost: {card.cost}",
            f"| A/D: {card.attack}/{card.defense}",
            f"| {id_display}",
            f"| {equipped_to}"
        ]
        card_lines.append(card_info)

    # Transpose the card lines to display them side by side
    for line_idx in range(5):
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

def display_cards_in_play(player, card_type=None, show_equipment=False):
    cards = player.battlezone + player.environs
    if card_type:
        cards = [card for card in cards if card.card_type == card_type]
    
    if not cards:
        print(f"No {'cards' if not card_type else card_type + ' cards'} in play.")
        return []

    print(f"\n{player.name}'s cards in play:")
    for i, card in enumerate(cards, 1):
        color = Fore.BLUE if card.card_type == "equipment" else Fore.WHITE
        equipped_to = card.equipped_to.name if hasattr(card, 'equipped_to') and card.equipped_to else "None"
        equip_info = f"On: {equipped_to[:15]}" if card.card_type == "equipment" else ""
        
        adjusted_cost = card.get_adjusted_cost(player)
        
        print(f"{color}{i}: {card.name}{Style.RESET_ALL}")
        print(f"{color}   Type: {card.card_type} Cost: {adjusted_cost}{Style.RESET_ALL}")
        print(f"{color}   A/D: {card.attack}/{card.defense} | ID: {card.id[:8]}{Style.RESET_ALL}")
        if equip_info:
            print(f"{color}   {equip_info}{Style.RESET_ALL}")
        print(f"{color}   {card.description[:50]}{'...' if len(card.description) > 50 else ''}{Style.RESET_ALL}")
        print()  # Add a blank line between cards

    return cards