from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from card import Card


def gain_energy(player, energy):
    player.energy += energy
    player.game_log.append(f"{player.name} gained {energy} energy.")



class Player:
    def __init__(self, name, game):
        self.name = name
        self.game = game
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
        self.equipment_cost_reduction = 0

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
        if 'value' in effect:
            self.energy_regen_effects = [e for e in self.energy_regen_effects if e['id'] != effect.get('id')]
            self.recalculate_energy_regen()

    def recalculate_energy_regen(self):
        self.energy_regen = self.base_energy_regen + sum(effect['value'] for effect in self.energy_regen_effects)

    def play_card(self, card: 'Card'):
        if hasattr(card, 'get_numeric_adjusted_cost') and hasattr(card, 'card_type'):
            adjusted_cost = card.get_numeric_adjusted_cost(self)
            if self.energy >= adjusted_cost:
                self.energy -= adjusted_cost
                self.hand.remove(card)
                
                if card.card_type == "spell":
                    self.game.log_action(f"{self.name} cast {card.name}.")
                    card.apply_effects(self.game, self)
                    self.graveyard.append(card)
                    self.game.log_action(f"{card.name} was moved to {self.name}'s graveyard.")
                elif card.card_type in ["environ", "enchantment", "equipment"]:
                    self.environs.append(card)
                    self.game.log_action(f"{self.name} played {card.name} to the environs.")
                elif card.card_type == "creature":
                    self.battlezone.append(card)
                    card.summoning_sickness = True
                    card.tapped = True
                    self.game.log_action(f"{self.name} played {card.name} to the battlezone.")
                else:
                    self.graveyard.append(card)
                    self.game.log_action(f"Unhandled card type {card.card_type}. {card.name} moved to graveyard.")
                
                if card.card_type != "spell":
                    card.apply_effects(self.game, self)
                return True
            else:
                print(f"Not enough energy to play {card.name}. It costs {adjusted_cost}, but you only have {self.energy} energy.")
                return False
        else:
            print("Error: Invalid card object passed to play_card method.")
            return False

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
            display_cost = card.get_display_cost(self)
            print(f"{idx}: {card.name} (Attack: {card.attack}, Defense: {card.defense}, Cost: {display_cost})")

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

    def calculate_equipment_cost_reduction(self):
        reduction = 0
        for card in self.battlezone:
            if card.name == "Tactical Drone":
                reduction += 1
        return reduction

    def equip_card(self, equipment_index, target_index):
        if 0 <= equipment_index < len(self.environs) and 0 <= target_index < len(self.battlezone):
            equipment = self.environs[equipment_index]
            target = self.battlezone[target_index]
            if equipment.card_type == "equipment" and target.card_type == "creature":
                if target.equipment:
                    self.unequip_card(target_index)
                equipment.equip(target)
                self.game.log_action(f"{self.name} equipped {equipment.name} to {target.name}")
                self.game.log_action(f"{target.name}'s attack is now {target.attack}")
                return True
        return False

    def unequip_card(self, creature_index):
        if 0 <= creature_index < len(self.battlezone):
            creature = self.battlezone[creature_index]
            if creature.equipment:
                equipment = creature.equipment
                equipment.unequip()
                self.game.log_action(f"{self.name} unequipped {equipment.name} from {creature.name}")
                self.game.log_action(f"{creature.name}'s attack is now {creature.attack}")
                return True
        return False