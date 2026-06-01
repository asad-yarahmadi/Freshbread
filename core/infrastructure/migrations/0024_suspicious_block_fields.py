from django.db import migrations, models
from django.db import connection


class Migration(migrations.Migration):

    dependencies = [
        ('infrastructure', '0023_suspicious_activity'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(
                    code=lambda apps, schema_editor: _ensure_activity_columns(),
                    reverse_code=lambda apps, schema_editor: None,
                )
            ],
            state_operations=[
                migrations.AddField(
                    model_name='suspiciousactivity',
                    name='is_blocked',
                    field=models.BooleanField(default=False),
                ),
                migrations.AddField(
                    model_name='suspiciousactivity',
                    name='blocked_until',
                    field=models.DateTimeField(blank=True, null=True),
                ),
            ],
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(
                    code=lambda apps, schema_editor: _ensure_event_columns(),
                    reverse_code=lambda apps, schema_editor: None,
                )
            ],
            state_operations=[
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
            ],
        ),
    ]


def _ensure_event_columns():
    table = "infrastructure_suspiciousevent"
    with connection.cursor() as cursor:
        existing = {col.name for col in connection.introspection.get_table_description(cursor, table)}
        if "action" not in existing:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN action VARCHAR(64) NULL")
        if "meta" not in existing:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN meta LONGTEXT NULL")


def _ensure_activity_columns():
    table = "infrastructure_suspiciousactivity"
    with connection.cursor() as cursor:
        existing = {col.name for col in connection.introspection.get_table_description(cursor, table)}
        if "is_blocked" not in existing:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN is_blocked TINYINT(1) NOT NULL DEFAULT 0")
        if "blocked_until" not in existing:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN blocked_until DATETIME NULL")
