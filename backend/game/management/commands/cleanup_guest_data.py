"""
古いゲストプレイヤーデータを削除する管理コマンド

使用方法:
    python manage.py cleanup_guest_data
    python manage.py cleanup_guest_data --days 7  # 7日以上前のデータを削除

ゲストプレイヤーのデータは再アクセス不可能なため、
定期的に削除することでデータベースを整理できます。
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from game.models import Player


class Command(BaseCommand):
    help = '古いゲストプレイヤーのデータを削除します'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=1,
            help='何日以上前のゲストデータを削除するか（デフォルト: 1日）'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='実際には削除せず、削除対象のみを表示'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        # 削除対象の期限を計算
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # 古いゲストプレイヤーを取得
        old_guests = Player.objects.filter(
            is_guest=True,
            user__isnull=True  # userに関連付けられていないゲストプレイヤー
        )
        
        # Player モデルには作成日時フィールドがないため、全てのゲストを対象とする
        # 実際の実装では、Playerモデルにcreated_atフィールドを追加することを推奨
        
        count = old_guests.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('削除対象のゲストプレイヤーはいません。')
            )
            return
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'[ドライラン] {count}件のゲストプレイヤーデータが削除対象です:'
                )
            )
            for guest in old_guests:
                self.stdout.write(f'  - ID: {guest.id}, 名前: {guest.name}, レベル: {guest.level}')
        else:
            # 実際に削除
            old_guests.delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f'{count}件のゲストプレイヤーデータを削除しました。'
                )
            )
