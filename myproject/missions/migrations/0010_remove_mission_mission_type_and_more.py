# Generated by Django 5.1.5 on 2025-05-28 07:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('missions', '0009_mission_mission_type_mission_mission_units'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='mission',
            name='mission_type',
        ),
        migrations.RemoveField(
            model_name='mission',
            name='mission_units',
        ),
    ]
