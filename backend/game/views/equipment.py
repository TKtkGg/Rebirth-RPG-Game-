"""
装備関連のview関数

装備変更画面の表示と装備処理を担当します。
"""
from django.shortcuts import render, redirect
from django.urls import reverse
from ..models import Player, Equipment
from .utils import get_player_from_request


def equipment_change(request, player_id):
    """
    装備変更画面を表示
    
    プレイヤーが所持している武器と防具を表示します。
    初期装備がない場合は自動的に追加します。
    """
    player = get_player_from_request(request, player_id)
    if not player:
        return redirect('game:start')
    
    # 初期装備がない場合は追加
    if not player.owned_equipment.exists():
        try:
            wooden_sword = Equipment.objects.get(name="木の剣")
            leather_armor = Equipment.objects.get(name="皮の服")
            player.owned_equipment.add(wooden_sword, leather_armor)
            if not player.weapon:
                player.weapon = wooden_sword
            if not player.armor:
                player.armor = leather_armor
            player.save()
        except Equipment.DoesNotExist:
            # 初期装備が存在しない場合はスキップ
            pass
    
    # 所持している装備を取得
    owned_weapons = player.owned_equipment.filter(equipment_type='weapon')
    owned_armors = player.owned_equipment.filter(equipment_type='armor')

    current_weapon = player.weapon
    current_armor = player.armor
    base_stats = {
        'atk': player.atk,
        'def': player.defense,
        'spd': player.spd,
        'max_hp': player.max_hp,
    }
    current_totals = {
        'atk': player.total_atk,
        'def': player.total_def,
        'spd': player.total_spd,
        'max_hp': player.total_max_hp,
    }

    return({
        'player': player,
        'owned_weapons': owned_weapons,
        'owned_armors': owned_armors,
        'current_weapon': current_weapon,
        'current_armor': current_armor,
        'base_stats': base_stats,
        'current_totals': current_totals,
    })
    
    # return render(request, 'game/equipment_change.html', {
    #     'player': player,
    #     'owned_weapons': owned_weapons,
    #     'owned_armors': owned_armors,
    # })


def equip_item(request, player_id, equipment_id):
    """
    装備を変更する
    
    プレイヤーが所持している装備を装備します。
    武器の場合は武器スロットに、防具の場合は防具スロットに装備します。
    """
    player = get_player_from_request(request, player_id)
    if not player:
        return redirect('game:start')
    
    try:
        equipment = Equipment.objects.get(id=equipment_id)
    except Equipment.DoesNotExist:
        return redirect('game:equipment_change', player_id=player.id)
    
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
