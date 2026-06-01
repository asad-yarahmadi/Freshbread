from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('infrastructure', '0027_merge_20260219_2355'),
    ]

    operations = [
        migrations.AddField(
            model_name='review',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='infrastructure.review'),
        ),
        migrations.AddField(
            model_name='review',
            name='depth',
            field=models.PositiveSmallIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='blogreview',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='infrastructure.blogreview'),
        ),
        migrations.AddField(
            model_name='blogreview',
            name='depth',
            field=models.PositiveSmallIntegerField(default=1),
        ),
    ]

