from json import JSONDecodeError
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from .forms import SignupForm

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
