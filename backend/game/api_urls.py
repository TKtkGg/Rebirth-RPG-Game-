from django.urls import path
from . import api_views

urlpatterns = [
    path('players/<int:player_id>/', api_views.player_detail, name='player_detail'),
    path('stages/<int:stage_id>/', api_views.stage_detail, name='stage_detail'),

]