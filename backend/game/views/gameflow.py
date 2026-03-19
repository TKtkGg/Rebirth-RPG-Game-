"""
ゲームフロー関連のview関数

ゲームの開始、ステージ選択、ゲームオーバーなどのゲームフローを担当します。
"""
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from ..models import Player, Stage, Equipment
from ..scorepoints_content import SCORE_POINT_CONFIG, JOB_CONFIG_KEY_MAP
from .utils import (
    get_player_from_request,
    initialize_player_quests,
    calculate_score,
    select_new_enemy,
    get_job_bonus_values,
)


def home(request):
    """ホーム画面を表示"""
    return render(request, 'game/home.html')


def stage_select(request, player_id):
    """
    ステージ選択画面を表示
    
    プレイヤーが戦闘するステージを選択します。
    """
    player = get_player_from_request(request, player_id)
    if not player:
        return redirect('game:start')
    
    stages = Stage.objects.all().order_by('order')
    
    return render(request, 'game/stage_select.html', {
        'player': player,
        'stages': stages,
    })

def format_job_bonus(user, job_key):
    config_key = JOB_CONFIG_KEY_MAP.get(job_key)
    if not config_key:
        return ""
    config_list = SCORE_POINT_CONFIG.get(config_key, [])
    if not config_list:
        return ""
    bonus_values = {}
    if user and user.is_authenticated:
        bonus_values = get_job_bonus_values(user, job_key)
    key_label_map = {
        "job_bonus_hp": "HP",
        "job_bonus_atk": "ATK",
        "job_bonus_def": "DEF",
        "job_bonus_spd": "SPD",
        "job_bonus_mp": "SP",
    }
    parts = []
    for cfg in config_list:
        if not cfg.get("key", "").startswith("job_bonus_"):
            continue
        value = cfg.get("base")
        if value is None:
            continue
        if cfg["key"] in bonus_values:
            value = bonus_values.get(cfg["key"], value)
        if value == 0:
            continue
        label = key_label_map.get(cfg.get("key"), "")
        if not label:
            continue
        if isinstance(value, (int, float)) and float(value).is_integer():
            value_text = f"{int(value):+d}"
        else:
            value_text = f"{value:+.1f}"
        parts.append(f"{label} {value_text}")
    return " , ".join(parts)


def build_job_slots(user, available_jobs):
    job_definitions_base = [
        {
            "key": "戦士",
            "icon": "game/img/アイコン/武器_アイコン.png",
            "description": "体力、攻撃力、防御力が高いが、スピードは遅め。",
        },
        {
            "key": "魔法使い",
            "icon": "game/img/アイコン/魔法の杖_アイコン.png",
            "description": "高い攻撃力を持つが、打たれ弱い。",
        },
        {
            "key": "忍者",
            "icon": "game/img/アイコン/忍者_アイコン.png",
            "description": "攻撃力、スピードのあるジョブ。他はフツー。",
        },
        {
            "key": "格闘家",
            "icon": "game/img/アイコン/格闘_アイコン.png",
            "description": "攻撃力に特に優れたジョブ。体力と気力が少し低め。",
        },
        {
            "key": "侍",
            "icon": "game/img/アイコン/武器_アイコン.png",
            "description": "一瞬の見切りで勝機を掴む剣士。",
        },
    ]
    job_slots = []
    for jd in job_definitions_base:
        job_slots.append({
            "name": jd["key"],
            "icon": jd["icon"],
            "description": jd["description"],
            "bonus": format_job_bonus(user, jd["key"]),
            "unlocked": jd["key"] in available_jobs,
        })
    while len(job_slots) < 8:
        job_slots.append({
            "name": "",
            "icon": "game/img/アイコン/はてな_アイコン.png",
            "description": "",
            "bonus": "",
            "unlocked": False,
        })
    return job_slots

