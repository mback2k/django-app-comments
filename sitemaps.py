# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator
from django.contrib.sitemaps import Sitemap
from .models import Thread, Post

class CategorySitemap(Sitemap):
    changefreq = 'daily'
    protocol = 'https'
    priority = 0.6

    def __init__(self, category):
        self.category = category

    def items(self):
        threads = Thread.objects.filter(category=self.category).exclude(is_deleted=True)
        paginator = Paginator(threads, 10)
        return paginator.page_range

    def location(self, page):
        category_kwargs = {'category': self.category}
        category_link = reverse('comments:show_threads', kwargs=category_kwargs)
        category_link += '?page=%d' % page
        return category_link

class ThreadSitemap(Sitemap):
    changefreq = 'daily'
    protocol = 'https'
    priority = 0.5

    def items(self):
        return Thread.objects.exclude(is_deleted=True)

    def lastmod(self, thread):
        return thread.tstamp

class PostSitemap(Sitemap):
    changefreq = 'daily'
    protocol = 'https'
    priority = 0.4

    def items(self):
        return Post.objects.exclude(is_deleted=True).exclude(is_spam=True).filter(is_approved=True)

    def lastmod(self, post):
        return post.tstamp
