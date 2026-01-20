import random
from django.shortcuts import render,redirect
from django.contrib.auth import logout
from django.urls import reverse
from django.db import models
from .models import Player, Enemy, Equipment, Item, Stage, QuestTemplate, PlayerQuest
from .skills import ENEMY_SKILLS, PLAYER_SKILLS
from .weapons_armors import WEAPONS, ARMORS


def calculate_score(player):
    """
    ゲームスコアを計算
    
    スコア計算式:
    - ATK × 100
    - DEF × 100
    - SPD × 100
    - HP × 10
    - SP × 10
    - 装備の持つスコア（各装備のscoreフィールドの合計）
    - 倒した敵の数 × 100
    - 倒した強敵の数 × 1000
    - プレイヤーレベル × 100
    
    戻り値:
        辞書 {
            'hp_score': int,
            'atk_score': int,
            'def_score': int,
            'spd_score': int,
            'mp_score': int,
            'equipment_score': int,
            'defeat_score': int,
            'strong_defeat_score': int,
            'level_score': int,
            'total_score': int
        }
    """
    # 基本ステータススコア
    atk_score = player.atk * 100
    def_score = player.defense * 100
    spd_score = player.spd * 100
    hp_score = player.max_hp * 10
    mp_score = player.max_mp * 10
    
    # 装備スコア（所持している全装備のscoreフィールドの合計）
    equipment_score = sum(eq.score for eq in player.owned_equipment.all())
    
    # 撃破スコア
    defeat_score = player.defeats * 100
    strong_defeat_score = player.strong_defeats * 1000
    
    # レベルスコア
    level_score = player.level * 300
    
    # 合計スコア
    total_score = (
        atk_score + def_score + spd_score + hp_score + mp_score +
        equipment_score + defeat_score + strong_defeat_score + level_score
    )
    
    return {
        'hp_score': hp_score,
        'atk_score': atk_score,
        'def_score': def_score,
        'spd_score': spd_score,
        'mp_score': mp_score,
        'equipment_score': equipment_score,
        'defeat_score': defeat_score,
        'strong_defeat_score': strong_defeat_score,
        'level_score': level_score,
        'total_score': total_score
    }


def find_quest_in_derivation_chain(player, initial_template):
    """
    初期クエストから派生チェーンを辿り、プレイヤーのPlayerQuestを探す
    
    Args:
        player: プレイヤーオブジェクト
        initial_template: 初期クエストのテンプレート（derivation_level=0）
    
    Returns:
        PlayerQuest or None
    """
    print(f"=== 派生チェーン探索開始: {initial_template.title} ===")
    # 派生チェーンを構築（初期クエスト→派生1→派生2→...）
    chain = [initial_template]
    current = initial_template
    while current.derived_quest:
        chain.append(current.derived_quest)
        current = current.derived_quest
    
    print(f"派生チェーン: {[t.title for t in chain]}")
    
    # チェーン内のどのテンプレートに一致するPlayerQuestがあるか探す
    for template in chain:
        pq = PlayerQuest.objects.filter(player=player, quest_template=template).first()
        print(f"  {template.title} (derivation_level={template.derivation_level}) -> PlayerQuest: {pq}")
        if pq:
            print(f"  ✓ 発見: {pq.quest_template.title}")
            return pq
    
    print(f"  ✗ PlayerQuestが見つかりませんでした")
    return None


def initialize_player_quests(player):
    """
    プレイヤーのクエストを初期化する
    存在しないPlayerQuestを自動生成する
    派生クエスト（derivation_level > 0）は初期化しない
    派生チェーン内にPlayerQuestが既に存在する場合は作成しない
    
    Args:
        player: Playerオブジェクト
    """
    # プレイヤーに適用可能なクエストテンプレートを取得（初期クエストのみ）
    life_templates = QuestTemplate.objects.filter(
        quest_type='life',
        is_active=True,
        derivation_level=0  # 初期クエストのみ
    ).filter(
        models.Q(job='all') | models.Q(job=player.job)
    )
    
    account_templates = QuestTemplate.objects.filter(
        quest_type='account',
        is_active=True,
        job='all',
        derivation_level=0  # 初期クエストのみ
    )
    
    # PlayerQuestを自動生成（派生チェーン内に存在しない場合のみ）
    for template in life_templates:
        # 派生チェーン内にPlayerQuestが存在するかチェック
        existing_in_chain = find_quest_in_derivation_chain(player, template)
        if not existing_in_chain:
            # 存在しない場合のみ作成
            PlayerQuest.objects.create(
                player=player,
                quest_template=template,
                progress_current=0,
                is_completed=False,
                is_claimed=False
            )
            print(f"初期クエスト作成: {template.title}")
    
    for template in account_templates:
        # 派生チェーン内にPlayerQuestが存在するかチェック
        existing_in_chain = find_quest_in_derivation_chain(player, template)
        if not existing_in_chain:
            # 存在しない場合のみ作成
            PlayerQuest.objects.create(
                player=player,
                quest_template=template,
                progress_current=0,
                is_completed=False,
                is_claimed=False
            )
            print(f"初期クエスト作成: {template.title}")


def level_up_player(player, message=""):
    """
    プレイヤーのレベルアップ処理を行う共通関数
    
    Args:
        player: Playerオブジェクト
        message: 既存のメッセージ文字列（追記される）
    
    Returns:
        message: レベルアップメッセージを追加した文字列
    """
    while player.exp >= player.next_exp:
        player.level += 1
        player.stat_points += 3
        player.exp -= player.next_exp
        player.next_exp = int(300 + player.level * 30 * player.level)
        
        # レベルアップ時にHPとSPを最大まで回復
        player.hp = player.max_hp
        player.mp = player.max_mp
        player.update_battle_stats()  # 戦闘用ステータスも更新
        
        message += f"レベルアップ！ レベル{player.level}になった！ ステータスポイント+3\n"
        message += f"HPとSPが全回復した！\n"
    
    return message


def get_player_from_request(request, player_id=None):
    """
    リクエストからプレイヤーを取得する
    
    Args:
        request: HTTPリクエスト
        player_id: プレイヤーID（指定された場合はそのIDのプレイヤーを取得）
    
    Returns:
        Player: プレイヤーオブジェクト
    
    処理の優先順位:
    1. player_idが指定されている場合: そのIDのプレイヤーを取得
    2. ログインユーザーの場合: userに紐付いたプレイヤーを取得
    3. ゲストの場合: セッションからプレイヤーIDを取得
    """
    if player_id:
        return Player.objects.get(id=player_id)
    
    if request.user.is_authenticated:
        # ログインユーザーの場合
        try:
            return request.user.player
        except Player.DoesNotExist:
            # プレイヤーが存在しない場合は作成
            return Player.objects.create(
                user=request.user,
                name=request.user.username,
                is_guest=False
            )
    else:
        # ゲストの場合
        guest_player_id = request.session.get('guest_player_id')
        if guest_player_id:
            try:
                return Player.objects.get(id=guest_player_id, is_guest=True)
            except Player.DoesNotExist:
                pass
    
    return None

