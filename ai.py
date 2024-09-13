import random
from colorama import Fore

def ai_make_decisions(game):
    ai_main_phase(game)
    ai_combat_phase(game)
    ai_main_phase(game)

def ai_upkeep(game):
    game.opponent.increase_energy()
    game.opponent.draw_card()
    game.log_action(f"AI Upkeep: Energy increased to {game.opponent.energy}. Drew a card.", Fore.YELLOW)

def ai_main_phase(game):
    ai_player = game.opponent
    playable_cards = [card for card in ai_player.hand if card.cost <= ai_player.energy]
    
    for card in playable_cards:
        if ai_can_play_card(game, card):
            if game.play_card(ai_player, card):
                game.log_action(f"AI played {card.name}")
                game.update_display()  # Update display after AI plays a card
                input("Press Enter to continue...")
                if ai_player.energy == 0:
                    break
            else:
                break  # Stop trying to play cards if one fails

def ai_can_play_card(game, card):
    ai_player = game.opponent

    if card.card_type == "creature":
        # Play creature if there's room in the battlezone
        return len(ai_player.battlezone) < 5  # Assuming max 5 creatures in battlezone

    elif card.card_type in ["enchantment", "equipment"]:
        # Play enchantments or equipment if there's a valid target
        return len(ai_player.battlezone) > 0

    elif card.card_type == "spell":
        # For now, always play spells if possible
        return True

    return False  # Default case, don't play the card

def ai_combat_phase(game):
    ai_player = game.opponent
    attackers = [creature for creature in ai_player.battlezone if not creature.tapped and not creature.summoning_sickness]
    game.declare_attackers(ai_player, attackers)

def ai_combat_phase(game):
    attackers = [creature for creature in game.opponent.battlezone if not creature.tapped and not creature.summoning_sickness]
    if attackers:
        total_damage = sum(creature.attack for creature in attackers)
        game.player.life -= total_damage
        for creature in attackers:
            creature.tap()
        game.log_action(f"AI attacks with {len(attackers)} creatures for {total_damage} damage. Player life: {game.player.life}", Fore.RED)

def ai_end_phase(game):
    while len(game.opponent.hand) > 7:
        card_to_discard = random.choice(game.opponent.hand)
        game.opponent.hand.remove(card_to_discard)
        game.opponent.graveyard.append(card_to_discard)
        game.log_action(f"AI discarded {card_to_discard.name} due to hand size limit.", Fore.YELLOW)