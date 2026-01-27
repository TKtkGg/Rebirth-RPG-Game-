"""
views パッケージの初期化ファイル

分割したview関数をエクスポートして、既存の urls.py との互換性を保ちます。
これにより、urls.py の `from . import views` がそのまま動作します。
"""
# 戦闘関連
from .battle import battle, battle_start, action_skill_click, action_skill_end

# ショップ関連
from .shop import shop, buy_item

# 装備関連
from .equipment import equipment_change, equip_item

# インベントリ関連
from .inventory import inventory, use_inventory_item

# クエスト関連
from .quest import quest, claim_quest_reward

# スコア関連
from .score import score_breakdown, score_points

# ゲームフロー関連
from .gameflow import home, start_game, stage_select, gameover, convert_guest_to_user, continue_battle

# ユーティリティ関数（必要に応じてエクスポート）
from .utils import (
    calculate_score,
    level_up_player,
    initialize_player_quests,
    get_player_from_request,
    select_new_enemy,
    SCORE_POINT_CONFIG,
)

# すべての関数をエクスポート（urls.py との互換性のため）
__all__ = [
    # 戦闘関連
    'battle',
    'battle_start',
    'action_skill_click',
    'action_skill_end',
    # ショップ関連
    'shop',
    'buy_item',
    # 装備関連
    'equipment_change',
    'equip_item',
    # インベントリ関連
    'inventory',
    'use_inventory_item',
    # クエスト関連
    'quest',
    'claim_quest_reward',
    # スコア関連
    'score_breakdown',
    'score_points',
    # ゲームフロー関連
    'home',
    'start_game',
    'stage_select',
    'gameover',
    'convert_guest_to_user',
    'continue_battle',
    # ユーティリティ関数
    'calculate_score',
    'level_up_player',
    'initialize_player_quests',
    'get_player_from_request',
    'select_new_enemy',
    'SCORE_POINT_CONFIG',
]
