from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from ..api_serializers import player_to_api_dict
from ..models import Player, Stage


def player_detail(request, player_id):
    player = get_object_or_404(Player, id=player_id)
    return JsonResponse({
        **player_to_api_dict(player),
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

