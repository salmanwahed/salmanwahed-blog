from django.db import migrations, models


class Migration(migrations.Migration):
    """Restore the model default after 0011's one-off HTML backfill.

    Django keeps field defaults in Python, not in the database schema, so this
    only affects posts created from here on -- the rows 0011 tagged as HTML are
    left exactly as they are.
    """

    dependencies = [
        ("blog", "0011_blogpost_body_format"),
    ]

    operations = [
        migrations.AlterField(
            model_name="blogpost",
            name="body_format",
            field=models.CharField(
                choices=[("HTML", "HTML (legacy)"), ("MD", "Markdown")],
                default="MD",
                max_length=4,
                verbose_name="Body Format",
            ),
        ),
    ]
