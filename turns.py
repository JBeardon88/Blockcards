# card_game/turns.py
from colorama import Fore, Back, Style
from player_effects import Effect, gain_energy


def upkeep_phase(board, player=True):
    current_player = board.player if player else board.opponent
    initial_energy = current_player.energy

    # First, apply the natural energy gain
    current_player.increase_energy()

    # Then, apply effects
    for card in current_player.battlezone + current_player.environs:
        for effect in card.effects:
            if 'trigger' not in effect:
                print(f"DEBUG: Effect missing 'trigger' key in card {card.name} (ID: {card.id})")
                continue
            if effect['trigger'] == 'upkeep' and effect['type'] == 'increase_energy_regen':
                effect_instance = Effect(effect['type'], effect['value'], effect['trigger'], card.id)
                effect_instance.apply(board.game, current_player)

    # Apply the energy regeneration effects
    current_player.apply_energy_regen_effects()

    energy_gained = current_player.energy - initial_energy

    drawn_card = current_player.draw_card()
    for card in current_player.battlezone:
        card.untap()
        card.remove_summoning_sickness()

    log_entry = f"{current_player.name}'s Upkeep: Energy increased from {initial_energy} to {current_player.energy} (gained {energy_gained}). All creatures untapped. "
    if drawn_card:
        log_entry += f"Drew Card: {drawn_card.name} (Attack: {drawn_card.attack}, Defense: {drawn_card.defense}, Cost: {drawn_card.cost})"
    return log_entry, Fore.YELLOW


def end_phase(game, player=True):
    current_player = game.player if player else game.opponent
    log_entries = []
    
    while len(current_player.hand) > 7:
        if player:
            game.display_game_state()  # This should now work
            print(f"\nYou must discard down to 7 cards. Current hand size: {len(current_player.hand)}")
            for i, card in enumerate(current_player.hand):
                print(f"{i + 1}. {card.name} (Attack: {card.attack}, Defense: {card.defense}, Cost: {card.cost})")
            
            while True:
                try:
                    index = int(input("Enter the index of the card to discard: ")) - 1
                    if 0 <= index < len(current_player.hand):
                        discarded_card = current_player.hand.pop(index)
                        current_player.graveyard.append(discarded_card)
                        log_entries.append((f"Discarded Card: {discarded_card.name} (Attack: {discarded_card.attack}, Defense: {discarded_card.defense}, Cost: {discarded_card.cost})", Fore.YELLOW))
                        break
                    else:
                        print("Invalid index. Please enter a number corresponding to a card in your hand.")
                except ValueError:
                    print("Invalid input. Please enter a valid number.")
        else:
            # AI discard logic (for simplicity, just discard the last card)
            discarded_card = current_player.hand.pop()
            current_player.graveyard.append(discarded_card)
            log_entries.append((f"AI Discarded Card: {discarded_card.name} (Attack: {discarded_card.attack}, Defense: {discarded_card.defense}, Cost: {discarded_card.cost})", Fore.YELLOW))
    
    return log_entries

def opponent_turn_structure(game):
    # Upkeep Phase
    log_entry, color = upkeep_phase(game.board, player=False)
    if log_entry:
        game.log_action(log_entry, color)

    # First Main Phase
    game.log_action("Opponent's First Main Phase", Fore.YELLOW)
    # AI logic will be called here from game.py

    # Combat Phase
    game.log_action("Opponent's Combat Phase", Fore.YELLOW)
    # AI logic will be called here from game.py

    # Second Main Phase
    game.log_action("Opponent's Second Main Phase", Fore.YELLOW)
    # AI logic will be called here from game.py

    # End Phase
    log_entries = end_phase(game, player=False)
    for entry in log_entries:
        game.log_action(entry[0], entry[1])