"""
ショップ関連のview関数

ショップ画面の表示とアイテム購入処理を担当します。
"""
import json
import random
from django.shortcuts import render, redirect
from ..models import Player, Equipment, Item, PlayerQuest, PlayerInventory
from .utils import get_player_from_request


def shop(request, player_id):
    """
    ショップページを表示
    
    セッションに保存されたショップ在庫を表示します。
    在庫が存在しない場合は、プレイヤーレベルに応じたアイテムをランダムに選択して表示します。
    """
    player = get_player_from_request(request, player_id)
    if not player:
        return redirect('game:start')
    
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
    """
    アイテム購入処理
    
    POSTリクエストでアイテム名、価格、タイプを受け取り、購入処理を行います。
    装備の場合は所持装備に追加、アイテムの場合は在庫を減らしてPlayerInventoryに追加します。
    """
    if request.method != 'POST':
        return redirect('game:shop', player_id=player_id)
    
    player = get_player_from_request(request, player_id)
    if not player:
        return redirect('game:start')
    
    item_name = request.POST.get('item_name')
    item_id = request.POST.get('item_id')
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
            equipment = None
            if item_id:
                equipment = Equipment.objects.filter(id=item_id, equipment_type=item_type).first()
            if not equipment:
                equipment = Equipment.objects.filter(name=item_name, equipment_type=item_type).first()
            if equipment:
                # プレイヤーの所持装備に追加（is_purchasedは更新しない）
                player.owned_equipment.add(equipment)
                # ショップ在庫から削除（売り切れ扱い）
                shop_inventory = request.session.get('shop_inventory', [])
                shop_inventory = [
                    item_data for item_data in shop_inventory
                    if not (
                        item_data.get('type') == 'equipment' and
                        item_data.get('id') == equipment.id
                    )
                ]
                request.session['shop_inventory'] = shop_inventory
        # Itemの場合は在庫を減らし、PlayerInventoryに追加
        elif item_type == 'item':
            # ショップ在庫を取得
            shop_inventory = request.session.get('shop_inventory', [])
            
            # 該当アイテムの在庫を減らす
            for item_data in shop_inventory:
                if item_data['type'] == 'item':
                    item = Item.objects.filter(id=item_data['id']).first()
                    if item and (
                        (item_id and str(item.id) == str(item_id)) or
                        (item_name and item.name == item_name)
                    ):
                        current_stock = item_data.get('current_stock', item.max_stock)
                        item_data['current_stock'] = max(0, current_stock - item_quantity)
                        
                        # PlayerInventoryに追加
                        inventory_item, created = PlayerInventory.objects.get_or_create(
                            player=player,
                            item=item
                        )
                        inventory_item.quantity += item_quantity
                        inventory_item.save()
                        # 在庫が0になったらショップから削除
                        if item_data['current_stock'] <= 0:
                            item_data['remove'] = True
                        break
            
            # セッションを更新
            request.session['shop_inventory'] = [
                data for data in shop_inventory if not data.get('remove')
            ]
        
        # セッションに今回のショップで購入済みのアイテムを追加（装備のみ）
        if item_type in ['weapon', 'armor']:
            session_purchased = request.session.get('session_purchased_items', [])
            if item_name not in session_purchased:
                session_purchased.append(item_name)
                request.session['session_purchased_items'] = session_purchased
    
    # ショップに戻る
    return redirect('game:shop', player_id=player.id)
