from django.http import JsonResponse
from game.views.score import get_score_breakdown


def score_breakdown_api(request):
    if request.method != "GET":
        return JsonResponse({"error": "GET required"}, status=405)

    data = get_score_breakdown(request)
    if data is None:
        return JsonResponse({"error": "No score breakdown", "redirect": "gameover"}, status=404)

    return JsonResponse({"breakdown": data})
