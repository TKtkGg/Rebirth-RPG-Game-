"""
戦闘関連のview関数

戦闘画面の表示と戦闘ロジックの処理を担当します。
"""
import json
import random
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import JsonResponse
from ..models import Player, Enemy, PlayerInventory, Item
from ..skills import PLAYER_SKILLS
from .utils import get_player_from_request, select_new_enemy, decrease_buff_debuff_turns
from .battle_helpers import (
    _get_effective_stat,
    _get_stage_or_first,
    _resolve_stage_from_request,
    _reset_battle_session,
    _get_player_skills_and_items,
)
from .battle_internal_functions import (
    render_battle_screen,
    tohome,
    win,
    playerAction,
    choose_enemyAction,
    enemyAction,
    is_defense_action,
    spdcheck,
    escape,
    summarize_effects,
    handle_action_mode_end,
)

from ..api_serializers import player_to_api_dict, enemy_to_api_dict, stage_to_api_dict, item_to_api_dict, player_inventory_to_api_dict

def battle_start_get(request, player_id):
    player = get_player_from_request(request, player_id)
    if not player:
        return JsonResponse({"error": "Player not found"}, status=404)
    
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

    return exp_percent, continue_count


def rest_at_home(player):
    # 休むペナルティ：次のレベルまでの経験値の5%を減少
    exp_penalty = int(player.next_exp * 0.05)
    actual_exp_penalty = min(exp_penalty, player.exp)
    
    player.exp = max(0, player.exp - exp_penalty)
    player.hp = player.max_hp  # 素のHPを最大値に戻す
    player.mp = player.max_mp  # SPも最大値に戻す
    player.update_battle_stats()
    player.save()

    return actual_exp_penalty

def allocate_stat_points(player, stat):
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
    else:
        return
    player.stat_points -= 1
    player.update_battle_stats()
    player.save()


