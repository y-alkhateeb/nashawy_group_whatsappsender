# Generated by Django 3.1.3 on 2020-11-22 01:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('whatsapp', '0005_systemsetting'),
    ]

    operations = [
        migrations.AlterField(
            model_name='systemsetting',
            name='last_index_sent',
            field=models.IntegerField(default=0),
        ),
    ]