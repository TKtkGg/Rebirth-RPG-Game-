from django.http import JsonResponse
from game.views.score import allocate_score_point, get_score_points_screen_data


def score_points_api(request):
    if request.method == "GET":
        category = request.GET.get("category", "all")
        data = get_score_points_screen_data(request, category_key=category)
        if data is None:
            return JsonResponse({"error": "Authentication required", "redirect": "start"}, status=401)
        return JsonResponse(data)

    if request.method == "POST":
        category = request.POST.get("category", "all")
        stat = request.POST.get("stat")
        data = allocate_score_point(request, stat, category)
        if data is None:
            return JsonResponse({"error": "Authentication required", "redirect": "start"}, status=401)
        return JsonResponse(data)

    return JsonResponse({"error": "Method not allowed"}, status=405)
