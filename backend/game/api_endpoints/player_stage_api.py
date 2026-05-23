from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from ..api_serializers import player_to_api_dict, stage_to_api_dict
from ..models import Player, Stage


def player_detail(request, player_id):
    player = get_object_or_404(Player, id=player_id)
    return JsonResponse({
        **player_to_api_dict(player),
    })


def stage_list(request, player_id):
    player = get_object_or_404(Player, id=player_id)
    if not player:
        return JsonResponse({"error": "Player not found"}, status=404)

    stagesData = Stage.objects.all()
    return JsonResponse({
        "player": player_to_api_dict(player),
        "stages": [stage_to_api_dict(stage) for stage in stagesData],
    })
