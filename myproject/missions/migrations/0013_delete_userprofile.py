# Generated by Django 5.1.6 on 2025-06-01 05:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('missions', '0012_alter_mission_mission_type_userprofile'),
    ]

    operations = [
        migrations.DeleteModel(
            name='UserProfile',
        ),
    ]
