# Django Webゲーム リファクタリング方針書

## 1. リファクタリング方針の全体像

### 現状の問題点

1. **views.py の肥大化**
   - 2683行の単一ファイルに31個の関数が集約
   - 戦闘、ショップ、装備、クエスト、スコア計算など異なる責務が混在
   - 関数の依存関係が把握しにくい
   - 新機能追加時に影響範囲が不明確

2. **HTML/CSS/JavaScript の混在**
   - `battle.html` に644行のCSS、1719行のJavaScriptが直書き
   - `shop.html` にも400行のCSS、270行のJavaScriptが直書き
   - スタイルやロジックの再利用が困難
   - デバッグやメンテナンスが困難

3. **ディレクトリ構造の不足**
   - `static` ディレクトリが未作成（settings.pyでは設定済み）
   - CSS/JSファイルの配置場所が不明確

### 改善方針

**原則：Django の標準的な構成に従い、初学者が理解しやすい構造にする**

1. **views.py の分割**
   - 機能・責務単位でファイル分割
   - 各ファイルは200-300行程度に収める
   - 共通処理は `utils.py` に集約

2. **HTML/CSS/JavaScript の分離**
   - CSS は `game/static/game/css/` に配置
   - JavaScript は `game/static/game/js/` に配置
   - テンプレートは構造（HTML）のみを担当

3. **命名規則の統一**
   - ファイル名はスネークケース（`battle_views.py`）
   - 関数名は明確な動詞で始める（`calculate_damage` など）

---

## 2. 改善前によくあるアンチパターン

### ❌ アンチパターン1: 巨大な views.py
```python
# 2683行の単一ファイル
# - 戦闘ロジック
# - ショップロジック
# - 装備ロジック
# - クエストロジック
# - スコア計算
# すべてが混在
```

**問題点：**
- 関数を探すのに時間がかかる
- 変更時の影響範囲が不明確
- コードレビューが困難

### ❌ アンチパターン2: HTML 内に CSS/JS を直書き
```html
{% block content %}
<style>
    /* 644行のCSS */
</style>
<script>
    /* 1719行のJavaScript */
</script>
<div>...</div>
{% endblock %}
```

**問題点：**
- ブラウザキャッシュが効かない
- 他のページで再利用できない
- デバッグが困難

### ❌ アンチパターン3: 責務が曖昧な関数
```python
def battle(request, player_id, enemy_id=None):
    # プレイヤー取得
    # 敵選択
    # 戦闘ロジック
    # レベルアップ処理
    # クエスト更新
    # セッション管理
    # レンダリング
    # すべてが1つの関数内
```

**問題点：**
- 単一責任の原則に違反
- テストが困難
- 再利用できない

---

## 3. 推奨ディレクトリ構成

```
mysite/
├── game/
│   ├── views/
│   │   ├── __init__.py          # 全view関数をエクスポート
│   │   ├── battle.py             # 戦闘関連のview（battle, battle_start, action_skill_*）
│   │   ├── shop.py               # ショップ関連のview（shop, buy_item）
│   │   ├── equipment.py          # 装備関連のview（equipment_change, equip_item）
│   │   ├── inventory.py          # インベントリ関連のview（inventory, use_inventory_item）
│   │   ├── quest.py              # クエスト関連のview（quest, claim_quest_reward）
│   │   ├── score.py              # スコア関連のview（score_breakdown, score_points）
│   │   ├── gameflow.py           # ゲームフロー関連（home, start_game, stage_select, gameover）
│   │   └── utils.py              # 共通ヘルパー関数（calculate_score, level_up_player など）
│   ├── static/
│   │   └── game/
│   │       ├── css/
│   │       │   ├── battle.css
│   │       │   ├── shop.css
│   │       │   └── common.css
│   │       └── js/
│   │           ├── battle.js
│   │           ├── shop.js
│   │           └── common.js
│   ├── templates/
│   │   └── game/
│   │       ├── battle.html       # CSS/JSは外部ファイル参照
│   │       ├── shop.html         # CSS/JSは外部ファイル参照
│   │       └── ...
│   └── ...
```

---

## 4. views.py 分割例

### 4.1 ファイル名: `views/battle.py`
**役割：** 戦闘画面の表示と戦闘ロジックの処理

**含まれる関数：**
- `battle()` - メインの戦闘処理
- `battle_start()` - 戦闘開始画面
- `action_skill_click()` - アクションスキルのクリック処理
- `action_skill_end()` - アクションスキルの終了処理
- `continue_battle()` - 続けて戦う処理

**最小コード例：**
```python
from django.shortcuts import render, redirect
from django.http import JsonResponse
from ..models import Player, Enemy, Stage
from ..skills import PLAYER_SKILLS
from .utils import get_player_from_request, select_new_enemy

def battle(request, player_id, enemy_id=None):
    """戦闘画面のメイン処理"""
    player = get_player_from_request(request, player_id)
    if not player:
        return redirect('game:start')
    
    # 戦闘ロジック（既存の処理をそのまま移行）
    # ...
    
    return render(request, "game/battle.html", context)
```

