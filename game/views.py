import random
from django.shortcuts import render,redirect
from .models import Player, PlayerProfile,Enemy


def home(request):
    return render(request, 'game/home.html')


def start_game(request):
    if request.method == 'POST':
        name = request.POST.get('name')

        profile = PlayerProfile.objects.create(name=name)
        player = Player.objects.create(profile=profile, hp=100, max_hp=100, job="戦士", item="なし")

        return redirect('battle_start_redirect',player_id=player.id)
    return render(request, 'game/start.html')

def battle_start(request, player_id, enemy_id=None):
    player = Player.objects.get(id=player_id)
    if player.hp <= 0:
        player.hp = player.max_hp
        player.save()

    # プレイヤーのレベル±10の範囲で敵を選択
    min_level = max(1, player.level - 10)
    max_level = player.level + 10
    enemies = Enemy.objects.filter(level__gte=min_level, level__lte=max_level)

    # 敵が存在しない場合のフォールバック
    if not enemies.exists():
        enemies = Enemy.objects.all()

    # レベル差に応じて出現確率を調整
    weighted_enemies = []
    for enemy in enemies:
        level_diff = abs(player.level - enemy.level)
        weight = max(1, 20 - level_diff)  # レベル差が大きいほど重みが小さくなる
        weighted_enemies.extend([enemy] * weight)

    # ランダムに敵を選択
    enemy = random.choice(weighted_enemies)

    # 敵のHPを常に最大値にリセット
    enemy.hp = enemy.max_hp
    enemy.is_defeated = False
    enemy.save()

    # セッションに敵のIDを保存
    request.session["enemy_id"] = enemy.id

    exp_percent = int(player.exp / player.next_exp * 100)

    continue_count = 2 - player.defeats

    if request.method == 'POST':
        # 休む機能の処理
        action = request.POST.get('action')
        if action == 'rest':
            player.hp = player.max_hp
            player.save()
            return redirect('battle_start_redirect', player_id=player.id)

        # ステータスポイント配分の処理
        stat = request.POST.get('stat')
        if stat and player.stat_points > 0:
            if stat == 'atk':
                player.atk += 1
            elif stat == 'defense':
                player.defense += 1
            elif stat == 'hp':
                player.max_hp += 10
                player.hp += 10
            player.stat_points -= 1
            player.save()
            return redirect('battle_start_redirect', player_id=player.id)

    return render(request, 'game/battle_start.html', {"player": player, "enemy": enemy, "exp_percent": exp_percent, "continue_count": continue_count,})

def battle(request,player_id,enemy_id):
    player=Player.objects.get(id=player_id)
    enemy_id = request.session.get("enemy_id")
    enemy = Enemy.objects.get(id=enemy_id)
    message = ""

    if request.method == 'POST':
        base_damage = (player.atk - enemy.defense // 3)
        damage = max(random.randint(base_damage - 1, base_damage + 2),1)
        enemy.hp -= damage
        enemy.save()
        message = f"{player.profile.name}の攻撃！ {enemy.name}に{damage}ダメージ！"

        if enemy.hp <= 0:
            gained_exp = enemy.exp
            player.exp += gained_exp
            message += f"\n{enemy.name}を倒した！"
            message += f"\n経験値を{gained_exp}ゲットした！"
            enemy.hp = 0
            enemy.defeated = True
            enemy.save()

            while player.exp >= player.next_exp:
                player.level += 1
                player.stat_points += 3
                player.exp -= player.next_exp
                player.next_exp = int(500 + player.level * 20 * player.level)
                message += f"\nレベルアップ！ レベル{player.level}になった！ ステータスポイント+3"

            player.save()
            return render(request, "game/battle.html", {
                "player": player,
                "enemy": None,
                "message": message,
            })


        enemy_damage_base = max(1,enemy.atk - player.defense // 3)
        enemy_damage = max(random.randint(enemy_damage_base - 1, enemy_damage_base + 2),1)
        player.hp -= enemy_damage
        message += f"{enemy.name} の攻撃！ {player.profile.name} は {enemy_damage} のダメージを受けた！\n"

        if player.hp <= 0:
            player.defeats += 1
            if player.defeats >= 3:
                message += f"\n{player.profile.name} は力尽きた… ゲームオーバー！"
                # 完全リセット
                player.defeats = 0
                player.level = 1
                player.exp = 0
                player.next_exp = 500
                player.max_hp = 100
                player.hp = 100
                player.atk = 10
                player.defense = 5
                player.stat_points = 0
                player.job = "戦士"
                player.item = "なし"
                player.save()
                return render(request, "game/gameover.html", {"player": player, "message": message})
            else:
                message += f"{player.profile.name} は倒れてしまった… 休んで回復しよう\n"
                player.save()
                return render(request, "game/battle.html", {
                    "player": player,
                    "enemy": enemy,
                    "message": message,
                    "redirect_after": True,  # ← これでテンプレートに伝える
                    "redirect_url": "battle_start",
                    "recovering":True,
                })

        player.save()
        enemy.save()

        return render(request, "game/battle.html", {
            "player": player,
            "enemy": enemy,
            "message": message,
        })
    
    return render(request, "game/battle.html", {
        "player": player,
        "enemy": enemy,
        "message": message,
    })
