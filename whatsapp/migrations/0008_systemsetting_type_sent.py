# Generated by Django 3.1.3 on 2020-11-23 13:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('whatsapp', '0007_systemsetting_last_phone_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='systemsetting',
            name='type_sent',
            field=models.IntegerField(default=0),
        ),
    ]
