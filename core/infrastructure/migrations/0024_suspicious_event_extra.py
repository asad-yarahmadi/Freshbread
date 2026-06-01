from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('infrastructure', '0023_suspicious_activity'),
    ]

    operations = [
        migrations.AddField(
            model_name='suspiciousevent',
            name='action',
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name='suspiciousevent',
            name='meta',
            field=models.TextField(blank=True),
        ),
    ]