### 4.2 ファイル名: `views/shop.py`
**役割：** ショップ画面の表示と購入処理

**含まれる関数：**
- `shop()` - ショップ画面表示
- `buy_item()` - アイテム購入処理

**最小コード例：**
```python
from django.shortcuts import render, redirect
from ..models import Player, Equipment, Item

def shop(request, player_id):
    """ショップ画面を表示"""
    player = get_player_from_request(request, player_id)
    if not player:
        return redirect('game:start')
    
    weapons = Equipment.objects.filter(equipment_type='weapon', appear_level__lte=player.level)
    armors = Equipment.objects.filter(equipment_type='armor', appear_level__lte=player.level)
    items = Item.objects.filter(appear_level__lte=player.level)
    
    return render(request, "game/shop.html", {
        'player': player,
        'weapons': weapons,
        'armors': armors,
        'items': items,
    })
```

### 4.3 ファイル名: `views/utils.py`
**役割：** 複数のviewで使用される共通ヘルパー関数

**含まれる関数：**
- `get_player_from_request()` - プレイヤー取得（エラーハンドリング込み）
- `calculate_score()` - スコア計算
- `level_up_player()` - レベルアップ処理
- `initialize_player_quests()` - クエスト初期化
- `_get_score_bonus_dict()` - スコアボーナス取得（内部関数）

**最小コード例：**
```python
from django.shortcuts import redirect
from ..models import Player

def get_player_from_request(request, player_id=None):
    """リクエストからプレイヤーを安全に取得"""
    try:
        if player_id:
            return Player.objects.get(id=player_id)
        # player_idがNoneの場合の処理
        return None
    except Player.DoesNotExist:
        return None
```

### 4.4 ファイル名: `views/__init__.py`
**役割：** 分割したview関数をエクスポートして、既存の `urls.py` との互換性を保つ

**最小コード例：**
```python
# 既存の import 文を維持するため、すべての関数をエクスポート
from .battle import battle, battle_start, action_skill_click, action_skill_end, continue_battle
from .shop import shop, buy_item
from .equipment import equipment_change, equip_item
from .inventory import inventory, use_inventory_item
from .quest import quest, claim_quest_reward
from .score import score_breakdown, score_points
from .gameflow import home, start_game, stage_select, gameover, convert_guest_to_user
from .utils import calculate_score, level_up_player, initialize_player_quests

# これにより、urls.py の `from . import views` がそのまま動作する
__all__ = [
    'battle', 'battle_start', 'action_skill_click', 'action_skill_end', 'continue_battle',
    'shop', 'buy_item',
    'equipment_change', 'equip_item',
    'inventory', 'use_inventory_item',
    'quest', 'claim_quest_reward',
    'score_breakdown', 'score_points',
    'home', 'start_game', 'stage_select', 'gameover', 'convert_guest_to_user',
    'calculate_score', 'level_up_player', 'initialize_player_quests',
]
```

---

## 5. templates / static の分離例

### 5.1 HTML 側の責務
- **構造のみを担当**：要素の配置、データの表示
- **CSS/JS は外部ファイル参照**：`{% load static %}` と `<link>`, `<script>` タグで読み込む

**改善後の battle.html（冒頭部分）：**
```html
{% extends 'game/base.html' %}
{% load static %}
{% block title %}バトル{% endblock %}

{% block extra_css %}
<link rel="stylesheet" href="{% static 'game/css/battle.css' %}">
{% endblock %}

{% block content %}
<div class="battle-container">
    <!-- HTML構造のみ -->
</div>
{% endblock %}

{% block extra_js %}
<script src="{% static 'game/js/battle.js' %}"></script>
{% endblock %}
```

### 5.2 CSS / JS の配置ルール

**ディレクトリ構造：**
```
game/static/game/
├── css/
│   ├── battle.css      # 戦闘画面専用スタイル
│   ├── shop.css        # ショップ画面専用スタイル
│   └── common.css      # 全画面共通スタイル（必要に応じて）
└── js/
    ├── battle.js        # 戦闘画面専用ロジック
    ├── shop.js          # ショップ画面専用ロジック
    └── common.js        # 全画面共通ロジック（必要に応じて）
```

**命名規則：**
- ファイル名はスネークケース（`battle.css`）
- クラス名はケバブケース（`.battle-container`）
- JavaScript変数はキャメルケース（`battleAnimation`）

