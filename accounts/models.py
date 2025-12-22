from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    """カスタムユーザーモデル（永続データ）"""
    
    # スコア関連
    best_score = models.IntegerField(default=0, verbose_name="最高スコア")
    total_score = models.IntegerField(default=0, verbose_name="累計スコア")
    
    # 初期ポイント（引き継ぎ用）
    initial_points = models.IntegerField(default=0, verbose_name="初期ポイント")
    
    # プレイ統計
    total_plays = models.IntegerField(default=0, verbose_name="総プレイ回数")
    total_clears = models.IntegerField(default=0, verbose_name="クリア回数")
    highest_stage = models.IntegerField(default=1, verbose_name="最高到達ステージ")
    
    # 開放済みジョブ（JSONフィールドで複数保存）
    unlocked_jobs = models.JSONField(default=list, verbose_name="開放済みジョブ")
    
    # クリア特典（引き継ぎ可能なステータスボーナス）
    bonus_hp = models.IntegerField(default=0, verbose_name="HP引き継ぎボーナス")
    bonus_atk = models.IntegerField(default=0, verbose_name="攻撃力引き継ぎボーナス")
    bonus_def = models.IntegerField(default=0, verbose_name="防御力引き継ぎボーナス")
    bonus_spd = models.IntegerField(default=0, verbose_name="素早さ引き継ぎボーナス")
    
    # その他
    first_clear_date = models.DateTimeField(null=True, blank=True, verbose_name="初回クリア日時")
    
    class Meta:
        verbose_name = "ユーザー"
        verbose_name_plural = "ユーザー"
    
    def update_score(self, new_score):
        """ゲーム側から渡されたスコアで記録を更新"""
        self.total_score += new_score
        self.total_plays += 1
        
        # 最高スコア更新時は初期ポイントも更新
        if new_score > self.best_score:
            self.best_score = new_score
            self.initial_points = new_score // 1000
        
        self.save()
    
    def unlock_job(self, job_name):
        """ジョブを開放"""
        if job_name not in self.unlocked_jobs:
            self.unlocked_jobs.append(job_name)
            self.save()
    
    def add_clear_bonus(self, hp=0, atk=0, defense=0, spd=0):
        """クリア時のボーナスを追加"""
        self.bonus_hp += hp
        self.bonus_atk += atk
        self.bonus_def += defense
        self.bonus_spd += spd
        self.total_clears += 1
        
        # 初回クリア日時を記録
        if not self.first_clear_date:
            from django.utils import timezone
            self.first_clear_date = timezone.now()
        
        self.save()

