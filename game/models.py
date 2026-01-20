from django.db import models
from django.conf import settings


class Stage(models.Model):
    """ステージ情報を管理するモデル"""
    name = models.CharField(max_length=30)
    unlock_level = models.IntegerField(default=0)  # 開放レベル
    background_image = models.CharField(max_length=100)  # 背景画像ファイル名
    min_enemy_level = models.IntegerField(default=1)  # 出現する敵の最小レベル
    max_enemy_level = models.IntegerField(default=10)  # 出現する敵の最大レベル
    order = models.IntegerField(default=0)  # 表示順序
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return self.name


class Equipment(models.Model):
    EQUIPMENT_TYPES = [
        ('weapon', '武器'),
        ('armor', '防具'),
    ]
    
    name = models.CharField(max_length=30)
    equipment_type = models.CharField(max_length=10, choices=EQUIPMENT_TYPES)
    atk_bonus = models.IntegerField(default=0)
    def_bonus = models.IntegerField(default=0)
    hp_bonus = models.IntegerField(default=0)
    spd_bonus = models.IntegerField(default=0)
    price = models.IntegerField(default=0)  # ショップ価格
    drop_rate = models.FloatField(default=0.0)  # ドロップ率（0.0〜1.0）
    description = models.TextField(default="")
    is_purchased = models.BooleanField(default=False)  # 購入済みフラグ（ショップ用）
    appear_level = models.IntegerField(default=1)  # ショップに出現する最小プレイヤーレベル
    score = models.IntegerField(default=0)  # この装備が持つスコア
    
    def __str__(self):
        return f"{self.name} ({self.get_equipment_type_display()})"

class Item(models.Model):
    TARGET = [
        ('mp',"SP"),
        ('hp',"HP"),
    ]

    name = models.CharField(max_length=30)
    target = models.CharField(max_length=10, choices=TARGET)
    effect_amount = models.IntegerField(default=0)
    price = models.IntegerField(default=0)  # ショップ価格
    description = models.TextField(default="")
    is_purchased = models.BooleanField(default=False)  # 購入済みフラグ(ショップ用)
    max_stock = models.IntegerField(default=10)  # 最大在庫数
    appear_level = models.IntegerField(default=1)  # ショップに出現する最小プレイヤーレベル
    
    def __str__(self):
        return f"{self.name} ({self.get_target_display()})"

class PlayerInventory(models.Model):
    """プレイヤーのアイテム所持数を管理"""
    player = models.ForeignKey('Player', on_delete=models.CASCADE, related_name='inventory')
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ('player', 'item')
        verbose_name = 'プレイヤーアイテム'
        verbose_name_plural = 'プレイヤーアイテム'
    
    def __str__(self):
        return f"{self.player.name} - {self.item.name}: {self.quantity}個"

