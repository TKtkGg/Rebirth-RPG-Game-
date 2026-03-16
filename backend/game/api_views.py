from . models import Player, Stage
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

def player_detail(request, player_id):
    player = get_object_or_404(Player, id=player_id)
    return JsonResponse({
        "id": player_id,
        "name": player.name,
        "level": player.level,
        "exp": player.exp,
        "max_hp": player.max_hp,
        "hp": player.hp,
        "atk": player.atk,
        "defense": player.defense,
        "spd": player.spd,
        "max_mp": player.max_mp,
        "mp": player.mp,
        "job": player.job,
        "item": player.item,
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
    })

def stage_list(request):
    stages = Stage.objects.all()
    return JsonResponse({
        "stages": list(stages.values('id', 'name', 'unlock_level', 'background_image', 'min_enemy_level', 'max_enemy_level', 'order'))
    })

def stage_detail(request, stage_id):
    stage = get_object_or_404(Stage, id=stage_id)
    return JsonResponse({
        "id": stage_id,
        "name": stage.name,
        "unlock_level": stage.unlock_level,
        "background_image": stage.background_image,
        "min_enemy_level": stage.min_enemy_level,
        "max_enemy_level": stage.max_enemy_level,
        "order": stage.order,
    })