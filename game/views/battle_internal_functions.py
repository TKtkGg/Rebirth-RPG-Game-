"""
battle関数の内部関数を外部化したモジュール
"""
import random
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from ..models import PlayerQuest
from ..skills import ENEMY_SKILLS, PLAYER_SKILLS
from .utils import (
    level_up_player,
    initialize_player_quests,
    decrease_buff_debuff_turns,
    _get_score_rates,
    get_skill_multiplier,
)
from .battle_helpers import _get_effective_stat


_ENEMY_DEFAULT = object()


def render_battle_screen(
    message,
    player,
    enemy,
    message_history,
    showplayer_atk,
    showplayer_def,
    showplayer_spd,
    buffs,
    showenemy_atk,
    showenemy_def,
    showenemy_spd,
    debuffs,
    player_skills,
    player_items,
    stage,
    enemy_override=_ENEMY_DEFAULT,
    **kwargs
):
    """戦闘画面のコンテキストを生成する共通関数"""
    # enemy_overrideが渡されていない場合はデフォルトのenemyを使用
    # 渡されている場合（Noneを含む）はその値を使用
    current_enemy = enemy if enemy_override is _ENEMY_DEFAULT else enemy_override
    
    # HP・SPのゲージ用パーセンテージを計算
    player_hp_percent = int((player.total_hp_battle / player.total_max_hp_battle) * 100) if player.total_max_hp_battle > 0 else 0
    player_sp_percent = int((player.mp / player.max_mp) * 100) if player.max_mp > 0 else 0
    enemy_hp_percent = int((current_enemy.hp / current_enemy.max_hp) * 100) if current_enemy and current_enemy.max_hp > 0 else 0
    
    context = {
        "player": player,
        "enemy": current_enemy,
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
        "player_items": player_items,
        "stage": stage,
        "player_hp_percent": player_hp_percent,
        "player_sp_percent": player_sp_percent,
        "enemy_hp_percent": enemy_hp_percent,
    }
    context.update(kwargs)
    return context


def tohome(message, player, request):
    # 休むペナルティ：経験値を全て失い、ゴールドの30%を減少
    gold_penalty = int(player.gold * 0.3)
    
    actual_exp_penalty = player.exp  # 全ての経験値を失う
    actual_gold_penalty = min(gold_penalty, player.gold)
    
    player.exp = 0
    player.gold = max(0, player.gold - gold_penalty)
    
    message += f"{player.name} は倒れてしまった… 休んで回復しよう\n"
    message += f"経験値を全て失った…\n"
    message += f"ゴールドを{actual_gold_penalty}失った…\n"
    request.session["buffs"] = {}
    request.session["debuffs"] = {}
    request.session["special_states"] = {}
    
    # 戦闘用HPを素のHPに反映
    player.sync_hp_from_battle()
    
    # SPを全回復
    player.mp = player.max_mp
    player.save()
    
    return message


def win(message, player, enemy, request):
    # 強敵の場合は経験値とゴールドを5倍
    exp_multiplier = 5 if enemy.is_strong else 1
    gold_multiplier = 5 if enemy.is_strong else 1

    gained_exp = enemy.exp * exp_multiplier
    gained_gold = enemy.drop_gold * gold_multiplier
    if player.user:
        gold_rate, exp_rate = _get_score_rates(player.user, player.job)
        gained_exp = int(gained_exp * exp_rate)
        gained_gold = int(gained_gold * gold_rate)
    
    player.exp += gained_exp
    player.gold += gained_gold
    existLevel = player.level
    message += f"{enemy.name}を倒した！\n"
    message += f"経験値を{gained_exp}ゲットした！\n"
    message += f"{gained_gold}Gゲットした！\n"
    enemy.hp = 0
    enemy.is_defeated = True
    enemy.save()
    
    # 敵を倒した回数をカウントアップ
    player.defeats += 1
    if enemy.is_strong:
        player.strong_defeats += 1
    player.save()
    
    # クエストを初期化（まだ作成されていないPlayerQuestを作成）
    initialize_player_quests(player)
    
    # クエスト進捗更新（敵撃破）
    enemy_defeat_quests = PlayerQuest.objects.filter(
        player=player,
        quest_template__condition_type='defeat_enemy',
        quest_template__condition_target=enemy.name,
        is_completed=False
    )
    for player_quest in enemy_defeat_quests:
        player_quest.update_progress(1)
    
    # クエスト進捗更新（強敵撃破）
    if enemy.is_strong:
        strong_enemy_defeat_quests = PlayerQuest.objects.filter(
            player=player,
            quest_template__condition_type='defeat_strong_enemy',
            is_completed=False
        )
        # condition_targetが空または敵の名前と一致する場合
        for player_quest in strong_enemy_defeat_quests:
            if not player_quest.quest_template.condition_target or player_quest.quest_template.condition_target == enemy.name:
                player_quest.update_progress(1)

    # レベルアップ処理
    message, _ = level_up_player(player, message)

    # 戦闘回数をカウントアップ
    battle_count = request.session.get('battle_count', 0)
    request.session['battle_count'] = battle_count + 1

    request.session["buffs"] = {}
    request.session["debuffs"] = {}
    
    # 戦闘用HPを素のHPに反映
    player.sync_hp_from_battle()
    
    # AJAX用に勝利情報をセッションに保存
    request.session['gained_exp'] = gained_exp
    request.session['gained_gold'] = gained_gold
    request.session['old_level'] = existLevel
    
    return message, gained_exp, gained_gold, existLevel


