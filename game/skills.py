ENEMY_SKILLS = {
    "スライム": [
        {"name": "体当たり", "effects": [
            {"type": "attack", "target": "player", "multiplier": 1.0}
        ], "priority": 5},
        {"name": "ぷにぷにガード", "effects": [
            {"type": "defense", "target": "enemy", "multiplier": 1.0}
        ], "priority": 2},
        {"name": "べとべと液", "effects": [
            {"type": "debuf", "target": "player", "multiplier": 1.0, "stat": "spd", "turn": 3}
        ], "priority": 3},
    ],
    "ゴブリン": [
        {"name": "殴る", "effects": [
            {"type": "attack", "target": "player", "multiplier": 1.0}
        ], "priority": 5},
        {"name": "ガード", "effects": [
            {"type": "defense", "target": "enemy", "multiplier": 1.0}
        ], "priority": 2},
        {"name": "ぶん殴り", "effects": [
            {"type": "attack", "target": "player", "multiplier": 1.5}
        ], "priority": 3},
    ],
    "オーク": [
        {"name": "殴る", "effects": [
            {"type": "attack", "target": "player", "multiplier": 1.0}
        ], "priority": 5},
        {"name": "ガード", "effects": [
            {"type": "defense", "target": "enemy", "multiplier": 1.0}
        ], "priority": 2},
        {"name": "怒り", "effects": [
            {"type": "buf", "target": "enemy", "stat": "atk", "multiplier": 1.5, "turn": 3}
        ], "priority": 3},
    ],
    "スケルトン": [
        {"name": "骨叩き", "effects": [
            {"type": "attack", "target": "player", "multiplier": 1.0}
        ], "priority": 5},
        {"name": "硬い骨", "effects": [
            {"type": "defense", "target": "enemy", "multiplier": 1.0}
        ], "priority": 2},
        {"name": "身軽", "effects": [
            {"type": "buf", "target": "enemy", "stat": "spd", "multiplier": 1.5, "turn": 3}
        ], "priority": 3},
    ],
    "ドラゴン": [
        {"name": "爪ひっかき", "effects": [
            {"type": "attack", "target": "player", "multiplier": 1.0}
        ], "priority": 5},
        {"name": "硬い鱗", "effects": [
            {"type": "defense", "target": "enemy", "multiplier": 1.0}
        ], "priority": 2},
        {"name": "ドラゴンブレス", "effects": [
            {"type": "attack", "target": "player", "multiplier": 2.0}
        ], "priority": 3},
    ],
    "魔法使いゴブリン": [
        {"name": "ファイア", "effects": [
            {"type": "attack", "target": "player", "multiplier": 1.0}
        ], "priority": 5},
        {"name": "シールド", "effects": [
            {"type": "defense", "target": "enemy", "multiplier": 1.0}
        ], "priority": 2},
        {"name": "メテオ", "effects": [
            {"type": "attack", "target": "player", "multiplier": 1.8}
        ], "priority": 3},
    ],
    "騎士の亡霊": [
        {"name": "薙ぎ払い", "effects": [
            {"type": "attack", "target": "player", "multiplier": 1.0}
        ], "priority": 5},
        {"name": "防御姿勢", "effects": [
            {"type": "defense", "target": "enemy", "multiplier": 1.0}
        ], "priority": 2},
        {"name": "士気上げ", "effects": [
            {"type": "buf", "target": "enemy", "stat": "atk", "multiplier": 1.5, "turn": 3},
            {"type": "buf", "target": "enemy", "stat": "def", "multiplier": 1.5, "turn": 3},
            {"type": "buf", "target": "enemy", "stat": "spd", "multiplier": 1.5, "turn": 3}
        ], "priority": 3},
    ],
    "盗賊": [
        {"name": "疾蹴り", "effects": [
            {"type": "attack", "target": "player", "multiplier": 1.0}
        ], "priority": 5},
        {"name": "受け身", "effects": [
            {"type": "defense", "target": "enemy", "multiplier": 1.0}
        ], "priority": 2},
        {"name": "足奪り", "effects": [
            {"type": "buf", "target": "enemy", "stat": "spd", "multiplier": 1.4, "turn": 3},
            {"type": "debuf", "target": "player", "stat": "spd", "multiplier": 0.6, "turn": 3}
        ], "priority": 3},
    ],
}