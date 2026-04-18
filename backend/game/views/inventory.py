"""
インベントリ関連のview関数

持ち物画面の表示とアイテム使用処理を担当します。
"""
from django.shortcuts import render, redirect
from django.urls import reverse
from ..models import Player, PlayerInventory
from .utils import get_player_from_request


def inventory(request, player_id):
    """
    持ち物画面を表示
    
    プレイヤーが所持しているアイテムを表示します。
    カテゴリーフィルターと検索機能に対応しています。
    """
    player = get_player_from_request(request, player_id)
    if not player:
        return redirect('game:start')
    
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
    
    return {
        'player': player,
        'inventory_items': inventory_items,
        'selected_item': selected_item,
        'category': category,
        'search_query': search_query,
        'use_message': use_message,
    }
    
    # return render(request, 'game/inventory.html', {
    #     'player': player,
    #     'inventory_items': inventory_items,
    #     'selected_item': selected_item,
    #     'category': category,
    #     'search_query': search_query,
    #     'use_message': use_message,
    # })


def use_inventory_item(request, player_id, inventory_item_id):
    """
    インベントリーからアイテムを使用する
    
    POSTリクエストでアイテムIDを受け取り、アイテムを使用します。
    HP回復アイテムの場合はHPを回復、SP回復アイテムの場合はSPを回復します。
    """
    if request.method != 'POST':
        return redirect('game:inventory', player_id=player_id)
    
    player = get_player_from_request(request, player_id)
    if not player:
        return redirect('game:start')
    
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
    
    player.update_battle_stats()
    player.save()
    
    # インベントリー画面に戻る
    category = request.GET.get('category', '全て')
    search_query = request.GET.get('search', '')

    return {
        'category': category,
        'search_query': search_query,
    }

    # return redirect(f"{reverse('game:inventory', kwargs={'player_id': player.id})}?category={category}&search={search_query}")
