def player_to_api_dict(player):
    return {
        "id": player.id,
        "name": player.name,
        "level": player.level,
        "exp": player.exp,
        "next_exp": player.next_exp,
        "max_hp": player.max_hp,
        "hp": player.hp,
        "atk": player.atk,
        "defense": player.defense,
        "spd": player.spd,
        "max_mp": player.max_mp,
        "mp": player.mp,
        "stat_points": player.stat_points,
        "job": player.job,
        "item": player.item,
        "weapon": player.weapon.name,
        "armor": player.armor.name,
        "defeats": player.defeats,
        "strong_defeats": player.strong_defeats,
        "death_count": player.death_count,
        "gold": player.gold,
        "gold_rate": player.gold_rate,
        "exp_rate": player.exp_rate,
        "total_max_hp_battle": player.total_max_hp_battle,
        "total_hp_battle": player.total_hp_battle,
        "total_atk_battle": player.total_atk_battle,
        "total_def_battle": player.total_def_battle,
        "total_spd_battle": player.total_spd_battle,
    }


def equipment_to_api_dict(equipment):
    return {
        "id": equipment.id,
        "name": equipment.name,
        "equipment_type": equipment.equipment_type,
        "price": equipment.price,
        "description": equipment.description,
        "atk_bonus": equipment.atk_bonus,
        "def_bonus": equipment.def_bonus,
        "hp_bonus": equipment.hp_bonus,
        "spd_bonus": equipment.spd_bonus,
    }


def item_to_api_dict(item):
    current_stock = getattr(item, 'current_stock', item.max_stock)
    return {
        "id": item.id,
        "name": item.name if item else None,
        "target": item.target,
        "effect_amount": item.effect_amount,
        "price": item.price,
        "description": item.description,
        "max_stock": item.max_stock,
        "current_stock": current_stock,
    }

