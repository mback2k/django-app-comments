# -*- coding: utf-8 -*-
from django.contrib import admin
from .models import Thread, Post, Vote

class ThreadAdmin(admin.ModelAdmin):
    pass

class PostAdmin(admin.ModelAdmin):
    pass

class VoteAdmin(admin.ModelAdmin):
    pass

admin.site.register(Thread, ThreadAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Vote, VoteAdmin)
