from django.db import migrations, models, connection


class Migration(migrations.Migration):

    dependencies = [
        ('infrastructure', '0024_suspicious_block_fields'),
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
                    name='unread',
                    field=models.BooleanField(default=True),
                ),
                migrations.AddField(
                    model_name='suspiciousactivity',
                    name='suppress_logging',
                    field=models.BooleanField(default=False),
                ),
                migrations.AddField(
                    model_name='suspiciousactivity',
                    name='last_success_at',
                    field=models.DateTimeField(blank=True, null=True),
                ),
            ],
        ),
    ]


def _ensure_activity_columns():
    table = "infrastructure_suspiciousactivity"
    with connection.cursor() as cursor:
        existing = {col.name for col in connection.introspection.get_table_description(cursor, table)}
        if "unread" not in existing:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN unread TINYINT(1) NOT NULL DEFAULT 1")
        if "suppress_logging" not in existing:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN suppress_logging TINYINT(1) NOT NULL DEFAULT 0")
        if "last_success_at" not in existing:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN last_success_at DATETIME NULL")