def battle_start(request, player_id, enemy_id=None):
    """
    戦闘開始画面（ホーム画面）を表示
    
    プレイヤーのステータス表示、休む機能、ステータスポイント配分を担当します。
    """
    player = get_player_from_request(request, player_id)
    if not player:
        return redirect('game:start')
    
    exp_percent, continue_count = battle_start_get(request, player_id)

    if request.method == 'POST':
        # 休む機能の処理
        action = request.POST.get('action')
        if action == 'rest':
            actual_exp_penalty = rest_at_home(player)
            return redirect('game:battle_start', player_id=player.id)

        # ステータスポイント配分の処理
        stat = request.POST.get('stat')
        if stat and player.stat_points > 0:
            allocate_stat_points(player, stat)
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

    render_kwargs = {
        "player": player,
        "enemy": enemy,
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
    }

    # アクションモード中ならその画面を優先表示
    if request.method == 'GET' and request.session.get('action_mode'):
        action_data = request.session['action_mode']
        return render(request, "game/battle.html", render_battle_screen(message, **render_kwargs, action_mode=action_data))

    # アクション特技終了後の勝利処理
    if request.method == 'GET' and request.session.get('after_action_skill_win'):
        message = request.session.pop('action_skill_message', '')
        request.session.pop('after_action_skill_win')
        
        # 勝利処理
        message, gained_exp, gained_gold, existLevel = win(message, player, enemy, request)
        return render(request, "game/battle.html", render_battle_screen(message, **render_kwargs, enemy_override=None, gained_exp=gained_exp, existLevel=existLevel, gained_gold=gained_gold))
    
    # アクション特技終了後の処理（敵が生きている場合）
    if request.method == 'GET' and request.session.get('after_action_skill'):
        message = request.session.pop('action_skill_message', '')
        request.session.pop('after_action_skill')
        
        # 敵のターンを実行
        actione = choose_enemyAction(enemy, player, buffs, debuffs)
        ex_message, buffs, debuffs = enemyAction(message, enemy, player, buffs, debuffs, None, actione, special_states)
        message += ex_message
        
        # セッションに保存
        request.session["buffs"] = buffs
        request.session["debuffs"] = debuffs
        render_kwargs["buffs"] = buffs
        render_kwargs["debuffs"] = debuffs
        
        # プレイヤーが倒れたかチェック
        if player.total_hp_battle <= 0:
            player.death_count += 1
            if player.death_count >= 3:
                request.session['gameover_player_id'] = player.id
                return redirect('game:gameover')
            else:
                message = tohome(message, player, request)
                return render(request, "game/battle.html", render_battle_screen(message, **render_kwargs, redirect_after=True, redirect_url="battle_start", recovering=True))
        
        # ターン経過でバフ・デバフを減少
        buffs, debuffs, special_states = decrease_buff_debuff_turns(buffs, debuffs, special_states)
        
        request.session["buffs"] = buffs
        request.session["debuffs"] = debuffs
        request.session["special_states"] = special_states
        render_kwargs["buffs"] = buffs
        render_kwargs["debuffs"] = debuffs
        
        # メッセージ履歴に追加
        message_history.append(message)
        request.session["message_history"] = message_history
        
        # 敵が倒されたかチェック
        if enemy.hp <= 0:
            message, gained_exp, gained_gold, existLevel = win(message, player, enemy, request)
            return render(request, "game/battle.html", render_battle_screen(message, **render_kwargs, enemy_override=None, gained_exp=gained_exp, existLevel=existLevel, gained_gold=gained_gold))
        
        # 戦闘を続行
        return render(request, "game/battle.html", render_battle_screen(message, **render_kwargs))

    if request.method == 'POST':
        # AJAX判定
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        start_player_hp = player.total_hp_battle
        start_player_mp = player.mp
        start_enemy_hp = enemy.hp
        did_enemy_act = False
        player_action_message = ""
        enemy_action_message = ""
        enemy_action_damage = 0
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
        timing_result = request.POST.get('timing_result')
        
        if not special and timing_result and request.session.get('action_mode'):
            action_mode = request.session.get('action_mode') or {}
            skill_index = action_mode.get('skill_index')
            if isinstance(skill_index, int):
                special = f"skill{skill_index + 1}"

        if special:
            player_skills_local = PLAYER_SKILLS.get(player.job, [])
            try:
                skill_index = int(special.replace('skill', '')) - 1
            except ValueError:
                skill_index = -1

            if 0 <= skill_index < len(player_skills_local):
                skill_data = player_skills_local[skill_index]
                skill_cost = skill_data.get("cost", 0)
                timing_result = request.POST.get('timing_result')
                is_timing_result = skill_data.get("action_type") == "timing" and timing_result is not None
                if not is_timing_result and player.mp < skill_cost:
                    message = "しかしSPが足りない！"
                    if is_ajax:
                        return JsonResponse({'error': message}, status=200)
                    return render(request, "game/battle.html", render_battle_screen(message, **render_kwargs))

        action_mode_response = handle_action_mode_end(
            request=request,
            player=player,
            enemy=enemy,
            buffs=buffs,
            debuffs=debuffs,
            special_states=special_states,
            message_history=message_history,
            timing_result=timing_result,
            start_player_hp=start_player_hp,
            is_ajax=is_ajax,
            player_attack_sound=player_attack_sound,
            player_attack_effect=player_attack_effect,
            enemy_attack_sound=enemy_attack_sound,
            enemy_attack_effect=enemy_attack_effect,
            actionp=actionp,
            render_kwargs=render_kwargs,
        )
        if action_mode_response:
            return action_mode_response
        
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
                player_hp_before_enemy = player.total_hp_battle
                ex_message, buffs, debuffs = enemyAction(message, enemy, player, buffs, debuffs, 'item', actione, special_states)
                enemy_action_damage = max(0, player_hp_before_enemy - player.total_hp_battle)
                request.session["buffs"] = buffs
                request.session["debuffs"] = debuffs
                render_kwargs["buffs"] = buffs
                render_kwargs["debuffs"] = debuffs
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
                        message = tohome(message, player, request)
                        return render(request, "game/battle.html", render_battle_screen(message, **render_kwargs, redirect_after=True))
                
                # ターン経過でバフ・デバフを減少
                buffs, debuffs, special_states = decrease_buff_debuff_turns(buffs, debuffs, special_states)
                request.session["buffs"] = buffs
                request.session["debuffs"] = debuffs
                request.session["special_states"] = special_states
                render_kwargs["buffs"] = buffs
                render_kwargs["debuffs"] = debuffs
                
                # 通常の戦闘画面に戻る
                if is_ajax:
                    # アイテム使用は必ず先攻
                    player_first = True
                    player_action_damage = 0
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
                            'target': enemy_action_target,
                            'value': 0,
                            'is_finisher': False,
                            'attack_sound': enemy_attack_sound,
                            'attack_effect': enemy_attack_effect,
                            'target_guarded': enemy_effect_type == "damage" and actionp == "defend",
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

                return render(request, "game/battle.html", render_battle_screen(message, **render_kwargs))
            except (PlayerInventory.DoesNotExist, ValueError):
                pass  # アイテムが存在しない場合は無視
        
        # 逃走処理
        if actionp == 'escape':
            message, escaped, exp_penalty, gold_penalty = escape(message, player, enemy, request)
            if escaped:
                # 逃走成功
                return render(request, "game/battle.html", render_battle_screen(message, **render_kwargs, enemy_override=None, escaped=True, exp_penalty=exp_penalty, gold_penalty=gold_penalty))
            else:
                # 逃走失敗 - 敵のターンへ
                actione = choose_enemyAction(enemy, player, buffs, debuffs)
                ex_message, buffs, debuffs = enemyAction(message, enemy, player, buffs, debuffs, actionp, actione, special_states)
                request.session["buffs"] = buffs
                request.session["debuffs"] = debuffs
                render_kwargs["buffs"] = buffs
                render_kwargs["debuffs"] = debuffs
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
                        message = tohome(message, player, request)
                        return render(request, "game/battle.html", render_battle_screen(message, **render_kwargs, redirect_after=True))
                
                # 通常の戦闘画面に戻る
                return render(request, "game/battle.html", render_battle_screen(message, **render_kwargs))
        
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

        is_player_first = True if special_action_skill else spdcheck(actionp, actione, player, enemy, buffs, debuffs)
        player_action_result = {"damage": 0, "evaded": False}
        if is_player_first:
            ex_message = ""
            message, success, player_action_result = playerAction(
                message,
                actionp,
                special,
                actione,
                player,
                enemy,
                buffs,
                debuffs,
                special_states,
                request,
            )
            player_action_message = message
            if not success:
                if is_ajax:
                    return JsonResponse({'error': message}, status=200)
                return render(request, "game/battle.html", render_battle_screen(message, **render_kwargs))
            
            # アクションモードチェック
            if request.session.get('action_mode'):
                action_data = request.session['action_mode']
                return render(request, "game/battle.html", render_battle_screen(message, **render_kwargs, action_mode=action_data))
            
            if enemy.hp <= 0:
                message, gained_exp, gained_gold, existLevel = win(message, player, enemy, request)
                if not is_ajax:
                    return render(request, "game/battle.html", render_battle_screen(message, **render_kwargs, enemy_override=None, gained_exp=gained_exp, existLevel=existLevel, gained_gold=gained_gold))
            else:
                player_hp_before_enemy = player.total_hp_battle
                ex_message, buffs, debuffs = enemyAction(message, enemy, player, buffs, debuffs, actionp, actione, special_states)
                enemy_action_damage = max(0, player_hp_before_enemy - player.total_hp_battle)
                did_enemy_act = True
                enemy_action_message = ex_message
            # セッションに保存
            request.session["buffs"] = buffs
            request.session["debuffs"] = debuffs
            render_kwargs["buffs"] = buffs
            render_kwargs["debuffs"] = debuffs
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
                    message = tohome(message, player, request)
                    if not is_ajax:
                        return render(request, "game/battle.html", render_battle_screen(message, **render_kwargs, redirect_after=True, redirect_url="battle_start", recovering=True))          
        else:
            player_hp_before_enemy = player.total_hp_battle
            message, buffs, debuffs = enemyAction(message, enemy, player, buffs, debuffs, actionp, actione, special_states)
            enemy_action_damage = max(0, player_hp_before_enemy - player.total_hp_battle)
            enemy_action_message = message
            did_enemy_act = True
            # セッションに保存
            request.session["buffs"] = buffs
            request.session["debuffs"] = debuffs
            render_kwargs["buffs"] = buffs
            render_kwargs["debuffs"] = debuffs
            
            # プレイヤーの総HPが0以下になったかチェック
            if player.total_hp_battle <= 0:
                player.death_count += 1
                if player.death_count >= 3:
                    request.session['gameover_player_id'] = player.id
                    redirect_url = reverse('game:gameover')
                    if not is_ajax:
                        return redirect('game:gameover')
                else:
                    message = tohome(message, player, request)
                    redirect_url = reverse('game:battle_start', kwargs={'player_id': player.id})
                    if not is_ajax:
                        return render(request, "game/battle.html", render_battle_screen(message, **render_kwargs, redirect_after=True, redirect_url="battle_start", recovering=True))

                if is_ajax:
                    player.save()
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
            
            ex_message, success, player_action_result = playerAction(
                message,
                actionp,
                special,
                actione,
                player,
                enemy,
                buffs,
                debuffs,
                special_states,
                request,
            )
            player_action_message = ex_message
            message += ex_message
            if not success:
                if is_ajax:
                    return JsonResponse({'error': message}, status=200)
                return render(request, "game/battle.html", render_battle_screen(message, **render_kwargs))
            
            # アクションモードチェック
            if request.session.get('action_mode'):
                action_data = request.session['action_mode']
                return render(request, "game/battle.html", render_battle_screen(message, **render_kwargs, action_mode=action_data))
            
            if enemy.hp <= 0:
                message, gained_exp, gained_gold, existLevel = win(message, player, enemy, request)
                if not is_ajax:
                    return render(request, "game/battle.html", render_battle_screen(message, **render_kwargs, enemy_override=None, gained_exp=gained_exp, existLevel=existLevel, gained_gold=gained_gold))
        

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
        render_kwargs["showplayer_atk"] = showplayer_atk
        render_kwargs["showplayer_def"] = showplayer_def
        render_kwargs["showplayer_spd"] = showplayer_spd
        render_kwargs["showenemy_atk"] = showenemy_atk
        render_kwargs["showenemy_def"] = showenemy_def
        render_kwargs["showenemy_spd"] = showenemy_spd

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
                        timing_result = request.POST.get('timing_result')
                        if skill_data.get("action_type") == "timing" and timing_result is not None:
                            player_action_type = "timing"
                            player_action_target = "enemy"
                            player_effect_type = "damage" if timing_result == "success" else "none"
                        else:
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
        
        return render(request, "game/battle.html", render_battle_screen(message, **render_kwargs))
    
    
    return render(request, "game/battle.html", render_battle_screen(message, **render_kwargs))