def home(request):
    return render(request, 'game/home.html')

def stage_select(request, player_id):
    """ステージ選択画面"""
    player = Player.objects.get(id=player_id)
    stages = Stage.objects.all().order_by('order')
    
    return render(request, 'game/stage_select.html', {
        'player': player,
        'stages': stages,
    })

def start_game(request):
    """職業選択画面（ログインユーザー/ゲスト両対応）"""
    force_guest = request.GET.get('guest') == '1'

    # ゲストで始める指定がある場合はログアウトしておく
    if force_guest and request.user.is_authenticated:
        logout(request)

    # 既にPlayerが存在する場合はゲーム画面へリダイレクト（ゲスト強制時はスキップ）
    if request.user.is_authenticated and not force_guest:
        try:
            player = request.user.player
            return redirect('game:battle_start', player_id=player.id)
        except Player.DoesNotExist:
            pass  # Playerが存在しない場合は職業選択へ進む
    
    if request.method == 'POST':
        name = request.POST.get('name')
        job = request.POST.get('job', '戦士')  # デフォルトは戦士

        request.session['session_purchased_items'] = []
        request.session['reset_shop'] = True
        
        # 前回のゲームオーバーのスコア情報を削除
        if 'gameover_score' in request.session:
            del request.session['gameover_score']
        if 'gameover_initial_point' in request.session:
            del request.session['gameover_initial_point']
        if 'score_breakdown' in request.session:
            del request.session['score_breakdown']
        
        # ジョブに応じたステータス設定
        if job == "戦士":
            base_hp, base_atk, base_def, base_spd, base_mp = 100, 5, 5, 5, 50
            job_bonus_hp, job_bonus_atk, job_bonus_def, job_bonus_spd, job_bonus_mp = 10, 3, 3, -3, -5
            stat_points = request.user.initial_points if request.user.is_authenticated else 0
        elif job == "魔法使い":
            base_hp, base_atk, base_def, base_spd, base_mp = 100, 5, 5, 5, 50
            job_bonus_hp, job_bonus_atk, job_bonus_def, job_bonus_spd, job_bonus_mp = -5, 7, -2, 0, +10
            stat_points = request.user.initial_points if request.user.is_authenticated else 0
        elif job == "忍者":
            base_hp, base_atk, base_def, base_spd, base_mp = 100, 5, 5, 5, 50
            job_bonus_hp, job_bonus_atk, job_bonus_def, job_bonus_spd, job_bonus_mp = -5, 3, 0, 5, 0
            stat_points = request.user.initial_points if request.user.is_authenticated else 0
        elif job == "格闘家":
            base_hp, base_atk, base_def, base_spd, base_mp = 100, 5, 5, 5, 50
            job_bonus_hp, job_bonus_atk, job_bonus_def, job_bonus_spd, job_bonus_mp = -20, 8, 3, 5, -10
            stat_points = request.user.initial_points if request.user.is_authenticated else 0
        else:
            base_hp, base_atk, base_def, base_spd, base_mp = 100, 5, 5, 5, 50
            job_bonus_hp, job_bonus_atk, job_bonus_def, job_bonus_spd, job_bonus_mp = 0, 0, 0, 0, 0
            stat_points = 0
        
        # 初期装備をデータベースから取得
        wooden_sword = Equipment.objects.get(name="木の剣")
        leather_armor = Equipment.objects.get(name="革の服")
        
        # ログインユーザーかゲストかで分岐
        if request.user.is_authenticated:
            # ログインユーザー: userに紐付けてPlayerを作成
            player = Player.objects.create(
                user=request.user,
                name=name if name else request.user.username,
                is_guest=False,
                level=1,
                exp=0,
                next_exp=300,
                max_hp=base_hp + job_bonus_hp,
                hp=base_hp + job_bonus_hp,
                atk=base_atk + job_bonus_atk,
                defense=base_def + job_bonus_def,
                spd=base_spd + job_bonus_spd,
                max_mp=base_mp + job_bonus_mp,
                mp=base_mp + job_bonus_mp,
                stat_points=stat_points,
                job=job,
                weapon=wooden_sword,
                armor=leather_armor,
                gold=100,
            )
        else:
            # ゲストプレイヤー: user=Noneで作成
            player = Player.objects.create(
                name=name,
                is_guest=True,
                level=1,
                exp=0,
                next_exp=300,
                max_hp=base_hp + job_bonus_hp,
                hp=base_hp + job_bonus_hp,
                atk=base_atk + job_bonus_atk,
                defense=base_def + job_bonus_def,
                spd=base_spd + job_bonus_spd,
                max_mp=base_mp + job_bonus_mp,
                mp=base_mp + job_bonus_mp,
                stat_points=stat_points,
                job=job,
                weapon=wooden_sword,
                armor=leather_armor,
                gold=100,
            )
            # ゲストプレイヤーの場合、セッションにIDを保存
            request.session['guest_player_id'] = player.id
        
        # 初期装備を所持装備に追加
        player.owned_equipment.add(wooden_sword, leather_armor)
        
        # クエストを初期化
        initialize_player_quests(player)
        
        return redirect('game:battle_start', player_id=player.id)
    
    # GETリクエスト: 職業選択画面を表示
    # ログインユーザーの場合はデフォルト名をユーザー名にする（ゲスト強制時は空にする）
    default_name = request.user.username if request.user.is_authenticated and not force_guest else ""
    
    return render(request, 'game/start.html', {'default_name': default_name})

def battle_start(request, player_id, enemy_id=None):
    player = Player.objects.get(id=player_id)
    
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

    exp_percent = int(player.exp / player.next_exp * 100)

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