def calculate_player_attack(player, enemy, buffs, debuffs, actione, multiplier=1.0, damage_variance=(-1, 2)):
    """プレイヤーの攻撃ダメージを計算する共通関数
    
    Args:
        multiplier: 攻撃力の倍率（デフォルト1.0）
        damage_variance: ダメージのランダム範囲（デフォルト-1〜+2）
    
    Returns:
        damage: 計算されたダメージ値
    """
    # プレイヤーの攻撃力【戦闘用ステータス】にバフとデバフを適用
    atk = int(
        _get_effective_stat(player.total_atk_battle, buffs, debuffs, "player", "atk") * multiplier
    )
    
    # 敵の防御力にバフとデバフを適用
    enemy_def = int(_get_effective_stat(enemy.defense, buffs, debuffs, "enemy", "def"))
    
    # 敵が防御アクション中か確認
    effective_def = enemy_def // 1.5 if is_defense_action(actione) else enemy_def // 3
    
    # 基礎ダメージ計算
    base_damage = int(atk - effective_def)
    
    # ランダムダメージ計算
    damage = max(random.randint(base_damage + damage_variance[0], base_damage + damage_variance[1]), 1)
    
    return damage


def calculate_evasion_rate(spd):
    """回避率を計算する関数
    
    Args:
        spd: 素早さの値（バフ・デバフ適用済み）
    
    Returns:
        evasion_rate: 回避率（0.0〜0.4）
    """
    if spd <= 0:
        return 0.0
    
    # 最低3%、最高40%
    # spd=1で3%、spd=100で40%
    min_rate = 0.03
    max_rate = 0.40
    min_spd = 1
    max_spd = 100
    
    if spd <= min_spd:
        return min_rate
    elif spd >= max_spd:
        return max_rate
    else:
        # 線形補間
        return min_rate + (spd - min_spd) * (max_rate - min_rate) / (max_spd - min_spd)


