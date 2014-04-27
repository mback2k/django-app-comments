# -*- coding: utf-8 -*-
from django import forms
from .models import Post

class PostNewForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('content',)

class PostReplyForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('content', 'parent', 'thread')
        widgets = {
            'parent': forms.widgets.HiddenInput(),
            'thread': forms.widgets.HiddenInput(),
        }