def select_new_enemy(player, stage, request):
    """
    新しい敵を選択する共通関数
    
    Args:
        player: プレイヤーオブジェクト
        stage: ステージオブジェクト
        request: リクエストオブジェクト
    
    Returns:
        enemy: 選択された敵オブジェクト（セッションに保存済み）
    """
    # プレイヤーレベルに応じた敵のレベル範囲を決定
    if player.level <= 5:
        min_enemy_level = stage.min_enemy_level
        max_enemy_level = min(player.level + 1, stage.max_enemy_level)
    elif player.level <= 8:
        min_enemy_level = stage.min_enemy_level
        max_enemy_level = min(player.level + 2, stage.max_enemy_level)
    elif player.level <= 10:
        min_enemy_level = stage.min_enemy_level
        max_enemy_level = min(player.level + 3, stage.max_enemy_level)
    elif player.level <= 15:
        min_enemy_level = stage.min_enemy_level
        max_enemy_level = min(player.level + 4, stage.max_enemy_level)
    else:
        min_enemy_level = stage.min_enemy_level
        max_enemy_level = min(player.level + 5, stage.max_enemy_level)
    
    # ステージに登録されている敵を取得
    stage_enemies = list(stage.enemies.all())
    
    if not stage_enemies:
        stage_enemies = list(Enemy.objects.filter(appear_level__lte=max_enemy_level))
    
    if not stage_enemies:
        stage_enemies = list(Enemy.objects.all())
    
    if not stage_enemies:
        return None
    
    # レベル差に応じて出現確率を調整
    weighted_enemies = []
    for enemy in stage_enemies:
        if enemy.appear_level > player.level:
            continue
        
        enemy_min_level = min_enemy_level
        enemy_max_level = max_enemy_level
        
        if enemy_min_level > enemy_max_level:
            continue
        
        potential_level = random.randint(enemy_min_level, enemy_max_level)
        level_diff = abs(player.level - potential_level)
        
        # レベル差が小さいほど重みを大きく
        if level_diff == 0:
            base_weight = 20
        elif level_diff == 1:
            base_weight = 15
        elif level_diff == 2:
            base_weight = 10
        elif level_diff == 3:
            base_weight = 6
        elif level_diff == 4:
            base_weight = 3
        else:
            base_weight = 1
        
        weight = max(1, int(base_weight * max(enemy.appearance_rate, 0)))
        
        if potential_level > player.level:
            if player.level <= 5:
                weight = int(weight * 0.75)
            elif player.level <= 8:
                weight = int(weight * 0.5)
            elif player.level <= 10:
                weight = int(weight * 0.6)
            elif player.level <= 15:
                weight = int(weight * 0.7)
            else:
                weight = int(weight * 0.8)
        
        weight = max(1, weight)
        weighted_enemies.extend([(enemy, potential_level)] * weight)
    
    if not weighted_enemies:
        return None
    
    # ランダムに敵を選択
    enemy, selected_level = random.choice(weighted_enemies)
    enemy.level = selected_level
    
    # 強敵判定
    is_strong = False
    if player.level >= 10 and random.random() < 0.05:
        is_strong = True
        enemy.level += random.randint(10, 15)
    
    # レベルに応じてステータスを変更
    enemy.max_hp = enemy.base_max_hp + (enemy.level - 1) * enemy.base_max_hp // 10
    enemy.hp = enemy.max_hp
    
    if enemy.level <= 14:
        enemy.atk = enemy.base_atk + (enemy.level - 1) * enemy.base_atk // 6
        enemy.defense = enemy.base_def + (enemy.level - 1) * enemy.base_def // 6
        enemy.spd = enemy.base_spd + (enemy.level - 1) * enemy.base_spd // 6
    else:
        level_20_atk = enemy.base_atk + 14 * enemy.base_atk // 10
        level_20_def = enemy.base_def + 14 * enemy.base_def // 10
        level_20_spd = enemy.base_spd + 14 * enemy.base_spd // 10
        
        additional_levels = enemy.level - 15
        enemy.atk = level_20_atk + additional_levels * enemy.base_atk // 4
        enemy.defense = level_20_def + additional_levels * enemy.base_def // 4
        enemy.spd = level_20_spd + additional_levels * enemy.base_spd // 4
    
    # expとゴールドの計算
    base_high_exp = enemy.base_exp + (enemy.level - 1) * enemy.base_exp // 3
    if enemy.level > player.level:
        enemy.exp = int(base_high_exp * random.uniform(1.3, 1.4))
        enemy.drop_gold = enemy.drop_gold_base + (enemy.level - 1) * enemy.drop_gold_base // 6
    else:
        enemy.exp = int(base_high_exp * random.uniform(0.7, 0.8))
        enemy.drop_gold = enemy.drop_gold_base + (enemy.level - 1) * enemy.drop_gold_base // 10
    
    enemy.is_defeated = False
    enemy.is_strong = is_strong
    enemy.save()
    
    # セッションに敵のIDを保存
    request.session["enemy_id"] = enemy.id
    
    return enemy


def decrease_buff_debuff_turns(buffs, debuffs, special_states):
    """
    ターン経過でバフ・デバフ・特殊状態を減少させる共通関数
    
    Args:
        buffs: バフの辞書
        debuffs: デバフの辞書
        special_states: 特殊状態の辞書
    
    Returns:
        tuple: (更新されたbuffs, debuffs, special_states)
    """
    # バフの減少
    for target in list(buffs.keys()):
        for stat in list(buffs[target].keys()):
            buffs[target][stat]["turn"] -= 1
            if buffs[target][stat]["turn"] <= 0:
                del buffs[target][stat]
        if not buffs[target]:
            del buffs[target]
    
    # デバフの減少
    for target in list(debuffs.keys()):
        for stat in list(debuffs[target].keys()):
            debuffs[target][stat]["turn"] -= 1
            if debuffs[target][stat]["turn"] <= 0:
                del debuffs[target][stat]
        if not debuffs[target]:
            del debuffs[target]
    
    # 特殊状態の減少
    for target in list(special_states.keys()):
        for state in list(special_states[target].keys()):
            special_states[target][state]["turn"] -= 1
            if special_states[target][state]["turn"] <= 0:
                del special_states[target][state]
        if not special_states[target]:
            del special_states[target]
    
    return buffs, debuffs, special_states


