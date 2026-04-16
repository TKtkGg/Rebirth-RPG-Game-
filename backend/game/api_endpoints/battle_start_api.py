from django.http import JsonResponse

from ..api_serializers import player_to_api_dict
from ..views.battle import allocate_stat_points, battle_start_get, rest_at_home
from ..views.utils import get_player_from_request


def battle_start_api(request, player_id):
    if request.method == "GET":
        return battle_start_get_api(request, player_id)
    elif request.method == "POST":
        return battle_start_post_api(request, player_id)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)


def battle_start_get_api(request, player_id):
    player = get_player_from_request(request, player_id)
    if not player:
        return JsonResponse({"error": "Player not found"}, status=404)

    exp_percent, continue_count = battle_start_get(request, player_id)
    player.refresh_from_db()
    return JsonResponse({
        **player_to_api_dict(player),
        "exp_percent": exp_percent,
        "continue_count": continue_count,
        "is_guest": player.is_guest,
    })


def battle_start_post_api(request, player_id):
    player = get_player_from_request(request, player_id)
    if not player:
        return JsonResponse({"error": "Player not found"}, status=404)

    action = request.POST.get('action')
    if action == 'rest':
        actual_exp_penalty = rest_at_home(player)
        exp_percent, continue_count = battle_start_get(request, player_id)
        player.refresh_from_db()
        return JsonResponse({
            **player_to_api_dict(player),
            "exp_percent": exp_percent,
            "continue_count": continue_count,
            "actual_exp_penalty": actual_exp_penalty,
            "is_guest": player.is_guest,
        })

    stat = request.POST.get('stat')
    if stat and player.stat_points > 0:
        allocate_stat_points(player, stat)
        exp_percent, continue_count = battle_start_get(request, player_id)
        player.refresh_from_db()
        return JsonResponse({
            **player_to_api_dict(player),
            "exp_percent": exp_percent,
            "continue_count": continue_count,
            "stat": stat,
            "is_guest": player.is_guest,
        })
    return JsonResponse({"error": "Invalid action"}, status=400)

