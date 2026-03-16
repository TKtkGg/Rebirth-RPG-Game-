from django.urls import path
from . import api_views

urlpatterns = [
    path('session/', api_views.session_view, name='auth-session'),
]