from django.db import migrations, models


class Migration(migrations.Migration):
    """Rename role/period and widen the ProjectStat text fields.

    RenameField, not remove-and-add: makemigrations proposed the latter, which
    would have dropped the values already stored (one project holds
    "FinTech" / "Android & Backend"). A rename carries the column across.

    The names are deliberately generic. The fields render as one badge,
    "primary . secondary", and hold a job title and dates on one project but a
    market segment and a tech stack on another.
    """

    dependencies = [
        ("portfolio", "0006_project_category_project_is_featured_project_period_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="project",
            old_name="role",
            new_name="meta_primary",
        ),
        migrations.RenameField(
            model_name="project",
            old_name="period",
            new_name="meta_secondary",
        ),
        migrations.AlterField(
            model_name="project",
            name="meta_primary",
            field=models.CharField(
                blank=True,
                help_text="First half of the badge on a featured card. e.g. FinTech, or Senior Software Engineer",
                max_length=100,
                verbose_name="Meta primary",
            ),
        ),
        migrations.AlterField(
            model_name="project",
            name="meta_secondary",
            field=models.CharField(
                blank=True,
                help_text="Second half, shown after a divider. e.g. Backend & Android, or 2019 — Present",
                max_length=100,
                verbose_name="Meta secondary",
            ),
        ),
        migrations.AlterField(
            model_name="projectstat",
            name="label",
            field=models.CharField(help_text="e.g. Users", max_length=100),
        ),
        migrations.AlterField(
            model_name="projectstat",
            name="value",
            field=models.CharField(help_text="e.g. 8M+", max_length=100),
        ),
    ]
