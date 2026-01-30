from django.contrib.admin.models import LogEntry
from django.db import connection
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from .models import CustomUser


@receiver(pre_delete, sender=CustomUser)
def cleanup_user_relations(sender, instance, **kwargs):
    """
    ユーザー削除時にFK制約で失敗しないよう、関連レコードを事前削除する。

    - django_admin_log: user_id が NOT NULL のため事前削除
    - game_scoreprofile: 過去の残存テーブルを事前削除
    """
    LogEntry.objects.filter(user_id=instance.id).delete()

    # game_scoreprofile は既にモデルが無い可能性があるため、SQLで安全に削除
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM game_scoreprofile WHERE user_id = %s",
                [instance.id],
            )
    except Exception:
        # テーブルが存在しない場合などは無視
        pass
