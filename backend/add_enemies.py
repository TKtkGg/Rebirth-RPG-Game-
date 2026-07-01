#!/usr/bin/env python
import os
import sys
import django

# Django設定を読み込み
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from game.models import Enemy

# エネミーデータを追加
enemies_data = [
    {"name": "スライム", "max_hp": 30, "hp": 30, "atk": 5, "defense": 2, "exp": 50},
    {"name": "ゴブリン", "max_hp": 50, "hp": 50, "atk": 8, "defense": 3, "exp": 80},
    {"name": "オーク", "max_hp": 80, "hp": 80, "atk": 12, "defense": 5, "exp": 120},
    {"name": "スケルトン", "max_hp": 60, "hp": 60, "atk": 10, "defense": 4, "exp": 100},
    {"name": "ドラゴン", "max_hp": 200, "hp": 200, "atk": 25, "defense": 10, "exp": 500},
    {"name": "魔法使いゴブリン", "max_hp": 40, "hp": 40, "atk": 15, "defense": 2, "exp": 150},
    {"name": "騎士の亡霊", "max_hp": 120, "hp": 120, "atk": 18, "defense": 8, "exp": 200},
    {"name": "盗賊", "max_hp": 45, "hp": 45, "atk": 12, "defense": 3, "exp": 90},
]

print("エネミーデータを追加中...")

for enemy_data in enemies_data:
    enemy, created = Enemy.objects.get_or_create(
        name=enemy_data["name"],
        defaults=enemy_data
    )
    if created:
        print(f"✅ {enemy.name} を追加しました")
    else:
        print(f"⚠️ {enemy.name} は既に存在します")

print(f"\n🎮 合計 {Enemy.objects.count()} 体のエネミーがデータベースに登録されています")
print("エネミーデータの追加が完了しました！")
