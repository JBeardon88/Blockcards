import uuid
from colorama import Fore, Style
from utils import check_and_destroy


class Card:
    def __init__(self, name, attack, defense, cost, description, card_type, effects=None, flavor_text="", owner=None):
        self.name = name
        self.attack = attack
        self.defense = defense
        self.cost = cost
        self.description = description
        self.card_type = card_type
        self.effects = effects if effects is not None else []
        self.id = str(uuid.uuid4())[:8]  # Generate a new UUID and take first 8 characters
        self._summoning_sickness = True
        self._tapped = False
        self.flavor_text = flavor_text
        self.owner = owner
        self.equipped_to = None  # Track which creature this equipment is attached to
        self.equipment = None  # Track what equipment is attached to this creature

    def __str__(self):
        return f"{self.name} (Type: {self.card_type}, Cost: {self.cost}, ATK/DEF: {self.attack}/{self.defense}, Flavor Text: {self.flavor_text}, ID: {self.id})"

    def tap(self):
        self._tapped = True

    def untap(self):
        self._tapped = False
    
    @property
    def summoning_sickness(self):
        return self._summoning_sickness

    @summoning_sickness.setter
    def summoning_sickness(self, value):
        if not isinstance(value, bool):
            raise ValueError("summoning_sickness must be a boolean value")
        self._summoning_sickness = value

    @property
    def tapped(self):
        return self._tapped

    @tapped.setter
    def tapped(self, value):
        if not isinstance(value, bool):
            raise ValueError("tapped must be a boolean value")
        self._tapped = value

    def can_attack(self):
        return not (self.summoning_sickness or self.tapped)

    def can_use_tap_ability(self):
        return not (self.summoning_sickness or self.tapped)

    def remove_summoning_sickness(self):
        self.summoning_sickness = False

    def __repr__(self):
        return (f"Card(name={self.name}, attack={self.attack}, defense={self.defense}, "
                f"cost={self.cost}, description={self.description}, card_type={self.card_type}, "
                f"effects={self.effects}, id={self.id}, tapped={self.tapped}, "
                f"summoning_sickness={self.summoning_sickness})")


    def destroy(self, game):
        while self.defense <= 0:
            if self.equipment:
                game.log_action(f"{self.equipment.name} was unequipped from {self.name}")
                self.equipment.unequip()
                self.equipment = None
            else:
                owner = game.player if self in game.player.battlezone else game.opponent
                owner.battlezone.remove(self)
                owner.graveyard.append(self)
                game.log_action(f"{self.name} was destroyed and moved to {owner.name}'s graveyard.")
                break

    def fight(self, other):
        self.defense -= other.attack
        other.defense -= self.attack
        print(f"DEBUG: {self.name} (ID: {self.id}) fought {other.name} (ID: {other.id})")


    
    def receive_damage(self, amount):
        self.defense -= amount
        print(f"DEBUG: {self.name} (ID: {self.id}) received {amount} damage. New defense: {self.defense}")
        if self.defense <= 0:
            print(f"DEBUG: {self.name} (ID: {self.id}) was destroyed")
            return True  # Indicate that the card was destroyed
        return False

    def apply_effects(self, game, player):
        for effect in self.effects:
            if 'trigger' in effect and effect['trigger'] == 'constant' and self.name == "Tactical Drone":
                player.equipment_cost_reduction += effect.get('value', 0)

    def remove_effects(self, game, player):
        for effect in self.effects:
            if 'trigger' in effect and effect['trigger'] == 'constant' and self.name == "Tactical Drone":
                player.equipment_cost_reduction -= effect.get('value', 0)

    def get_adjusted_cost(self, player):
        original_cost = str(self.cost).rjust(3)
        if self.card_type == "equipment":
            adjusted_cost = max(0, self.cost - player.equipment_cost_reduction)
            if adjusted_cost != self.cost:
                return f"{Fore.BLUE}{str(adjusted_cost).rjust(3)}{Style.RESET_ALL}"
        return original_cost

    def equip(self, target):
        if self.card_type == "equipment" and target.card_type == "creature" and target.can_use_tap_ability():
            if self.equipped_to:
                self.unequip()
            self.equipped_to = target
            target.equipment = self
            self.apply_equipment_effects(target)
            print(f"DEBUG: {self.name} equipped to {target.name}")
            return True
        return False

    def unequip(self):
        if self.equipped_to:
            self.remove_equipment_effects(self.equipped_to)
            equipped_to_name = self.equipped_to.name if self.equipped_to else "Unknown"
            self.equipped_to.equipment = None
            self.equipped_to = None
            print(f"DEBUG: {self.name} unequipped from {equipped_to_name}")

    def apply_equipment_effects(self, target):
        for effect in self.effects:
            if effect['type'] == 'gain_attack':
                target.attack += effect['value']
                print(f"DEBUG: {target.name}'s attack increased by {effect['value']} to {target.attack}")
            elif effect['type'] == 'gain_defense':
                target.defense += effect['value']
                print(f"DEBUG: {target.name}'s defense increased by {effect['value']} to {target.defense}")

    def remove_equipment_effects(self, target):
        for effect in self.effects:
            if effect['type'] == 'gain_attack':
                target.attack -= effect['value']
                print(f"DEBUG: {target.name}'s attack decreased by {effect['value']} to {target.attack}")
            elif effect['type'] == 'gain_defense':
                target.defense -= effect['value']
                print(f"DEBUG: {target.name}'s defense decreased by {effect['value']} to {target.defense}")

def check_and_destroy(self, game):
    if self.defense <= 0:
        self.destroy(game)