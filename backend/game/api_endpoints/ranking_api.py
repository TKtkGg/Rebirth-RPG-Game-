from django.http import JsonResponse
from game.views.utils import get_player_from_request
from game.views.score import ranking

def ranking_api(request, player_id):
    player = get_player_from_request(request, player_id)
    if not player:
        return JsonResponse({"error": "Player not found"}, status=404)

    ranking_data = ranking(request, player_id)
    return JsonResponse({
        "categories": ranking_data["categories"],
        "category": ranking_data["category"],
        "entries": ranking_data["entries"],
        "label": ranking_data["label"],
    })
