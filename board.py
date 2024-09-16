# card_game/board.py
import random
from colorama import Fore, Back, Style, init
from card import Card
from effects import Effect

init(autoreset=True)

class Board:
    def __init__(self, player, opponent, game):
        self.player = player
        self.opponent = opponent
        self.game = game  # Store the reference to the Game instance

    def reset(self, player_card_pool, opponent_card_pool, deck_size=30):
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

        self.build_deck(player_card_pool, deck_size, player=True)
        self.build_deck(opponent_card_pool, deck_size, player=False)
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



    def get_all_cards(self):
        return self.player.battlezone + self.player.environs + self.player.graveyard + self.opponent.battlezone + self.opponent.environs + self.opponent.graveyard


    def move_card_to_graveyard(self, card, player):
        target_player = self.player if player else self.opponent
        if card in target_player.hand:
            target_player.hand.remove(card)
        elif card in target_player.battlezone:
            target_player.battlezone.remove(card)
            # Remove constant effects when a creature leaves the battlefield
            for effect in card.effects:
                if effect['trigger'] == 'constant':
                    effect_instance = Effect(effect['type'], -effect['value'], effect['trigger'], card.id)
                    effect_instance.apply(self.game, target_player)
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