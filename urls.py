# -*- coding: utf-8 -*-
from django.conf.urls import patterns, include, url
from . import views

urlpatterns = patterns('',
    url(r'^comments/(?P<category>(discussion|request|issue))s/(?P<thread_id>\d+)/reply/(?P<parent_id>\d+)/$', views.reply_post, name='reply_post'),
    url(r'^comments/(?P<category>(discussion|request|issue))s/(?P<thread_id>\d+)/$', views.show_posts, name='show_posts'),
    url(r'^comments/(?P<category>(discussion|request|issue))s/new/$', views.new_post, name='new_post'),
    url(r'^comments/(?P<category>(discussion|request|issue))s/$', views.show_threads, name='show_threads'),
)
