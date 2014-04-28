# -*- coding: utf-8 -*-
from django.db import models
from django.core.cache import cache
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
import urllib, hashlib, datetime

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
        ('discussion', _('Discussion')),
        ('request',    _('Request')),
        ('issue',      _('Issue')),
    )

    category = models.CharField(_('Category'), max_length=20, choices=CATEGORIES, default='discussion')

    crdate = models.DateTimeField(_('Date created'), auto_now_add=True)
    tstamp = models.DateTimeField(_('Date changed'), auto_now=True)

    is_closed = models.BooleanField(_('Is closed'), blank=True, default=False)
    is_deleted = models.BooleanField(_('Is deleted'), blank=True, default=False)

    class Meta:
        ordering = ('-crdate', '-tstamp')

    def __unicode__(self):
        return self.category

    @property
    def first_post(self):
        return self.posts.filter(parent=None).last()

    @property
    def first_active_post(self):
        return self.posts.filter(parent=None).exclude(is_deleted=True).exclude(is_spam=True).filter(is_approved=True).last()

class Post(models.Model):
    parent = models.ForeignKey('self', related_name='posts', blank=True, null=True)
    thread = models.ForeignKey(Thread, related_name='posts')
    author = models.ForeignKey(Author, related_name='posts')

    content = models.TextField(_('Comment'))

    crdate = models.DateTimeField(_('Date created'), auto_now_add=True)
    tstamp = models.DateTimeField(_('Date changed'), auto_now=True)
    edited = models.DateTimeField(_('Date edited'), blank=True, null=True)

    is_deleted = models.BooleanField(_('Is deleted'), blank=True, default=False)
    is_approved = models.BooleanField(_('Is approved'), blank=True, default=False)
    is_flagged = models.BooleanField(_('Is flagged'), blank=True, default=False)
    is_spam = models.BooleanField(_('Is spam'), blank=True, default=False)
    is_highlighted = models.BooleanField(_('Is highlighted'), blank=True, default=False)

    class Meta:
        ordering = ('-crdate', '-tstamp')

    def __unicode__(self):
        return self.content

    @property
    def active_posts(self):
        return self.posts.exclude(is_deleted=True).exclude(is_spam=True).filter(is_approved=True)

    @property
    def is_editable(self):
        if self.thread.is_closed:
            return False
        if self.crdate < timezone.now() - datetime.timedelta(days=1):
            return False
        if self.posts.exists():
            return False
        return True

    @property
    def vote_sum(self):
        return self.votes.aggregate(vote_sum=models.Sum('mode'))['vote_sum']

class Vote(models.Model):
    CATEGORIES = (
        ( 1, _('Up')),
        (-1, _('Down')),
    )

    post = models.ForeignKey(Post, related_name='votes')
    user = models.ForeignKey(User, related_name='votes')
    mode = models.SmallIntegerField(_('Mode'))

    class Meta:
        unique_together = ('post', 'user')
