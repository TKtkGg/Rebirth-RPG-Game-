from django.http import JsonResponse
from game.views.gameflow import process_gameover


def gameover_api(request):
    if request.method != "GET":
        return JsonResponse({"error": "GET required"}, status=405)

    data = process_gameover(request)
    return JsonResponse({
        "score": data["score"],
        "initial_point": data["initial_point"],
        "is_guest": data["is_guest"],
    })
