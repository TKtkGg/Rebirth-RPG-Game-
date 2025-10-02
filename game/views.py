import random
from django.shortcuts import render,redirect
from .models import Player, PlayerProfile,Enemy


def home(request):
    return render(request, 'game/home.html')


def start_game(request):
    if request.method == 'POST':
        name = request.POST.get('name')

        profile = PlayerProfile.objects.create(name=name)
        player = Player.objects.create(profile=profile, hp=100, max_hp=100, mp=30, max_mp=30, job="戦士", item="なし")

        return redirect('battle_start_redirect',player_id=player.id)
    return render(request, 'game/start.html')

def battle_start(request, player_id, enemy_id=None):
    player = Player.objects.get(id=player_id)
    if player.hp <= 0:
        player.hp = player.max_hp
        player.save()

    # 敵のレベル範囲を設定
    if player.level <= 5:
        min_level = max(1, player.level - 1)
        max_level = player.level + 1
    elif player.level <= 10:
        min_level = max(1, player.level - 3)
        max_level = player.level + 3
    else:
        min_level = max(1, player.level - 10)
        max_level = player.level + 5

    enemies = Enemy.objects.filter(level__gte=min_level, level__lte=max_level)

    # 敵が存在しない場合のフォールバック
    if not enemies.exists():
        enemies = Enemy.objects.all()

    # レベル差に応じて出現確率を調整
    weighted_enemies = []
    for enemy in enemies:
        if player.level <= 5:
            weight = 10  # 同じレベルまたは±1の敵は均等に出現
        elif player.level <= 10:
            level_diff = abs(player.level - enemy.level)
            weight = max(1, 10 - level_diff * 2)  # レベル差が大きいほど重みが小さくなる
        else:
            level_diff = abs(player.level - enemy.level)
            weight = max(1, 20 - level_diff)  # レベル差が大きいほど重みが小さくなる
        weighted_enemies.extend([enemy] * weight)

    # ランダムに敵を選択
    enemy = random.choice(weighted_enemies)

    # 敵のレベルをランダムに変更（範囲内で）
    if max(min_level, enemy.level, enemy.level_default) > max_level:
        enemy.level = max_level  # 範囲が無効な場合は最大値を設定
    else:
        enemy.level = random.randint(max(min_level, enemy.level_default), max_level)

    # レベルに応じてステータスを変更
    enemy.max_hp = enemy.max_hp_default + (enemy.level - enemy.level_default) * enemy.max_hp // 10
    enemy.hp = enemy.max_hp
    enemy.atk = enemy.atk_default + (enemy.level - enemy.level_default) * enemy.atk // 5
    enemy.defense = enemy.defense_default + (enemy.level - enemy.level_default) * enemy.defense // 5
    enemy.spd = enemy.spd_default + (enemy.level - enemy.level_default) * enemy.spd // 5
    enemy.exp = enemy.exp_default + (enemy.level - enemy.level_default) * enemy.exp // 10
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
            player.mp = player.max_mp
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
            elif stat == 'spd':
                player.spd += 1
            elif stat == 'mp':
                player.max_mp += 5
                player.mp += 5
            player.stat_points -= 1
            player.save()
            return redirect('battle_start_redirect', player_id=player.id)

    return render(request, 'game/battle_start.html', {"player": player, "enemy": enemy, "exp_percent": exp_percent, "continue_count": continue_count,})

