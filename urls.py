# -*- coding: utf-8 -*-
from django.conf.urls import include, url
from . import views

urlpatterns = (
    url(r'^comments/(?P<category>(discussion|request|issue))s/(?P<thread_id>\d+)/moderate/(?P<post_id>\d+)/approve/$', views.approve_post, name='approve_post'),
    url(r'^comments/(?P<category>(discussion|request|issue))s/(?P<thread_id>\d+)/moderate/(?P<post_id>\d+)/spam/$', views.spam_post, name='spam_post'),
    url(r'^comments/(?P<category>(discussion|request|issue))s/(?P<thread_id>\d+)/moderate/(?P<post_id>\d+)/delete/$', views.delete_post, name='delete_post'),
    url(r'^comments/(?P<category>(discussion|request|issue))s/(?P<thread_id>\d+)/vote/(?P<post_id>\d+)/(?P<mode>(up|down))/$', views.vote_post, name='vote_post'),
    url(r'^comments/(?P<category>(discussion|request|issue))s/(?P<thread_id>\d+)/edit/(?P<post_id>\d+)/$', views.edit_post, name='edit_post'),
    url(r'^comments/(?P<category>(discussion|request|issue))s/(?P<thread_id>\d+)/reply/(?P<parent_id>\d+)/$', views.reply_post, name='reply_post'),
    url(r'^comments/(?P<category>(discussion|request|issue))s/(?P<thread_id>\d+)/(?P<mode>(open|close))/$', views.manage_thread, name='manage_thread'),
    url(r'^comments/(?P<category>(discussion|request|issue))s/(?P<thread_id>\d+)/$', views.show_posts, name='show_posts'),
    url(r'^comments/(?P<category>(discussion|request|issue))s/new/$', views.new_post, name='new_post'),
    url(r'^comments/(?P<category>(discussion|request|issue))s/(?P<filter>(all|closed))/$', views.show_threads, name='show_threads'),
    url(r'^comments/(?P<category>(discussion|request|issue))s/$', views.show_threads, name='show_threads'),
)
