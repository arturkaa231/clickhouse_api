# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-07-24 06:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('WV', '0002_remove_data_data_title'),
    ]

    operations = [
        migrations.AddField(
            model_name='data',
            name='Data_title',
            field=models.CharField(blank=True, default=None, max_length=100, null=True),
        ),
    ]