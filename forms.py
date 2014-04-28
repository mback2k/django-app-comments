# -*- coding: utf-8 -*-
from django import forms
from django.utils.translation import ugettext_lazy as _
from .models import Post

class PostNewForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('content',)
        help_texts = {
            'content': _('You can use the following HTML tags: <br>, <p>, <a>, <b>, <i>, <strong> and <em>.'),
        }

class PostReplyForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('content', 'parent', 'thread')
        widgets = {
            'parent': forms.widgets.HiddenInput(),
            'thread': forms.widgets.HiddenInput(),
        }
        help_texts = {
            'content': _('You can use the following HTML tags: <br>, <p>, <a>, <b>, <i>, <strong> and <em>.'),
        }

class PostEditForm(PostNewForm):
    pass
