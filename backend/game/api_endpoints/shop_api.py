from django.http import JsonResponse

from ..api_serializers import (
    equipment_to_api_dict,
    item_to_api_dict,
    player_to_api_dict,
)
from ..views.shop import buy_item, shop


def shop_api(request, player_id):
    if request.method == "GET":
        return shop_get_api(request, player_id)
    elif request.method == "POST":
        return shop_post_api(request, player_id)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)


def build_shop_data(request, player_id):
    shop_data = shop(request, player_id)
    return {
        "player": player_to_api_dict(shop_data['player']),
        "weapons": [equipment_to_api_dict(weapon) for weapon in shop_data['weapons']],
        "armors": [equipment_to_api_dict(armor) for armor in shop_data['armors']],
        "items": [item_to_api_dict(item) for item in shop_data['items']],
        "session_purchased": shop_data['session_purchased'],
    }


def shop_get_api(request, player_id):
    shop_data = build_shop_data(request, player_id)
    return JsonResponse(shop_data)


def shop_post_api(request, player_id):
    buy_item(request, player_id)
    shop_data = build_shop_data(request, player_id)
    return JsonResponse({
        "ok": True,
        **shop_data,
    })