**CSS の分離例（battle.css の冒頭）：**
```css
/* game/static/game/css/battle.css */

/* base.htmlのデフォルトスタイルをリセット */
body {
    margin: 0;
    padding: 0;
    overflow: hidden;
}

.battle-container {
    position: fixed;
    top: 0px;
    left: 0;
    width: 100vw;
    height: 100vh;
    /* ... */
}
```

**JavaScript の分離例（battle.js の冒頭）：**
```javascript
// game/static/game/js/battle.js

// 戦闘アニメーションシステム
(function() {
    let isBattleAnimating = false;
    
    // 数値表示関数
    function showNumber(targetElement, value, className, delay = 0) {
        // ...
    }
    
    // 既存のJavaScriptコードをそのまま移行
    // ...
})();
```

---

## 6. 初学者向け理解ポイントまとめ

### ポイント1: なぜ views.py を分割するのか？

**理由：**
- **可読性の向上**：関連する関数が同じファイルに集約されるため、目的の処理を素早く見つけられる
- **保守性の向上**：変更時の影響範囲が明確になる
- **テストの容易さ**：機能単位でテストファイルも分割できる

**例：**
```python
# ❌ 悪い例：すべてが1つのファイル
views.py (2683行)
  - battle()
  - shop()
  - equipment_change()
  - quest()
  # どこに何があるか分からない

# ✅ 良い例：機能別に分割
views/battle.py (300行)
  - battle()
  - battle_start()
views/shop.py (150行)
  - shop()
  - buy_item()
# 目的の機能がすぐに見つかる
```

### ポイント2: なぜ CSS/JS を分離するのか？

**理由：**
- **再利用性**：同じスタイルやロジックを複数ページで使える
- **キャッシュ効率**：ブラウザがCSS/JSをキャッシュするため、2回目以降の読み込みが高速
- **デバッグの容易さ**：開発者ツールでファイル名が表示されるため、問題箇所を特定しやすい

**例：**
```html
<!-- ❌ 悪い例：HTML内に直書き -->
<style>/* 644行のCSS */</style>
<script>/* 1719行のJS */</script>

<!-- ✅ 良い例：外部ファイル参照 -->
<link rel="stylesheet" href="{% static 'game/css/battle.css' %}">
<script src="{% static 'game/js/battle.js' %}"></script>
```

### ポイント3: Django の標準構成とは？

**Django の推奨構成：**
```
app/
├── views.py          # または views/ ディレクトリ
├── models.py
├── urls.py
├── templates/
│   └── app/
└── static/
    └── app/
        ├── css/
        └── js/
```

**重要な原則：**
- **1つのファイルは1つの責務**：戦闘ロジックは `battle.py`、ショップロジックは `shop.py`
- **再利用可能な処理は utils に**：複数のviewで使う関数は `utils.py` に集約
- **静的ファイルは static に**：CSS/JS/画像は `static/` ディレクトリに配置

---

## 7. 今後拡張する場合の指針（ゲーム追加時）

### 新しい機能を追加する場合

**例：ギルドシステムを追加する場合**

1. **views の追加**
   ```
   game/views/
   └── guild.py          # 新規作成
       - guild_list()     # ギルド一覧
       - guild_join()    # ギルド加入
   ```

2. **urls.py の更新**
   ```python
   from .views.guild import guild_list, guild_join
   
   urlpatterns = [
       # ...
       path('guild/', guild_list, name='guild_list'),
       path('guild/join/<int:guild_id>/', guild_join, name='guild_join'),
   ]
   ```

3. **テンプレートの追加**
   ```
   game/templates/game/
   └── guild_list.html
   ```

4. **CSS/JS の追加（必要に応じて）**
   ```
   game/static/game/
   ├── css/
   │   └── guild.css     # 新規作成
   └── js/
       └── guild.js      # 新規作成
   ```

### 既存機能を拡張する場合

**例：戦闘システムに「連続攻撃」機能を追加する場合**

1. **既存ファイルを編集**
   - `views/battle.py` に `combo_attack()` 関数を追加
   - `templates/game/battle.html` にボタンを追加
   - `static/game/js/battle.js` に連続攻撃のアニメーションを追加

2. **影響範囲が明確**
   - 戦闘関連の変更は `battle.py` と `battle.js` のみ
   - ショップや装備には影響しない

### コードレビューの指針

**チェックポイント：**
1. ✅ 新しい機能は適切なファイルに配置されているか？
2. ✅ 既存の関数を再利用できるか？（DRY原則）
3. ✅ CSS/JS は外部ファイルに分離されているか？
4. ✅ 関数名は明確で、責務が1つに絞られているか？

---

## まとめ

このリファクタリングにより：
- **可読性**：目的のコードを素早く見つけられる
- **保守性**：変更時の影響範囲が明確
- **拡張性**：新機能追加が容易
- **教育性**：Django の標準的な構成を学習できる

**重要な原則：**
> 「誰が見ても理解でき、拡張しやすい構成」を最優先に設計する
