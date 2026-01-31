"""
戦闘関連のview関数

戦闘画面の表示と戦闘ロジックの処理を担当します。
"""
import json
import random
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import JsonResponse
from ..models import Player, Enemy, Stage, PlayerInventory, PlayerQuest
from ..skills import ENEMY_SKILLS, PLAYER_SKILLS
from .utils import (
    get_player_from_request,
    select_new_enemy,
    level_up_player,
    initialize_player_quests,
    decrease_buff_debuff_turns,
    _get_score_rates,
)


def _get_stat_multiplier(buffs, debuffs, target, stat):
    buff = buffs.get(target, {}).get(stat, {}).get("multiplier", 1.0)
    debuff = debuffs.get(target, {}).get(stat, {}).get("multiplier", 1.0)
    return buff * debuff


def _get_effective_stat(base_value, buffs, debuffs, target, stat):
    return base_value * _get_stat_multiplier(buffs, debuffs, target, stat)


def _get_stage_or_first(stage_id):
    try:
        return Stage.objects.get(id=stage_id) if stage_id else Stage.objects.first()
    except Stage.DoesNotExist:
        return Stage.objects.first()


def _resolve_stage_from_request(request):
    stage_id = request.GET.get('stage_id') or request.session.get('stage_id')
    stage = _get_stage_or_first(stage_id)
    request.session['stage_id'] = stage.id if stage else None
    return stage


def _reset_battle_session(request, clear_enemy_id=False):
    if clear_enemy_id:
        request.session.pop('enemy_id', None)
    request.session["message_history"] = []
    request.session["buffs"] = {}
    request.session["debuffs"] = {}
    request.session["special_states"] = {}


def _get_player_skills_and_items(player):
    player_skills = PLAYER_SKILLS.get(player.job, [])
    for skill in player_skills:
        if 'is_action' not in skill:
            skill['is_action'] = False
    player_items = PlayerInventory.objects.filter(
        player=player,
        quantity__gt=0
    ).select_related('item')
    return player_skills, player_items


def battle_start(request, player_id, enemy_id=None):
    """
    戦闘開始画面（ホーム画面）を表示
    
    プレイヤーのステータス表示、休む機能、ステータスポイント配分を担当します。
    """
    player = get_player_from_request(request, player_id)
    if not player:
        return redirect('game:start')
    
    # プレイヤーのHPが0以下の場合、最大HPに回復
    if player.total_hp_battle <= 0:
        player.hp = player.max_hp  # 素のHPを最大値に戻す
        player.update_battle_stats()  # 戦闘用ステータスを更新
        player.save()
        
        # 敗北時にショップのセッション購入履歴をクリアし、在庫をリセット
        request.session['session_purchased_items'] = []
        request.session['reset_shop'] = True
    
    # 戦闘回数をカウント(セッションで管理)
    battle_count = request.session.get('battle_count', 0)
    
    # 3回戦闘終了後にショップのセッション購入履歴をクリアし、在庫をリセット
    if battle_count >= 3:
        request.session['session_purchased_items'] = []
        request.session['reset_shop'] = True
        request.session['battle_count'] = 0

    # 戦闘終了後にセッションをクリア
    if 'enemy_id' in request.session:
        del request.session['enemy_id']
    if 'stage_id' in request.session:
        del request.session['stage_id']
    request.session['message_history'] = []
    request.session['buffs'] = {}
    request.session['debuffs'] = {}

    exp_percent = int(player.exp / player.next_exp * 100) if player.next_exp > 0 else 0

    continue_count = 2 - player.death_count

    if request.method == 'POST':
        # 休む機能の処理
        action = request.POST.get('action')
        if action == 'rest':
            # 休むペナルティ：次のレベルまでの経験値の5%を減少
            exp_penalty = int(player.next_exp * 0.05)
            actual_exp_penalty = min(exp_penalty, player.exp)
            
            player.exp = max(0, player.exp - exp_penalty)
            player.hp = player.max_hp  # 素のHPを最大値に戻す
            player.mp = player.max_mp  # SPも最大値に戻す
            player.save()
            return redirect('game:battle_start', player_id=player.id)

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
            return redirect('game:battle_start', player_id=player.id)

    return render(request, 'game/battle_start.html', {
        "player": player, 
        "exp_percent": exp_percent, 
        "continue_count": continue_count,
        "is_guest": player.is_guest,
    })


