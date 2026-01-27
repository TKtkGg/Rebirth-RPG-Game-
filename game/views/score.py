"""
スコア関連のview関数

スコア内訳画面とスコアポイント振り分け画面を担当します。
"""
from django.shortcuts import render, redirect
from django.urls import reverse
from .utils import SCORE_POINT_CONFIG, _get_score_bonus_dict, _set_score_bonus_dict


def score_breakdown(request):
    """
    スコア内訳を表示
    
    セッションに保存されたスコア内訳を表示します。
    内訳データがない場合はゲームオーバー画面にリダイレクトします。
    """
    breakdown = request.session.get('score_breakdown', {})
    
    if not breakdown:
        # 内訳データがない場合はゲームオーバー画面にリダイレクト
        return redirect('game:gameover')
    
    return render(request, 'game/score_breakdown.html', {
        'breakdown': breakdown,
    })


def score_points(request):
    """
    スコアポイント振り分け画面
    
    ログインユーザーがスコアポイントを振り分けて、次回プレイ時の初期ステータスを強化できます。
    全職業共通ボーナスと職業別ボーナスに対応しています。
    """
    if not request.user.is_authenticated:
        return redirect('game:start')

    user = request.user
    default_jobs = ["戦士", "魔法使い", "忍者", "格闘家"]
    unlocked = user.unlocked_jobs or []
    job_list = [job for job in default_jobs if job in unlocked] or default_jobs

    category_key = request.GET.get('category', 'all')
    if category_key != 'all' and category_key not in job_list:
        category_key = 'all'

    if request.method == 'POST':
        stat_key = request.POST.get('stat')
        category_key = request.POST.get('category', 'all')
        if category_key != 'all' and category_key not in job_list:
            category_key = 'all'
        if stat_key and user.score_points > 0:
            valid_keys = {cfg["key"] for cfg in SCORE_POINT_CONFIG}
            if stat_key in valid_keys:
                bonus_dict = _get_score_bonus_dict(user, category_key)
                bonus_dict[stat_key] = int(bonus_dict.get(stat_key, 0)) + 1
                user.score_points -= 1
                _set_score_bonus_dict(user, category_key, bonus_dict)
                user.initial_points = user.score_points
                user.save()
        return redirect(f"{reverse('game:score_points')}?category={category_key}")

    bonus_dict = _get_score_bonus_dict(user, category_key)
    stat_items = []
    for idx, cfg in enumerate(SCORE_POINT_CONFIG):
        count = int(bonus_dict.get(cfg["key"], 0))
        current_value = cfg["base"] + count * cfg["inc"]
        next_value = cfg["base"] + (count + 1) * cfg["inc"]
        if cfg.get("format"):
            current_text = cfg["format"].format(current_value)
            next_text = cfg["format"].format(next_value)
        else:
            current_text = str(int(current_value))
            next_text = str(int(next_value))
        card_class = "stat-card-bottom" if idx >= 6 else "stat-card"
        stat_items.append({
            "key": cfg["key"],
            "label": cfg["label"],
            "current": current_text,
            "next": next_text,
            "card_class": card_class,
        })

    categories = [{"key": "all", "label": "全て"}] + [
        {"key": job, "label": job} for job in job_list
    ]

    return render(request, 'game/score_points.html', {
        'categories': categories,
        'category_key': category_key,
        'stat_items': stat_items,
        'score_points': user.score_points,
    })
