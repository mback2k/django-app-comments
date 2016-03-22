# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comments', '0002_auto_20160311_2158'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vote',
            name='mode',
            field=models.SmallIntegerField(verbose_name='Mode', choices=[(1, 'Up'), (-1, 'Down')]),
        ),
    ]
