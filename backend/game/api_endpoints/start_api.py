from django.contrib.auth import logout
from django.http import JsonResponse

from ..views.gameflow import build_job_slots
from ..views.utils import create_player_from_start


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

