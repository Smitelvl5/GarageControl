# Generated by Django 5.2.1 on 2025-05-14 08:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('garage', '0005_alter_sensordata_humidity_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='sensordata',
            name='abs_humidity',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='sensordata',
            name='dew_point',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='sensordata',
            name='steam_pressure',
            field=models.FloatField(null=True),
        ),
    ]
