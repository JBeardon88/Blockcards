import uuid
from colorama import Fore, Style
from utils import check_and_destroy
from effects import Effect, create_effect, Trigger
from player import Player

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
        print(f"DEBUG: Destroying {self.name} (ID: {self.id})")
        if self.card_type == "creature" and self.equipment:
            for equip in self.equipment:
                equip.unequip(game)
        if self in self.owner.battlezone:
            self.owner.battlezone.remove(self)
        elif self in self.owner.environs:
            self.owner.environs.remove(self)
        self.owner.graveyard.append(self)
        game.log_action(f"{self.name} was destroyed and moved to {self.owner.name}'s graveyard.")

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
            print(f"DEBUG: Processing effect for {self.name}: {effect}")
            if 'trigger' in effect:
                if effect['trigger'] == 'constant':
                    if effect['type'] == 'equipment_cost_reduction':
                        value = effect.get('value', 0)
                        player.update_effect_modifier('equipment_cost_reduction', value)
                        print(f"DEBUG: Applied equipment_cost_reduction of {value} for {self.name}")
                    # Add other constant effects here
                elif effect['trigger'] == 'upkeep':
                    if self.card_type == "equipment" and not self.equipped_to:
                        continue  # Skip effects if the equipment is not equipped
                    if effect['type'] == 'deal_damage':
                        target = game.select_target(card_type="creature", effect_description=f"{self.name} can deal {effect['value']} damage to any target creature:", player=player)
                        if target:
                            target.receive_damage(effect['value'])
                            game.log_action(f"{self.name} dealt {effect['value']} damage to {target.name} (ID: {target.id})")
                    # Add other upkeep effects here
                elif effect['trigger'] == 'on_cast':
                    if self.card_type == "equipment" and not self.equipped_to:
                        continue  # Skip effects if the equipment is not equipped
                    if effect['type'] == 'draw_cards':
                        print(f"Attempting to create effect: {effect}")
                        effect_obj = create_effect(effect['type'], effect['value'], effect['trigger'], self.id)
                        print(f"Effect object created: {effect_obj}")
                        effect_obj.apply(game, player)
                    elif effect['type'] == 'destroy_equipment':
                        effect_value = effect.get('value', 0)  # Provide a default value of 0 if 'value' key is missing
                        target = game.select_target(card_type="equipment", effect_description=f"{self.name} can destroy {effect_value} equipment:", player=player)
                        if target:
                            target.destroy(game)
                            game.log_action(f"{self.name} destroyed {target.name} (ID: {target.id})")
                    elif effect['type'] == 'destroy_enchantment':
                        effect_value = effect.get('value', 0)  # Provide a default value of 0 if 'value' key is missing
                        target = game.select_target(card_type="enchantment", effect_description=f"{self.name} can destroy {effect_value} enchantment:", player=player)
                        if target:
                            target.destroy(game)
                            game.log_action(f"{self.name} destroyed {target.name} (ID: {target.id})")
                    elif effect['type'] == 'deal_damage':
                        print(f"DEBUG: Triggering on_cast deal_damage effect: {effect}")
                        target = game.select_target(card_type="creature_or_player", effect_description=f"{self.name} can deal {effect['value']} damage to any target:", player=player)
                        if target:
                            if isinstance(target, Player):
                                target.take_damage(effect['value'])
                                game.log_action(f"{self.name} dealt {effect['value']} damage to {target.name}")
                            else:
                                target.receive_damage(effect['value'])
                                game.log_action(f"{self.name} dealt {effect['value']} damage to {target.name} (ID: {target.id})")
                        else:
                            print(f"DEBUG: No target selected for deal_damage effect")
            else:
                print(f"DEBUG: Effect has no trigger: {effect}")

    def remove_effects(self, game, player):
        for effect in self.effects:
            if 'trigger' in effect and effect['trigger'] == 'constant':
                if effect['type'] == 'equipment_cost_reduction':
                    value = effect.get('value', 0)
                    player.update_effect_modifier('equipment_cost_reduction', -value)
                    print(f"DEBUG: Removed equipment_cost_reduction of {value} for {self.name}")
                # Add other constant effects here

    def get_adjusted_cost(self, player):
        original_cost = str(self.cost).rjust(3)
        if self.card_type == "equipment":
            adjusted_cost = self.get_numeric_adjusted_cost(player)
            if adjusted_cost != self.cost:
                return f"{Fore.BLUE}{str(adjusted_cost).rjust(3)}{Style.RESET_ALL}"
        return original_cost

    def get_numeric_adjusted_cost(self, player):
        if self.card_type == "equipment":
            reduction = player.effect_modifiers.get('equipment_cost_reduction', 0)
            adjusted_cost = max(0, self.cost - reduction)
            return adjusted_cost
        return self.cost

    def equip(self, target):
        if self.card_type == "equipment" and target.card_type == "creature":
            self.equipped_to = target
            target.equipment = self
            self.apply_equipment_effects(target)
            return True
        return False

    def unequip(self):
        if self.equipped_to:
            print(f"DEBUG: Unequipping {self.name} from {self.equipped_to.name}")
            self.equipped_to.equipment = None
            self.equipped_to = None
            self.owner.environs.append(self)
            self.owner.game.log_action(f"{self.name} was unequipped and moved to {self.owner.name}'s environs.")

    def apply_equipment_effects(self, target):
        for effect in self.effects:
            if effect['type'] == 'gain_attack':
                target.attack += effect['value']
                print(f"DEBUG: {target.name}'s attack increased by {effect['value']} to {target.attack}")
            elif effect['type'] == 'gain_defense':
                target.defense += effect['value']
                print(f"DEBUG: {target.name}'s defense increased by {effect['value']} to {target.defense}")
            elif effect['type'] == 'deal_damage' and effect['trigger'] == 'upkeep':
                target.effects.append({
                    "type": "deal_damage",
                    "value": effect['value'],
                    "trigger": "upkeep",
                    "source_id": self.id,
                    "source_name": self.name  # Add source name to identify the equipment
                })
                print(f"DEBUG: {target.name} gained upkeep effect to deal {effect['value']} damage")

    def remove_equipment_effects(self, target):
        for effect in self.effects:
            if effect['type'] == 'gain_attack':
                target.attack -= effect['value']
                print(f"DEBUG: {target.name}'s attack decreased by {effect['value']} to {target.attack}")
            elif effect['type'] == 'gain_defense':
                target.defense -= effect['value']
                print(f"DEBUG: {target.name}'s defense decreased by {effect['value']} to {target.defense}")
            elif effect['type'] == 'deal_damage' and effect['trigger'] == 'upkeep':
                target.effects = [
                    e for e in target.effects
                    if e.get("source_id") != self.id
                ]
                print(f"DEBUG: {target.name} lost upkeep effect to deal {effect['value']} damage")



def check_and_destroy(self, game):
    if self.defense <= 0:
        self.destroy(game)