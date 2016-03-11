# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comments', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('file', models.FileField(upload_to=b'comments/posts/%Y/%m/%d', max_length=250, verbose_name='File')),
            ],
        ),
        migrations.AlterModelOptions(
            name='post',
            options={'ordering': ('crdate', 'tstamp')},
        ),
        migrations.AddField(
            model_name='attachment',
            name='post',
            field=models.ForeignKey(related_name='attachments', to='comments.Post'),
        ),
    ]
