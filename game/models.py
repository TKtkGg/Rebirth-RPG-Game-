from django.db import models


class PlayerProfile(models.Model):
    name = models.CharField(max_length=20)
    total_score = models.IntegerField(default=0)
    bonus_points = models.IntegerField(default=0)
    unlocked_jobs = models.JSONField(default=list)


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
    
    def __str__(self):
        return f"{self.name} ({self.get_equipment_type_display()})"


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
    
    # 所持金
    gold = models.IntegerField(default=100)
    
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
    
    # ドロップ可能な装備
    drop_equipment = models.ManyToManyField(Equipment, blank=True, related_name='dropped_by')