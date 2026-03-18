from django.urls import path
from . import api_views

urlpatterns = [
    path('session/', api_views.session_view, name='auth-session'),
    path('login/', api_views.login_view, name='auth-login'),
    path('logout/', api_views.logout_view, name='auth-logout'),
    path('signup/', api_views.signup_view, name='auth-signup'),
    path('csrf/', api_views.csrf_view, name='auth-csrf'),
]