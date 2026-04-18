from django.http import JsonResponse

from ..models import Player, PlayerInventory
from ..api_serializers import player_to_api_dict, item_to_api_dict
from ..views.utils import get_player_from_request
from ..views.inventory import inventory, use_inventory_item

def player_inventory_to_api_dict(player_inventory):
    return {
        "id": player_inventory.id,
        "item": item_to_api_dict(player_inventory.item),
        "quantity": player_inventory.quantity,
    }

def inventory_api(request, player_id):
    if request.method == "GET":
        return inventory_get_api(request, player_id)
    elif request.method == "POST":
        return inventory_post_api(request, player_id)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)

def inventory_get_api(request, player_id):
    player = get_player_from_request(request, player_id)
    if not player:
        return JsonResponse({"error": "Player not found"}, status=404)
    
    inventory_data = inventory(request, player_id)

    return JsonResponse({
        "player": player_to_api_dict(player),
        "inventory_items": [player_inventory_to_api_dict(item) for item in inventory_data['inventory_items']],
        "selected_item": player_inventory_to_api_dict(inventory_data['selected_item']) if inventory_data['selected_item'] else None,
        "category": inventory_data['category'],
        "search_query": inventory_data['search_query'],
        "use_message": inventory_data['use_message'],
    })
    

def inventory_post_api(request, player_id):
    player = get_player_from_request(request, player_id)
    if not player:
        return JsonResponse({"error": "Player not found"}, status=404)

    inventory_item_id = request.POST.get('inventory_item_id')
    if not inventory_item_id:
        return JsonResponse({"error": "Inventory item ID is required"}, status=400)

    try:
        inventory_data = use_inventory_item(request, player_id, inventory_item_id)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({
        "category": inventory_data['category'],
        "search_query": inventory_data['search_query'],
    })