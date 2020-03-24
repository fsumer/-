# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2020-03-19 02:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app01', '0004_deploytask'),
    ]

    operations = [
        migrations.CreateModel(
            name='HookTemplate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=32, verbose_name='标题')),
                ('content', models.TextField(verbose_name='脚本内容')),
                ('hook_type', models.IntegerField(choices=[(2, '下载前'), (4, '下载后'), (6, '发布前'), (8, '发布后')], verbose_name='钩子类型')),
            ],
        ),
    ]