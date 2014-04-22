# -*- coding: utf-8 -*-
from django.conf.urls import patterns, include, url
from . import views

urlpatterns = patterns('',
    url(r'^threads/(?P<post_type>\w+)s/$', views.show_threads, name='show_threads'),
)
