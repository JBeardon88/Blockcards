def check_and_destroy(game, card):
    if card.defense <= 0:
        from combat import destroy_creature
        destroy_creature(game, card)