def battle(request, player_id, enemy_id=None):
    from .models import PlayerInventory
    
    player=Player.objects.get(id=player_id)
    
    # ステージIDを取得（GETパラメータまたはセッション）
    stage_id = request.GET.get('stage_id') or request.session.get('stage_id')
    if stage_id:
        request.session['stage_id'] = stage_id
        stage = Stage.objects.get(id=stage_id)
    else:
        # デフォルトステージ（草原）
        stage = Stage.objects.first()
        request.session['stage_id'] = stage.id if stage else None
    
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
        request.session["message_history"] = []
        request.session["buffs"] = {}
        request.session["debuffs"] = {}
        request.session["special_states"] = {}
    else:
        enemy = Enemy.objects.get(id=enemy_id)
    
    message = ""
    
    # メッセージ履歴を取得（累積表示用）
    message_history = request.session.get("message_history", [])

    buffs = request.session.get("buffs", {})
    debuffs = request.session.get("debuffs", {})
    special_states = request.session.get("special_states", {})  # 特殊状態（確定回避など）
    
    # プレイヤーのスキルを取得
    player_skills = PLAYER_SKILLS.get(player.job, [])
    # スキルにis_actionフラグがない場合はFalseを設定
    for skill in player_skills:
        if 'is_action' not in skill:
            skill['is_action'] = False
    
    # プレイヤーのアイテムを取得
    player_items = PlayerInventory.objects.filter(player=player, quantity__gt=0).select_related('item')
    
    # 【表示用ステータス】戦闘用ステータス + バフ×デバフ適用
    # プレイヤー（total_*_battleフィールドを使用）
    player_atk_buff = buffs.get("player", {}).get("atk", {}).get("multiplier", 1.0)
    player_atk_debuff = debuffs.get("player", {}).get("atk", {}).get("multiplier", 1.0)
    showplayer_atk = int(player.total_atk_battle * player_atk_buff * player_atk_debuff)
    
    player_def_buff = buffs.get("player", {}).get("def", {}).get("multiplier", 1.0)
    player_def_debuff = debuffs.get("player", {}).get("def", {}).get("multiplier", 1.0)
    showplayer_def = int(player.total_def_battle * player_def_buff * player_def_debuff)
    
    player_spd_buff = buffs.get("player", {}).get("spd", {}).get("multiplier", 1.0)
    player_spd_debuff = debuffs.get("player", {}).get("spd", {}).get("multiplier", 1.0)
    showplayer_spd = int(player.total_spd_battle * player_spd_buff * player_spd_debuff)
    
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

        # レベルアップ処理
        message = level_up_player(player, message)

        # 戦闘回数をカウントアップ
        battle_count = request.session.get('battle_count', 0)
        request.session['battle_count'] = battle_count + 1

        request.session["buffs"] = {}
        request.session["debuffs"] = {}
        
        # 戦闘用HPを素のHPに反映
        player.sync_hp_from_battle()
        return message,gained_exp,gained_gold,existLevel
    
    def calculate_player_attack(multiplier=1.0, damage_variance=(-1, 2)):
        """プレイヤーの攻撃ダメージを計算する共通関数
        
        Args:
            multiplier: 攻撃力の倍率（デフォルト1.0）
            damage_variance: ダメージのランダム範囲（デフォルト-1〜+2）
        
        Returns:
            damage: 計算されたダメージ値
        """
        # プレイヤーの攻撃力【戦闘用ステータス】にバフとデバフを適用
        player_atk_buff = buffs.get("player", {}).get("atk", {}).get("multiplier", 1.0)
        player_atk_debuff = debuffs.get("player", {}).get("atk", {}).get("multiplier", 1.0)
        atk = int(player.total_atk_battle * multiplier * player_atk_buff * player_atk_debuff)
        
        # 敵の防御力にバフとデバフを適用
        enemy_def_buff = buffs.get("enemy", {}).get("def", {}).get("multiplier", 1.0)
        enemy_def_debuff = debuffs.get("enemy", {}).get("def", {}).get("multiplier", 1.0)
        enemy_def = int(enemy.defense * enemy_def_buff * enemy_def_debuff)
        
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
    
    def playerAction(message,action,special,actione):
        if action == 'attack':
            # 敵の回避判定（確定回避 or spd基づく確率）
            has_guaranteed_evasion = special_states.get("enemy", {}).get("guaranteed_evasion", {}).get("turn", 0) > 0
            
            if has_guaranteed_evasion:
                message = f"{player.name}の攻撃！ {enemy.name}は回避した！\n"
            else:
                enemy_spd_buff = buffs.get("enemy", {}).get("spd", {}).get("multiplier", 1.0)
                enemy_spd_debuff = debuffs.get("enemy", {}).get("spd", {}).get("multiplier", 1.0)
                enemy_effective_spd = enemy.spd * enemy_spd_buff * enemy_spd_debuff
                evasion_rate = calculate_evasion_rate(enemy_effective_spd)
                
                if random.random() < evasion_rate:
                    message = f"{player.name}の攻撃！ {enemy.name}は回避した！\n"
                else:
                    damage = calculate_player_attack()
                    enemy.hp -= damage
                    enemy.save()
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
            player_skills = PLAYER_SKILLS.get(player.job, [])
            skill_index = int(special.replace('skill', '')) - 1  # skill1 -> 0, skill2 -> 1, ...
            
            if skill_index < 0 or skill_index >= len(player_skills):
                message = f"そのスキルは存在しません。"
                return message, False
            
            skill_data = player_skills[skill_index]
            skill_name = skill_data["name"]
            skill_cost = skill_data["cost"]
            is_action_skill = skill_data.get("is_action", False)
            
            # SP不足チェック
            if player.mp < skill_cost:
                message = f"SPが足りません！ {skill_name} を発動するには SPが{skill_cost}必要です。"
                return message, False
            
            # アクション特技の場合は特別な処理
            if is_action_skill:
                player.mp -= skill_cost
                player.save()
                # アクションモードであることをセッションに保存
                request.session['action_mode'] = {
                    'skill_name': skill_name,
                    'skill_data': skill_data,
                    'multiplier': skill_data["effects"][0].get("multiplier", 1.0)
                }
                # アクションモード用の特別なレンダリングを返す
                return message, True
            
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
                    else:
                        enemy_spd_buff = buffs.get("enemy", {}).get("spd", {}).get("multiplier", 1.0)
                        enemy_spd_debuff = debuffs.get("enemy", {}).get("spd", {}).get("multiplier", 1.0)
                        enemy_effective_spd = enemy.spd * enemy_spd_buff * enemy_spd_debuff
                        evasion_rate = calculate_evasion_rate(enemy_effective_spd)
                        
                        if random.random() < evasion_rate:
                            message += f"{enemy.name}は回避した！\n"
                        else:
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
                
                elif etype == "guaranteed_evasion":
                    # 確定回避処理
                    special_states.setdefault(target, {})
                    special_states[target]["guaranteed_evasion"] = {"turn": turn}
                    request.session["special_states"] = special_states
                    message += f"{target_obj.name}は姿をくらました！\n"
            
            message += f"SPが{skill_cost}減った！\n"
            player.save()
                
        return message,True
    
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
                    priority *= 0.2
                
                # 2. 自身（enemy）にバフがかかっていない場合、自身の技にバフがあれば
                if not buffs.get("enemy") and has_buff_effect:
                    priority *= 2
                elif buffs.get("enemy") and has_buff_effect:
                    priority *= 0.2
                
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
                if enemy_hp_ratio <= 0.5 and has_defense_effect:
                    priority *= 1.3
                else:
                    priority *= 0.3  # HPが高い場合、防御スキルの優先度を下げる
            
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
                # プレイヤーの回避判定（確定回避 or spdに基づく確率）
                should_evade = False
                if target == "player":
                    # 確定回避チェック
                    has_guaranteed_evasion = special_states.get("player", {}).get("guaranteed_evasion", {}).get("turn", 0) > 0
                    
                    if has_guaranteed_evasion:
                        should_evade = True
                    else:
                        player_spd_buff = buffs.get("player", {}).get("spd", {}).get("multiplier", 1.0)
                        player_spd_debuff = debuffs.get("player", {}).get("spd", {}).get("multiplier", 1.0)
                        player_effective_spd = player.total_spd_battle * player_spd_buff * player_spd_debuff
                        evasion_rate = calculate_evasion_rate(player_effective_spd)
                        should_evade = random.random() < evasion_rate
                
                if should_evade:
                    message += f"{target_obj.name}は回避した！\n"
                else:
                    # 敵の攻撃力にバフとデバフの両方を適用
                    enemy_atk_buff = buffs.get("enemy", {}).get("atk", {}).get("multiplier", 1.0)
                    enemy_atk_debuff = debuffs.get("enemy", {}).get("atk", {}).get("multiplier", 1.0)
                    atk = int(me_obj.atk * multiplier * enemy_atk_buff * enemy_atk_debuff)
                    
                    # プレイヤーの防御力にバフとデバフを適用【戦闘用ステータス】
                    player_def_buff = buffs.get("player", {}).get("def", {}).get("multiplier", 1.0)
                    player_def_debuff = debuffs.get("player", {}).get("def", {}).get("multiplier", 1.0)
                    player_def = int(target_obj.total_def_battle * player_def_buff * player_def_debuff)
                    
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

        return message,buffs,debuffs

    def is_defense_action(actione):
        """actioneが防御スキルかどうかを判定"""
        if not actione:
            return False
        return any(effect.get("type") == "defense" for effect in actione.get("effects", []))

    def spdcheck(actionp,actione):
        if actionp == 'defend' or actionp == 'item':
            return True
        elif is_defense_action(actione):
            return False
        else:
            # プレイヤーの素早さにバフとデバフを適用（戦闘用ステータス）
            player_spd_buff = buffs.get("player", {}).get("spd", {}).get("multiplier", 1.0)
            player_spd_debuff = debuffs.get("player", {}).get("spd", {}).get("multiplier", 1.0)
            effective_player_spd = player.total_spd_battle * player_spd_buff * player_spd_debuff
            
            # 敵の素早さにバフとデバフを適用
            enemy_spd_buff = buffs.get("enemy", {}).get("spd", {}).get("multiplier", 1.0)
            enemy_spd_debuff = debuffs.get("enemy", {}).get("spd", {}).get("multiplier", 1.0)
            effective_enemy_spd = enemy.spd * enemy_spd_buff * enemy_spd_debuff
            
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
            return render(request, "game/battle.html", render_battle_screen(message, enemy_override=None, gained_exp=gained_exp, existLevel=existLevel, gained_gold=gained_gold))
        
        # 戦闘を続行
        return render(request, "game/battle.html", render_battle_screen(message))

    if request.method == 'POST':
        
        actionp = request.POST.get('action')
        special = request.POST.get('special')
        use_item_id = request.POST.get('use_item')
        
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
                elif item.target == 'mp':
                    old_mp = player.mp
                    player.mp = min(player.mp + item.effect_amount, player.max_mp)
                    actual_recovery = player.mp - old_mp
                    message = f"{player.name}は{item.name}を使った！\nSPが{actual_recovery}回復した！\n"
                
                # アイテムを1つ消費
                inventory_item.quantity -= 1
                inventory_item.save()
                player.save()
                
                # アイテム使用後は敵のターン（必ず先手だがターン経過）
                actione = choose_enemyAction(enemy, player, buffs, debuffs)
                ex_message,buffs,debuffs = enemyAction(message,enemy,player,buffs,debuffs,'item',actione)
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
                ex_message,buffs,debuffs = enemyAction(message,enemy,player,buffs,debuffs,actionp,actione)
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

        spdcheck = spdcheck(actionp,actione)
        if spdcheck:
            message,success = playerAction(message,actionp,special,actione)
            if not success:
                return render(request, "game/battle.html", render_battle_screen(message))
            
            # アクションモードチェック
            if request.session.get('action_mode'):
                action_data = request.session['action_mode']
                return render(request, "game/battle.html", render_battle_screen(message, action_mode=action_data))
            
            if enemy.hp <= 0:
                message, gained_exp, gained_gold, existLevel = win(message)
                return render(request, "game/battle.html", render_battle_screen(message, enemy_override=None, gained_exp=gained_exp, existLevel=existLevel, gained_gold=gained_gold))
            ex_message,buffs,debuffs = enemyAction(message,enemy,player,buffs,debuffs,actionp,actione)
            # セッションに保存
            request.session["buffs"] = buffs
            request.session["debuffs"] = debuffs
            message += ex_message    
            
            # プレイヤーの総HPが0以下になったかチェック
            # プレイヤーが倒れたかチェック
            if player.total_hp_battle <= 0:
                player.death_count += 1
                if player.death_count >= 3:
                    request.session['gameover_player_id'] = player.id
                    return redirect('game:gameover')
                else:
                    message = tohome(message)
                    return render(request, "game/battle.html", render_battle_screen(message, redirect_after=True, redirect_url="battle_start", recovering=True))          
        else:
            message,buffs,debuffs = enemyAction(message,enemy,player,buffs,debuffs,actionp,actione)
            # セッションに保存
            request.session["buffs"] = buffs
            request.session["debuffs"] = debuffs
            
            # プレイヤーの総HPが0以下になったかチェック
            if player.total_hp_battle <= 0:
                player.death_count += 1
                if player.death_count >= 3:
                    request.session['gameover_player_id'] = player.id
                    return redirect('game:gameover')
                else:
                    message = tohome(message)
                    return render(request, "game/battle.html", render_battle_screen(message, redirect_after=True, redirect_url="battle_start", recovering=True))
            
            ex_message,success = playerAction(message,actionp,special,actione)
            message += ex_message
            if not success:
                return render(request, "game/battle.html", render_battle_screen(message))
            
            # アクションモードチェック
            if request.session.get('action_mode'):
                action_data = request.session['action_mode']
                return render(request, "game/battle.html", render_battle_screen(message, action_mode=action_data))
            
            if enemy.hp <= 0:
                message,gained_exp,gained_gold,existLevel = win(message)
                return render(request, "game/battle.html", render_battle_screen(message, enemy_override=None, gained_exp=gained_exp, existLevel=existLevel, gained_gold=gained_gold))
          

        # ターン経過でバフを減少
        buffs, debuffs, special_states = decrease_buff_debuff_turns(buffs, debuffs, special_states)

        request.session["buffs"] = buffs
        request.session["debuffs"] = debuffs
        request.session["special_states"] = special_states
        
        # 表示用ステータスを再計算【装備ボーナス込み + バフ×デバフ適用】
        # プレイヤーのステータス（total_atk, total_def, total_spdは装備込み）
        player_atk_buff = buffs.get("player", {}).get("atk", {}).get("multiplier", 1.0)
        player_atk_debuff = debuffs.get("player", {}).get("atk", {}).get("multiplier", 1.0)
        showplayer_atk = int(player.total_atk_battle * player_atk_buff * player_atk_debuff)
        
        player_def_buff = buffs.get("player", {}).get("def", {}).get("multiplier", 1.0)
        player_def_debuff = debuffs.get("player", {}).get("def", {}).get("multiplier", 1.0)
        showplayer_def = int(player.total_def_battle * player_def_buff * player_def_debuff)
        
        player_spd_buff = buffs.get("player", {}).get("spd", {}).get("multiplier", 1.0)
        player_spd_debuff = debuffs.get("player", {}).get("spd", {}).get("multiplier", 1.0)
        showplayer_spd = int(player.total_spd_battle * player_spd_buff * player_spd_debuff)
        
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
        
        return render(request, "game/battle.html", render_battle_screen(message))
    
    
    return render(request, "game/battle.html", render_battle_screen(message))


