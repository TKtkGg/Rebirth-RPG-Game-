from django.http import JsonResponse

def health(request):
    print("health check")
    return JsonResponse({"status": "ok"})