def build_battle_data(state):
    return {
        "player": player_to_api_dict(state["player"]),
        "enemy": enemy_to_api_dict(state["enemy"]) if state["enemy"] else None,
        "message_history": state["message_history"],
        "showplayer_atk": state["showplayer_atk"],
        "showplayer_def": state["showplayer_def"],
        "showplayer_spd": state["showplayer_spd"],
        "buffs": state["buffs"],
        "showenemy_atk": state["showenemy_atk"],
        "showenemy_def": state["showenemy_def"],
        "showenemy_spd": state["showenemy_spd"],
        "debuffs": state["debuffs"],
        "player_skills": state["player_skills"],
        "player_items": [player_inventory_to_api_dict(item) for item in state["player_items"]],
        "stage": stage_to_api_dict(state["stage"]),
        "player_hp_percent": state["player_hp_percent"],
        "player_sp_percent": state["player_sp_percent"],
        "enemy_hp_percent": state["enemy_hp_percent"],
    }
def build_result_data(result):
    return {
        "gained_exp": result["gained_exp"],
        "gained_gold": result["gained_gold"],
        "existLevel": result["existLevel"],
        "newLevel": result["newLevel"],
        "stage": stage_to_api_dict(result["stage"]),
    } if result else None


def battle_get(request, player_id):
    player = get_player_from_request(request, player_id)
    if not player:
        return {
            "battle": None,
            "event": {
                "type": "error",
                "payload": {
                    "message": "プレイヤーが存在しません。",
                },
            },
        }
    
    # ステージIDを取得（GETパラメータまたはセッション）
    stage = _resolve_stage_from_request(request)
    
    enemy_id = request.session.get("enemy_id")
    
    # 新しい戦闘開始時のみ敵を選択（stage_idがGETパラメータにある場合、またはenemy_idが存在しない場合）
    if (request.GET.get('stage_id') or not enemy_id) and not enemy_id:
        enemy = select_new_enemy(player, stage, request)
        if not enemy:
            # 敵が1体も存在しない場合はエラー
            return {
                "battle": None,
                "event": {
                    "type": "error",
                    "payload": {
                        "message": "敵が存在しません。",
                    },
                },
            }
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
            return {
                "battle": None,
                "event": {
                    "type": "error",
                    "payload": {
                        "message": "enemy_idが存在しません。",
                    },
                },
            }
        
    # メッセージ履歴を取得（累積表示用）
    message_history = request.session.get("message_history", [])

    buffs = request.session.get("buffs", {})
    debuffs = request.session.get("debuffs", {})
    
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

    # HP・SPのゲージ用パーセンテージを計算
    player_hp_percent = int((player.total_hp_battle / player.total_max_hp_battle) * 100) if player.total_max_hp_battle > 0 else 0
    player_sp_percent = int((player.mp / player.max_mp) * 100) if player.max_mp > 0 else 0
    enemy_hp_percent = int((enemy.hp / enemy.max_hp) * 100) if enemy.max_hp > 0 else 0

    full_state = {
        "player": player,
        "enemy": enemy,
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

    return {
        "battle": build_battle_data(full_state),
        "event": None,
    }


def battle_post(request, player_id):
    player = get_player_from_request(request, player_id)
    if not player:
        return {
            "battle": None,
            "event": {
                "type": "error",
                "payload": {
                    "message": "プレイヤーが存在しません。",
                },
            },
        }
    
    # ステージIDを取得（GETパラメータまたはセッション）
    stage = _resolve_stage_from_request(request)

    player_skills, player_items = _get_player_skills_and_items(player)
    
    enemy_id = request.session.get("enemy_id")
    
    # 新しい戦闘開始時のみ敵を選択（stage_idがGETパラメータにある場合、またはenemy_idが存在しない場合）
    if (request.GET.get('stage_id') or not enemy_id) and not enemy_id:
        enemy = select_new_enemy(player, stage, request)
        if not enemy:
            # 敵が1体も存在しない場合はエラー
            return {
                "battle": None,
                "event": {
                    "type": "error",
                    "payload": {
                        "message": "敵が存在しません。",
                    },
                },
            }
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
            return {
                "battle": None,
                "event": {
                    "type": "error",
                    "payload": {
                        "message": "enemy_idが存在しません。",
                    },
                },
            }
    
    message = ""
    
    # メッセージ履歴を取得（累積表示用）
    message_history = request.session.get("message_history", [])

    buffs = request.session.get("buffs", {})
    debuffs = request.session.get("debuffs", {})
    special_states = request.session.get("special_states", {})  # 特殊状態（確定回避など）

    actionp = request.POST.get('action')
    # 逃走処理
    if actionp == 'escape':
        message, escaped, exp_penalty, gold_penalty = escape(message, player, enemy, request)
        if escaped:
            player.save()
            _reset_battle_session(request, clear_enemy_id=True)
            # 逃走成功
            return {
                "battle": None,
                "event": {
                    "type": "escape",
                    "payload": {
                        "message": message,
                        "enemy_override": None,
                        "escaped": True,
                        "exp_penalty": exp_penalty,
                        "gold_penalty": gold_penalty,
                    },
                }
            }
        else:
            # 逃走失敗 - 敵のターンへ
            actione = choose_enemyAction(enemy, player, buffs, debuffs)
            ex_message, buffs, debuffs = enemyAction(message, enemy, player, buffs, debuffs, actionp, actione, special_states)
            request.session["buffs"] = buffs
            request.session["debuffs"] = debuffs
            message += ex_message
            
            # メッセージ履歴に追加
            message_history.append(message)
            request.session["message_history"] = message_history
            player.save()
            # プレイヤーが倒れたかチェック
            if player.total_hp_battle <= 0:
                player.death_count += 1
                player.save()
                _reset_battle_session(request, clear_enemy_id=True)
                if player.death_count >= 3:
                    request.session['gameover_player_id'] = player.id                    
                    return {
                        "battle": None,
                        "event": {
                            "type": "gameover",
                            "payload": {
                                "message": "プレイヤーが倒れました。",
                            },
                        }
                    }
                else:
                    message = tohome(message, player, request)
                    return {
                        "battle": None,
                        "event": {
                            "type": "tohome",
                            "payload": {
                                "message": message,
                                "redirect_after": True,
                                "recovering": True,
                            },  
                        }
                    }
            
            # 表示用ステータスを再計算【装備ボーナス込み + バフ×デバフ適用】
            # プレイヤーのステータス（total_atk, total_def, total_spdは装備込み）
            showplayer_atk = int(_get_effective_stat(player.total_atk_battle, buffs, debuffs, "player", "atk"))
            showplayer_def = int(_get_effective_stat(player.total_def_battle, buffs, debuffs, "player", "def"))
            showplayer_spd = int(_get_effective_stat(player.total_spd_battle, buffs, debuffs, "player", "spd"))
            
            # 敵のステータス（装備なし）
            showenemy_atk = int(_get_effective_stat(enemy.atk, buffs, debuffs, "enemy", "atk"))
            showenemy_def = int(_get_effective_stat(enemy.defense, buffs, debuffs, "enemy", "def"))
            showenemy_spd = int(_get_effective_stat(enemy.spd, buffs, debuffs, "enemy", "spd"))

            state = {
                "player": player,
                "enemy": enemy,
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
                "player_hp_percent": int((player.total_hp_battle / player.total_max_hp_battle) * 100) if player.total_max_hp_battle > 0 else 0,
                "player_sp_percent": int((player.mp / player.max_mp) * 100) if player.max_mp > 0 else 0,
                "enemy_hp_percent": int((enemy.hp / enemy.max_hp) * 100) if enemy.max_hp > 0 else 0,
            }
            # 通常の戦闘画面に戻る
            return {
                "battle": build_battle_data(state),
                "event": None,
            }

    actione = choose_enemyAction(enemy, player, buffs, debuffs)

    is_player_first = spdcheck(actionp, actione, player, enemy, buffs, debuffs)
    if is_player_first:
        ex_message = ""
        message, success, player_action_result = playerAction(
            message,
            actionp,
            None,
            actione,
            player,
            enemy,
            buffs,
            debuffs,
            special_states,
            request,
        )
        if not success:
            return {
                "battle": None,
                "event": {
                    "type": "error",
                    "payload": {
                        "message": "プレイヤーの行動に失敗しました。",
                    },
                },
            }
            
        if enemy.hp <= 0:
            message, gained_exp, gained_gold, existLevel = win(message, player, enemy, request)
            result = {
                "gained_exp": gained_exp,
                "gained_gold": gained_gold,
                "existLevel": existLevel,
                "newLevel": player.level,
                "stage": stage,
            }
            _reset_battle_session(request, clear_enemy_id=True)
            return {
                "battle": None,
                "event": {
                    "type": "victory",
                    "payload": build_result_data(result),
                }
            }
        else:
            ex_message, buffs, debuffs = enemyAction(message, enemy, player, buffs, debuffs, actionp, actione, special_states)

        # セッションに保存
        request.session["buffs"] = buffs
        request.session["debuffs"] = debuffs
        if ex_message:
            message += ex_message    
        
        # プレイヤーの総HPが0以下になったかチェック
        # プレイヤーが倒れたかチェック
        if player.total_hp_battle <= 0:
            player.death_count += 1
            _reset_battle_session(request, clear_enemy_id=True)
            player.save()
            if player.death_count >= 3:
                request.session['gameover_player_id'] = player.id
                return {
                    "battle": None,
                    "event": {
                        "type": "gameover",
                        "payload": {
                            "message": "プレイヤーが倒れました。",
                        },
                    },
                }   
            else:
                message = tohome(message, player, request)
                return {
                    "battle": None,
                    "event": {
                        "type": "tohome",
                        "payload": {
                            "message": message,
                            "redirect_after": True,
                            "recovering": True,
                        },
                    }
                }          
    else:
        message, buffs, debuffs = enemyAction(message, enemy, player, buffs, debuffs, actionp, actione, special_states)

        # セッションに保存
        request.session["buffs"] = buffs
        request.session["debuffs"] = debuffs
        
        # プレイヤーの総HPが0以下になったかチェック
        if player.total_hp_battle <= 0:
            player.death_count += 1
            player.save()
            _reset_battle_session(request, clear_enemy_id=True)
            if player.death_count >= 3:
                request.session['gameover_player_id'] = player.id
                return {
                    "battle": None,
                    "event": {
                        "type": "gameover",
                        "payload": {
                            "message": "プレイヤーが倒れました。",
                        },
                    },
                }
            else:
                message = tohome(message, player, request)
                return {
                    "battle": None,
                    "event": {
                        "type": "tohome",
                        "payload": {
                            "message": message,
                            "redirect_after": True,
                            "recovering": True,
                        },
                    }
                }
        
        ex_message, success, player_action_result = playerAction(
            message,
            actionp,
            None,
            actione,
            player,
            enemy,
            buffs,
            debuffs,
            special_states,
            request,
        )
        message += ex_message
        if not success:
            return {
                "battle": None,
                "event": {
                    "type": "error",
                    "payload": {
                        "message": message,
                    },
                },
            }
        
        if enemy.hp <= 0:
            message, gained_exp, gained_gold, existLevel = win(message, player, enemy, request)
            result = {
                "gained_exp": gained_exp,
                "gained_gold": gained_gold,
                "existLevel": existLevel,
                "newLevel": player.level,
                "stage": stage,
            }
            _reset_battle_session(request, clear_enemy_id=True)
            return {
                "battle": None,
                "event": {
                    "type": "victory",
                    "payload": build_result_data(result),
                }
            }
    

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

    state = {
        "player": player,
        "enemy": enemy,
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
        "player_hp_percent": int((player.total_hp_battle / player.total_max_hp_battle) * 100) if player.total_max_hp_battle > 0 else 0,
        "player_sp_percent": int((player.mp / player.max_mp) * 100) if player.max_mp > 0 else 0,
        "enemy_hp_percent": int((enemy.hp / enemy.max_hp) * 100) if enemy.max_hp > 0 else 0,
    }

    player.save()
    return {
        "battle": build_battle_data(state),
        "event": None,
    }
