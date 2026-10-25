from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("infrastructure", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                CREATE TABLE `infrastructure_userblogview` (
                    `id` char(32) NOT NULL PRIMARY KEY,
                    `viewed_at` datetime(6) NOT NULL,
                    `reading_duration_seconds` integer UNSIGNED NOT NULL,
                    `reached_end` bool NOT NULL,
                    `is_valid_view` bool NOT NULL,
                    `post_id` bigint NOT NULL,
                    `user_id` integer NOT NULL,
                    CONSTRAINT `infrastructure_userb_post_id_fk`
                        FOREIGN KEY (`post_id`)
                        REFERENCES `infrastructure_blogpost` (`id`),
                    CONSTRAINT `infrastructure_userblogview_user_id_fk`
                        FOREIGN KEY (`user_id`)
                        REFERENCES `auth_user` (`id`),
                    CONSTRAINT `infrastructure_userblogview_user_post_uniq`
                        UNIQUE (`user_id`, `post_id`)
                );
            """,
            reverse_sql="""
                DROP TABLE IF EXISTS `infrastructure_userblogview`;
            """,
        ),
    ]