from django.urls import path
from . import views

app_name = 'game'  # 名前空間を追加

urlpatterns = [
    path('', views.home, name='home'),          # トップページ
    path('start/', views.start_game, name='start'),  # ゲーム開始ページ（名前をstartに変更）
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
    path('use_inventory_item/<int:player_id>/<int:inventory_item_id>/', views.use_inventory_item, name='use_inventory_item'),  # インベントリーからアイテム使用
    path('quest/<int:player_id>/', views.quest, name='quest'),  # クエスト画面
    path('quest/claim/<int:quest_id>/', views.claim_quest_reward, name='claim_quest_reward'),  # クエスト報酬受け取り
    path('action_click/<int:player_id>/<int:enemy_id>/', views.action_skill_click, name='action_skill_click'),  # アクション特技クリック
    path('action_end/<int:player_id>/<int:enemy_id>/', views.action_skill_end, name='action_skill_end'),  # アクション特技終了
    path('continue_battle/<int:player_id>/', views.continue_battle, name='continue_battle'),  # 続けて戦う
    path('convert_guest/<int:player_id>/', views.convert_guest_to_user, name='convert_guest_to_user'),  # ゲストからユーザーへ変換
    path('gameover/', views.gameover, name='gameover'),  # ゲームオーバー画面
    path('score_breakdown/', views.score_breakdown, name='score_breakdown'),  # スコア内訳画面
]