def shop(request, player_id):
    """ショップページ"""
    import json
    import random
    player = Player.objects.get(id=player_id)
    
    # セッションからショップ在庫を取得
    shop_inventory = request.session.get('shop_inventory', None)
    
    # ショップ在庫が存在しない場合、または強制リセットフラグがある場合は新規生成
    if shop_inventory is None or request.session.get('reset_shop', False):
        # プレイヤーが所持している装備を取得
        owned_equipment_ids = player.owned_equipment.values_list('id', flat=True)
        
        # データベースから未所持の装備を取得（is_purchasedは使わない、appear_levelでフィルタ）
        available_weapons = list(Equipment.objects.filter(
            equipment_type='weapon',
            appear_level__lte=player.level
        ).exclude(id__in=owned_equipment_ids))
        available_armors = list(Equipment.objects.filter(
            equipment_type='armor',
            appear_level__lte=player.level
        ).exclude(id__in=owned_equipment_ids))
        available_items = list(Item.objects.filter(
            is_purchased=False,
            appear_level__lte=player.level
        ))
        
        # 全てのアイテムを結合
        all_items = available_weapons + available_armors + available_items
        
        # ランダムに最大8個を選択
        if len(all_items) > 8:
            shop_items = random.sample(all_items, 8)
        else:
            shop_items = all_items
        
        # アイテム情報をセッションに保存(IDとタイプのみ)
        shop_inventory = []
        for item in shop_items:
            if isinstance(item, Equipment):
                shop_inventory.append({
                    'id': item.id,
                    'type': 'equipment',
                    'equipment_type': item.equipment_type
                })
            else:  # Item
                shop_inventory.append({
                    'id': item.id,
                    'type': 'item',
                    'current_stock': item.max_stock  # 現在の在庫を最大在庫数で初期化
                })
        
        request.session['shop_inventory'] = shop_inventory
        request.session['reset_shop'] = False
    
    # セッションに保存されたIDからアイテムを取得
    weapons = []
    armors = []
    items = []
    
    session_purchased = request.session.get('session_purchased_items', [])
    
    for item_data in shop_inventory:
        if item_data['type'] == 'equipment':
            equipment = Equipment.objects.filter(id=item_data['id']).first()
            # 装備が存在する場合のみ表示（is_purchasedチェックは不要）
            if equipment:
                if equipment.equipment_type == 'weapon':
                    weapons.append(equipment)
                else:
                    armors.append(equipment)
        else:  # item
            item = Item.objects.filter(id=item_data['id']).first()
            # アイテムの現在在庫を取得
            if item:
                # 在庫数をアイテムオブジェクトに動的に追加
                item.current_stock = item_data.get('current_stock', item.max_stock)
                # 在庫が残っている場合のみ表示
                if item.current_stock > 0:
                    items.append(item)
    
    return render(request, 'game/shop.html', {
        'player': player,
        'weapons': weapons,
        'armors': armors,
        'items': items,
        'session_purchased': json.dumps(session_purchased),
    })


