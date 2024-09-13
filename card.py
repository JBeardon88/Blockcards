import uuid

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
        self.tapped = False
        self.summoning_sickness = True  # True when first summoned
        self.flavor_text = flavor_text
        self.owner = owner

    def __str__(self):
        return f"{self.name} (Type: {self.card_type}, Cost: {self.cost}, ATK/DEF: {self.attack}/{self.defense}, Flavor Text: {self.flavor_text}, ID: {self.id})"

    def tap(self):
        self.tapped = True

    def untap(self):
        self.tapped = False

    def remove_summoning_sickness(self):
        self.summoning_sickness = False

    def __repr__(self):
        return (f"Card(name={self.name}, attack={self.attack}, defense={self.defense}, "
                f"cost={self.cost}, description={self.description}, card_type={self.card_type}, "
                f"effects={self.effects}, id={self.id}, tapped={self.tapped}, "
                f"summoning_sickness={self.summoning_sickness})")


    def destroy(self, game):
        # Remove the card from wherever it is
        for zone in [self.owner.battlezone, self.owner.environs, self.owner.hand, self.owner.deck]:
            if self in zone:
                zone.remove(self)
                break

        # Remove the card's effects from the game state
        for effect in self.effects:
            if effect['trigger'] == 'upkeep':
                self.owner.remove_energy_regen_effect(effect)

        # Always move the card to the owner's graveyard
        self.owner.graveyard.append(self)
        game.log_action(f"{self.name} (ID: {self.id}) was destroyed and moved to {self.owner.name}'s graveyard.")


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