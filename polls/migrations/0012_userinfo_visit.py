# Generated by Django 2.0.1 on 2018-03-05 11:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0011_auto_20180304_2014'),
    ]

    operations = [
        migrations.AddField(
            model_name='userinfo',
            name='visit',
            field=models.IntegerField(default=0),
        ),
    ]
