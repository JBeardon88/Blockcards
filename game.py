# card_game/game.py
from display import display_game_state, display_graveyard, display_card_info, display_cards_in_play
from board import Board  # Make sure you have a Board class defined
from turns import upkeep_phase, end_phase, opponent_turn_structure
from combat import combat_phase as execute_combat_phase  # Add this import at the top
from card import Card
import json
from colorama import Fore, Back, Style
from ai import ai_make_decisions, ai_upkeep, ai_main_phase, ai_combat_phase, ai_end_phase, ai_can_play_card
from player_effects import Player, Effect, Trigger
import textwrap

class Game:
    def __init__(self, player_name, opponent_name):
        self.card_pool = []
        self.load_card_pool()
        self.player = Player(player_name)
        self.opponent = Player(opponent_name)
        self.board = Board(self.player, self.opponent, self)  # Pass the Game instance to the Board
        self.turn_counter = 0
        self.player_turn = True
        self.game_log = []
        self.game_over = False
        self.turn_phase = ""
        self.last_played_card = None
        
        #self.log_action(f"Game initialized. Player energy: {self.player.energy}, Opponent energy: {self.opponent.energy}")

    def log_action(self, action, color=Fore.WHITE):
        timestamp = f"[Turn {self.turn_counter}]"
        player = "Player" if self.player_turn else "Opponent"
        log_entry = f"{timestamp} {player}: {action}"
        self.game_log.append((log_entry, color))
        print(color + log_entry + Style.RESET_ALL)  # Print the log entry immediately

    def start(self):
        self.log_action(f"Starting game. Player energy: {self.player.energy}, Opponent energy: {self.opponent.energy}")
        self.load_card_pool()
        self.board.reset(self.card_pool)
        self.initial_draw()
        self.log_action(f"After setup. Player energy: {self.player.energy}, Opponent energy: {self.opponent.energy}")
        
        while not self.game_over:
            self.turn_counter += 1
            current_player = self.player if self.player_turn else self.opponent
            self.log_action(f"{current_player.name}'s Turn {self.turn_counter} started.")
            self.turn_flow(current_player)
            self.log_action(f"{current_player.name} ended their turn.")
            
            if self.game_over:
                break
            
            self.player_turn = not self.player_turn
            
            # Add a small delay and prompt between turns
            input("Press Enter to continue to the next turn...")
        
        self.log_action("Game Over!")

    def turn_flow(self, current_player):
        # Upkeep Phase
        self.turn_phase = "upkeep"
        upkeep_log, color = upkeep_phase(self.board, player=current_player==self.player)
        self.log_action(upkeep_log, color)
        self.update_display()

        # Main Phase 1
        self.turn_phase = "main_phase_1"
        self.log_action(f"{current_player.name}'s First Main Phase")
        self.main_phase(current_player)
        self.update_display()

        # Combat Phase
        self.turn_phase = "combat"
        self.log_action(f"{current_player.name}'s Combat Phase")
        self.combat_phase(current_player)
        self.update_display()

        # Main Phase 2
        self.turn_phase = "main_phase_2"
        self.log_action(f"{current_player.name}'s Second Main Phase")
        self.main_phase(current_player)
        self.update_display()

        # End Phase
        self.turn_phase = "end"
        end_log_entries = end_phase(self, player=current_player==self.player)
        for entry in end_log_entries:
            self.log_action(entry[0], entry[1])
        self.update_display()

        if current_player == self.player:
            input("Press Enter to end your turn...")
        else:
            input("Press Enter to start your turn...")

    def apply_effects(self, player):
        for card in player.battlezone + player.environs:
            for effect in card.effects:
                if 'trigger' not in effect:
                    print(f"DEBUG: Effect missing 'trigger' key in card {card.name} (ID: {card.id})")
                    continue
                trigger = Trigger(effect['trigger'])
                if trigger.check(self, player):
                    effect_instance = Effect(effect['type'], effect['value'], effect['trigger'], card.id)
                    effect_instance.apply(self, player)

    def check_triggers(self, player, trigger_type, card_played=None):
        for card in player.battlezone + player.environs:
            for effect in card.effects:
                if 'trigger' not in effect:
                    print(f"DEBUG: Effect missing 'trigger' key in card {card.name} (ID: {card.id})")
                    continue
                if effect['trigger'] == trigger_type:
                    if trigger_type == "on_play_equipment" and card_played and card_played.card_type == "equipment":
                        effect_instance = Effect(effect['type'], effect['value'], effect['trigger'], card.id)
                        effect_instance.apply(self, player, card_played=card_played)
                        print(f"DEBUG: Triggered effect {effect['type']} from card {card.name} (ID: {card.id})")
                    elif trigger_type != "on_play_equipment":
                        effect_instance = Effect(effect['type'], effect['value'], effect['trigger'], card.id)
                        effect_instance.apply(self, player)
                        print(f"DEBUG: Triggered effect {effect['type']} from card {card.name} (ID: {card.id})")
    
    
    def main_phase(self, current_player):
        if current_player == self.player:
            # Human player logic
            while True:
                display_game_state(self)
                print("Main Phase - Enter command: 1. Play, 2. Pass, 3. Game Log, 4. Graveyard, 5. Card Info")
                command = input("Enter command number: ").strip().lower()
                if command == "2" or command == "pass":
                    break
                elif command == "1" or command == "play":
                    self.play_card(current_player)
                elif command == "3" or command == "gamelog":
                    self.display_gamelog()
                elif command == "4" or command == "graveyard":
                    self.display_graveyard()
                elif command == "5" or command == "info":
                    self.card_info_menu()
                else:
                    print("Unknown command! Use '1', '2', '3', '4', or '5'.")
        else:
            # AI logic
            ai_main_phase(self)

    def card_info_menu(self):
        while True:
            print("Card Info - Select source: 1. Hand, 2. Board, 3. Graveyard, 4. Card ID, 5. Cancel")
            choice = input("Enter command number: ").strip().lower()
            if choice == "1":
                self.display_hand(self.player)
                card_index = int(input("Enter the card index: ").strip()) - 1
                if 0 <= card_index < len(self.player.hand):
                    display_card_info([self.player.hand[card_index]])
                break
            elif choice == "2":
                display_cards_in_play(self.player)
                card_index = int(input("Enter the card index: ").strip()) - 1
                all_cards = self.player.battlezone + self.player.environs
                if 0 <= card_index < len(all_cards):
                    display_card_info([all_cards[card_index]])
                break
            elif choice == "3":
                self.display_graveyard()
                card_index = int(input("Enter the card index: ").strip()) - 1
                if 0 <= card_index < len(self.player.graveyard):
                    display_card_info([self.player.graveyard[card_index]])
                break
            elif choice == "4":
                id_prefix = input("Enter the first four digits of the card ID: ").strip().lower()
                cards = self.find_cards_by_id_prefix(id_prefix)
                display_card_info(cards)
                break
            elif choice == "5" or choice == "cancel":
                break
            else:
                print("Invalid choice. Please try again.")
                
    def combat_phase(self, current_player):
        if current_player == self.player:
            # Human player logic
            while True:
                display_game_state(self)
                print("Combat Phase - Enter command: 1. Attack, 2. Pass, 3. Game Log, 4. Graveyard, 5. Card Info by ID")
                command = input("Enter command number: ").strip().lower()
                if command == "2" or command == "pass":
                    break
                elif command == "1" or command == "attack":
                    execute_combat_phase(self)
                    break
                elif command == "3" or command == "gamelog":
                    self.display_gamelog()
                elif command == "4" or command == "graveyard":
                    self.display_graveyard()
                elif command == "5" or command == "info id":
                    id_prefix = input("Enter the first four digits of the card ID: ").strip().lower()
                    self.display_card_info(id_prefix)
                else:
                    print("Unknown command! Use '1', '2', '3', '4', or '5'.")
        else:
            # AI logic
            execute_combat_phase(self)

    def load_card_pool(self):
        with open('technobros.json') as f:
            self.card_pool = json.load(f)
            print(f"DEBUG: Loaded card pool with {len(self.card_pool)} cards")

    def initial_draw(self):
        for _ in range(6):
            self.player.draw_card()
            self.opponent.draw_card()
        display_game_state(self)

            
    def play_card(self, player, card=None):
        if player == self.player:
            # Human player logic
            while True:
                try:
                    card_input = input("Select a card to play by index (or 'cancel' to go back): ").strip().lower()
                    if card_input == 'cancel':
                        print(Fore.YELLOW + "Cancelled card play." + Style.RESET_ALL)
                        return

                    card_index = int(card_input) - 1
                    if 0 <= card_index < len(player.hand):
                        card = player.hand[card_index]
                        if self.board.play_card(card, player=True):
                            return card
                        else:
                            print(Fore.RED + "Insufficient energy to play this card." + Style.RESET_ALL)
                    else:
                        print(Fore.RED + "Invalid card index. Please try again." + Style.RESET_ALL)
                except ValueError:
                    print(Fore.RED + "Invalid input. Please enter a number or 'cancel'." + Style.RESET_ALL)
        else:
            # AI player logic
            if card and self.board.play_card(card, player=False):
                return True
            else:
                return False

    def check_board_effects(self, player, card_played):
        for card in self.board.get_all_cards():
            for effect in card.effects:
                effect_instance = Effect(effect['type'], effect.get('value'), effect.get('trigger'), card.id)
                effect_instance.apply(self, player, card_played=card_played)
                
    def summon_effects(self, card, player):
        print(f"DEBUG: Summoning effects for {card.name} (ID: {card.id})")
        for effect in card.effects:
            if effect['trigger'] == 'on_summon':
                effect_instance = Effect(effect['type'], effect.get('value'), effect['trigger'], card.id)
                effect_instance.apply(self, player)
                print(f"DEBUG: Applied summon effect {effect['type']} for {card.name} (ID: {card.id})")

    def display_game_state(self):
        print("\nCurrent Game State:")
        print(f"Player Life: {self.player.life}, Energy: {self.player.energy}")
        print(f"Opponent Life: {self.opponent.life}, Energy: {self.opponent.energy}")
        print("\nPlayer's Hand:")
        for i, card in enumerate(self.player.hand, 1):
            print(f"{i}. {card.name} (Type: {card.card_type}, Cost: {card.cost}, ATK/DEF: {card.attack}/{card.defense}, ID: {card.id[:4]})")

    def display_gamelog(self):
        print(Fore.CYAN + "\nGame Log:" + Style.RESET_ALL)
        for entry, color in self.game_log:  # Show last 10 entries
            print(color + entry + Style.RESET_ALL)
        input(Fore.MAGENTA + "\nPress Enter to return to the game." + Style.RESET_ALL)

    def display_graveyard(self):
        while True:
            print(Fore.CYAN + "\nWhose graveyard do you want to see?")
            print("1. Player's graveyard")
            print("2. Opponent's graveyard")
            print("3. Back to main phase" + Style.RESET_ALL)
            choice = input("Enter your choice (1-3): ")
            if choice == '1':
                self.display_player_graveyard(self.player)
            elif choice == '2':
                self.display_player_graveyard(self.opponent)
            elif choice == '3':
                break
            else:
                print("Invalid choice. Please try again.")

    def display_player_graveyard(self, player):
        print(f"\n{player.name}'s Graveyard:")
        for i, card in enumerate(player.graveyard, 1):
            print(f"{i}. {card.name} (Type: {card.card_type}, Cost: {card.cost}, ATK/DEF: {card.attack}/{card.defense}, ID: {card.id})")
        input("\nPress Enter to continue...")

    def display_hand(self, player):
        print(f"\n{player.name}'s Hand:")
        for i, card in enumerate(player.hand, 1):
            print(f"{i}. {card.name} (Type: {card.card_type}, Cost: {card.cost}, ATK/DEF: {card.attack}/{card.defense})")

    def log_action(self, action, color=Fore.WHITE):
        timestamp = f"[Turn {self.turn_counter}]"
        player = "Player" if self.player_turn else "Opponent"
        log_entry = f"{timestamp} {player}: {action}"
        self.game_log.append((log_entry, color))

    def update_display(self):
        display_game_state(self)
        # Print the last 5 log entries
        #print("\nGame Log (last 5 entries):")
        #for message, color in self.game_log[-5:]:
        #    print(f"{color}{message}{Style.RESET_ALL}")

    def handle_command(self, command):
        parts = command.split()
        if len(parts) == 3 and parts[0] == "info" and parts[1] == "id":
            self.display_card_info(parts[2])
        elif len(parts) == 2 and parts[0] == "info" and parts[1] == "id":
            print("Error: Please provide the first four digits of the card ID.")
        else:
            print("Unknown command")

    def find_cards_by_id_prefix(self, id_prefix):
        cards = []
        # Search in player        for card in self.player.deck + self.player.hand + self.player.battlezone + self.player.graveyard + self.player.environs:
        for card in self.player.deck + self.player.hand + self.player.battlezone + self.player.graveyard + self.player.environs:
            if card.id.startswith(id_prefix):
                cards.append(card)
        # Search in opponent's zones
        for card in self.opponent.deck + self.opponent.hand + self.opponent.battlezone + self.opponent.graveyard + self.opponent.environs:
            if card.id.startswith(id_prefix):
                cards.append(card)
        return cards

    def select_target(self, card_type=None, effect_description=None, player=None):
        if effect_description:
            print(f"\n{effect_description}")

        legal_targets = self.get_legal_targets(card_type, player)

        if not legal_targets:
            print("No legal targets found.")
            return None

        print("Legal targets:")
        for i, target in enumerate(legal_targets, 1):
            if isinstance(target, Player):
                print(f"{i}. {target.name} (Player)")
            else:
                owner = "Your" if target in player.battlezone + player.environs else "Opponent's"
                print(f"{i}. {owner} {target.name} (ID: {target.id[:8]})")
        print(f"{len(legal_targets) + 1}. Enter custom card ID")
        print(f"{len(legal_targets) + 2}. Cancel")

        while True:
            choice = input(f"Enter your choice (1-{len(legal_targets) + 2}): ").strip()
            if choice.isdigit():
                choice = int(choice)
                if 1 <= choice <= len(legal_targets):
                    return legal_targets[choice - 1]
                elif choice == len(legal_targets) + 1:
                    id_prefix = input("Enter the first four digits of the target card ID: ").strip().lower()
                    custom_targets = self.find_cards_by_id_prefix(id_prefix)
                    custom_targets = [card for card in custom_targets if self.is_legal_target(card, card_type)]
                    if custom_targets:
                        return custom_targets[0]
                    else:
                        print(f"No valid {card_type if card_type else 'card'} found with that ID.")
                elif choice == len(legal_targets) + 2:
                    return None
            print("Invalid choice. Please try again.")

    def get_legal_targets(self, card_type=None, player=None):
        legal_targets = []
        if card_type in ["creature", "enchantment", "equipment"]:
            for p in [self.player, self.opponent]:
                legal_targets.extend([card for card in p.battlezone + p.environs if self.is_legal_target(card, card_type)])
        elif card_type == "creature_or_player":
            for p in [self.player, self.opponent]:
                legal_targets.extend([card for card in p.battlezone if card.card_type == "creature"])
            legal_targets.extend([self.player, self.opponent])
        elif card_type == "player":
            legal_targets = [self.player, self.opponent]
        elif card_type is None:
            for p in [self.player, self.opponent]:
                legal_targets.extend(p.battlezone + p.environs)
            legal_targets.extend([self.player, self.opponent])
        return legal_targets

    def is_legal_target(self, card, card_type):
        if card_type == "creature":
            return card.card_type == "creature"
        elif card_type == "enchantment":
            return card.card_type == "enchantment"
        elif card_type == "equipment":
            return card.card_type == "equipment"
        return True

    from display import display_card_info, display_cards_in_play

    def show_card_info(self):
        print("\nCards in Play:")
        print("1. Player's cards")
        print("2. Opponent's cards")
        print("3. Back to main menu")
        
        choice = input("Enter your choice (1-3): ")
        if choice == '1':
            display_cards_in_play(self.player)
            cards_to_show = self.select_cards(self.player)
            if cards_to_show:
                display_card_info(cards_to_show)
        elif choice == '2':
            display_cards_in_play(self.opponent)
            cards_to_show = self.select_cards(self.opponent)
            if cards_to_show:
                display_card_info(cards_to_show)
        elif choice == '3':
            return
        else:
            print("Invalid choice. Please try again.")

    def select_cards(self, player):
        all_cards = player.battlezone + player.environs
        if not all_cards:
            print(f"No cards in play for {player.name}.")
            return None
        
        while True:
            choice = input(f"Enter the number of the card you want to see (1-{len(all_cards)}) or 'all' to see all cards, or 'back' to return: ")
            if choice.lower() == 'back':
                return None
            elif choice.lower() == 'all':
                return all_cards
            try:
                index = int(choice) - 1
                if 0 <= index < len(all_cards):
                    return [all_cards[index]]
                else:
                    print("Invalid card number. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number, 'all', or 'back'.")

    def process_command(self, command):
        if command == "1":
            self.play_card(self.player)
        elif command == "2":
            self.pass_turn()
        elif command == "3":
            self.display_game_log()
        elif command == "4":
            self.display_graveyard()
        elif command == "5":
            self.show_card_info()  # Call the new method here
        else:
            print("Invalid command. Please try again.")



