from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),          # トップページ
    path('start/', views.start_game, name='start_game'),  # ゲーム開始ページなど
    path('stage_select/<int:player_id>/', views.stage_select, name='stage_select'),  # ステージ選択
    path('battle/<int:player_id>/home/', views.battle_start, name='battle_start'),  # ホーム画面
    path('battle/<int:player_id>/<int:enemy_id>/start/',views.battle_start,name='battle_start_old'),  # 旧URL（互換性）
    path('battle/<int:player_id>/<int:enemy_id>/',views.battle,name='battle'),
    path('battle/<int:player_id>/',views.battle,name='battle_start_redirect'),  # 戦闘開始
    path('shop/<int:player_id>/',views.shop,name='shop'),  # ショップページ
    path('buy_item/<int:player_id>/', views.buy_item, name='buy_item'),  # アイテム購入
    path('equipment/<int:player_id>/', views.equipment_change, name='equipment_change'),  # 装備変更
    path('equip/<int:player_id>/<int:equipment_id>/', views.equip_item, name='equip_item'),  # 装備実行
    path('inventory/<int:player_id>/', views.inventory, name='inventory'),  # 持ち物画面
]