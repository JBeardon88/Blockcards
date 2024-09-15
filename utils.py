def check_and_destroy(self, card):
    if card.defense <= 0:
        owner = self.player if card in self.player.battlezone else self.opponent
        owner.battlezone.remove(card)
        owner.graveyard.append(card)
        self.game.log_action(f"{card.name} was destroyed and moved to {owner.name}'s graveyard.")
        if card.equipment:
            self.unequip_card(card)