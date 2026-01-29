from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_score_points_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='best_score_job',
            field=models.CharField(default='', max_length=20, verbose_name='最高スコア時の職業'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='best_strong_defeats',
            field=models.IntegerField(default=0, verbose_name='最高強敵討伐数'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='best_strong_defeats_job',
            field=models.CharField(default='', max_length=20, verbose_name='強敵討伐数記録時の職業'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='best_victories',
            field=models.IntegerField(default=0, verbose_name='最高勝利回数'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='best_victories_job',
            field=models.CharField(default='', max_length=20, verbose_name='勝利回数記録時の職業'),
        ),
    ]
