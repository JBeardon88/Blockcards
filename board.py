# card_game/board.py
import random
from colorama import Fore, Back, Style, init
from card import Card
from player_effects import Effect

init(autoreset=True)

class Board:
    def __init__(self, player, opponent, game):
        self.player = player
        self.opponent = opponent
        self.game = game  # Store the reference to the Game instance

    def reshuffle_deck(self, player=True):
        if player:
            self.player.deck.extend(self.player.graveyard)
            self.player.graveyard.clear()
            random.shuffle(self.player.deck)
            print(Fore.GREEN + "Player's deck reshuffled!")
        else:
            self.opponent.deck.extend(self.opponent.graveyard)
            self.opponent.graveyard.clear()
            random.shuffle(self.opponent.deck)
            print(Fore.GREEN + "Opponent's deck reshuffled!")

    def reset(self, card_pool, deck_size=30):
        self.player.hand.clear()
        self.player.graveyard.clear()
        self.player.battlezone.clear()
        self.player.environs.clear()
        self.player.deck.clear()

        self.opponent.hand.clear()
        self.opponent.graveyard.clear()
        self.opponent.battlezone.clear()
        self.opponent.environs.clear()
        self.opponent.deck.clear()

        self.player.life = 20
        self.opponent.life = 20
        self.player.energy = 2
        self.opponent.energy = 2

        self.build_deck(card_pool, deck_size, player=True)
        self.build_deck(card_pool, deck_size, player=False)
        print(Fore.GREEN + "Game reset!")
        self.build_deck(card_pool, deck_size, player=True)
        self.build_deck(card_pool, deck_size, player=False)
        print(Fore.GREEN + "Game reset!")

    def build_deck(self, card_pool, deck_size=30, player=True):
        deck = []
        card_counts = {}
        while len(deck) < deck_size:
            card_data = random.choice(card_pool)
            card_name = card_data['name']
            if card_counts.get(card_name, 0) < 2:
                card = Card(
                    name=card_data['name'],
                    card_type=card_data['card_type'],
                    cost=card_data['cost'],
                    attack=card_data['attack'],
                    defense=card_data['defense'],
                    description=card_data['description'],
                    effects=card_data.get('effects', []),
                    flavor_text=card_data.get('flavor_text', ''),
                    owner=self.player if player else self.opponent
                )
                deck.append(card)
                card_counts[card_name] = card_counts.get(card_name, 0) + 1

        if player:
            self.player.deck = deck
        else:
            self.opponent.deck = deck

    def display_board(self):
        print(Fore.CYAN + "\nOpponent's Battlezone:")
        for card in self.opponent.battlezone:
            print(f"  {card.name} (Attack: {card.attack}, Defense: {card.defense}, Cost: {card.cost})")

        print(Fore.CYAN + "\nOpponent's Environs:")
        for card in self.opponent.environs:
            print(f"  {card.name} (Attack: {card.attack}, Defense: {card.defense}, Cost: {card.cost})")

        print(Fore.CYAN + "\nPlayer's Battlezone:")
        for card in self.player.battlezone:
            print(f"  {card.name} (Attack: {card.attack}, Defense: {card.defense}, Cost: {card.cost})")

        print(Fore.CYAN + "\nPlayer's Environs:")
        for card in self.player.environs:
            print(f"  {card.name} (Attack: {card.attack}, Defense: {card.defense}, Cost: {card.cost})")

    def play_card(self, card, player=True):
        target_player = self.player if player else self.opponent
        if target_player.spend_energy(card.cost):
            card.owner = target_player  # Set the card's owner
            target_player.hand.remove(card)
            if card.card_type == "creature":
                target_player.battlezone.append(card)
                card.tap()  # Tap the creature when it's played
                self.game.summon_effects(card, target_player)
            elif card.card_type in ["enchantment", "equipment"]:
                target_player.environs.append(card)
                if card.card_type == "equipment":
                    self.game.last_played_card = card
                    self.game.check_triggers(target_player, "on_play_equipment", card)
            elif card.card_type == "spell":
                # Apply spell effects immediately
                for effect in card.effects:
                    effect_instance = Effect(effect['type'], effect.get('value'), effect['trigger'], card.id)
                    effect_instance.apply(self.game, target_player, card_played=card)
                # Move spell to graveyard after resolving
                self.move_card_to_graveyard(card, player)
            else:
                # For any unhandled card types, move them to graveyard
                self.move_card_to_graveyard(card, player)
                self.game.log_action(f"Unhandled card type {card.card_type}. {card.name} moved to graveyard.")
            
            self.game.log_action(f"{target_player.name} played {card.name}")
            self.game.update_display()  # Update display after playing a card
            
            # Check triggers for all card types
            self.game.check_triggers(target_player, "on_play", card)
            
            print(f"DEBUG: Played card {card.name} with ID {card.id}")
            return True
        else:
            self.game.log_action(f"Insufficient energy to play {card.name}.")
            return False
        
    def get_all_cards(self):
        return self.player.battlezone + self.player.environs + self.player.graveyard + self.opponent.battlezone + self.opponent.environs + self.opponent.graveyard


    def move_card_to_graveyard(self, card, player):
        target_player = self.player if player else self.opponent
        if card in target_player.hand:
            target_player.hand.remove(card)
        elif card in target_player.battlezone:
            target_player.battlezone.remove(card)
        elif card in target_player.environs:
            target_player.environs.remove(card)
        card.owner.graveyard.append(card)  # Always move to the owner's graveyard
        self.game.log_action(f"{card.name} moved to {card.owner.name}'s graveyard.")

    def __repr__(self):
        return (f"Opponent's Board:\n"
                f"  Life: {self.opponent.life}\n"
                f"  Energy: {self.opponent.energy}/{self.opponent.max_energy}\n"
                f"  Deck: {len(self.opponent.deck)} cards\n"
                f"  Hand: {len(self.opponent.hand)} cards\n"
                f"  Battlezone: {len(self.opponent.battlezone)} cards\n"
                f"  Environs: {len(self.opponent.environs)} cards\n"
                f"  Graveyard: {len(self.opponent.graveyard)} cards\n\n"
                f"Player's Board:\n"
                f"  Life: {self.player.life}\n"
                f"  Energy: {self.player.energy}/{self.player.max_energy}\n"
                f"  Deck: {len(self.player.deck)} cards\n"
                f"  Hand: {len(self.player.hand)} cards\n"
                f"  Battlezone: {len(self.player.battlezone)} cards\n"
                f"  Environs: {len(self.player.environs)} cards\n"
                f"  Graveyard: {len(self.player.graveyard)} cards\n")