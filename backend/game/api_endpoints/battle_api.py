from django.http import JsonResponse
from ..views.utils import get_player_from_request
from ..views.battle import battle_action_finish, battle_action_hit, battle_get, battle_post

def battle_api(request, player_id):
    if request.method == "GET":
        return battle_get_api(request, player_id)
    elif request.method == "POST":
        return battle_post_api(request, player_id)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)

def battle_get_api(request, player_id):
    player = get_player_from_request(request, player_id)
    if not player:
        return JsonResponse({"error": "Player not found"}, status=404)
    
    return JsonResponse(battle_get(request, player_id), status=200)

def battle_post_api(request, player_id):
    player = get_player_from_request(request, player_id)
    if not player:
        return JsonResponse({"error": "Player not found"}, status=404)

    return JsonResponse(battle_post(request, player_id), status=200)


def battle_action_hit_api(request, player_id):
    player = get_player_from_request(request, player_id)
    if not player:
        return JsonResponse({"error": "Player not found"}, status=404)

    result = battle_action_hit(request, player_id)
    return JsonResponse(result, status=400 if "error" in result else 200)


def battle_action_finish_api(request, player_id):
    player = get_player_from_request(request, player_id)
    if not player:
        return JsonResponse({"error": "Player not found"}, status=404)

    result = battle_action_finish(request, player_id)
    return JsonResponse(result, status=400 if "error" in result else 200)