def battle(request,player_id,enemy_id):
    player=Player.objects.get(id=player_id)
    enemy_id = request.session.get("enemy_id")
    enemy = Enemy.objects.get(id=enemy_id)
    message = ""
    buffs = request.session.get("buffs", {})
    bufatk = int(player.atk * buffs.get("atk_up", {}).get("multiplier", 1.0))
    bufdef = int(player.defense * buffs.get("def_up", {}).get("multiplier", 1.0))
    debuffs = request.session.get("debuffs", {})
    debufatk = int(enemy.atk * debuffs.get("atk_down", {}).get("multiplier", 1.0))
    debufdef = int(enemy.defense * debuffs.get("def_down", {}).get("multiplier", 1.0))
    def game_over(message):
        message += f"{player.profile.name} は力尽きた… ゲームオーバー！\n"
        player.defeats = 0
        player.level = 1
        player.exp = 0
        player.next_exp = 500
        player.max_hp = 100
        player.hp = 100
        player.atk = 10
        player.defense = 5
        player.spd = 5
        player.max_mp = 30
        player.mp = 30
        player.stat_points = 0
        player.job = "戦士"
        player.item = "なし"
        request.session["buffs"] = {}
        request.session["debuffs"] = {}
        player.save()

        # 敵のステータスをデフォルトに戻す
        enemies = Enemy.objects.all()
        for enemy in enemies:
            enemy.hp = enemy.max_hp
            enemy.level = enemy.level_default
            enemy.atk = enemy.atk_default  # デフォルト値に戻す
            enemy.defense = enemy.defense_default  # デフォルト値に戻す
            enemy.is_defeated = False
            enemy.save()

        return message


    def tohome(message):
        message += f"{player.profile.name} は倒れてしまった… 休んで回復しよう\n"
        request.session["buffs"] = {}
        request.session["debuffs"] = {}
        player.save()
        return message
    
    def win(message):
        gained_exp = enemy.exp
        player.exp += gained_exp
        message += f"{enemy.name}を倒した！\n"
        message += f"経験値を{gained_exp}ゲットした！\n"
        enemy.hp = 0
        enemy.is_defeated = True
        enemy.save()

        while player.exp >= player.next_exp:
            player.level += 1
            player.stat_points += 3
            player.exp -= player.next_exp
            player.next_exp = int(500 + player.level * 20 * player.level)
            message += f"レベルアップ！ レベル{player.level}になった！ ステータスポイント+3\n"

        request.session["buffs"] = {}
        request.session["debuffs"] = {}
        player.save()
        return message
    
    def playerAction(message,action,special):
        if action == 'attack':
            atk = int(player.atk * buffs.get("atk_up", {}).get("multiplier", 1.0))
            base_damage = int(atk - (enemy.defense * debuffs.get("def_down", {}).get("multiplier", 1.0)) // 3)
            damage = max(random.randint(base_damage - 1, base_damage + 2),1)
            enemy.hp -= damage
            enemy.save()
            message = f"{player.profile.name}の攻撃！ {enemy.name}に{damage}ダメージ！\n"
        
        elif special:
            required_mp = 0
            if special == 'skill1':
                special = "渾身斬り"
                required_mp = 12
            elif special == 'skill2':
                special = "身体強化"
                required_mp = 10
            elif special == 'skill3':
                special = "気迫"
                required_mp = 10

            if player.mp < required_mp:
                message = f"SPが足りません！ {special} を発動するには SPが{required_mp}必要です。"
                return message,False

            if special == '渾身斬り':
                # 得意技1: 敵に大ダメージを与える
                atk = int(player.atk * buffs.get("atk_up", {}).get("multiplier", 1.0))
                base_damage = int(atk * 2 - (enemy.defense * debuffs.get("def_down", {}).get("multiplier", 1.0)))
                damage = max(random.randint(base_damage, base_damage + 3), 1)
                enemy.hp -= damage
                player.mp -= 12
                message = f"{player.profile.name}の渾身斬り！ {enemy.name}に{damage}の大ダメージ！\nSPが12減った！\n"
                enemy.save()

            elif special == '身体強化':
                # 得意技2: プレイヤーにバフを付与
                if "atk_up" not in buffs:  # 重ねがけ防止
                    buffs["atk_up"] = {"turns": 4, "multiplier": 1.5}
                else:
                    buffs["atk_up"]["turns"] = 4  # ターン数をリセット

                # 防御力アップ
                if "def_up" not in buffs:
                    buffs["def_up"] = {"turns": 4, "multiplier": 1.5}
                else:
                    buffs["def_up"]["turns"] = 4  # ターン数をリセット

                request.session["buffs"] = buffs
                player.mp -= 10
                message = f"{player.profile.name}の身体強化！ 攻撃力と防御力が上昇した！\nSPが10減った！\n"
                player.save()

            elif special == '気迫':
                # 得意技3: 敵を弱体化
                if "atk_down" not in debuffs:  # 重ねがけ防止
                    debuffs["atk_down"] = {"turns": 4, "multiplier": 0.6}
                else:
                    debuffs["atk_down"]["turns"] = 4  # ターン数をリセット

                if "def_down" not in debuffs:
                    debuffs["def_down"] = {"turns": 4, "multiplier": 0.6}
                else:
                    debuffs["def_down"]["turns"] = 4  # ターン数をリセット

                request.session["debuffs"] = debuffs
                player.mp -= 10
                message = f"{player.profile.name}の気迫！ {enemy.name}の攻撃力と防御力が弱体化した！\nSPが10減った！\n"
                player.save()
        return message,True
    
    def enemyAction(message,action):
        if action == 'defend':
            defense = int(player.defense * buffs.get("def_up", {}).get("multiplier", 1.0))
            base_damage = int(enemy.atk * debuffs.get("atk_down", {}).get("multiplier", 1.0) - defense)
            damage = max(random.randint(base_damage - 2, base_damage + 1), 1)
            player.hp -= damage
            player.mp += random.randint(player.max_mp // 20 , player.max_mp // 10) if player.mp < player.max_mp else 0
            message = f"{enemy.name} の攻撃！\n{player.profile.name} は防御した！ {damage}ダメージ！\n" + (f"防御によってSPが少し回復した！\n" if player.mp < player.max_mp else "")
        else:
            defense = int(player.defense * buffs.get("def_up", {}).get("multiplier", 1.0))
            enemy_damage_base = int(enemy.atk * debuffs.get("atk_down", {}).get("multiplier", 1.0) - defense // 3)
            enemy_damage = max(random.randint(enemy_damage_base - 1, enemy_damage_base + 2),1)
            player.hp -= enemy_damage
            message = f"{enemy.name} の攻撃！ {player.profile.name} は {enemy_damage} のダメージを受けた！\n"
        return message

    if request.method == 'POST':
        
        action = request.POST.get('action')
        special = request.POST.get('special')

        if player.spd >= enemy.spd:
            message,success = playerAction(message,action,special)
            if not success:
                return render(request, "game/battle.html", {
                    "player": player,
                    "enemy": enemy,
                    "message": message,
                    "bufatk": bufatk,
                    "bufdef": bufdef,
                    "buffs": buffs,
                    "debufatk": debufatk,
                    "debufdef": debufdef,
                    "debuffs": debuffs,
                })
            if enemy.hp <= 0:
                message = win(message)
                return render(request, "game/battle.html", {
                    "player": player,
                    "enemy": None,
                    "message": message,
                    "bufatk": bufatk,
                    "bufdef": bufdef,
                    "buffs": buffs,
                    "debufatk": debufatk,
                    "debufdef": debufdef,
                    "debuffs": debuffs,
                })
            
            message += enemyAction(message,action)    
            if player.hp <= 0:
                player.defeats += 1
                if player.defeats >= 3:
                    message = game_over(message)
                    return render(request, "game/gameover.html", {"player": player, "message": message})
                else:
                    message = tohome(message)
                    return render(request, "game/battle.html", {
                        "player": player,
                        "enemy": enemy,
                        "message": message,
                        "bufatk": bufatk,
                        "bufdef": bufdef,
                        "buffs": buffs,
                        "debufatk": debufatk,
                        "debufdef": debufdef,
                        "debuffs": debuffs,
                        "redirect_after": True,  # ← これでテンプレートに伝える
                        "redirect_url": "battle_start",
                        "recovering": True,
                    })          
        else:
            message = enemyAction(message,action)
            if player.hp <= 0:
                player.defeats += 1
                if player.defeats >= 3:
                    message = game_over(message)
                    return render(request, "game/gameover.html", {"player": player, "message": message})
                else:
                    message = tohome(message)
                    return render(request, "game/battle.html", {
                        "player": player,
                        "enemy": enemy,
                        "message": message,
                        "bufatk": bufatk,
                        "bufdef": bufdef,
                        "buffs": buffs,
                        "debufatk": debufatk,
                        "debufdef": debufdef,
                        "debuffs": debuffs,
                        "redirect_after": True,  # ← これでテンプレートに伝える
                        "redirect_url": "battle_start",
                        "recovering": True,
                    })
            
            extra_message,success = playerAction(message,action,special)
            message += extra_message
            if not success:
                return render(request, "game/battle.html", {
                    "player": player,
                    "enemy": enemy,
                    "message": message,
                    "bufatk": bufatk,
                    "bufdef": bufdef,
                    "buffs": buffs,
                    "debufatk": debufatk,
                    "debufdef": debufdef,
                    "debuffs": debuffs,
                })
            if enemy.hp <= 0:
                message = win(message)
                return render(request, "game/battle.html", {
                    "player": player,
                    "enemy": None,
                    "message": message,
                    "bufatk": bufatk,
                    "bufdef": bufdef,
                    "buffs": buffs,
                    "debufatk": debufatk,
                    "debufdef": debufdef,
                    "debuffs": debuffs,
                })
          

        # ターン経過でバフを減少
        for key in list(buffs.keys()):
            buffs[key]["turns"] -= 1
            if buffs[key]["turns"] <= 0:
                del buffs[key]

        request.session["buffs"] = buffs
        bufatk = int(player.atk * buffs.get("atk_up", {}).get("multiplier", 1.0))
        bufdef = int(player.defense * buffs.get("def_up", {}).get("multiplier", 1.0))

        # ターン経過でデバフを減少
        for key in list(debuffs.keys()):
            debuffs[key]["turns"] -= 1
            if debuffs[key]["turns"] <= 0:
                del debuffs[key]

        request.session["debuffs"] = debuffs
        debufatk = int(enemy.atk * debuffs.get("atk_down", {}).get("multiplier", 1.0))
        debufdef = int(enemy.defense * debuffs.get("def_down", {}).get("multiplier", 1.0))


        player.save()
        return render(request, "game/battle.html", {
            "player": player,
            "enemy": enemy,
            "message": message,
            "bufatk": bufatk,
            "bufdef": bufdef,
            "buffs": buffs,
            "debufatk": debufatk,
            "debufdef": debufdef,
            "debuffs": debuffs,
        })
    
    return render(request, "game/battle.html", {
        "player": player,
        "enemy": enemy,
        "message": message,
        "bufatk": bufatk,
        "bufdef": bufdef,
        "buffs": buffs,
        "debufatk": debufatk,
        "debufdef": debufdef,
        "debuffs": debuffs,
    })
