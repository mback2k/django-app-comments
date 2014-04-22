# -*- coding: utf-8 -*-
from django.contrib import admin
from .models import Thread, Post

class ThreadAdmin(admin.ModelAdmin):
    pass

class PostAdmin(admin.ModelAdmin):
    pass

admin.site.register(Thread, ThreadAdmin)
admin.site.register(Post, PostAdmin)
