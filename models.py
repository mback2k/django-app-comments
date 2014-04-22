# -*- coding: utf-8 -*-
from django.db import models
from django.core.cache import cache
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
import urllib, hashlib

class Author(User):
    class Meta:
        proxy = True

    @property
    def avatar(self):
        hash = hashlib.md5(self.email.lower()).hexdigest()
        gravatar_url = "//www.gravatar.com/avatar/%s.jpg?" % hash
        gravatar_url += urllib.urlencode({'d': 'retro', 's': 64})
        return gravatar_url

class Thread(models.Model):
    CATEGORIES = (
        ('discussion', _('discussion')),
        ('request',    _('request')),
        ('issue',      _('issue')),
    )

    category = models.CharField(_('category'), max_length=20, choices=CATEGORIES, default='discussion')

    crdate = models.DateTimeField(_('date created'), auto_now_add=True)
    tstamp = models.DateTimeField(_('date edited'), auto_now=True)

    is_closed = models.BooleanField(_('is closed'), blank=True, default=False)
    is_deleted = models.BooleanField(_('is deleted'), blank=True, default=False)

    class Meta:
        ordering = ('-crdate', '-tstamp')

    def __unicode__(self):
        return self.category

    @property
    def first_post(self):
        return self.posts.filter(parent=None).last()

class Post(models.Model):
    parent = models.ForeignKey('self', related_name='posts', blank=True, null=True)
    thread = models.ForeignKey(Thread, related_name='posts')
    author = models.ForeignKey(Author)

    content = models.TextField(_('content'))

    crdate = models.DateTimeField(_('date created'), auto_now_add=True)
    tstamp = models.DateTimeField(_('date edited'), auto_now=True)

    is_deleted = models.BooleanField(_('is deleted'), blank=True, default=False)
    is_approved = models.BooleanField(_('is approved'), blank=True, default=False)
    is_flagged = models.BooleanField(_('is flagged'), blank=True, default=False)
    is_spam = models.BooleanField(_('is spam'), blank=True, default=False)
    is_highlighted = models.BooleanField(_('is highlighted'), blank=True, default=False)

    class Meta:
        ordering = ('-crdate', '-tstamp')

    def __unicode__(self):
        return self.content
