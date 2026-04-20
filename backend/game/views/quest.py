"""
クエスト関連のview関数

クエスト画面の表示と報酬受け取り処理を担当します。
"""
from django.shortcuts import render, redirect
from django.urls import reverse
from django.db import models
from ..models import Player, QuestTemplate, PlayerQuest
from .utils import get_player_from_request, find_quest_in_derivation_chain, initialize_player_quests, level_up_player, _get_score_rates


def quest(request, player_id):
    """
    クエスト画面を表示
    
    プレイヤーに適用可能なクエスト（ライフクエストとアカウントクエスト）を表示します。
    派生クエストシステムに対応しています。
    """
    player = get_player_from_request(request, player_id)
    if not player:
        return redirect('game:start')
    
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
    

    return ({
        'player': player,
        'life_quests': life_quests[:8],
        'account_quests': account_quests[:8],
        'is_guest': player.is_guest,
    })
    
    # return render(request, 'game/quest.html', {
    #     'player': player,
    #     'life_quests': life_quests[:8],
    #     'account_quests': account_quests[:8],
    #     'is_guest': player.is_guest,
    # })


def claim_quest_reward(request, quest_id):
    """
    クエスト報酬を受け取る
    
    達成済みで未受け取りのクエストの報酬を付与します。
    派生クエストがある場合は、現在のクエストを派生クエストに置き換えます。
    """
    try:
        player_quest = PlayerQuest.objects.get(id=quest_id)
    except PlayerQuest.DoesNotExist:
        return redirect('game:start')
    
    player = player_quest.player
    quest_type = player_quest.quest_template.quest_type  # クエストタイプを保存
    
    # 達成済みで未受け取りの場合のみ報酬を付与
    if player_quest.is_completed and not player_quest.is_claimed:
        # 報酬を付与
        reward_exp = player_quest.quest_template.reward_exp
        reward_gold = player_quest.quest_template.reward_gold
        if player.user:
            gold_rate, exp_rate = _get_score_rates(player.user, player.job)
            reward_exp = int(reward_exp * exp_rate)
            reward_gold = int(reward_gold * gold_rate)
        player.exp += reward_exp
        player.gold += reward_gold
        
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
