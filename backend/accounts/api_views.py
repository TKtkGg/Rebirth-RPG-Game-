from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from .forms import SignupForm
from django.views.decorators.csrf import ensure_csrf_cookie
from django.middleware.csrf import get_token
from game.models import Player

def session_view(request):
    is_authenticated = request.user.is_authenticated
    user = request.user if is_authenticated else None
    if is_authenticated:
        try:
            player_id = request.user.player.id
        except Player.DoesNotExist:
            player_id = None
    else:
        player_id = None

    return JsonResponse({
        "is_authenticated": is_authenticated,
        "user": user and {
            "id": user.id,
            "username": user.username,
        } or None,
        "player_id": player_id,
    })

def login_view(request):
    if request.method != 'POST':
        return JsonResponse({
            "error": "Method not allowed"
        }, status=405)
    
    username = request.POST.get('username')
    password = request.POST.get('password')
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return JsonResponse({
            "ok": True
        })
    else:
        return JsonResponse({
            "ok": False,
            "error": "Invalid username or password"
        }, status=401)

def logout_view(request):
    if request.method != 'POST':
        return JsonResponse({
            "error": "Method not allowed"
        }, status=405)

    logout(request)
    return JsonResponse({
        "ok": True
    })

def signup_view(request):
    if request.method != 'POST':
        return JsonResponse({
            "error": "Method not allowed"
        }, status=405)

    form = SignupForm(request.POST)
    if form.is_valid():
        user = form.save()
        login(request, user)
        return JsonResponse({
            "ok": True,
            "user": {
                "id": user.id,
                "username": user.username,
            }
        })
    else:
        return JsonResponse({
            "ok": False,
            "errors": form.errors
        }, status=400)

def guest_login_view(request):
    if request.method != 'POST':
        return JsonResponse({
            "ok": False,
            "error": "Method not allowed"
        }, status=405)
    
    if request.user.is_authenticated:
        logout(request)

    return JsonResponse({
        "ok": True
    })

@ensure_csrf_cookie
def csrf_view(request):
    return JsonResponse({
        "csrf_token": get_token(request)
    })
