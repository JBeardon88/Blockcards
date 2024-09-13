from typing import TYPE_CHECKING
from card import Card

if TYPE_CHECKING:
    from game import Game

def gain_energy(player, energy):
    player.energy += energy
    player.game_log.append(f"{player.name} gained {energy} energy.")

class Player:
    def __init__(self, name):
        self.name = name
        self.deck = []
        self.hand = []
        self.battlezone = []
        self.environs = []
        self.graveyard = []
        self._energy = 0
        self.base_energy_regen = 1  # Fixed and immutable natural energy gain rate
        self.energy_regen_effects = []  # Track individual energy regeneration effects
        self.life = 20
        self.applied_effects = {}
        self.game_log = []

    def draw_card(self):
        if self.deck:
            card = self.deck.pop(0)
            self.hand.append(card)
            print(f"DEBUG: Drew card {card.name} with ID {card.id}")
            return card
        return None

    def take_damage(self, amount):
        self.life -= amount
        print(f"DEBUG: {self.name} took {amount} damage. Remaining life: {self.life}")

    @property
    def energy(self):
        return self._energy

    @energy.setter
    def energy(self, value):
        self._energy = value

    def increase_energy(self):
        # Always add the fixed natural energy gain rate
        gain_energy(self, self.base_energy_regen)
        print(f"{self.name}'s energy increased to {self.energy} (natural gain)")

    def apply_energy_regen_effects(self):
        # Apply additional energy from effects separately
        additional_energy = sum(effect.value for effect in self.energy_regen_effects)
        if additional_energy > 0:
            gain_energy(self, additional_energy)
            print(f"{self.name}'s energy increased by {additional_energy} from effects, now at {self.energy}")

    def remove_energy_regen_effect(self, effect):
        if effect in self.energy_regen_effects:
            self.energy_regen_effects.remove(effect)
            print(f"Removed energy regeneration effect from card ID {effect.source_id}")

    def play_card(self, card_index):
        if 0 <= card_index < len(self.hand):
            card = self.hand[card_index]
            if self.energy >= card.cost:
                self.energy -= card.cost
                self.hand.pop(card_index)
                self.sort_card_to_zone(card)
                for effect in card.effects:
                    effect_instance = Effect(effect['type'], effect['value'], effect['trigger'], card.id)
                    effect_instance.apply(self.game, self)
                print(f"DEBUG: Played card {card.name} with ID {card.id}")
                return card
        return None

    def sort_card_to_zone(self, card):
        if card.card_type == "creature":
            self.battlezone.append(card)
        elif card.card_type in ["enchantment", "equipment"]:
            self.environs.append(card)
        elif card.card_type == "spell":
            self.move_card_to_graveyard(card)
        print(f"DEBUG: Moved card {card.name} with ID {card.id} to {card.card_type} zone")

    def move_card_to_graveyard(self, card):
        if card in self.battlezone:
            self.battlezone.remove(card)
        elif card in self.hand:
            self.hand.remove(card)
        elif card in self.environs:
            self.environs.remove(card)
        card.owner.graveyard.append(card)  # Always move to the owner's graveyard
        print(f"DEBUG: Moved card {card.name} with ID {card.id} to graveyard")

    def display_hand(self):
        for idx, card in enumerate(self.hand, 1):
            print(f"{idx}: {card.name} (Attack: {card.attack}, Defense: {card.defense}, Cost: {card.cost})")

    def display_graveyard(self):
        for idx, card in enumerate(self.graveyard, 1):
            print(f"{idx}: {card.name} (Attack: {card.attack}, Defense: {card.defense}, Cost: {card.cost})")

    def spend_energy(self, cost):
        if self.energy >= cost:
            self.energy -= cost
            return True
        return False

    def discard_card(self, index):
        if 0 <= index < len(self.hand):
            card_to_discard = self.hand.pop(index)
            self.graveyard.append(card_to_discard)
            return card_to_discard
        return None

class Effect:
    def __init__(self, effect_type, value, trigger, source_id):
        self.effect_type = effect_type
        self.value = value
        self.trigger = trigger
        self.source_id = source_id
        self.applied = False

    def apply(self, game: 'Game', player: 'Player', card_played=None):
        if self.applied:
            return
        effect_handlers = {
            "increase_energy_regen": self.increase_energy_regen,
            "draw_cards": self.draw_cards,
            "deal_damage": self.deal_damage,
            "destroy_equipment": self.destroy_equipment,
            "destroy_enchantment": self.destroy_enchantment
        }
        handler = effect_handlers.get(self.effect_type)
        if handler:
            game.log_action(f"Effect triggered: {self.effect_type} from card ID {self.source_id}")
            handler(game, player)
            self.applied = True
        else:
            game.log_action(f"Unknown effect type: {self.effect_type}")

    def increase_energy_regen(self, game: 'Game', player: 'Player'):
        # Instead of modifying the energy_regen_effects list here,
        # we'll just apply the effect directly
        gain_energy(player, self.value)
        game.log_action(f"{player.name} gained {self.value} energy from card ID {self.source_id}")

    def draw_cards(self, game: 'Game', player: 'Player'):
        for _ in range(self.value):
            card = player.draw_card()
            if card:
                game.log_action(f"{player.name} drew card {card.name} (ID: {card.id})")

    def deal_damage(self, game: 'Game', player: 'Player'):
        target = game.select_target(card_type="creature_or_player", effect_description=f"Select a target to deal {self.value} damage:", player=player)
        if target:
            if isinstance(target, Player):
                target.take_damage(self.value)
                game.log_action(f"{player.name} dealt {self.value} damage to {target.name}")
            elif hasattr(target, 'receive_damage'):
                destroyed = target.receive_damage(self.value)
                game.log_action(f"{player.name} dealt {self.value} damage to {target.name} (ID: {target.id})")
                if destroyed:
                    target.destroy(game)  # Use the destroy method of the Card class
        else:
            game.log_action(f"{player.name} tried to deal damage but no valid target was found.")

    def destroy_equipment(self, game: 'Game', player: 'Player'):
        target = game.select_target(card_type="equipment", effect_description="Select an equipment to destroy:", player=player)
        self.handle_destruction(game, player, target, "equipment")

    def destroy_enchantment(self, game: 'Game', player: 'Player'):
        target = game.select_target(card_type="enchantment", effect_description="Select an enchantment to destroy:", player=player)
        self.handle_destruction(game, player, target, "enchantment")

    def handle_destruction(self, game: 'Game', player: 'Player', target, card_type: str):
        if target:
            if hasattr(target, 'destroy'):
                target.destroy(game)
                game.log_action(f"{player.name} destroyed {card_type} {target.name} (ID: {target.id}) owned by {target.owner.name}")
            else:
                game.log_action(f"{player.name} tried to destroy a {card_type} but the target was invalid.")
        else:
            game.log_action(f"{player.name} tried to destroy a {card_type} but no valid target was found.")

class Trigger:
    def __init__(self, trigger_type):
        self.trigger_type = trigger_type

    def check(self, game, player):
        if self.trigger_type == "upkeep":
            return game.turn_phase == "upkeep"
        elif self.trigger_type == "on_play_equipment":
            return game.last_played_card and game.last_played_card.card_type == "equipment"
        return False