# Generated by Django 4.0.1 on 2022-06-04 05:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portfolio', '0002_project_project_weight'),
    ]

    operations = [
        migrations.AddField(
            model_name='tag',
            name='external_url',
            field=models.URLField(blank=True, null=True),
        ),
    ]