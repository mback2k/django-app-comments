# -*- coding: utf-8 -*-
from django.db import models
from django.db.models import signals
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone, html, safestring
from django.dispatch import receiver
from lxml.html import clean
import urllib, hashlib, datetime

class Author(User):
    class Meta:
        proxy = True

    @property
    def name(self):
        if self.first_name:
            return self.first_name
        if self.email:
            return self.email.split('@', 2)[0]
        return self.username

    @property
    def avatar(self):
        if self.email:
            hash = hashlib.md5(self.email.lower()).hexdigest()
        else:
            hash = hashlib.md5(self.name.encode('utf-8')).hexdigest()
        gravatar_url = "//www.gravatar.com/avatar/%s.jpg?" % hash
        if self.email:
            gravatar_url += urllib.urlencode({'d': 'retro', 's': 64})
        else:
            gravatar_url += urllib.urlencode({'d': 'retro', 's': 64, 'f': 'y'})
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
        return self.get_category_display()

    def get_absolute_url(self):
        thread_kwargs = {'category': self.category, 'thread_id': self.id}
        thread_link = reverse('comments:show_posts', kwargs=thread_kwargs)
        return thread_link

    @property
    def first_post(self):
        return self.posts.filter(parent=None).get()

    @property
    def first_active_post(self):
        return self.posts.filter(parent=None).exclude(is_deleted=True).exclude(is_spam=True).filter(is_approved=True).get()

class Post(models.Model):
    parent = models.ForeignKey('self', related_name='posts', blank=True, null=True)
    thread = models.ForeignKey(Thread, related_name='posts')
    author = models.ForeignKey(Author, related_name='posts')

    content = models.TextField(_('Comment'))
    content_cleaned = models.TextField(null=True, editable=False)

    crdate = models.DateTimeField(_('Date created'), auto_now_add=True)
    tstamp = models.DateTimeField(_('Date changed'), auto_now=True)
    edited = models.DateTimeField(_('Date edited'), blank=True, null=True)

    is_deleted = models.BooleanField(_('Is deleted'), blank=True, default=False)
    is_approved = models.BooleanField(_('Is approved'), blank=True, default=False)
    is_flagged = models.BooleanField(_('Is flagged'), blank=True, default=False)
    is_spam = models.BooleanField(_('Is spam'), blank=True, default=False)
    is_highlighted = models.BooleanField(_('Is highlighted'), blank=True, default=False)

    cleaner = clean.Cleaner(allow_tags=('br', 'p', 'a', 'b', 'i', 'strong', 'em'),
                            remove_unknown_tags=False, style=True, links=True,
                            page_structure=True, safe_attrs_only=True, add_nofollow=True)

    class Meta:
        ordering = ('crdate', 'tstamp')

    def __unicode__(self):
        return u'%s by %s' % (self.thread, self.author)

    def get_absolute_url(self):
        thread_kwargs = {'category': self.thread.category, 'thread_id': self.thread.id}
        thread_link = reverse('comments:show_posts', kwargs=thread_kwargs)
        thread_link_post = '%s#p%d' % (thread_link, self.id)
        return thread_link_post

    def get_cleaned_content(self):
        return self.cleaned_content
    get_cleaned_content.allow_tags = True
    get_cleaned_content.admin_order_field = content_cleaned
    get_cleaned_content.short_description = _('Comment')

    def clean_content(self, commit=True):
        cleaned_content = self.content
        cleaned_content = cleaned_content.replace('<p>', '')
        cleaned_content = cleaned_content.replace('</p>', '\n\n')
        cleaned_content = cleaned_content.replace('<br>', '\n')
        cleaned_content = cleaned_content.replace('<br />', '\n')
        cleaned_content = html.linebreaks(cleaned_content)
        cleaned_content = clean.autolink_html(cleaned_content)
        cleaned_content = self.cleaner.clean_html(cleaned_content)
        self.content_cleaned = cleaned_content
        if commit and self.id:
            self.save(update_fields=('content_cleaned',))
        return self.content_cleaned

    @property
    def cleaned_content(self):
        if not self.content_cleaned:
            content = _('This post is still being processed, please give it a few seconds and reload this page.')
            return safestring.mark_safe(u'<p>%s</p>' % content)
        return self.content_cleaned

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

class Media(models.Model):
    post = models.ForeignKey(Post, related_name='media')
    image = models.ImageField(_('Image'), upload_to='comments/posts/%Y/%m/%d',
                                          width_field='width', height_field='height',
                                          max_length=250)
    width = models.SmallIntegerField(_('Width'))
    height = models.SmallIntegerField(_('Height'))

class Attachment(models.Model):
    post = models.ForeignKey(Post, related_name='attachments')
    file = models.FileField(_('File'), upload_to='comments/posts/%Y/%m/%d',
                                       max_length=250)

@receiver(signals.pre_save, sender=Post)
def handle_post_pre_save_signal(sender, instance, update_fields, **kwargs):
    if not update_fields or 'content' in update_fields:
        instance.content_cleaned = None

@receiver(signals.post_save, sender=Post)
def handle_post_post_save_signal(sender, instance, update_fields, **kwargs):
    from .tasks import clean_post_content
    if not instance.content_cleaned:
        clean_post_content.apply_async(countdown=1, kwargs={'post_id': instance.id})
