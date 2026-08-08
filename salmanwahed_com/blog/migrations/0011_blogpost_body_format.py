from django.db import migrations, models


class Migration(migrations.Migration):
    """Add BlogPost.body_format.

    Every post that exists today was written in CKEditor and holds raw HTML, so
    existing rows are backfilled with "HTML" -- rendering them as Markdown would
    mangle them. preserve_default=False keeps that one-off value out of the
    model, where the default stays "MD" so new posts are Markdown.
    """

    dependencies = [
        ("blog", "0010_alter_blogpost_hero_image_alter_blogpost_tag_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="blogpost",
            name="body_format",
            field=models.CharField(
                choices=[("HTML", "HTML (legacy)"), ("MD", "Markdown")],
                default="HTML",
                max_length=4,
                verbose_name="Body Format",
            ),
            preserve_default=False,
        ),
    ]
