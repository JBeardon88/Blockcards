# card_game/game.py
from display import display_game_state, display_graveyard, display_card_info, display_cards_in_play
from board import Board  # Make sure you have a Board class defined
from turns import upkeep_phase, end_phase, opponent_turn_structure
from combat import combat_phase as execute_combat_phase  # Add this import at the top
from card import Card
import json
from colorama import Fore, Back, Style
from ai import ai_make_decisions, ai_upkeep, ai_main_phase, ai_combat_phase, ai_end_phase, ai_can_play_card
import textwrap
from combat import combat_phase as execute_combat_phase
from effects import Effect, Trigger, create_effect
from player import Player
import os

class Game:
    def __init__(self, player_name, opponent_name):
        self.card_pool = []
        self.load_card_pool()
        self.player = Player(player_name, self)
        self.opponent = Player(opponent_name, self)
        self.board = Board(self.player, self.opponent, self)  # Pass the Game instance to the Board
        self.turn_counter = 0
        self.current_player = self.player
        self.player_turn = True
        self.game_log = []
        self.game_over = False
        self.turn_phase = ""
        self.last_played_card = None
        
        self.log_action(f"Game initialized. Player energy: {self.player.energy}, Opponent energy: {self.opponent.energy}")
        
    def load_card_pool(self):
        sets_dir = os.path.join(os.path.dirname(__file__), 'sets')
        available_sets = [f for f in os.listdir(sets_dir) if f.endswith('.json')]
        
        print("Available sets:")
        for i, set_file in enumerate(available_sets, 1):
            print(f"{i}. {set_file}")
        
        player_choice = int(input("Select a set for your deck: ")) - 1
        opponent_choice = (player_choice + 1) % len(available_sets)
        
        player_set = available_sets[player_choice]
        opponent_set = available_sets[opponent_choice]
        
        print(f"Player selected set: {player_set}")
        print(f"Opponent will use set: {opponent_set}")
        
        self.card_pool = self.load_set(os.path.join(sets_dir, player_set))
        self.opponent_card_pool = self.load_set(os.path.join(sets_dir, opponent_set))
        
    def load_set(self, set_path):
        with open(set_path, 'r') as file:
            return json.load(file)
        
    def start(self):
        self.log_action(f"Starting game. Player energy: {self.player.energy}, Opponent energy: {self.opponent.energy}")
        self.board.reset(self.card_pool, self.opponent_card_pool)
        self.initial_draw()
        self.log_action(f"After setup. Player energy: {self.player.energy}, Opponent energy: {self.opponent.energy}")
        
        while not self.game_over:
            self.turn_counter += 1
            self.turn_flow(self.current_player)
            self.current_player = self.opponent if self.current_player == self.player else self.player
            self.player_turn = not self.player_turn
            
            # Add a small delay and prompt between turns
            input("Press Enter to continue to the next turn...")
            
            # Ensure the next turn starts properly
            if not self.player_turn:
                self.log_action(f"Opponent's Turn {self.turn_counter + 1} is about to start.")
        
        self.log_action("Game Over!")

    def apply_constant_effects(self, player):
        player.effect_modifiers['equipment_cost_reduction'] = 0  # Reset the reduction
        for card in player.battlezone + player.environs:
            card.apply_effects(self, player)
        print(f"DEBUG: After applying constant effects, equipment_cost_reduction = {player.effect_modifiers['equipment_cost_reduction']}")

    def turn_flow(self, current_player):
        print(f"DEBUG: Starting turn for {current_player.name}")

        # Apply constant effects at the start of each turn
        self.apply_constant_effects(current_player)

        if current_player == self.player:
            # Human player turn (keep existing logic)
            # Upkeep Phase
            self.turn_phase = "upkeep"
            upkeep_log, color = upkeep_phase(self.board, player=True)
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
            end_log_entries = end_phase(self, player=True)
            for entry in end_log_entries:
                self.log_action(entry[0], entry[1])
            self.update_display()
        else:
            # AI player turn
            print("DEBUG: Starting opponent turn structure")
            try:
                opponent_turn_structure(self)
            except Exception as e:
                error_message = f"ERROR: An exception occurred during the opponent's turn: {str(e)}"
                self.log_action(error_message, Fore.RED)
                print(error_message)
            self.update_display()

    def apply_effects(self, player):
        processed_effects = set()  # Add this line at the beginning of the function
        for card in player.battlezone + player.environs:
            if hasattr(card, 'equipment_damage') and card.equipment_damage > 0:
                target = self.select_target(card_type="creature", effect_description=f"{card.equipment_damage_source} can deal {card.equipment_damage} damage to any target creature:", player=player)
                if target:
                    target.receive_damage(card.equipment_damage)
                    self.log_action(f"{card.equipment_damage_source} dealt {card.equipment_damage} damage to {target.name} (ID: {target.id})")
            
            for effect in card.effects:
                effect_key = (card.id, effect['type'], effect.get('source_id'))
                if effect_key in processed_effects:
                    print(f"DEBUG: Skipping already processed effect: {effect}")
                    continue
                processed_effects.add(effect_key)
                if 'trigger' not in effect:
                    continue
                trigger = Trigger(effect['trigger'])
                if trigger.check(self, player):
                    effect_instance = Effect(effect['type'], effect['value'], effect['trigger'], card.id)
                    effect_instance.apply(self, player)

    def check_triggers(self, player, trigger_type, card_played=None):
        for card in player.battlezone + player.environs:
            for effect in card.effects:
                if 'trigger' not in effect:
                    #print(f"DEBUG: Effect missing 'trigger' key in card {card.name} (ID: {card.id})")
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
        while True:
            self.update_display()
            options = [
                "1. Play card", "2. Pass", "3. Game log",
                "4. Graveyard", "5. Card info"
            ]
            
            # Add equip and unequip options if there are valid targets
            if self.has_equipment_to_equip(current_player):
                options.append("6. Equip")
            if self.has_equipment_to_unequip(current_player):
                options.append("7. Unequip")
            
            print("\nMain Phase Options:")
            print(" | ".join(options))
            
            if current_player == self.player:
                choice = input("Enter your choice (1-7): ")
                if choice == "1":
                    self.play_card_from_hand()
                elif choice == "2":
                    break  # Pass and end the main phase
                elif choice == "3":
                    self.display_gamelog()  # Changed from display_game_log to display_gamelog
                elif choice == "4":
                    self.display_graveyard()
                elif choice == "5":
                    self.show_card_info()
                elif choice == "6" and "6. Equip" in options:
                    self.equip_card()
                elif choice == "7" and "7. Unequip" in options:
                    self.unequip_card()
                else:
                    print("Invalid choice. Please try again.")
            else:
                # AI logic for main phase
                break

    def has_equipment_to_equip(self, player):
        return any(card.card_type == "equipment" and not card.equipped_to for card in player.environs)

    def has_equipment_to_unequip(self, player):
        return any(card.equipment for card in player.battlezone)

    def play_card_from_hand(self):
        while True:
            print("\n0. Back to main phase")
            choice = input("Enter the index of the card to play (or 0 to go back): ").strip()

            if choice == '0':
                print("Returning to main phase.")
                return

            if not choice:
                print("Invalid input. Please enter a number.")
                continue

            try:
                card_index = int(choice) - 1
                if 0 <= card_index < len(self.player.hand):
                    card = self.player.hand[card_index]
                    if self.player.play_card(card):
                        return
                else:
                    print("Invalid card index. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number.")

    def equip_card(self):
        print("\nSelect an equipment card to equip:")
        equipment_cards = display_cards_in_play(self.player, card_type="equipment")
        if not equipment_cards:
            print("No equipment cards available to equip.")
            return

        equipment_index = int(input("Enter the index of the equipment card: ")) - 1
        if equipment_index < 0 or equipment_index >= len(equipment_cards):
            print("Invalid equipment index.")
            return

        equipment = equipment_cards[equipment_index]
        equip_cost = 1  # You can adjust this cost as needed

        if self.player.energy < equip_cost:
            print(f"Not enough energy to equip. Cost: {equip_cost}, Your energy: {self.player.energy}")
            return

        print("\nSelect a creature to equip it to:")
        creature_cards = display_cards_in_play(self.player, card_type="creature")
        if not creature_cards:
            print("No creatures available to equip to.")
            return

        creature_index = int(input("Enter the index of the target creature: ")) - 1
        if creature_index < 0 or creature_index >= len(creature_cards):
            print("Invalid creature index.")
            return

        creature = creature_cards[creature_index]

        self.player.energy -= equip_cost
        if equipment.equip(creature):
            self.log_action(f"{equipment.name} successfully equipped to {creature.name} for {equip_cost} energy.")
            self.log_action(f"{creature.name}'s attack is now {creature.attack}")
        else:
            print("Failed to equip the card.")
            self.player.energy += equip_cost

    def unequip_card(self):
        print("\nSelect a creature to unequip:")
        creature_cards = display_cards_in_play(self.player, card_type="creature", show_equipment=True)
        if not creature_cards:
            print("No creatures with equipment to unequip.")
            return

        creature_index = int(input("Enter the index of the creature: ")) - 1
        if creature_index < 0 or creature_index >= len(creature_cards):
            print("Invalid creature index.")
            return

        creature = creature_cards[creature_index]
        if not creature.equipment:
            print(f"{creature.name} has no equipment to unequip.")
            return

        equipment = creature.equipment
        creature.equipment = None
        equipment.equipped_to = None

        print(f"Successfully unequipped {equipment.name} from {creature.name}.")

        # Optionally, you can add an energy cost for unequipping
        # unequip_cost = 1
        # self.player.energy -= unequip_cost
        # print(f"Unequipping cost {unequip_cost} energy.")

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
            while True:
                self.update_display()
                options = [
                    "1. Attack", "2. Pass", "3. Game log",
                    "4. Graveyard", "5. Card info"
                ]
                print("\nCombat Phase Options:")
                print(" | ".join(options))
                
                choice = input("Enter your choice (1-5): ")
                if choice == "1":
                    self.execute_combat_phase()
                elif choice == "2":
                    break
                elif choice == "3":
                    self.display_game_log()
                elif choice == "4":
                    self.display_graveyard()
                elif choice == "5":
                    self.show_card_info()
                else:
                    print("Invalid choice. Please try again.")
        else:
            # AI combat logic
            self.execute_combat_phase()

    def execute_combat_phase(self):
        execute_combat_phase(self)

    def initial_draw(self):
        for _ in range(6):
            self.player.draw_card()
            self.opponent.draw_card()
        display_game_state(self)



    def check_on_play_equipment_triggers(self, player):
        for card in player.battlezone + player.environs:
            for effect in card.effects:
                if effect.get('trigger') == 'on_play_equipment':
                    print(f"DEBUG: Triggering on_play_equipment effect for {card.name} (ID: {card.id})")
                    effect_obj = create_effect(effect['type'], effect['value'], effect['trigger'], card.id)
                    effect_obj.apply(self, player)

    def check_board_effects(self, player, card_played):
        for card in self.board.get_all_cards():
            for effect in card.effects:
                effect_instance = Effect(effect['type'], effect.get('value'), effect.get('trigger'), card.id)
                effect_instance.apply(self, player, card_played=card_played)
                
    def summon_effects(self, card, player):
        print(f"DEBUG: Summoning effects for {card.name} (ID: {card.id})")
        card.apply_effects(self, player)
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
        print(f"DEBUG: Selecting target for {effect_description}")
        valid_targets = self.get_valid_targets(card_type)
        if not valid_targets:
            print(f"DEBUG: No valid targets found for {card_type}")
            return None

        print("Legal targets:")
        for i, target in enumerate(valid_targets, 1):
            if isinstance(target, Player):
                print(f"{i}. {target.name} (Player)")
            else:
                owner = "Your" if target in player.battlezone + player.environs else "Opponent's"
                print(f"{i}. {owner} {target.name} (ID: {target.id[:8]})")
        print(f"{len(valid_targets) + 1}. Enter custom card ID")
        print(f"{len(valid_targets) + 2}. Cancel")

        while True:
            try:
                choice = int(input(f"Enter your choice (1-{len(valid_targets) + 2}): "))
                if choice == len(valid_targets) + 2:
                    return None
                if 1 <= choice <= len(valid_targets):
                    return valid_targets[choice - 1]
                if choice == len(valid_targets) + 1:
                    id_prefix = input("Enter the first four digits of the target card ID: ").strip().lower()
                    custom_targets = self.find_cards_by_id_prefix(id_prefix)
                    custom_targets = [card for card in custom_targets if self.is_legal_target(card, card_type)]
                    if custom_targets:
                        return custom_targets[0]
                    else:
                        print(f"No valid {card_type if card_type else 'card'} found with that ID.")
                print("Invalid choice. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number.")

    def get_valid_targets(self, card_type):
        valid_targets = []
        if card_type == "creature_or_player":
            valid_targets.extend([self.player, self.opponent])
            valid_targets.extend(self.player.battlezone + self.opponent.battlezone)
        elif card_type == "creature":
            valid_targets.extend(self.player.battlezone + self.opponent.battlezone)
        elif card_type == "enchantment":
            valid_targets.extend([card for card in self.player.environs + self.opponent.environs if card.card_type == "enchantment"])
        elif card_type == "equipment":
            valid_targets.extend([card for card in self.player.environs + self.opponent.environs if card.card_type == "equipment"])
        # Add other card type checks here if needed
        return valid_targets

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
        print("\nSelect card source:")
        print("1. Player's hand")
        print("2. Player's cards in play")
        print("3. Opponent's cards in play")
        print("4. Back to main menu")
        
        choice = input("Enter your choice (1-4): ")
        if choice == '1':
            self.display_hand(self.player)
            cards_to_show = self.select_cards_from_hand(self.player)
            if cards_to_show:
                display_card_info(cards_to_show)
        elif choice == '2':
            display_cards_in_play(self.player)
            cards_to_show = self.select_cards(self.player)
            if cards_to_show:
                display_card_info(cards_to_show)
        elif choice == '3':
            display_cards_in_play(self.opponent)
            cards_to_show = self.select_cards(self.opponent)
            if cards_to_show:
                display_card_info(cards_to_show)
        elif choice == '4':
            return
        else:
            print("Invalid choice. Please try again.")

    def select_cards_from_hand(self, player):
        if not player.hand:
            print(f"No cards in {player.name}'s hand.")
            return None
        
        while True:
            choice = input(f"Enter the number of the card you want to see (1-{len(player.hand)}) or 'all' to see all cards, or 'back' to return: ")
            if choice.lower() == 'back':
                return None
            elif choice.lower() == 'all':
                return player.hand
            try:
                index = int(choice) - 1
                if 0 <= index < len(player.hand):
                    return [player.hand[index]]
                else:
                    print("Invalid card number. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number, 'all', or 'back'.")

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



