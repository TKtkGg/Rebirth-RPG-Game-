import os
import django

# Djangoの設定を読み込む
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from game.models import Stage, Enemy

# 既存のステージをクリア（オプション）
# Stage.objects.all().delete()

# ステージデータを作成
stages_data = [
    {
        'name': '草原',
        'unlock_level': 0,
        'background_image': 'ステージ_草原.jpg',
        'min_enemy_level': 1,
        'max_enemy_level': 10,
        'order': 1
    },
    {
        'name': '森林',
        'unlock_level': 10,
        'background_image': 'ステージ_森林.jpg',
        'min_enemy_level': 11,
        'max_enemy_level': 20,
        'order': 2
    },
    {
        'name': '海',
        'unlock_level': 20,
        'background_image': 'ステージ_海.jpg',
        'min_enemy_level': 21,
        'max_enemy_level': 30,
        'order': 3
    },
    {
        'name': '火山',
        'unlock_level': 30,
        'background_image': 'ステージ_火山.jpg',
        'min_enemy_level': 31,
        'max_enemy_level': 100,
        'order': 4
    },
]

# ステージを作成または更新
for stage_data in stages_data:
    stage, created = Stage.objects.get_or_create(
        name=stage_data['name'],
        defaults=stage_data
    )
    if created:
        print(f"ステージ「{stage.name}」を作成しました。")
    else:
        # 既存のステージを更新
        for key, value in stage_data.items():
            setattr(stage, key, value)
        stage.save()
        print(f"ステージ「{stage.name}」を更新しました。")

# 既存の敵を各ステージに割り当て
grass_stage = Stage.objects.get(name='草原')
forest_stage = Stage.objects.get(name='森林')
sea_stage = Stage.objects.get(name='海')
volcano_stage = Stage.objects.get(name='火山')

# 全ての敵を取得してレベルに応じて割り当て
all_enemies = Enemy.objects.all()
for enemy in all_enemies:
    # デフォルトレベルに基づいてステージに割り当て
    if enemy.level_default <= 10:
        enemy.stages.add(grass_stage)
    if 5 <= enemy.level_default <= 20:
        enemy.stages.add(forest_stage)
    if 15 <= enemy.level_default <= 30:
        enemy.stages.add(sea_stage)
    if enemy.level_default >= 25:
        enemy.stages.add(volcano_stage)

print("\n初期ステージデータの追加が完了しました。")
print(f"草原: レベル1-10 (開放レベル: なし)")
print(f"森林: レベル11-20 (開放レベル: 10)")
print(f"海: レベル21-30 (開放レベル: 20)")
print(f"火山: レベル31以上 (開放レベル: 30)")
