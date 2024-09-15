from display import display_game_state, display_graveyard, display_card_info, display_cards_in_play
from colorama import Fore, Back, Style
from utils import check_and_destroy



def combat_phase(game):
    game.log_action(f"{game.current_player.name}'s Combat Phase")
    available_attackers = [card for card in game.current_player.battlezone if not card.tapped and not card.summoning_sickness]
    
    if not available_attackers:
        game.log_action("No available attackers.")
        return

    while True:
        print("\nCombat Phase Options:")
        print("1. Declare attackers")
        print("2. Pass")
        print("3. View game log")
        print("4. View graveyard")
        print("5. View card info")
        
        choice = input("Enter your choice (1-5): ")
        
        if choice == '1':
            display_cards_in_play(game.current_player, card_type="creature")
            attackers = declare_attackers(game, game.current_player)
            if attackers:
                defending_player = game.player if game.current_player == game.opponent else game.opponent
                if game.current_player == game.player:
                    blockers = declare_blockers(game, defending_player, attackers)
                else:
                    blockers = ai_declare_blockers(game, defending_player, attackers)
                resolve_combat_phase(game, attackers, blockers)
            break
        elif choice == '2':
            game.log_action("Player passed combat phase.")
            break
        elif choice == '3':
            display_game_log(game)
        elif choice == '4':
            display_graveyard(game)
        elif choice == '5':
            display_card_info(game)
        else:
            print("Invalid choice. Please try again.")

    game.log_action("Combat phase ended.")

def declare_attackers(game, attacking_player):
    available_attackers = [creature for creature in attacking_player.battlezone if creature.can_attack()]
    if not available_attackers:
        print("No available attackers.")
        return []

    print("Available attackers:")
    for i, creature in enumerate(available_attackers, 1):
        print(f"{i}. {creature.name} (ATK: {creature.attack}, DEF: {creature.defense})")

    while True:
        attacker_input = input("Enter the indices of attacking creatures (comma-separated) or 'pass': ").strip().lower()
        if attacker_input == 'pass':
            return []
        try:
            attacker_indices = [int(i) - 1 for i in attacker_input.split(',')]
            attackers = [available_attackers[i] for i in attacker_indices if 0 <= i < len(available_attackers)]
            for attacker in attackers:
                attacker.tap()
                game.log_action(f"{attacker.name} is tapped and attacking.")
            return attackers
        except ValueError:
            print("Invalid input. Please enter comma-separated numbers or 'pass'.")

def declare_blockers(game, defending_player, attackers):
    available_blockers = [creature for creature in defending_player.battlezone if not creature.tapped]
    if not available_blockers:
        return [None] * len(attackers)

    print("Attacking creatures:")
    for i, creature in enumerate(attackers, 1):
        print(f"{i}. {creature.name} (ATK: {creature.attack}, DEF: {creature.defense})")

    print("\nAvailable blockers:")
    for i, creature in enumerate(available_blockers, 1):
        print(f"{i}. {creature.name} (ATK: {creature.attack}, DEF: {creature.defense})")

    blockers = [None] * len(attackers)
    while True:
        blocker_input = input("Enter the indices of blocking creatures (comma-separated, use 'x' for no blocker) or 'pass': ").strip().lower()
        if blocker_input == 'pass':
            return blockers
        try:
            blocker_indices = blocker_input.split(',')
            for i, index in enumerate(blocker_indices):
                if index == 'x':
                    blockers[i] = None
                else:
                    blocker_index = int(index) - 1
                    if 0 <= blocker_index < len(available_blockers):
                        blockers[i] = available_blockers[blocker_index]
                    else:
                        print(f"Invalid blocker index: {index}. Ignoring this blocker.")
            
            for i, (attacker, blocker) in enumerate(zip(attackers, blockers)):
                if blocker:
                    game.log_action(f"{blocker.name} blocks {attacker.name}")
                else:
                    game.log_action(f"{attacker.name} is unblocked")
            
            return blockers
        except ValueError:
            print("Invalid input. Please enter comma-separated numbers, 'x', or 'pass'.")

    return blockers

def ai_declare_blockers(game, defending_player, attackers):
    available_blockers = [creature for creature in defending_player.battlezone if not creature.tapped]
    blockers = [None] * len(attackers)
    
    for i, attacker in enumerate(attackers):
        potential_blockers = [b for b in available_blockers if b.defense >= attacker.attack]
        if potential_blockers:
            blocker = max(potential_blockers, key=lambda x: x.attack)
            blockers[i] = blocker
            available_blockers.remove(blocker)
            game.log_action(f"{blocker.name} blocks {attacker.name}")
        else:
            game.log_action(f"{attacker.name} is unblocked")
    
    return blockers


def assign_blockers(game, blockers, attackers):
    assignments = {}
    for attacker, blocker in zip(attackers, blockers):
        if blocker:
            assignments[attacker] = blocker
    return assignments

def resolve_combat_phase(game, attackers, blockers):
    for attacker, blocker in zip(attackers, blockers):
        resolve_combat(game, attacker, blocker)

def resolve_combat(game, attacker, defender):
    attacker_damage = attacker.attack
    defender_damage = defender.attack if defender else 0
    
    attacking_player = game.opponent if attacker in game.opponent.battlezone else game.player
    defending_player = game.player if attacking_player == game.opponent else game.opponent

    if defender:
        attacker.defense -= defender_damage
        defender.defense -= attacker_damage
        
        game.log_action(f"{attacker.name} deals {attacker_damage} damage to {defender.name}.")
        game.log_action(f"{defender.name} deals {defender_damage} damage to {attacker.name}.")
        
        check_and_destroy(game.board, attacker)
        check_and_destroy(game.board, defender)
    else:
        game.log_action(f"{attacker.name} attacks directly.")
        defending_player.life -= attacker_damage
        game.log_action(f"{defending_player.name} takes {attacker_damage} damage.")

    return attacker.defense <= 0, defender.defense <= 0 if defender else False


def cleanup_phase(game, attacking_player, defending_player):
    for player in [attacking_player, defending_player]:
        for creature in player.battlezone[:]:
            check_and_destroy(game.board, creature)

    if defending_player.life <= 0:
        game.game_over = True
        game.log_action(f"{defending_player.name}'s life reached 0. {attacking_player.name} wins!")

def display_game_log(game):
    print("\n=== Game Log ===")
    for log_entry in game.log[-20:]:  # Display the last 20 log entries
        print(log_entry)
    print("================\n")