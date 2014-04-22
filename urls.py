# -*- coding: utf-8 -*-
from django.conf.urls import patterns, include, url
from . import views

urlpatterns = patterns('',
    url(r'^comments/(?P<category>(discussion|request|issue))s/(?P<thread_id>\d+)/$', views.show_posts, name='show_posts'),
    url(r'^comments/(?P<category>(discussion|request|issue))s/$', views.show_threads, name='show_threads'),
)
