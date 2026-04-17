from django.http import JsonResponse
from ..models import Equipment

from ..views.equipment import equipment_change
from ..views.utils import get_player_from_request
from ..api_serializers import player_to_api_dict, equipment_to_api_dict

def equipment_api(request, player_id):
    if request.method == "GET":
        return equipment_get_api(request, player_id)
    elif request.method == "POST":
        return equipment_post_api(request, player_id)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)

def equipment_get_api(request, player_id):
    player = get_player_from_request(request, player_id)
    if not player:
        return JsonResponse({"error": "Player not found"}, status=404)

    equipment_data = equipment_change(request, player_id)
    return JsonResponse({
        "player": player_to_api_dict(equipment_data['player']),
        "owned_weapons": [equipment_to_api_dict(weapon) for weapon in equipment_data['owned_weapons']],
        "owned_armors": [equipment_to_api_dict(armor) for armor in equipment_data['owned_armors']],
    })

def equipment_post_api(request, player_id):
    equipment_id = request.POST.get('equipment_id')
    if not equipment_id:
        return JsonResponse({"error": "Equipment ID is required"}, status=400)

    player = get_player_from_request(request, player_id)
    if not player:
        return JsonResponse({"error": "Player not found"}, status=404)
    try:
        equipment = Equipment.objects.get(id=equipment_id)
    except Equipment.DoesNotExist:
        return JsonResponse({"error": "Equipment not found"}, status=404)

    if equipment in player.owned_equipment.all():
        if equipment.equipment_type == 'weapon':
            player.change_weapon(equipment)
        elif equipment.equipment_type == 'armor':
            player.change_armor(equipment)
        else:
            return JsonResponse({"error": "Invalid equipment type"}, status=400)

    return JsonResponse({
        "player": player_to_api_dict(player),
        "owned_weapons": [equipment_to_api_dict(weapon) for weapon in player.owned_equipment.filter(equipment_type='weapon')],
        "owned_armors": [equipment_to_api_dict(armor) for armor in player.owned_equipment.filter(equipment_type='armor')],
    })