import random
from django.shortcuts import render,redirect
from .models import Player, PlayerProfile,Enemy, Equipment
from .skills import ENEMY_SKILLS, PLAYER_SKILLS
from .weapons_armors import WEAPONS, ARMORS


def home(request):
    return render(request, 'game/home.html')


def start_game(request):
    """新規プレイヤー作成（職業選択あり）"""
    if request.method == 'POST':
        name = request.POST.get('name')
        job = request.POST.get('job', '戦士')  # デフォルトは戦士
        
        # プロフィール作成
        profile = PlayerProfile.objects.create(name=name)
        
        # ジョブに応じたステータス設定
        if job == "戦士":
            base_hp, base_atk, base_def, base_spd = 100, 10, 5, 5
            job_bonus_hp, job_bonus_atk, job_bonus_def, job_bonus_spd = 5, 3, 2, 0
            stat_points = 5
        elif job == "魔法使い":
            base_hp, base_atk, base_def, base_spd = 100, 10, 5, 5
            job_bonus_hp, job_bonus_atk, job_bonus_def, job_bonus_spd = -10, 8, -2, 2
            stat_points = 5
        elif job == "盗賊":
            base_hp, base_atk, base_def, base_spd = 100, 10, 5, 5
            job_bonus_hp, job_bonus_atk, job_bonus_def, job_bonus_spd = 0, 3, 0, 7
            stat_points = 5
        else:
            base_hp, base_atk, base_def, base_spd = 100, 10, 5, 5
            job_bonus_hp, job_bonus_atk, job_bonus_def, job_bonus_spd = 0, 0, 0, 0
            stat_points = 5
        
        # 初期装備をデータベースから取得
        wooden_sword = Equipment.objects.get(name="木の剣")
        leather_armor = Equipment.objects.get(name="皮の服")
        
        # プレイヤー作成
        player = Player.objects.create(
            profile=profile,
            level=1,
            exp=0,
            next_exp=500,
            max_hp=base_hp + job_bonus_hp,
            hp=base_hp + job_bonus_hp,
            atk=base_atk + job_bonus_atk,
            defense=base_def + job_bonus_def,
            spd=base_spd + job_bonus_spd,
            max_mp=50,
            mp=50,
            stat_points=stat_points,
            job=job,
            weapon=wooden_sword,
            armor=leather_armor,
            gold=100,
        )
        
        return redirect('battle_start_redirect', player_id=player.id)
    
    return render(request, 'game/start.html')


def battle_start(request, player_id, enemy_id=None):
    player = Player.objects.get(id=player_id)
    
    # プレイヤーのHPが0以下の場合、最大HPに回復
    if player.total_hp <= 0:
        player.hp = player.max_hp  # 素のHPを最大値に戻す
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
    
    # 新しい戦闘開始時にメッセージ履歴をクリア
    request.session["message_history"] = []

    exp_percent = int(player.exp / player.next_exp * 100)

    continue_count = 2 - player.defeats

    if request.method == 'POST':
        # 休む機能の処理
        action = request.POST.get('action')
        if action == 'rest':
            player.hp = player.max_hp  # 素のHPを最大値に戻す
            player.mp = player.max_mp  # SPも最大値に戻す
            player.save()
            return redirect('battle_start_redirect', player_id=player.id)

        # ステータスポイント配分の処理
        stat = request.POST.get('stat')
        if stat and player.stat_points > 0:
            if stat == 'atk':
                player.atk += 1  # 【素のATK】を増やす
            elif stat == 'defense':
                player.defense += 1  # 【素のDEF】を増やす
            elif stat == 'hp':
                player.max_hp += 10  # 【素の最大HP】を増やす
                player.hp += 10  # 【素の現在HP】も増やす
            elif stat == 'spd':
                player.spd += 1  # 【素のSPD】を増やす
            elif stat == 'mp':
                player.max_mp += 5  # 【最大SP】を増やす
                player.mp += 5  # 【現在SP】も増やす
            player.stat_points -= 1
            player.save()
            return redirect('battle_start_redirect', player_id=player.id)

    return render(request, 'game/battle_start.html', {"player": player, "enemy": enemy, "exp_percent": exp_percent, "continue_count": continue_count,})

