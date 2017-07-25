# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-07-24 13:17
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('WV', '0005_auto_20170724_1034'),
    ]

    operations = [
        migrations.AddField(
            model_name='options',
            name='html',
            field=models.FileField(blank=True, default=None, null=True, upload_to=''),
        ),
        migrations.AlterField(
            model_name='options',
            name='text',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='WV.Data'),
        ),
    ]