# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-08-22 14:25
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('capdb', '0004_auto_20170731_2035'),
    ]

    operations = [
        migrations.AddField(
            model_name='casemetadata',
            name='duplicative',
            field=models.BooleanField(default=False),
        ),
    ]