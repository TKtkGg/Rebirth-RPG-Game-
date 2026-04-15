from . models import Player, Stage
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth import logout
from .views.gameflow import build_job_slots
from .views.utils import create_player_from_start, get_player_from_request
from .views.battle import battle_start_get, rest_at_home, allocate_stat_points
from .views.shop import shop, buy_item

def player_to_api_dict(player):
    return {
        "id": player.id,
        "name": player.name,
        "level": player.level,
        "exp": player.exp,
        "next_exp": player.next_exp,
        "max_hp": player.max_hp,
        "hp": player.hp,
        "atk": player.atk,
        "defense": player.defense,
        "spd": player.spd,
        "max_mp": player.max_mp,
        "mp": player.mp,
        "stat_points": player.stat_points,
        "job": player.job,
        "item": player.item,
        "weapon": player.weapon.name,
        "armor": player.armor.name,
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
    }

def equipment_to_api_dict(equipment):
    return {
        "id": equipment.id,
        "name": equipment.name,
        "equipment_type": equipment.equipment_type,
        "price": equipment.price,
        "description": equipment.description,
        "atk_bonus": equipment.atk_bonus,
        "def_bonus": equipment.def_bonus,
        "hp_bonus": equipment.hp_bonus,
        "spd_bonus": equipment.spd_bonus,
    }

def item_to_api_dict(item):
    return {
        "id": item.id,
        "name": item.name,
        "target": item.target,
        "effect_amount": item.effect_amount,
        "price": item.price,
        "description": item.description,
        "current_stock": item.current_stock,
        "max_stock": item.max_stock,
    }


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

def start_api(request):
    if request.method == "GET":
        return start_get(request)
    elif request.method == "POST":
        return start_post(request)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)

def start_get(request):
    force_guest = request.GET.get('guest') == "1"
    user_real = request.user.is_authenticated and not force_guest
    if force_guest and request.user.is_authenticated:
        logout(request)
    
    default_name = request.user.username if user_real else ""

    default_jobs = ["戦士", "魔法使い", "忍者", "格闘家", "侍"]
    unlocked_jobs = (request.user.unlocked_jobs or []) if user_real else []
    available_jobs = list(dict.fromkeys(default_jobs + unlocked_jobs))

    job_slots = build_job_slots(request.user, available_jobs)

    return JsonResponse({
        "default_name": default_name,
        "job_slots": job_slots,
    })

def start_post(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    default_jobs = ["戦士", "魔法使い", "忍者", "格闘家", "侍"]
    unlocked_jobs = (request.user.unlocked_jobs or []) if request.user.is_authenticated else []
    available_jobs = list(dict.fromkeys(default_jobs + unlocked_jobs))

    player = create_player_from_start(request, available_jobs, False)

    return JsonResponse({
        "ok": True,
        "player_id": player.id,
    })

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