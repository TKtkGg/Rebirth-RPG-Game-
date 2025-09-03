from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),          # トップページ
    path('start/', views.start_game, name='start_game'),  # ゲーム開始ページなど
    path('battle/<int:player_id>/<int:enemy_id>/start/',views.battle_start,name='battle_start'),
    path('battle/<int:player_id>/<int:enemy_id>/',views.battle,name='battle'),
    path('battle/<int:player_id>/',views.battle_start,name='battle_start_redirect'),  # enemy_idなしの場合
]