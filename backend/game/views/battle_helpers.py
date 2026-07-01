"""
battle.pyの補助処理（内部関数ではない共通処理）
"""
from ..models import Stage, PlayerInventory
from ..skills import PLAYER_SKILLS


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
