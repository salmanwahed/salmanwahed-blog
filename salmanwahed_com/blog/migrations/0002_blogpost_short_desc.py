# Generated by Django 4.0.1 on 2022-03-25 16:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='blogpost',
            name='short_desc',
            field=models.CharField(blank=True, max_length=280, null=True, verbose_name='Short Description'),
        ),
    ]
