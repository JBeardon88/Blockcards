# card_game/turns.py
from colorama import Fore, Back, Style
from effects import Effect
from player import gain_energy
from ai import ai_main_phase, ai_combat_phase, ai_end_phase
from utils import check_and_destroy


def upkeep_phase(board, player=True):
    current_player = board.player if player else board.opponent
    
    print(f"\nDEBUG: ===== STARTING UPKEEP PHASE FOR {current_player.name} =====")
    
    initial_energy = current_player.energy

    print(f"DEBUG: {current_player.name}'s Upkeep Phase - Initial Energy: {initial_energy}, Hand: {[card.name for card in current_player.hand]}")

    # First, apply the natural energy gain
    current_player.increase_energy()

    # Reset the effect_processed flag for all cards
    for card in current_player.battlezone + current_player.environs:
        card.reset_effect_processed()

    # Keep track of triggered effects
    triggered_effects = set()

    processed_effects = set()

    # Then, apply effects
    for card in current_player.battlezone + current_player.environs:
        print(f"DEBUG: Processing effects for {card.name} (ID: {card.id})")
        for effect in card.effects:
            effect_key = (card.id, effect['type'], effect.get('source_id'))
            if effect_key in processed_effects:
                print(f"DEBUG: Skipping already processed effect: {effect}")
                continue
            processed_effects.add(effect_key)
            print(f"DEBUG: Effect: {effect}")
            if 'trigger' not in effect:
                print(f"DEBUG: Effect missing 'trigger' key in card {card.name} (ID: {card.id})")
                continue
            if effect['trigger'] == 'upkeep':
                if card.card_type == "equipment" and not card.equipped_to:
                    continue  # Skip effects for unequipped equipment
                effect_key = (card.id, effect['type'])
                if effect_key in triggered_effects:
                    print(f"DEBUG: Skipping duplicate effect for {card.name} (ID: {card.id})")
                    continue  # Skip if this effect has already been triggered this turn
                triggered_effects.add(effect_key)
                
                print(f"DEBUG: Triggering upkeep effect for {card.name} (ID: {card.id}): {effect}")
                
                if effect['type'] == 'increase_energy_regen':
                    effect_instance = Effect(effect['type'], effect['value'], effect['trigger'], card.id)
                    effect_instance.apply(board.game, current_player)
                elif effect['type'] == 'deal_damage':
                    print(f"DEBUG: Triggering upkeep deal_damage effect for {card.name} (ID: {card.id})")
                    target = board.game.select_target(card_type="creature", effect_description=f"{card.name} can deal {effect['value']} damage to any target creature:", player=current_player)
                    if target:
                        target.receive_damage(effect['value'])
                        board.game.log_action(f"{card.name} dealt {effect['value']} damage to {target.name} (ID: {target.id})")
                        check_and_destroy(board, target)  # Changed to use board instead of board.game

    # Apply the energy regeneration effects
    current_player.apply_energy_regen_effects()

    energy_gained = current_player.energy - initial_energy

    drawn_card = current_player.draw_card()
    for card in current_player.battlezone:
        card.tapped = False
        card.summoning_sickness = False  # Remove summoning sickness

    log_entry = f"{current_player.name}'s Upkeep: Energy increased from {initial_energy} to {current_player.energy} (gained {energy_gained}). All creatures untapped and summoning sickness removed. "
    if drawn_card:
        log_entry += f"Drew Card: {drawn_card.name} (Attack: {drawn_card.attack}, Defense: {drawn_card.defense}, Cost: {drawn_card.cost})"
    print(f"DEBUG: {current_player.name}'s Upkeep Phase - Final Energy: {current_player.energy}, Hand: {[card.name for card in current_player.hand]}")
    
    print(f"DEBUG: ===== ENDING UPKEEP PHASE FOR {current_player.name} =====\n")
    
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
                    index = int(input("Enter the index of the card to discard: ").strip()) - 1
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
    try:
        print("DEBUG: Opponent turn started")
        
        # Upkeep Phase
        log_entry, color = upkeep_phase(game.board, player=False)
        if log_entry:
            game.log_action(log_entry, color)
        print("DEBUG: Opponent upkeep phase completed")

        # First Main Phase
        game.log_action("Opponent's First Main Phase", Fore.YELLOW)
        print("DEBUG: Opponent first main phase started")
        ai_main_phase(game)
        print("DEBUG: Opponent first main phase completed")

        # Combat Phase
        game.log_action("Opponent's Combat Phase", Fore.YELLOW)
        print("DEBUG: Opponent combat phase started")
        ai_combat_phase(game)
        print("DEBUG: Opponent combat phase completed")

        # Second Main Phase
        game.log_action("Opponent's Second Main Phase", Fore.YELLOW)
        print("DEBUG: Opponent second main phase started")
        ai_main_phase(game)
        print("DEBUG: Opponent second main phase completed")

        # End Phase
        log_entries = end_phase(game, player=False)
        for entry in log_entries:
            game.log_action(entry[0], entry[1])
        ai_end_phase(game)
        print("DEBUG: Opponent end phase completed")
    except Exception as e:
        print(f"ERROR: An exception occurred during the opponent's turn: {str(e)}")
        game.log_action(f"ERROR: An exception occurred during the opponent's turn: {str(e)}", Fore.RED)