def action_skill_click(request, player_id, enemy_id):
    """
    アクション特技のクリック時ダメージ処理
    
    AJAXリクエストで連続クリック時のダメージを計算し、敵のHPを減らします。
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)
    
    player = get_player_from_request(request, player_id)
    if not player:
        return JsonResponse({'error': 'Player not found'}, status=404)
    
    try:
        enemy = Enemy.objects.get(id=enemy_id)
    except Enemy.DoesNotExist:
        return JsonResponse({'error': 'Enemy not found'}, status=404)
    
    # アクションモードのデータを取得
    action_data = request.session.get('action_mode')
    if not action_data:
        return JsonResponse({'error': 'No action mode'}, status=400)
    
    # バフ・デバフを取得
    buffs = request.session.get("buffs", {})
    debuffs = request.session.get("debuffs", {})
    
    # ダメージ計算（通常攻撃と同じ計算式）
    multiplier = action_data.get('multiplier', 1.0)
    if request.body:
        try:
            body = json.loads(request.body.decode('utf-8'))
        except (ValueError, json.JSONDecodeError):
            body = {}
        timing_multiplier = body.get('timing_multiplier')
        if timing_multiplier is not None:
            try:
                multiplier = float(timing_multiplier)
            except (TypeError, ValueError):
                pass
    
    # プレイヤーの攻撃力（バフ・デバフ適用）
    effective_atk = _get_effective_stat(player.total_atk_battle, buffs, debuffs, "player", "atk")
    
    # 敵の防御力（バフ・デバフ適用）
    effective_def = _get_effective_stat(enemy.defense, buffs, debuffs, "enemy", "def")
    # 通常攻撃と同じ軽減
    effective_def = effective_def // 3
    
    # ダメージ計算
    base_damage = max(1, effective_atk - effective_def)
    damage_variance = random.randint(0, 3)
    damage = max(int(base_damage * multiplier) + damage_variance, 1)
    
    # 敵のHPを減らす
    enemy.hp = max(0, enemy.hp - damage)
    enemy.save()
    
    # 累積ダメージをセッションに保存
    total_damage = request.session.get('action_total_damage', 0)
    total_damage += damage
    request.session['action_total_damage'] = total_damage
    
    # 敵のHP割合を計算
    enemy_hp_percent = int((enemy.hp / enemy.max_hp) * 100) if enemy.max_hp > 0 else 0
    
    return JsonResponse({
        'damage': damage,
        'enemy_hp': enemy.hp,
        'enemy_max_hp': enemy.max_hp,
        'enemy_hp_percent': enemy_hp_percent,
        'enemy_defeated': enemy.hp <= 0
    })


def action_skill_end(request, player_id, enemy_id):
    """
    アクション特技終了処理
    
    アクションモード終了後、敵のターンを実行するか勝利処理を行います。
    """
    if request.method != 'POST':
        return redirect('game:battle', player_id=player_id, enemy_id=enemy_id)
    
    player = get_player_from_request(request, player_id)
    if not player:
        return redirect('game:start')
    
    try:
        enemy = Enemy.objects.get(id=enemy_id)
    except Enemy.DoesNotExist:
        return redirect('game:battle_start', player_id=player_id)
    
    # セッションからaction_modeを削除
    action_data = request.session.pop('action_mode', None)
    if not action_data:
        return redirect('game:battle', player_id=player_id, enemy_id=enemy_id)
    
    action_type = action_data.get('action_type', 'spam')
    timing_result = request.POST.get('timing_result')
    
    # click_countと累積ダメージを取得
    click_count = int(request.POST.get('click_count', 0))
    total_damage = request.session.pop('action_total_damage', 0)
    
    # メッセージを作成
    message = f"{player.name}の{action_data['skill_name']}！\n"
    if action_type == 'timing' and timing_result == 'fail':
        message += "失敗してしまった！\n"
    else:
        message += f"{click_count}回の連続攻撃！ 合計{total_damage}ダメージ！\n"
    
    # 敵のHPチェック（既に倒されている場合は勝利処理へ）
    if enemy.hp <= 0:
        # 敵が倒された場合、勝利処理のフラグを立てる
        request.session['after_action_skill_win'] = True
        request.session['action_skill_message'] = message
        return redirect('game:battle', player_id=player_id, enemy_id=enemy_id)
    
    # 敵が生きている場合、敵のターンを実行
    request.session['after_action_skill'] = True
    request.session['action_skill_message'] = message
    
    return redirect('game:battle', player_id=player_id, enemy_id=enemy_id)


def battle(request, player_id, enemy_id=None):
    """
    戦闘画面のメイン処理
    
    プレイヤーと敵の戦闘を処理します。攻撃、防御、スキル、アイテム使用、逃走などの
    すべての戦闘アクションを担当します。AJAX対応でリアルタイムな戦闘アニメーションを
    実現します。
    """
    try:
        player = get_player_from_request(request, player_id)
    except Player.DoesNotExist:
        # 既にプレイヤーが削除済み（ゲームオーバー後など）の場合は安全に遷移
        if request.session.get('gameover_player_id'):
            return redirect('game:gameover')
        return redirect('game:start')
    
    if not player:
        if request.session.get('gameover_player_id'):
            return redirect('game:gameover')
        return redirect('game:start')
    
    def apply_levelup_recovery_if_needed(message=""):
        if request.session.pop('pending_levelup_recovery', False):
            player.hp = player.max_hp
            player.mp = player.max_mp
            player.update_battle_stats()
            player.save()
            message += "HPとSPが全回復した！\n"
        return message

    # AJAXで勝利した後のリロード時の処理
    if request.session.get('battle_won'):
        gained_exp = request.session.pop('gained_exp', 0)
        gained_gold = request.session.pop('gained_gold', 0)
        old_level = request.session.pop('old_level', player.level)
        request.session.pop('battle_won')
        
        # セッションをクリア
        _reset_battle_session(request, clear_enemy_id=True)
        
        # ステージを取得
        stage = _get_stage_or_first(request.session.get('stage_id'))
        
        # 勝利画面を表示
        player_skills, player_items = _get_player_skills_and_items(player)
        
        victory_message = f"勝利！\n経験値を{gained_exp}ゲットした！\n{gained_gold}Gゲットした！\n"
        victory_message = apply_levelup_recovery_if_needed(victory_message)
        return render(request, "game/battle.html", {
            "player": player,
            "enemy": None,
            "message": victory_message,
            "message_history": [],
            "player_skills": player_skills,
            "player_items": player_items,
            "stage": stage,
            "player_hp_percent": 100,
            "player_sp_percent": 100,
            "enemy_hp_percent": 0,
            "gained_exp": gained_exp,
            "gained_gold": gained_gold,
            "existLevel": old_level,
        })
    
    # ステージIDを取得（GETパラメータまたはセッション）
    stage = _resolve_stage_from_request(request)
    
    enemy_id = request.session.get("enemy_id")
    
    # 新しい戦闘開始時のみ敵を選択（stage_idがGETパラメータにある場合、またはenemy_idが存在しない場合）
    if (request.GET.get('stage_id') or not enemy_id) and not enemy_id:
        enemy = select_new_enemy(player, stage, request)
        
        if not enemy:
            # 敵が1体も存在しない場合はエラー
            return render(request, "game/battle.html", {
                "player": player,
                "enemy": None,
                "message": "敵が存在しません。add_enemies.pyを実行してください。",
                "message_history": [],
                "player_skills": PLAYER_SKILLS.get(player.job, []),
                "player_items": [],
                "stage": stage,
                "player_hp_percent": 100,
                "player_sp_percent": 100,
                "enemy_hp_percent": 0,
            })
        
        enemy_id = enemy.id
        
        # 戦闘用ステータスを更新（装備ボーナス込み）
        player.update_battle_stats()
        player.save()
        
        # 新しい戦闘開始時にメッセージ履歴をクリア
        _reset_battle_session(request)
    else:
        try:
            enemy = Enemy.objects.get(id=enemy_id)
        except Enemy.DoesNotExist:
            return redirect('game:battle_start', player_id=player.id)
    
    message = ""
    
    # メッセージ履歴を取得（累積表示用）
    message_history = request.session.get("message_history", [])

    buffs = request.session.get("buffs", {})
    debuffs = request.session.get("debuffs", {})
    special_states = request.session.get("special_states", {})  # 特殊状態（確定回避など）
    
    # プレイヤーのスキル/アイテムを取得
    player_skills, player_items = _get_player_skills_and_items(player)
    
    # 【表示用ステータス】戦闘用ステータス + バフ×デバフ適用
    # プレイヤー（total_*_battleフィールドを使用）
    showplayer_atk = int(_get_effective_stat(player.total_atk_battle, buffs, debuffs, "player", "atk"))
    
    showplayer_def = int(_get_effective_stat(player.total_def_battle, buffs, debuffs, "player", "def"))
    
    showplayer_spd = int(_get_effective_stat(player.total_spd_battle, buffs, debuffs, "player", "spd"))
    
    # 敵（装備なし）
    showenemy_atk = int(_get_effective_stat(enemy.atk, buffs, debuffs, "enemy", "atk"))
    
    showenemy_def = int(_get_effective_stat(enemy.defense, buffs, debuffs, "enemy", "def"))
    
    showenemy_spd = int(_get_effective_stat(enemy.spd, buffs, debuffs, "enemy", "spd"))

    # センチネル値（引数が渡されたかどうかを判定するため）
    _ENEMY_DEFAULT = object()
    
    def render_battle_screen(message, enemy_override=_ENEMY_DEFAULT, **kwargs):
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

    def tohome(message):
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
    
    def win(message):
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
        message, leveled_up = level_up_player(player, message)
        if leveled_up:
            request.session['pending_levelup_recovery'] = True

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
    
    def calculate_player_attack(multiplier=1.0, damage_variance=(-1, 2)):
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
    
    def playerAction(message, action, special, actione):
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
                    damage = calculate_player_attack()
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
            
            # SP不足チェック
            if player.mp < skill_cost:
                message = "しかしSPが足りない！"
                return message, False, action_result
            
            # アクション特技の場合は特別な処理
            if is_action_skill:
                player.mp -= skill_cost
                player.save()
                # アクションモードであることをセッションに保存
                base_multiplier = skill_data["effects"][0].get("multiplier", 1.0)
                request.session['action_mode'] = {
                    'skill_name': skill_name,
                    'skill_data': skill_data,
                    'action_type': skill_data.get("action_type", "spam"),
                    'base_multiplier': base_multiplier,
                    'multiplier': base_multiplier,
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
                multiplier = effect.get("multiplier", 1.0)
                stat = effect.get("stat", None)
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

    def enemyAction(message, enemy, player, buffs, debuffs, actionp, actione):     
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

    def spdcheck(actionp, actione):
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

    def escape(message):
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
    
    # アクション特技終了後の勝利処理
    if request.method == 'GET' and request.session.get('after_action_skill_win'):
        message = request.session.pop('action_skill_message', '')
        request.session.pop('after_action_skill_win')
        
        # 勝利処理
        message, gained_exp, gained_gold, existLevel = win(message)
        message = apply_levelup_recovery_if_needed(message)
        return render(request, "game/battle.html", render_battle_screen(message, enemy_override=None, gained_exp=gained_exp, existLevel=existLevel, gained_gold=gained_gold))
    
    # アクション特技終了後の処理（敵が生きている場合）
    if request.method == 'GET' and request.session.get('after_action_skill'):
        message = request.session.pop('action_skill_message', '')
        request.session.pop('after_action_skill')
        
        # 敵のターンを実行
        actione = choose_enemyAction(enemy, player, buffs, debuffs)
        ex_message, buffs, debuffs = enemyAction(message, enemy, player, buffs, debuffs, None, actione)
        message += ex_message
        
        # セッションに保存
        request.session["buffs"] = buffs
        request.session["debuffs"] = debuffs
        
        # プレイヤーが倒れたかチェック
        if player.total_hp_battle <= 0:
            player.death_count += 1
            if player.death_count >= 3:
                request.session['gameover_player_id'] = player.id
                return redirect('game:gameover')
            else:
                message = tohome(message)
                return render(request, "game/battle.html", render_battle_screen(message, redirect_after=True, redirect_url="battle_start", recovering=True))
        
        # ターン経過でバフ・デバフを減少
        buffs, debuffs, special_states = decrease_buff_debuff_turns(buffs, debuffs, special_states)
        
        request.session["buffs"] = buffs
        request.session["debuffs"] = debuffs
        request.session["special_states"] = special_states
        
        # メッセージ履歴に追加
        message_history.append(message)
        request.session["message_history"] = message_history
        
        # 敵が倒されたかチェック
        if enemy.hp <= 0:
            message, gained_exp, gained_gold, existLevel = win(message)
            message = apply_levelup_recovery_if_needed(message)
            return render(request, "game/battle.html", render_battle_screen(message, enemy_override=None, gained_exp=gained_exp, existLevel=existLevel, gained_gold=gained_gold))
        
        # 戦闘を続行
        return render(request, "game/battle.html", render_battle_screen(message))

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

    if request.method == 'POST':
        # AJAX判定
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        start_player_hp = player.total_hp_battle
        start_player_mp = player.mp
        start_enemy_hp = enemy.hp
        did_enemy_act = False
        player_action_message = ""
        enemy_action_message = ""
        used_item = None
        item_effect_type = None
        item_effect_value = 0
        item_message = ""
        player_attack_sound = player.weapon.attack_sound.url if player.weapon and player.weapon.attack_sound else ""
        player_attack_effect = player.weapon.attack_effect.url if player.weapon and player.weapon.attack_effect else ""
        enemy_attack_sound = enemy.attack_sound.url if enemy and enemy.attack_sound else ""
        enemy_attack_effect = enemy.attack_effect.url if enemy and enemy.attack_effect else ""
        
        actionp = request.POST.get('action')
        special = request.POST.get('special')
        use_item_id = request.POST.get('use_item')

        if special:
            player_skills_local = PLAYER_SKILLS.get(player.job, [])
            try:
                skill_index = int(special.replace('skill', '')) - 1
            except ValueError:
                skill_index = -1

            if 0 <= skill_index < len(player_skills_local):
                skill_cost = player_skills_local[skill_index].get("cost", 0)
                if player.mp < skill_cost:
                    message = "しかしSPが足りない！"
                    if is_ajax:
                        return JsonResponse({'error': message}, status=200)
                    return render(request, "game/battle.html", render_battle_screen(message))
        
        # デバッグ用：kキーでゲームオーバー
        if actionp == 'debug_gameover':
            player.death_count = 3  # 完全敗北状態にする
            player.save()
            request.session['gameover_player_id'] = player.id
            return redirect('game:gameover')
        
        # アイテム使用処理
        if use_item_id:
            try:
                item_id = int(use_item_id)
                inventory_item = PlayerInventory.objects.get(player=player, item_id=item_id, quantity__gt=0)
                item = inventory_item.item
                
                # アイテムの効果を適用
                if item.target == 'hp':
                    old_hp = player.total_hp_battle
                    player.total_hp_battle = min(player.total_hp_battle + item.effect_amount, player.total_max_hp_battle)
                    actual_recovery = player.total_hp_battle - old_hp
                    
                    # 素のHPも同時に更新
                    weapon_bonus = player.weapon.hp_bonus if player.weapon else 0
                    armor_bonus = player.armor.hp_bonus if player.armor else 0
                    player.hp = max(0, player.total_hp_battle - weapon_bonus - armor_bonus)
                    
                    message = f"{player.name}は{item.name}を使った！\nHPが{actual_recovery}回復した！\n"
                    item_message = message
                    used_item = item
                    item_effect_type = "heal"
                    item_effect_value = actual_recovery
                elif item.target == 'mp':
                    old_mp = player.mp
                    player.mp = min(player.mp + item.effect_amount, player.max_mp)
                    actual_recovery = player.mp - old_mp
                    message = f"{player.name}は{item.name}を使った！\nSPが{actual_recovery}回復した！\n"
                    item_message = message
                    used_item = item
                    item_effect_type = "mp"
                    item_effect_value = actual_recovery
                
                # アイテムを1つ消費
                inventory_item.quantity -= 1
                inventory_item.save()
                player.save()
                
                # アイテム使用後は敵のターン（必ず先手だがターン経過）
                actione = choose_enemyAction(enemy, player, buffs, debuffs)
                ex_message, buffs, debuffs = enemyAction(message, enemy, player, buffs, debuffs, 'item', actione)
                request.session["buffs"] = buffs
                request.session["debuffs"] = debuffs
                message += ex_message
                enemy_action_message = ex_message
                did_enemy_act = True
                
                # メッセージ履歴に追加
                message_history.append(message)
                request.session["message_history"] = message_history
                
                # プレイヤーが倒れたかチェック
                if player.total_hp_battle <= 0:
                    player.death_count += 1
                    if player.death_count >= 3:
                        request.session['gameover_player_id'] = player.id
                        return redirect('game:gameover')
                    else:
                        message = tohome(message)
                        return render(request, "game/battle.html", render_battle_screen(message, redirect_after=True))
                
                # ターン経過でバフ・デバフを減少
                buffs, debuffs, special_states = decrease_buff_debuff_turns(buffs, debuffs, special_states)
                request.session["buffs"] = buffs
                request.session["debuffs"] = debuffs
                request.session["special_states"] = special_states
                
                # 通常の戦闘画面に戻る
                if is_ajax:
                    # アイテム使用は必ず先攻
                    player_first = True
                    player_action_damage = 0
                    enemy_action_damage = max(0, start_player_hp - player.total_hp_battle)
                    enemy_effect_type = "damage"
                    if enemy_action_message and "回避" in enemy_action_message:
                        enemy_effect_type = "evade"
                        enemy_action_damage = 0
                    battle_result = {
                        'player_first': player_first,
                        'player_hp': player.total_hp_battle,
                        'player_max_hp': player.total_max_hp_battle,
                        'player_mp': player.mp,
                        'player_max_mp': player.max_mp,
                        'enemy_hp': max(enemy.hp, 0),
                        'enemy_max_hp': enemy.max_hp,
                        'battle_ended': False,
                        'player_won': False,
                        'player_died': False,
                        'message': message,
                        'buffs': buffs,
                        'debuffs': debuffs,
                        'player_action': {
                            'damage': player_action_damage,
                            'message': item_message,
                            'action_type': 'item',
                            'effect_type': item_effect_type,
                            'target': 'player',
                            'value': item_effect_value,
                            'is_finisher': False,
                            'attack_sound': "",
                            'attack_effect': "",
                            'target_guarded': False,
                        },
                        'enemy_action': None if not did_enemy_act else {
                            'damage': enemy_action_damage,
                            'message': enemy_action_message,
                            'action_type': 'skill',
                            'effect_type': enemy_effect_type,
                            'target': 'player',
                            'value': 0,
                            'is_finisher': False,
                            'attack_sound': enemy_attack_sound,
                            'attack_effect': enemy_attack_effect,
                            'target_guarded': False,
                        },
                        'item_update': {
                            'item_id': item.id,
                            'quantity': inventory_item.quantity,
                        },
                    }
                    if enemy.hp <= 0:
                        battle_result['battle_ended'] = True
                        battle_result['player_won'] = True
                        battle_result['enemy_hp'] = 0
                        request.session['battle_won'] = True
                    elif player.total_hp_battle <= 0:
                        battle_result['battle_ended'] = True
                        battle_result['player_died'] = True
                        battle_result['player_hp'] = 0
                    return JsonResponse(battle_result)

                return render(request, "game/battle.html", render_battle_screen(message))
            except (PlayerInventory.DoesNotExist, ValueError):
                pass  # アイテムが存在しない場合は無視
        
        # 逃走処理
        if actionp == 'escape':
            message, escaped, exp_penalty, gold_penalty = escape(message)
            if escaped:
                # 逃走成功
                return render(request, "game/battle.html", render_battle_screen(message, enemy_override=None, escaped=True, exp_penalty=exp_penalty, gold_penalty=gold_penalty))
            else:
                # 逃走失敗 - 敵のターンへ
                actione = choose_enemyAction(enemy, player, buffs, debuffs)
                ex_message, buffs, debuffs = enemyAction(message, enemy, player, buffs, debuffs, actionp, actione)
                request.session["buffs"] = buffs
                request.session["debuffs"] = debuffs
                message += ex_message
                
                # メッセージ履歴に追加
                message_history.append(message)
                request.session["message_history"] = message_history
                
                # プレイヤーが倒れたかチェック
                if player.total_hp_battle <= 0:
                    player.death_count += 1
                    if player.death_count >= 3:
                        request.session['gameover_player_id'] = player.id
                        return redirect('game:gameover')
                    else:
                        message = tohome(message)
                        return render(request, "game/battle.html", render_battle_screen(message, redirect_after=True))
                
                # 通常の戦闘画面に戻る
                return render(request, "game/battle.html", render_battle_screen(message))
        
        actione = choose_enemyAction(enemy, player, buffs, debuffs)
        
        special_action_skill = False
        if special:
            player_skills_local = PLAYER_SKILLS.get(player.job, [])
            try:
                skill_index = int(special.replace('skill', '')) - 1
            except ValueError:
                skill_index = -1
            if 0 <= skill_index < len(player_skills_local):
                special_action_skill = player_skills_local[skill_index].get("is_action", False)

        is_player_first = True if special_action_skill else spdcheck(actionp, actione)
        player_action_result = {"damage": 0, "evaded": False}
        if is_player_first:
            ex_message = ""
            message, success, player_action_result = playerAction(message, actionp, special, actione)
            player_action_message = message
            if not success:
                if is_ajax:
                    return JsonResponse({'error': message}, status=200)
                return render(request, "game/battle.html", render_battle_screen(message))
            
            # アクションモードチェック
            if request.session.get('action_mode'):
                action_data = request.session['action_mode']
                return render(request, "game/battle.html", render_battle_screen(message, action_mode=action_data))
            
            if enemy.hp <= 0:
                message, gained_exp, gained_gold, existLevel = win(message)
                if not is_ajax:
                    message = apply_levelup_recovery_if_needed(message)
                    return render(request, "game/battle.html", render_battle_screen(message, enemy_override=None, gained_exp=gained_exp, existLevel=existLevel, gained_gold=gained_gold))
            else:
                ex_message, buffs, debuffs = enemyAction(message, enemy, player, buffs, debuffs, actionp, actione)
                did_enemy_act = True
                enemy_action_message = ex_message
            # セッションに保存
            request.session["buffs"] = buffs
            request.session["debuffs"] = debuffs
            if ex_message:
                message += ex_message    
            
            # プレイヤーの総HPが0以下になったかチェック
            # プレイヤーが倒れたかチェック
            if player.total_hp_battle <= 0:
                player.death_count += 1
                if player.death_count >= 3:
                    request.session['gameover_player_id'] = player.id
                    if not is_ajax:
                        return redirect('game:gameover')
                else:
                    message = tohome(message)
                    if not is_ajax:
                        return render(request, "game/battle.html", render_battle_screen(message, redirect_after=True, redirect_url="battle_start", recovering=True))          
        else:
            message, buffs, debuffs = enemyAction(message, enemy, player, buffs, debuffs, actionp, actione)
            enemy_action_message = message
            did_enemy_act = True
            # セッションに保存
            request.session["buffs"] = buffs
            request.session["debuffs"] = debuffs
            
            # プレイヤーの総HPが0以下になったかチェック
            if player.total_hp_battle <= 0:
                player.death_count += 1
                if player.death_count >= 3:
                    request.session['gameover_player_id'] = player.id
                    redirect_url = reverse('game:gameover')
                    if not is_ajax:
                        return redirect('game:gameover')
                else:
                    message = tohome(message)
                    redirect_url = reverse('game:battle_start', kwargs={'player_id': player.id})
                    if not is_ajax:
                        return render(request, "game/battle.html", render_battle_screen(message, redirect_after=True, redirect_url="battle_start", recovering=True))

                if is_ajax:
                    player.save()
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
                        'player_first': False,
                        'player_hp': 0,
                        'player_max_hp': player.total_max_hp_battle,
                        'player_mp': player.mp,
                        'player_max_mp': player.max_mp,
                        'enemy_hp': enemy.hp if enemy.hp > 0 else 0,
                        'enemy_max_hp': enemy.max_hp,
                        'battle_ended': True,
                        'player_won': False,
                        'player_died': True,
                        'message': message,
                        'buffs': buffs,
                        'debuffs': debuffs,
                        'redirect_url': redirect_url,
                        'player_action': None,
                        'enemy_action': {
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
                    return JsonResponse(battle_result)
            
            ex_message, success, player_action_result = playerAction(message, actionp, special, actione)
            player_action_message = ex_message
            message += ex_message
            if not success:
                if is_ajax:
                    return JsonResponse({'error': message}, status=200)
                return render(request, "game/battle.html", render_battle_screen(message))
            
            # アクションモードチェック
            if request.session.get('action_mode'):
                action_data = request.session['action_mode']
                return render(request, "game/battle.html", render_battle_screen(message, action_mode=action_data))
            
            if enemy.hp <= 0:
                message, gained_exp, gained_gold, existLevel = win(message)
                if not is_ajax:
                    message = apply_levelup_recovery_if_needed(message)
                    return render(request, "game/battle.html", render_battle_screen(message, enemy_override=None, gained_exp=gained_exp, existLevel=existLevel, gained_gold=gained_gold))
          

        # ターン経過でバフを減少
        buffs, debuffs, special_states = decrease_buff_debuff_turns(buffs, debuffs, special_states)

        request.session["buffs"] = buffs
        request.session["debuffs"] = debuffs
        request.session["special_states"] = special_states
        
        # 表示用ステータスを再計算【装備ボーナス込み + バフ×デバフ適用】
        # プレイヤーのステータス（total_atk, total_def, total_spdは装備込み）
        showplayer_atk = int(_get_effective_stat(player.total_atk_battle, buffs, debuffs, "player", "atk"))
        
        showplayer_def = int(_get_effective_stat(player.total_def_battle, buffs, debuffs, "player", "def"))
        
        showplayer_spd = int(_get_effective_stat(player.total_spd_battle, buffs, debuffs, "player", "spd"))
        
        # 敵のステータス（装備なし）
        showenemy_atk = int(_get_effective_stat(enemy.atk, buffs, debuffs, "enemy", "atk"))
        
        showenemy_def = int(_get_effective_stat(enemy.defense, buffs, debuffs, "enemy", "def"))
        
        showenemy_spd = int(_get_effective_stat(enemy.spd, buffs, debuffs, "enemy", "spd"))

        # メッセージを履歴に追加
        if message:
            message_history.append(message)
            request.session["message_history"] = message_history

        player.save()
        
        # AJAX対応：JSON形式で戦闘結果を返す
        if is_ajax:
            # 先攻判定
            player_first = is_player_first
            player_action_damage = max(player_action_result.get("damage", 0), 0)
            enemy_action_damage = max(0, start_player_hp - player.total_hp_battle)

            # プレイヤー行動の種別・効果
            player_action_type = None
            player_effect_type = "none"
            player_action_target = None
            player_action_value = 0

            if use_item_id and used_item:
                player_action_type = "item"
                player_action_target = "player"
                player_effect_type = item_effect_type or "none"
                player_action_value = item_effect_value
            elif special:
                player_action_type = "skill"
                try:
                    skill_index = int(special.replace('skill', '')) - 1
                    if 0 <= skill_index < len(player_skills):
                        skill_data = player_skills[skill_index]
                        effect_type, target = summarize_effects(skill_data.get("effects", []))
                        if effect_type == "attack":
                            player_effect_type = "damage"
                        elif effect_type == "buf":
                            player_effect_type = "buff"
                        elif effect_type == "debuf":
                            player_effect_type = "debuff"
                        elif effect_type == "guaranteed_evasion":
                            player_effect_type = "evade"
                        elif effect_type == "defense":
                            player_effect_type = "guard"
                        player_action_target = target
                except ValueError:
                    pass
            else:
                if actionp == 'attack':
                    player_action_type = "attack"
                    player_effect_type = "damage"
                    player_action_target = "enemy"
                elif actionp == 'defend':
                    player_action_type = "defend"
                    player_effect_type = "guard"
                    player_action_target = "player"
            if player_action_result.get("evaded") and player_action_type in ("attack", "skill"):
                player_effect_type = "evade"

            # 敵行動の種別・効果
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

            player_target_guarded = player_effect_type == "damage" and player_action_target == "enemy" and is_defense_action(actione)
            enemy_target_guarded = enemy_effect_type == "damage" and actionp == "defend"
            
            # 戦闘結果を構築
            battle_result = {
                'player_first': player_first,
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
                'buffs': buffs,
                'debuffs': debuffs,
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
                    'target_guarded': player_target_guarded,
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
                    'target_guarded': enemy_target_guarded,
                },
            }
            
            # 勝利判定
            if enemy.hp <= 0:
                battle_result['battle_ended'] = True
                battle_result['player_won'] = True
                battle_result['enemy_hp'] = 0
                battle_result['player_action']['is_finisher'] = True
                
                # 勝利情報をセッションに保存（リロード時に使用）
                gained_exp = request.session.get('gained_exp', 0)
                gained_gold = request.session.get('gained_gold', 0)
                old_level = request.session.get('old_level', player.level)
                
                request.session['battle_won'] = True
                battle_result['gained_exp'] = gained_exp
                battle_result['gained_gold'] = gained_gold
                battle_result['leveled_up'] = (player.level > old_level)
                battle_result['new_level'] = player.level if player.level > old_level else None
            
            # 敗北判定
            elif player.total_hp_battle <= 0:
                battle_result['battle_ended'] = True
                battle_result['player_died'] = True
                battle_result['player_hp'] = 0
                if player.death_count >= 3:
                    battle_result['redirect_url'] = reverse('game:gameover')
                else:
                    battle_result['redirect_url'] = reverse('game:battle_start', kwargs={'player_id': player.id})
            
            return JsonResponse(battle_result)
        
        return render(request, "game/battle.html", render_battle_screen(message))
    
    
    return render(request, "game/battle.html", render_battle_screen(message))