def battle(request,player_id,enemy_id):
    player=Player.objects.get(id=player_id)
    enemy_id = request.session.get("enemy_id")
    enemy = Enemy.objects.get(id=enemy_id)
    message = ""
    
    # メッセージ履歴を取得（累積表示用）
    message_history = request.session.get("message_history", [])

    buffs = request.session.get("buffs", {})
    debuffs = request.session.get("debuffs", {})
    
    # プレイヤーのスキルを取得
    player_skills = PLAYER_SKILLS.get(player.job, [])
    
    # 【表示用ステータス】装備ボーナス込み + バフ×デバフ適用
    # プレイヤー（total_atk, total_def, total_spdは装備込みのプロパティ）
    player_atk_buff = buffs.get("player", {}).get("atk", {}).get("multiplier", 1.0)
    player_atk_debuff = debuffs.get("player", {}).get("atk", {}).get("multiplier", 1.0)
    showplayer_atk = int(player.total_atk * player_atk_buff * player_atk_debuff)
    
    player_def_buff = buffs.get("player", {}).get("def", {}).get("multiplier", 1.0)
    player_def_debuff = debuffs.get("player", {}).get("def", {}).get("multiplier", 1.0)
    showplayer_def = int(player.total_def * player_def_buff * player_def_debuff)
    
    player_spd_buff = buffs.get("player", {}).get("spd", {}).get("multiplier", 1.0)
    player_spd_debuff = debuffs.get("player", {}).get("spd", {}).get("multiplier", 1.0)
    showplayer_spd = int(player.total_spd * player_spd_buff * player_spd_debuff)
    
    # 敵（装備なし）
    enemy_atk_buff = buffs.get("enemy", {}).get("atk", {}).get("multiplier", 1.0)
    enemy_atk_debuff = debuffs.get("enemy", {}).get("atk", {}).get("multiplier", 1.0)
    showenemy_atk = int(enemy.atk * enemy_atk_buff * enemy_atk_debuff)
    
    enemy_def_buff = buffs.get("enemy", {}).get("def", {}).get("multiplier", 1.0)
    enemy_def_debuff = debuffs.get("enemy", {}).get("def", {}).get("multiplier", 1.0)
    showenemy_def = int(enemy.defense * enemy_def_buff * enemy_def_debuff)
    
    enemy_spd_buff = buffs.get("enemy", {}).get("spd", {}).get("multiplier", 1.0)
    enemy_spd_debuff = debuffs.get("enemy", {}).get("spd", {}).get("multiplier", 1.0)
    showenemy_spd = int(enemy.spd * enemy_spd_buff * enemy_spd_debuff)

    def game_over(message):
        message += f"{player.name} は力尽きた… ゲームオーバー！\n"
        player.defeats = 0
        player.level = 1
        player.exp = 0
        player.next_exp = 500
        player.max_hp = 100  # 【素の最大HP】をリセット
        player.hp = 100  # 【素の現在HP】をリセット
        player.atk = 10  # 【素のATK】をリセット
        player.defense = 5  # 【素のDEF】をリセット
        player.spd = 5  # 【素のSPD】をリセット
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
        message += f"{player.name} は倒れてしまった… 休んで回復しよう\n"
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
    
    def calculate_player_attack(multiplier=1.0, damage_variance=(-1, 2)):
        """プレイヤーの攻撃ダメージを計算する共通関数
        
        Args:
            multiplier: 攻撃力の倍率（デフォルト1.0）
            damage_variance: ダメージのランダム範囲（デフォルト-1〜+2）
        
        Returns:
            damage: 計算されたダメージ値
        """
        # プレイヤーの攻撃力【装備ボーナス込み】にバフとデバフを適用
        player_atk_buff = buffs.get("player", {}).get("atk", {}).get("multiplier", 1.0)
        player_atk_debuff = debuffs.get("player", {}).get("atk", {}).get("multiplier", 1.0)
        atk = int(player.total_atk * multiplier * player_atk_buff * player_atk_debuff)
        
        # 敵の防御力にバフとデバフを適用
        enemy_def_buff = buffs.get("enemy", {}).get("def", {}).get("multiplier", 1.0)
        enemy_def_debuff = debuffs.get("enemy", {}).get("def", {}).get("multiplier", 1.0)
        enemy_def = int(enemy.defense * enemy_def_buff * enemy_def_debuff)
        
        # 敵が防御アクション中か確認
        effective_def = enemy_def if is_defense_action(actione) else enemy_def // 3
        
        # 基礎ダメージ計算
        base_damage = int(atk - effective_def)
        
        # ランダムダメージ計算
        damage = max(random.randint(base_damage + damage_variance[0], base_damage + damage_variance[1]), 1)
        
        return damage
    
    def playerAction(message,action,special,actione):
        if action == 'attack':
            damage = calculate_player_attack()
            enemy.hp -= damage
            enemy.save()
            message = f"{player.name}の攻撃！ {enemy.name}に{damage}ダメージ！\n"
        
        elif action == 'defend':
            message = f"{player.name} は防御した！\n"+ (f"防御によってSPが少し回復した！\n" if action == "defend" and player.mp < player.max_mp else "")
            player.mp += random.randint(player.max_mp // 20 , player.max_mp // 10) if player.mp < player.max_mp else 0

        elif special:
            # skills.pyからプレイヤーのスキルを取得
            player_skills = PLAYER_SKILLS.get(player.job, [])
            skill_index = int(special.replace('skill', '')) - 1  # skill1 -> 0, skill2 -> 1, ...
            
            if skill_index < 0 or skill_index >= len(player_skills):
                message = f"そのスキルは存在しません。"
                return message, False
            
            skill_data = player_skills[skill_index]
            skill_name = skill_data["name"]
            skill_cost = skill_data["cost"]
            
            # SP不足チェック
            if player.mp < skill_cost:
                message = f"SPが足りません！ {skill_name} を発動するには SPが{skill_cost}必要です。"
                return message, False
            
            # SPを消費
            player.mp -= skill_cost
            message = f"{player.name}の{skill_name}！\n"
            
            # スキルの効果を適用
            for effect in skill_data["effects"]:
                etype = effect["type"]
                target = effect["target"]
                multiplier = effect.get("multiplier", 1.0)
                stat = effect.get("stat", None)
                turn = effect.get("turn", 0)
                
                target_obj = player if target == "player" else enemy
                
                if etype == "attack":
                    # 攻撃処理（共通関数を使用、スキル攻撃は防御アクション無視）
                    damage = calculate_player_attack(
                        multiplier=multiplier,
                        damage_variance=(0, 3),
                    )
                    enemy.hp -= damage
                    message += f"{enemy.name}に{damage}の大ダメージ！\n"
                    enemy.save()
                
                elif etype == "buf" or etype == "debuf":
                    # バフ・デバフ処理
                    container = buffs if etype == "buf" else debuffs
                    container.setdefault(target, {})
                    if stat not in container[target]:
                        container[target][stat] = {"multiplier": multiplier, "turn": turn}
                    else:
                        container[target][stat]["turn"] = turn
                    request.session["buffs"] = buffs
                    request.session["debuffs"] = debuffs
                    message += f"{target_obj.name}の{stat}が" + ("上昇した！\n" if etype == "buf" else "低下した！\n")
            
            message += f"SPが{skill_cost}減った！\n"
            player.save()
                
        return message,True
    
    def choose_enemyAction(enemy,player):
        skills = ENEMY_SKILLS.get(enemy.name, [])
        if not skills:
            return None  # スキルが存在しない場合はNoneを返す
        
        total_priority = sum(skill["priority"] for skill in skills)
        rand_val = random.uniform(0, total_priority)
        cumulative = 0
        for skill in skills:
            cumulative += skill["priority"]
            if rand_val <= cumulative:
                return skill
            
        return random.choice(skills)  # フォールバックとしてランダムに選択

    def enemyAction(message,enemy,player,buffs,debuffs,actionp,actione):     
        message = f"{enemy.name}の{actione['name']}！　"

        for effect in actione["effects"]:
            etype = effect["type"]      # attack / defense / buf / debuf など
            target = effect["target"]   # "player" or "enemy"
            multiplier = effect.get("multiplier", 1.0)
            stat = effect.get("stat", None)
            turn = effect.get("turn", 0)

            target_obj = player if target == "player" else enemy
            me_obj = enemy if target == "player" else player

            if etype == "attack":
                # 敵の攻撃力にバフとデバフの両方を適用
                enemy_atk_buff = buffs.get("enemy", {}).get("atk", {}).get("multiplier", 1.0)
                enemy_atk_debuff = debuffs.get("enemy", {}).get("atk", {}).get("multiplier", 1.0)
                atk = int(me_obj.atk * multiplier * enemy_atk_buff * enemy_atk_debuff)
                
                # プレイヤーの防御力にバフとデバフを適用【装備ボーナス込み】
                player_def_buff = buffs.get("player", {}).get("def", {}).get("multiplier", 1.0)
                player_def_debuff = debuffs.get("player", {}).get("def", {}).get("multiplier", 1.0)
                player_def = int(target_obj.total_def * player_def_buff * player_def_debuff)
                
                # 防御アクションを考慮してダメージ計算
                damage_base = int(atk - (player_def if actionp == "defend" else player_def // 3))                
                damage = max(random.randint(damage_base - 2, damage_base + 1), 1)
                
                # プレイヤーが対象の場合は【素のHP】を減らす（total_hpは自動計算される）
                target_obj.hp = max(0, target_obj.hp - damage)
                message += f"{target_obj.name}に{damage}のダメージ！\n"

            elif etype == "defense":
                message += f"{target_obj.name}は防御した！\n"
            
            elif etype == "buf" or etype == "debuf":
                container = buffs if etype == "buf" else debuffs
                container.setdefault(target, {})
                if stat not in container[target]:
                    container[target][stat] = {"multiplier": multiplier, "turn": turn}
                else:
                    container[target][stat]["turn"] = turn

                message += f"{target_obj.name}の{stat}が{turn}ターン" + ("上がった！\n" if etype == "buf" else "下がった\n")  

        return message,buffs,debuffs

    def is_defense_action(actione):
        """actioneが防御スキルかどうかを判定"""
        if not actione:
            return False
        return any(effect.get("type") == "defense" for effect in actione.get("effects", []))

    def spdcheck(actionp,actione):
        if actionp == 'defend':
            return True
        elif is_defense_action(actione):
            return False
        else:
            # プレイヤーの素早さにバフとデバフを適用（装備ボーナス込み）
            player_spd_buff = buffs.get("player", {}).get("spd", {}).get("multiplier", 1.0)
            player_spd_debuff = debuffs.get("player", {}).get("spd", {}).get("multiplier", 1.0)
            effective_player_spd = player.total_spd * player_spd_buff * player_spd_debuff
            
            # 敵の素早さにバフとデバフを適用
            enemy_spd_buff = buffs.get("enemy", {}).get("spd", {}).get("multiplier", 1.0)
            enemy_spd_debuff = debuffs.get("enemy", {}).get("spd", {}).get("multiplier", 1.0)
            effective_enemy_spd = enemy.spd * enemy_spd_buff * enemy_spd_debuff
            
            return effective_player_spd >= effective_enemy_spd

    if request.method == 'POST':
        
        actionp = request.POST.get('action')
        special = request.POST.get('special')
        actione = choose_enemyAction(enemy,player)

        spdcheck = spdcheck(actionp,actione)
        if spdcheck:
            message,success = playerAction(message,actionp,special,actione)
            if not success:
                # HP・SPのゲージ用パーセンテージを計算
                player_hp_percent = int((player.total_hp / player.total_max_hp) * 100) if player.total_max_hp > 0 else 0
                player_sp_percent = int((player.mp / player.max_mp) * 100) if player.max_mp > 0 else 0
                enemy_hp_percent = int((enemy.hp / enemy.max_hp) * 100) if enemy.max_hp > 0 else 0
                
                return render(request, "game/battle.html", {
                    "player": player,
                    "enemy": enemy,
                    "message": message,
                    "message_history": message_history,
                    "showplayer_atk": showplayer_atk,
                    "showplayer_def": showplayer_def,
                    "showplayer_spd": showplayer_spd,
                    "buffs": buffs,
                    "showenemy_atk": showenemy_atk,
                    "showenemy_def": showenemy_def,
                    "showenemy_spd": showenemy_spd,
                    "debuffs": debuffs,
                    "player_skills": player_skills,
                    "player_hp_percent": player_hp_percent,
                    "player_sp_percent": player_sp_percent,
                    "enemy_hp_percent": enemy_hp_percent,
                })
            if enemy.hp <= 0:
                message = win(message)
                # HP・SPのゲージ用パーセンテージを計算
                player_hp_percent = int((player.total_hp / player.total_max_hp) * 100) if player.total_max_hp > 0 else 0
                player_sp_percent = int((player.mp / player.max_mp) * 100) if player.max_mp > 0 else 0
                enemy_hp_percent = 0  # 敵は倒された
                
                return render(request, "game/battle.html", {
                    "player": player,
                    "enemy": None,
                    "message": message,
                    "message_history": message_history,
                    "showplayer_atk": showplayer_atk,
                    "showplayer_def": showplayer_def,
                    "showplayer_spd": showplayer_spd,
                    "buffs": buffs,
                    "showenemy_atk": showenemy_atk,
                    "showenemy_def": showenemy_def,
                    "showenemy_spd": showenemy_spd,
                    "debuffs": debuffs,
                    "player_skills": player_skills,
                    "player_hp_percent": player_hp_percent,
                    "player_sp_percent": player_sp_percent,
                    "enemy_hp_percent": enemy_hp_percent,
                })
            ex_message,buffs,debuffs = enemyAction(message,enemy,player,buffs,debuffs,actionp,actione)
            # セッションに保存
            request.session["buffs"] = buffs
            request.session["debuffs"] = debuffs
            message += ex_message    
            
            # プレイヤーの【素のHP】が0以下になったかチェック
            if player.hp <= 0:
                player.defeats += 1
                if player.defeats >= 3:
                    message = game_over(message)
                    return render(request, "game/gameover.html", {"player": player, "message": message})
                else:
                    message = tohome(message)
                    # HP・SPのゲージ用パーセンテージを計算
                    player_hp_percent = int((player.total_hp / player.total_max_hp) * 100) if player.total_max_hp > 0 else 0
                    player_sp_percent = int((player.mp / player.max_mp) * 100) if player.max_mp > 0 else 0
                    enemy_hp_percent = int((enemy.hp / enemy.max_hp) * 100) if enemy.max_hp > 0 else 0
                    
                    return render(request, "game/battle.html", {
                        "player": player,
                        "enemy": enemy,
                        "message": message,
                        "message_history": message_history,
                        "showplayer_atk": showplayer_atk,
                        "showplayer_def": showplayer_def,
                        "showplayer_spd": showplayer_spd,
                        "buffs": buffs,
                        "showenemy_atk": showenemy_atk,
                        "showenemy_def": showenemy_def,
                        "showenemy_spd": showenemy_spd,
                        "debuffs": debuffs,
                        "redirect_after": True,
                        "redirect_url": "battle_start",
                        "recovering": True,
                        "player_skills": player_skills,
                        "player_hp_percent": player_hp_percent,
                        "player_sp_percent": player_sp_percent,
                        "enemy_hp_percent": enemy_hp_percent,
                    })          
        else:
            message,buffs,debuffs = enemyAction(message,enemy,player,buffs,debuffs,actionp,actione)
            # セッションに保存
            request.session["buffs"] = buffs
            request.session["debuffs"] = debuffs
            
            # プレイヤーの【素のHP】が0以下になったかチェック
            if player.hp <= 0:
                player.defeats += 1
                if player.defeats >= 3:
                    message = game_over(message)
                    return render(request, "game/gameover.html", {"player": player, "message": message})
                else:
                    message = tohome(message)
                    # HP・SPのゲージ用パーセンテージを計算
                    player_hp_percent = int((player.total_hp / player.total_max_hp) * 100) if player.total_max_hp > 0 else 0
                    player_sp_percent = int((player.mp / player.max_mp) * 100) if player.max_mp > 0 else 0
                    enemy_hp_percent = int((enemy.hp / enemy.max_hp) * 100) if enemy.max_hp > 0 else 0
                    
                    return render(request, "game/battle.html", {
                        "player": player,
                        "enemy": enemy,
                        "message": message,
                        "message_history": message_history,
                        "showplayer_atk": showplayer_atk,
                        "showplayer_def": showplayer_def,
                        "showplayer_spd": showplayer_spd,
                        "buffs": buffs,
                        "showenemy_atk": showenemy_atk,
                        "showenemy_def": showenemy_def,
                        "showenemy_spd": showenemy_spd,
                        "debuffs": debuffs,
                        "redirect_after": True,
                        "redirect_url": "battle_start",
                        "recovering": True,
                        "player_skills": player_skills,
                        "player_hp_percent": player_hp_percent,
                        "player_sp_percent": player_sp_percent,
                        "enemy_hp_percent": enemy_hp_percent,
                    })
            
            ex_message,success = playerAction(message,actionp,special,actione)
            message += ex_message
            if not success:
                # HP・SPのゲージ用パーセンテージを計算
                player_hp_percent = int((player.total_hp / player.total_max_hp) * 100) if player.total_max_hp > 0 else 0
                player_sp_percent = int((player.mp / player.max_mp) * 100) if player.max_mp > 0 else 0
                enemy_hp_percent = int((enemy.hp / enemy.max_hp) * 100) if enemy.max_hp > 0 else 0
                
                return render(request, "game/battle.html", {
                    "player": player,
                    "enemy": enemy,
                    "message": message,
                    "message_history": message_history,
                    "showplayer_atk": showplayer_atk,
                    "showplayer_def": showplayer_def,
                    "showplayer_spd": showplayer_spd,
                    "buffs": buffs,
                    "showenemy_atk": showenemy_atk,
                    "showenemy_def": showenemy_def,
                    "showenemy_spd": showenemy_spd,
                    "debuffs": debuffs,
                    "player_skills": player_skills,
                    "player_hp_percent": player_hp_percent,
                    "player_sp_percent": player_sp_percent,
                    "enemy_hp_percent": enemy_hp_percent,
                })
            if enemy.hp <= 0:
                message = win(message)
                # HP・SPのゲージ用パーセンテージを計算
                player_hp_percent = int((player.total_hp / player.total_max_hp) * 100) if player.total_max_hp > 0 else 0
                player_sp_percent = int((player.mp / player.max_mp) * 100) if player.max_mp > 0 else 0
                enemy_hp_percent = 0  # 敵は倒された
                
                return render(request, "game/battle.html", {
                    "player": player,
                    "enemy": None,
                    "message": message,
                    "message_history": message_history,
                    "showplayer_atk": showplayer_atk,
                    "showplayer_def": showplayer_def,
                    "showplayer_spd": showplayer_spd,
                    "buffs": buffs,
                    "showenemy_atk": showenemy_atk,
                    "showenemy_def": showenemy_def,
                    "showenemy_spd": showenemy_spd,
                    "debuffs": debuffs,
                    "player_skills": player_skills,
                    "player_hp_percent": player_hp_percent,
                    "player_sp_percent": player_sp_percent,
                    "enemy_hp_percent": enemy_hp_percent,
                })
          

        # ターン経過でバフを減少
        for target in list(buffs.keys()):
            for stat in list(buffs[target].keys()):
                buffs[target][stat]["turn"] -= 1
                if buffs[target][stat]["turn"] <= 0:
                    del buffs[target][stat]
            # 空になったターゲットを削除
            if not buffs[target]:
                del buffs[target]

        request.session["buffs"] = buffs

        # ターン経過でデバフを減少
        for target in list(debuffs.keys()):
            for stat in list(debuffs[target].keys()):
                debuffs[target][stat]["turn"] -= 1
                if debuffs[target][stat]["turn"] <= 0:
                    del debuffs[target][stat]
            # 空になったターゲットを削除
            if not debuffs[target]:
                del debuffs[target]

        request.session["debuffs"] = debuffs
        
        # 表示用ステータスを再計算【装備ボーナス込み + バフ×デバフ適用】
        # プレイヤーのステータス（total_atk, total_def, total_spdは装備込み）
        player_atk_buff = buffs.get("player", {}).get("atk", {}).get("multiplier", 1.0)
        player_atk_debuff = debuffs.get("player", {}).get("atk", {}).get("multiplier", 1.0)
        showplayer_atk = int(player.total_atk * player_atk_buff * player_atk_debuff)
        
        player_def_buff = buffs.get("player", {}).get("def", {}).get("multiplier", 1.0)
        player_def_debuff = debuffs.get("player", {}).get("def", {}).get("multiplier", 1.0)
        showplayer_def = int(player.total_def * player_def_buff * player_def_debuff)
        
        player_spd_buff = buffs.get("player", {}).get("spd", {}).get("multiplier", 1.0)
        player_spd_debuff = debuffs.get("player", {}).get("spd", {}).get("multiplier", 1.0)
        showplayer_spd = int(player.total_spd * player_spd_buff * player_spd_debuff)
        
        # 敵のステータス（装備なし）
        enemy_atk_buff = buffs.get("enemy", {}).get("atk", {}).get("multiplier", 1.0)
        enemy_atk_debuff = debuffs.get("enemy", {}).get("atk", {}).get("multiplier", 1.0)
        showenemy_atk = int(enemy.atk * enemy_atk_buff * enemy_atk_debuff)
        
        enemy_def_buff = buffs.get("enemy", {}).get("def", {}).get("multiplier", 1.0)
        enemy_def_debuff = debuffs.get("enemy", {}).get("def", {}).get("multiplier", 1.0)
        showenemy_def = int(enemy.defense * enemy_def_buff * enemy_def_debuff)
        
        enemy_spd_buff = buffs.get("enemy", {}).get("spd", {}).get("multiplier", 1.0)
        enemy_spd_debuff = debuffs.get("enemy", {}).get("spd", {}).get("multiplier", 1.0)
        showenemy_spd = int(enemy.spd * enemy_spd_buff * enemy_spd_debuff)

        # メッセージを履歴に追加
        if message:
            message_history.append(message)
            request.session["message_history"] = message_history

        player.save()
        
        # HP・SPのゲージ用パーセンテージを計算
        player_hp_percent = int((player.total_hp / player.total_max_hp) * 100) if player.total_max_hp > 0 else 0
        player_sp_percent = int((player.mp / player.max_mp) * 100) if player.max_mp > 0 else 0
        enemy_hp_percent = int((enemy.hp / enemy.max_hp) * 100) if enemy.max_hp > 0 else 0
        
        return render(request, "game/battle.html", {
            "player": player,
            "enemy": enemy,
            "message": message,
            "message_history": message_history,
            "showplayer_atk": showplayer_atk,
            "showplayer_def": showplayer_def,
            "showplayer_spd": showplayer_spd,
            "buffs": buffs,
            "showenemy_atk": showenemy_atk,
            "showenemy_def": showenemy_def,
            "showenemy_spd": showenemy_spd,
            "debuffs": debuffs,
            "player_skills": player_skills,
            "player_hp_percent": player_hp_percent,
            "player_sp_percent": player_sp_percent,
            "enemy_hp_percent": enemy_hp_percent,
        })
    
    
    # HP・SPのゲージ用パーセンテージを計算
    player_hp_percent = int((player.total_hp / player.total_max_hp) * 100) if player.total_max_hp > 0 else 0
    player_sp_percent = int((player.mp / player.max_mp) * 100) if player.max_mp > 0 else 0
    enemy_hp_percent = int((enemy.hp / enemy.max_hp) * 100) if enemy.max_hp > 0 else 0
    
    return render(request, "game/battle.html", {
        "player": player,
        "enemy": enemy,
        "message": message,
        "message_history": message_history,
        "showplayer_atk": showplayer_atk,
        "showplayer_def": showplayer_def,
        "showplayer_spd": showplayer_spd,
        "buffs": buffs,
        "showenemy_atk": showenemy_atk,
        "showenemy_def": showenemy_def,
        "showenemy_spd": showenemy_spd,
        "debuffs": debuffs,
        "player_skills": player_skills,
        "player_hp_percent": player_hp_percent,
        "player_sp_percent": player_sp_percent,
        "enemy_hp_percent": enemy_hp_percent,
    })


def shop(request, player_id):
    """ショップページ"""
    player = Player.objects.get(id=player_id)
    
    # データベースから全装備を取得
    weapons = Equipment.objects.filter(equipment_type='weapon')
    armors = Equipment.objects.filter(equipment_type='armor')
    
    return render(request, 'game/shop.html', {
        'player': player,
        'weapons': weapons,
        'armors': armors,
    })
