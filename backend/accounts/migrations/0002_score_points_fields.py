from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='score_points',
            field=models.IntegerField(default=0, verbose_name='スコアポイント'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='score_bonus_all',
            field=models.JSONField(default=dict, verbose_name='スコアボーナス(全体)'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='score_bonus_jobs',
            field=models.JSONField(default=dict, verbose_name='スコアボーナス(職業別)'),
        ),
    ]
