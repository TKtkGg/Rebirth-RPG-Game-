ENEMY_SKILLS = {
    "スライム": [
        {"name": "体当たり", "effects": [
            {"type": "attack", "target": "player", "multiplier": 1.0}
        ], "priority": 5},
        {"name": "ぷにぷにガード", "effects": [
            {"type": "defense", "target": "enemy", "multiplier": 1.0}
        ], "priority": 2},
        {"name": "べとべと液", "effects": [
            {"type": "debuf", "target": "player", "multiplier": 0.6, "stat": "spd", "turn": 3}
        ], "priority": 3, "max_uses": 5},
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
        ], "priority": 3, "max_uses": 4},
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
        ], "priority": 3, "max_uses": 3},
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
        ], "priority": 3, "max_uses": 3},
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
        ], "priority": 3, "max_uses": 5},
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
        ], "priority": 3, "max_uses": 4},
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
        ], "priority": 3, "max_uses": 3},
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
        ], "priority": 3, "max_uses": 5},
    ],
}

# プレイヤースキル定義
PLAYER_SKILLS = {
    "戦士": [
        {
            "name": "渾身斬り",
            "cost": 12,
            "description": "全力で敵を斬りつける強力な攻撃",
            "effects": [
                {
                    "type": "attack",
                    "target": "enemy",
                    "multiplier": 2.0
                }
            ]
        },
        {
            "name": "身体強化",
            "cost": 10,
            "description": "自身の攻撃力と防御力を一時的に上昇させる",
            "effects": [
                {
                    "type": "buf",
                    "target": "player",
                    "stat": "atk",
                    "multiplier": 1.3,
                    "turn": 4
                },
                {
                    "type": "buf",
                    "target": "player",
                    "stat": "def",
                    "multiplier": 1.3,
                    "turn": 4
                }
            ]
        },
        {
            "name": "気迫",
            "cost": 10,
            "description": "敵を威嚇して攻撃力、防御力を下げる",
            "effects": [
                {
                    "type": "debuf",
                    "target": "enemy",
                    "stat": "atk",
                    "multiplier": 0.7,
                    "turn": 4
                },
                {
                    "type": "debuf",
                    "target": "enemy",
                    "stat": "def",
                    "multiplier": 0.7,
                    "turn": 4
                },
            ]
        },
    ],
    "魔法使い": [
        {
            "name": "インパクトメテオ",
            "cost": 30,
            "description": "一撃必殺の超火力で焼き払う",
            "effects": [
                {
                    "type": "attack",
                    "target": "enemy",
                    "multiplier": 3.0
                }
            ]
        },
        {
            "name": "魔力強化",
            "cost": 20,
            "description": "魔力を高めて攻撃力を上げる",
            "effects": [
                {
                    "type": "buf",
                    "target": "player",
                    "stat": "atk",
                    "multiplier": 2.0,
                    "turn": 3
                }
            ]
        },
        {
            "name": "マジックシールド",
            "cost": 20,
            "description": "魔法の盾で敵の攻撃を防ぐ",
            "effects": [
                {
                    "type": "buf",
                    "target": "player",
                    "stat": "def",
                    "multiplier": 3.0,
                    "turn": 2
                }
            ]

        }
    ],
    "忍者": [
        {
            "name": "影分身の術",
            "cost": 15,
            "description": "分身を作り出し、敵の攻撃を回避しやすくする",
            "effects": [
                {
                    "type": "buf",
                    "target": "player",
                    "stat": "spd",
                    "multiplier": 1.5,
                    "turn": 4
                }
            ]
        },
        {
            "name": "急所突き",
            "cost": 20,
            "description": "敵の急所を狙い、通常よりも大きなダメージを与える攻撃",
            "effects": [
                {
                    "type": "attack",
                    "target": "enemy",
                    "multiplier": 2.5
                }
            ]
        },
        {
            "name": "毒刃",
            "cost": 15,
            "description": "攻撃に毒の効果を付与し、敵に継続ダメージを与える",
            "effects": [
                {
                    "type": "attack",
                    "target": "enemy",
                    "multiplier": 1.0
                },
                {
                    "type": "debuf",
                    "target": "enemy",
                    "stat": "hp",
                    "multiplier": 0.9,
                    "turn": 5
                }
            ]
        }
    ],
    # 他の職業も追加可能
}
