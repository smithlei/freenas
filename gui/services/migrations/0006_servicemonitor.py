# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-05-26 12:58
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0005_add_afp_srv_chmod_request'),
    ]

    operations = [
        migrations.CreateModel(
            name='ServiceMonitor',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sm_name', models.CharField(max_length=120, unique=True, verbose_name='Service Name')),
                ('sm_host', models.CharField(max_length=120, verbose_name='Host Name')),
                ('sm_port', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(65535)], verbose_name='Port')),
                ('sm_frequency', models.PositiveIntegerField(verbose_name='Frequency')),
                ('sm_retry', models.PositiveIntegerField(verbose_name='Retry')),
                ('sm_enable', models.BooleanField(default=False, verbose_name='Enable')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
