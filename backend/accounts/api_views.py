from django.http import JsonResponse

def session_view(request):
    is_authenticated = request.user.is_authenticated
    user = request.user if is_authenticated else None
    return JsonResponse({
        "is_authenticated": is_authenticated,
        "user": user and {
            "id": user.id,
            "username": user.username,
        } or None,
    })