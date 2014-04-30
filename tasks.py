# -*- coding: utf-8 -*-
from celery.task import task
from django.db.models import Q
from django.contrib.auth.models import User, Permission
from django.contrib.sites.models import Site
from .models import User, Post

@task(ignore_result=True)
def notification_post_moderation_pending(post_id, mode='approval'):
    post = Post.objects.get(id=post_id)

    perm = Permission.objects.get_by_natural_key(codename='change_post', app_label='comments', model='post')
    users = User.objects.filter(Q(is_superuser=True) | Q(groups__permissions=perm) | Q(user_permissions=perm)).distinct()

    for user in users:
        notification_post_moderation_pending_user.delay(post.id, user.id, mode)

@task(ignore_result=True)
def notification_post_moderation_pending_user(post_id, user_id, mode='approval'):
    post = Post.objects.get(id=post_id)
    user = User.objects.get(id=user_id)

    current_site = Site.objects.get_current()
    absolute_url = 'https://%s%s' % (current_site.domain, post.get_absolute_url())

    if mode == 'approval':
        user.email_user('%s - Post approval pending' % current_site.name,
                        'A new comment on %s has just been posted, you can approve it at the following location:\n\n' \
                        '%s' % (current_site.name, absolute_url))

    elif mode == 'flagged':
        user.email_user('%s - Post has been flagged' % current_site.name,
                        'A comment on %s has just been flagged, you can review it at the following location:\n\n' \
                        '%s' % (current_site.name, absolute_url))

    elif mode == 'highlighted':
        user.email_user('%s - Post has been highlighted' % current_site.name,
                        'A comment on %s has just been highlighted, you can review it at the following location:\n\n' \
                        '%s' % (current_site.name, absolute_url))

@task(ignore_result=True)
def notification_post_approved(post_id):
    post = Post.objects.get(id=post_id, is_approved=True)
    user = User.objects.get(id=post.author.id)

    current_site = Site.objects.get_current()
    absolute_url = 'https://%s%s' % (current_site.domain, post.get_absolute_url())

    user.email_user('%s - Post approved' % current_site.name,
                    'Your comment on %s has just been approved, you can view it at the following location:\n\n' \
                    '%s' % (current_site.name, absolute_url))

@task(ignore_result=True)
def notification_post_new_reply(post_id):
    post = Post.objects.get(id=post_id, is_approved=True)

    author_ids = set()
    parent_post = post.parent
    while parent_post:
        author_ids.add(parent_post.author.id)
        parent_post = parent_post.parent

    for author_id in author_ids:
        notification_post_new_reply_user.delay(post.id, author_id)

@task(ignore_result=True)
def notification_post_new_reply_user(post_id, user_id):
    post = Post.objects.get(id=post_id, is_approved=True)
    user = User.objects.get(id=user_id)

    current_site = Site.objects.get_current()
    absolute_url = 'https://%s%s' % (current_site.domain, post.get_absolute_url())

    user.email_user('%s - New reply to your post' % current_site.name,
                    'A new reply to your comment on %s has just been posted, you can view it at the following location:\n\n' \
                    '%s' % (current_site.name, absolute_url))
