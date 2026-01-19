import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from game.models import Player, Quest

def add_test_quests_to_all_players():
    """全プレイヤーにテストクエストを追加"""
    players = Player.objects.all()
    
    for player in players:
        # 既存のクエストを削除（テスト用）
        Quest.objects.filter(player=player).delete()
        
        # ライフクエスト：スライム倒し
        Quest.objects.create(
            player=player,
            quest_type='life',
            title='スライム倒し',
            description='スライムを3匹倒す',
            condition_type='defeat_enemy',
            condition_target='スライム',
            progress_current=0,
            progress_max=3,
            reward_exp=300,
            reward_gold=100,
            order=1
        )
        
        # アカウントクエスト：経済まわし
        Quest.objects.create(
            player=player,
            quest_type='account',
            title='経済まわし',
            description='ショップで500ゴールド使う',
            condition_type='spend_gold',
            condition_target='',
            progress_current=0,
            progress_max=500,
            reward_exp=200,
            reward_gold=500,
            order=1
        )
        
        # 残りの6つは空のクエスト（準備中）
        for i in range(2, 8):
            # ライフクエスト（準備中）
            Quest.objects.create(
                player=player,
                quest_type='life',
                title='準備中',
                description='このクエストは現在準備中です',
                condition_type='defeat_enemy',
                condition_target='',
                progress_current=0,
                progress_max=1,
                reward_exp=0,
                reward_gold=0,
                order=i
            )
        
        for i in range(2, 8):
            # アカウントクエスト（準備中）
            Quest.objects.create(
                player=player,
                quest_type='account',
                title='準備中',
                description='このクエストは現在準備中です',
                condition_type='defeat_enemy',
                condition_target='',
                progress_current=0,
                progress_max=1,
                reward_exp=0,
                reward_gold=0,
                order=i
            )
        
        print(f"プレイヤー {player.name} にクエストを追加しました")

if __name__ == '__main__':
    add_test_quests_to_all_players()
    print("完了！")
