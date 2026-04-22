from django.urls import path
from .api_endpoints import (
    player_detail,
    stage_list,
    start_api,
    battle_start_api,
    shop_api,
    equipment_api,
    inventory_api,
    quest_api,
    ranking_api,
)

urlpatterns = [
    path('players/<int:player_id>/', player_detail, name='player_detail'),
    path('stages/<int:player_id>/', stage_list, name='stage_list'),
    path('start/', start_api, name='start_api'),
    path('battle_start/<int:player_id>/', battle_start_api, name='battle_start_api'),
    path('shop/<int:player_id>/', shop_api, name='shop_api'),
    path('equipment/<int:player_id>/', equipment_api, name='equipment_api'),
    path('inventory/<int:player_id>/', inventory_api, name='inventory_api'),
    path('quest/<int:player_id>/', quest_api, name='quest_api'),
    path('ranking/<int:player_id>/', ranking_api, name='ranking_api'),
]