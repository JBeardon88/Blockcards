from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game import Game
    from player import Player


from player import gain_energy

def create_effect(effect_type, value, trigger, source_id):
    print(f"Creating effect: {effect_type}, {value}, {trigger}, {source_id}")
    return Effect(effect_type, value, trigger, source_id)

class Effect:
    def __init__(self, effect_type, value, trigger, source_id):
        print(f"Initializing Effect: {effect_type}, {value}, {trigger}, {source_id}")
        self.effect_type = effect_type
        self.value = value
        self.trigger = trigger
        self.source_id = source_id
        self.applied = False

    def apply(self, game: 'Game', player: 'Player', card_played=None):
        if self.applied and self.trigger != "constant":
            return
        effect_handlers = {
            "increase_energy_regen": self.increase_energy_regen,
            "draw_cards": self.draw_cards,
            "deal_damage": self.deal_damage,
            "destroy_equipment": self.destroy_equipment,
            "destroy_enchantment": self.destroy_enchantment,
            "reduce_equipment_cost": self.reduce_equipment_cost,
            "gain_defense": self.gain_defense
        }
        handler = effect_handlers.get(self.effect_type)
        if handler:
            game.log_action(f"Effect triggered: {self.effect_type} from card ID {self.source_id}")
            handler(game, player)
            self.applied = True
        else:
            game.log_action(f"Unknown effect type: {self.effect_type}")

    def increase_energy_regen(self, game: 'Game', player: 'Player'):
        gain_energy(player, self.value)
        game.log_action(f"{player.name} gained {self.value} energy from card ID {self.source_id}")

    def draw_cards(self, game: 'Game', player: 'Player'):
        for _ in range(self.value):
            card = player.draw_card()
            if card:
                game.log_action(f"{player.name} drew card {card.name} (ID: {card.id})")

    def deal_damage(self, game: 'Game', player: 'Player'):
        print(f"DEBUG: Attempting to deal damage")
        target = game.select_target(card_type="creature_or_player", effect_description=f"Select a target to deal {self.value} damage:", player=player)
        if target:
            print(f"DEBUG: Target selected: {target.name} (ID: {target.id})")
            if isinstance(target, Player):
                target.take_damage(self.value)
                game.log_action(f"{player.name} dealt {self.value} damage to {target.name}")
            elif hasattr(target, 'receive_damage'):
                destroyed = target.receive_damage(self.value)
                game.log_action(f"{player.name} dealt {self.value} damage to {target.name} (ID: {target.id})")
                if destroyed:
                    target.destroy(game)
        else:
            game.log_action(f"{player.name} tried to deal damage but no valid target was found.")
            print(f"DEBUG: No valid target found for deal_damage effect")

    def gain_defense(self, game: 'Game', player: 'Player'):
        target = game.select_target(card_type="creature", effect_description="Select a target to gain defense:", player=player)
        if target:
            target.defense += self.value
            game.log_action(f"{player.name} gained {self.value} defense to {target.name}")
        else:
            game.log_action(f"{player.name} tried to gain defense but no valid target was found.")

    def destroy_equipment(self, game: 'Game', player: 'Player'):
        target = game.select_target(card_type="equipment", effect_description="Select an equipment to destroy:", player=player)
        self.handle_destruction(game, player, target, "equipment")


    def destroy_enchantment(self, game: 'Game', player: 'Player'):
        print(f"DEBUG: Attempting to destroy an enchantment")
        target = game.select_target(card_type="enchantment", effect_description="Select an enchantment to destroy:", player=player)
        if target:
            print(f"DEBUG: Target selected: {target.name} (ID: {target.id})")
            if target in target.owner.environs:
                target.owner.environs.remove(target)
                target.owner.graveyard.append(target)
                game.log_action(f"{player.name} destroyed enchantment {target.name} (ID: {target.id}) owned by {target.owner.name}")
                print(f"DEBUG: Enchantment destroyed and moved to graveyard")
            else:
                game.log_action(f"Failed to destroy {target.name}: not found in environs.")
                print(f"DEBUG: Failed to destroy enchantment: not found in environs")
        else:
            game.log_action(f"{player.name} tried to destroy an enchantment but no valid target was found.")
            print(f"DEBUG: No valid target found for destroy_enchantment effect")

    def handle_destruction(self, game: 'Game', player: 'Player', target, card_type: str):
        if target:
            if hasattr(target, 'destroy'):
                target.destroy(game)
                game.log_action(f"{player.name} destroyed {card_type} {target.name} (ID: {target.id}) owned by {target.owner.name}")
            else:
                game.log_action(f"{player.name} tried to destroy a {card_type} but the target was invalid.")
        else:
            game.log_action(f"{player.name} tried to destroy a {card_type} but no valid target was found.")

    def reduce_equipment_cost(self, game: 'Game', player: 'Player'):
        player.equipment_cost_reduction += self.value
        game.log_action(f"{player.name}'s equipment cost reduced by {self.value}")

class Trigger:
    def __init__(self, trigger_type):
        self.trigger_type = trigger_type

    def check(self, game, player):
        if self.trigger_type == "upkeep":
            return game.turn_phase == "upkeep"
        elif self.trigger_type == "on_play_equipment":
            return game.last_played_card and game.last_played_card.card_type == "equipment"
        return False
