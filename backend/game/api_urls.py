from django.urls import path
from . import api_views

urlpatterns = [
    path('players/<int:player_id>/', api_views.player_detail, name='player_detail'),
    path('stages/<int:stage_id>/', api_views.stage_detail, name='stage_detail'),
    path('stages/', api_views.stage_list, name='stage_list'),
    path('start/', api_views.start_api, name='start_api'),
    path('battle_start/<int:player_id>/', api_views.battle_start_api, name='battle_start_api'),
]