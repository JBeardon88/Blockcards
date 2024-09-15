import random
from colorama import Fore, Style
from combat import declare_attackers, ai_declare_blockers, resolve_combat_phase, cleanup_phase, declare_blockers

def ai_upkeep(game):
    game.opponent.energy += 1
    game.opponent.draw_card()
    game.log_action(f"AI Upkeep: Energy increased to {game.opponent.energy}. Drew a card.", Fore.YELLOW)
    print(f"DEBUG: AI Upkeep - Energy: {game.opponent.energy}, Hand: {[card.name for card in game.opponent.hand]}")

def ai_main_phase(game):
    ai_player = game.opponent
    playable_cards = [card for card in ai_player.hand if ai_can_play_card(game, card)]
    
    if playable_cards:
        card_to_play = random.choice(playable_cards)
        game.log_action(f"AI attempts to play {card_to_play.name}", Fore.YELLOW)
        if ai_player.play_card(card_to_play):  # Changed from game.player to ai_player
            game.log_action(f"AI successfully played {card_to_play.name}", Fore.GREEN)
        else:
            game.log_action(f"AI failed to play {card_to_play.name}", Fore.RED)
    else:
        game.log_action("AI has no playable cards", Fore.YELLOW)
    
    # Add a prompt for the player to acknowledge the AI's action
    input("Press Enter to continue...")

def ai_combat_phase(game):
    game.log_action("AI Combat Phase", Fore.YELLOW)
    
    # Declare attackers
    available_attackers = [creature for creature in game.opponent.battlezone if not creature.tapped and not creature.summoning_sickness]
    attackers = declare_attackers(game, game.opponent)
    
    if attackers:
        game.log_action(f"AI declares {len(attackers)} attacker(s)", Fore.RED)
        for attacker in attackers:
            game.log_action(f"AI attacks with {attacker.name}", Fore.RED)
        
        # Allow player to declare blockers
        game.update_display()
        blockers = declare_blockers(game, game.player, attackers)
        
        # Resolve combat
        resolve_combat_phase(game, attackers, blockers)
    else:
        game.log_action("AI doesn't declare any attackers", Fore.YELLOW)
    
    # Cleanup phase
    cleanup_phase(game, game.opponent, game.player)
    
    game.update_display()
    input("Press Enter to continue...")

def ai_end_phase(game):
    game.log_action("AI End Phase", Fore.YELLOW)
    while len(game.opponent.hand) > 7:
        card_to_discard = random.choice(game.opponent.hand)
        game.opponent.hand.remove(card_to_discard)
        game.opponent.graveyard.append(card_to_discard)
        game.log_action(f"AI discarded {card_to_discard.name} due to hand size limit.", Fore.YELLOW)
        print(f"DEBUG: AI discarded {card_to_discard.name} due to hand size limit.")

def ai_can_play_card(game, card):
    can_play = game.opponent.energy >= card.cost and len(game.opponent.battlezone) < 5  # Assuming max 5 creatures
    #print(f"DEBUG: Can AI play {card.name}? {'Yes' if can_play else 'No'}")
    return can_play

def ai_make_decisions(game):
    # This function can be used for more complex decision-making in the future
    # For now, it will just call the main phase and combat phase
    ai_main_phase(game)
    ai_combat_phase(game)
    ai_main_phase(game)  # Second main phase