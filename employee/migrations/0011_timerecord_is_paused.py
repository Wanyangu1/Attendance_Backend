# Generated by Django 5.2 on 2025-05-10 21:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employee', '0010_remove_timerecord_biweekly_total_hours_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='timerecord',
            name='is_paused',
            field=models.BooleanField(default=False),
        ),
    ]