def playerAction(message, action, special, actione, player, enemy, buffs, debuffs, special_states, request):
    action_result = {
        "damage": 0,
        "evaded": False,
    }
    if action == 'attack':
        # 敵の回避判定（確定回避 or spd基づく確率）
        has_guaranteed_evasion = special_states.get("enemy", {}).get("guaranteed_evasion", {}).get("turn", 0) > 0
        
        if has_guaranteed_evasion:
            message = f"{player.name}の攻撃！ {enemy.name}は回避した！\n"
            action_result["evaded"] = True
        else:
            enemy_effective_spd = _get_effective_stat(enemy.spd, buffs, debuffs, "enemy", "spd")
            evasion_rate = calculate_evasion_rate(enemy_effective_spd)
            
            if random.random() < evasion_rate:
                message = f"{player.name}の攻撃！ {enemy.name}は回避した！\n"
                action_result["evaded"] = True
            else:
                damage = calculate_player_attack(player, enemy, buffs, debuffs, actione)
                enemy.hp -= damage
                enemy.save()
                action_result["damage"] = damage
                message = f"{player.name}の攻撃！ {enemy.name}に{damage}ダメージ！\n"
        player.save()  # プレイヤーの状態を保存
    
    elif action == 'defend':
        message = f"{player.name} は防御した！\n"
        if player.mp < player.max_mp:
            sp_recovery = random.randint(player.max_mp // 20, player.max_mp // 10)
            player.mp = min(player.mp + sp_recovery, player.max_mp)
            message += f"防御によってSPが少し回復した！\n"
        player.save()  # プレイヤーの状態を保存

    elif special:
        # skills.pyからプレイヤーのスキルを取得
        player_skills_local = PLAYER_SKILLS.get(player.job, [])
        skill_index = int(special.replace('skill', '')) - 1  # skill1 -> 0, skill2 -> 1, ...
        
        if skill_index < 0 or skill_index >= len(player_skills_local):
            message = f"そのスキルは存在しません。"
            return message, False, action_result
        
        skill_data = player_skills_local[skill_index]
        skill_name = skill_data["name"]
        skill_cost = skill_data["cost"]
        is_action_skill = skill_data.get("is_action", False)
        
        timing_result = request.POST.get('timing_result')
        
        # SP不足チェック（タイミング特技の結果処理では再チェックしない）
        if not (is_action_skill and skill_data.get("action_type") == "timing" and timing_result is not None):
            if player.mp < skill_cost:
                message = "しかしSPが足りない！"
                return message, False, action_result
        
        # アクション特技の場合は特別な処理
        if is_action_skill:
            timing_result = request.POST.get('timing_result')
            if skill_data.get("action_type") == "timing" and timing_result is not None:
                action_data = request.session.pop('action_mode', None)
                skill_name = action_data.get('skill_name', skill_name) if action_data else skill_name
                try:
                    timing_multiplier = float(request.POST.get('timing_multiplier', 0))
                except (TypeError, ValueError):
                    timing_multiplier = 0
                base_effect = skill_data["effects"][0]
                base_multiplier = base_effect.get("multiplier", 1.0)
                adjusted_base = get_skill_multiplier(
                    player.user,
                    player.job,
                    skill_name,
                    base_effect.get("type"),
                    base_effect.get("stat"),
                    base_multiplier,
                )
                if base_multiplier:
                    timing_multiplier *= adjusted_base / base_multiplier
                else:
                    timing_multiplier = adjusted_base
                timing_multiplier = min(10.0, timing_multiplier)
                
                message = f"{player.name}の{skill_name}！\n"
                
                if timing_result != 'success':
                    message += "失敗してしまった！\n"
                    return message, True, action_result
                
                effective_atk = _get_effective_stat(player.total_atk_battle, buffs, debuffs, "player", "atk")
                enemy_def = _get_effective_stat(enemy.defense, buffs, debuffs, "enemy", "def")
                effective_def = enemy_def // 3
                base_damage = max(1, effective_atk - effective_def)
                damage_variance = random.randint(0, 3)
                damage = max(int(base_damage * timing_multiplier) + damage_variance, 1)
                
                enemy.hp = max(0, enemy.hp - damage)
                enemy.save()
                action_result["damage"] = damage
                message += f"{enemy.name}に{damage}ダメージ！\n"
                return message, True, action_result

            player.mp -= skill_cost
            player.save()
            # アクションモードであることをセッションに保存
            base_effect = skill_data["effects"][0]
            base_multiplier = base_effect.get("multiplier", 1.0)
            adjusted_multiplier = get_skill_multiplier(
                player.user,
                player.job,
                skill_name,
                base_effect.get("type"),
                base_effect.get("stat"),
                base_multiplier,
            )
            request.session['action_mode'] = {
                'skill_name': skill_name,
                'skill_data': skill_data,
                'action_type': skill_data.get("action_type"),
                'skill_index': skill_index,
                'base_multiplier': adjusted_multiplier,
                'multiplier': adjusted_multiplier,
            }
            # アクションモード用の特別なレンダリングを返す
            return message, True, action_result
        
        # SPを消費
        player.mp -= skill_cost
        message = f"{player.name}の{skill_name}！\n"
        
        # スキルの効果を適用
        for effect in skill_data["effects"]:
            etype = effect["type"]
            target = effect["target"]
            stat = effect.get("stat", None)
            multiplier = effect.get("multiplier", 1.0)
            multiplier = get_skill_multiplier(
                player.user,
                player.job,
                skill_name,
                etype,
                stat,
                multiplier,
            )
            turn = effect.get("turn", 0)
            
            target_obj = player if target == "player" else enemy
            
            if etype == "attack":
                # 攻撃処理（共通関数を使用、スキル攻撃は防御アクション無視）
                
                # 敵の回避判定（確定回避 or spd基づく確率）
                has_guaranteed_evasion = special_states.get("enemy", {}).get("guaranteed_evasion", {}).get("turn", 0) > 0
                
                if has_guaranteed_evasion:
                    message += f"{enemy.name}は回避した！\n"
                    action_result["evaded"] = True
                else:
                    enemy_effective_spd = _get_effective_stat(enemy.spd, buffs, debuffs, "enemy", "spd")
                    evasion_rate = calculate_evasion_rate(enemy_effective_spd)
                    
                    if random.random() < evasion_rate:
                        message += f"{enemy.name}は回避した！\n"
                        action_result["evaded"] = True
                    else:
                        damage = calculate_player_attack(
                            player,
                            enemy,
                            buffs,
                            debuffs,
                            actione,
                            multiplier=multiplier,
                            damage_variance=(0, 3),
                        )
                        enemy.hp -= damage
                        action_result["damage"] += damage
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
            
            elif etype == "guaranteed_evasion":
                # 確定回避処理
                special_states.setdefault(target, {})
                special_states[target]["guaranteed_evasion"] = {"turn": turn}
                request.session["special_states"] = special_states
                message += f"{target_obj.name}は姿をくらました！\n"
        
        message += f"SPが{skill_cost}減った！\n"
        player.save()
            
    return message, True, action_result


def choose_enemyAction(enemy, player, buffs, debuffs):
    skills = ENEMY_SKILLS.get(enemy.name, [])
    if not skills:
        return None  # スキルが存在しない場合はNoneを返す
    
    # HP比率を計算
    player_hp_ratio = player.total_hp_battle / player.total_max_hp_battle if player.total_max_hp_battle > 0 else 1.0
    enemy_hp_ratio = enemy.hp / enemy.max_hp if enemy.max_hp > 0 else 1.0
    
    # 各スキルの優先度を動的に調整
    adjusted_skills = []
    for skill in skills:
        # 元のスキルをコピー（ENEMY_SKILLSを破壊しないため）
        skill_copy = {**skill}
        priority = skill_copy["priority"]  # 元の優先度
        
        # スキルの効果を解析
        has_debuff_effect = any(effect.get("type") == "debuf" and effect.get("target") == "player" for effect in skill_copy.get("effects", []))
        has_buff_effect = any(effect.get("type") == "buf" and effect.get("target") == "enemy" for effect in skill_copy.get("effects", []))
        has_attack_effect = any(effect.get("type") == "attack" for effect in skill_copy.get("effects", []))
        has_defense_effect = any(effect.get("type") == "defense" for effect in skill_copy.get("effects", []))
        
        # max_usesがある攻撃/防御スキルを特別扱い
        has_max_uses = "max_uses" in skill_copy
        is_special_attack = has_attack_effect and has_max_uses
        is_special_defense = has_defense_effect and has_max_uses
        
        # 使用回数が0のスキルは優先度を0にする（選ばれなくなる）
        if has_max_uses and skill_copy.get("max_uses", 0) <= 0:
            priority = 0
        else:
            # 1. 敵（player）にデバフがかかっていない場合、自身の技にデバフがあれば
            if not debuffs.get("player") and has_debuff_effect:
                priority *= 2
            elif debuffs.get("player") and has_debuff_effect:
                priority *= 0.05
            
            # 2. 自身（enemy）にバフがかかっていない場合、自身の技にバフがあれば
            if not buffs.get("enemy") and has_buff_effect:
                priority *= 2
            elif buffs.get("enemy") and has_buff_effect:
                priority *= 0.05
            
            # 3. 敵（player）のHPが20%以下の場合
            if player_hp_ratio <= 0.2 and has_attack_effect:
                if is_special_attack:
                    priority *= 5  # 特殊攻撃スキルならさらに優先度を上げる
                else:
                    priority *= 3  # 優先度を大幅に上げる
            # 敵（player）のHPが50%以下の場合
            elif player_hp_ratio <= 0.5 and has_attack_effect:
                if is_special_attack:
                    priority *= 3  # 特殊攻撃スキルなら優先度を上げる
                else:
                    priority *= 2  # 優先度を上げる
            # 敵（player）のHPが100%以下の場合
            elif player_hp_ratio <= 1.0 and has_attack_effect:
                if is_special_attack:
                    priority *= 2  # 特殊攻撃スキルなら少し優先度を上げる
                else:
                    priority *= 1.5  # 優先度を少し上げる
            
            # 4. 自身（enemy）のHPが50%以下の場合
            if enemy_hp_ratio <= 0.35 and has_defense_effect:
                priority -= 1
            else:
                priority -= 1  # HPが高い場合、防御スキルの優先度を下げる
        
        skill_copy["priority"] = priority
        adjusted_skills.append(skill_copy)
    
    # 調整後の優先度に基づいて選択
    total_priority = sum(s["priority"] for s in adjusted_skills)
    if total_priority <= 0:
        # 全スキルの優先度が0の場合、通常攻撃を返す
        return {"name": "攻撃", "effects": [{"type": "attack", "target": "player", "multiplier": 1.0}], "priority": 1}
    
    rand_val = random.uniform(0, total_priority)
    cumulative = 0
    
    for skill in adjusted_skills:
        cumulative += skill["priority"]
        if rand_val <= cumulative:
            # 選ばれたスキルのmax_usesを減らす（元データを更新）
            if "max_uses" in skill and skill["max_uses"] > 0:
                # ENEMY_SKILLSの元データを検索して更新
                for original_skill in ENEMY_SKILLS[enemy.name]:
                    if original_skill["name"] == skill["name"]:
                        original_skill["max_uses"] -= 1
                        break
            
            return skill
    
    return adjusted_skills[0] if adjusted_skills else None  # フォールバックとして最初のスキルを選択


def enemyAction(message, enemy, player, buffs, debuffs, actionp, actione, special_states):
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
            # プレイヤーの回避判定（確定回避 or spdに基づく確率）
            should_evade = False
            if target == "player":
                # 確定回避チェック
                has_guaranteed_evasion = special_states.get("player", {}).get("guaranteed_evasion", {}).get("turn", 0) > 0
                
                if has_guaranteed_evasion:
                    should_evade = True
                else:
                    player_effective_spd = _get_effective_stat(
                        player.total_spd_battle,
                        buffs,
                        debuffs,
                        "player",
                        "spd",
                    )
                    evasion_rate = calculate_evasion_rate(player_effective_spd)
                    should_evade = random.random() < evasion_rate
            
            if should_evade:
                message += f"{target_obj.name}は回避した！\n"
            else:
                # 敵の攻撃力にバフとデバフの両方を適用
                atk = int(
                    _get_effective_stat(me_obj.atk, buffs, debuffs, "enemy", "atk") * multiplier
                )
                
                # プレイヤーの防御力にバフとデバフを適用【戦闘用ステータス】
                player_def = int(
                    _get_effective_stat(
                        target_obj.total_def_battle,
                        buffs,
                        debuffs,
                        "player",
                        "def",
                    )
                )
                
                # 防御アクションを考慮してダメージ計算
                damage_base = int(atk - (player_def // 1.5 if actionp == "defend" else player_def // 3))                
                damage = max(random.randint(damage_base - 2, damage_base + 1), 1)
                
                # プレイヤーが対象の場合、total_hp_battleを直接減らす
                if target == "player":
                    target_obj.total_hp_battle = max(0, target_obj.total_hp_battle - damage)
                    # 素のHPも同期（装備ボーナスを引いた値）
                    weapon_bonus = target_obj.weapon.hp_bonus if target_obj.weapon else 0
                    armor_bonus = target_obj.armor.hp_bonus if target_obj.armor else 0
                    target_obj.hp = max(0, target_obj.total_hp_battle - weapon_bonus - armor_bonus)
                    target_obj.save()  # プレイヤーのHP変更を保存
                else:
                    # 敵の場合は通常通り
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

    return message, buffs, debuffs


def is_defense_action(actione):
    """actioneが防御スキルかどうかを判定"""
    if not actione:
        return False
    return any(effect.get("type") == "defense" for effect in actione.get("effects", []))


def spdcheck(actionp, actione, player, enemy, buffs, debuffs):
    if actionp == 'defend' or actionp == 'item':
        return True
    elif is_defense_action(actione):
        return False
    else:
        # プレイヤー/敵の素早さにバフとデバフを適用
        effective_player_spd = _get_effective_stat(
            player.total_spd_battle,
            buffs,
            debuffs,
            "player",
            "spd",
        )
        effective_enemy_spd = _get_effective_stat(enemy.spd, buffs, debuffs, "enemy", "spd")
        
        return effective_player_spd >= effective_enemy_spd


def escape(message, player, enemy, request):
    """逃走処理"""
    # 逃走成功率の計算（レベル差が大きいほど成功しやすい）
    level_diff = player.level - enemy.level
    base_chance = 0.8  # 基本成功率80%
    # レベル差1につき5%加算、最大100%、最小10%
    escape_chance = max(0.1, min(1.0, base_chance + (level_diff * 0.05)))
    
    if random.random() < escape_chance:
        # 逃走成功
        # 経験値とゴールドのペナルティ（5%）
        exp_penalty = int(player.next_exp * 0.05)
        gold_penalty = int(player.gold * 0.05)
        
        # 実際に減らす経験値（現在の経験値を超えない）
        actual_exp_penalty = min(exp_penalty, player.exp)
        actual_gold_penalty = min(gold_penalty, player.gold)
        
        player.exp = max(0, player.exp - exp_penalty)
        player.gold = max(0, player.gold - gold_penalty)
        
        # 戦闘用HPを素のHPに反映
        player.sync_hp_from_battle()
        
        # バフ・デバフをリセット
        request.session["buffs"] = {}
        request.session["debuffs"] = {}
        
        message += f"にげた！\n"
        return message, True, actual_exp_penalty, actual_gold_penalty
    else:
        # 逃走失敗
        message += f"逃げようとした、しかし失敗した！\n"
        return message, False, 0, 0


def summarize_effects(effects):
    """effectsからアニメーション種別と対象を取得"""
    if not effects:
        return "none", None
    # 優先順位: attack > buf > debuf > guaranteed_evasion > defense
    for effect_type in ("attack", "buf", "debuf", "guaranteed_evasion", "defense"):
        for effect in effects:
            if effect.get("type") == effect_type:
                return effect_type, effect.get("target")
    return "none", None


def handle_action_mode_end(
    request,
    player,
    enemy,
    buffs,
    debuffs,
    special_states,
    message_history,
    timing_result,
    start_player_hp,
    is_ajax,
    player_attack_sound,
    player_attack_effect,
    enemy_attack_sound,
    enemy_attack_effect,
    actionp,
    render_kwargs
):
    action_mode_end = request.POST.get('action_mode_end')
    if not action_mode_end or not request.session.get('action_mode'):
        return None

    local_buffs = buffs
    local_debuffs = debuffs
    local_special_states = special_states

    action_data = request.session.pop('action_mode', None)
    action_type = action_data.get('action_type', 'spam') if action_data else 'spam'
    click_count = int(request.POST.get('click_count', 0))
    total_damage = request.session.pop('action_total_damage', 0)
    skill_name = action_data.get('skill_name', '') if action_data else ''

    message = f"{player.name}の{skill_name}！\n"
    if action_type == 'timing' and timing_result == 'fail':
        message += "失敗してしまった！\n"
    else:
        message += f"{click_count}回の連続攻撃！ 合計{total_damage}ダメージ！\n"

    player_action_message = message
    player_action_damage = total_damage
    player_action_type = "skill"
    player_effect_type = "damage" if total_damage > 0 else "none"
    player_action_target = "enemy"
    player_action_value = 0
    actione = None
    did_enemy_act = False
    enemy_action_message = ""

    if enemy.hp <= 0:
        message, gained_exp, gained_gold, existLevel = win(message, player, enemy, request)
    else:
        actione = choose_enemyAction(enemy, player, local_buffs, local_debuffs)
        ex_message, local_buffs, local_debuffs = enemyAction(
            message,
            enemy,
            player,
            local_buffs,
            local_debuffs,
            None,
            actione,
            local_special_states,
        )
        message += ex_message
        enemy_action_message = ex_message
        did_enemy_act = True

        if player.total_hp_battle <= 0:
            player.death_count += 1
            if player.death_count >= 3:
                request.session['gameover_player_id'] = player.id
            else:
                message = tohome(message, player, request)

    # ターン経過でバフ・デバフを減少
    local_buffs, local_debuffs, local_special_states = decrease_buff_debuff_turns(
        local_buffs,
        local_debuffs,
        local_special_states,
    )
    request.session["buffs"] = local_buffs
    request.session["debuffs"] = local_debuffs
    request.session["special_states"] = local_special_states

    if message:
        message_history.append(message)
        request.session["message_history"] = message_history

    player.save()

    if is_ajax:
        enemy_action_damage = max(0, start_player_hp - player.total_hp_battle)
        enemy_action_type = "skill"
        enemy_effect_type = "none"
        enemy_action_target = None
        if actione:
            effect_type, target = summarize_effects(actione.get("effects", []))
            if effect_type == "attack":
                enemy_effect_type = "damage"
            elif effect_type == "buf":
                enemy_effect_type = "buff"
            elif effect_type == "debuf":
                enemy_effect_type = "debuff"
            elif effect_type == "guaranteed_evasion":
                enemy_effect_type = "evade"
            elif effect_type == "defense":
                enemy_effect_type = "guard"
            enemy_action_target = target
        if enemy_action_message and "回避" in enemy_action_message and enemy_effect_type == "damage":
            enemy_effect_type = "evade"
            enemy_action_damage = 0

        battle_result = {
            'player_first': True,
            'player_hp': player.total_hp_battle,
            'player_max_hp': player.total_max_hp_battle,
            'player_mp': player.mp,
            'player_max_mp': player.max_mp,
            'enemy_hp': enemy.hp if enemy.hp > 0 else 0,
            'enemy_max_hp': enemy.max_hp,
            'battle_ended': False,
            'player_won': False,
            'player_died': False,
            'message': message,
            'buffs': local_buffs,
            'debuffs': local_debuffs,
            'skip_player_animation': True,
            'player_action': {
                'damage': player_action_damage,
                'message': player_action_message,
                'action_type': player_action_type,
                'effect_type': player_effect_type,
                'target': player_action_target,
                'value': player_action_value,
                'is_finisher': False,
                'attack_sound': player_attack_sound,
                'attack_effect': player_attack_effect,
                'target_guarded': False,
            },
            'enemy_action': None if not did_enemy_act else {
                'damage': enemy_action_damage,
                'message': enemy_action_message,
                'action_type': enemy_action_type,
                'effect_type': enemy_effect_type,
                'target': enemy_action_target,
                'value': 0,
                'is_finisher': False,
                'attack_sound': enemy_attack_sound,
                'attack_effect': enemy_attack_effect,
                'target_guarded': enemy_effect_type == "damage" and actionp == "defend",
            },
        }

        if enemy.hp <= 0:
            battle_result['battle_ended'] = True
            battle_result['player_won'] = True
            battle_result['enemy_hp'] = 0
            battle_result['player_action']['is_finisher'] = True

            gained_exp = request.session.get('gained_exp', 0)
            gained_gold = request.session.get('gained_gold', 0)
            old_level = request.session.get('old_level', player.level)

            request.session['battle_won'] = True
            battle_result['gained_exp'] = gained_exp
            battle_result['gained_gold'] = gained_gold
            battle_result['leveled_up'] = (player.level > old_level)
            battle_result['new_level'] = player.level if player.level > old_level else None

        elif player.total_hp_battle <= 0:
            battle_result['battle_ended'] = True
            battle_result['player_died'] = True
            battle_result['player_hp'] = 0
            if player.death_count >= 3:
                battle_result['redirect_url'] = reverse('game:gameover')
            else:
                battle_result['redirect_url'] = reverse('game:battle_start', kwargs={'player_id': player.id})

        return JsonResponse(battle_result)

    if enemy.hp <= 0:
        return render(request, "game/battle.html", render_battle_screen(
            message,
            **render_kwargs,
            enemy_override=None,
            gained_exp=gained_exp,
            existLevel=existLevel,
            gained_gold=gained_gold,
        ))
    return render(request, "game/battle.html", render_battle_screen(message, **render_kwargs))
