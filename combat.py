from display import display_game_state
from colorama import Fore, Back, Style

def combat_phase(game):
    print("\nCombat Phase:")
    attacking_player = game.player if game.player_turn else game.opponent
    defending_player = game.opponent if game.player_turn else game.player
    board = game.board

    # 1. Declare attackers
    attackers = declare_attackers(game, attacking_player)
    if not attackers:
        game.log_action("No attackers declared.", Fore.BLUE)
        return
    game.update_display()

    # 2. Declare blockers
    if defending_player == game.opponent:
        blockers = ai_declare_blockers(game, defending_player, attackers)
    else:
        blockers = declare_blockers(game, defending_player, attackers)
    game.update_display()

    # 3. Resolve combat
    resolve_combat(game, attacking_player, defending_player, attackers, blockers)
    game.update_display()

    # 4. Clean up phase
    cleanup_phase(game, attacking_player, defending_player)
    game.update_display()

    game.log_action("Combat phase ended.", Fore.BLUE)
    if game.player_turn:
        input("Press Enter to continue...")

def declare_attackers(game, attacking_player):
    available_attackers = [creature for creature in attacking_player.battlezone if not creature.tapped]
    if not available_attackers:
        return []

    print("Available attackers:")
    for i, creature in enumerate(available_attackers):
        print(f"{i+1}. {creature.name} (ATK: {creature.attack}, DEF: {creature.defense})")

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
            return blockers
        except ValueError:
            print("Invalid input. Please enter comma-separated numbers, 'x', or 'pass'.")

    return blockers

def ai_declare_blockers(game, defending_player, attackers):
    available_blockers = [creature for creature in defending_player.battlezone if not creature.tapped]
    blockers = []
    
    print("AI is declaring blockers...")
    for attacker in attackers:
        potential_blockers = [b for b in available_blockers if b.defense > attacker.attack]
        if potential_blockers:
            blocker = max(potential_blockers, key=lambda x: x.attack)
            blockers.append(blocker)
            available_blockers.remove(blocker)
            game.log_action(f"AI blocks {attacker.name} with {blocker.name}")
        else:
            blockers.append(None)
            game.log_action(f"AI doesn't block {attacker.name}")
    
    return blockers


def assign_blockers(game, blockers, attackers):
    assignments = {}
    for attacker, blocker in zip(attackers, blockers):
        if blocker:
            assignments[attacker] = blocker
    return assignments

def resolve_combat(game, attacking_player, defending_player, attackers, blockers):
    for i, attacker in enumerate(attackers):
        if i < len(blockers) and blockers[i]:
            blocker = blockers[i]
            game.log_action(f"{attacker.name} is blocked by {blocker.name}.")
            
            # Creatures deal damage to each other
            attacker.defense -= blocker.attack
            blocker.defense -= attacker.attack
            
            game.log_action(f"{attacker.name} deals {attacker.attack} damage to {blocker.name}.")
            game.log_action(f"{blocker.name} deals {blocker.attack} damage to {attacker.name}.")
            
            # Check if creatures are destroyed
            if attacker.defense <= 0:
                game.log_action(f"{attacker.name} (ID: {attacker.id}) is destroyed.")
                attacking_player.battlezone.remove(attacker)
                attacking_player.graveyard.append(attacker)
            if blocker.defense <= 0:
                game.log_action(f"{blocker.name} (ID: {blocker.id}) is destroyed.")
                defending_player.battlezone.remove(blocker)
                defending_player.graveyard.append(blocker)
        else:
            # Unblocked creature deals damage to the defending player
            damage = attacker.attack
            defending_player.life -= damage
            game.log_action(f"{attacker.name} deals {damage} damage to {defending_player.name}.")
    
    if defending_player.life <= 0:
        game.game_over = True
        game.log_action(f"{defending_player.name}'s life reached 0. {attacking_player.name} wins!")

def cleanup_phase(game, attacking_player, defending_player):
    for player in [attacking_player, defending_player]:
        for creature in player.battlezone[:]:
            if creature.defense <= 0:
                player.battlezone.remove(creature)
                player.graveyard.append(creature)
                game.log_action(f"{creature.name} (ID: {creature.id}) was destroyed and moved to {player.name}'s graveyard.")

    if defending_player.life <= 0:
        game.game_over = True
        game.log_action(f"{defending_player.name}'s life reached 0. {attacking_player.name} wins!")