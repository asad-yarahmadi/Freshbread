from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('infrastructure', '0022_site_announcement_and_release_note'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SuspiciousActivity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip', models.GenericIPAddressField()),
                ('failure_count', models.IntegerField(default=0)),
                ('is_tracking', models.BooleanField(default=False)),
                ('first_seen', models.DateTimeField(auto_now_add=True)),
                ('last_seen', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='SuspiciousEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('method', models.CharField(max_length=8)),
                ('path', models.CharField(max_length=512)),
                ('query_string', models.CharField(blank=True, max_length=512)),
                ('referer', models.CharField(blank=True, max_length=512)),
                ('user_agent', models.CharField(blank=True, max_length=512)),
                ('status_code', models.IntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('activity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to='infrastructure.suspiciousactivity')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='suspiciousactivity',
            index=models.Index(fields=['ip'], name='infrastruct_ip_0f0927_idx'),
        ),
        migrations.AddIndex(
            model_name='suspiciousactivity',
            index=models.Index(fields=['last_seen'], name='infrastruct_last_see_d134d5_idx'),
        ),
    ]
