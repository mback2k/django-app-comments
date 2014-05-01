# -*- coding: utf-8 -*-
from django.contrib import admin
from .models import Thread, Post, Vote, Media

class ThreadAdmin(admin.ModelAdmin):
    list_display = ('category', 'crdate', 'tstamp', 'is_closed', 'is_deleted')
    list_filter = ('is_closed', 'is_deleted', 'crdate', 'tstamp')
    date_hierarchy = 'crdate'

class PostAdmin(admin.ModelAdmin):
    raw_id_fields = ('thread', 'author')
    search_fields = ('author__username', 'author__email', '^author__first_name', '^author__last_name')
    list_display = ('thread', 'author', 'get_cleaned_content', 'crdate', 'tstamp', 'edited',
                    'is_deleted', 'is_approved', 'is_flagged', 'is_spam', 'is_highlighted')
    list_filter = ('is_deleted', 'is_approved', 'is_flagged', 'is_spam', 'is_highlighted',
                   'crdate', 'tstamp', 'edited')
    date_hierarchy = 'crdate'
    list_select_related = True
    list_per_page = 50

class VoteAdmin(admin.ModelAdmin):
    raw_id_fields = ('post', 'user')
    list_display = ('post', 'user', 'mode')
    list_filter = ('mode',)

class MediaAdmin(admin.ModelAdmin):
    raw_id_fields = ('post',)
    list_display = ('post', 'image', 'width', 'height')

admin.site.register(Thread, ThreadAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Vote, VoteAdmin)
admin.site.register(Media, MediaAdmin)