def start_game(request):
    """
    職業選択画面（ログインユーザー/ゲスト両対応）
    
    プレイヤーが職業を選択してゲームを開始します。
    ログインユーザーの場合はスコアボーナスが適用されます。
    """
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
    
    default_jobs = ["戦士", "魔法使い", "忍者", "格闘家", "侍"]
    unlocked_jobs = []
    if request.user.is_authenticated:
        unlocked_jobs = request.user.unlocked_jobs or []
    available_jobs = list(dict.fromkeys(default_jobs + unlocked_jobs))

    if request.method == 'POST':
        name = request.POST.get('name')
        job = request.POST.get('job', '戦士')  # デフォルトは戦士
        if job not in available_jobs:
            job = '戦士'

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
            stat_points = 0
        elif job == "魔法使い":
            base_hp, base_atk, base_def, base_spd, base_mp = 100, 5, 5, 5, 50
            job_bonus_hp, job_bonus_atk, job_bonus_def, job_bonus_spd, job_bonus_mp = -5, 10, -2, 0, +10
            stat_points = 0
        elif job == "忍者":
            base_hp, base_atk, base_def, base_spd, base_mp = 100, 5, 5, 5, 50
            job_bonus_hp, job_bonus_atk, job_bonus_def, job_bonus_spd, job_bonus_mp = -5, 3, 0, 5, 0
            stat_points = 0
        elif job == "格闘家":
            base_hp, base_atk, base_def, base_spd, base_mp = 100, 5, 5, 5, 50
            job_bonus_hp, job_bonus_atk, job_bonus_def, job_bonus_spd, job_bonus_mp = -20, 8, 3, 5, -10
            stat_points = 0
        elif job == "侍":
            base_hp, base_atk, base_def, base_spd, base_mp = 100, 5, 5, 5, 50
            job_bonus_hp, job_bonus_atk, job_bonus_def, job_bonus_spd, job_bonus_mp = -10, 10, 0, 5, -20
            stat_points = 0
        else:
            base_hp, base_atk, base_def, base_spd, base_mp = 100, 5, 5, 5, 50
            job_bonus_hp, job_bonus_atk, job_bonus_def, job_bonus_spd, job_bonus_mp = 0, 0, 0, 0, 0
            stat_points = 0

        job_bonus_values = {}
        if request.user.is_authenticated:
            job_bonus_values = get_job_bonus_values(request.user, job)
            job_bonus_hp = int(job_bonus_values.get("job_bonus_hp", job_bonus_hp))
            job_bonus_atk = int(job_bonus_values.get("job_bonus_atk", job_bonus_atk))
            job_bonus_def = int(job_bonus_values.get("job_bonus_def", job_bonus_def))
            job_bonus_spd = int(job_bonus_values.get("job_bonus_spd", job_bonus_spd))
            job_bonus_mp = int(job_bonus_values.get("job_bonus_mp", job_bonus_mp))

        all_defaults = {cfg["key"]: cfg["base"] for cfg in SCORE_POINT_CONFIG.get("all", [])}
        base_gold = int(all_defaults.get("gold", 100))
        if request.user.is_authenticated:
            all_bonus = request.user.score_bonus_all or {}
            base_hp = int(all_bonus.get("hp", all_defaults.get("hp", base_hp)))
            base_atk = int(all_bonus.get("atk", all_defaults.get("atk", base_atk)))
            base_def = int(all_bonus.get("def", all_defaults.get("def", base_def)))
            base_spd = int(all_bonus.get("spd", all_defaults.get("spd", base_spd)))
            base_mp = int(all_bonus.get("mp", all_defaults.get("mp", base_mp)))
            base_gold = int(all_bonus.get("gold", all_defaults.get("gold", base_gold)))

        bonus_hp = bonus_atk = bonus_def = bonus_spd = bonus_mp = 0
        if request.user.is_authenticated:
            bonus_hp = request.user.bonus_hp
            bonus_atk = request.user.bonus_atk
            bonus_def = request.user.bonus_def
            bonus_spd = request.user.bonus_spd
        
        # 初期装備をデータベースから取得
        try:
            wooden_sword = Equipment.objects.get(name="木の剣")
            leather_armor = Equipment.objects.get(name="革の服")
        except Equipment.DoesNotExist:
            # 初期装備が存在しない場合はエラー
            return render(request, 'game/start.html', {
                'default_name': request.user.username if request.user.is_authenticated and not force_guest else "",
                'error': '初期装備が見つかりません。データベースを確認してください。'
            })
        
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
                max_hp=base_hp + job_bonus_hp + bonus_hp,
                hp=base_hp + job_bonus_hp + bonus_hp,
                atk=base_atk + job_bonus_atk + bonus_atk,
                defense=base_def + job_bonus_def + bonus_def,
                spd=base_spd + job_bonus_spd + bonus_spd,
                max_mp=base_mp + job_bonus_mp + bonus_mp,
                mp=base_mp + job_bonus_mp + bonus_mp,
                stat_points=stat_points,
                job=job,
                weapon=wooden_sword,
                armor=leather_armor,
                gold=base_gold,
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
    
    job_slots = build_job_slots(request.user, available_jobs)

    return render(request, 'game/start.html', {
        'default_name': default_name,
        'job_slots': job_slots,
    })


def gameover(request):
    """
    ゲームオーバー画面を表示
    
    プレイヤーが敗北した際にスコアを計算し、ゲームオーバー画面を表示します。
    ログインユーザーの場合はスコアポイントを加算します。
    """
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
            initial_point = score // 5000  # スコアの1/5000を初期ポイントとする
            
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
                    user.best_score_job = player.job
                
                # スコアポイントを加算（永続）
                user.score_points += initial_point
                user.initial_points = user.score_points
                user.total_plays += 1

                # 強敵討伐数の最高記録を更新
                if player.strong_defeats > user.best_strong_defeats:
                    user.best_strong_defeats = player.strong_defeats
                    user.best_strong_defeats_job = player.job

                # 勝利回数の最高記録を更新（戦闘勝利数）
                if player.defeats > user.best_victories:
                    user.best_victories = player.defeats
                    user.best_victories_job = player.job
                user.save()
                
        except Player.DoesNotExist:
            pass
    
    return render(request, 'game/gameover.html', {
        'score': score,
        'initial_point': initial_point,
        'is_guest': not request.user.is_authenticated,
    })


def convert_guest_to_user(request, player_id):
    """
    ゲストプレイヤーをログインユーザーに変換
    
    ゲストプレイヤーをログインユーザーに紐付けるための準備を行います。
    実際の変換処理は accounts アプリで行われます。
    """
    player = get_player_from_request(request, player_id)
    if not player:
        return redirect('game:start')
    
    # ゲストプレイヤーでない場合はエラー
    if not player.is_guest:
        return redirect('game:battle_start', player_id=player.id)
    
    # セッションにゲストプレイヤーIDを保存
    request.session['converting_guest_player_id'] = player_id
    
    # サインアップページにリダイレクト
    return redirect('accounts:signup')


def continue_battle(request, player_id):
    """
    勝利後、続けて新しい敵と戦う
    
    戦闘に勝利した後、新しい敵を選択して戦闘を続行します。
    バフ・デバフはリセットされます。
    """
    player = get_player_from_request(request, player_id)
    if not player:
        return redirect('game:start')
    
    # ステージIDを取得
    stage_id = request.session.get('stage_id')
    if stage_id:
        try:
            stage = Stage.objects.get(id=stage_id)
        except Stage.DoesNotExist:
            stage = Stage.objects.first()
            request.session['stage_id'] = stage.id if stage else None
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