def buy_item(request, player_id):
    """アイテム購入処理"""
    from .models import PlayerInventory
    
    if request.method == 'POST':
        player = Player.objects.get(id=player_id)
        item_name = request.POST.get('item_name')
        item_price = int(request.POST.get('item_price'))
        item_type = request.POST.get('item_type')  # 'weapon', 'armor', 'item'
        item_quantity = int(request.POST.get('item_quantity', 1))  # 購入個数（デフォルト1）
        
        # 合計金額を計算
        total_price = item_price * item_quantity
        
        # 所持金チェック
        if player.gold >= total_price:
            # お金を減らす
            player.gold -= total_price
            
            # クエスト進捗更新（ゴールド消費）
            gold_spend_quests = PlayerQuest.objects.filter(
                player=player,
                quest_template__condition_type='spend_gold',
                is_completed=False
            )
            for player_quest in gold_spend_quests:
                player_quest.update_progress(total_price)
            
            player.save()
            
            # Equipmentの場合はプレイヤーの所持装備に追加
            if item_type == 'weapon' or item_type == 'armor':
                equipment = Equipment.objects.filter(name=item_name, equipment_type=item_type).first()
                if equipment:
                    # プレイヤーの所持装備に追加（is_purchasedは更新しない）
                    player.owned_equipment.add(equipment)
            # Itemの場合は在庫を減らし、PlayerInventoryに追加
            elif item_type == 'item':
                # ショップ在庫を取得
                shop_inventory = request.session.get('shop_inventory', [])
                
                # 該当アイテムの在庫を減らす
                for item_data in shop_inventory:
                    if item_data['type'] == 'item':
                        item = Item.objects.filter(id=item_data['id']).first()
                        if item and item.name == item_name:
                            current_stock = item_data.get('current_stock', item.max_stock)
                            item_data['current_stock'] = max(0, current_stock - item_quantity)
                            
                            # PlayerInventoryに追加
                            inventory_item, created = PlayerInventory.objects.get_or_create(
                                player=player,
                                item=item
                            )
                            inventory_item.quantity += item_quantity
                            inventory_item.save()
                            break
                
                # セッションを更新
                request.session['shop_inventory'] = shop_inventory
            
            # セッションに今回のショップで購入済みのアイテムを追加（装備のみ）
            if item_type in ['weapon', 'armor']:
                session_purchased = request.session.get('session_purchased_items', [])
                if item_name not in session_purchased:
                    session_purchased.append(item_name)
                    request.session['session_purchased_items'] = session_purchased
        
        # ショップに戻る
        return redirect('game:shop', player_id=player.id)
    
    return redirect('game:shop', player_id=player_id)


def equipment_change(request, player_id):
    """装備変更画面"""
    player = Player.objects.get(id=player_id)
    
    # 初期装備がない場合は追加
    if not player.owned_equipment.exists():
        wooden_sword = Equipment.objects.get(name="木の剣")
        leather_armor = Equipment.objects.get(name="皮の服")
        player.owned_equipment.add(wooden_sword, leather_armor)
        if not player.weapon:
            player.weapon = wooden_sword
        if not player.armor:
            player.armor = leather_armor
        player.save()
    
    # 所持している装備を取得
    owned_weapons = player.owned_equipment.filter(equipment_type='weapon')
    owned_armors = player.owned_equipment.filter(equipment_type='armor')
    
    return render(request, 'game/equipment_change.html', {
        'player': player,
        'owned_weapons': owned_weapons,
        'owned_armors': owned_armors,
    })


def equip_item(request, player_id, equipment_id):
    """装備を変更する"""
    player = Player.objects.get(id=player_id)
    equipment = Equipment.objects.get(id=equipment_id)
    
    # プレイヤーが所持している装備かチェック
    if equipment in player.owned_equipment.all():
        if equipment.equipment_type == 'weapon':
            player.change_weapon(equipment)
            # 武器タブに戻る
            return redirect(f'{reverse("game:equipment_change", kwargs={"player_id": player.id})}?tab=weapons')
        elif equipment.equipment_type == 'armor':
            player.change_armor(equipment)
            # 防具タブに戻る
            return redirect(f'{reverse("game:equipment_change", kwargs={"player_id": player.id})}?tab=armors')
    
    # 装備変更画面に戻る（デフォルト）
    return redirect('game:equipment_change', player_id=player.id)


