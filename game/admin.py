from django.contrib import admin
from .models import Player, Enemy, Equipment, Item, Stage, QuestTemplate, PlayerQuest


@admin.register(QuestTemplate)
class QuestTemplateAdmin(admin.ModelAdmin):
    list_display = ['title', 'quest_type', 'job', 'condition_display', 'progress_max', 'reward_display', 'order', 'is_active']
    list_filter = ['quest_type', 'job', 'condition_type', 'is_active']
    search_fields = ['title', 'description']
    ordering = ['quest_type', 'order']
    list_editable = ['order', 'is_active']
    
    fieldsets = (
        ('基本情報', {
            'fields': ('title', 'description', 'quest_type', 'job', 'order', 'is_active')
        }),
        ('条件', {
            'fields': ('condition_type', 'condition_target', 'progress_max')
        }),
        ('報酬', {
            'fields': ('reward_exp', 'reward_gold')
        }),
    )
    
    def condition_display(self, obj):
        if obj.condition_target:
            return f"{obj.get_condition_type_display()}: {obj.condition_target} x{obj.progress_max}"
        return f"{obj.get_condition_type_display()} x{obj.progress_max}"
    condition_display.short_description = '条件'
    
    def reward_display(self, obj):
        return f"EXP +{obj.reward_exp}, Gold +{obj.reward_gold}"
    reward_display.short_description = '報酬'


@admin.register(PlayerQuest)
class PlayerQuestAdmin(admin.ModelAdmin):
    list_display = ['player', 'quest_title', 'progress_display', 'is_completed', 'is_claimed']
    list_filter = ['is_completed', 'is_claimed', 'quest_template__quest_type']
    search_fields = ['player__name', 'quest_template__title']
    ordering = ['player', 'quest_template__quest_type', 'quest_template__order']
    readonly_fields = ['player', 'quest_template']
    
    def quest_title(self, obj):
        return obj.quest_template.title
    quest_title.short_description = 'クエスト'
    
    def progress_display(self, obj):
        return f"{obj.progress_current}/{obj.quest_template.progress_max}"
    progress_display.short_description = '進捗'


admin.site.register(Player)
admin.site.register(Enemy)
admin.site.register(Equipment)
admin.site.register(Item)
admin.site.register(Stage)