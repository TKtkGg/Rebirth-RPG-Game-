from . import views 
from django.urls import path, include

urlpatterns = [
    path("health/", views.health, name="health"),
    path("", include('game.api_urls')),
]