# Generated by Django 4.0.1 on 2022-06-04 04:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portfolio', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='project_weight',
            field=models.SmallIntegerField(default=0),
        ),
    ]