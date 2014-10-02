# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Media',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('image', models.ImageField(height_field=b'height', upload_to=b'comments/posts/%Y/%m/%d', width_field=b'width', max_length=250, verbose_name='Image')),
                ('width', models.SmallIntegerField(verbose_name='Width')),
                ('height', models.SmallIntegerField(verbose_name='Height')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('content', models.TextField(verbose_name='Comment')),
                ('content_cleaned', models.TextField(null=True, editable=False)),
                ('crdate', models.DateTimeField(auto_now_add=True, verbose_name='Date created')),
                ('tstamp', models.DateTimeField(auto_now=True, verbose_name='Date changed')),
                ('edited', models.DateTimeField(null=True, verbose_name='Date edited', blank=True)),
                ('is_deleted', models.BooleanField(default=False, verbose_name='Is deleted')),
                ('is_approved', models.BooleanField(default=False, verbose_name='Is approved')),
                ('is_flagged', models.BooleanField(default=False, verbose_name='Is flagged')),
                ('is_spam', models.BooleanField(default=False, verbose_name='Is spam')),
                ('is_highlighted', models.BooleanField(default=False, verbose_name='Is highlighted')),
                ('parent', models.ForeignKey(related_name=b'posts', blank=True, to='comments.Post', null=True)),
            ],
            options={
                'ordering': ('-crdate', '-tstamp'),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Thread',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('category', models.CharField(default=b'discussion', max_length=20, verbose_name='Category', choices=[(b'discussion', 'Discussion'), (b'request', 'Request'), (b'issue', 'Issue')])),
                ('crdate', models.DateTimeField(auto_now_add=True, verbose_name='Date created')),
                ('tstamp', models.DateTimeField(auto_now=True, verbose_name='Date changed')),
                ('is_closed', models.BooleanField(default=False, verbose_name='Is closed')),
                ('is_deleted', models.BooleanField(default=False, verbose_name='Is deleted')),
            ],
            options={
                'ordering': ('-crdate', '-tstamp'),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Vote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('mode', models.SmallIntegerField(verbose_name='Mode')),
                ('post', models.ForeignKey(related_name=b'votes', to='comments.Post')),
                ('user', models.ForeignKey(related_name=b'votes', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='vote',
            unique_together=set([('post', 'user')]),
        ),
        migrations.AddField(
            model_name='post',
            name='thread',
            field=models.ForeignKey(related_name=b'posts', to='comments.Thread'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='media',
            name='post',
            field=models.ForeignKey(related_name=b'media', to='comments.Post'),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='Author',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('auth.user',),
        ),
        migrations.AddField(
            model_name='post',
            name='author',
            field=models.ForeignKey(related_name=b'posts', to='comments.Author'),
            preserve_default=True,
        ),
    ]
