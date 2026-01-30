"""
共通ヘルパー関数を集約するモジュール

複数のviewで使用される共通処理をここに集約します。
これにより、コードの重複を避け、保守性を向上させます。
"""
import random
from django.db import models
from ..models import Player, Enemy, Stage, QuestTemplate, PlayerQuest


# スコアポイント設定（複数の関数で使用されるため、ここに定義）
SCORE_POINT_CONFIG = [
    {"key": "hp", "label": "HP", "base": 100, "inc": 5},
    {"key": "atk", "label": "ATK", "base": 5, "inc": 1},
    {"key": "def", "label": "DEF", "base": 5, "inc": 1},
    {"key": "spd", "label": "SPD", "base": 5, "inc": 1},
    {"key": "mp", "label": "SP", "base": 50, "inc": 5},
    {"key": "gold", "label": "初期G", "base": 100, "inc": 50},
    {"key": "gold_rate", "label": "G獲得倍率", "base": 1.0, "inc": 0.05, "format": "{:.2f}"},
    {"key": "exp_rate", "label": "EXP獲得倍率", "base": 1.0, "inc": 0.05, "format": "{:.2f}"},
]


def _get_score_bonus_dict(user, category_key):
    """スコアボーナス辞書を取得（内部関数）"""
    if not user:
        return {}
    if category_key == "all":
        return user.score_bonus_all or {}
    bonus_jobs = user.score_bonus_jobs or {}
    return bonus_jobs.get(category_key, {})


def _set_score_bonus_dict(user, category_key, bonus_dict):
    """スコアボーナス辞書を設定（内部関数）"""
    if category_key == "all":
        user.score_bonus_all = bonus_dict
    else:
        bonus_jobs = user.score_bonus_jobs or {}
        bonus_jobs[category_key] = bonus_dict
        user.score_bonus_jobs = bonus_jobs


def _combine_score_bonus(user, job):
    """全職業共通ボーナスと職業別ボーナスを結合（内部関数）"""
    all_bonus = user.score_bonus_all or {}
    job_bonus = (user.score_bonus_jobs or {}).get(job, {})
    combined = {}
    for cfg in SCORE_POINT_CONFIG:
        key = cfg["key"]
        combined[key] = int(all_bonus.get(key, 0)) + int(job_bonus.get(key, 0))
    return combined


def _get_score_rates(user, job):
    """ゴールド獲得倍率と経験値獲得倍率を取得（内部関数）"""
    if not user:
        return 1.0, 1.0
    combined = _combine_score_bonus(user, job)
    gold_rate = 1.0 + combined.get("gold_rate", 0) * 0.05
    exp_rate = 1.0 + combined.get("exp_rate", 0) * 0.05
    return gold_rate, exp_rate


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
    - プレイヤーレベル × 300
    
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
        tuple: (message, leveled_up)
            message: レベルアップメッセージを追加した文字列
            leveled_up: レベルアップしたかどうか（bool）
    """
    leveled_up = False
    while player.exp >= player.next_exp:
        player.level += 1
        player.stat_points += 3
        player.exp -= player.next_exp
        player.next_exp = int(300 + player.level * 30 * player.level)
        leveled_up = True
        
        message += f"レベルアップ！ レベル{player.level}になった！ ステータスポイント+3\n"
    
    return message, leveled_up


def get_player_from_request(request, player_id=None):
    """
    リクエストからプレイヤーを取得する
    
    Args:
        request: HTTPリクエスト
        player_id: プレイヤーID（指定された場合はそのIDのプレイヤーを取得）
    
    Returns:
        Player: プレイヤーオブジェクト、見つからない場合はNone
    
    処理の優先順位:
    1. player_idが指定されている場合: そのIDのプレイヤーを取得
    2. ログインユーザーの場合: userに紐付いたプレイヤーを取得
    3. ゲストの場合: セッションからプレイヤーIDを取得
    """
    if player_id:
        try:
            return Player.objects.get(id=player_id)
        except Player.DoesNotExist:
            return None
    
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


def select_new_enemy(player, stage, request):
    """
    新しい敵を選択する共通関数
    
    Args:
        player: プレイヤーオブジェクト
        stage: ステージオブジェクト
        request: リクエストオブジェクト
    
    Returns:
        enemy: 選択された敵オブジェクト（セッションに保存済み）、見つからない場合はNone
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
    def _decrease_turn(container):
        for target in list(container.keys()):
            for key in list(container[target].keys()):
                effect = container[target][key]
                if 'turn' in effect:
                    effect['turn'] -= 1
                    if effect['turn'] <= 0:
                        del container[target][key]
                elif 'turns' in effect:
                    effect['turns'] -= 1
                    if effect['turns'] <= 0:
                        del container[target][key]
            if not container[target]:
                del container[target]

    # バフの減少
    _decrease_turn(buffs)

    # デバフの減少
    _decrease_turn(debuffs)

    # 特殊状態の減少
    _decrease_turn(special_states)
    
    return buffs, debuffs, special_states


# 外部から使用可能な関数をエクスポート
__all__ = [
    'SCORE_POINT_CONFIG',
    'calculate_score',
    'find_quest_in_derivation_chain',
    'initialize_player_quests',
    'level_up_player',
    'get_player_from_request',
    'select_new_enemy',
    'decrease_buff_debuff_turns',
    '_get_score_rates',  # 内部関数だが、他のモジュールで使用される可能性があるためエクスポート
    '_combine_score_bonus',  # 内部関数だが、他のモジュールで使用される可能性があるためエクスポート
]
