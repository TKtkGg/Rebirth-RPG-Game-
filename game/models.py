from django.db import models


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


class PlayerProfile(models.Model):
    name = models.CharField(max_length=20)
    total_score = models.IntegerField(default=0)
    bonus_points = models.IntegerField(default=0)
    unlocked_jobs = models.JSONField(default=list)
    
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
    
    def __str__(self):
        return f"{self.name} ({self.get_equipment_type_display()})"

class Item(models.Model):
    TARGET = [
        ('mp',"MP"),
        ('hp',"HP"),
    ]

    name = models.CharField(max_length=30)
    target = models.CharField(max_length=10, choices=TARGET)
    effect_amount = models.IntegerField(default=0)
    price = models.IntegerField(default=0)  # ショップ価格
    description = models.TextField(default="")
    is_purchased = models.BooleanField(default=False)  # 購入済みフラグ(ショップ用)
    max_stock = models.IntegerField(default=10)  # 最大在庫数
    
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
        return f"{self.player.profile.name} - {self.item.name}: {self.quantity}個"

class Player(models.Model):
    profile = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE)
    level = models.IntegerField(default=1)
    exp = models.IntegerField(default=0)
    next_exp = models.IntegerField(default=500)
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
    defeats = models.IntegerField(default=0)
    
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
        return f"{self.profile.name} (Lv.{self.level})"
    
    @property
    def name(self):
        return self.profile.name
    
    @property
    def total_atk(self):
        """武器のボーナスを含めた総ATK"""
        bonus = self.weapon.atk_bonus if self.weapon else 0
        return self.atk + bonus
    
    @property
    def total_def(self):
        """防具のボーナスを含めた総DEF"""
        bonus = self.armor.def_bonus if self.armor else 0
        return self.defense + bonus
    
    @property
    def total_spd(self):
        """装備のボーナスを含めた総SPD"""
        weapon_bonus = self.weapon.spd_bonus if self.weapon else 0
        armor_bonus = self.armor.spd_bonus if self.armor else 0
        return self.spd + weapon_bonus + armor_bonus
    
    @property
    def total_max_hp(self):
        """防具のボーナスを含めた総最大HP"""
        bonus = self.armor.hp_bonus if self.armor else 0
        return self.max_hp + bonus
    
    @property
    def total_hp(self):
        """防具のボーナスを含めた現在のHP"""
        bonus = self.armor.hp_bonus if self.armor else 0
        return min(self.hp + bonus, self.total_max_hp)
    
    def update_battle_stats(self):
        """戦闘用ステータスを装備ボーナス込みで更新"""
        # 武器ボーナス
        weapon_atk = self.weapon.atk_bonus if self.weapon else 0
        weapon_spd = self.weapon.spd_bonus if self.weapon else 0
        
        # 防具ボーナス
        armor_def = self.armor.def_bonus if self.armor else 0
        armor_hp = self.armor.hp_bonus if self.armor else 0
        armor_spd = self.armor.spd_bonus if self.armor else 0
        
        # 戦闘用ステータスを更新
        self.total_atk_battle = self.atk + weapon_atk
        self.total_def_battle = self.defense + armor_def
        self.total_spd_battle = self.spd + weapon_spd + armor_spd
        self.total_max_hp_battle = self.max_hp + armor_hp
        
        # 現在のHPも調整（最大HPを超えないように）
        self.total_hp_battle = min(self.hp + armor_hp, self.total_max_hp_battle)
    
    def change_weapon(self, new_weapon):
        """武器を変更する（戦闘外専用）        
        Args:new_weapon: 新しい装備するEquipmentオブジェクト
        Returns:bool: 変更成功ならTrue"""

        self.weapon = new_weapon
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
        armor_bonus = self.armor.hp_bonus if self.armor else 0
        self.hp = max(0, self.total_hp_battle - armor_bonus)
        self.save()


class Enemy(models.Model):
    name = models.CharField(max_length=30)
    max_hp = models.IntegerField(default=50)
    hp = models.IntegerField(default=50)
    atk = models.IntegerField(default=8)
    defense = models.IntegerField(default=3)
    spd = models.IntegerField(default=5)
    exp = models.IntegerField(default=120)
    is_defeated = models.BooleanField(default=False)
    level = models.IntegerField(default=1)
    max_hp_default = models.IntegerField(default=50)
    atk_default = models.IntegerField(default=8)
    defense_default = models.IntegerField(default=3)
    spd_default = models.IntegerField(default=5)
    exp_default = models.IntegerField(default=120)
    level_default = models.IntegerField(default=1)
    
    # 強敵フラグ
    is_strong = models.BooleanField(default=False)
    
    # ドロップ可能な装備
    drop_equipment = models.ManyToManyField(Equipment, blank=True, related_name='dropped_by')
    drop_gold = models.IntegerField(default=20)  # ドロップされるゴールド量（レベル変動）
    drop_gold_default = models.IntegerField(default=20)  # デフォルトのドロップゴールド量
    
    # 出現するステージ
    stages = models.ManyToManyField(Stage, blank=True, related_name='enemies')
    
    def __str__(self):
        return f"{self.name} (Lv.{self.level}) (ステージ: {', '.join([stage.name for stage in self.stages.all()])})"

    