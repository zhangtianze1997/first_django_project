# Generated by Django 2.0.1 on 2018-03-12 15:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0016_actionlog'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actionlog',
            name='time',
            field=models.IntegerField(),
        ),
    ]