def inventory(request, player_id):
    """持ち物画面"""
    from .models import PlayerInventory
    
    player = Player.objects.get(id=player_id)
    
    # カテゴリーフィルター（デフォルトは'全て'）
    category = request.GET.get('category', '全て')
    
    # 検索クエリ
    search_query = request.GET.get('search', '').strip()
    
    # 使用メッセージを取得（あれば）
    use_message = request.session.pop('use_item_message', None)
    
    # プレイヤーのインベントリを取得
    inventory_items = PlayerInventory.objects.filter(player=player, quantity__gt=0).select_related('item')
    
    # カテゴリーでフィルタリング
    if category == '回復':
        inventory_items = inventory_items.filter(item__target='hp')
    elif category == '魔法':
        inventory_items = inventory_items.filter(item__target='mp')
    
    # 検索クエリでフィルタリング
    if search_query:
        inventory_items = inventory_items.filter(item__name__icontains=search_query)
    
    # 最初に選択されているアイテム（最初のアイテム）
    selected_item = None
    if inventory_items.exists():
        selected_item_id = request.GET.get('selected_item')
        if selected_item_id:
            try:
                selected_item = inventory_items.get(id=int(selected_item_id))
            except (PlayerInventory.DoesNotExist, ValueError):
                selected_item = inventory_items.first()
        else:
            selected_item = inventory_items.first()
    
    return render(request, 'game/inventory.html', {
        'player': player,
        'inventory_items': inventory_items,
        'selected_item': selected_item,
        'category': category,
        'search_query': search_query,
        'use_message': use_message,
    })

def use_inventory_item(request, player_id, inventory_item_id):
    """インベントリーからアイテムを使用する"""
    from .models import PlayerInventory
    
    if request.method == 'POST':
        player = Player.objects.get(id=player_id)
        
        try:
            inventory_item = PlayerInventory.objects.get(id=inventory_item_id, player=player, quantity__gt=0)
            item = inventory_item.item
            
            # HP回復アイテムの場合
            if item.target == 'hp':
                old_hp = player.hp
                player.hp = min(player.hp + item.effect_amount, player.max_hp)
                actual_recovery = player.hp - old_hp
                
                # アイテムを1つ消費
                inventory_item.quantity -= 1
                inventory_item.save()
                player.save()
                
                # 成功メッセージをセッションに保存
                request.session['use_item_message'] = f"HPが{actual_recovery}回復した！"
            
            # SP回復アイテムの場合
            elif item.target == 'mp':
                old_mp = player.mp
                player.mp = min(player.mp + item.effect_amount, player.max_mp)
                actual_recovery = player.mp - old_mp
                
                # アイテムを1つ消費
                inventory_item.quantity -= 1
                inventory_item.save()
                player.save()
                
                # 成功メッセージをセッションに保存
                request.session['use_item_message'] = f"SPが{actual_recovery}回復した！"
            
        except PlayerInventory.DoesNotExist:
            request.session['use_item_message'] = "アイテムが見つかりません"
    
    # インベントリー画面に戻る
    category = request.GET.get('category', '全て')
    search_query = request.GET.get('search', '')
    return redirect(f"{reverse('game:inventory', kwargs={'player_id': player.id})}?category={category}&search={search_query}")

def gameover(request):
    # セッションからplayer_idを取得してスコア計算
    player_id = request.session.get('gameover_player_id')
    
    # セッションに保存されたスコアがあればそれを使う
    score = request.session.get('gameover_score', 0)
    initial_point = request.session.get('gameover_initial_point', 0)
    
    # プレイヤーがまだ存在する場合のみ計算と削除を行う
    if player_id and score == 0:
        try:
            player = Player.objects.get(id=player_id)
            # プレイヤーのスコアを計算
            score_data = calculate_score(player)
            score = score_data['total_score']
            initial_point = score // 10000  # スコアの1/10000を初期ポイントとする
            
            # スコアをセッションに保存（内訳から戻った時のため）
            request.session['gameover_score'] = score
            request.session['gameover_initial_point'] = initial_point
            
            # スコア内訳をセッションに保存
            request.session['score_breakdown'] = {
                'hp': player.max_hp,
                'hp_score': score_data['hp_score'],
                'atk': player.atk,
                'atk_score': score_data['atk_score'],
                'defense': player.defense,
                'def_score': score_data['def_score'],
                'spd': player.spd,
                'spd_score': score_data['spd_score'],
                'mp': player.max_mp,
                'mp_score': score_data['mp_score'],
                'equipment_list': [eq.name for eq in player.owned_equipment.all()],
                'equipment_score': score_data['equipment_score'],
                'defeats': player.defeats,
                'defeat_score': score_data['defeat_score'],
                'strong_defeats': player.strong_defeats,
                'strong_defeat_score': score_data['strong_defeat_score'],
                'level': player.level,
                'level_score': score_data['level_score'],
                'total_score': score
            }
            
            # Playerを削除
            player.delete()
            del request.session['gameover_player_id']
            
            # ログインユーザーの場合、アカウントにスコアとポイントを保存
            if request.user.is_authenticated:
                user = request.user
                
                # 最高スコアの場合のみ更新
                if score > user.best_score:
                    user.best_score = score
                
                # 初期ポイントは毎回更新
                user.initial_points = initial_point
                user.total_plays += 1
                user.save()
                
        except Player.DoesNotExist:
            pass
    
    return render(request, 'game/gameover.html', {
        'score': score,
        'initial_point': initial_point,
    })


def score_breakdown(request):
    """スコア内訳を表示"""
    breakdown = request.session.get('score_breakdown', {})
    
    if not breakdown:
        # 内訳データがない場合はゲームオーバー画面にリダイレクト
        return redirect('game:gameover')
    
    return render(request, 'game/score_breakdown.html', {
        'breakdown': breakdown,
    })


def quest(request, player_id):
    """クエスト画面"""
    player = Player.objects.get(id=player_id)
    
    # プレイヤーのクエストを初期化
    initialize_player_quests(player)
    
    # プレイヤーに適用可能なクエストテンプレートを取得（初期クエストのみ）
    # 派生クエストはPlayerQuestから取得されるので、ここでは初期クエストのみ
    life_templates = QuestTemplate.objects.filter(
        quest_type='life',
        is_active=True,
        derivation_level=0  # 初期クエストのみ
    ).filter(
        models.Q(job='all') | models.Q(job=player.job)
    ).order_by('order')[:8]
    
    account_templates = QuestTemplate.objects.filter(
        quest_type='account',
        is_active=True,
        job='all',  # アカウントクエストは全職業共通
        derivation_level=0  # 初期クエストのみ
    ).order_by('order')[:8]
    
    # PlayerQuestを取得（派生クエストも含めて探す）
    life_quests = []
    for template in life_templates:
        # このテンプレートまたはその派生チェーン内のPlayerQuestを探す
        pq = find_quest_in_derivation_chain(player, template)
        life_quests.append(pq)  # Noneの可能性もあるがそのまま追加
    
    account_quests = []
    for template in account_templates:
        # このテンプレートまたはその派生チェーン内のPlayerQuestを探す
        pq = find_quest_in_derivation_chain(player, template)
        account_quests.append(pq)  # Noneの可能性もあるがそのまま追加
    
    # 8つに満たない場合は空で埋める
    while len(life_quests) < 8:
        life_quests.append(None)
    while len(account_quests) < 8:
        account_quests.append(None)
    
    return render(request, 'game/quest.html', {
        'player': player,
        'life_quests': life_quests[:8],
        'account_quests': account_quests[:8],
        'is_guest': player.is_guest,
    })