class Player(models.Model):
    # 認証システムとの連携（null=Trueでゲストプレイ対応）
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='player')
    
    # プレイヤー情報
    name = models.CharField(max_length=20, default="ゲスト")
    is_guest = models.BooleanField(default=False)  # ゲストプレイヤーかどうか
    
    # ゲームステータス
    level = models.IntegerField(default=1)
    exp = models.IntegerField(default=0)
    next_exp = models.IntegerField(default=300)
    max_hp = models.IntegerField(default=100)
    hp = models.IntegerField(default=100)
    atk = models.IntegerField(default=10)
    defense = models.IntegerField(default=5)
    spd = models.IntegerField(default=5)
    max_mp = models.IntegerField(default=50)
    mp = models.IntegerField(default=50)
    stat_points = models.IntegerField(default=0)
    job = models.CharField(max_length=20, default="戦士")
    item = models.CharField(max_length=30, default="なし")
    defeats = models.IntegerField(default=0)  # 敵を倒した回数（スコア計算用）
    strong_defeats = models.IntegerField(default=0)  # 強敵を倒した回数（スコア計算用）
    death_count = models.IntegerField(default=0)  # 敗北回数（復活回数の計算用）
    
    # 装備スロット
    weapon = models.ForeignKey(Equipment, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipped_as_weapon')
    armor = models.ForeignKey(Equipment, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipped_as_armor')
    
    # 所持している装備（インベントリ）
    owned_equipment = models.ManyToManyField(Equipment, blank=True, related_name='owned_by_players')
    
    # 所持金
    gold = models.IntegerField(default=100)
    
    # 戦闘用の総ステータス（装備ボーナス込み）
    total_max_hp_battle = models.IntegerField(default=100)
    total_hp_battle = models.IntegerField(default=100)
    total_atk_battle = models.IntegerField(default=10)
    total_def_battle = models.IntegerField(default=5)
    total_spd_battle = models.IntegerField(default=5)
    
    def __str__(self):
        return f"{self.name} (Lv.{self.level})"
    
    @property
    def total_atk(self):
        """装備のボーナスを含めた総ATK"""
        weapon_bonus = self.weapon.atk_bonus if self.weapon else 0
        armor_bonus = self.armor.atk_bonus if self.armor else 0
        return self.atk + weapon_bonus + armor_bonus
    
    @property
    def total_def(self):
        """装備のボーナスを含めた総DEF"""
        weapon_bonus = self.weapon.def_bonus if self.weapon else 0
        armor_bonus = self.armor.def_bonus if self.armor else 0
        return self.defense + weapon_bonus + armor_bonus
    
    @property
    def total_spd(self):
        """装備のボーナスを含めた総SPD"""
        weapon_bonus = self.weapon.spd_bonus if self.weapon else 0
        armor_bonus = self.armor.spd_bonus if self.armor else 0
        return self.spd + weapon_bonus + armor_bonus
    
    @property
    def total_max_hp(self):
        """装備のボーナスを含めた総最大HP"""
        weapon_bonus = self.weapon.hp_bonus if self.weapon else 0
        armor_bonus = self.armor.hp_bonus if self.armor else 0
        return self.max_hp + weapon_bonus + armor_bonus
    
    @property
    def total_hp(self):
        """装備のボーナスを含めた現在のHP"""
        weapon_bonus = self.weapon.hp_bonus if self.weapon else 0
        armor_bonus = self.armor.hp_bonus if self.armor else 0
        return min(self.hp + weapon_bonus + armor_bonus, self.total_max_hp)
    
    def update_battle_stats(self):
        """戦闘用ステータスを装備ボーナス込みで更新"""
        # 武器ボーナス
        weapon_atk = self.weapon.atk_bonus if self.weapon else 0
        weapon_def = self.weapon.def_bonus if self.weapon else 0
        weapon_hp = self.weapon.hp_bonus if self.weapon else 0
        weapon_spd = self.weapon.spd_bonus if self.weapon else 0
        
        # 防具ボーナス
        armor_atk = self.armor.atk_bonus if self.armor else 0
        armor_def = self.armor.def_bonus if self.armor else 0
        armor_hp = self.armor.hp_bonus if self.armor else 0
        armor_spd = self.armor.spd_bonus if self.armor else 0
        
        # 戦闘用ステータスを更新
        self.total_atk_battle = self.atk + weapon_atk + armor_atk
        self.total_def_battle = self.defense + weapon_def + armor_def
        self.total_spd_battle = self.spd + weapon_spd + armor_spd
        self.total_max_hp_battle = self.max_hp + weapon_hp + armor_hp
        
        # 現在のHPも調整（最大HPを超えないように）
        self.total_hp_battle = min(self.hp + weapon_hp + armor_hp, self.total_max_hp_battle)
    
    def change_weapon(self, new_weapon):
        """武器を変更する（戦闘外専用、HPを調整）        
        Args:new_weapon: 新しい装備するEquipmentオブジェクト（Noneで装備解除）
        Returns:bool: 変更成功ならTrue
        Note:
            - 現在の総HPから古い装備ボーナスを引き、新しい装備ボーナスを足す
            - HPが0以下になる場合は最低1HPを保証
            - 新しい最大HPを超える場合は最大HPに制限"""
            
        # 現在の総HPを取得
        current_total_hp = self.total_hp
        
        # 古い装備のボーナスを取得
        old_bonus = self.weapon.hp_bonus if self.weapon else 0
        
        # 新しい装備のボーナスを取得
        new_bonus = new_weapon.hp_bonus if new_weapon else 0
        
        # 装備を変更
        self.weapon = new_weapon
        
        # 素のHPを調整（現在の総HP - 古いボーナス + 新しいボーナス）
        adjusted_hp = current_total_hp - old_bonus
        
        # 最低1HP、最大は素の最大HPまで
        self.hp = max(1, min(adjusted_hp, self.max_hp))
        
        self.update_battle_stats()
        self.save()
        return True
    
    def change_armor(self, new_armor):
        """防具を変更する（戦闘外専用、HPを調整）  
        Args:new_armor: 新しい装備するEquipmentオブジェクト（Noneで装備解除）
        Returns:bool: 変更成功ならTrue
        Note:
            - 現在の総HPから古い装備ボーナスを引き、新しい装備ボーナスを足す
            - HPが0以下になる場合は最低1HPを保証
            - 新しい最大HPを超える場合は最大HPに制限"""
            
        # 現在の総HPを取得
        current_total_hp = self.total_hp
        
        # 古い装備のボーナスを取得
        old_bonus = self.armor.hp_bonus if self.armor else 0
        
        # 新しい装備のボーナスを取得
        new_bonus = new_armor.hp_bonus if new_armor else 0
        
        # 装備を変更
        self.armor = new_armor
        
        # 素のHPを調整（現在の総HP - 古いボーナス + 新しいボーナス）
        # 実質的に: 現在の総HP + (新しいボーナス - 古いボーナス)
        adjusted_hp = current_total_hp - old_bonus
        
        # 最低1HP、最大は素の最大HPまで
        self.hp = max(1, min(adjusted_hp, self.max_hp))
        
        self.update_battle_stats()
        self.save()
        return True
    
    def unequip_weapon(self):
        """武器を外す"""
        self.weapon = None
        self.save()
        return True
    
    def unequip_armor(self):
        """防具を外す（HPを調整）"""
        return self.change_armor(None)
    
    def sync_hp_from_battle(self):
        """戦闘用HPを素のHPに反映（戦闘終了時に使用）"""
        weapon_bonus = self.weapon.hp_bonus if self.weapon else 0
        armor_bonus = self.armor.hp_bonus if self.armor else 0
        self.hp = max(0, self.total_hp_battle - weapon_bonus - armor_bonus)
        self.save()


class Enemy(models.Model):
    name = models.CharField(max_length=30)
    image_url = models.CharField(max_length=200, default="game/img/スライム.png")  # 敵の画像URL
    
    # 戦闘中の現在のステータス
    max_hp = models.IntegerField(default=50)
    hp = models.IntegerField(default=50)
    atk = models.IntegerField(default=8)
    defense = models.IntegerField(default=3)
    spd = models.IntegerField(default=5)
    exp = models.IntegerField(default=120)
    drop_gold = models.IntegerField(default=20)  # ドロップされるゴールド量（レベル変動）
    
    # 戦闘管理
    is_defeated = models.BooleanField(default=False)
    level = models.IntegerField(default=1)
    appearance_rate = models.FloatField(default=1.0)  # 出現率（1.0で等倍）
    
    # このモンスターが出現する最小プレイヤーレベル
    appear_level = models.IntegerField(default=1)
    # レベル1時点での基本ステータス（このモンスターの強さの基準）
    base_max_hp = models.IntegerField(default=50)
    base_atk = models.IntegerField(default=8)
    base_def = models.IntegerField(default=3)
    base_spd = models.IntegerField(default=5)
    base_exp = models.IntegerField(default=120)
    drop_gold_base = models.IntegerField(default=20)  # レベル1時点でのドロップゴールド量

    # ドロップ可能な装備
    drop_equipment = models.ManyToManyField(Equipment, blank=True, related_name='dropped_by')
    
    # 強敵フラグ
    is_strong = models.BooleanField(default=False)
    
    # 出現するステージ
    stages = models.ManyToManyField(Stage, blank=True, related_name='enemies')
    
    def __str__(self):
        return f"{self.name} (出現条件: Lv.{self.appear_level}以上) (ステージ: {', '.join([stage.name for stage in self.stages.all()])})"


class QuestTemplate(models.Model):
    """クエストテンプレート - 全プレイヤー共通のクエスト定義"""
    QUEST_TYPES = [
        ('life', 'ライフ'),
        ('account', 'アカウント'),
    ]
    
    QUEST_CONDITIONS = [
        ('defeat_enemy', '敵を倒す'),
        ('spend_gold', 'ゴールドを使う'),
    ]
    
    JOB_CHOICES = [
        ('all', '全職業'),
        ('戦士', '戦士'),
        ('魔法使い', '魔法使い'),
        ('盗賊', '盗賊'),
    ]
    
    quest_type = models.CharField(max_length=10, choices=QUEST_TYPES)  # ライフ or アカウント
    job = models.CharField(max_length=20, choices=JOB_CHOICES, default='all')  # 対象職業
    title = models.CharField(max_length=50)  # クエスト名
    description = models.TextField()  # クエスト内容
    condition_type = models.CharField(max_length=20, choices=QUEST_CONDITIONS)  # 条件タイプ
    condition_target = models.CharField(max_length=50, blank=True)  # 条件の対象（敵の名前など）
    progress_max = models.IntegerField(default=1)  # 目標値
    reward_exp = models.IntegerField(default=0)  # 報酬経験値
    reward_gold = models.IntegerField(default=0)  # 報酬ゴールド
    order = models.IntegerField(default=0)  # 表示順序
    is_active = models.BooleanField(default=True)  # 有効フラグ
    
    # 派生クエストシステム
    derived_quest = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='previous_quest')  # 次の派生クエスト
    derivation_level = models.IntegerField(default=0)  # 派生段階（0=初期、1=1段階目、2=2段階目...）
    
    class Meta:
        ordering = ['quest_type', 'order']
        verbose_name = 'クエストテンプレート'
        verbose_name_plural = 'クエストテンプレート'
    
    def __str__(self):
        job_display = f"[{self.get_job_display()}]" if self.job != 'all' else ""
        return f"{job_display}{self.title} ({self.get_quest_type_display()})"


class PlayerQuest(models.Model):
    """プレイヤーのクエスト進捗"""
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='player_quests')
    quest_template = models.ForeignKey(QuestTemplate, on_delete=models.CASCADE, related_name='player_progresses')
    progress_current = models.IntegerField(default=0)  # 現在の進捗
    is_completed = models.BooleanField(default=False)  # 達成フラグ
    is_claimed = models.BooleanField(default=False)  # 報酬受け取りフラグ
    
    class Meta:
        unique_together = ('player', 'quest_template')
        verbose_name = 'プレイヤークエスト'
        verbose_name_plural = 'プレイヤークエスト'
    
    def __str__(self):
        return f"{self.player.name} - {self.quest_template.title}"
    
    def check_completion(self):
        """進捗を確認して達成判定"""
        if not self.is_completed and self.progress_current >= self.quest_template.progress_max:
            self.is_completed = True
            self.save()
        return self.is_completed
    
    def update_progress(self, amount=1):
        """進捗を更新"""
        if not self.is_completed:
            self.progress_current = min(self.progress_current + amount, self.quest_template.progress_max)
            self.save()
            self.check_completion()
