def check_and_destroy(self, card):
    if card.defense <= 0:
        owner = self.player if card in self.player.battlezone else self.opponent
        if card in owner.battlezone:
            owner.battlezone.remove(card)
        if card.equipment:
            card.equipment.unequip()
        owner.graveyard.append(card)
        self.game.log_action(f"{card.name} was destroyed and moved to {owner.name}'s graveyard.")