def claim_quest_reward(request, quest_id):
    """クエスト報酬を受け取る"""
    player_quest = PlayerQuest.objects.get(id=quest_id)
    player = player_quest.player
    quest_type = player_quest.quest_template.quest_type  # クエストタイプを保存
    
    # 達成済みで未受け取りの場合のみ報酬を付与
    if player_quest.is_completed and not player_quest.is_claimed:
        # 報酬を付与
        player.exp += player_quest.quest_template.reward_exp
        player.gold += player_quest.quest_template.reward_gold
        
        # レベルアップ処理
        level_up_player(player)
        
        player.save()
        
        # 派生クエストがあるかチェック
        current_template = player_quest.quest_template
        derived_template = current_template.derived_quest
        
        if derived_template:
            # 派生クエストに置き換える
            print(f"派生クエスト発見: {current_template.title} -> {derived_template.title}")
            
            # 派生クエストのPlayerQuestが既に存在する場合は削除
            # （unique_together制約を回避するため）
            existing_derived = PlayerQuest.objects.filter(
                player=player,
                quest_template=derived_template
            ).exclude(id=player_quest.id).first()
            
            if existing_derived:
                print(f"既存の派生クエストを削除: {existing_derived.id}")
                existing_derived.delete()
            
            # 現在のPlayerQuestを派生クエストに置き換える
            player_quest.quest_template = derived_template
            player_quest.progress_current = 0  # 進捗をリセット
            player_quest.is_completed = False
            player_quest.is_claimed = False
            player_quest.save()
            print(f"派生クエスト保存完了: PlayerQuest ID={player_quest.id}, Template={player_quest.quest_template.title}")
        else:
            print(f"派生クエストなし: {current_template.title}")
            # 派生クエストがない場合は報酬受け取りフラグを立てる
            player_quest.is_claimed = True
            player_quest.save()
    
    # 元のタブに戻るためにクエストタイプをパラメータとして渡す
    return redirect(f"{reverse('game:quest', kwargs={'player_id': player.id})}?tab={quest_type}")


def action_skill_click(request, player_id, enemy_id):
    """アクション特技のクリック時ダメージ処理"""
    from django.http import JsonResponse
    import random
    
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)
    
    player = Player.objects.get(id=player_id)
    enemy = Enemy.objects.get(id=enemy_id)
    
    # アクションモードのデータを取得
    action_data = request.session.get('action_mode')
    if not action_data:
        return JsonResponse({'error': 'No action mode'}, status=400)
    
    # バフ・デバフを取得
    buffs = request.session.get("buffs", {})
    debuffs = request.session.get("debuffs", {})
    
    # ダメージ計算（通常攻撃と同じ計算式）
    multiplier = action_data.get('multiplier', 1.0)
    
    # プレイヤーの攻撃力（バフ・デバフ適用）
    player_atk_buff = buffs.get("player", {}).get("atk", {}).get("multiplier", 1.0)
    player_atk_debuff = debuffs.get("player", {}).get("atk", {}).get("multiplier", 1.0)
    effective_atk = player.total_atk_battle * player_atk_buff * player_atk_debuff
    
    # 敵の防御力（バフ・デバフ適用）
    enemy_def_buff = buffs.get("enemy", {}).get("def", {}).get("multiplier", 1.0)
    enemy_def_debuff = debuffs.get("enemy", {}).get("def", {}).get("multiplier", 1.0)
    effective_def = enemy.defense * enemy_def_buff * enemy_def_debuff
    
    # ダメージ計算
    base_damage = max(1, effective_atk - effective_def)
    damage_variance = random.randint(0, 3)
    damage = int(base_damage * multiplier) + damage_variance
    
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
    """アクション特技終了処理"""
    if request.method != 'POST':
        return redirect('game:battle', player_id=player_id, enemy_id=enemy_id)
    
    player = Player.objects.get(id=player_id)
    enemy = Enemy.objects.get(id=enemy_id)
    
    # セッションからaction_modeを削除
    action_data = request.session.pop('action_mode', None)
    if not action_data:
        return redirect('game:battle', player_id=player_id, enemy_id=enemy_id)
    
    # click_countと累積ダメージを取得
    click_count = int(request.POST.get('click_count', 0))
    total_damage = request.session.pop('action_total_damage', 0)
    
    # メッセージを作成
    message = f"{player.name}の{action_data['skill_name']}！\n"
    message += f"{click_count}回の連続攻撃！ 合計{total_damage}ダメージ！\n"
    
    buffs = request.session.get("buffs", {})
    debuffs = request.session.get("debuffs", {})
    message_history = request.session.get("message_history", [])
    
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


def continue_battle(request, player_id):
    """勝利後、続けて新しい敵と戦う"""
    player = Player.objects.get(id=player_id)
    
    # ステージIDを取得
    stage_id = request.session.get('stage_id')
    if stage_id:
        stage = Stage.objects.get(id=stage_id)
    else:
        stage = Stage.objects.first()
        request.session['stage_id'] = stage.id if stage else None
    
    # 新しい敵を選択
    enemy = select_new_enemy(player, stage, request)
    
    if not enemy:
        # 敵が選択できない場合はホーム画面に戻る
        return redirect('game:battle_start', player_id=player.id)
    
    # バフ・デバフをリセット
    request.session["buffs"] = {}
    request.session["debuffs"] = {}
    request.session["special_states"] = {}
    request.session["message_history"] = []
    
    # 戦闘用HPを素のHPに反映（回復は無し）
    player.sync_hp_from_battle()
    
    # 戦闘画面にリダイレクト
    return redirect('game:battle', player_id=player.id, enemy_id=enemy.id)


def convert_guest_to_user(request, player_id):
    """ゲストプレイヤーをログインユーザーに変換"""
    player = Player.objects.get(id=player_id)
    
    # ゲストプレイヤーでない場合はエラー
    if not player.is_guest:
        return redirect('game:battle_start', player_id=player.id)
    
    # セッションにゲストプレイヤーIDを保存
    request.session['converting_guest_player_id'] = player_id
    
    # サインアップページにリダイレクト
    return redirect('accounts:signup')
