from django.http import JsonResponse

from game.views.utils import get_player_from_request
from game.views.quest import quest, claim_quest_reward
from game.api_serializers import player_to_api_dict
from game.models import PlayerQuest

def quest_to_api_dict(quest_data):
    if quest_data is None:
        return None

    return {
        'id': quest_data.id,
        'quest_template': {
            'quest_type': quest_data.quest_template.quest_type,
            'title': quest_data.quest_template.title,
            'description': quest_data.quest_template.description,
            'condition_type': quest_data.quest_template.condition_type,
            'condition_target': quest_data.quest_template.condition_target,
            'progress_max': quest_data.quest_template.progress_max,
            'reward_exp': quest_data.quest_template.reward_exp,
            'reward_gold': quest_data.quest_template.reward_gold,
        },
        'progress_current': quest_data.progress_current,
        "is_claimed": quest_data.is_claimed,
        "is_completed": quest_data.is_completed,
    }

def quest_api(request, player_id):
    if request.method == "GET":
        return quest_get_api(request, player_id)
    elif request.method == "POST":
        return quest_post_api(request, player_id)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)


def quest_get_api(request, player_id):
    player = get_player_from_request(request, player_id)
    if not player:
        return JsonResponse({"error": "Player not found"}, status=404)

    quest_data = quest(request, player_id)

    return JsonResponse({
        'player': player_to_api_dict(quest_data['player']),
        'life_quests': [quest_to_api_dict(quest) for quest in quest_data['life_quests']],
        'account_quests': [quest_to_api_dict(quest) for quest in quest_data['account_quests']],
        'is_guest': player.is_guest,
    })

def quest_post_api(request, player_id):
    player = get_player_from_request(request, player_id)
    if not player:
        return JsonResponse({"error": "Player not found"}, status=404)

    quest_id = request.POST.get('quest_id')
    if not quest_id:
        return JsonResponse({"error": "Quest ID is required"}, status=400)

    try:
        player_quest = PlayerQuest.objects.get(id=quest_id, player=player)
    except PlayerQuest.DoesNotExist:
        return JsonResponse({"error": "Quest not found"}, status=404)

    try:
        claim_quest_reward(request, player_quest.id)
    except Exception:
        return JsonResponse({"error": "Failed to claim quest reward"}, status=500)

    quest_data = quest(request, player_id)
    return JsonResponse({
        "ok": True,
        'player': player_to_api_dict(quest_data['player']),
        'life_quests': [quest_to_api_dict(quest) for quest in quest_data['life_quests']],
        'account_quests': [quest_to_api_dict(quest) for quest in quest_data['account_quests']],
        'is_guest': player.is_guest,
    })
