from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """CustomUser管理画面"""
    
    fieldsets = UserAdmin.fieldsets + (
        ('ゲームデータ', {
            'fields': (
                'best_score', 
                'total_score', 
                'initial_points',
                'total_plays',
                'total_clears',
                'highest_stage',
                'unlocked_jobs',
                'first_clear_date',
            )
        }),
        ('引き継ぎボーナス', {
            'fields': (
                'bonus_hp',
                'bonus_atk',
                'bonus_def',
                'bonus_spd',
            )
        }),
    )
    
    list_display = ['username', 'email', 'best_score', 'total_plays', 'total_clears', 'is_staff']
    list_filter = ['is_staff', 'is_superuser', 'total_clears']
    search_fields = ['username', 'email']
