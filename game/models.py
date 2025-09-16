from django.db import models


class PlayerProfile(models.Model):
    name = models.CharField(max_length=20)
    total_score = models.IntegerField(default=0)
    bonus_points = models.IntegerField(default=0)
    unlocked_jobs = models.JSONField(default=list)
    unlocked_jobs = models.JSONField(default=list)


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